#!/usr/bin/env python3
"""
Convert Cantus Index JSON files to a single CSV file.
This script reads all individual JSON files downloaded by fetch.py
and combines them into a single CSV file for easier analysis.
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from tqdm import tqdm

# Configuration
INPUT_DIR = Path("cantus_index/data/raw/")
OUTPUT_FILE = Path("cantus_index/data/merged/cantus_index.csv")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def read_json_file(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Read a JSON file and return its contents."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def extract_fields(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract relevant fields from JSON data."""
    # For cantus index data, each file contains a list with one item
    if not data or not isinstance(data, list):
        return []
    
    # Return the data as is, we'll handle field extraction during CSV writing
    return data

def main():
    """Main function to process JSON files and create CSV."""
    # Check if input directory exists
    if not INPUT_DIR.exists() or not INPUT_DIR.is_dir():
        logger.error(f"Input directory {INPUT_DIR} does not exist or is not a directory.")
        return
    
    # Create output directory if it doesn't exist
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Get all JSON files
    json_files = list(INPUT_DIR.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files to process.")
    
    if not json_files:
        logger.error("No JSON files found in the input directory.")
        return
    
    # Read a single file to determine the fields. All Json files should have the same structure.
    sample_json = read_json_file(json_files[0])
    if not sample_json:
        logger.error("Could not read sample file to determine fields.")
        return
    
    # Extract all field names from the sample data
    fieldnames = []
    for item in sample_json:
        for key in item.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    
    # Write to CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process each JSON file
        processed_count = 0
        with tqdm(total=len(json_files), desc="Processing JSON files") as pbar:
            for json_file in json_files:
                data = read_json_file(json_file)
                if data:
                    # Extract fields and write to CSV
                    records = extract_fields(data)
                    for record in records:
                        writer.writerow(record)
                    processed_count += 1
                pbar.update(1)
    
    logger.info(f"Successfully processed {processed_count} out of {len(json_files)} JSON files.")
    logger.info(f"CSV file created at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
