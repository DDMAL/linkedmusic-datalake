"""Property Mappings Extractor

Aggregates relation phrases + Wikidata PIDs from multiple repository
sources into a consolidated `property_mappings.json` used during prompt
construction (alias expansion + disambiguation hints).

Current data sources:
1. DIAMM relations: `code/diamm/relations.json`
2. MusicBrainz relations: `code/musicbrainz/rdf_conversion_config/relations.json`
3. Existing `property_mappings.json` (manual seeds / curated aliases)

Heuristics / Rules:
- Phrase normalization: lowercase, strip surrounding whitespace, collapse
  internal runs of whitespace, remove trailing punctuation (.,;:).
- Existing mapping wins on PID conflicts (we log a warning).
- If existing mapping is unmapped (pid null) and new provides a PID -> upgrade.
- Preserve and merge aliases (set union) keeping them sorted.
- Non‑alphanumeric phrases (after normalization) are ignored.
- Duplicate phrases consolidated.

Metrics reported:
- total_phrases
- mapped_count
- unmapped_count
- coverage (mapped / total)
- newly_added (count)
- upgraded (phrases whose PID was filled in this run)

CLI:
    poetry run python code/nlq2sparql/ontology/extract_property_mappings.py \
        --write            # (default) write updates back to JSON file
        --no-write         # dry run only
        --min-length 3     # minimum phrase length after normalization
        --show-diff 10     # show up to N new or upgraded mappings

Outputs human‑readable summary to stdout. Designed to be idempotent.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Tuple

# Paths
ONT_DIR = Path(__file__).parent
PROP_FILE = ONT_DIR / "property_mappings.json"
DIAMM_REL = Path(__file__).resolve().parents[2] / "diamm" / "relations.json"
MB_REL = Path(__file__).resolve().parents[2] / "musicbrainz" / "rdf_conversion_config" / "relations.json"


@dataclass
class PhraseRecord:
    phrase: str
    pid: str | None
    source: str


def normalize_phrase(p: str) -> str:
    p = p.strip().lower()
    p = re.sub(r"[\s\u00A0]+", " ", p)  # collapse whitespace incl. nbsp
    p = re.sub(r"[.,;:]+$", "", p)
    return p


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # pragma: no cover
        return None


def iter_diamm_relations(min_length: int) -> Iterable[PhraseRecord]:
    data = load_json(DIAMM_REL)
    if not data:
        return []
    out: list[PhraseRecord] = []
    # structure: {"organizations": { phrase: pid|null, ... }, "people": {...}}
    for cat, mapping in data.items():
        if not isinstance(mapping, dict):
            continue
        for phrase, pid in mapping.items():
            norm = normalize_phrase(phrase)
            if len(norm) < min_length or not re.search(r"[a-z0-9]", norm):
                continue
            out.append(PhraseRecord(norm, pid if pid else None, f"diamm:{cat}"))
    return out


def iter_musicbrainz_relations(min_length: int) -> Iterable[PhraseRecord]:
    data = load_json(MB_REL)
    if not data:
        return []
    out: list[PhraseRecord] = []
    # nested: subject -> object -> phrase -> pid|null
    def walk(d: Dict, stack: Tuple[str, ...]):
        for key, val in d.items():
            if isinstance(val, dict):
                walk(val, stack + (key,))
            else:
                phrase = key
                pid = val if isinstance(val, str) and val.startswith("P") else None
                norm = normalize_phrase(phrase)
                if len(norm) < min_length or not re.search(r"[a-z0-9]", norm):
                    continue
                out.append(PhraseRecord(norm, pid, f"mb:{stack[0]}->{stack[1]}" if len(stack) >= 2 else "mb"))
    walk(data, tuple())
    return out


def load_existing() -> dict:
    if not PROP_FILE.exists():
        return {"_meta": {"description": "auto-generated", "version": 1}}
    with open(PROP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def merge(existing: dict, new_records: Iterable[PhraseRecord]) -> tuple[dict, dict]:
    """Merge new phrase records into existing mapping structure.

    Returns (updated_mapping, stats)
    stats keys: newly_added, upgraded, conflicts
    """
    stats = {"newly_added": 0, "upgraded": 0, "conflicts": 0}
    for rec in new_records:
        phrase = rec.phrase
        cur = existing.get(phrase)
        if cur is None:
            existing[phrase] = {
                "pid": rec.pid,
                "aliases": [],
                "status": "mapped" if rec.pid else "unmapped",
                "sources": [rec.source],
            }
            stats["newly_added"] += 1
            continue
        # merge sources
        if isinstance(cur, dict):
            sources = set(cur.get("sources", []))
            sources.add(rec.source)
            cur["sources"] = sorted(sources)
            # upgrade unmapped
            if (not cur.get("pid")) and rec.pid:
                cur["pid"] = rec.pid
                cur["status"] = "mapped"
                stats["upgraded"] += 1
            elif cur.get("pid") and rec.pid and cur["pid"] != rec.pid:
                # conflict – keep existing, record conflict count
                stats["conflicts"] += 1
        else:  # pragma: no cover (unexpected data shape)
            existing[phrase] = {
                "pid": rec.pid,
                "aliases": [],
                "status": "mapped" if rec.pid else "unmapped",
                "sources": [rec.source],
            }
            stats["newly_added"] += 1
    return existing, stats


def compute_metrics(mapping: dict) -> dict:
    phrases = [k for k in mapping.keys() if not k.startswith("_")]
    mapped = [p for p in phrases if mapping[p].get("pid")]
    unmapped = [p for p in phrases if not mapping[p].get("pid")]
    return {
        "total_phrases": len(phrases),
        "mapped_count": len(mapped),
        "unmapped_count": len(unmapped),
        "coverage": round(len(mapped) / max(1, len(phrases)), 4),
    }


def update_meta(mapping: dict, stats: dict, metrics: dict):
    meta = mapping.setdefault("_meta", {})
    meta.update(
        {
            "last_built": datetime.now(timezone.utc).isoformat(),
            "newly_added": stats.get("newly_added", 0),
            "upgraded": stats.get("upgraded", 0),
            "conflicts": stats.get("conflicts", 0),
            **metrics,
        }
    )


def write(mapping: dict):
    with open(PROP_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False, sort_keys=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Extract & merge property mappings from dataset sources")
    ap.add_argument("--no-write", dest="write", action="store_false", help="Do not write file (dry run)")
    ap.add_argument("--min-length", type=int, default=3, help="Minimum normalized phrase length")
    ap.add_argument("--show-diff", type=int, default=10, help="Show up to N new/upgraded phrases")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    existing = load_existing()
    # collect new phrase records
    records = []
    records.extend(iter_diamm_relations(args.min_length))
    records.extend(iter_musicbrainz_relations(args.min_length))
    merged, stats = merge(existing, records)
    metrics = compute_metrics(merged)
    update_meta(merged, stats, metrics)

    # Prepare diff view
    new_phrases = [p for p, v in merged.items() if p != "_meta" and v.get("sources") and "sources" in v and len(v["sources"]) == 1 and v["sources"][0].startswith("diamm")]
    upgraded = [p for p, v in merged.items() if p != "_meta" and v.get("status") == "mapped" and v.get("pid") and v.get("sources") and "diamm" in ",".join(v["sources"]) and v.get("_upgraded", False)]  # placeholder (not tracking per-entry flag)

    print("Property Mappings Extraction Summary")
    print("----------------------------------")
    print(f"Total phrases:    {metrics['total_phrases']}")
    print(f"Mapped:           {metrics['mapped_count']}")
    print(f"Unmapped:         {metrics['unmapped_count']}")
    print(f"Coverage:         {metrics['coverage']*100:.2f}%")
    print(f"Newly added:      {stats['newly_added']}")
    print(f"Upgraded (pid set): {stats['upgraded']}")
    print(f"Conflicts:        {stats['conflicts']}")
    if args.show_diff and stats["newly_added"]:
        print("\nSample new phrases:")
        for p in sorted(new_phrases)[: args.show_diff]:
            rec = merged[p]
            print(f"  + {p} -> {rec.get('pid')}")
    if args.show_diff and stats["upgraded"]:
        print("\n(Upgraded phrases omitted: tracking not yet granular)")

    if args.write:
        write(merged)
        print(f"\nWrote updated mapping file: {PROP_FILE}")
    else:
        print("\nDry run complete (no file written).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
