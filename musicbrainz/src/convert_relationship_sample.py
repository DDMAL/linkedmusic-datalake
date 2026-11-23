"""Convert bounded JSON records offline; keep base RDF, schema, and audit separate."""

import argparse
import hashlib
import importlib.metadata
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from rdflib import Dataset, Graph, URIRef
from rdflib.namespace import RDF

from convert_to_rdf import process_entity
from mapping_schema import MappingSchema
from relationship_mapping import ROLE, TERMS, WDT, RelationshipMappings

ROOT = Path(__file__).resolve().parents[1]


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    entity_types = ("recording", "release", "artist", "label")
    for kind in entity_types:
        parser.add_argument(f"--{kind}", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--source-kind", choices=("synthetic", "api", "dump"), default=None
    )
    args = parser.parse_args(argv)
    inputs = [(kind, path) for kind in entity_types for path in getattr(args, kind)]
    if not inputs:
        if args.source_kind not in (None, "synthetic"):
            parser.error("Provide JSON input files for API/dump evidence")
        args.source_kind = "synthetic"
        inputs = [("recording", ROOT / "tests/fixtures/role_pilot.json")]
    elif args.source_kind is None:
        parser.error(
            "Explicit input files require --source-kind synthetic, api or dump"
        )
    try:
        args.output_dir.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        parser.error(str(error))

    config_dir = ROOT / "src/rdf_conversion_config"
    relations_path = config_dir / "relations.json"
    fields_path = config_dir / "mappings.json"
    attributes_path = config_dir / "attribute_mapping.json"
    mapping = RelationshipMappings(json.loads(relations_path.read_text()))
    schema = MappingSchema({})
    schema.add_from_formatted_dict(json.loads(fields_path.read_text()))
    attributes = {
        key: WDT[value] if value else None
        for key, value in json.loads(attributes_path.read_text()).items()
    }
    graph = Graph()
    sources = []
    for index, (kind, path) in enumerate(inputs):
        payload = path.read_bytes()
        record = json.loads(payload)
        archive = f"input-{index:04d}-{kind}.json"
        (args.output_dir / archive).write_bytes(payload)
        process_entity(record, kind, schema, mapping, {}, attributes, graph)
        sources.append(
            {
                "path": str(path.resolve()),
                "entity_type": kind,
                "id": record.get("id"),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "archived_input": archive,
                "top_level_relationships": len(record.get("relations", [])),
            }
        )

    schema_graph = mapping.schema_graph()
    query_graph = Dataset(default_union=False)
    data_iri = "urn:linkedmusic:pilot:data"
    schema_iri = "urn:linkedmusic:pilot:schema"
    for triple in graph:
        query_graph.graph(URIRef(data_iri)).add(triple)
    for triple in schema_graph:
        query_graph.graph(URIRef(schema_iri)).add(triple)
    contributor_query = ROOT / "doc/queries/pilot_contributors.rq"
    queries = {
        "recording_engineers": f"SELECT ?record ?artist WHERE {{ GRAPH <{data_iri}> {{ ?record <{ROLE['a01ee869-80a8-45ef-9447-c59e91aa7926']}> ?artist }} }} ORDER BY ?record ?artist",
        "recording_photographers": f"SELECT ?record ?artist WHERE {{ GRAPH <{data_iri}> {{ ?record <{ROLE['a7e408a1-8c64-4122-9ec2-906068955187']}> ?artist }} }} ORDER BY ?record ?artist",
        "contributors": contributor_query.read_text(encoding="utf-8"),
        "relationship_dates": f"""SELECT ?observation ?begin ?end WHERE {{
  GRAPH <{data_iri}> {{
  ?observation <{RDF.type}> <{TERMS.RelationshipObservation}> .
  OPTIONAL {{ ?observation <{TERMS.begin}> ?begin }}
  OPTIONAL {{ ?observation <{TERMS.end}> ?end }}
  FILTER(BOUND(?begin) || BOUND(?end))
  }}
}} ORDER BY ?observation""",
    }
    results = {}
    for name, query in queries.items():
        result = query_graph.query(query)
        results[name] = {
            "query": query,
            "columns": [str(var) for var in result.vars],
            "rows": [
                [term.n3() if term is not None else None for term in row]
                for row in result
            ],
        }
    statuses = Counter(
        str(status) for status in graph.objects(None, TERMS.mappingStatus)
    )
    code_paths = [
        ROOT / "src/convert_to_rdf.py",
        ROOT / "src/relationship_mapping.py",
        Path(__file__),
        ROOT / "src/mapping_schema.py",
        contributor_query,
    ]
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_kind": args.source_kind,
        "python": sys.version,
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("rdflib", "pandas", "pyparsing")
        },
        "lock_sha256": checksum(ROOT.parent / "poetry.lock"),
        "query_graphs": {"data": data_iri, "schema": schema_iri},
        "scope": "Bounded source observations; not a population quality estimate. Empty reconciliation lookup for auxiliary fields.",
        "sources": sources,
        "implementation_sha256": {
            str(path.relative_to(ROOT)): checksum(path) for path in code_paths
        },
        "configuration_sha256": {
            path.name: checksum(path)
            for path in (relations_path, fields_path, attributes_path)
        },
        "base_triples": len(graph),
        "schema_triples": len(schema_graph),
        "observation_statuses": dict(statuses),
        "distinct_role_assertions": len(
            {(s, p, o) for s, p, o in graph if str(p).startswith(str(ROLE))}
        ),
        "queries": results,
    }
    graph.serialize(args.output_dir / "base.ttl", format="turtle")
    schema_graph.serialize(args.output_dir / "schema.ttl", format="turtle")
    report["output_sha256"] = {
        name: checksum(args.output_dir / name) for name in ("base.ttl", "schema.ttl")
    }
    (args.output_dir / "audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "source_records": len(inputs),
                "observations": dict(statuses),
                "distinct_role_assertions": report["distinct_role_assertions"],
                "query_rows": {
                    name: len(result["rows"]) for name, result in results.items()
                },
            }
        )
    )
    if any(status != "mapped" for status in statuses):
        raise SystemExit(
            "Unresolved relationship evidence was preserved; review audit.json"
        )


if __name__ == "__main__":
    main()
