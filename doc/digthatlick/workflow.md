# Workflow
## dtl_metadata_v0.9.csv

we split up the file into three smaller csv files: dtl1000_solos.csv, dtl1000_tracks.csv, dtl1000_performers.csv.
Since each row in the file corresponded to a single solo and some tracks have multiple solos, we decided to split up to make reconciling faster and for rdf
The three new files contain information on solos, tracks, and performers.
the solos file contains the columns soloid, soloist (and potential soloists) and instrment, then a track_id to link back to the track
tracks have a track id, and then the band leader, band, all the track stuff like when and where recorded
performers, since each track had multiple performers listed, we wanted to expand that column out to reconcile each performer, but then we would have had so many duplicate
track information, so this one is also separate, its 

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