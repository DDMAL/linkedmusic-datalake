# 11-8-2024
RISM: No progress. Andrew replied under the issue saying that my data is not the correct one. I stopped experimenting with the data, progress is same as last week.
MusicBrainz & all other potential Databases: applied new logic:
### Using JSON logic:
> advantages:
1. RDF have the same logic as JSON, conserves the data structure perfectly. No need to worry about having complex data structure which CSV could not handle.
2. CSV had too much unecessary nested columns due to the JSON structure, making the reconciliation very confusing. This can prevent it, making reconciliation much more simplier.
3. No data lost, unlike CSV, where we must cut some data, otherwise the CSV will have blank cells for the most part.
4. RDF could also be imported into OpenRefine for reconciliation. We can skip CSV, which is an extra process.
> disadvantage:
1. Implemented using Blank Nodes, might be difficult to query.
