#!/usr/bin/env python3
"""
preprocess.py - Stage B of the CKG -> LinkedMusic ingestion (see doc/INGESTION-PLAN.md).

Given a per-feed CKG N-Triples dump, this does a single streaming pass that

1. **Normalizes the typo predicates/classes** ``NFDI0001006/9/10`` (missing the
   underscore) -> ``NFDI_0001006/9/10``. Without this fix the 1,704 malformed
   ``NFDI0001006`` authority links would be lost. The corrected triples are
   written to ``<feed>.norm.nt``.

2. **Builds the entity index** the converter (Stage E) needs. Two distinct
   shapes carry the relational backbone (see doc/predicate-evidence.md and the
   profiling that refined it):

     * **Authority bnodes** - a relation object that is a blank node typed
       ``NFDI_0000003/4/5/107`` (org/person/place/collection) and carrying
       exactly one ``NFDI_0001006`` authority URI (GND/VIAF). These are indexed
       ``{bnode -> (local_class, authority_URI)}`` so the converter can collapse
       the bnode to its authority URI (the no-blank-node rule) and dedupe.
     * **Bare source URIs** - a relation object that is already a
       ``performance.musiconn.de/{person,corporation,location,series}`` URI with
       *no* authority ID and *no* type. These are the residue the evidence sheet
       did not separately count; they are NOT indexed here (there is no bnode and
       no authority to resolve) - the converter types them inline from the
       relation and keeps them as persistent residue nodes.

3. **Builds the record-type index** so the converter can emit ``wdt:P31``:
     * ``record -> classifier`` from ``CTO_0001026`` (AAT URI, musiconn) /
       ``CTO_0001049`` (CTO media class, APSearch); and
     * ``record -> kind`` ("Event"/"Work") from the ``CTO_0001025`` "is about"
       bnode's ``schema:MusicEvent`` / ``schema:MusicComposition`` type - a clean
       parallel signal that also lets us drop the identity-less is-about bnode.

4. **Collects the distinct authority IDs** (deduped GND + VIAF + GeoNames) -> Stage C.

Outputs (to ``../data/extracted/`` by default):
    <feed>.norm.nt          normalized N-Triples (input to Stage E pass 2)
    <feed>.entities.json    entity index + record kind/classifier maps
    <feed>.authorities.json deduped {gnd:[...], viaf:[...]} id lists (-> Stage C)

Run from ``ckg/src/`` (CWD convention)::

    python preprocess.py musiconn
    python preprocess.py detmold --raw-root /some/other/path
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterator

from tqdm import tqdm

# --- Feed -> CKG dump id (doc/INGESTION-PLAN.md "Inputs & implementation gotchas")
FEEDS = {"musiconn": "E5320", "detmold": "E5305", "apsearch": "E6304"}
DEFAULT_RAW_ROOT = "../../raw_data/ckg/mnt/data/culture-kg-kitchen/data/production"

RDF_TYPE = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
NFDI = "https://nfdi.fiz-karlsruhe.de/ontology/"
CTO = "https://nfdi4culture.de/ontology/"
SCHEMA = "http://schema.org/"
RDFS_LABEL = "<http://www.w3.org/2000/01/rdf-schema#label>"

P_AUTH_ID = f"<{NFDI}NFDI_0001006>"  # has external identifier (GND/VIAF)
P_IS_ABOUT = f"<{CTO}CTO_0001025>"  # is about real world entity (-> bare event/work bnode)
P_CLASSIFIER_AAT = f"<{CTO}CTO_0001026>"  # has external classifier (AAT)
P_DATA_CONCEPT = f"<{CTO}CTO_0001049>"  # has data concept (CTO media class, APSearch)
P_ASSOC_MEDIA = f"<{SCHEMA}associatedMedia>"  # record -> media bnode (APSearch)
P_CONTENT_URL = f"<{CTO}CTO_0001021>"  # has content url, on the media bnode (APSearch)

# Blank-node entity types -> the local lmckg class the converter will assign.
ENTITY_TYPE_CLASS = {
    f"<{NFDI}NFDI_0000003>": "Organization",
    f"<{NFDI}NFDI_0000004>": "Person",
    f"<{NFDI}NFDI_0000005>": "Place",
    f"<{CTO}NFDI_0000107>": "Collection",
}
# is-about bnode types -> record kind. musiconn uses the precise schema:MusicEvent
# / schema:MusicComposition; Detmold + APSearch use the generic schema:CreativeWork
# (no AAT classifier), so it maps to the broadest kind we emit, "Work".
EVENT_WORK_KIND = {
    f"<{SCHEMA}MusicEvent>": "Event",
    f"<{SCHEMA}MusicComposition>": "Work",
    f"<{SCHEMA}CreativeWork>": "Work",
}
# Relations whose objects form the backbone - counted here for the coverage report.
BACKBONE_RELATIONS = {
    f"<{CTO}CTO_0001009>": "person",
    f"<{CTO}CTO_0001010>": "organization",
    f"<{CTO}CTO_0001011>": "location",
    f"<{CTO}CTO_0001019>": "related_item",
    f"<{CTO}CTO_0001006>": "referenced_in",
    "<http://purl.obolibrary.org/obo/BFO_0000050>": "part_of",
}

# Normalize "NFDI" immediately followed by a digit (the typo) -> "NFDI_" + digit.
# Legitimate IRIs are always "NFDI_<digits>", so they are never touched.
_NFDI_TYPO = re.compile(r"NFDI(\d)")


def normalize_line(line: str) -> str:
    """Repair the missing-underscore ``NFDI0001006/9/10`` typo on a raw NT line."""
    return _NFDI_TYPO.sub(r"NFDI_\1", line)


def iter_triples(path: Path) -> Iterator[tuple[str, str, str, str]]:
    """Yield ``(subject, predicate, object, normalized_line)`` from an NT file.

    The normalized line is returned alongside so the caller can both index and
    re-emit in one pass. Subject/predicate are the first two whitespace tokens;
    the object is the remainder up to the trailing ``" ."`` (per profile_predicate).
    """
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.rstrip("\n")
            if not raw or raw[0] == "#":
                continue
            line = normalize_line(raw)
            body = line
            if body.endswith(" ."):
                body = body[:-2]
            elif body.endswith("."):
                body = body[:-1]
            parts = body.split(" ", 2)
            if len(parts) < 3:
                continue
            yield parts[0], parts[1], parts[2].strip(), line


def authority_id(uri_obj: str) -> tuple[str, str] | None:
    """Map a ``<...>`` authority object to ``(scheme, bare_id)`` for GND/VIAF/GeoNames."""
    if not (uri_obj.startswith("<") and uri_obj.endswith(">")):
        return None
    uri = uri_obj[1:-1]
    if "d-nb.info/gnd/" in uri:
        return "gnd", uri.rsplit("/", 1)[-1]
    if "viaf.org/viaf/" in uri:
        return "viaf", uri.rsplit("/", 1)[-1]
    if "sws.geonames.org/" in uri:  # Detmold places (-> Wikidata P1566)
        return "geonames", uri.rstrip("/").rsplit("/", 1)[-1]
    return None


def preprocess(feed: str, input_path: Path, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    norm_path = outdir / f"{feed}.norm.nt"
    entities_path = outdir / f"{feed}.entities.json"
    authorities_path = outdir / f"{feed}.authorities.json"

    # Entity index: bnode -> [local_class, authority_URI]. authority_URI may be
    # None transiently if the type triple is seen before the id triple; merged below.
    bnode_class: dict[str, str] = {}
    bnode_auth: dict[str, str] = {}
    # is-about: record -> bnode, and bnode -> kind; joined at the end.
    record_isabout: dict[str, str] = {}
    isabout_kind: dict[str, str] = {}
    # record -> classifier URI (AAT or CTO media class)
    record_classifier: dict[str, str] = {}
    # associatedMedia: media bnode -> owning record, and media bnode -> content URL.
    # The content URL lives on the bnode (which the converter never emits), so it is
    # joined back to the record below -> converter emits <record> wdt:P953 <url>.
    media_bnode_record: dict[str, str] = {}
    bnode_content_url: dict[str, str] = {}
    # deduped authority URIs and their bare ids
    auth_uris: dict[str, set[str]] = {"gnd": set(), "viaf": set(), "geonames": set()}
    auth_for_uri: dict[str, str] = {}  # authority_URI -> already seen (dedupe helper)

    relation_obj_kind: dict[str, Counter] = {
        name: Counter() for name in BACKBONE_RELATIONS.values()
    }
    n_lines = 0

    print(f"[{feed}] pass 1: normalize + index  ({input_path})")
    with open(norm_path, "w", encoding="utf-8") as out:
        for s, p, o, line in tqdm(iter_triples(input_path), unit=" triples"):
            out.write(line + "\n")
            n_lines += 1

            is_bnode_subj = s.startswith("_:")

            if p == RDF_TYPE:
                if is_bnode_subj and o in ENTITY_TYPE_CLASS:
                    bnode_class[s] = ENTITY_TYPE_CLASS[o]
                elif is_bnode_subj and o in EVENT_WORK_KIND:
                    isabout_kind[s] = EVENT_WORK_KIND[o]
            elif p == P_AUTH_ID:
                if is_bnode_subj:
                    bnode_auth[s] = o[1:-1] if o.startswith("<") else o
                hit = authority_id(o)
                if hit:
                    scheme, bare = hit
                    auth_uris[scheme].add(o[1:-1])
                    auth_for_uri[o[1:-1]] = bare
            elif p == P_IS_ABOUT:
                if o.startswith("_:"):
                    record_isabout[s] = o
            elif p == P_CLASSIFIER_AAT or p == P_DATA_CONCEPT:
                if o.startswith("<"):
                    record_classifier[s] = o[1:-1]
            elif p == P_ASSOC_MEDIA:
                if o.startswith("_:"):
                    media_bnode_record[o] = s
            elif p == P_CONTENT_URL:
                if is_bnode_subj and o.startswith('"'):
                    bnode_content_url[s] = o[1 : o.rfind('"')]

            if p in BACKBONE_RELATIONS:
                kind = "bnode" if o.startswith("_:") else ("uri" if o.startswith("<") else "lit")
                relation_obj_kind[BACKBONE_RELATIONS[p]][kind] += 1

    # Join: record -> kind via its is-about bnode.
    record_kind: dict[str, str] = {}
    for rec, bn in record_isabout.items():
        if bn in isabout_kind:
            record_kind[rec] = isabout_kind[bn]

    # Join: record -> content URLs via its associatedMedia bnode(s) (APSearch).
    record_content_urls: dict[str, list[str]] = {}
    for bnode, url in bnode_content_url.items():
        rec = media_bnode_record.get(bnode)
        if rec:
            record_content_urls.setdefault(rec, []).append(url)

    # Merge bnode class + auth into the entity index. Keep only bnodes that have
    # both a known class and an authority (the documented authority-bnode shape).
    entities: dict[str, dict[str, str]] = {}
    n_class_no_auth = 0
    for bn, cls in bnode_class.items():
        auth = bnode_auth.get(bn)
        if auth is None:
            n_class_no_auth += 1
            continue
        entities[bn] = {"t": cls, "a": auth}

    index = {
        "feed": feed,
        "entities": entities,
        "record_kind": record_kind,
        "record_classifier": record_classifier,
        "record_content_urls": record_content_urls,
    }
    with open(entities_path, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False)

    # {scheme: {bare_id: full_authority_URI}} - keyed so Stage C can write the
    # crosswalk against the exact URI string the converter will look up.
    authorities = {
        scheme: {auth_for_uri[u]: u for u in sorted(auth_uris[scheme])}
        for scheme in ("gnd", "viaf", "geonames")
    }
    with open(authorities_path, "w", encoding="utf-8") as fh:
        json.dump(authorities, fh, ensure_ascii=False)

    # --- Report ---
    cls_counts = Counter(v["t"] for v in entities.values())
    distinct_gnd = len(authorities["gnd"])
    distinct_viaf = len(authorities["viaf"])
    distinct_geo = len(authorities["geonames"])
    print(f"\n[{feed}] preprocess summary")
    print(f"  triples written      : {n_lines:,}  -> {norm_path}")
    print(f"  authority bnodes      : {len(entities):,}  (indexed for collapse)")
    for cls, n in cls_counts.most_common():
        print(f"      {cls:<14}: {n:,}")
    if n_class_no_auth:
        print(f"  typed bnodes w/o auth : {n_class_no_auth:,}  (skipped)")
    print(f"  distinct authorities  : {distinct_gnd + distinct_viaf + distinct_geo:,}  "
          f"(GND {distinct_gnd:,} + VIAF {distinct_viaf:,} + GeoNames {distinct_geo:,})"
          f"  -> {authorities_path}")
    print(f"  records w/ kind       : {len(record_kind):,}  "
          f"({Counter(record_kind.values())})")
    print(f"  records w/ classifier : {len(record_classifier):,}  "
          f"({Counter(record_classifier.values())})")
    if record_content_urls:
        n_urls = sum(len(v) for v in record_content_urls.values())
        print(f"  records w/ content URL: {len(record_content_urls):,}  "
              f"({n_urls:,} URLs total -> wdt:P953)")
    print(f"  backbone relation objects (bnode vs bare URI residue):")
    for name, c in relation_obj_kind.items():
        if sum(c.values()):
            print(f"      {name:<14}: {dict(c)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CKG Stage B preprocess (normalize + index).")
    parser.add_argument("feed", choices=sorted(FEEDS), help="feed name")
    parser.add_argument("--raw-root", default=DEFAULT_RAW_ROOT,
                        help="root of the per-feed CKG dumps (E####/nt/E####.nt)")
    parser.add_argument("--input", help="explicit path to the feed .nt (overrides --raw-root)")
    parser.add_argument("--outdir", default="../data/extracted", help="output directory")
    args = parser.parse_args()

    e = FEEDS[args.feed]
    input_path = Path(args.input) if args.input else Path(args.raw_root) / e / "nt" / f"{e}.nt"
    if not input_path.is_file():
        parser.error(f"input not found: {input_path}")

    preprocess(args.feed, input_path, Path(args.outdir))


if __name__ == "__main__":
    main()
