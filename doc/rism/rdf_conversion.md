# RISM RDF Conversion

This document explains the RDF conversion process for RISM, from property mappings all the way to outputting a Turtle file.

## Mappings

The [`code/rism/mappings/property_mapping.json`](/code/rism/mappings/property_mapping.json) file contains the mappings from the properties used in the CSV files to the final properties used in the graph. Empty strings indicate that the property is ignored.

The [`code/rism/mappings/roles.json`](/code/rism/mappings/roles.json) file contains the mappings for all the roles used by the <https://rism.online/api/v1#hasRole> property. Empty strings indicate that the role is ignored as there is no analogous property on Wikidata. A thing to note is that quite a few roles are dummy URIs pointing to the library of congress database. For some roles, I can fairly reasonably understand the name of the relationship (e.g. <http://id.loc.gov/vocabulary/relators/father_of>), but other roles are single letters, so there's not much guessing that can be performed (e.g. <http://id.loc.gov/vocabulary/relators/g>) and thus are ignored.

The following list contains decisions made for specific roles:

- "former owner" is mapped to P127 because there is no dedicated property for former
- "is complemented by" is mapped to P527 "has part" because it's the closest thing I could find
- "dubious author" is mapped to P50 "author" because there's no dedicated property for a dubious author, that information would be contained in a statement/blank node

## Blank nodes

A vast quantity of data in RISM's original graph is stored in blank nodes. In order to reduce the amount of blank nodes and dummy URIs, the following actions are taken:

- For the <https://rism.online/api/v1#hasEncoding> property, we take the RDFS:label value of the blank node as the object for the triple, since we ignore the URL to the file.
- For the <https://rism.online/api/v1#hasRelationship> property, it points to a blank node with the <https://rism.online/api/v1#hasRole>, <http://purl.org/dc/terms/relation>, and <https://rism.online/api/v1#hasQualifier> properties. To construct the triple, we take the <https://rism.online/api/v1#hasRole> value of the blank node and run it through the role mapping to get the property, and we use the <http://purl.org/dc/terms/relation> value of the blank node as the object.
- For the <https://rism.online/api/v1#hasHolding> property, we take the <http://www.wikidata.org/prop/direct/P195> value of the blank node as the object for the triple.
- For the <http://www.wikidata.org/prop/direct/P921> property, we take the <http://wikidata.org/prop/direct/P2888> value if it is present, otherwise we take the rdf:value.
- For the <https://rism.online/api/v1#hasMaterialGroup> property, we do not currently do anything (see [#444](https://github.com/DDMAL/linkedmusic-datalake/issues/444))
- For the <http://www.wikidata.org/prop/direct/P585> property, it points to a blank node with <https://rism.online/api/v1#dateStatement>, <http://www.wikidata.org/prop/direct/P1319>, and <http://www.wikidata.org/prop/direct/P1326> properties. The dateStatement is a string representation of the date/range, and the other 2 properties indicate the start and end years. 2 triples are constructed, one for the start year and one for the end year, and they are constructed by traversing the blank node, and converting the object of the P1319 and P1326 triples to XSD:date on January 1st of the year.

## Entity Types

RISM already has their own set of dummy URIs for the type of each entity, of the form `f"https://rism.online/api/v1#{type}"` (e.g. <https://rism.online/api/v1#Incipit>). For consistency with all the other databases in the LinkedMusic graph, these types are converted to use the LinkedMusic dummy URIs, so `f"https://linkedmusic.ca/graphs/rism/{type}"` (e.g. <https://linkedmusic.ca/graphs/rism/Incipit>).

The list of types is:

- Institution
- Person
- Place
- Source
- Exemplar
- Incipit
- Subject

## General notes on the RDF conversion script

- The script will process each file in its own process. The number of processes/workers is currently set to 6 and can be edit at the top of the script.
- The `convert_rdf_object` function is made to be a one-stop shop to convert fields from the CSV files to the relevant RDFlib objects, handling all the necessary edge cases for the script to function as intended.
- The `old_graph` dictionary contains all triples for all non-basic entities (all entities that aren't people, institutions, or sources), to enable graph traversal during the RDF conversion process when it is necessary to access the data from a blank node or other entity. It is much more time- and space-efficient to store the temporary graph in a dictionary rather than an `rdflib.Graph` since the latter generates many more indices and has much more overhead, and provides no additional benefits.
- All the work on a single file is done by a single worker instead of having a worker for RDF conversion and one for serialization. This is due to the fact that the script isn't using a disk store for the graphs, and thus transferring the graph objects between processes is quite slow, negating any benefits from having multiple worker types.

## Future work

Currently, the RDF conversion script is built on the assumption that if a blank node is referenced in a CSV file (e.g. a source has a material group blank node), when that blank node will also appear in the same CSV file. A possible improvement is to solve this problem, so that data split between CSV files is not lost. A potential way to do this is to effectively combine all CSV files together when processing, and to split the graph by number of triples/chunks instead of making a graph per file (see the MusicBrainz RDF conversion script).

The [`reconciliation_todo.md`](/doc/rism/reconciliation_todo.md) file contains a list of future reconciliation work that was found when performing the RDF conversion process.
