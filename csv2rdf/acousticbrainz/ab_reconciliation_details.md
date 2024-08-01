#   Properties:

##  Genres:

The reconciliation of AcousticBrainz properties are not specific. 
For genre properties, if the cells in that column is all literal objects, then the property uses the AcousticBrainz documentation page for that genre. Since AcousticBrainz documentations include links and detailed description for feature extraction of genres, I decide to use the source description of the property.
For the wikidata link objects, I have no choice but to use the wikidata property for "genre" (P136). Since the AcousticBrainz genre feature-extracted and is specified in much more details, this causes some loss of meaning in the detail of the genres. 
The same principle applies to the columns for mood.

## Machine Versions:

Since there is no properties in Wikidata and Schema.org, I choose the official download website for the feature extraction machines.
Build_sha and Git_sha are made-up URIs. It uses the same URI as essentia and gaia followed by a fragment identifier.
The probability for all features are also made-up URIs. It uses the same URI as the feature followed by a ".probability".

## made-up URIs:

metadata.tags.engineer
metadata.tags.mixer
metadata.tags.compilation
metadata.tags.notes
metadata.tags.ensemble
metadata.tags.replaygain_reference_loudness
metadata.tags.acoustid_id
metadata.tags.mp3gain_album_minmax
metadata.tags.mp3gain_minmax
metadata.tags.replaygain_album_gain
metadata.tags.replaygain_album_peak
metadata.tags.replaygain_track_gain
metadata.tags.replaygain_track_peak

#   Instances:
For testing, the gender and genres are reconciled against Wikidata.
Albums, artists, etc are reconciled against their MusicBrainz links since they already have MBIDs.