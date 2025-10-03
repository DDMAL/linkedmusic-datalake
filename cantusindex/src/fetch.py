"""
Fetch Cantus Index data using async requests with rate limiting and error recovery.

This script downloads chant data from the Cantus Index API (format: https://cantusindex.org/json-cid-data/{cid})
Each chant's JSON data is saved as an individual file.

The script implements:
- Asynchronous HTTP requests with rate limiting and semaphore.
- Automatic retry logic with exponential backoff for failed requests
- Resume capability by skipping already downloaded valid JSON files

Usage:
    python fetch.py [--output OUTPUT_DIR]

Configuration:
    - RATE_LIMIT: Maximum number of requests per second
    - CONCURRENT_REQUESTS: Maximum concurrent requests
    - MAX_RETRIES: Maximum retry attempts per request
    - TIMEOUT: HTTP request timeout in seconds
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import aiohttp
from aiolimiter import AsyncLimiter
from tqdm import tqdm

# Configuration
# The CIDS_URL provides a list of all Cantus Index IDs
CIDS_URL = "https://cantusindex.org/json-cids"
# The CID_DATA_URL is a template URL to fetch JSON data for a specific Cantus Index chant
CID_DATA_URL = "https://cantusindex.org/json-cid-data/{}"
DEFAULT_OUTPUT_FOLDER = Path("cantusindex/data/raw")
MAX_RETRIES = 5  # Maximum number of retries for a single CID
TIMEOUT = aiohttp.ClientTimeout(total=10)  # Timeout for network requests in seconds
RATE_LIMIT = 6  # Requests per second
CONCURRENT_REQUESTS = 3  # Number of concurrent requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def fetch_cids_list(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Fetch the list of Cantus Index IDs."""
    try:
        async with session.get(CIDS_URL, timeout=TIMEOUT) as response:
            response.raise_for_status()
            content = await response.text(encoding="utf-8-sig")
            return json.loads(content)
    except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError) as e:
        logger.error("Error fetching CIDs list: %s", e)
        return []


async def fetch_indiv_cid(
    session: aiohttp.ClientSession,
    limiter: AsyncLimiter,
    semaphore: asyncio.Semaphore,
    cid: str,
    pbar: tqdm,
    output_dir: Path,
) -> None:
    """Fetch data from Cantus Index for a single CID and save as JSON file.

    Args:
        session: Shared aiohttp ClientSession for making HTTP requests.
        limiter: AsyncLimiter instance to control requests rate
        semaphore: Asyncio Semaphore to limit concurrent requests.
        cid: Cantus Index ID string identifying the specific chant to fetch.
        pbar: tqdm progress bar instance for tracking download progress.
        output_dir: Path object specifying directory where JSON file will be saved.

    Returns:
        None. The function saves data directly to a file named '{cid}.json'
        in the output directory.

    Raises:
        Logs errors but does not raise exceptions. Failed requests are retried
        up to MAX_RETRIES times with exponential backoff before giving up.

    Note:
        - Respects rate limiting and concurrency constraints
        - Automatically retries failed requests with exponential backoff
        - Logs recovery messages when requests succeed after initial failures
    """

    output_file = output_dir / f"{cid}.json"
    url = CID_DATA_URL.format(cid)
    retries = 0
    had_error = False

    async with semaphore:
        while retries < MAX_RETRIES:
            try:
                async with limiter:
                    async with session.get(url, timeout=TIMEOUT) as response:
                        response.raise_for_status()
                        content = await response.text(encoding="utf-8-sig")
                        data = json.loads(content)

                        # Save individual JSON file
                        with open(output_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)

                        pbar.update(1)
                        if had_error:
                            logger.info(
                                "Recovered after error, successfully fetched CID %s",
                                cid,
                            )

                        return  # No need to return data

            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
                json.JSONDecodeError,
            ) as e:
                had_error = True
                retries += 1
                wait_time = 2**retries  # Exponential backoff
                logger.warning(
                    "Error fetching CID %s (attempt %d/%d): %s",
                    cid,
                    retries,
                    MAX_RETRIES,
                    e,
                )
                logger.info("Waiting %d seconds before retrying...", wait_time)
                await asyncio.sleep(wait_time)

        logger.error(
            "Failed to fetch CID %s after %d attempts. Skipping.", cid, MAX_RETRIES
        )
        return None


