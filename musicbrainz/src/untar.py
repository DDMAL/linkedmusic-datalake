"""
unzip the downloaded .tar.xz files into linkedmusic-datalake/musicbrainz/data/raw/extracted_jsonl
"""

import glob
import tarfile
import os
import argparse
import concurrent.futures


def extract_single_file(filepath, dest_folder):
    print(f"Extracting {filepath} to {dest_folder}")
    with tarfile.open(filepath, "r:xz") as tar:
        for member in tar.getmembers():
            if member.name.startswith("mbdump"):
                tar.extract(member, path=dest_folder)
                original_file_path = os.path.join(dest_folder, member.name)
                new_file_path = original_file_path + ".jsonl"
                os.rename(original_file_path, new_file_path)
    print(f"Extracted {filepath} to {dest_folder}")


def extract_file_multithread(folderpath, dest_folder):
    filepaths = glob.glob(f"{folderpath}/*.tar.xz", recursive=False)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(lambda fp: extract_single_file(fp, dest_folder), filepaths)


parser = argparse.ArgumentParser(
    description="Extract tar.xz files to destination folder."
)
parser.add_argument(
    "--input_folder",
    type=str,
    default="../data/raw/archived",
    help="Folder containing archived .tar.xz files",
)
parser.add_argument(
    "--output_folder",
    type=str,
    default="../data/raw/extracted_jsonl",
    help="Folder where files will be extracted as .jsonl",
)
args = parser.parse_args()

INPUT_FOLDER = os.path.abspath(args.input_folder)
OUTPUT_FOLDER = args.output_folder

if not os.path.exists(INPUT_FOLDER):
    print(f"Input folder {INPUT_FOLDER} does not exist.")
    exit(1)

# create the folder if it does not exist
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

extract_file_multithread(INPUT_FOLDER, OUTPUT_FOLDER)
