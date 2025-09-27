"""
Convert Cantus Index JSON files to a single CSV file.
This script reads all individual JSON files downloaded by fetch.py
and combines them into a single CSV file for easier RDF conversion.
"""

import json
import logging
from pathlib import Path
from tqdm import tqdm
import argparse
import pandas as pd

# Configuration
DEFAULT_INPUT_DIR = Path("cantusindex/data/raw/")
DEFAULT_OUTPUT_FILE = Path("cantusindex/data/merged/cantusindex.csv")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def json_files_to_csv(input_dir, output_file):
    """Process JSON files and write to a CSV file using pandas.

    Assumes that each JSON file contains a list of records (dictionaries)."""
    # Check if input directory exists
    if not input_dir.exists() or not input_dir.is_dir():
        logger.error(
            "Input directory %s does not exist or is not a directory.", input_dir
        )
        return

    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Get all JSON files
    json_files = list(input_dir.glob("*.json"))
    logger.info("Found %d JSON files to process.", len(json_files))

    if not json_files:
        logger.error("No JSON files found in the input directory.")
        return

    # Initialize list to hold DataFrames
    dataframes = []
    processed_count = 0

    # Process each JSON file
    with tqdm(total=len(json_files), desc="Processing JSON files") as pbar:
        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error("Error reading %s: %s", json_file, e)
                pbar.update(1)
                continue

            if not data:
                pbar.update(1)
                continue

            # Convert JSON data to DataFrame
            df = pd.DataFrame(data)
            dataframes.append(df)
            processed_count += 1
            pbar.update(1)

    # Concatenate all DataFrames
    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True, sort=False)

        # Write to CSV
        combined_df.to_csv(output_file, index=False, encoding="utf-8")

    else:
        logger.error("No valid data found to process.")
        return

    logger.info(
        "Successfully processed %d out of %d JSON files.",
        processed_count,
        len(json_files),
    )
    logger.info("CSV file created at %s", output_file)


def main():
    """Main function to parse arguments and call processing logic."""
    parser = argparse.ArgumentParser(
        description="Convert Cantus Index JSON files to a single CSV file."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory containing JSON files (default: cantusindex/data/raw/)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Output CSV file path (default: cantusindex/data/merged/cantusindex.csv)",
    )
    args = parser.parse_args()

    json_files_to_csv(args.input_dir, args.output)


if __name__ == "__main__":
    main()
