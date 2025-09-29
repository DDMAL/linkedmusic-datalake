"""
Script to export all tables from a PostgreSQL database to structured CSV files.

Tables are categorized into subdirectories based on predefined mappings.
Empty tables are skipped during the export process.
"""

import psycopg2
import csv
import re
import os
import logging

# Database connection parameters
DB_PARAMS = {
    "dbname": "simssadb",
    "user": "myuser",
    "password": "mypassword",
    "host": "localhost",
}

BASE_OUTPUT_DIR = os.path.abspath("./simssa/data/raw")

# Table to directory mapping based on existing structure
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


def main():
    """
    Export all tables from the database to CSV files.

    Tables are placed in subdirectories based on their category.
    Skips empty tables and logs the export process.
    """

    # Ensure base output directory exists
    os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

    # Create all subdirectories
    subdirs = set(TABLE_MAPPINGS.values()) | {"other"}
    for subdir in subdirs:
        os.makedirs(os.path.join(BASE_OUTPUT_DIR, subdir), exist_ok=True)

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
                # Get table directory (default to 'other' if unknown)
                table_dir = TABLE_MAPPINGS.get(table_name, "other")
                output_dir = os.path.join(BASE_OUTPUT_DIR, table_dir)

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
    main()
