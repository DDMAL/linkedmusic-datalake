import glob
import tarfile

def extract_file(folderpath, dest_folder):
    """
    untar the downloaded files
    """
    for filepath in glob.glob(folderpath, recursive=False):
        if filepath.endswith(".tar.xz"):
            with tarfile.open(f"{filepath}/mbdump/", "r:xz") as tar:
                tar.extractall(path=dest_folder)
            print(f"Extracted {filepath} to {dest_folder}")
    

DEST_FOLDER = "../data/raw"
        
extract_file(DEST_FOLDER, DEST_FOLDER + "/jsonl")
