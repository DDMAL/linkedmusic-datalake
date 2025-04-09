import os
import concurrent.futures
import glob
import argparse


def split_jsonl_file(input_file, output_dir, chunk_size_mb=300):
    """
    Split a single JSON Lines file into chunks of specified size

    Args:
        input_file (str): Input JSONL file path
        output_dir (str): Output directory for chunks
        chunk_size_mb (int): Approximate size of each chunk (MB)
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get the base filename without extension
    base_name = os.path.basename(input_file)
    file_name_without_ext = os.path.splitext(base_name)[0]

    # Calculate chunk size in bytes
    chunk_size_bytes = chunk_size_mb * 1024 * 1024

    chunk_num = 1
    current_size = 0
    current_chunk = []

    # Open the input file and read line by line
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line_size = len(line.encode("utf-8"))
            current_size += line_size
            current_chunk.append(line)

            # If the current chunk exceeds the target size, write to file
            if current_size >= chunk_size_bytes:
                output_file = os.path.join(
                    output_dir, f"{file_name_without_ext}_{chunk_num}.jsonl"
                )
                with open(output_file, "w", encoding="utf-8") as out_f:
                    out_f.writelines(current_chunk)

                print(
                    f"Created {output_file}, size: {current_size / (1024 * 1024):.2f} MB"
                )

                # Reset for the next chunk
                chunk_num += 1
                current_size = 0
                current_chunk = []

        # If there's remaining data, write to the last chunk
        if current_chunk:
            output_file = os.path.join(
                output_dir, f"{file_name_without_ext}_{chunk_num}.jsonl"
            )
            with open(output_file, "w", encoding="utf-8") as out_f:
                out_f.writelines(current_chunk)

            print(f"Created {output_file}, size: {current_size / (1024 * 1024):.2f} MB")


def process_files(input_files, output_dir, chunk_size_mb=300):
    """
    Process multiple files using a thread pool

    Args:
        input_files (list): List of input file paths
        output_dir (str): Output directory for chunks
        chunk_size_mb (int): Approximate size of each chunk (MB)
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit all files to the thread pool
        futures = [
            executor.submit(split_jsonl_file, file_path, output_dir, chunk_size_mb)
            for file_path in input_files
        ]

        # Wait for all threads to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing file: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Split multiple JSON Lines files into smaller chunks"
    )
    parser.add_argument(
        "--input", required=True, help="Input directory or glob pattern for JSONL files"
    )
    parser.add_argument(
        "--output",
        default="chunks",
        help="Output directory for chunks (default: chunks)",
    )
    parser.add_argument(
        "--chunk-size", type=int, default=300, help="Chunk size in MB (default: 300)"
    )

    args = parser.parse_args()

    # Get list of input files
    if os.path.isdir(args.input):
        input_files = list(glob.glob(os.path.join(args.input, "*.jsonl")))
    else:
        input_files = list(glob.glob(args.input))

    if not input_files:
        print(f"No matching JSONL files found: {args.input}")
        return

    print(f"Found {len(input_files)} files to process")

    # Process files
    process_files(input_files, args.output, args.chunk_size)
    print("All files processed")


if __name__ == "__main__":
    main()
