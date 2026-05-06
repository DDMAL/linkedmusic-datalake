# Weimar Jazz Database OpenRefine Reconciliation Procedures

This guide covers the steps to take to clean and reconcile the Weimar Jazz Database in OpenRefine. More specifically, the following CSV files will be reconciled before being converted to RDF:

- `solo_info.csv`
- `composition_info.csv`
- `record_info.csv`
- `track_info.csv`

The JSON files located in `wjazzd/openrefine` can be used to automatically apply the procedures detailed below.

## solo_info.csv

- The performer column must be reconciled to the type `human (Q5)`. Some musicians need to be manually selected amongst matching people with similar names
- The `instrument` column must be expanded using the dictionary below, before being reconciled:

```json
{
  "as": "Alto Saxophone",
  "bcl": "Bass Clarinet",
  "bs": "Bass Saxophone",
  "cl": "Clarinet",
  "cor": "Cornet",
  "g": "Guitar",
  "p": "Piano",
  "ss": "Soprano Saxophone",
  "tb": "Trombone",
  "tp": "Trumpet",
  "ts": "Tenor Saxophone",
  "ts-c": "C Melody Saxophone",
  "vib": "Vibraphone"
}
```

- The `style` column should be prepended `" jazz"` and then reconciled
- The `key` column should be processed using the following Jython expression, then reconciled; strings like "C-dor" will be left unreconciled

```python
if value.endswith("maj"):
    return value[:-3] + " major"
elif value.endswith("min"):
    return value[:-3] + " minor"
else:
    return value
```

- The `signature` column should be reconciled with time signatures

## composition_info.csv

- The ids in `compid` are unfortunately slightly misaligned with the ones in Jazztube, which the URI should reference. Run the following Python command to align the ids:
```python
num = int(value)
if num >= 156:
    num += 1

# Step 2
if num >= 276:
    num += 1

# Step 3
if num >= 281:
    num += 1

return str(num)
```
- The column `genre` has two possible values: `"Original"` and `Great American Songbook`. The former should be deleted (it will not be stored); the latter should be reconciled to `Great American Songbook (Q1151397)`.
- In the column `template`, the value `blues` should be expanded to `twelve-bar blues`, the column should then be reconciled
- For the column `composer`, do the following steps:
  1. Split multi-valued cell at `,` (e.g. `"Parker, Gillespie` should be split in two)
  2. Spilt multi-valued cell at `/` (e.g. `Carmichael/Parish` should be split in two)
  3. Trim leading and trailing whitespace
  4. Create a separate `jazz musician` column, filled entirely with the value `"jazz musician"`. Reconcile the `composer` column using `jazz musician` as the `occupation (P106)`: this should improve the accuracy of reconciliation. Delete the `jazz musician` column after reconciliation.
  5. After the first reconciliation, you will do a second reconciliation for `composer` that have been unmatched. This time, you should create a column filled with the value `"composer"`
  6. Repeat the same process for the profession `"songwriter"`

## record_info.csv

- The column `artist` must have its multi-valued cells split at `/`, and then reconciled
- The column `label` must have its multi-valued cells split at `/`, and then reconciled. This reconciliation requires slightly more manual verification.

## track_info.csv

- For the column `lineup` (and `instrument` column, which we will create from it), do the following steps:

  1. Split multi-valued cell in the column `lineup` at `;` (e.g. `"Art Pepper (as, cl); Charles Haden (b)` should be split in two)
  2. Create a new column `instrument` based on the `lineup` column. Use the following GREL regex: `value.match(/.*\(([^)]+)\).*/)[0]`
  3. Split multi-valued cell in the column `instrument` at `,` (e.g. `"as, cl"` should be split in two)
  4. Delete the parenthesis containing the instrument from the `lineup` column (e.g. `"Charles Haden (b)` becomes `Charles Haden`). Use the following GREL regex: `value.replace(/\s*\(.*\)\s*/, "")`
  5. Trim whitespace for both columns
  6. Expand the column `instrument` using the following dictionary

  ```python
  jazz_instruments = {
  "arr": "",
  "as": "Alto Saxophone",
  "b": "Bass",
  "B": "Bass",
  "bc": "Bass Clarinet",
  "bcl": "Bass Clarinet",
  "bgo": "Baritone Guitar",
  "bjo": "Banjo",
  "bs": "Baritone Saxophone",
  "cga": "Congas",
  "cl": "Clarinet",
  "cn": "Conga",
  "cor": "Cornet",
  "dr": "Drums",
  "eb": "Electric Bass",
  "electric p": "Electric Piano",
  "fl": "Flute",
  "flgn": "Flugelhorn",
  "g": "Guitar",
  "git": "Guitar",
  "hca": "Harmonica",
  "key": "Keyboard",
  "p": "Piano",
  "p-tp": "Piccolo Trumpet",
  "perc": "Percussion",
  "rhodes": "Rhodes Piano (Electric Piano)",
  "ss": "Soprano Saxophone",
  "synth": "Synthesizer",
  "tb": "Trombone",
  "tp": "Trumpet",
  "trp": "Trumpet",
  "ts": "Tenor Saxophone",
  "ts-c": "Tenor Saxophone C-melody",
  "Vc": "Cello",
  "vcl": "Vocals",
  "vib": "Vibraphone",
  "voc": "Vocals"
  }
  ```

  7. Reconcile both the `instrument` and `lineup` column

- The `recordingdate` column has many entity that needs to be cleaned up:

  1. Apply the following Jython command to clean up most of the badly formatted cells:

  ```python
  import re

  def extract_date(value):
      g = re.search(r"(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{4})$", value)

      if g:
          day = g.group(1).zfill(2)
          month = g.group(2).zfill(2)
          year = g.group(3)
          return year + "-" + month + "-" + day
      else:
          return value

  return extract_date(value)
  ```

  2. Apply the following Jython command to clean up a few remaining cells in the format of `January, 1999`

  ```python
  import re

  def extract_date(value):
      month_dict = {
      "january":   "01",
      "february":  "02",
      "march":     "03",
      "april":     "04",
      "may":       "05",
      "june":      "06",
      "july":      "07",
      "august":    "08",
      "september": "09",
      "october":   "10",
      "november":  "11",
      "december":  "12"
      }

      g = re.search(r"([A-Za-z]+)\s*(\d{4})$", value)

      if g:
          day = "01"
          month = month_dict[g.group(1).lower()]
          year = g.group(2)
          return year + "-" + month + "-" + day
      else:
          return value

  return extract_date(value)
  ```

  3. Apply the following command to expand years (e.g. `1999`) to a date (e.g. `1999-01-01`)

  ```python
  import re

  def extract_date(value):
      g = re.match(r"\d{4}", value)

      if g:
          return g.group(1)+"-01-01"
      else:
          return value

  return extract_date(value)
  ```

