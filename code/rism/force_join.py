import os 
import re 

def convert_uris_to_blank_nodes(ntriples_str):
    return re.sub(r'<http://dummy.org/bnode/([a-zA-Z0-9]+)>', lambda m: f'_:{m.group(1)}', ntriples_str)

def force_join_ttl(input_dir, output_file):
    with open(output_file, "wb") as outfile:
        for file in os.listdir(input_dir):
            with open(os.path.join(input_dir, file), "rb") as infile:
                for line in infile:
                    line = convert_uris_to_blank_nodes(line.decode("utf-8"))
                    line = line.encode("utf-8")
                    outfile.write(line)

if __name__ == "__main__":
    input_dir = "../data/split_input"  # Replace with your input directory
    output_file = "../data/joined_output.ttl"  # Replace with your desired output file
    force_join_ttl(input_dir, output_file)