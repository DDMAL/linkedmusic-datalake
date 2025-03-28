# This folder "csv2rdf" mainly store the reconciled RDF files for different databases. It also documents different approaches of CSV2RDF (see ...HowToConvertCSV2RDFIntoVirtuoso folder)

# CSV -> RDF

The script "csv2rdf_single_subject.py" converts a reconciled CSV file into a RDF turtle file.
    Why is it called "single_subject"? Because it serves the occasion where each CSV file is structured around a primary entity, which is consistently located in the first column. The remaining columns provide properties related to this central entity. 
Steps:

1.  Set up the child folder for each database such as thesession, MusicBrainz, cantus... 
Move the “reconciled CSV” file to the corresponding child folder, such as events-csv.csv, recordings-csv.csv in thesession
(Notion: by "reconciled CSV", it only means the instances are reconciled while the properties, types/classes are not reconciled, which should be done manually in the next step
Please refer to DDMAL / linkedmusic-datalake / Wiki / Guidelines or suggestions for data reconciliation... [https://github.com/DDMAL/linkedmusic-datalake/wiki/Guidelines-or-suggestions-for-data-reconciliation-(updated-from-time-to-time;-collecting-advice-from-everyone)]
)

2.  Schema mapping/definition:
Run `get_relations.py` to generate a mapping.json file, E.g.:
```python3 get_relations.py thesession/``` -> generates `thesession/mapping.json`
The mapping.json file will be structured as a JSON dictionary. The keys will represent all the headers from the input CSV files, and each key will initially have an empty string as its value. Users are expected to then fill in these empty string values with corresponding Wikidata property/entity_type URIs (or Schema.org's), etc.

3.  e.g. snippet from `thesession/mapping.json`:
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

4.  In addition, there is a log file for each database. The file is named "AccountForReconciliation_updated".

5.  Run csv2rdf_single_subject.py. 

e.g.
```python3 csv2rdf_single_subject.py thesession/mapping.json thesession/*.csv False```
```python3 csv2rdf_single_subject.py cantus/mapping.json cantus/*.csv True```
...

There can be as many input csv files as needed, and they will be merged into one single `out_rdf.ttl` file inside the target database folder.
The last parameter is a boolean that indicates whether the output TTL file should be in separate files identified by the CSV file (True) or if the output TTL should be in one single large graph (False).

6.  This `out_rdf.ttl` file can be imported into Open Link Virtuoso.

7.  In https://virtuoso.staging.simssa.ca, navigate to ```Conductor > Login > Linked Data > Quad Store Upload > Choose File > Create graph explicitly (select its corresponding check box) > Rename the "Name Graph IRI*" > Upload```
Before uploading to a existing graph, if you do not delete the existing graph in ```Linked Data > Graphs > Graphs > Delete the graph```, the upload process will append to the existing graph.


# 