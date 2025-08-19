# General notes

- We are ignoring Parlametrics for now, as it concerns conversations which are not directly related to music.
- We are ignoring latitude and longitude for now, as locations
- The Urban Strain files are incoherent and so are skipped for now
    - After much searching within both the files and on the Global Jukebox website, we were unable to match the songs in the files to songs on the website and vice versa
    - The metadata file is also clearly incomplete; there is not even a clear primary key column

# Column notes
- `C-id` references songs found in the dataset.
    - Use prefix "gjs", which will expand to "https://theglobaljukebox.org/song/"
- Columns with titles matching `*_cid` (found in Societies files) indicate whether the target society is found within the relevant datasets (cantometrics, parlametrics, minutage, etc)
