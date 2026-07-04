#!/usr/bin/env python3
"""
profile_predicate.py - show how predicates are actually used in N-Triples data.

Purpose
-------
When ingesting an RDF-native dataset (e.g. the NFDI4Culture Culture Knowledge
Graph) into the LinkedMusic data lake, every source predicate must be mapped to
a Wikidata property (``wdt:P*``) or deliberately kept / dropped. Choosing the
right property requires knowing how a predicate is *used* - what kinds of
subjects carry it and what its objects look like - because a single generic
predicate (e.g. ``NFDI_0001008`` "has url") can stand in for several distinct
Wikidata properties depending on context.

This script profiles that usage so the mapping is chosen from evidence rather
than guessed. It complements the project's two existing reconciliation tools:

* OpenRefine reconciles *values*               (a cell  -> ``wd:Q...``)
* ``shared/prop_cli.py`` searches Wikidata for *properties* (a relation -> ``wdt:P...``)
* this script characterises the *source predicate* that feeds both decisions.

It streams the input line by line (no RDF library, no in-memory graph), so it
runs on the per-feed dumps and, more slowly, on the multi-GB merged dump.

Note on memory: ``--predicate`` (deep) mode holds an rdf:type index for every
subject, so prefer running it per feed file rather than on the full merged dump.
The overview mode is bounded by the number of distinct predicates.

Usage
-----
Overview of every predicate in a feed (triple counts + object kinds)::

    python profile_predicate.py E5320.nt

Deep profile of one predicate (full IRI, or any unique substring of it)::

    python profile_predicate.py E5320.nt --predicate NFDI_0001008
    python profile_predicate.py E5320.nt E6304.nt --predicate "NFDI_0001008" --samples 15
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from typing import Iterator

RDF_TYPE = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
_HOST_RE = re.compile(r'^https?://([^/"]+)')


def iter_triples(paths: list[str]) -> Iterator[tuple[str, str, str]]:
    """Yield (subject, predicate, object) tokens from N-Triples file(s).

    Subject and predicate never contain spaces in N-Triples, so they are the
    first two whitespace-separated tokens; the object is everything else up to
    the trailing " .". Comment and blank lines are skipped.
    """
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.rstrip("\n")
                if not line or line[0] == "#":
                    continue
                if line.endswith(" ."):
                    line = line[:-2]
                elif line.endswith("."):
                    line = line[:-1]
                parts = line.split(" ", 2)
                if len(parts) < 3:
                    continue
                yield parts[0], parts[1], parts[2].strip()


def object_kind(obj: str) -> str:
    """Classify an object term as uri / bnode / literal / other."""
    if obj.startswith("<"):
        return "uri"
    if obj.startswith("_:"):
        return "bnode"
    if obj.startswith('"'):
        return "literal"
    return "other"


def object_datatype(obj: str) -> str | None:
    """Return the datatype IRI or @lang tag of a literal object, if any."""
    if not obj.startswith('"'):
        return None
    end = obj.rfind('"')
    if end <= 0:
        return None
    suffix = obj[end + 1 :]
    if suffix.startswith("^^<") and suffix.endswith(">"):
        return suffix[3:-1]
    if suffix.startswith("@"):
        return suffix  # language tag, e.g. @de
    return "(plain literal)"


def url_value(obj: str) -> str | None:
    """Extract a URL from a URI object or from a string-literal holding a URL."""
    if obj.startswith("<") and obj.endswith(">"):
        return obj[1:-1]
    if obj.startswith('"'):
        end = obj.rfind('"')
        if end > 0:
            return obj[1:end]
    return None


def host_of(value: str | None) -> str | None:
    """Return the host part of an http(s) URL, or None."""
    if not value:
        return None
    match = _HOST_RE.match(value)
    return match.group(1) if match else None


def overview(paths: list[str], top: int) -> None:
    """Print a one-line summary per predicate: count and object-kind mix."""
    counts: Counter[str] = Counter()
    kinds: dict[str, Counter[str]] = defaultdict(Counter)
    for _s, p, o in iter_triples(paths):
        counts[p] += 1
        kinds[p][object_kind(o)] += 1
    print(f"{'count':>12}  {'uri':>9} {'literal':>9} {'bnode':>9}  predicate")
    print("-" * 90)
    for pred, n in counts.most_common(top):
        k = kinds[pred]
        print(f"{n:>12}  {k['uri']:>9} {k['literal']:>9} {k['bnode']:>9}  {pred}")


def deep(paths: list[str], needle: str, top: int, samples: int) -> None:
    """Profile one predicate: subject types, object shape, URL hosts, samples."""
    subject_type: dict[str, str] = {}
    target_subjects: set[str] = set()
    obj_kinds: Counter[str] = Counter()
    datatypes: Counter[str] = Counter()
    hosts: Counter[str] = Counter()
    sample_rows: list[tuple[str, str]] = []
    triples = 0

    for s, p, o in iter_triples(paths):
        if p == RDF_TYPE:
            subject_type[s] = o
        if needle in p:
            triples += 1
            target_subjects.add(s)
            obj_kinds[object_kind(o)] += 1
            datatypes[object_datatype(o) or "(uri/bnode)"] += 1
            hosts[host_of(url_value(o)) or "(not a url)"] += 1
            if len(sample_rows) < samples:
                sample_rows.append((s, o))

    if not triples:
        print(f"No predicate containing {needle!r} found.")
        return

    type_dist: Counter[str] = Counter(
        subject_type.get(s, "(untyped)") for s in target_subjects
    )

    # Second pass: which *other* predicates do the target subjects also carry?
    # This reveals, e.g., whether url-bearing nodes are also identifier nodes.
    cooccur_subjects: dict[str, set[str]] = defaultdict(set)
    for s, p, _o in iter_triples(paths):
        if s in target_subjects and needle not in p and p != RDF_TYPE:
            cooccur_subjects[s].add(p)
    cooccur: Counter[str] = Counter()
    for preds in cooccur_subjects.values():
        for p in preds:
            cooccur[p] += 1

    n_subj = len(target_subjects)
    print(f"predicate matching: {needle!r}")
    print(f"triples: {triples:,}    distinct subjects: {n_subj:,}")

    print("\nsubject rdf:type distribution")
    for t, c in type_dist.most_common(top):
        print(f"  {c:>10,} ({100 * c / n_subj:5.1f}%)  {t}")

    print("\nobject kinds")
    for k, c in obj_kinds.most_common():
        print(f"  {c:>10,}  {k}")

    print("\nobject datatype / language")
    for d, c in datatypes.most_common(top):
        print(f"  {c:>10,}  {d}")

    print("\nobject URL hosts")
    for h, c in hosts.most_common(top):
        print(f"  {c:>10,}  {h}")

    print(f"\nco-occurring predicates (% of the {n_subj:,} subjects that also use them)")
    for p, c in cooccur.most_common(top):
        print(f"  {c:>10,} ({100 * c / n_subj:5.1f}%)  {p}")

    print("\nsample triples")
    for s, o in sample_rows:
        o_short = (o[:100] + "...") if len(o) > 100 else o
        print(f"  {s}  ->  {o_short}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile predicate usage in N-Triples data."
    )
    parser.add_argument("paths", nargs="+", help="one or more .nt files")
    parser.add_argument(
        "--predicate",
        help="profile only this predicate (full IRI or any substring of it); "
        "omit for an overview of all predicates",
    )
    parser.add_argument(
        "--top", type=int, default=25, help="rows to show per ranked list"
    )
    parser.add_argument(
        "--samples", type=int, default=10, help="example triples to print"
    )
    args = parser.parse_args()

    if args.predicate:
        deep(args.paths, args.predicate, args.top, args.samples)
    else:
        overview(args.paths, args.top)


if __name__ == "__main__":
    main()
