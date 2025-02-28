import os
from pathlib import Path


def force_split_ttl(input_file, output_dir, chunk_size_mb=1e3):
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Convert chunk size to bytes
    chunk_size = chunk_size_mb * 1024 * 1024

    # Initialize counters
    file_number = 1
    current_size = 0
    current_file = None
    with open(input_file, "rb") as infile:
        for line in infile:
            # Open new file if needed
            if current_file is None:
                output_path = os.path.join(output_dir, f"part_{file_number}.ttl")
                current_file = open(output_path, "wb")
                current_size = 0

            # Write line to current file
            current_file.write(line)
            current_size += len(line)

            # Check if current file size exceeds chunk_size
            if current_size >= chunk_size:
                current_file.close()
                current_file = None
                file_number += 1

        # Close the last file if it's still open
        if current_file:
            current_file.close()


if __name__ == "__main__":
    input_file = "../data/raw/rism-dump.ttl"  # Replace with your input file
    output_dir = "split_output"  # Replace with your desired output directory
    force_split_ttl(input_file, output_dir)
