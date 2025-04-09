import pandas as pd
import json
import re

df = pd.read_csv("../flattening/final_flattened.csv")
# for column in df.columns:
#     if "@id" in column and df[column].dtype == "object":
#         # Try to convert the values to integers, set to NaN if conversion fails
#         df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")


json_data = df.to_json(orient="records")
parsed_json = json.loads(json_data)
# pretty_json = json.dumps(parsed_json, indent=4)
# with open('gen_json.json', 'w') as json_file:
#     json_file.write(pretty_json)


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


for work in parsed_json:
    for k in work:
        if "id" in k:
            if type(work[k]) is float:
                work[k] = int(work[k])


for work in parsed_json:
    work["@context"] = "https://raw.githubusercontent.com/malajvan/linkedmusic-datalake/main/simssadb/jsonld/context.jsonld"
    work["database"] = "simssadb:"
    work["@type"] = "wd:Q2188189"
    work["@id"] = f"mw:{work.pop('musical_work_id')}"

    # work["composer"] =  handle_rec_col(work,"composer")
    work["genre_style"] = handle_rec_col(work, "genre_style")
    work["genre_type"] = handle_rec_col(work, "genre_type")
    #### testing
    work["file_format"] = handle_rec_col(work, "file_format")
    work["contributor_role"] = handle_rec_col(work, "contributor_role")
    work["contributor_name"] = handle_rec_col(work, "contributor_name")

    work["files"] = {
        "@id": work.pop("url_to_file"),
        "file_type": work.pop("file_type"),
        "file_format": work.pop("file_format"),
        "file_version": work.pop("file_version"),
    }

    if work["files"]["@id"] is None:
        del work["files"]

    contribution_id = work.pop("contribution_id")
    work["contributor"] = {
        "@id": f"https://db.simssa.ca/contributions/{contribution_id}",
        "contributor_role": work.pop("contributor_role"),
        "contributor_name": work.pop("contributor_name"),
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
pretty_json = json.dumps(parsed_json, indent=4)
with open("compact.jsonld", "w") as json_file:
    json_file.write(pretty_json)
