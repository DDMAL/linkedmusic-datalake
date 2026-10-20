"""Draw a reproducible stratified review sample from a supplied complete JSON frame."""

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def select(frame, quotas, seed):
    if frame.get("complete") is not True:
        raise ValueError(
            "A complete frozen frame is required, not a LIMIT query sample"
        )
    if not frame.get("provenance"):
        raise ValueError("Frame provenance is required")
    groups = defaultdict(list)
    seen = set()
    for row in frame["units"]:
        key = row["id"]
        if not isinstance(key, str) or not key or key in seen:
            raise ValueError("Frame IDs must be nonempty, unique strings")
        seen.add(key)
        if type(row["linked"]) is not bool:
            raise ValueError("linked must be a boolean")
        if row["linked"] and not row.get("target"):
            raise ValueError("Linked units require a target")
        for field in ("dataset", "entity_type", "method", "source_locator"):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ValueError(f"Missing frame field: {field}")
        # One source entity is one unit. Multi-target links go into target as a list.
        stratum = "|".join(
            (
                row["dataset"],
                row["entity_type"],
                row["method"],
                str(row["linked"]).lower(),
            )
        )
        groups[stratum].append(row)
    if set(quotas) != set(groups):
        raise ValueError("Quotas must cover every observed stratum exactly")
    selected, summary = [], []
    for stratum, rows in sorted(groups.items()):
        size = quotas[stratum]
        if type(size) is not int or not 1 <= size <= len(rows):
            raise ValueError(f"Quota outside 1..N for {stratum}")
        # Hash priority is deterministic under input reordering. Record the seed
        # before inspecting outcomes; changing it to select desired cases is invalid.
        ordered = sorted(
            rows,
            key=lambda row: (
                hashlib.sha256(
                    json.dumps([seed, stratum, row["id"]]).encode()
                ).hexdigest(),
                row["id"],
            ),
        )
        summary.append({"stratum": stratum, "N": len(rows), "n": size})
        for row in ordered[:size]:
            selected.append(
                {
                    **row,
                    "stratum": stratum,
                    "inclusion_probability": size / len(rows),
                    "identifier_agreement": "unreviewed",
                    "identity_verdict": "unreviewed",
                    "missed_link_verdict": "unreviewed",
                    "evidence": [],
                    "reviewer": None,
                    "reviewed_at_utc": None,
                }
            )
    return {"strata": summary, "selected": selected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--quotas", type=Path, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frame_bytes, quota_bytes = args.frame.read_bytes(), args.quotas.read_bytes()
    try:
        result = select(json.loads(frame_bytes), json.loads(quota_bytes), args.seed)
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    result.update(
        selected_at_utc=datetime.now(timezone.utc).isoformat(),
        seed=args.seed,
        selection="SHA-256 priority within strata; no replacement",
        frame_sha256=hashlib.sha256(frame_bytes).hexdigest(),
        quotas_sha256=hashlib.sha256(quota_bytes).hexdigest(),
        sampler_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        frame_provenance=json.loads(frame_bytes)["provenance"],
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(f"Selected {len(result['selected'])} units in {len(result['strata'])} strata")


if __name__ == "__main__":
    main()
