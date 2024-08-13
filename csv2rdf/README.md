# CSV -> RDF

The script csv2rdf_single_subject.py converts a reconciled CSV file into a RDF turtle file.
Steps:

1.  Move the reconciled CSV file to this current folder.

2.  Run `get_relations.py` to generate a mapping.json file. 
```python3 get_relations.py thesession/``` -> generates `thesession/mapping.json`
This mapping.json file will contain all the headers from the input CSV files as keys in a JSON dictionary, and their respective values are empty strings. The users should fill all the empty values with corresponding Wikidata or Schema.org property links, etc.

3.  e.g. part from `thesession/mapping.json`:
```
{
    "entity_type": {
        "aliases.csv": "http://www.wikidata.org/entity/Q61002",
        "events.csv": "http://www.wikidata.org/entity/Q1656682",
        "recordings.csv": "http://www.wikidata.org/entity/Q273057",
        "sessions.csv": "http://www.wikidata.org/entity/Q932410",
        "sets.csv": "http://www.wikidata.org/entity/Q36161",
        "tune-popularity.csv": "http://www.wikidata.org/entity/Q1357284",
        "tunes.csv": "http://www.wikidata.org/entity/Q170412"
    },
    "tune_id": "https://thesession.org/tunes",
    "alias": "http://www.wikidata.org/prop/direct/P742",
    "name": "http://www.wikidata.org/prop/direct/P2561",
    "events_id": "https://thesession.org/events",
    "event": "http://www.wikidata.org/prop/direct/P2561",
    "dtstart": "http://www.wikidata.org/prop/direct/P580",
    "dtend": "http://www.wikidata.org/prop/direct/P582",
    "venue": "http://www.wikidata.org/prop/direct/P276",
}
```
* Object "entity_type" should be a dict of types (instances, not properties) mapped to the filename.

5. Run csv2rdf_single_subject.py. 

e.g.
```python3 csv2rdf_single_subject.py thesession/mapping.json thesession/*.csv```
```python3 csv2rdf_single_subject.py cantus/mapping.json cantus/*.csv```
...

There can be as many input csv files as needed, and they will be merged into one single `out_rdf.ttl` file inside the target database folder. 

6. This `out_rdf.ttl` file can be imported into Virtuoso.