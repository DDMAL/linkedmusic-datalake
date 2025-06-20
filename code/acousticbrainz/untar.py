"""
Extracts all tar.zst files from the AcousticBrainz dataset.
All JSON files are sent to JSONL files, separated by the first 2 hexadecimal
characters of the MBID.
"""

import tarfile
import os
import json
import zstandard as zstd

BASE_PATH = "../../data/acousticbrainz/raw/"
OUTPUT_PATH = "../../data/acousticbrainz/extracted/"


def extract_tar_files(folder_name):
    """
    Extracts all tar.zst files from the specified input path to the output path.
    It will only extract files contained within the specified folder.
    """
    input_path = os.path.join(BASE_PATH, folder_name)

    try:
        jsonl_files = []
        versions = {}
        if folder_name:  # Assume that the file contains JSON files
            os.makedirs(os.path.join(OUTPUT_PATH, folder_name), exist_ok=True)
            jsonl_files = [
                open(
                    os.path.join(OUTPUT_PATH, folder_name, f"{i:02x}.jsonl"),
                    "w",
                    encoding="utf-8",
                )
                for i in range(256)
            ]

        for filename in os.listdir(input_path):
            if not filename.endswith(".tar.zst"):
                continue
            file_path = os.path.join(input_path, filename)
            print(f"Extracting {file_path} to {OUTPUT_PATH}")
            with open(file_path, "rb") as compressed_file:
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(compressed_file) as reader:
                    with tarfile.open(fileobj=reader, mode="r|") as tar:
                        for member in tar:
                            if "COPYING" in member.name:
                                continue
                            if not member.isfile():
                                continue
                            if member.name.endswith(".json"):
                                *mbid, version = (
                                    member.name.split("/")[-1].split(".")[0].split("-")
                                )
                                mbid = "-".join(mbid)
                                version = int(version)
                                # Only add the file to the JSONL file if the version is higher
                                # than the one already stored for this MBID
                                if versions.get(mbid, -1) < version:
                                    versions[mbid] = version
                                    file = int(member.name.split("/")[-1][:2], base=16)
                                    with tar.extractfile(member) as extracted_file:
                                        data = json.load(extracted_file)
                                        data["submission_number"] = version
                                        jsonl_files[file].write(
                                            json.dumps(data, ensure_ascii=False) + "\n"
                                        )
                            else:
                                new_filename = os.path.join(
                                    OUTPUT_PATH, *member.name.split("/")[1:]
                                )
                                os.makedirs(
                                    os.path.dirname(new_filename), exist_ok=True
                                )
                                with tar.extractfile(member) as extracted_file, open(
                                    new_filename, "wb"
                                ) as out_file:
                                    out_file.write(extracted_file.read())

    finally:
        for jsonl_file in jsonl_files:  # Close all JSONL files if they were opened
            jsonl_file.close()

        if versions:
            with open(
                os.path.join(OUTPUT_PATH, folder_name, "versions.json"),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(versions, f, ensure_ascii=False)


if __name__ == "__main__":
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    extract_tar_files("highlevel")
    extract_tar_files("")
    print("All tar.zst files extracted successfully.")
