"""
Scans all high level data files and extracts the values for specific fields
"""

import os
import csv
import json
from pathlib import Path
import pandas as pd

INPUT_PATH = "../data/extracted/highlevel/"
INPUT_PATH_TONAL = "../data/extracted/acousticbrainz-lowlevel-features-20220623-tonal.csv"
OUTPUT_PATH = "../data/unreconciled/"
os.makedirs(OUTPUT_PATH, exist_ok=True)

MAPPINGS = {
    "genre_tzanetakis": {
        "blu": "blues",
        "cla": "classical",
        "cou": "country",
        "dis": "disco",
        "hip": "hiphop",
        "jaz": "jazz",
        "met": "metal",
        "pop": "pop",
        "reg": "reggae",
        "roc": "rock",
    },
    "genre_rosamerica": {
        "cla": "classical",
        "dan": "dance",
        "hip": "hip-hop",
        "jaz": "jazz",
        "pop": "pop",
        "rhy": "rhythm'n'blues",
        "roc": "rock",
        "spe": "speech",
    },
}

EXTRACT_ALL = [
    "gender",
    "genre_dortmund",
    "genre_electronic",
    "genre_rosamerica",
    "genre_tzanetakis",
    "ismir04_rhythm",
    "moods_mirex",
    "timbre",
    "tonal_atonal",
    "voice_instrumental",
]

EXTRACT_MOOD = [
    "mood_acoustic",
    "mood_aggressive",
    "mood_electronic",
    "mood_happy",
    "mood_party",
    "mood_relaxed",
    "mood_sad",
]

values = {}

print("Processing values...")
file = next(Path(INPUT_PATH).glob("*.jsonl"))
with open(file, "r", encoding="utf-8") as f:
    sample = json.loads(f.readline())["highlevel"]
    values = {field: [k for k in sample[field]["all"].keys()] for field in EXTRACT_ALL}
    values["mood"] = [
        value
        for field in EXTRACT_MOOD
        for value in sample[field]["all"].keys()
        if not value.startswith("not_")
    ]

print("Processing tonal values...")
tonality = set()
with open(INPUT_PATH_TONAL, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        tonality.add(f"{row["key_key"]} {row["key_scale"]}")
values["tonality"] = [t for t in tonality if t.strip()]

for key, mapping in MAPPINGS.items():
    values[key] = [mapping.get(v, v) for v in values[key]]

for k, v in values.items():
    df = pd.DataFrame(v, columns=[k])
    df.to_csv(os.path.join(OUTPUT_PATH, f"{k}.csv"), index=False, encoding="utf-8")
