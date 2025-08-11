# Guide to RDF Config File Syntax

- This guide is meant to be a section of [General RDF Conversion Script: User Guide](./using_rdfconv_script.md). It is presented as a standalone document because the user may have to consult it more frequently.

- This guide will show you how to manually complete an RDF config file — what keywords to use, what syntax to follow, etc.

- It is suggested for the user to read [RDF Conversion Guideline on the Wiki](https://github.com/DDMAL/linkedmusic-datalake/wiki/RDF-Conversion-Guidelines) before following this guide. The former focuses on ontology design, whereas this guide explains the specific syntax of the config file required by the general RDF conversion script.

## Introduction

- The RDF config file is a TOML file generated with `/code/rdfconv/tomlgen.py`. See [Step 2. Create a TOML Configuration File](./using_rdfconv_script.md#step-2-create-a-toml-configuration-file) to learn how to create a new config file.

- The user must manually complete an RDF config file to decide what ontology the output TTL shall follow.

- A complete RDF config file is used as input to the General RDF Conversion Script. See [4. Running the Conversion Script](./using_rdfconv_script.md#4-running-the-conversion-script) for instructions on how to provide the RDF config file to the script.

## 1. General Structure of the RDF Config File

- The essence of the configuration file is that it contains the name of every single column from every single CSV in a specific `csv_folder`.
- The user must construct the RDF graph by linking columns together.
  - In almost all cases, the `subject` and the `object` should be found in the dataset — your task consists mainly of choosing the correct `predicate` that connects them.

### 1.1 Brief Introduction to TOML syntax

- TOML is very similar to JSON or Python nested dictionary objects.

- Read the [Official TOML Documentation](https://toml.io/en/v1.0.0) to learn more about TOML structure (it is very clear and concise).

#### 1.1.1 Note: TOML Sub-Tables

- According to TOML syntax, any table containing `.` in their name is a sub-table: they are equivalent to a key paired with an inline dictionary.

For example, this subtable:

```toml
[sets-reconciled.username]
    key1 = "value1"
    key2 = "value2"
```

Is equivalent to this inline dictionary:

```toml
[sets-reconciled]
    username = { key1 = "value1", key2 = "value2" }
```

- When updating a config file (see [Alternative Step 2: Update the Config File](./using_rdfconv_script.md#alternative-step-2-update-the-config-file)), inline dictionaries all become sub-tables. That's because `tomli-w` does not support writing inline dictionaries.

- For this reason, you may encounter sub-tables in a config file even though this guide only talks about [inline dictionaries](#22-understanding-inline-dictionary-mappings). This is not a problem, since sub-tables are functionally equivalent to inline dictionaries.

### 1.2 Structural Overview of the Config File

- Here is a quick overview of the structure of the TOML file. Each section will be explained in more detail

```
[general]
name
csv_folder
rdf_output_folder
test_mode

[namespaces]
<ns1>
<ns2>
<ns3>
...

[<csv0>]
PRIMARY_KEY
<col0>
<col1>
<col2>
...

[<csv1>]
PRIMARY_KEY
<col0>
<col1>
<col2>
...
```

### 1.3 The `[general]` table

- The `[general]` table defines core configuration settings
  - `name`: the name of the outputted ttl file (`name = "thesession"` results in `thesession.ttl` )
  - `csv_folder`: path to the directory containing CSV files to be converted (path is relative to `/code/rdfconv`)
  - `rdf_output_folder`: path to the directory where the ttl will be outputted (path is relative to `/code/rdfconv`; parent directory automatically created if needed)
  - `test_mode`: if set to `true`, generates a test TTL file (e.g., `thesession_test.ttl`) containing a sample of twenty rows from each CSV file.

Example of a `[general]` table:

```toml
[general]
name = "thesession"
csv_folder = "../../data/thesession/reconciled"
rdf_output_folder = "../../data/thesession/rdf"
test_mode = false
```

### 1.4 The `[namespaces]` table

- This table contains a list of prefixes and their corresponding URIs. Prefixes are short labels (like `rdf:` or `wd:`) used to simplify long URIs in RDF data.

- Note: Once a prefix is defined, URIs will be automatically shortened when serializing to TTL.

  - For example, by specifying `wdt = "http://www.wikidata.org/prop/direct/"`, all URI starting with `http://www.wikidata.org/prop/direct/` will use `wdt:` instead. This helps to make TTL file smaller and serialization faster

- Note: TTL syntax does not allow `/` after a prefix.

  - For example, `https://thesession.org/recordings/1` cannot be shortened to `ts:recordings/1`: to shorten the URI, you must define `tsr = "https://thesession.org/recordings/"`.

- Note: Config file namespaces determine TTL file prefixes. However, TTL file prefixes do not affect prefixes on Virtuoso (i.e. prefixes that can be used in a SPARQL query): these must be defined separately on the Virtuoso Conductor page (see [documentation on the Wiki](https://github.com/DDMAL/linkedmusic-datalake/wiki/List-of-Prefixes-for-SPARQL-Queries) for list of currently defined Virtuoso prefixes).

Example of `[namespaces]` table:

```toml
[namespaces]
rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
rdfs = "http://www.w3.org/2000/01/rdf-schema#"
xsd = "http://www.w3.org/2001/XMLSchema#"
wd = "http://www.wikidata.org/entity/"
wdt = "http://www.wikidata.org/prop/direct/"
geo = "http://www.opengis.net/ont/geosparql#"
skos = "http://www.w3.org/2004/02/skos/core#"
tse = "https://thesession.org/events/"
tst = "https://thesession.org/tunes/"
tsm = "https://thesession.org/members/"
tsr = "https://thesession.org/recordings/"
lmts = "https://linkedmusic.ca/graphs/thesession/"
```

### 1.5 The CSV tables.

- On top of `[general]` and `[namespaces]`, there is a table in the config file for every CSV file in the `csv_folder` directory.

  - For example, in `thesession.toml`, there is `[events-reconciled]`, `[tune-reconciled]`. The first stands for `events-reconciled.csv` and the second for `tunes-reconciled.csv`

- All keys in a CSV table, with the exception of `PRIMARY_KEY`, are names of columns within the corresponding CSV file.

  - It is important to update the config file before converting a new batch of reconciled CSV, as the column names may have changed (see [Alternative Step 2](./using_rdfconv_script.md#alternative-step-2-updating-the-config-file) for instructions on updating the config file)

- Each CSV table contains a `PRIMARY_KEY` field. The user must map it onto a column, whose values will act as the default subject for all RDF triples created from that CSV.
  - Do not be confused by the fact that the value of `PRIMARY_KEY` is also a key within the table: all columns are listed in the table, and one of them has to be the primary key.

Example of a completed CSV table (the meaning of the values will be explained in the next section):

```toml
[sessions-reconciled]
PRIMARY_KEY = "sessions_id"
sessions_id = { type = "lmts:Session" }
name = "P276"
address = ""
town = ""
coordinate = { pred = "P625", datatype = "geo:wktLiteral" }
```

## 2. Deeper Dive Into CSV Table Syntax

### 2.1 Understanding Simple String Mappings

Consider the following abstract CSV table

```toml
[example_file]
PRIMARY_KEY = "subject_column"
subject_column = ""
object_column0 = "predicate0"
object_column1 = "predicate1"
```

- The column `subject_column` is designated as the subject of each RDF triple, since it is marked as the `PRIMARY_KEY`.
- Each value in `object_column0` is linked to the value in `subject_column` from the same row using the predicate `predicate0`.
- Similarly, each value in `object_column1` is linked to `subject_column` using `predicate1`.
- To be clear, the values in `object_column0` and `object_column1` serve as **objects** in the generated triples — the subject is always from `subject_column`, since it is the `PRIMARY_KEY`.

Important distinctions:

    - Only columns explicitly associated with a predicate will produce RDF triples — in each such triple, the value from that column is always used as the object.
        - Any column left unpaired (i.e. with an empty value) is ignored during conversion, in the sense that there will be no triple where it act as object.
        - In the previous example, since `subject_column` serves as the subject, it doesn’t need to appear as the object in any triple.
        - If a column is never the subject, and is unpaired (i.e. is never the object), this means that it will be entirely omitted from the RDF output.

Let's use the following `events_example.csv` as a more concrete example:
| event_id | event_name |
| ---------- | ------------- |
| https://thesession.org/events/1 | Festival 2023 |
| https://thesession.org/events/2 | Jazz Night |

Its corresponding config file table should look like:

```toml
[events_example]
PRIMARY_KEY = "event_id"
event_id = ""
event_name = "rdfs:label"
```

Converting `events_example.csv` to RDF using the above config file would create the following TTL file:

```ttl
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<https://thesession.org/events/1> rdfs:label "Festival 2023" .
<https://thesession.org/events/2> rdfs:label "Jazz Night" .
```

- Note: When used in the config file, Wikidata properties do not need the prefix `wdt:` (i.e. you can write `P123` instead of `wdt:P123`)

#### 2.1.1 Note: `PRIMARY_KEY` and Fill Down

As explained in the [General RDF Conversion Script: User Guide](./using_rdfconv_script.md#11-note-column-fill-down), the RDF conversion scripts automatically performs a fill-down for empty cells in the CSV, which is an artifact of OpenRefine records (see [OpenRefine documentation on Records](https://openrefine.org/docs/manual/exploring#rows-vs-records))

For example:

```csv
Name,Email,Phone
Alice,a@example.com,123-456
,a.work@example.com,
Bob,b@example.com,789-000
,,789-001
Charlie,c@example.com,
```

Becomes:

```csv
Name,Email,Phone
Alice,a@example.com,123-456
Alice,a.work@example.com,123-456
Bob,b@example.com,789-000
Bob,b@example.com,789-001
Charlie,c@example.com,
```

- In the general RDF conversion script, fill-down continues only until a non-empty value is encountered in the column set to be `PRIMARY_KEY`.

  - When setting a `PRIMARY_KEY`, you need to ensure that values in this column is never empty at the beginning of a record `session_id` is a good `PRIMARY_KEY` within `sessions-reconciled.csv` because each record is guaranteed to have a `session_id`

- In the example above, the `PRIMARY_KEY` would have to be set to `Name`

### 2.2 Understanding Inline Dictionary Mappings

The `column = "predicate"` string mapping is not customizable enough for all use-cases. For instance, what if the column `username` needs a column other than the `PRIMARY_KEY` as subject? This is where an inline dictionary needs to be used.

Below is a list of keywords that can be used in a inline dictionary:

- `pred`: predicate to use to create the triple. Same as the predicate value you would put in a simple string mapping

  ```toml
  # Example
  country = {pred = "P17"}
  ```

- `datatype`: the datatype of the object. Only Literals can have a datatype: adding it to URIRefs has no effect. As per RDF rule, you can't specify both `datatype` and `lang` at the same time.

  - You can use prefixes instead of full URI as long as the prefixes are defined in `[namespaces]`
  - Common datatypes are: `xsd:date`, `xsd:dateTime`, and `geo:wktLiteral`

  ```toml
  coordinates = {pred = "P625", datatype = "geo:wktLiteral"}
  ```

- `lang`: the language label (using two letter language code) of the object. Only Literals can have a language label: adding it to URIRefs has no effect. As per RDF rule, you can't specify both `datatype` and `lang` at the same time.

  ```toml
  event_name = {pred = "rdfs:label", lang = "en"}
  ```

- `subj`: column whose value will act as subject instead of `PRIMARY_KEY`

  ```toml
  username = {pred = "rdfs:label", subj = "member_id"}
  ```

- `if`: condition that must be true for the triple to be created. It is evaluated for every row.

  - Available variables within the condition:
    - `subj` — the subject value for the triple (either from `PRIMARY_KEY` column or `subj` column defined in inline dictionary)
    - `obj` — the object value from the current column
    - `row` — a dictionary representing the entire CSV row (column names as keys)
  - Since values are transformed into either `URIRef` or `Literal` (both are `rdflib` classes) before triples are created, `instanceof()` can be used to conveniently evaluate whether value is one or the other.
    - The general RDF conversion script assumes all values starting with "http" to be `URIRef`. Specify the datatype to be `xsd:anyURI` if you wish for values in a column to remain `Literal` URLs.

  ```toml
  # Only create triple if the object is a Literal
  username = {pred = "rdfs:label", if = "isinstance(obj,Literal)"}
  ```

  - String comparison work on `URIRef` or `Literal`. However, you should convert them to string first if you want to use any string method.
    ```toml
    # Only create triple if object does not start with "M"
    username = {pred = "rdfs:label", if = "not str(obj).startswith('M')"}
    ```

Note that all keywords above would all be useless if `pred` is not defined within the dictionary: you cannot customize how the triple is created if it is not created at all!

However, the dictionary keywords below are still effective even when `pred` is not present

- `prefix`: prefix of the namespace to prepend to every value in this column

  - Allows replacing partial URI (e.g. "1") with full URI (e.g. "https://thesession.org/tunes/1"). Prefix expansion is performed prior to creating RDF triples, guaranteeing that only full URIs are stored within the graph.

  ```toml
  [namespaces]
  tst = "https://thesession.org/tunes/"

  [tunes-reconciled]
  tune_id = {prefix = "tst"}

  # "1" -> "https://thesession.org/tunes/1"
  # "2" -> "https://thesession.org/tunes/2"
  ```

- `type`: the class to which the values in this column are instances of

  - All values will be linked to the class using `rdf:type`
  - Indicating, for example, that `https://thesession.org/sessions/20` is an instance of `https://linkedmusic.ca/graphs/thesession/Session` makes it much easier to write queries that return only sessions.

  ```toml
  recording_id = {type = "lmts:Recording"}

  # Assuming that lmts = "https://linkedmusic.ca/graphs/thesession/"
  ```

## 3. Checklist for Completing The RDF Config

With the information above, you should be able to complete the RDF config.

Below is a checklist to follow along as you create your configuration file.

- Move any comment out of the config file and store them separately: comments have no permanence and are deleted upon config file update.

In the `[general]` table

- Set `name` and `rdf_output_folder`
- Set `test_mode` to `false` unless you are doing a test run (see [Test-Run RDF Conversion](./using_rdfconv_script.md#step-2-test-run-rdf-conversion))

In the `namespaces` table:

- Define every prefix you used elsewhere in the config file (e.g. `geo:`, `skos:`)
- Add a namespace for `https://linkedmusic.ca/graphs/{dataset}`: you will be using this namespace to create classes (see `type` keyword explanation in [Section 2.2](#22-understanding-inline-dictionary-mappings))
- (Optional) Define as many namespaces as possible in order to make URIs shorter (e.g. define `tss = "https://thesession.org/sessions/"` to make all session URIs shorter)

In each CSV table:

- Determine a `PRIMARY_KEY`

  - all values in this `PRIMARY_KEY` column must be an URI (full or partial)
  - Make sure that the column you have selected as `PRIMARY_KEY` has a value for every record (see [Section 2.1.1](#211-note-primary_key-and-fill-down)).

- Add a `prefix` to all columns that have only partial URI (e.g. "1" instead of `https://thesession.org/recordings/1`)
- Add a `type` to all columns that belong to a dataset-defined classes (e.g. `<https://thesession.org/recordings/2>` belongs to `https://linkedmusic.ca/graphs/thesession/Recording`).

  - Note how classes are named following `https://linkedmusic.ca/graphs/{dataset}/{SingularClassName}` convention.

- Choose the appropriate predicate for each column to be stored (the most important and time-consuming task)

  - Consult [Mapping against Wikidata properties using prop_cli.py](./rdf_property_mapping_guide.md) for general property mapping tips.
  - Consult [RDF Conversion Guideline on the Wiki](https://github.com/DDMAL/linkedmusic-datalake/wiki/RDF-Conversion-Guidelines) for detailed ontology design guideline.

- Ensure that all columns serving as `subj` contain only URIs

  - Any RDF triple where a Literal serves as subject is invalid.

- Add `datatype` for dates (`xsd:date`), datetime (`xsd:dateTime`) and coordinates (`geo:wktLiteral`).
  - When applicable, add `datatype` for Literals not listed above
- When applicable, add `lang` for Literals

Congratulations, the configuration file is now functionally complete. Return to [General RDF Conversion Script: User Guide](./using_rdfconv_script.md) and continue from [3. Verifying the Config File](./using_rdfconv_script.md#3-verifying-the-config-file)
