# CantusDB flattening and json-ld structures

> Summarize:   
>   1.  Get the data dumps for Cantus DB. (Todo)
>   2.  Reconcile the flattened csv dump
>   3. 

## 1. How to Get Data Dumps
(Todo)

## 2. Reconciliation with OpenRefine
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

## 2. Reconcile column names and generating json-ld 
### DEPRECATED
Currently the json-ld is generated as follow:
In `jsonld/generate_jsonld.py`
- Load the reconciled csv as a dataframe in pandas and convert them to json documents (each corresponds to an entry/line in the csv)
- Loop through each json document and edit each entry, creating the compact jsonld. More information can be found in `generate_jsonld.py`
- Generate the jsonld file at `compact.jsonld`
- The contexts used in the compact.jsonld file is imported from `context.jsonld`
