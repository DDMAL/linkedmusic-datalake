# CSV -> RDF
The script csv2rdf_single_subject.py converts a reconciled CSV file into a RDF turtle file.
Steps:
1.  Get the file that needs to be converted from the target database.
    *   for example, in musicbrainz/csv, there is a script that converts the JSON file into a finite CSV file.
2.  (Optional) Make that file into a CSV file and reconcile it. 
    *   for the same example, in musicbrainz/csv/history, there are JSON files that have the reconciliation process in OpenRefine.
3.  Move the reconciled CSV file to this current folder.
4.  Run get_relations.py to generate a mapping.json file. This mapping.json file will contain all the headers from the input CSV files as keys in a JSON dictionary, and their respective values are empty strings. The users should fill all the empty values with corresponding Wikidata or Schema.org property links(etc.). 
5.  The operation flow should be:
    1.  Run get_relations.py with all CSV files needed.
    2.  Get the mapping.json.
    3.  Fill the empty values.
    4.  For example:
{
    "area_id": "https://www.wikidata.org/wiki/Property:P982",
    "sort-name": "https://www.wikidata.org/wiki/Property:P2561",
    "relations_wiki": "https://www.wikidata.org/wiki/Property:P1687",
    "type": "https://www.wikidata.org/wiki/Property:P2308",
    "annotation": "https://www.wikidata.org/wiki/Property:P2916",
    "name": "https://www.wikidata.org/wiki/Property:P2561",
    "disambiguation": "https://schema.org/disambiguatingDescription",
    "type-id": "https://musicbrainz.org/doc/Label/Type",
    "genres_name": "https://www.wikidata.org/wiki/Property:P136",
    "genres_id": "https://www.wikidata.org/wiki/Property:P8052",
    "entity_type": {
        "area.csv": "http://www.wikidata.org/entity/Q2221906",
        "event.csv": "http://www.wikidata.org/entity/Q1656682",
        "genre.csv": "http://www.wikidata.org/entity/Q188451",
        "instrument.csv": "http://www.wikidata.org/entity/Q34379",
        "label.csv": "http://www.wikidata.org/entity/Q18127",
        "recording.csv": "http://www.wikidata.org/entity/Q15975575"
    },
    "event_id": "https://www.wikidata.org/wiki/Property:P6423"
}
* Object "entity_type" should be a dict of types (instances, not properties) mapped to the filename.
5. Run csv2rdf_single_subject.py. Example execution:
    python3 csv2rdf_single_subject.py mapping.json area.csv artist.csv genre.csv recording.csv ...
There can be as many input csv files as needed, and they will be merged into one single out_rdf.ttl file. The "entity_type" should contain the types of entities of these input files respectively.
6. This out_rdf.ttl file can be imported into Virtuoso.
    