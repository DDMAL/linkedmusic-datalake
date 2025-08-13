# DTL1000 Workflow
## 1. Fetching Raw Data

The CSV containing the entire DTL1000 dataset (also referred to as the Dig That Lick Database) can be downloaded at the bottom of [this page](https://dig-that-lick.hfm-weimar.de/similarity_search/documentation).

It is named `dtl_metadata_v0.9.csv`. Please store it at `/data/digthatlick/raw`

## 2. Splitting and Cleaning the CSV file
Change working directory to `code/digthatlick`

- Run the following command
```python
python split_dtl1000.py [path to csv]
```
- The `[path to csv]` argument is not needed if the raw CSV is stored at `/data/digthatlick/raw`

### 2.1 Logic Behind This Step

- Splitting the CSV file is not strictly mandatory, since reconciliation and RDF conversion can happen without. However, it does makes the data much easier to navigate. 

- We split up the raw CSV into three files:
   - dtl1000_solos.csv 
    - dtl1000_tracks.csv 
    - dtl1000_performers.csv

- `solos.csv` contains all metadata unique to the solo (e.g. performers on the solo,  instrument used in the solo)
- `track.csv` contains all metadata unique to the track from which the solo is taken (e.g. recording location). It does not include performers
- `performers.csv`contains all track performers data. It is a separate file because track performers are often in multi-valued cells (i.e. multiple performer names in a single cell), splitting them into different cells create many extra rows, which would make `tracks.csv` unnecessarily large and cumbersome.


## Changes made to data during the split:

### solo_id column
We remove the 0's that are extra in the millisecond section of the times in the solo_id (see `digthatlick_data_schema.md` for the explanation).

### track_id column
We make a new column `track_id` based on the solo_id column, it is the same as the solo_id but without the time stamps, since this is unique for each track.
This new column gets added to all 3 files as a way to link performers to a track and solos to a track.


### Instrument_label column (this is for soloist) 
To help reconciliation, we expand the abbreviation with this map:
```
{
    "as": "alto saxophone",
    "bs": "bari saxophone",
    "cl": "clarinet",
    "cor": "cornet",
    "fl": "flute",
    "flg": "flugelhorn",
    "ss": "soprano saxophone",
    "tb": "trombone",
    "tp": "trumpet",
    "ts": "saxophone",
    "vib": "vibraphone",
    "vln": "violin",
    "voc": "voice",
}
```
This way the instruments could be used as property `instrument` to be more accurate when reconciling the column solo_performer_name against type human.
But notice ts (tenor saxophone) became saxophone, this is because we noticed for some musicians in wikidata their instrument is listed as just saxophone. I think it is better to do just saxophone as it still matches the tenor players, but tenor saxophone wouldnt match as well the people who just have saxophone in their wikidata.
After the reconciliation is done we will transform saxophone to tenor saxophone so that it can be reconciled to the actual instrument tenor saxophone.

### possible solo performer names
we split this column to allow for reconciliation on each person.

### performers
Split this column so each person has their own row. We didn't include their instrument abbreviations, as they didn't seem entirely necessary and some people had multiple instruments, just made it complicated.

###
Remove the solo start and end from all of them as it is already part of the solo_id.


# Reconciling
So far leader_name and most of solo_performer_name have been reconciled.
see reconciliation_procedures.md for the steps to take in openrefine.


# mapping reconciled files to rdf using schema