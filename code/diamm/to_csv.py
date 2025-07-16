"""
Script to convert the JSON files from the DIAMM dataset into CSV files.
"""

import os
import json
import re
from pathlib import Path
import pandas as pd
from utils import HashableDict

BASE_PATH = "../../data/diamm/raw/"
BASE_CSV_PATH = "../../data/diamm/csv/"

# Regex used to sanitize names to remove any dates
PERSON_NAME_DATE_REGEX = re.compile(
    r"^(.*?)(?:\s*\((?:ca\.|fl\.|–|\d|\d{3,4}).*?\))?\s*$"
)

os.makedirs(BASE_CSV_PATH, exist_ok=True)

# Make the relations set
relations = set()

# Archives
print("Starting to process archives")
rows = []
for file in (Path(BASE_PATH) / "archives").glob("*.json"):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        line = {}
        line["id"] = data["pk"]
        line["name"] = data["name"]
        line["siglum"] = data["siglum"]
        line["website"] = data["website"] if "website" in data else ""
        line["rism_id"] = ""
        for identifier in data["identifiers"]:
            if re.search("RISM", identifier["label"], re.IGNORECASE):
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
        relations.add(
            HashableDict(
                {
                    "key1": f"archive:{line['id']}",
                    "key2": f"city:{data['city']['url'].split('/')[-2]}",
                    "type": "",
                }
            )
        )
        rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "archives.csv"), index=False)
print("Finished processing archives")

# Cities
print("Starting to process cities")
rows = []
for file in (Path(BASE_PATH) / "cities").glob("*.json"):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        line = {}
        line["id"] = data["pk"]
        line["name"] = data["name"]
        line["country"] = data["country"]["name"]
        for archive in data["archives"]:
            archive_id = int(archive["url"].split("/")[-2])
            relations.add(
                HashableDict(
                    {
                        "key1": f"archive:{archive_id}",
                        "key2": f"city:{line['id']}",
                        "type": "",
                    }
                )
            )
        for source in data["provenance"]:
            source_id = int(source["url"].split("/")[-2])
            relations.add(
                HashableDict(
                    {
                        "key1": f"city:{line['id']}",
                        "key2": f"source:{source_id}",
                        "type": "",
                    }
                )
            )
        for organization in data["organizations"]:
            organization_id = int(organization["url"].split("/")[-2])
            relations.add(
                HashableDict(
                    {
                        "key1": f"city:{line['id']}",
                        "key2": f"organization:{organization_id}",
                        "type": "",
                    }
                )
            )
        relations.add(
            HashableDict(
                {
                    "key1": f"city:{line['id']}",
                    "key2": f"country:{data['country']['url'].split('/')[-2]}",
                    "type": "",
                }
            )
        )
        rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "cities.csv"), index=False)
print("Finished processing cities")

# Compositions
print("Starting to process compositions")
rows = []
for file in (Path(BASE_PATH) / "compositions").glob("*.json"):
    with open(file, "r", encoding="utf-8") as f:
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

# Countries
print("Starting to process countries")
rows = []
for file in (Path(BASE_PATH) / "countries").glob("*.json"):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        line = {}
        line["id"] = data["pk"]
        line["name"] = data["name"]
        for city in data["cities"]:
            city_id = int(city["url"].split("/")[-2])
            relations.add(
                HashableDict(
                    {
                        "key1": f"city:{city_id}",
                        "key2": f"country:{line['id']}",
                        "type": "",
                    }
                )
            )
        for region in data["regions"] + data["states"]:
            region_id = int(region["url"].split("/")[-2])
            relations.add(
                HashableDict(
                    {
                        "key1": f"country:{line['id']}",
                        "key2": f"region:{region_id}",
                        "type": "",
                    }
                )
            )
        rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "countries.csv"), index=False)
print("Finished processing countries")

