"""
This script splits the DTL1000 dataset into three separate CSV files:
- dtl1000_solos.csv: Contains solo performance information.
- dtl1000_tracks.csv: Contains track information.
- dtl1000_performers.csv: Contains performer information.
This allows for easier reconciliation and conversion to RDF
"""

import pandas as pd
import re

input_file = "dtl_metadata_v0.9.csv"


df = pd.read_csv(input_file, sep=";")

# solo_info has all the information that directly relates to a specific solo on a track,
# so it has solo_id, solo_performer_name, Instrument_label, solo_start and solo_end, possible performer_names (solo_start and solo_end are in the id so maybe not)
solo_info = df.iloc[:, [0, 1, 3, 12]].copy()  # and then add track id later

# track_info has all the information that relates to a specific track,
# so it has area, session_date, track_title, disk_title, medium_record_number, medium_title, leader_name, band_name,
# and then it has first part of solo_id as that is basically the track id.
track_info = df.iloc[:, [0, 4, 5, 6, 7, 8, 9, 10, 11]].copy()

performers = df.iloc[:, [0, 2]].copy()

# add track_id to solo_info
solo_info["track_id"] = solo_info["solo_id"].apply(
    lambda x: str(x)[:32] if isinstance(x, str) and len(x) > 28 else x
)
# map instruments to full names
solo_info.loc[:, ("instrument_label")] = solo_info.loc[:, ("instrument_label")].apply(
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

# edit track_info
track_info.loc[:, ("solo_id")] = track_info.loc[:, ("solo_id")].apply(
    lambda x: str(x)[:32] if isinstance(x, str) and len(x) > 28 else x
)

track_info.rename(mapper={"solo_id": "track_id"}, axis=1, inplace=True)
track_info.drop_duplicates(inplace=True)


# edit performers
performers.loc[:, ("solo_id")] = performers.loc[:, ("solo_id")].apply(
    lambda x: str(x)[:32] if isinstance(x, str) and len(x) > 28 else x
)
performers.drop_duplicates(inplace=True)
performers.rename(mapper={"solo_id": "track_id"}, axis=1, inplace=True)


def split_after_parenthesis_punct(s):
    if pd.isna(s):
        return []
    # Split at punctuation that immediately follows ')'
    parts = re.split(r"\)[\.,;:]\s*", s)
    # Add back the ')' to each part except the last (if not empty)
    parts = [p + ")" for p in parts[:-1] if p.strip()] + (
        [parts[-1]] if parts[-1].strip() else []
    )
    return [p.strip() for p in parts if p.strip()]


# def extract_last_parentheses(s):
#    if pd.isna(s):
#        return None
#    match = re.search(r'\(([^()]*)\)\s*$', s)
#    return match.group(1).strip() if match else None
#


def remove_last_parentheses(s):
    if pd.isna(s):
        return s
    return re.sub(r"\s*\([^()]*\)\s*$", "", s).strip()


performers["performer_names"] = performers["performer_names"].apply(
    split_after_parenthesis_punct
)
performers = performers.explode("performer_names")

# performers['instrument_label'] = performers['performer_names'].apply(extract_last_parentheses)

performers["performer_names"] = performers["performer_names"].apply(
    remove_last_parentheses
)

# Save the dataframes to CSV files
solo_info.to_csv("dtl1000_solos.csv", index=False)
track_info.to_csv("dtl1000_tracks.csv", index=False)
performers.to_csv("dtl1000_performers.csv", index=False)
