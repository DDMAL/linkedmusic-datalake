#!/usr/bin/env python3
"""
convert_to_rdf.py - Stage E of the CKG -> LinkedMusic ingestion (doc/INGESTION-PLAN.md).

Two-pass streaming NT -> TTL converter. "Pass 1" is the Stage B/C index build
(entity index, crosswalk, record types - loaded here); "pass 2" streams the
normalized N-Triples and rewrites each triple by the finalized mapping
(doc/predicate-evidence.md s4, distilled into ontology/mapping.json), applying:

  * **drop** the DataFeed envelope / provenance / broken predicates;
  * **remap** to ``wdt:P*`` (with ``xsd:date``/``gYear`` coercion for dates);
  * **collapse** every relation object: an authority blank node becomes its
    GND/VIAF URI (the no-blank-node rule, also dedupes); a bare source URI is
    kept as a residue node. Both get a local ``lmckg:*`` class; reconciled nodes
    additionally get a ``wdt:P2888``->QID pivot. Unreconciled residue is kept
    intact (no QID) for a later OpenRefine pass;
  * **type** every record (``lmckg:Event``/``Work`` + ``wdt:P31``->QID) from its
    classifier, and keep the AAT URI;
  * **keep** ``rdfs:label`` (record/event/work titles) verbatim.

Output is streamed as prefixed Turtle (controlled terms are emitted pre-compacted;
data URIs and source literals are written verbatim, which is valid Turtle), so
memory is bounded by a dedupe set rather than an in-memory graph.

Run from ``src/``::

    python convert_to_rdf.py musiconn
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from isodate import parse_date
from isodate.isoerror import ISO8601Error
from rdflib import Literal
from rdflib.util import from_n3
from tqdm import tqdm

RDF_TYPE = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
RDFS_LABEL = "<http://www.w3.org/2000/01/rdf-schema#label>"
RECORD_TYPE = "<https://nfdi4culture.de/ontology/CTO_0001005>"  # "source item"
CTO_NS = "https://nfdi4culture.de/ontology/"
CREATION_PERIOD = f"<{CTO_NS}CTO_0001073>"
PERIOD_MODEL_VERSION = "apsearch-creation-period-v1"

# Fallback P31 for records whose classifiers produced NO P31 (no AAT/media class,
# or a classifier we deliberately leave unmapped such as the ethnographic-objects
# AAT), keyed by feed then record kind:
#  * Detmold (Hoftheater repertoire) -> Q838948 "work of art": a heterogeneous mix
#    of operas + spoken plays + Singspiele; Q838948 is the best-connected Wikidata
#    class (67 sitelinks) that is a verified superclass (P279*) of BOTH play
#    (Q25379) and opera (Q1344) -- correct for every record and a strong federation
#    hub, unlike abstract "creative work" (Q17537576) or play-excluding "composed
#    musical work" (Q207628).
#  * APSearch (ELAR endangered-language documentation) -> Q17537576 "creative work":
#    these are linguistic/oral field recordings (the faithful schema:CreativeWork
#    mapping); "work of art" would mis-type them.
# musiconn records all carry a resolving classifier, so no fallback fires there.
RECORD_KIND_P31_BY_FEED = {
    "detmold": {"Work": "Q838948"},
    "apsearch": {"Work": "Q17537576"},
}

PREFIXES = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "wd": "http://www.wikidata.org/entity/",
    "wdt": "http://www.wikidata.org/prop/direct/",
    "lmckg": "https://linkedmusic.ca/graphs/ckg/",
    "cto": "https://nfdi4culture.de/ontology/",
}

_YMD = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_YEAR = re.compile(r"^\d{4}$")
# Detmold's CTO_0001073 is a schema:DateTime interval START/END (the source's way
# of expressing precision): same day -> a date; a full calendar month -> gYearMonth;
# a full calendar year -> gYear. musiconn carries no interval dates, so this branch
# never fires there (its dates stay byte-identical).
_DT_INTERVAL = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T[\d:]+/(\d{4})-(\d{2})-(\d{2})T[\d:]+$"
)
_PERIOD_ENDPOINT = re.compile(
    r"([0-9]{4})(?:-([0-9]{2})-([0-9]{2})(?:T([0-9]{2}:[0-9]{2}:[0-9]{2}))?)?"
)


def period_endpoint(value: str, side: str) -> tuple[str | None, list[str]]:
    """Extract a year without guessing missing years or repairing invalid dates.

    Recognized APSearch precision: bare year, Jan-01 placeholder, or zero
    month/day components. Other valid calendar dates retain their year but
    require review before the period is used as a year-only projection.
    """
    match = _PERIOD_ENDPOINT.fullmatch(value)
    if not match:
        return None, [f"unrecognized-{side}"]
    year, month, day, time = match.groups()
    if year == "0000":
        return None, [f"invalid-{side}"]
    flags = []
    if month is not None:
        try:
            if month == "00":
                if day != "00" or time is not None:
                    raise ValueError("Unknown month cannot have a day or time")
            elif day == "00":
                if not 1 <= int(month) <= 12 or time is not None:
                    raise ValueError("Invalid unknown-day date")
            else:
                date(int(year), int(month), int(day))
                if time is not None:
                    datetime.strptime(time, "%H:%M:%S")
                if (month, day) != ("01", "01") or time not in (
                    None,
                    "00:00:00" if side == "start" else "23:59:59",
                ):
                    flags.append(f"unexpected-precision-{side}")
        except ValueError:
            return None, [f"invalid-{side}"]
    return year, flags


def creation_period(obj_token: str) -> tuple[str | None, str | None, str, list[str]]:
    """Return supplied year bounds, parse status and review flags.

    The original RDF term is emitted separately, including its datatype or
    language. 'parsed' means supported syntax and ordered bounds, not verified
    historical accuracy. In particular, 9009 is preserved and flagged.
    """
    value = from_n3(obj_token) if obj_token.startswith('"') else None
    if not isinstance(value, Literal):
        return None, None, "unresolved", ["non-literal"]
    if value.language:
        return None, None, "unresolved", ["language-tagged"]
    endpoints = str(value).split("/")
    if len(endpoints) == 1:
        endpoints *= 2
    if len(endpoints) != 2:
        return None, None, "unresolved", ["unrecognized-interval"]
    start, start_flags = period_endpoint(endpoints[0], "start")
    end, end_flags = period_endpoint(endpoints[1], "end")
    flags = start_flags + end_flags
    if start is not None and end is not None:
        # Compare only mutually known components; 1950-12-00/1950-02-00 is
        # reversed even though both year projections are 1950.
        left = _PERIOD_ENDPOINT.fullmatch(endpoints[0]).groups()
        right = _PERIOD_ENDPOINT.fullmatch(endpoints[1]).groups()
        for first, last in zip(left, right):
            if first in (None, "00") or last in (None, "00"):
                break
            if first != last:
                if first > last:
                    flags.append("reversed-interval")
                break
    status = "unresolved" if flags else "parsed"
    if "9009" in (start, end):
        flags.append("year-9009")
    return start, end, status, flags


def coerce_date(obj_token: str, feed: str = "") -> str:
    """Coerce an NT literal date token to the most precise XSD temporal type.

    Full valid date -> ``xsd:date``; ``YYYY-MM-00`` -> ``xsd:gYearMonth``;
    ``YYYY-00-00`` / bare ``YYYY`` -> ``xsd:gYear`` (musiconn uses ``-00`` for an
    unknown month/day). A ``schema:DateTime`` ``START/END`` interval (Detmold) is
    reduced to the precision its span implies (day/month/year). Falls back to a
    plain literal if nothing parses.

    For APSearch this helper returns only the compatibility start-year projection
    of a supported, ordered period; unresolved values remain unchanged here.
    The converter's creation-period branch preserves the source and both bounds
    separately and withholds P571 for unresolved values.
    """
    if feed == "apsearch":
        start, _, status, _ = creation_period(obj_token)
        return f'"{start}"^^xsd:gYear' if status == "parsed" else obj_token
    if not obj_token.startswith('"'):
        return obj_token
    val = obj_token[1 : obj_token.rfind('"')]
    if m := _YMD.match(val):
        year, month, day = m.groups()
        if month != "00" and day != "00":
            try:
                parse_date(val)
                return f'"{val}"^^xsd:date'
            except (ISO8601Error, ValueError):
                pass
        if month != "00" and "01" <= month <= "12":
            return f'"{year}-{month}"^^xsd:gYearMonth'
        return f'"{year}"^^xsd:gYear'
    if _YEAR.match(val):
        return f'"{val}"^^xsd:gYear'
    if m := _DT_INTERVAL.match(val):
        y1, mo1, d1, y2, mo2, d2 = m.groups()
        if (y1, mo1, d1) == (y2, mo2, d2):  # single day
            try:
                parse_date(f"{y1}-{mo1}-{d1}")
                return f'"{y1}-{mo1}-{d1}"^^xsd:date'
            except (ISO8601Error, ValueError):
                return f'"{y1}"^^xsd:gYear'
        if (y1, mo1) == (y2, mo2):  # within one calendar month
            return f'"{y1}-{mo1}"^^xsd:gYearMonth'
        if y1 == y2:  # within one calendar year
            return f'"{y1}"^^xsd:gYear'
        return obj_token  # multi-year span (none observed): leave as a plain literal
    return obj_token  # leave free-form values as a plain literal


def cto_pname(pred_token: str) -> str:
    """Compact a kept CTO predicate ``<.../CTO_0001009>`` -> ``cto:CTO_0001009``."""
    iri = pred_token[1:-1]
    return "cto:" + iri[len(CTO_NS) :]


def ttl_string(value: str) -> str:
    """Turtle-escape a string and wrap it as a quoted literal."""
    esc = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{esc}"'


def load_authority_names(path: Path) -> dict[str, str]:
    """authority_uri -> preferred name, from the reconciliation name fetch.

    These are GND/VIAF/GeoNames preferred names fetched for OpenRefine; emitting
    them as ``rdfs:label`` gives the authority entities a name alongside their
    ``wdt:P2888`` pivot (the house "name + P2888" convention). Missing file is
    non-fatal - the converter just emits no authority labels.
    """
    if not path.is_file():
        return {}
    names: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            uri, name = row.get("authority_uri", ""), (row.get("name") or "").strip()
            if uri and name:
                names[uri] = name
    return names


def convert(
    feed: str, extracted: Path, mappings: Path, ontology: Path, outdir: Path
) -> None:
    index = json.loads(
        (extracted / f"{feed}.entities.json").read_text(encoding="utf-8")
    )
    crosswalk = json.loads((mappings / "crosswalk.json").read_text(encoding="utf-8"))
    record_types = json.loads(
        (mappings / "record_types.json").read_text(encoding="utf-8")
    )
    mapping = json.loads((ontology / "mapping.json").read_text(encoding="utf-8"))
    mapping.pop("_doc", None)
    # GND/VIAF/GeoNames preferred names (authority_uri -> name) for rdfs:label.
    authority_names = load_authority_names(
        extracted.parent / "openrefine" / "names_for_reconciliation.csv"
    )

    entities: dict[str, dict[str, str]] = index["entities"]  # bnode -> {t, a}
    record_kind: dict[str, str] = index["record_kind"]  # record_uri -> Event/Work
    # record -> [content URLs], joined in preprocess from the associatedMedia
    # bnode -> CTO_0001021 chain (APSearch); emitted as wdt:P953. Empty elsewhere.
    record_content_urls: dict[str, list[str]] = index.get("record_content_urls", {})
    # Fallback P31 for this feed (Detmold/APSearch); applied post-loop to any record
    # whose classifiers produced no P31. records_with_p31 tracks which records did.
    fallback_p31: dict[str, str] = RECORD_KIND_P31_BY_FEED.get(feed, {})
    records_with_p31: set[str] = set()
    norm_path = extracted / f"{feed}.norm.nt"

    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f"{feed}.ttl"

    seen: set[str] = set()  # output-line dedupe (collapse produces duplicates)
    stats: Counter[str] = Counter()
    unknown: Counter[str] = Counter()
    out = open(out_path, "w", encoding="utf-8")
    for prefix, ns in PREFIXES.items():
        out.write(f"@prefix {prefix}: <{ns}> .\n")
    if feed == "apsearch":
        out.write("@prefix ckgterm: <https://linkedmusic.ca/terms/ckg/> .\n")
    out.write("\n")
    period_counts: Counter[str] = Counter()
    period_flags: Counter[str] = Counter()

    def emit(subj: str, pred: str, obj: str) -> bool:
        """Write one triple line (deduped). subj/obj are final Turtle terms."""
        line = f"{subj} {pred} {obj} ."
        if line in seen:
            return False
        seen.add(line)
        out.write(line + "\n")
        stats["triples"] += 1
        return True

    def node_metadata(node_iri: str, local_class: str | None) -> str:
        """Emit type (+ P2888 if reconciled) for an entity node; return its term.

        ``node_iri`` is the bare URI; the returned term is ``<node_iri>``.
        """
        term = f"<{node_iri}>"
        if local_class:
            emit(term, "rdf:type", f"lmckg:{local_class}")
        qid = crosswalk.get(node_iri)
        if qid and emit(term, "wdt:P2888", f"wd:{qid}"):
            stats["pivots"] += 1  # distinct reconciled nodes
        name = authority_names.get(node_iri)
        if name and emit(term, "rdfs:label", ttl_string(name)):
            stats["authority_labels"] += 1
        return term

    def emit_creation_period(subj: str, obj: str) -> None:
        """Retain the source assertion and one named observation per NT payload."""
        if obj.startswith("_:"):
            raise ValueError("APSearch creation period is a blank node; inspect source")
        period_counts["input_occurrences"] += 1
        digest = hashlib.sha256(
            json.dumps([subj, CREATION_PERIOD, obj], ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        node = f"<https://linkedmusic.ca/graphs/ckg-apsearch/creation-period/{digest}>"
        emit(subj, "cto:CTO_0001073", obj)
        if not emit(subj, "ckgterm:creationPeriod", node):
            period_counts["duplicate_occurrences"] += 1
            return
        start, end, status, flags = creation_period(obj)
        period_counts["distinct_periods"] += 1
        period_counts[status] += 1
        emit(node, "rdf:type", "ckgterm:CreationPeriod")
        emit(node, "rdf:value", obj)
        emit(node, "ckgterm:parseStatus", ttl_string(status))
        for predicate, year in (("startYear", start), ("endYear", end)):
            if year is not None:
                emit(node, f"ckgterm:{predicate}", f'"{year}"^^xsd:gYear')
                period_counts[predicate] += 1
        if flags:
            period_counts["flagged_periods"] += 1
        for flag in flags:
            emit(node, "ckgterm:reviewFlag", ttl_string(flag))
            period_flags[flag] += 1
        if status == "parsed":
            emit(subj, "wdt:P571", f'"{start}"^^xsd:gYear')

    def resolve_object(obj_token: str, entity_class: str | None) -> str | None:
        """Collapse a relation object to its final term, emitting node metadata.

        - authority bnode  -> its GND/VIAF URI, typed from the index (+ P2888)
        - bare source URI   -> kept as a residue node, typed from entity_class
        - record/feed URI   -> kept verbatim, untyped (entity_class is None)
        - unknown bnode     -> None (cannot emit a blank node)
        """
        if obj_token.startswith("_:"):
            ent = entities.get(obj_token)
            if not ent:
                stats["dropped_orphan_bnode"] += 1
                return None
            stats["collapsed_bnode"] += 1
            return node_metadata(ent["a"], ent["t"])
        if obj_token.startswith("<"):
            iri = obj_token[1:-1]
            if entity_class:
                stats["residue_uri"] += 1
                return node_metadata(iri, entity_class)
            return obj_token  # record/feed cross-reference, kept untyped
        stats["dropped_literal_relation"] += 1
        return None  # backbone relations never carry literals

    print(f"[{feed}] pass 2: convert {norm_path} -> {out_path}")
    with open(norm_path, "r", encoding="utf-8") as fh:
        for raw in tqdm(fh, unit=" triples"):
            raw = raw.rstrip("\n")
            if not raw or raw[0] == "#":
                continue
            body = raw[:-2] if raw.endswith(" .") else raw
            parts = body.split(" ", 2)
            if len(parts) < 3:
                continue
            s, p, o = parts[0], parts[1], parts[2].strip()

            # Blank-node subjects (entity + is-about nodes) are fully captured by
            # the Stage B index; never emit them.
            if s.startswith("_:"):
                continue

            spec = mapping.get(p[1:-1])
            if spec is None:
                unknown[p] += 1
                continue
            action = spec["action"]

            if action == "drop":
                continue

            if action == "type":
                # rdf:type. Records -> local lmckg class; everything else dropped
                # (authority-URI id classes, DataFeed envelope, etc.). The wdt:P31
                # fallback for records without a resolving classifier is applied
                # post-loop (see below), so it also catches records whose only
                # classifier is one we leave unmapped (e.g. ethnographic-objects AAT).
                if o == RECORD_TYPE:
                    kind = record_kind.get(s)
                    if kind:
                        emit(s, "rdf:type", f"lmckg:{kind}")
                continue

            if action == "label":
                emit(s, "rdfs:label", o)
                continue

            if action == "remap":
                emit(s, f"wdt:{spec['target']}", o)
                # If the remapped object is a URI that reconciles (a license or
                # publisher entity), add its local-node wdt:P2888 -> QID pivot, the
                # same indirection used for backbone authority nodes. No-op for
                # musiconn/Detmold (their license/publisher URIs aren't crosswalked)
                # and for date remaps (literal objects).
                if o.startswith("<"):
                    qid = crosswalk.get(o[1:-1])
                    if qid and emit(o, "wdt:P2888", f"wd:{qid}"):
                        stats["pivots"] += 1
                continue

            if action == "remap_date":
                if feed == "apsearch" and p == CREATION_PERIOD:
                    emit_creation_period(s, o)
                else:
                    emit(s, f"wdt:{spec['target']}", coerce_date(o, feed))
                continue

            if action == "url_permalink":
                # Retained for a hypothetical feed whose NFDI_0001008 is a genuine
                # external permalink. Currently UNUSED: every observed feed (incl.
                # Detmold) has a self-referential value == the subject IRI, so the
                # mapping drops it. See mapping.json NFDI_0001008 _note.
                if feed == "detmold":
                    emit(s, f"wdt:{spec['target']}", o)
                continue

            if action == "classifier_aat":
                qid = record_types.get(o[1:-1])
                if qid:
                    emit(s, "wdt:P31", f"wd:{qid}")
                    records_with_p31.add(s)
                emit(s, cto_pname(p), o)  # keep the AAT URI for interoperability
                continue

            if action == "classifier_media":
                qid = record_types.get(o[1:-1])
                if qid:
                    emit(s, "wdt:P31", f"wd:{qid}")
                    records_with_p31.add(s)
                continue

            if action == "is_about":
                continue  # record already typed via record_kind; drop the relation

            if action in ("keep_relation", "remap_relation"):
                term = resolve_object(o, spec.get("entity_class"))
                if term is None:
                    continue
                pred = (
                    cto_pname(p)
                    if action == "keep_relation"
                    else f"wdt:{spec['target']}"
                )
                emit(s, pred, term)
                continue

    # Post-loop (order-independent: records_with_p31 is now complete).
    # 1. Fallback wdt:P31 for any record whose classifiers produced no P31.
    for rec, kind in record_kind.items():
        if rec not in records_with_p31:
            qid = fallback_p31.get(kind)
            if qid:
                emit(rec, "wdt:P31", f"wd:{qid}")
    # 2. wdt:P953 content URLs (APSearch): emitted as URI nodes, matching the
    #    repo's url-property convention (cf. diamm P856 URIRef objects).
    for rec, urls in record_content_urls.items():
        for url in urls:
            if emit(rec, "wdt:P953", f"<{url}>"):
                stats["content_urls"] += 1

    out.close()

    if feed == "apsearch":

        def sha256(path: Path) -> str:
            with path.open("rb") as stream:
                return hashlib.file_digest(stream, "sha256").hexdigest()

        audit_path = outdir / "apsearch.creation-period-audit.json"
        audit = {
            "model_version": PERIOD_MODEL_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_snapshot_date": None,
            "input": {"path": str(norm_path.resolve()), "sha256": sha256(norm_path)},
            "converter_sha256": sha256(Path(__file__)),
            "mapping_sha256": sha256(ontology / "mapping.json"),
            "output_sha256": sha256(out_path),
            "counts": {
                key: period_counts[key]
                for key in (
                    "input_occurrences",
                    "distinct_periods",
                    "duplicate_occurrences",
                    "parsed",
                    "unresolved",
                    "startYear",
                    "endYear",
                    "flagged_periods",
                )
            },
            "review_flags": dict(sorted(period_flags.items())),
        }
        audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
        print(f"  creation-period audit: {audit_path}")

    print(f"\n[{feed}] convert summary -> {out_path}")
    print(f"  triples emitted          : {stats['triples']:,}")
    print(f"  distinct P2888 pivots    : {stats['pivots']:,}")
    print(f"  P953 content URLs        : {stats['content_urls']:,}")
    print(f"  authority rdfs:labels    : {stats['authority_labels']:,}")
    print(f"  bnode-collapse occurrences: {stats['collapsed_bnode']:,}")
    print(f"  residue-URI occurrences   : {stats['residue_uri']:,}")
    for k in ("dropped_orphan_bnode", "dropped_literal_relation"):
        if stats[k]:
            print(f"  {k}: {stats[k]:,}")
    if unknown:
        print(f"  UNKNOWN predicates (dropped): {dict(unknown.most_common())}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CKG Stage E: NT -> TTL converter.")
    parser.add_argument("feed", help="feed name (e.g. musiconn)")
    parser.add_argument(
        "--extracted", default="../data/extracted", help="Stage B output dir"
    )
    parser.add_argument(
        "--mappings", default="../data/mappings", help="Stage C crosswalk dir"
    )
    parser.add_argument("--ontology", default="./ontology", help="mapping.json dir")
    parser.add_argument("--outdir", default="../data/rdf", help="output .ttl dir")
    args = parser.parse_args()
    convert(
        args.feed,
        Path(args.extracted),
        Path(args.mappings),
        Path(args.ontology),
        Path(args.outdir),
    )


if __name__ == "__main__":
    main()
