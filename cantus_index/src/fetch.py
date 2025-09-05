"""
Fetch and process Cantus Index data using async requests.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiohttp
from aiolimiter import AsyncLimiter
from tqdm import tqdm

# Configuration
CIDS_URL = "https://cantusindex.org/json-cids"
CID_DATA_URL = "https://cantusindex.org/json-cid-data/{}"
OUTPUT_FOLDER = Path("cantus_index/data/raw")
MAX_RETRIES = 5  # Maximum number of retries for a single CID
TIMEOUT = aiohttp.ClientTimeout(total=10)  # Timeout for network requests in seconds
RATE_LIMIT = 6  # Requests per second
CONCURRENT_REQUESTS = 3  # Number of concurrent requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
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
        logger.error(f"Error fetching CIDs list: {e}")
        return []


async def fetch_cid_json(
    session: aiohttp.ClientSession, 
    limiter: AsyncLimiter,
    cid: str, 
    pbar: tqdm,
    output_dir: Path
) -> None:
    """Fetch data for a single Cantus Index ID with rate limiting and retries."""
    output_file = output_dir / f"{cid}.json"
    
    # Check if file already exists and is valid
    if output_file.exists():
        try:
            # Just verify the file contains valid JSON
            with open(output_file, "r", encoding="utf-8") as f:
                json.load(f)
            logger.debug(f"File already exists for CID {cid}")
            pbar.update(1)
            return  # Early return, no need to fetch again
        except (json.JSONDecodeError, IOError) as e:
            # If file exists but is corrupt or unreadable, log and continue to fetch
            logger.warning(f"Existing file for CID {cid} is corrupt or unreadable: {e}. Re-fetching.")
    
    url = CID_DATA_URL.format(cid)
    retries = 0
    had_error = False
    
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
                        logger.info(f"Recovered after error, successfully fetched CID {cid}")
                    
                    return  # No need to return data
                    
        except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError) as e:
            had_error = True
            retries += 1
            wait_time = 2 ** retries  # Exponential backoff
            logger.warning(f"Error fetching CID {cid} (attempt {retries}/{MAX_RETRIES}): {e}")
            logger.info(f"Waiting {wait_time} seconds before retrying...")
            await asyncio.sleep(wait_time)
    
    logger.error(f"Failed to fetch CID {cid} after {MAX_RETRIES} attempts. Skipping.")
    return None


async def process_cids(cids_list: List[Dict[str, Any]], output_dir: Path):
    """Process all Cantus Index IDs concurrently with rate limiting."""
    limiter = AsyncLimiter(RATE_LIMIT, 1)  # Allow N requests per second
    
    # Use a semaphore to limit the number of concurrent tasks
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    
    async def fetch_with_semaphore(cid, pbar):
        """Fetch a single CID with semaphore-based concurrency control."""
        async with semaphore:
            return await fetch_cid_json(session, limiter, cid, pbar, output_dir)
    
    async with aiohttp.ClientSession() as session:
        with tqdm(total=len(cids_list), desc="Fetching Cantus Index data") as pbar:
            # Create all tasks but control concurrency with semaphore
            tasks = []
            for chant in cids_list:
                cid = chant['cid']
                tasks.append(fetch_with_semaphore(cid, pbar))
            
            # Run all tasks and wait for completion
            # This will start up to CONCURRENT_REQUESTS tasks at once
            # When any task completes, it immediately starts another one
            await asyncio.gather(*tasks)


async def main_async():
    """Main async function to orchestrate the fetching process."""
    # Create output directory
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
    
    async with aiohttp.ClientSession() as session:
        # Fetch list of Cantus Index IDs
        cids = await fetch_cids_list(session)
        
        if not cids:
            logger.error("Unable to find the list of Cantus Index IDs to retrieve. Exiting.")
            return
        
        logger.info(f"Found {len(cids)} Cantus Index IDs to process.")
        
        # Process all CIDs and save individual JSON files
        await process_cids(cids, OUTPUT_FOLDER)
        
        # Count the number of successfully downloaded files
        successful_files = list(OUTPUT_FOLDER.glob("*.json"))
        logger.info(f"Successfully downloaded {len(successful_files)} out of {len(cids)} Cantus Index IDs.")
        logger.info(f"Saved individual JSON files to {OUTPUT_FOLDER}")


def main():
    """Entry point for the script."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()