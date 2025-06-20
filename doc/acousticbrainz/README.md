# AcousticBrainz Data Pipeline Documentation

This guide details all the steps required to translate raw data from AcousticBrainz into an RDF graph reconciled with Wikidata.

## Data Processing Pipeline

Change directory to `code/acousticbrainz` so that the paths in the scripts point to the correct files.

### 1. Fetching the Data

As per their [website](https://acousticbrainz.org/), AcousticBrainz is no longer updated as of 2022, but the data can still be downloaded. As per their [downloads page](https://acousticbrainz.org/download), the data is split into high and low level data, and each type is split into 30 archives, each containing 1 million JSON files, once for each recording. Most of low level data is coefficients and other calculated data, which is not useful to the datalake project. 

However, there are partial dumps in CSV for "features", which are subsets of the 3 "subtypes" of lowlevel data `tonal`, `rhythm` and `lowlevel`. The `tonal` dump contains information about the tonality, the `rhythm` dump contains information about the bpm, and the `lowlevel` dump contains some coefficients about spectral data.

Another thing to consider is that the high and low level dumps are respectively 39GB and 589GB compressed, while the partial low level dumps are 3GB compressed, so we also save a lot of space (and procesing time) by going with the partial dumps.

As such, we will be downloading and processing the full highlevel dumps, and the partial `tonal` and `rhythm` dumps.

The dumps also contain every submission for every recording (~30 million), but there are quite a few recordings hat have multiple submissions, and the total number of recordings is closer to 7 million. It is mentioned on the website in 2022 that they would create another set of dumps that remove the duplicate data and only keep 1 submission per recording, but as of 2025, this has not been done.

I use the data dumps instead of downloading from the [API](https://acousticbrainz.readthedocs.io/api.html) as it requires less work on the acousticbrainz server and it is easier to process the data ourselves.

Run the following command to download all the high level files and the partial low level dumps. Since the data isn't being updated, this should only need to be run once.

```bash
python fetch.py
```

The script will download all 30 high level files and the 2 partial lowlevel dumps, and will output them in the `data/acousticbrainz/raw/highlevel/` and `data/acousticbrainz/raw/` folders, respectively. The script will skip all the files already downloaded, instead of redownloading them.

### 2. Extracting the data

The data is compressed using [zstandard](https://en.wikipedia.org/wiki/Zstd), and the full dumps contain 1 JSON file per recording. The files in these dumps are organized in the following directory structure `acousticbrainz-highlevel-json-20220623/{type}/{ab}/{c}/{mbid}-{n}.json` where `type` is either `lowlevel` or `highlevel`, `abc` are the first 3 digits (in hexadecimal) of the MBID for the recording, `mbid` is the full MBID for the recording, and `n` is the submission number for that recording (starting at 0).

Since the full dumps contain 1 JSON file per entry (and there are 29.5M entries), storing 1 json file per entry is not realistic. As such, the extraction script will output the data in JSON Lines files, where each line will be a full JSON entry. There will be 256 JSONL files, from `00.jsonl` to `ff.jsonl`, indicating the first 2 digits of the MBID for the recording.

However, since the submission numbers are only stored in the file name, the script will add a `submission_number` field to each entry that indicates the submission number. The script will also keep track of the highest submission number for each recording and will output that dictionary to a `versions.json` file.

The script will also skip any entries for which an entry with a later submission number has already been extracted. There will still be multiple entries for each recording, but this is the best way to reduce the amount of duplicates without running through the data a second time.

The partial dumps are much simpler, containing a single CSV file in the `acousticbrainz-lowlevel-features-20220623` folder.

The [`code/acousticbrainz/untar.py`](/code/acousticbrainz/untar.py) script will extract all files from the tarfiles, ignoring the outermost directory and following the structure described above.

Run the following command to extract all compressed files:

```bash
python untar.py
```

### 3. Reconciliation

All objects in AcousticBrainz are recordings, and their ID is the same as their MusicBrainz Recording ID, and MusicBrainz is already reconciled with Wikidata, so there is no need to reconcile the recordings themselves against Wikidata. The only thing that will need reconciling is the values of the fields (e.g. the key/tonality).

The values for the `genre_tzanetakis` and `genre_rosamerica` fields are acronyms. The acronyms are expanded according to the following documentation: [this paper](https://web.archive.org/web/20120530070141/http://marsyas.info/docs/manual/marsyas-user.pdf) (page 30) for `genre_tzanetakis` and [this page](https://acousticbrainz.org/datasets/accuracy#genre_rosamerica) for `genre_rosamerica`.
