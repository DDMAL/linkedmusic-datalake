"""
Script to convert the JSON files from the DIAMM dataset into CSV files.
"""

import os
import json
import pandas as pd
import re

BASE_PATH = "../../data/diamm/raw/"
BASE_CSV_PATH = "../../data/diamm/csv/"

# Regex used to sanitize names to remove any dates
PERSON_NAME_DATE_REGEX = re.compile(r"^(.*?)(?:\s*\((?:ca\.|fl\.|–|\d|\d{3,4}).*?\))?\s*$")

os.makedirs(BASE_CSV_PATH, exist_ok=True)

# Hashable dictionary class to use with relations to make removing duplicate relations easier
class HashableDict:
    def __init__(self, d):
        self.d = dict(d)
        self._frozen = frozenset(self.d.items())

    def __hash__(self):
        return hash(self._frozen)

    def __eq__(self, other):
        return isinstance(other, HashableDict) and self._frozen == other._frozen

    def __repr__(self):
        return f"HashableDict({self.d})"

    @staticmethod
    def to_list_of_dicts(lst):
        """
        Takes an iterable object (set, list, etc) containing HashableDict
        objects and returns a list of dictionaries.
        This is useful for converting the set of relations to a DataFrame.
        """
        return [d.d for d in lst]

# Make the relations dataframe
relations = set()

# Archives
print("Starting to process archives")
rows = []
for file in os.listdir(os.path.join(BASE_PATH, "archives")):
    if file.endswith(".json"):
        with open(
            os.path.join(BASE_PATH, "archives", file), "r", encoding="utf-8"
        ) as f:
            data = json.load(f)
            line = {}
            line["id"] = data["pk"]
            line["name"] = data["name"]
            line["siglum"] = data["siglum"]
            line["website"] = data["website"] if "website" in data else ""
            line["rism_id"] = ""
            for identifier in data["identifiers"]:
                if re.match("RISM", identifier["label"], re.IGNORECASE):
                    line["rism_id"] = identifier["identifier"]
                    break
            for source in data["sources"]:
                source_id = int(source["url"].split("/")[-2])
                relations.add(
                    HashableDict(
                        {
                            "key1": f"archive:{line['id']}",
                            "key2": f"source:{source_id}",
                            "type": "",
                        }
                    )
                )
            line["city"] = data["city"]["name"]
            line["country"] = data["city"]["country"]
            rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "archives.csv"), index=False)
print("Finished processing archives")

# Compositions
print("Starting to process compositions")
rows = []
for file in os.listdir(os.path.join(BASE_PATH, "compositions")):
    if file.endswith(".json"):
        with open(
            os.path.join(BASE_PATH, "compositions", file), "r", encoding="utf-8"
        ) as f:
            data = json.load(f)
            line = {}
            line["id"] = data["pk"]
            line["title"] = data["title"]
            line["anonymous"] = data["anonymous"]
            line["genres"] = ";".join(data["genres"])
            for composer in data["composers"]:
                composer_id = int(composer["url"].split("/")[-2])
                relations.add(
                    HashableDict(
                        {
                            "key1": f"composition:{line['id']}",
                            "key2": f"people:{composer_id}",
                            "type": "",
                        }
                    )
                )
            for source in data["sources"]:
                source_id = int(source["url"].split("/")[-2])
                relations.add(
                    HashableDict(
                        {
                            "key1": f"composition:{line['id']}",
                            "key2": f"source:{source_id}",
                            "type": "",
                        }
                    )
                )
            rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "compositions.csv"), index=False)
print("Finished processing compositions")

# Organizations
print("Starting to process organizations")
rows = []
for organization in os.listdir(os.path.join(BASE_PATH, "organizations")):
    if organization.endswith(".json"):
        with open(
            os.path.join(BASE_PATH, "organizations", organization),
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)
            line = {}
            line["id"] = data["pk"]
            line["name"] = data["name"]
            line["organization_type"] = data["organization_type"]
            line["city"] = line["country"] = ""
            if "location" in data:
                if data["location"]["parent"].lower() != "none":
                    line["country"] = data["location"]["parent"]
                    line["city"] = data["location"]["name"]
                else:
                    line["country"] = data["location"]["name"]
            for source in data["related_sources"]:
                source_id = int(source["url"].split("/")[-2])
                relations.add(
                    HashableDict(
                        {
                            "key1": f"organization:{line['id']}",
                            "key2": f"source:{source_id}",
                            "type": "related",
                        }
                    )
                )
            for source in data["copied_sources"]:
                source_id = int(source["url"].split("/")[-2])
                relations.add(
                    HashableDict(
                        {
                            "key1": f"organization:{line['id']}",
                            "key2": f"source:{source_id}",
                            "type": "copied",
                        }
                    )
                )
            for source in data["source_provenance"]:
                source_id = int(source["url"].split("/")[-2])
                relations.add(
                    HashableDict(
                        {
                            "key1": f"organization:{line['id']}",
                            "key2": f"source:{source_id}",
                            "type": "provenance",
                        }
                    )
                )
            rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "organizations.csv"), index=False)
