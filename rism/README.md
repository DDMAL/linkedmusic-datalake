Data dump address: from Andrew Hankinson

for data folder:
1. output: contains the final partially reconciled RDF
2. raw: 
In this folder, "rism-test-100000.ttl" is an excerpt from the original RISM RDF(rendered in n-triples format, where there are numerous blank nodes identified by their ID numbers); "output.ttl" is the RDF turtles converted from the "rism-test-100000.ttl" file. In "output.ttl", the blank nodes are represented using square brackets “[]” 
3. reconciled
Mapping.json is the record for classes and properties mapping
"output-ttl.csv" is the output from open refine after reconciliation based on the input RDF (that is output.ttl of raw folder)