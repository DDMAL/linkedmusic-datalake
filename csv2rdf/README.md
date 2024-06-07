# CSV -> RDF
The script csv2rdf_single_subject.py converts a reconciled CSV file into a RDF turtle file.
Steps:
1.  Get the file that needs to be converted from the target database.
    a. for example, in musicbrainz/csv, there is a script that converts the JSON file into a finite CSV file.
2.  Make that file into a CSV file and reconcile it.
    a. for the same example, in musicbrainz/csv/history, there are JSON files that has the reconciliation process in OpenRefine.
3.  Move the reconciled CSV file to this current folder.
4.  Run get_relations.py to generate a test.json file, rename it, and fill the values with the references to the key properties. For example:
{
    "id": "https://www.wikidata.org/wiki/Q853614",
    "type": [
        "https://www.wikidata.org/wiki/Q18127",
        "https://www.wikidata.org/wiki/Q13557414"
    ],
    "disambiguation": "https://www.wikidata.org/wiki/Q115916384",
    "video": "https://www.wikidata.org/wiki/Property:P10",      
}
* Object "type" should be a list of types with the same order.
5. Run csv2rdf_single_subject.py. Example execution:
python3 csv2rdf_single_subject.py reconciled_mb_area.csv reconciled_mb_label.csv reconciled_mb_recording.csv 
There can be as many as needed input csv files, and they will be merged into one single .ttl file.
6. This .ttl file can be imported into Virtuoso.
    