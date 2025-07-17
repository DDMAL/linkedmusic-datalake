"""
Wikidata Label Annotator

Features:
- Extract Wikidata ID from each line of a text file.
- Fetch English label for each Wikidata ID using the Wikidata API.
- Append the label as comment at the end of each line (using `#`).
- If more than one Wikidata ID is found on a single line, only the last one is considered.

Requires:
- aiohttp
- wikidata_utils (internal module)

Note:
    This script must be run with the current working directory set to `/code`.

Usage:
    python -m rdfconv.labels input.txt --output output.txt
    python -m rdfconv.labels input.txt  # overwrites input.txt
"""

import asyncio

import re
from pathlib import Path
import argparse
import logging
from wikidata_utils import extract_wd_id, WikidataAPIClient
import aiohttp

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


async def add_labels_as_comments(
    input_path: Path, output_path: Path, client: WikidataAPIClient
):
    """
    Reads an input file line-by-line, extracts the last Wikidata ID from each line,
    fetches the corresponding English label from Wikidata, and writes the annotated
    lines to an output file with the label appended as a comment.

    Each line will be formatted as:
        original content  # label (QID)
    or:
        original content  # QID does not exist
    or unchanged if no ID was found.

    Args:
        input_path (Path): Path to the input text file.
        output_path (Path): Path to the output file to write results.
        client (WikidataAPIClient): An async API client to fetch labels from Wikidata.
    """
    lines_with_ids: list[tuple[str, str]] = []
    ids: list[str] = []

    if not input_path.exists():
        logger.error("Input file '%s' does not exist.", input_path)
        return None

    # === Reading input file ===
    logger.info("Reading input file: %s", input_path)
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            # Remove existing comments (but preserve inline hash inside quotes)
            line_no_comm = re.split(r"\s+#", line, maxsplit=1)[0].rstrip()
            wd_id: str = extract_wd_id(line_no_comm)
            lines_with_ids.append((line_no_comm, wd_id))
            if wd_id:
                ids.append(wd_id)
    # === Fetching labels from Wikidata ===
    unique_ids = list(set(ids))
    logger.info("Fetching labels for %d unique Wikidata IDs...", len(unique_ids))
    try:
        labels_dict = await client.wbgetentities(
            unique_ids, props="labels", languages="en"
        )
    except Exception as e:
        logger.error("Error fetching labels from Wikidata API: %s", e)
        return None

    # === Write output ===
    output_dir = output_path.parent
    if not output_dir.exists():
        logger.info("Creating output directory: %s", output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Writing output to: %s", output_path)
    with open(output_path, "w", encoding="utf-8") as f_out:
        for line, wd_id in lines_with_ids:
            # In labels_dict, the each Wikidata ID is paired with a dictionary containing the field "labels"
            label = labels_dict.get(wd_id, {}).get("labels", "")
            if label:
                f_out.write(f"{line}  # {label} ({wd_id})\n")
            elif wd_id:
                f_out.write(f"{line}  # {wd_id} does not exist\n")
            else:
                f_out.write(line + "\n")


async def main():
    """
    Asynchronous CLI entry point for the Wikidata label annotator script.

    CLI arguments:
        input_file (str): Path to the input file containing Wikidata IDs.
        --output (str): Optional path to the output file. If omitted, the input file
            will be overwritten.
    """
    parser = argparse.ArgumentParser(
        description="Script to add Wikidata labels as comments using QID/PID extracted from each line."
    )

    parser.add_argument(
        "input_file",
        metavar="INPUT_FILE",
        type=str,
        help="Path to the input file containing Wikidata IDs (e.g., Q42, P31).",
    )

    parser.add_argument(
        "--output",
        metavar="OUTPUT_FILE",
        type=str,
        help="Path to the output file. If omitted, the input file will be overwritten.",
    )

    args = parser.parse_args()

    input_file = Path(args.input_file)
    output_file = Path(args.output) if args.output else input_file

    async with aiohttp.ClientSession() as session:
        client = WikidataAPIClient(session)
        await add_labels_as_comments(input_file, output_file, client)


if __name__ == "__main__":
    asyncio.run(main())
