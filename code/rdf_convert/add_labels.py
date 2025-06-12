import asyncio
import sys
from typing import List, Tuple
from pathlib import Path
import aiohttp
# Add the parent directory (code/) to sys.path
sys.path.append(str(Path(__file__).parent.parent))
from wikidata_utils import extract_wd_id, WikidataAPIClient

# Add the parent directory (code/) to sys.path
sys.path.append(str(Path(__file__).parent.parent))


async def add_labels(input_path: Path, output_path: Path, client: WikidataAPIClient):
    lines: List[Tuple[str, str]] = []
    ids: List[str] = []

    # Read lines & extract last Wikidata ID per line
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            wd_id: str = extract_wd_id(line)
            lines.append((line, wd_id))
            if wd_id:
                ids.append(wd_id)

    # Remove duplicates
    unique_ids = list(set(ids))

    # Fetch labels in batch
    labels_list = await client.wbgetentities(unique_ids, props="labels", languages="en")
    labels_dict = {
        item["id"]: item["labels"] for item in labels_list if "labels" in item
    }

    # Write output with labels as comments
    with open(output_path, "w", encoding="utf-8") as f_out:
        for line, wd_id in lines:
            label = labels_dict.get(wd_id, "")
            if label:
                f_out.write(f"{line}  # {label}({wd_id})\n")
            elif wd_id:
                # If we have a Wikidata ID but no label, write a comment to point it out
                f_out.write(f"{line}  # {wd_id} does not exist \n")
            else:
                f_out.write(line + "\n")


async def main():
    async with aiohttp.ClientSession() as session:
        client = WikidataAPIClient(session=session)
        await add_labels(input_file, output_file, client)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python add_wd_labels.py input.txt output.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    asyncio.run(main())
