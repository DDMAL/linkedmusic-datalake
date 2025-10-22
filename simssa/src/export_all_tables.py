"""
Script to export all tables from the SimssaDB PostgreSQL database to CSV files.

Make sure to set up the database following the guidelines in the README.

CSV filesare categorized into subdirectories based on predefined mappings.
Empty tables are skipped during the export process.
"""

import csv
import os
import logging
import argparse
import psycopg2

# Database connection parameters
DB_PARAMS = {
    "dbname": "simssadb",
    "user": "myuser",
    "password": "mypassword",
    "host": "localhost",
}

DEFAULT_OUTPUT_DIR = os.path.abspath("./simssa/data/raw")

# Table to subdirectory mapping based on existing structure
# Example: "extracted_feature" CSV goes to "data/raw/feature" subdirectory
TABLE_MAPPINGS = {
    # Feature-related tables
    "extracted_feature": "feature",
    "feature": "feature",
    "feature_file": "feature",
    # Genre-related tables
    "genre_as_in_style": "genre",
    "genre_as_in_type": "genre",
    "musical_work_genres_as_in_style": "genre",
    "musical_work_genres_as_in_type": "genre",
    # Instance-related tables
    "files": "instance",
    "source_instantiation": "instance",
    "source_instantiation_sections": "instance",
    # Musical work-related tables
    "musical_work": "musical_work",
    "part": "musical_work",
    "section": "musical_work",
    "geographic_area": "musical_work",
    "instrument": "musical_work",
    # Person-related tables
    "contribution_musical_work": "person",
    "person": "person",
    # Source-related tables
    "source": "source",
}

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main(base_output_dir):
    """
    Export all tables from the database to CSV files.

    Tables are placed in subdirectories based on existing mapping.
    Skips empty tables.
    """

    # Ensure base output directory exists
    os.makedirs(base_output_dir, exist_ok=True)

    # Create all subdirectories
    subdirs = set(TABLE_MAPPINGS.values()) | {"other"}
    for subdir in subdirs:
        os.makedirs(os.path.join(base_output_dir, subdir), exist_ok=True)

    # Connect to database
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    try:
        # Get all table names in public schema
        cur.execute(
            """
            SELECT tablename FROM pg_tables WHERE schemaname = 'public';
        """
        )
        table_names = [row[0] for row in cur.fetchall()]

        exported_count = 0

        for table_name in table_names:
            try:
                # Get table subdirectory (default to 'other' if unknown)
                table_subdir = TABLE_MAPPINGS.get(table_name, "other")
                output_dir = os.path.join(base_output_dir, table_subdir)

                # Execute query
                cur.execute(f'SELECT * FROM "{table_name}"')

                # Skip empty tables
                rows = cur.fetchall()
                if len(rows) == 0:
                    logging.info("Skipped %s (empty table)", table_name)
                    continue

                # Write to CSV
                csv_path = os.path.join(output_dir, f"{table_name}.csv")
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [col[0] for col in cur.description]
                    )  # Write headers
                    writer.writerows(rows)

                exported_count += 1

            except (psycopg2.Error, IOError) as e:
                logging.error("Error exporting table %s: %s", table_name, e)

        logging.info("\nExport completed!")
        logging.info("Total tables exported: %d", exported_count)

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export all tables from the SimssaDB PostgreSQL database to CSV files."
        )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Base directory for output CSV files (default: ./simssa/data/raw)"
    )
    args = parser.parse_args()
    main(args.output)
