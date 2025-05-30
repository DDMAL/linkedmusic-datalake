# Workflow
# stuff we did to the data to help reconciling


## dtl1000 or file name dtl_metadata_v0.9.csv

we split up the file into three smaller csv files.
Since each row in the file corresponded to a single solo and some tracks have multiple solos, we decided to split up to make reconciling faster and for rdf
now 3 files: solos, tracks, performers
the solos just have soloid soloist (and potential soloists) and instrment, then a track_id to link back to the track
tracks have a track id, and then the band leader, band, all the track stuff like when and where recorded
performers, since each track had multiple performers listed, we wanted to expand that column out to reconcile each performer, but then we would have had so many duplicate
track information, so this one is also separate, its 

## Changes made to data during the split to make stuff easer:

### solo_id column
Because of that weird thing with the extra zeros, we just removed the zeros
also made a new column based on this column, track_id, which is just the first ?? characters, as we noticed before is unique for each track
this new column got added to all 3 files as a way to link performers to track and soloist to track


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
This way the instruments could be used as property `instrument` to be more accurate when reconciling the column solo_performer_name against type human
But notice ts (tenor saxophone) became saxophone, this is because we noticed in wikidata  for all musicians who play tenor saxophone their instrument was listed as just saxophone. (just kidding) some are listed as just saxophone.... hmmmm so i think it was better to do just saxophone as it still matched the tenor players, but tenor saxophone wouldnt match well the people who just have saxophone in their wikidata
After the reconciliation is done we will transform saxophone to tenor saxophone so that it can be reconciled to the actual instrument tenor saxophone
abbreviated, note for reconciliation, expanded to match with wikidata, also used as property instrument for reconcile solo performer, but ts becomes saxophone because whenever someone plays tenor sax, for some reason in wikidata they just put saxophone
put back to tenor saxophone after

### possible solo performer names
we split this column to allow for reconciliation on each person

### performers
split this column so each person has their own row
got rid of instrument, maybe good idk

###
removed the solo start and end from all of them as it is part of the solo_id






# then reconciling
when reconciling band leader names and soloist names found some trouble matching some people to wikidata



# mapping reconciled files to rdf using schema