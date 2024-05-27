# This file converts a JSON Lines file from MusicBrainz to a CSV file
# For OpenRefine Reconciling
# Input file can be downloaded in
# https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/20240522-001002/
# Output file can be imported to OpenRefine
import json
import copy

header = ["id"]
values = []

with open("test2", "r") as f:
    json_data = [json.loads(m) for m in f]

# print(json_data)


def extract(data, value: dict, first_level: bool = True, key: str = ""):
    if key != "":
        first_level = False
    if "relations" in key or "aliases" in key or "tags" in key:
        # ignore relations and aliases to make output simplier
        return

    if isinstance(data, dict):
        if first_level:
            global values
            value = {}
            for k in data:
                extract(data[k], value, False, k)
            values.append(copy.deepcopy(value))
            value = {}

        else:
            for k in data:
                if k == "id":
                    extract(data["id"], value, first_level, key + "_ids")

                if k == "name":
                    extract(data["name"], value, first_level, key + "_name")

                if isinstance(data[k], dict) or isinstance(data[k], list):
                    extract(data[k], value, first_level, key + "_" + k)

    elif isinstance(data, list):
        rep_count = 0
        for element in data:
            rep_count += 1
            if isinstance(element, dict) and rep_count <= 3:
                if first_level:
                    rep_count = 0
                    extract(element, value, first_level, key)
                else:
                    extract(element, value, first_level, key + str(rep_count))

    else:
        global header
        if key not in header:
            header.append(key)

        if isinstance(data, str):
            data = data.replace(",", "")
            data = data.replace("\r\n", "")

        if data is None:
            data = ""

        value[key] = data
        return


if __name__ == "__main__":
    extract(json_data, {})

    with open("out.csv", "w") as out:
        # write header
        line = "id,"
        header.sort(key=len)
        for column in header:
            if column == "id":
                continue

            line += column

            if column != header[-1]:
                line += ","

        out.writelines(line)
        out.writelines("\n")

        line = ""
        for row in values:
            for column in header:
                if column in row:
                    line += str(row[column])

                if column != header[-1]:
                    line += ","
                else:
                    line += "\n"

        out.writelines(line)
