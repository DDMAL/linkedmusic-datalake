# AcousticBrainz Data Pipeline Documentation

This guide details all the steps required to translate raw data from AcousticBrainz into an RDF graph reconciled with Wikidata.

## Data Processing Pipeline

Change directory to `code/acousticbrainz` so that the paths in the scripts point to the correct files.

### 1. Fetching the Data

As per their [website](https://acousticbrainz.org/), AcousticBrainz is no longer updated as of 2022, but the data can still be downloaded. As per their [downloads page](https://acousticbrainz.org/download), the data is split into high and low level data, and each type is split into 30 archives, each containing 1 million JSON files, once for each recording. Most of low level data is coefficients and other calculated data, which is not useful to the datalake project. However, there are partial dumps in CSV that contain the information that is useful for us (e.g. key/tonality, bpm, etc). As such, we download the full high level data and the partial low level data.

Another thing to consider is that the high and low level dumps are respectively 39GB and 589GB compressed, while the partial low level dumps are 3GB compressed, so we also save a lot of space (and procesing time) by going with the partial dumps.

The dumps also contain every submission for every recording (~30 million), but there are quite a few recordings hat have multiple submissions, and the total number of recordings is closer to 7 million. It is mentioned on the website in 2022 that they would create another set of dumps that remove the duplicate data and only keep 1 submission per recording, but as of 2025, this has not been done.

I use the data dumps instead of downloading from the [API](https://acousticbrainz.readthedocs.io/api.html) as it requires less work on the acousticbrainz serveer and it is easier to process the data ourselves.

Run the following command to download all the high level files and the partial low level dumps. Since the data isn't being updated, this should only need to be run once.

```bash
python fetch.py
```

The script will download all 30 high and low level files, and will output them in the `data/acousticbrainz/raw/highlevel/` and `data/acousticbrainz/raw/lowlevel/` folders, respectively. The script will skip all the files already downloaded, instead of redownloading them.

### 2. Extracting the data

The data is compressed using [zstandard](https://en.wikipedia.org/wiki/Zstd), and the full dumps contain 1 JSON file per recording. The files in these dumps are organized in the following directory structure `acousticbrainz-highlevel-json-20220623/{type}/{ab}/{c}/{mbid}-{n}.json` where `type` is either `lowlevel` or `highlevel`, `abc` are the first 3 digits (in hexadecimal) of the MBID for the recording, `mbid` is the full MBID for the recording, and `n` is the submission number for that recording (starting at 0).

Since the full dumps contain 1 JSON file per entry (and there are 29.5M entries), storing 1 json file per entry is not realistic. As such, the extraction script will output the data in JSON Lines files, where each line will be a full JSON entry. There will be 256 JSONL files, from `00.jsonl` to `ff.jsonl`, indicating the first 2 digits of the MBID for the recording. In addition, since the submission number is only stored in the name of the JSON file, the script will also output a `versions.json` file that contains a list of versions for each recording ID, in the order in which they appear in the JSONL files.

The partial dumps are much simpler, containing a single CSV file in the `acousticbrainz-lowlevel-features-20220623` folder.

The [`code/acousticbrainz/untar.py`](/code/acousticbrainz/untar.py) script will extract all files from the tarfiles, ignoring the outermost directory and following the structure described above.

Run the following command to extract all compressed files:

```bash
python untar.py
```
