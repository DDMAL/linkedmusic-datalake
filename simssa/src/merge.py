import argparse
import logging
from pathlib import Path
import pandas as pd

DEFAULT_INPUT_DIR = Path("simssa/data/raw")
DEFAULT_OUTPUT_DIR = Path("simssa/data/merged")

# Configure logger
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def load_and_select(csv_path, usecols, rename_dict):
    df = pd.read_csv(csv_path, usecols=usecols, dtype=str)
    return df.rename(columns=rename_dict)


def merge_instance_data(input_dir):
    source_inst_df = load_and_select(
        input_dir / "instance" / "source_instantiation.csv",
        usecols=["id", "source_id", "work_id"],
        rename_dict={"id": "instance_id"},
    )

    source_inst_section_df = load_and_select(
        input_dir / "instance" / "source_instantiation_sections.csv",
        usecols=["sourceinstantiation_id", "section_id"],
        rename_dict={"sourceinstantiation_id": "instance_id"},
    )

    files_df = load_and_select(
        input_dir / "instance" / "files.csv",
        usecols=["id", "file_format", "file", "instantiates_id"],
        rename_dict={
            "id": "file_id",
            "file": "file_name",
            "instantiates_id": "instance_id",
        },
    )

    # Each instance may have multiple files
    merged_df = pd.merge(source_inst_df, source_inst_section_df, on="instance_id", how="left")
    full_merged_df = pd.merge(
        merged_df, files_df, on="instance_id", how="left"
    )

    # Drop the instance_id column
    full_merged_df = full_merged_df.drop(columns=["instance_id"])

    return full_merged_df


def merge_work_data(input_dir):
    # Load and process musical_work.csv
    work_df = load_and_select(
        input_dir / "musical_work" / "musical_work.csv",
        usecols=["id", "variant_titles", "sacred_or_secular"],
        rename_dict={"id": "work_id", "variant_titles": "work_title"},
    )
    # Clean work_title by removing brackets and quotes
    work_df["work_title"] = work_df["work_title"].str.replace(
        r"[\[\]'\"']", "", regex=True
    )
    work_df["sacred_or_secular"] = work_df["sacred_or_secular"].replace(
        {"False": "Secular", "True": "Sacred"}
    )

    # Load and process section.csv
    section_df = load_and_select(
        input_dir / "musical_work" / "section.csv",
        usecols=["id", "title", "musical_work_id"],
        rename_dict={
            "id": "section_id",
            "title": "section_title",
            "musical_work_id": "work_id",
        },
    )

    # Left join work_df with section_df on work_id
    merged_with_sections_df = pd.merge(work_df, section_df, on="work_id", how="left")

    # Load and process contribution_musical_works.csv
    contribution_df = load_and_select(
        input_dir / "person" / "contribution_musical_work.csv",
        usecols=["role", "person_id", "contributed_to_work_id"],
        rename_dict={"contributed_to_work_id": "work_id"},
    )

    # The original table store the role of the contributor as either AUTHOR or COMPOSER
    contribution_pivot = (
        contribution_df.pivot_table(
            index="work_id", columns="role", values="person_id", aggfunc="first"
        )
        .rename(columns={"AUTHOR": "author_id", "COMPOSER": "composer_id"})
        .reset_index()
    )

    # Merge the pivoted contribution data with the work-section DataFrame
    merged_with_creator_df = pd.merge(
        merged_with_sections_df, contribution_pivot, on="work_id", how="left"
    )

    # Processing genre data
    # Load and process genre-work match table
    genre_of_work_df = load_and_select(
        input_dir / "genre" / "musical_work_genres_as_in_type.csv",
        usecols=["musicalwork_id", "genreasintype_id"],
        rename_dict={"musicalwork_id": "work_id", "genreasintype_id": "genre_id"},
    )

    # Load and process genre id-name match table
    genres_df = load_and_select(
        input_dir / "genre" / "genre_as_in_type.csv",
        usecols=["id", "name"],
        rename_dict={"id": "genre_id", "name": "genre_name"},
    )

    # Left join genres_df with work_genres_df on genre_id
    merged_genres_df = pd.merge(genre_of_work_df, genres_df, on="genre_id", how="left")

    # Left join the result with the merged work-section-contribution DataFrame on work_id
    final_merged_df = pd.merge(
        merged_with_creator_df, merged_genres_df, on="work_id", how="left"
    )

    # genre_as_in_style.csv explicitly specify "Renaissance" for all works
    final_merged_df["style"] = "Renaissance"

    return final_merged_df


def process_source_data(input_dir):
    # Load and process source/source.csv
    source_df = load_and_select(
        input_dir / "source" / "source.csv",
        usecols=["id", "title"],
        rename_dict={"id": "source_id", "title": "source_title"},
    )
    # Remove double quotes from source_title
    source_df["source_title"] = source_df["source_title"].str.replace(
        '"', "", regex=False
    )

    return source_df


def process_person_data(input_dir):
    # Load and process person/person.csv
    person_df = load_and_select(
        input_dir / "person" / "person.csv",
        usecols=[
            "id",
            "given_name",
            "surname",
            "birth_date_range_year_only",
            "death_date_range_year_only",
            "authority_control_url",
        ],
        rename_dict={"id": "person_id", "authority_control_url": "viaf_id"},
    )

    # Combine given_name and surname into person_name
    person_df["person_name"] = person_df["given_name"] + " " + person_df["surname"]

    # Extract the year and convert to xsd:date compatible format (YYYY-01-01)
    person_df["birth_year"] = (
        person_df["birth_date_range_year_only"]
        .str.extract(r"\[(\d{4})")[0]
        .apply(lambda y: f"{y}-01-01" if pd.notnull(y) else None)
    )

    person_df["death_year"] = (
        person_df["death_date_range_year_only"]
        .str.extract(r"\[(\d{4})")[0]
        .apply(lambda y: f"{y}-01-01" if pd.notnull(y) else None)
    )

    # Drop unnecessary name and date_range columns
    person_df = person_df[
        ["person_id", "person_name", "birth_year", "death_year", "viaf_id"]
    ]

    return person_df


def main():
    parser = argparse.ArgumentParser(description="SIMSSA CSV merge utilities")
    parser.add_argument(
        "-i",
        "--input-dir",
        default=DEFAULT_INPUT_DIR,
        type=Path,
        help="Input raw data directory (default: simssa/data/raw)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        type=Path,
        help="Output directory for merged CSVs (default: simssa/data/merged)",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    merge_instance_data(args.input_dir).to_csv(
        args.output_dir / "instance.csv", index=False
    )
    merge_work_data(args.input_dir).to_csv(args.output_dir / "work.csv", index=False)
    process_source_data(args.input_dir).to_csv(
        args.output_dir / "source.csv", index=False
    )
    process_person_data(args.input_dir).to_csv(
        args.output_dir / "person.csv", index=False
    )

    logger.info(
        "All CSVs have been successfully processed and saved to %s", args.output_dir
    )


if __name__ == "__main__":
    main()
