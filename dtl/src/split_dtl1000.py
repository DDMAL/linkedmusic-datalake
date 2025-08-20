"""
This script processes the raw DTL1000 CSV (dtl_metadata_v0.9.csv) and splits it into three
separate CSV files:

- dtl1000_solos.csv: Contains solo performance information, including solo IDs, performer
  names, instruments, and associated track IDs.
- dtl1000_tracks.csv: Contains track metadata shared by solos on the same track, such as
  band name, leader name, and session details.
- dtl1000_performers.csv: Contains performer information, including cleaned and exploded
  performer names for reconciliation.

The script performs the following steps:
1. Reads the input dataset from a CSV file.
2. Processes and cleans data, including:
   - Generating track IDs from solo IDs.
   - Expanding instrument labels to full instrument names.
   - Cleaning and splitting performer names.
3. Splits the dataset into three separate dataframes for solos, tracks, and performers.
4. Saves the processed dataframes as CSV files for further use.

Run this script from its own directory.
"""

import re
import os
import argparse
import pandas as pd

# Constants
DEFAULT_INPUT_FILE = "../data/raw/dtl_metadata_v0.9.csv"
OUTPUT_PATH = "../data/"

# Instrument label mappings
INSTRUMENT_MAPPINGS = {
    "as": "alto saxophone",
    "bs": "bari saxophone",
    "cl": "clarinet",
    "cor": "cornet",
    "fl": "flute",
    "flg": "flugelhorn",
    "ss": "soprano saxophone",
    "tb": "trombone",
    "tp": "trumpet",
    "ts": "saxophone",
    "vib": "vibraphone",
    "vln": "violin",
    "voc": "voice",
}


def truncate_to_track_id(solo_id: str) -> str:
    """
    Generate a track ID by truncating the first 32 characters of a solo ID.
    """
    try:
        return str(solo_id)[:32]
    except Exception as e:
        msg = f"Failed to generate track_id based off of '{solo_id}'"
        raise ValueError(msg) from e


def clean_performers_name(string: str) -> list:
    """
    Split and clean performer names by removing instrument labels in parentheses.

    Args:
        string (str): A string containing performer names with optional instrument labels.

    Returns:
        list: A list of cleaned performer names.

    Example:
        Input: "Bill Thomas (sb), Ella Fitzgerald (voc), Bobby Stark (tp)"
        Output: ["Bill Thomas", "Ella Fitzgerald", "Bobby Stark"]
    """
    if pd.isna(string):
        return []

    # Step 1: look behind closing parentheses and split on that punctuation
    perf_list = re.split(r"(?<=\))[\.,;:]\s*", string)

    cleaned_perf_list = []
    for performer in perf_list:
        # Step 2: remove last parentheses group from each part
        cleaned_performer = re.sub(r"\s*\([^()]*\)\s*$", "", performer).strip()
        if cleaned_performer:
            cleaned_perf_list.append(cleaned_performer)

    return cleaned_perf_list


def expand_instrument_labels(df: pd.DataFrame) -> None:
    """
    Expand instrument abbreviations to their full names in the 'instrument_label' column.
    """
    df["instrument_label"] = (
        df["instrument_label"]
        .map(INSTRUMENT_MAPPINGS)
        .fillna(df["instrument_label"])
    )


def split_solos(df: pd.DataFrame) -> pd.DataFrame:
    """split and clean solo data."""
    solos = df.loc[
        :,
        [
            "solo_id",
            "possible_solo_performer_names",
            "solo_performer_name",
            "instrument_label",
            "track_id",
        ],
    ].copy()

    # Split possible solo performer names at comma
    solos["possible_solo_performer_names"] = solos[
        "possible_solo_performer_names"
    ].apply(lambda x: x.split(",") if pd.notna(x) else [])
    solos = solos.explode("possible_solo_performer_names")

    # Remove extra 0s in solo_id at positions 41 and 56
    solos["solo_id"] = solos["solo_id"].apply(lambda x: x[:41] + x[42:56] + x[57:])

    return solos


def split_tracks(df: pd.DataFrame) -> pd.DataFrame:
    """Split and clean tracks data."""
    tracks = df.loc[
        :,
        [
            "track_id",
            "band_name",
            "leader_name",
            "medium_title",
            "medium_record_number",
            "disk_title",
            "track_title",
            "session_date",
            "area",
        ],
    ].copy()

    # Remove duplicates since many solos belong to the same track
    tracks.drop_duplicates(inplace=True)

    return tracks


def split_performers(df: pd.DataFrame) -> pd.DataFrame:
    """split and clean track performers data."""
    performers = df.loc[:, ["track_id", "performer_names"]].copy()

    # Remove duplicates
    performers.drop_duplicates(inplace=True)

    # Clean performer names and explode
    performers["performer_names"] = performers["performer_names"].apply(
        clean_performers_name
    )
    performers = performers.explode("performer_names")

    return performers


def save_dataframes(
    solos: pd.DataFrame, tracks: pd.DataFrame, performers: pd.DataFrame
) -> None:
    """Save the processed dataframes to CSV files."""
    solos.to_csv(os.path.join(OUTPUT_PATH, "dtl1000_solos.csv"), index=False)
    print(
        "Solos saved to:",
        os.path.join(os.path.abspath(OUTPUT_PATH), "dtl1000_solos.csv"),
    )

    tracks.to_csv(os.path.join(OUTPUT_PATH, "dtl1000_tracks.csv"), index=False)
    print(
        "Tracks saved to:",
        os.path.join(os.path.abspath(OUTPUT_PATH), "dtl1000_tracks.csv"),
    )

    performers.to_csv(os.path.join(OUTPUT_PATH, "dtl1000_performers.csv"), index=False)
    print(
        "Performers saved to:",
        os.path.join(os.path.abspath(OUTPUT_PATH), "dtl1000_performers.csv"),
    )


def main(args: argparse.Namespace) -> None:
    """Main function to orchestrate the data processing pipeline."""

    # Load the dataset
    df = pd.read_csv(args.input, sep=";")

    # Add column track_id to dataset
    df["track_id"] = df["solo_id"].apply(truncate_to_track_id)

    # Expand instrument labels
    expand_instrument_labels(df)

    # Split the dataframe into three CSV
    solos = split_solos(df)
    tracks = split_tracks(df)
    performers = split_performers(df)

    # Save the results
    save_dataframes(solos, tracks, performers)


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Process and split the DTL1000 dataset."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=DEFAULT_INPUT_FILE,
        help=f"Path to the input CSV file. Defaults to '{DEFAULT_INPUT_FILE}'.",
    )
    args = parser.parse_args()
    main(args)
