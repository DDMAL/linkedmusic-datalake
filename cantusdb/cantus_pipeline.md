#   CantusDB flattening and json-ld structures

> Summarize:   
>   1.  Get the data dumps for Cantus DB. (Todo)
>   2.  Reconcile the flattened csv dump
>   3.  Export and process after

##  1. How to Get Data Dumps
(Todo)

##  2. Reconciliation with OpenRefine
### Organizing the IDs
For column "cantus_id":
1.  In the arrow beside column names, choose "Edit cells" > "Transform"
2.  Copy and paste the following code to the box:
```python
if value is not None: return "https://cantusindex.org/id/" + value
else: return None
```
3.  Delete the chant_id column by "Edit column" > "Remove this column"
4.  Move the absolute_url to be beginning by "Edit column" > "Move column to beginning"
### Reconciliation
5.  Reconcile the "genre" column against "music genre" instance Q188451.
6.  Move the best candidate's score facet box to 99-101, match all of them to their best candidate.
7.  Reset the best candidate's score facet, choose none in the judgement facet, create new item for all of them.
8.  Reconcile the "mode" column against "mode" instance Q731978.
9.  Since the mode are numbers, we have to search for the mode names manually.
10. For example, if it's mode 1, then search for a new match > "mode 1" > "dorian mode".
11. For all uncertain modes, create a new item for each.
12. For the two reconciled columns, add column with URLs of matched entities.

##  3. Export and process after

##  2. Reconcile column names and generating json-ld 
### DEPRECATED
Currently the json-ld is generated as follow:
In `jsonld/generate_jsonld.py`
- Load the reconciled csv as a dataframe in pandas and convert them to json documents (each corresponds to an entry/line in the csv)
- Loop through each json document and edit each entry, creating the compact jsonld. More information can be found in `generate_jsonld.py`
- Generate the jsonld file at `compact.jsonld`
- The contexts used in the compact.jsonld file is imported from `context.jsonld`
