#   1.  Get CSV from SQL

**This is not completed, consider reworking.**

Using the steps described in `simssadb_pipeline.md ## 1. Extracting columns and feature flattening`, we get the `final_flattened.csv`. This CSV merges all tables in the SQL file into one single CSV. For this single CSV to be better converted into RDF using the csv2rdf script, different entities should be separated to other CSV file. For example, in the `final_flattened.csv`, after line 496, the `musical_work_id` is no longer the primary key of the records. 

>   TODO: modify the SQL query script to do the work automatically without merging

#   2.  Test files
Cut & Paste all texts after line 496 into another CSV file, import it into OpenRefine, and delete the previous two empty columns.

>   TODO: make this process automatic or get rid of this

#   3.  How to choose entities
In the new CSV, the `source_id` is chosen to be the new primary key. In this case, for the csv2rdf script to process the data correctly, the records with `musical_work_id` as the primary key and the records with `source_id` as the primary key should exist in two different CSV files.