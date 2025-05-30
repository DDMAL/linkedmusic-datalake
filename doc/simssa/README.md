# SimssaDB Documentation

## 1.  Get CSV from SQL

Using the steps described in `simssadb_pipeline.md ## 1. Extracting columns and feature flattening`, we get the `final_flattened.csv`. This CSV merges all tables in the SQL file into one single CSV. The database has multiple files that aren't linked to any musical work, so they are ignored.

## 2.  How to choose entities

In the new CSV, the `musical_work_id` is chosen to be the primary key.