print("Finished processing organizations")

# People
print("Starting to process people")
rows = []
for file in os.listdir(os.path.join(BASE_PATH, "people")):
    if file.endswith(".json"):
        with open(os.path.join(BASE_PATH, "people", file), "r", encoding="utf-8") as f:
            data = json.load(f)
            line = {}
            line["id"] = data["pk"]
            name_match = PERSON_NAME_DATE_REGEX.match(data["full_name"])
            line["full_name"] = name_match.group(1) if name_match else data["full_name"]
            line["variant_names"] = ", ".join(data["variant_names"])
            line["earliest_year"] = (
                data["earliest_year"] if "earliest_year" in data else ""
            )
            line["latest_year"] = data["latest_year"] if "latest_year" in data else ""
            line["earliest_year_approximate"] = (
                data["earliest_year_approximate"]
                if "earliest_year_approximate" in data
                else ""
            )
            line["latest_year_approximate"] = (
                data["latest_year_approximate"]
                if "latest_year_approximate" in data
                else ""
            )
            for composition in data["compositions"]:
                composition_id = int(composition["url"].split("/")[-2])
                composition_dict = HashableDict(
                    {
                        "key1": f"composition:{composition_id}",
                        "key2": f"people:{line['id']}",
                        "type": "",
                    }
                )
                if composition_dict not in relations:
                    relations.add(composition_dict)
            for source in data["related_sources"]:
                source_id = int(source["url"].split("/")[-2])
                relations.add(
                    HashableDict(
                        {
                            "key1": f"people:{line['id']}",
                            "key2": f"source:{source_id}",
                            "type": "related",
                        }
                    )
                )
            for source in data["copied_sources"]:
                source_id = int(source["url"].split("/")[-2])
                relations.add(
                    HashableDict(
                        {
                            "key1": f"people:{line['id']}",
                            "key2": f"source:{source_id}",
                            "type": "copied",
                        }
                    )
                )
            rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "people.csv"), index=False)
print("Finished processing people")

# Sets
print("Starting to process sets")
rows = []
for file in os.listdir(os.path.join(BASE_PATH, "sets")):
    if file.endswith(".json"):
        with open(os.path.join(BASE_PATH, "sets", file), "r", encoding="utf-8") as f:
            data = json.load(f)
            line = {}
            line["id"] = data["pk"]
            line["type"] = data["type"]
            line["cluster_shelfmark"] = data["cluster_shelfmark"]
            line["description"] = data["description"] if "description" in data else ""
            for archive in data["holding_archives"]:
                archive_id = int(archive["url"].split("/")[-2])
                archive_dict = HashableDict(
                    {
                        "key1": f"archive:{archive_id}",
                        "key2": f"set:{line['id']}",
                        "type": "",
                    }
                )
                if archive_dict not in relations:
                    relations.add(archive_dict)
            for source in data["sources"]:
                source_id = int(source["url"].split("/")[-2])
                relations.add(
                    HashableDict(
                        {
                            "key1": f"set:{line['id']}",
                            "key2": f"source:{source_id}",
                            "type": "",
                        }
                    )
                )
            rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "sets.csv"), index=False)
print("Finished processing sets")

# Sources
print("Starting to process sources")
rows = []
for file in os.listdir(os.path.join(BASE_PATH, "sources")):
    if file.endswith(".json"):
        with open(os.path.join(BASE_PATH, "sources", file), "r", encoding="utf-8") as f:
            data = json.load(f)
            line = {}
            line["id"] = data["pk"]
            line["display_name"] = data["display_name"]
            line["shelfmark"] = data["shelfmark"]
            line["source_type"] = data["source_type"] if "source_type" in data else ""
            for composition in data["inventory"]:
                if "url" in composition:
                    composition_id = int(composition["url"].split("/")[-2])
                    composition_dict = HashableDict(
                        {
                            "key1": f"composition:{composition_id}",
                            "key2": f"source:{line['id']}",
                            "type": "",
                        }
                    )
                    if composition_dict not in relations:
                        relations.add(composition_dict)
            archive_id = int(data["archive"]["url"].split("/")[-2])
            archive_dict = HashableDict(
                {
                    "key1": f"archive:{archive_id}",
                    "key2": f"source:{line['id']}",
                    "type": "",
                }
            )
            if archive_dict not in relations:
                relations.add(archive_dict)
            for source_set in data["sets"]:
                source_set_id = int(source_set["url"].split("/")[-2])
                set_dict = HashableDict(
                    {
                        "key1": f"set:{source_set_id}",
                        "key2": f"source:{line['id']}",
                        "type": "",
                    }
                )
                if set_dict not in relations:
                    relations.add(set_dict)
            rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "sources.csv"), index=False)
print("Finished processing sources")

# Write relations to CSV
df = pd.DataFrame(HashableDict.to_list_of_dicts(relations))
df.to_csv(os.path.join(BASE_CSV_PATH, "relations.csv"), index=False)
print("Finished writing relations")
