"""
Extracts all tar.zst files from the AcousticBrainz dataset.
"""

import tarfile
import os
import zstandard as zstd

BASE_PATH = "../../data/acousticbrainz/raw/"
OUTPUT_PATH = "../../data/acousticbrainz/extracted/"


def extract_tar_files(folder_name):
    """
    Extracts all tar.zst files from the specified input path to the output path.
    It will only extract files contained within the specified folder.
    """
    input_path = os.path.join(BASE_PATH, folder_name)

    for filename in os.listdir(input_path):
        if filename.endswith(".tar.zst"):
            file_path = os.path.join(input_path, filename)
            print(f"Extracting {file_path} to {OUTPUT_PATH}")
            with open(file_path, "rb") as compressed_file:
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(compressed_file) as reader:
                    with tarfile.open(fileobj=reader, mode="r|") as tar:
                        for member in tar:
                            if "COPYING" in member.name:
                                continue
                            if member.isfile():
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


if __name__ == "__main__":
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    extract_tar_files("highlevel")
    extract_tar_files("")
    print("All tar.zst files extracted successfully.")
