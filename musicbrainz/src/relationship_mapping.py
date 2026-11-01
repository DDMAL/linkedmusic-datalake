"""Validated relationship mappings and the bounded contributor-role pilot."""

import hashlib
import json
import re
from dataclasses import dataclass
from urllib.parse import urlsplit
from uuid import UUID

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, XSD

WDT = Namespace("http://www.wikidata.org/prop/direct/")
TERMS = Namespace("https://linkedmusic.ca/terms/musicbrainz/")
ROLE = Namespace(f"{TERMS}relationship/")
OBSERVATION = Namespace("https://linkedmusic.ca/graphs/musicbrainz/relationship/")
MB = Namespace("https://musicbrainz.org/")
ENTITY = Namespace("https://linkedmusic.ca/graphs/musicbrainz/")
VERSION = TERMS["mapping/contributor-pilot-v1"]
MODEL_DOCUMENT = URIRef(
    "https://github.com/DDMAL/linkedmusic-datalake/blob/main/"
    "musicbrainz/doc/relationship_preservation.md"
)


def predicate_iri(value):
    """Accept a Wikidata PID or an absolute HTTP(S)/URN IRI, never concatenate both."""
    if not isinstance(value, str) or re.search(r'[\s<>"{}|\\^`]', value):
        raise ValueError(f"Invalid relationship predicate: {value!r}")
    if re.fullmatch(r"P[1-9][0-9]*", value):
        return WDT[value]
    parts = urlsplit(value)
    if (parts.scheme in ("http", "https") and parts.netloc) or (
        parts.scheme == "urn" and parts.path
    ):
        return URIRef(value)
    raise ValueError(f"Expected a PID or absolute IRI: {value!r}")


@dataclass(frozen=True)
class RoleMapping:
    type_id: str
    predicate: URIRef
    subject_type: str
    object_type: str
    label: str
    definition: str
    source: URIRef
    broader: URIRef | None

    @classmethod
    def parse(cls, value, subject_type, object_type):
        required = {
            "type_id",
            "predicate",
            "subject_type",
            "object_type",
            "label",
            "definition",
            "source",
            "broader",
        }
        if set(value) != required:
            raise ValueError(f"Role mapping requires exactly these fields: {required}")
        type_id = value["type_id"]
        if not isinstance(type_id, str) or str(UUID(type_id)) != type_id:
            raise ValueError(f"Invalid relationship type UUID: {type_id!r}")
        if (
            subject_type not in ("recording", "release")
            or object_type != "artist"
            or value["subject_type"] != subject_type
            or value["object_type"] != object_type
        ):
            raise ValueError("Structured role mappings are restricted to the pilot")
        if value["predicate"] != str(ROLE[type_id]):
            raise ValueError("Pilot predicates must use the stable source type UUID")
        if value["source"] != f"{MB}relationship/{type_id}":
            raise ValueError("Source definition must refer to the same type UUID")
        for key in ("label", "definition"):
            if not isinstance(value[key], str) or not value[key].strip():
                raise ValueError(f"Missing readable {key}")
        broader = predicate_iri(value["broader"]) if value["broader"] else None
        if broader not in (None, WDT.P767):
            raise ValueError("Only the reviewed P767 alignment is supported")
        return cls(
            type_id,
            predicate_iri(value["predicate"]),
            subject_type,
            object_type,
            value["label"],
            value["definition"],
            URIRef(value["source"]),
            broader,
        )


