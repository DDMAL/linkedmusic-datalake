# AcousticBrainz Reconciliation

Since all entries in AcousticBrainz pertain to a recording in MusicBrainz, we do not need to reconcile the entries themselves as we can simply link them to the MusicBrainz entities. As such, the only things that need reconciliation the values for certain fields that pertain to tonality, mood, genre, etc.

This file will describe steps take for each field, and the `acousticbrainz/openrefine/` folder will contain history and export files for the reconciliation.

Keep in mind that all metadata in AcousticBrainz is extracted using Essentia (machine learning models). Values for fields like gender and genre are not ground truth and may contain errors.

## Gender

The values were reconciled against Q48277 "gender".

## Genres

The values were reconciled against Q188451 "music genre".

### Genre Dortmund
Some genre categories are overly broad and cannot be cleanly reconciled to Wikidata.
-"Folkcountry" was lef unreconciled.
-"Funksoulrnb" was reconciled to Q45981 "rhythm and blues".
-"Raphiphop" was reconciled to Q11401 "hip-hop".

### Genre Electronic
No comments.

### Genre Rosamerica
"Speech" was reconciled to Q52946 "speech".
The "speech" genre is not music, but rather spoken audio from advertisements, debates or sports transmission. See page 47 of [Guaus, E. (2009). Audio content processing for automatic music genre classification: descriptors, databases, and classifiers (Doctoral dissertation, Universitat Pompeu Fabra, Barcelona)](https://www.tesisenred.net/bitstream/handle/10803/7559/tegt.pdf?sequence=1&isAllowed=y).

## ismir04_rhythm

The values were reconciled against Q107357104 "type of dance".

## Mood

This file contains a mix of genres and emotions.

-Reconcile cells to Q188451 "music genre".
-Reconcile remaining cells to Q9415 "emotion".
-Reconcile "relaxed" to Q110690264 "carefree".

## Moods Mirex

This file does not describe what the clusters themselves represent. This information is instead provided on the [2010 MIREX Audio Music Mood Classification page](https://music-ir.org/mirex/wiki/2010:Audio_Music_Mood_Classification). The clusters represent the following:

-Cluster_1: passionate, rousing, confident, boisterous, rowdy
-Cluster_2: rollicking, cheerful, fun, sweet, amiable/good natured
-Cluster_3: literate, poignant, wistful, bittersweet, autumnal, brooding
-Cluster_4: humorous, silly, campy, quirky, whimsical, witty, wry
-Cluster_5: aggressive, fiery, tense/anxious, intense, volatile, visceral

 Since these are all broad categories, they were all left unreconciled.

## Timbre

This file only contains bright and dark, which are not Wikidata entities in the timbral sense. They were left unreconciled.

## Tonal Atonal/Tonality

Straightforward reconciliation against Q192822 "tonality".

## Voice Instrumental

Reconcile "instrumental" to Q639197 "instrumental music".
Reconcile "voice" to Q685884 "vocal music".
