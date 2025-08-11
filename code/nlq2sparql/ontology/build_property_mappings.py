"""Skeleton builder for ontology/property_mappings.json."""
from __future__ import annotations

import json
from pathlib import Path
import argparse

MAPPINGS_FILE = Path(__file__).parent / "property_mappings.json"


def load() -> dict:
    if MAPPINGS_FILE.exists():
        with open(MAPPINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"_meta": {"description": "auto-generated", "version": 1}}


def save(data: dict):
    with open(MAPPINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_mapping(data: dict, phrase: str, pid: str | None, *aliases: str):
    entry = data.setdefault(phrase.lower(), {})
    entry.update({
        "pid": pid,
        "aliases": sorted({a.lower() for a in aliases if a}),
        "status": "mapped" if pid else "unmapped",
    })


def main():
    p = argparse.ArgumentParser(description="Update property_mappings.json")
    p.add_argument("phrase")
    p.add_argument("pid", nargs="?")
    p.add_argument("aliases", nargs="*")
    args = p.parse_args()
    data = load()
    add_mapping(data, args.phrase, args.pid, *args.aliases)
    save(data)
    print(f"Updated {MAPPINGS_FILE} with phrase '{args.phrase}' (pid={args.pid})")


if __name__ == "__main__":  # pragma: no cover
    main()
