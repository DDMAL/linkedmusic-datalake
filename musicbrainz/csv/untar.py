import glob
import tarfile

def extract_file(folderpath, dest_folder):
    """
    untar the downloaded files
    """
    for filepath in glob.glob(f"{folderpath}/*.csv", recursive=False):
        with tarfile.open(f"{filepath}", "r:xz") as tar:
            for member in tar.getmembers():
                if member.name.startswith("mbdump"):
                    tar.extractall(path=dest_folder)
        print(f"Extracted {filepath} to {dest_folder}")
    

DEST_FOLDER = "../data/raw"
        
extract_file(DEST_FOLDER, DEST_FOLDER + "/extracted_jsonl")