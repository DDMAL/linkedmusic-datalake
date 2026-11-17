"""Emit a separately loadable contributor schema from the exact batch mapping."""

import argparse
import hashlib
import json
from importlib.metadata import version
from pathlib import Path
import platform

from relationship_mapping import RelationshipMappings

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--relations",
        type=Path,
        default=Path(__file__).parent / "rdf_conversion_config/relations.json",
        help="The relations.json used by the batch converter",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    source = args.relations.read_bytes()
    schema = RelationshipMappings(json.loads(source)).schema_graph()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "relations.json").write_bytes(source)
    output = args.output_dir / "schema.ttl"
    output.write_bytes(schema.serialize(format="turtle", encoding="utf-8"))
    audit = {
        "scope": "Schema only; no data converted, loaded or inferred",
        "relations_path": str(args.relations.resolve()),
        "relations_sha256": hashlib.sha256(source).hexdigest(),
        "schema_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "schema_triples": len(schema),
        "runtime": {"python": platform.python_version(), "rdflib": version("rdflib")},
        "code_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__).resolve(),
                Path(__file__).parent / "relationship_mapping.py",
                ROOT / "poetry.lock",
            )
        },
    }
    (args.output_dir / "audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
