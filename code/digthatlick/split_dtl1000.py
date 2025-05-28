"""
This script splits the DTL1000 dataset into three separate CSV files:
- dtl1000_solos.csv: Contains solo performance information.
- dtl1000_tracks.csv: Contains track information.
- dtl1000_performers.csv: Contains performer information.
This allows for easier reconciliation and conversion to RDF
Run this script in the same directory as the input CSV file.
"""

import pandas as pd
import re

input_file = "dtl_metadata_v0.9.csv"


df = pd.read_csv(input_file, sep=";")


def truncate_to_track_id(solo_id: str) -> str:
    """
    Take the first 32 characters of a solo_id to create a track_id."""
    try:
        return str(solo_id)[:32]
    except Exception as e:
        raise ValueError(f"Failed to generate track_id based off of '{solo_id}': {e}")


def clean_performers_name(performers: str) -> list:
    """Performer names are formatted like "Bill Thomas (sb). Ella Fitzgerald (voc), Bobby Stark (tp)"
    This function split the performer names and remove the instrument parentetheses.
    This will help performer names reconciliation"""
    if pd.isna(performers):
        return []

    # Step 1: look behind closing parentheses and split on that punctuation
    perf_list = re.split(r"(?<=\))[\.,;:]\s*", performers)

    cleaned_perf_list = []
    for performer in perf_list:
        # Step 2: remove last parentheses group from each part
        cleaned_performer = re.sub(r"\s*\([^()]*\)\s*$", "", performer).strip()
        if cleaned_performer:
            cleaned_perf_list.append(cleaned_performer)

    return cleaned_perf_list


# add track_id to solo_info
df["track_id"] = df["solo_id"].apply(truncate_to_track_id)

# expand instrument_label
df.loc[:, ("instrument_label")] = df.loc[:, ("instrument_label")].apply(
    lambda x: {
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
    }.get(x, x)
)

# solo_info has all the information that directly relates to a specific solo on a track,
# )
solos = df.loc[
    :,
    [
        "solo_id",
        "possible_solo_performer_names",
        "solo_performer_name",
        "instrument_label",
    ],
].copy()  # and then add track id later

# track_info has all the information that relates to a specific track,
# so it has area, session_date, track_title, disk_title, medium_record_number, medium_title, leader_name, band_name,
# and then it has first part of solo_id as that is basically the track id.
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

# performers.csv contains all performers associated with a track.
performers = df.loc[:, ["track_id", "performer_names"]].copy()


# many solos belong same track and share duplicate track metadata
tracks.drop_duplicates(inplace=True)
performers.drop_duplicates(inplace=True)

# Possible solo_performer_names needs to be split at the comma
solos["possible_solo_performer_names"] = solos["possible_solo_performer_names"].apply(
    lambda x: x.split(",") if pd.notna(x) else []
)

solos = solos.explode("possible_solo_performer_names")

# Performer names need to be cleaned and exploded to allow reconciliation
performers["performer_names"] = performers["performer_names"].apply(
    clean_performers_name
)
performers = performers.explode("performer_names")


# Save the dataframes to CSV files
solos.to_csv("dtl1000_solos.csv", index=False)
tracks.to_csv("dtl1000_tracks.csv", index=False)
performers.to_csv("dtl1000_performers.csv", index=False)