# Organizations
print("Starting to process organizations")
rows = []
for file in (Path(BASE_PATH) / "organizations").glob("*.json"):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        line = {}
        line["id"] = data["pk"]
        line["name"] = data["name"]
        line["organization_type"] = data["organization_type"]
        line["country"] = ""
        if location := data.get("location"):
            if location_url := location.get("url"):
                location_type, location_id = location_url.split("/")[-3:-1]
                if location_type == "cities":
                    relations.add(
                        HashableDict(
                            {
                                "key1": f"city:{location_id}",
                                "key2": f"organization:{line['id']}",
                                "type": "",
                            }
                        )
                    )
                elif location_type == "countries":
                    relations.add(
                        HashableDict(
                            {
                                "key1": f"country:{location_id}",
                                "key2": f"organization:{line['id']}",
                                "type": "",
                            }
                        )
                    )
                    line["country"] = location["name"]
            if not line["country"] and not re.match(
                r"^none$", location["parent"], re.I
            ):
                line["country"] = location["parent"]
        for source in data["related_sources"]:
            source_id = int(source["url"].split("/")[-2])
            relationship_type = source["relationship"]
            relations.add(
                HashableDict(
                    {
                        "key1": f"organization:{line['id']}",
                        "key2": f"source:{source_id}",
                        "type": f"related:{relationship_type}",
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
for file in (Path(BASE_PATH) / "people").glob("*.json"):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        line = {}
        line["id"] = data["pk"]
        name_match = PERSON_NAME_DATE_REGEX.match(data["full_name"])
        line["full_name"] = name_match.group(1) if name_match else data["full_name"]
        line["variant_names"] = ", ".join(data["variant_names"])
        line["earliest_year"] = data["earliest_year"] if "earliest_year" in data else ""
        line["latest_year"] = data["latest_year"] if "latest_year" in data else ""
        line["earliest_year_approximate"] = (
            data["earliest_year_approximate"]
            if "earliest_year_approximate" in data
            else ""
        )
        line["latest_year_approximate"] = (
            data["latest_year_approximate"] if "latest_year_approximate" in data else ""
        )
        line["rism_id"] = line["viaf_id"] = ""
        for identifier in data["identifiers"]:
            if re.search("RISM", identifier["label"], re.IGNORECASE):
                line["rism_id"] = identifier["identifier"]
            elif re.search("VIAF", identifier["label"], re.IGNORECASE):
                line["viaf_id"] = identifier["identifier"]
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
            relationship_type = source["relationship"]
            relations.add(
                HashableDict(
                    {
                        "key1": f"people:{line['id']}",
                        "key2": f"source:{source_id}",
                        "type": f"related:{relationship_type}",
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

# Regions
print("Starting to process regions")
rows = []
for file in (Path(BASE_PATH) / "regions").glob("*.json"):
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        line = {}
        line["id"] = data["pk"]
        line["name"] = data["name"]
        line["country"] = data["parent"]
        for organization in data["organizations"]:
            organization_id = int(organization["url"].split("/")[-2])
            relations.add(
                HashableDict(
                    {
                        "key1": f"organization:{organization_id}",
                        "key2": f"region:{line['id']}",
                        "type": "",
                    }
                )
            )
        for city in data["cities"]:
            city_id = int(city["url"].split("/")[-2])
            relations.add(
                HashableDict(
                    {
                        "key1": f"city:{city_id}",
                        "key2": f"region:{line['id']}",
                        "type": "",
                    }
                )
            )
        for source in data["provenance"]:
            source_id = int(source["url"].split("/")[-2])
            relations.add(
                HashableDict(
                    {
                        "key1": f"region:{line['id']}",
                        "key2": f"source:{source_id}",
                        "type": "",
                    }
                )
            )
        rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "regions.csv"), index=False)
print("Finished processing regions")

# Sets
print("Starting to process sets")
rows = []
for file in (Path(BASE_PATH) / "sets").glob("*.json"):
    with open(file, "r", encoding="utf-8") as f:
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
for file in (Path(BASE_PATH) / "sources").glob("*.json"):
    with open(file, "r", encoding="utf-8") as f:
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
        for relation in data["relationships"]:
            if (rtype := relation.get("relationship_type")) and (
                eurl := relation.get("related_entity", {}).get("url")
            ):
                etype = eurl.split("/")[-3]
                if etype == "people":
                    related_id = int(eurl.split("/")[-2])
                    relations.add(
                        HashableDict(
                            {
                                "key1": f"people:{related_id}",
                                "key2": f"source:{line['id']}",
                                "type": f"related:{rtype}",
                            }
                        )
                    )
                elif etype == "organizations":
                    related_id = int(eurl.split("/")[-2])
                    relations.add(
                        HashableDict(
                            {
                                "key1": f"organization:{related_id}",
                                "key2": f"source:{line['id']}",
                                "type": f"related:{rtype}",
                            }
                        )
                    )
        rows.append(line)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(BASE_CSV_PATH, "sources.csv"), index=False)
print("Finished processing sources")

# Write relations to CSV
df = pd.DataFrame(HashableDict.to_list_of_dicts(relations))
df.to_csv(os.path.join(BASE_CSV_PATH, "relations.csv"), index=False)
print("Finished writing relations")
