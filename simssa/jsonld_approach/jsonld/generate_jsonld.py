import pandas as pd
import json
import re

df = pd.read_csv("../flattening/final_flattened.csv")
# for column in df.columns:
#     if "@id" in column and df[column].dtype == "object":
#         # Try to convert the values to integers, set to NaN if conversion fails
#         df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")


json_data = df.to_json(orient="records")
parsed_json_flattened = json.loads(json_data)
# pretty_json = json.dumps(parsed_json, indent=4)
# with open('gen_json.json', 'w') as json_file:
#     json_file.write(pretty_json)

df = pd.read_csv("../flattening/reconciled_files_WikiID.csv")
json_data = df.to_json(orient="records")
parsed_json_compact_files = json.loads(json_data)


files_keys = [
    "file_format_1",
    "file_format_2",
    "file_format_3",
    "file_format_4",
    "file_format_1_@id",
    "file_format_2_@id",
    "file_format_3_@id",
    "file_format_4_@id",
    "url_to_file_1",
    "url_to_file_2",
    "url_to_file_3",
    "url_to_file_4",
    # "Last_Pitch_Class_1", "Last_Pitch_Class_2", "Last_Pitch_Class_3", "Last_Pitch_Class_4"
]


# Create a nested list of dictionaries
def handle_rec_col(work, key):
    val = work.pop(key)
    wID = work.pop(f"{key}_@id")
    if val is None:
        return None
    if re.match(r"^[Q]\d+", wID):  # if cell was reconciled with wikidata
        # work["@context"].append({key:f"wdt:{name_wID}"}) # overwrite context
        return {"@id": f"wd:{wID}", "name": val}

    if val[:8] == "https://":  # if cell was reconciled with another source
        return {"@id": val}
    else:  # cell is value
        # work["@context"].append({key:f"wdt:{wID}"}) # overwrite context
        return val

def handle_file_integration(work_id):
    """
    Integrates file data for a given musical work ID.

    This function filters and processes file-related data from the global
    `parsed_json_compact_files` list, matching entries based on the provided
    `work_id`. It constructs a list of dictionaries, each representing a file
    with its associated metadata.

    Args:
        work_id (int): The unique identifier for a musical work.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary contains:
            - "@id" (str): The URL or identifier of the file.
            - "file_type" (str): The type of the file.
            - "file_format" (dict or str): The file format, processed by `handle_rec_col`.
            - "file_version" (str): The version of the file.
    """
    files = []
    for f in parsed_json_compact_files:
        if f["musical_work_id"] == work_id:
            files.append(
                {
                    "@id": f.pop("url_to_file"),
                    "file_type": f.pop("file_type"),
                    "file_format": handle_rec_col(f, "file_format"),
                    "file_version": f.pop("file_version"),
                }
            )
    return files


for work in parsed_json_flattened:
    for k in work:
        if "id" in k:
            if type(work[k]) is float:
                work[k] = int(work[k])


for work in parsed_json_flattened:
    work["@context"] = "https://raw.githubusercontent.com/ddmal/linkedmusic-datalake/main/simssa/jsonld_approach/jsonld/context.jsonld"
    work["database"] = "simssadb:"
    work["@type"] = "wd:Q2188189"
    work_id = work.pop('musical_work_id')
    work["@id"] = f"mw:{work_id}"

    # work["composer"] =  handle_rec_col(work,"composer")
    work["genre_style"] = handle_rec_col(work, "genre_style")
    work["genre_type"] = handle_rec_col(work, "genre_type")
    work["author_name"] = handle_rec_col(work, "author_name")
    work["composer_name"] = handle_rec_col(work, "composer_name")

    work["files"] = handle_file_integration(work_id)

    author_id = work.pop("author_contribution_id")
    work["author"] = {
        "@id": f"https://db.simssa.ca/contributions/{author_id}",
        "author_name": work.pop("author_name"),
        "author_viaf_id": work.pop("author_viaf_id")
    }

    composer_id = work.pop("composer_contribution_id")
    work["composer"] = {
        "@id": f"https://db.simssa.ca/contributions/{composer_id}",
        "composer_name": work.pop("composer_name"),
        "composer_viaf_id": work.pop("composer_viaf_id")
    }

    work["source"] = {
        "@id": f'https://db.simssa.ca/sources/{work.pop("source_id")}',
        "source_title": work.pop("source_title"),
        "source_type": work.pop("source_type"),
        "source_url": work.pop("source_url"),
    }

## Rearrange
## files
# nested_list = []
# for i in range(1, 5):
#     file_format_key = f"file_format_{i}"
#     url_key = f"url_to_file_{i}"
#     # last_pitch_key = f"Last_Pitch_Class_{i}"

#     file_format = work.get(file_format_key, None)
#     url = work.get(url_key, None)
#     # last_pitch = work.get(last_pitch_key, None)
#     if url is None:
#         continue
#     nested_list.append(
#         {
#             "@type": "simssadb_file",
#             "@id": url,
#             # 'P2701': f'wd:{file_format}',
#             "file_format": handle_rec_col(
#                 {
#                     "file_format": file_format,
#                     "file_format_@id": work[f"file_format_{i}_@id"],
#                 },
#                 "file_format",
#             ),
#             # "Last_Pitch_Class": last_pitch,
#         }
#     )
# work["files"] = nested_list

# # Contributors
# contri_list = []
# for i in range(1, 5):
#     file_format_key = f"file_format_{i}"

#     file_format = work.get(file_format_key, None)
#     url = work.get(url_key, None)
#     last_pitch = work.get(last_pitch_key, None)
#     if url is None:
#         continue
#     nested_list.append(
#         {
#             "@type": "simssadb_file",
#             "@id": url,
#             # 'P2701': f'wd:{file_format}',
#             "file_format": handle_rec_col(
#                 {
#                     "file_format": file_format,
#                     "file_format_@id": work[f"file_format_{i}_@id"],
#                 },
#                 "file_format",
#             ),
#             "Last_Pitch_Class": last_pitch,
#         }
#     )
# work['contributors'] = contri_list
# for col in files_keys:
#     del work[col]
# Print the nested list of dictionaries
pretty_json = json.dumps(parsed_json_flattened, indent=4)
with open("compact.jsonld", "w") as json_file:
    json_file.write(pretty_json)
