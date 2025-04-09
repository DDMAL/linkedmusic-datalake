"""
unzip the downloaded .tar.xz files into linkedmusic-datalake/data/musicbrainz/raw
"""

import glob
import tarfile
import os


def extract_file(folderpath, dest_folder):
    """
    untar the downloaded files
    """
    for filepath in glob.glob(f"{folderpath}/*.tar.xz", recursive=False):
        with tarfile.open(f"{filepath}", "r:xz") as tar:
            for member in tar.getmembers():
                # in the tar file, we only need the dumps in this folder.
                # Other files contains unnecessary info.
                if member.name.startswith("mbdump"):
                    tar.extract(member, path=dest_folder)
                    # Get the original file path after extraction
                    original_file_path = os.path.join(dest_folder, member.name)

                    # Create a new file path with .jsonl extension
                    new_file_path = original_file_path + ".jsonl"

                    # Rename the file to add .jsonl extension
                    os.rename(original_file_path, new_file_path)
        print(f"Extracted {filepath} to {dest_folder}")


INPUT_FOLDER = os.path.abspath("./data/musicbrainz/raw/archived/")
DEST_FOLDER = "./data/musicbrainz/raw/extracted_jsonl/"

if not os.path.exists(INPUT_FOLDER):
    print(f"Input folder {INPUT_FOLDER} does not exist.")
    exit(1)

# create the folder if it does not exist
if not os.path.exists(DEST_FOLDER):
    os.makedirs(DEST_FOLDER)

extract_file(INPUT_FOLDER, DEST_FOLDER)