async def fetch_all_cids(cids_list: List[Dict[str, Any]], output_dir: Path):
    """Fetch all Cantus Index chants concurrently with rate limiting.

    Each chant's data is saved as an individual JSON
    file in the output directory. The function implements rate limiting
    and concurrency control

    Args:
        cids_list: List of dictionaries containing chant metadata. Each dictionary
            must have a 'cid' key with the Cantus Index ID as its value.
        output_dir: Path object specifying the directory where individual JSON
            files will be saved. Each file will be named '{cid}.json'.

    Returns:
        None. Files are written directly to disk.

    Note:
        - Allows resuming downloads by skipping already existing files.
        - Handles errors with exponential backoff retry logic.
    """
    limiter = AsyncLimiter(RATE_LIMIT, 1)  # Limits number of requests per second

    # Limit the number of concurrent requests
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    # Filter out CIDs that already have valid files
    cids_to_fetch = []
    for chant in cids_list:
        cid = chant["cid"]
        output_file = output_dir / f"{cid}.json"

        # Check if file already exists and is valid
        if output_file.exists():
            try:
                # Just verify the file contains valid JSON
                with open(output_file, "r", encoding="utf-8") as f:
                    json.load(f)
                logger.debug("File already exists for CID %s", cid)
                continue  # Skip this CID, file already exists
            except (json.JSONDecodeError, IOError) as e:
                # If file exists but is corrupt or unreadable, log and continue to fetch
                logger.warning(
                    "Existing file for CID %s is corrupt or unreadable: %s. Re-fetching.",
                    cid,
                    e,
                )

        cids_to_fetch.append(chant)

    logger.info(
        "Need to fetch %d out of %d CIDs (skipping %d existing valid files)",
        len(cids_to_fetch),
        len(cids_list),
        len(cids_list) - len(cids_to_fetch),
    )

    if not cids_to_fetch:
        logger.info("All files already exist and are valid. Nothing to fetch.")
        return

    async with aiohttp.ClientSession() as session:
        with tqdm(total=len(cids_to_fetch), desc="Fetching Cantus Index data") as pbar:
            # Create all tasks
            tasks = []
            for chant in cids_to_fetch:
                cid = chant["cid"]
                tasks.append(
                    fetch_indiv_cid(session, limiter, semaphore, cid, pbar, output_dir)
                )

            # Run all tasks and wait for completion
            # This will start up to CONCURRENT_REQUESTS tasks at once
            # When any task completes, it immediately starts another one
            await asyncio.gather(*tasks)


def filter_valid_cids(cids: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out chants whose 'cid' starts with 'Error:'.
    Args:
        cids: List of chant dictionaries, each containing a 'cid' key.
    Returns:
        List of chant dictionaries with valid 'cid' values.
    """
    return [chant for chant in cids if not chant.get("cid", "").startswith("Error:")]


async def main_async(output_folder: Path):
    """Main async function to orchestrate the fetching process."""
    # Create output directory
    output_folder.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        # Fetch list of Cantus Index IDs
        cids = await fetch_cids_list(session)

        # Filter out chants whose cid starts with "Error:"
        filtered_cids = filter_valid_cids(cids)

        if not filtered_cids:
            logger.error("Unable to find valid Cantus Index IDs to retrieve. Exiting.")
            return

        logger.info("Found %d valid Cantus Index IDs to process.", len(filtered_cids))

        # Process all CIDs and save individual JSON files
        await fetch_all_cids(filtered_cids, output_folder)

        # Count the number of successfully downloaded files
        successful_files = list(output_folder.glob("*.json"))
        logger.info(
            "Successfully downloaded %d out of %d valid Cantus Index IDs.",
            len(successful_files),
            len(filtered_cids),
        )
        logger.info("Saved individual JSON files to %s", output_folder)


def main():
    """Entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Fetch Cantus Index data and save as individual JSON files."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FOLDER,
        help=f"Output directory for JSON files (default: {DEFAULT_OUTPUT_FOLDER})",
    )
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args.output))
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user.")
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)


if __name__ == "__main__":
    main()
