"""City/region provenance evidence; see doc/source_provenance.md."""

import hashlib
import json
import re

from rdflib import Literal, Namespace, RDF
from rdflib.namespace import DCTERMS, XSD

LM = Namespace("https://linkedmusic.ca/graphs/diamm/")
DIAMM = Namespace("https://www.diamm.ac.uk/")
PLACE_TABLES = {"city": "cities", "region": "regions"}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f"non-JSON numeric constant: {value}")


def provenance_source_id(entry):
    """Accept the source-detail URLs exposed by the inspected serializers."""
    if not isinstance(entry, dict) or not isinstance(entry.get("url"), str):
        raise ValueError("provenance entry requires a source URL")
    match = re.fullmatch(
        r"https?://www\.diamm\.ac\.uk/sources/([1-9][0-9]*)/?", entry["url"]
    )
    if not match:
        raise ValueError(f"unsupported provenance source URL: {entry['url']!r}")
    return int(match[1])


def provenance_relation(field, place_id, entry):
    """Keep the complete parsed entry in the relation's deduplication key."""
    try:
        source_id = provenance_source_id(entry)
        evidence = json.dumps(
            entry,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (ValueError, TypeError) as error:
        raise ValueError(
            f"Invalid provenance for {field}:{place_id}: {error}"
        ) from error
    return {
        "key1": f"{field}:{place_id}",
        "key2": f"source:{source_id}",
        "type": "provenance",
        "source_provenance": evidence,
    }


def add_source_provenance(graph, row, field, place_id, source_id):
    """Preserve a qualified observation, or explicitly mark a legacy relation."""
    context = f"{row['key1']} -> {row['key2']}"
    if row.get("type") not in (None, "", "provenance"):
        raise ValueError(f"Unsupported provenance relation type for {context}")
    source = DIAMM[f"sources/{source_id}"]
    place = DIAMM[f"{PLACE_TABLES[field]}/{place_id}"]
    evidence = row.get("source_provenance") or ""
    entry = None
    if evidence:
        try:
            entry = json.loads(
                evidence,
                object_pairs_hook=_unique_object,
                parse_constant=_invalid_constant,
            )
            if provenance_source_id(entry) != source_id:
                raise ValueError("evidence URL disagrees with the source endpoint")
        except (ValueError, TypeError) as error:
            raise ValueError(
                f"Invalid source_provenance for {context}: {error}"
            ) from error

    # Identity includes both typed endpoints and the exact CSV evidence. It is
    # independent of input order; conflicting entries cannot exchange qualifiers.
    identity = json.dumps(
        [str(source), str(place), evidence], ensure_ascii=False, separators=(",", ":")
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    observation = LM[f"source-provenance/{digest}"]
    graph.add((source, LM.sourceProvenance, observation))
    graph.add((observation, RDF.type, LM.SourceProvenanceObservation))
    graph.add((observation, LM.place, place))
    graph.add((observation, DCTERMS.source, place))
    graph.add((observation, LM.sourceField, Literal(field, datatype=XSD.string)))

    def flag(value):
        graph.add((observation, LM.validationFlag, Literal(value)))

    if entry is None:
        flag("legacy-unqualified-provenance")
        return
    graph.add(
        (observation, LM.sourceProvenanceJson, Literal(evidence, datatype=XSD.string))
    )

    uncertain_field = f"{field}_uncertain"
    if type(entry.get(uncertain_field)) is bool:
        graph.add((observation, LM.uncertain, Literal(entry[uncertain_field])))
    else:
        status = (
            "missing"
            if uncertain_field not in entry
            else "null" if entry[uncertain_field] is None else "invalid"
        )
        flag(f"{status}-uncertainty")

    years = {}
    for key, predicate in (
        ("earliest_year", LM.earliestYear),
        ("latest_year", LM.latestYear),
    ):
        value = entry.get(key)
        # bool is a subclass of int in Python, but is not a source year. Numeric
        # strings/floats also remain raw evidence rather than guessed repairs.
        if type(value) is int and 1 <= value <= 9999:
            years[key] = value
            graph.add(
                (
                    observation,
                    predicate,
                    Literal(f"{value:04d}", datatype=XSD.gYear, normalize=False),
                )
            )
        else:
            status = (
                "missing"
                if key not in entry
                else "null" if value is None else "invalid"
            )
            flag(f"{status}-{key.replace('_', '-')}")
    if len(years) == 2 and years["earliest_year"] > years["latest_year"]:
        flag("reversed-year-bounds")
