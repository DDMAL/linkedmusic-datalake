"""
add_labels.py

This script extracts the last Wikidata ID from each line,
fetches the English label for those IDs from the Wikidata API, and appends the label
as a comment at the end of the line (using #). It supports either overwriting the original file or
writing to a separate output file.

Requires:
- aiohttp
- wikidata_utils (must provide extract_wd_id and WikidataAPIClient)

Usage:
    python -m add_labels input.txt --output output.txt
    python -m add_labels input.txt --overwrite
"""

import asyncio
from pathlib import Path
import argparse
import logging
from wikidata_utils import extract_wd_id, WikidataAPIClient
import aiohttp

logger = logging.getLogger("add_labels")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


async def add_labels(input_path: Path, output_path: Path, client: WikidataAPIClient):
    """
    Reads an input file line-by-line, extracts the last Wikidata ID from each line,
    fetches the corresponding label from Wikidata, and writes the lines to an output file
    with the label as a comment.

    Args:
        input_path (Path): Path to the input file.
        output_path (Path): Path to the output file to write results.
        client (WikidataAPIClient): An instance of WikidataAPIClient for label fetching.
    """
    lines: list[tuple[str, str]] = []
    ids: list[str] = []

    if not input_path.exists():
        logger.error("Input file '%s' does not exist.", input_path)
        return

    logger.info("Reading input file: %s", input_path)
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            wd_id: str = extract_wd_id(line)
            lines.append((line, wd_id))
            if wd_id:
                ids.append(wd_id)

    unique_ids = list(set(ids))
    logger.info("Fetching labels for %d unique Wikidata IDs...", len(unique_ids))

    try:
        labels_dict = await client.wbgetentities(
            unique_ids, props="labels", languages="en"
        )
    except Exception as e:
        logger.error("Error fetching labels from Wikidata API: %s", e)
        return

    output_dir = output_path.parent
    if not output_dir.exists():
        logger.info("Creating output directory: %s", output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Writing output to: %s", output_path)
    with open(output_path, "w", encoding="utf-8") as f_out:
        for line, wd_id in lines:
            label = labels_dict.get(wd_id, {}).get("labels", {})
            if label:
                f_out.write(f"{line}  # {label} ({wd_id})\n")
            elif wd_id:
                f_out.write(f"{line}  # {wd_id} does not exist\n")
            else:
                f_out.write(line + "\n")


async def main(input_file: Path, output_file: Path):
    """
    Main async entry point. Initializes the Wikidata API client session and
    delegates to `add_labels`.

    Args:
        input_file (Path): Path to the input file.
        output_file (Path): Path to the output file (can be same as input).
    """
    async with aiohttp.ClientSession() as session:
        client = WikidataAPIClient(session)
        await add_labels(input_file, output_file, client)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to add Wikidata labels as comments based on QID/PID on each line."
    )

    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input file containing Wikidata IDs (e.g., Q42, P31) line by line",
    )

    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the original file with labels added as comments",
    )
    output_group.add_argument(
        "--output",
        type=str,
        help="Path to the output file with labels added as comments (original file remains unchanged)",
    )

    args = parser.parse_args()

    input_file = Path(args.input_file)
    output_file = Path(args.output) if args.output else input_file

    asyncio.run(main(input_file, output_file))
