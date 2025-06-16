# AcousticBrainz Data Pipeline Documentation

This guide details all the steps required to translate raw data from AcousticBrainz into an RDF graph reconciled with Wikidata.

## Data Processing Pipeline

Change directory to `code/acousticbrainz` so that the paths in the scripts point to the correct files.

### 1. Fetching the Data

As per their [website](https://acousticbrainz.org/), AcousticBrainz is no longer updated as of 2022, but the data can still be downloaded. As per their [downloads page](https://acousticbrainz.org/download), the data is split into high and low level data, and each type is split into 30 archives, each containing 1 million JSON files, once for each recording. Most of low level data is coefficients and other calculated data, which is not useful to the datalake project. However, there are partial dumps in CSV that contain the information that is useful for us (e.g. key/tonality, bpm, etc). As such, we download the full high level data and the partial low level data.

Another thing to consider is that the high and low level dumps are respectively 39GB and 589GB compressed, while the partial low level dumps are 3GB compressed, so we also save a lot of space (and procesing time) by going with the partial dumps.

The dumps also contain every submission for every recording (~30 million), but there are quite a few recordings hat have multiple submissions, and the total number of recordings is closer to 7 million. It is mentioned on the website in 2022 that they would create another set of dumps that remove the duplicate data and only keep 1 submission per recording, but as of 2025, this has not been done.

I use the data dumps instead of downloading from the [API](https://acousticbrainz.readthedocs.io/api.html) as it requires less work on the acousticbrainz serveer and it is easier to process the data ourselves.

Run the following command to download all the high and low level files. Since the data isn't being updated, this should only need to be run once.

```bash
python fetch.py
```

The script will download all 30 high and low level files, and will output them in the `data/acousticbrainz/raw/highlevel/` and `data/acousticbrainz/raw/lowlevel/` folders, respectively. The script will skip all the files already downloaded, instead of redownloading them.