class RelationshipMappings(dict):
    """Keep legacy lookups while indexing pilot roles by source type UUID."""

    def __init__(self, raw):
        super().__init__()
        self.by_id = {}
        for source_type, targets in raw.items():
            self[source_type] = {}
            for target_type, entries in (targets or {}).items():
                converted = {}
                for name, value in (entries or {}).items():
                    if isinstance(value, dict):
                        value = RoleMapping.parse(value, source_type, target_type)
                        if value.type_id in self.by_id:
                            raise ValueError(f"Duplicate role type ID: {value.type_id}")
                        self.by_id[value.type_id] = value
                    elif value is not None:
                        value = predicate_iri(value)
                    converted[name] = value
                self[source_type][target_type] = converted

    def preserve_role(self, graph, source, source_type, target_type, relation):
        """Return True if this is pilot evidence (including unresolved evidence).

        MusicBrainz orders these endpoints artist -> recording/release. RDF roles
        are deliberately defined in the reverse direction: work -> artist.
        Unknown IDs never inherit a role solely from a coincident label.
        """
        type_id = relation.get("type-id")
        role = self.by_id.get(type_id)
        candidate = (
            self.get(source_type, {}).get(target_type, {}).get(relation.get("type"))
        )
        if not role and source_type == "artist":
            candidate = (
                self.get(target_type, {}).get("artist", {}).get(relation.get("type"))
            )
        if not role and not isinstance(candidate, RoleMapping):
            return False

        target_data = relation.get(target_type.replace("-", "_")) or {}
        target_id = target_data.get("id") if isinstance(target_data, dict) else None
        target = URIRef(f"{MB}{target_type}/{target_id}") if target_id else None
        expected_direction = "forward" if source_type == "artist" else "backward"
        status = "mapped"
        if not type_id:
            status = "missing-type-id"
        elif role is None:
            status = "unrecognized-type-id"
        elif (source_type, target_type) not in (
            (role.subject_type, role.object_type),
            (role.object_type, role.subject_type),
        ):
            status = "unexpected-endpoints"
        elif relation.get("direction") != expected_direction:
            status = "unexpected-direction"
        elif target is None:
            status = "missing-target"

        # Include the entire source relationship JSON, without guessing missing
        # attribute identifiers or coercing partial dates to invented full dates.
        payload = json.dumps(
            relation, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
        digest = hashlib.sha256(f"{source}\n{payload}".encode("utf-8")).hexdigest()
        node = OBSERVATION[digest]
        graph.add((node, RDF.type, TERMS.RelationshipObservation))
        graph.add((node, DCTERMS.source, source))
        graph.add((node, TERMS.sourcePayload, Literal(payload, datatype=RDF.JSON)))
        graph.add((node, TERMS.mappingVersion, VERSION))
        graph.add((node, TERMS.mappingStatus, Literal(status)))
        for key, pred in (
            ("type-id", TERMS.sourceTypeId),
            ("type", TERMS.sourceTypeName),
            ("direction", TERMS.sourceDirection),
            ("begin", TERMS.begin),
            ("end", TERMS.end),
            ("ended", TERMS.ended),
        ):
            if key in relation and relation[key] is not None:
                graph.add((node, pred, Literal(relation[key])))
        for attribute in relation.get("attributes", []):
            graph.add((node, TERMS.attribute, Literal(attribute)))
        for key, pred in (
            ("attribute-ids", TERMS.attributeIds),
            ("attribute-values", TERMS.attributeValues),
            ("attribute-credits", TERMS.attributeCredits),
        ):
            if key in relation:
                graph.add(
                    (
                        node,
                        pred,
                        Literal(
                            json.dumps(
                                relation[key], sort_keys=True, ensure_ascii=False
                            ),
                            datatype=RDF.JSON,
                        ),
                    )
                )
        if status != "mapped":
            return True

        subject, obj = (target, source) if source_type == "artist" else (source, target)
        graph.add((subject, role.predicate, obj))
        graph.add((node, RDF.type, RDF.Statement))
        graph.add((node, RDF.subject, subject))
        graph.add((node, RDF.predicate, role.predicate))
        graph.add((node, RDF.object, obj))
        graph.add((node, TERMS.sourceRelationshipType, role.source))
        # The pilot does not materialize broader assertions. Schema-path queries
        # expose the reviewed alignment without claiming every contributor is an engineer.
        return True

    def schema_graph(self):
        graph = Graph()
        graph.bind("mbrel", ROLE)
        graph.bind("mbterm", TERMS)
        graph.bind("wdt", WDT)
        for role in self.by_id.values():
            graph.add((role.predicate, RDF.type, RDF.Property))
            graph.add((role.predicate, RDFS.label, Literal(role.label, lang="en")))
            graph.add(
                (role.predicate, RDFS.comment, Literal(role.definition, lang="en"))
            )
            graph.add((role.predicate, DCTERMS.source, role.source))
            graph.add((role.predicate, DCTERMS.isPartOf, VERSION))
            graph.add((role.predicate, RDFS.domain, ENTITY[role.subject_type.title()]))
            graph.add((role.predicate, RDFS.range, ENTITY.Artist))
            if role.broader:
                graph.add((role.predicate, RDFS.subPropertyOf, role.broader))
        for term, label, description in (
            (
                "RelationshipObservation",
                "Source relationship observation",
                "A relationship as supplied on one MusicBrainz record. Multiple observations can describe the same relationship; this is not a MusicBrainz relationship instance ID.",
            ),
            (
                "sourcePayload",
                "Source relationship JSON",
                "Complete source relationship object, including unrecognized fields and null values, as rdf:JSON. Subject is an observation; object is a JSON literal.",
            ),
            (
                "sourceTypeId",
                "Supplied relationship type ID",
                "Source type UUID as supplied; does not identify an individual relationship.",
            ),
            (
                "sourceTypeName",
                "Supplied relationship type name",
                "Source relationship label, retained even when it differs from the current definition.",
            ),
            (
                "sourceDirection",
                "Supplied relationship direction",
                "Forward or backward relative to MusicBrainz endpoint order, not the direction of the emitted RDF role.",
            ),
            (
                "sourceRelationshipType",
                "MusicBrainz relationship definition",
                "Observation to official source relationship definition. This does not assert that LinkedMusic terms form an official MusicBrainz ontology.",
            ),
            (
                "begin",
                "Supplied relationship begin date",
                "Unmodified date text for the role. May be empty, year-only, or year-month; not a release or recording date.",
            ),
            (
                "end",
                "Supplied relationship end date",
                "Unmodified date text for the role. No missing month or day is invented.",
            ),
            (
                "ended",
                "Supplied ended flag",
                "Source boolean on an observation; false is retained and is distinct from missing.",
            ),
            (
                "attribute",
                "Supplied relationship attribute",
                "Source attribute label on an observation. May modify a role, such as assistant, and does not describe the artist in every context.",
            ),
            (
                "attributeIds",
                "Supplied attribute identifiers",
                "Source attribute-name to identifier mapping as rdf:JSON.",
            ),
            (
                "attributeValues",
                "Supplied attribute values",
                "Source attribute values as rdf:JSON, preserving keys and associations.",
            ),
            (
                "attributeCredits",
                "Supplied attribute credits",
                "Source credit text as rdf:JSON, preserving keys and associations.",
            ),
            (
                "mappingVersion",
                "Relationship mapping version",
                "Observation to the version of the local mapping used to interpret it.",
            ),
            (
                "mappingStatus",
                "Relationship mapping status",
                "Mapped, or a reason a direct role was withheld. Unresolved observations retain their source payload.",
            ),
        ):
            uri = TERMS[term]
            graph.add((uri, RDFS.label, Literal(label, lang="en")))
            graph.add((uri, RDFS.comment, Literal(description, lang="en")))
            graph.add(
                (
                    uri,
                    RDF.type,
                    RDFS.Class if term == "RelationshipObservation" else RDF.Property,
                )
            )
            graph.add((uri, DCTERMS.source, MODEL_DOCUMENT))
            if term != "RelationshipObservation":
                graph.add((uri, RDFS.domain, TERMS.RelationshipObservation))
                if term in ("mappingVersion", "sourceRelationshipType"):
                    range_type = RDFS.Resource
                elif term == "ended":
                    range_type = XSD.boolean
                elif term in (
                    "sourcePayload",
                    "attributeIds",
                    "attributeValues",
                    "attributeCredits",
                ):
                    range_type = RDF.JSON
                else:
                    range_type = XSD.string
                graph.add((uri, RDFS.range, range_type))
        return graph
