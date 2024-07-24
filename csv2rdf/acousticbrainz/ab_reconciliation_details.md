#   Properties:
The reconciliation of AcousticBrainz properties are not specific. 
For genre properties, if the cells in that column is all literal objects, then the property uses the AcousticBrainz documentation page for that genre. Since AcousticBrainz documentations include links and detailed description for feature extraction of genres, I decide to use the source description of the property.
For the wikidata link objects, I have no choice but to use the wikidata property for "genre" (P136). Since the AcousticBrainz genre feature-extracted and is specified in much more details, this causes some loss of meaning in the detail of the genres. 
The same principle applies to the columns for mood.

#   Instances:
For testing, the gender and genres are reconciled against Wikidata.
Albums, artists, etc are reconciled against their MusicBrainz links since they already have MBIDs.