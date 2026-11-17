"""Draw a reproducible stratified review sample from a supplied complete JSON frame."""

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from manifest import absolute_iri, utc_timestamp

UNIT_FIELDS = (
    "id",
    "dataset",
    "entity_type",
    "method",
    "linked",
    "target",
    "source_locator",
)


def read_json(data):
    def unique_keys(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"Duplicate JSON key: {key}")
            value[key] = item
        return value

    result = json.loads(data, object_pairs_hook=unique_keys)
    # Validate even optional metadata before attempting to create an output.
    json.dumps(result, allow_nan=False)
    return result


def select(frame, quotas, seed):
    if not isinstance(frame, dict):
        raise ValueError("Frame must be an object")
    versions = {
        "schema_version": "1.0",
        "protocol_version": "1.0",
        "manifest_schema_version": "2.0",
    }
    if any(frame.get(key) != value for key, value in versions.items()):
        raise ValueError(
            "Unsupported or missing frame/protocol/manifest schema version"
        )
    if not isinstance(seed, str) or not seed.strip():
        raise ValueError("A nonempty recorded seed is required")
    if frame.get("complete") is not True:
        raise ValueError(
            "A complete frozen frame is required, not a LIMIT query sample"
        )
    provenance = frame.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("Frame provenance is required")
    for field in ("snapshot_sha256", "reconciliation_export_sha256"):
        value = provenance.get(field)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise ValueError(f"Frame provenance requires {field}")
    for field in ("extraction_command", "unit_definition"):
        if not isinstance(provenance.get(field), str) or not provenance[field].strip():
            raise ValueError(f"Frame provenance requires {field}")
    if not isinstance(provenance.get("extracted_at_utc"), str) or not utc_timestamp(
        provenance["extracted_at_utc"]
    ):
        raise ValueError("Frame extraction requires a UTC timestamp")
    if not isinstance(provenance.get("exclusions"), list) or any(
        not isinstance(item, str) for item in provenance["exclusions"]
    ):
        raise ValueError("Frame exclusions must be an explicit list of strings")
    if not isinstance(frame.get("units"), list) or not isinstance(quotas, dict):
        raise ValueError("Frame units must be a list and quotas an object")
    groups = defaultdict(list)
    seen = set()
    for row in frame["units"]:
        if not isinstance(row, dict):
            raise ValueError("Frame unit must be an object")
        if set(row) - set(UNIT_FIELDS):
            raise ValueError(
                "Unknown frame unit fields: "
                + ", ".join(sorted(set(row) - set(UNIT_FIELDS)))
            )
        key = row["id"]
        if not isinstance(key, str) or not key or key in seen:
            raise ValueError("Frame IDs must be nonempty, unique strings")
        seen.add(key)
        if type(row["linked"]) is not bool:
            raise ValueError("linked must be a boolean")
        if "target" not in row:
            raise ValueError("Every unit requires an explicit target set or null")
        target = row["target"]
        targets = [target] if isinstance(target, str) else target
        if row["linked"]:
            if (
                not isinstance(targets, list)
                or not targets
                or any(not isinstance(t, str) or not absolute_iri(t) for t in targets)
                or len(set(targets)) != len(targets)
            ):
                raise ValueError("Linked units require distinct absolute target IRIs")
        elif target is not None and target != []:
            raise ValueError("Unlinked units must have null or empty target sets")
        for field in ("dataset", "entity_type", "method", "source_locator"):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ValueError(f"Missing frame field: {field}")
            if field != "source_locator" and "|" in row[field]:
                raise ValueError("Stratum fields cannot contain '|'")
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
                    **{key: row[key] for key in UNIT_FIELDS},
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
    return {**versions, "strata": summary, "selected": selected}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--quotas", type=Path, required=True)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        frame_bytes, quota_bytes = args.frame.read_bytes(), args.quotas.read_bytes()
        frame = read_json(frame_bytes)
        result = select(frame, read_json(quota_bytes), args.seed)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    result.update(
        selected_at_utc=datetime.now(timezone.utc).isoformat(),
        seed=args.seed,
        selection="SHA-256 priority within strata; no replacement",
        frame_sha256=hashlib.sha256(frame_bytes).hexdigest(),
        quotas_sha256=hashlib.sha256(quota_bytes).hexdigest(),
        sampler_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        manifest_adapter_sha256=hashlib.sha256(
            Path(__file__).with_name("manifest.py").read_bytes()
        ).hexdigest(),
        protocol_sha256=hashlib.sha256(
            Path(__file__).with_name("protocol.md").read_bytes()
        ).hexdigest(),
        frame_provenance=frame["provenance"],
    )
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
    except OSError as exc:
        parser.error(str(exc))
    print(f"Selected {len(result['selected'])} units in {len(result['strata'])} strata")


if __name__ == "__main__":
    main()
