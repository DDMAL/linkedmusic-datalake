# General Notes:

- The Global Jukebox data dump can be found in the 8 repositories in [The Global Jukebox Github](https://github.com/theglobaljukebox).
  > IMPORTANT: Before reconciling a column, make a copy first titled `[Name_literal]` in order to preserve the string literals.
      - If splitting columns, make the copies after splitting the column, as a string literal list is not helpful when querying.
- For each dataset in The Global Jukebox, the `codings.csv` file is skipped, as it does not contain easily reconcilable data.
- The `data.csv` files are also not particularly useful for reconciliation, as they depend on the codings found in `codings.csv` and, consequently, not much easily reconilable to WikiData. However, depending on the data set, there may be a few columns that can be reconciled.
- By reconciling the remaining files, we should be able to link the surrounding information that can be found in WikiData.
- The datasets are small, so it is possible to manually reconcile many of the columns after a first automatic pass (or a few passes).

# Applying Histories:

> Do this before reading further.

- In the `reconciliation_history` folder, JSON files are generated in OpenRefine via `Undo/Redo > Extract... > Export`.
- These files can be applied to a specific CSV in OpenRefine by using `Undo/Redo > Apply...` and selecting the corresponding JSON.
- This process might cause errors during reconciliation. If this happens, please check below for detailed reconciliation instructions.

# Exporting Data:

- When exporting to CSV, choose `Export > Custom Tabular...`
- For each reconciled column, make sure you select the "Matched entity's ID" option.
- Before exporting, make sure to copy and save the Option Code.
- To export, select "Comma-separated values (CSV)" and click "Download".

# Instruments

## Data

- Reconcile the cells in column `Instrument_Name` to type `type of musical instrument` (Q17362829) using `Sachs_Number` as property `Hornbostel-Sachs classification` (P1762).
  - Manually match any items that seem like they would get automatically mismatched/missed.
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 80-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `Archival_Culture_Name` to type `ethnic group` (Q41710).
  - Manually match any items that seem like they would get automatically mismatched/missed.
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 78-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.

## Societies

- Reconcile the cells in column `Region` to type `geographic region` (Q82794).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `Division` to type `geographic region` (Q82794).
  - Manually match "Central Africa" to `Central Africa` (Q27433).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Split the column `alternative_names` into several columns using `;` as the separator.
- Reconcile the cells in column `society` to type `ethnic group` (Q41710) with `alternative_names 1` as property `alternative name` (P4970).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 71-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Split the column `Koppen_climate_terrain` into several columns using `,` as the separator.
- Reconcile the cells in each `Koppen_climate_terrain` column to type `category in the Köppen climate classification systems` (Q23702033).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 57-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Text transform the cells in column `ISO6393` using the GREL regex `value.replace(/^ISO 639-3: /, "")`
- Reconcile the cells in column `Language` to type `modern language` (Q1288568), using the column `ISO6393` as property `ISO 639-3 code (P220)`.
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 62-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the `Language family` columns to type `language family (Q25295)`.
- Split the column `Country` into several columns using `;` as the separator.
- Reconcile the cells in each `Country` column to type `sovereign state` (Q3624078).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 100-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.

## Instrument

- Reconcile the cells in column `Archival_Culture_Name` to type `ethnic group` (Q41710).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `Instrument_Name` to type `type of musical instrument` (Q17362829) using `Sachs_Number` as property `Hornbostel-Sachs classification` (P1762) and `Alt_Instrument_Names` as property `alternative name` (P4970).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 62-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.

## Sources

- Reconcile the cells in column `Culture New` to type `ethnic group` (Q41710) using `Culture Old` as property `alternative name` (P4970).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 71-72. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `Author` to type `person` (Q5).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 100-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.

# Cantometrics

## Societies

- Reconcile the cells in column `Region` to type `geographic region` (Q82794).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `Division` to type `geographic region` (Q82794). - Manually match "Central Africa" to `Central Africa` (Q27433). - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present. - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none." - Match the cells using `reconcile > actions > match each cell to its best candidate`. - Remove both facets.
  > Note: The `Subregion` and `Area` columns may also be reconciled to `geographic region` (Q82794) and/or `human settlement` (Q486972), but these columns are often more difficult to sufficiently reconcile as they contain a mix of subsections of regions not found in WikiData (like "North Central China") or a mix of countries, states, and other areas of countries which are not always easy to reconcile.
- Split the column `alternative_names` into several columns using `;` as the separator.
- Reconcile the cells in column `society` to type `ethnic group` (Q41710) with `alternative_names 1` as property `alternative name` (P4970).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 71-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `People` to type `ethnic group` (Q41710) with `People2` as property `alternative name` (P4970).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 71-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Split the column `Koppen_climate_terrain` into several columns using `,` as the separator.
- Reconcile the cells in each `Koppen_climate_terrain` column to type `category in the Köppen climate classification systems` (Q23702033).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 57-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Text transform the cells in column `ISO6393` using the GREL regex `value.replace(/^ISO 639-3: /, "")`
- Reconcile the cells in column `Language` to type `modern language` (Q1288568), using the column `ISO6393` as property `ISO 639-3 code (P220)`.
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 62-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Reset the `Best candidate's score` facet.
  - Rereconcile the cells in column `Language` to type `dialect` (Q33384).
  - Remove both facets.
- Reconcile the `Language family` columns to type `language family (Q25295)`.
- Split the column `Country` into several columns using `;` as the separator.
- Reconcile the cells in each `Country` column to type `sovereign state` (Q3624078).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 100-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.

## Songs

- Reconcile the cells in column `Region` to type `geographic region` (Q82794).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `Division` to type `geographic region` (Q82794).
  - Manually match "Central Africa" to `Central Africa` (Q27433).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `Subegion` to type `geographic region` (Q82794).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `Preferred_name` to type `ethnic group` (Q41710).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 71-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Add a column named `country` based on the column `Society_location` using the GREL regex `value.replace(/\[.*?\]/, "").replace(/.*,\s*/, "")`.
- Add a column named `area` based on the column `Society_location` using the GREL regex `value.replace(/,.*/, "")`.
- Reconcile the new `country` column to type `sovereign state` (Q3624078).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 100-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the new `area` column to type `human settlement` (Q486972) using `country` as the property `country` (P17).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 100-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Split the column `Genre` into several columns using `;` as the separator.
- Reconcile the cells in each `Genre` column to type `song type` (Q107356781).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 71-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Split the column `Instruments` into several columns using `;` as the separator.
- Remove any leading or trailing whitespace.
- Text transform the `Instruments` columns using the GREL regex `value.replace(/^\d+-\d+\s*/, "").replace(/\d+\s*/, "").replace(/s$/, "")` to remove trailing "s" and any numbers at the beginning.
- Reconcile the cells in the first three `Instruments` columns to type `voice type` (Q1063547).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 71-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Manually match "Dancers" to `dancers` (Q13000618)
- Reconcile the cells in each `Instruments` column after the first one to type `family of musical instruments` (Q1254773).
- Split the column `Vocalist_gender` into several columns using `;` as the separator.
- Reconcile the cells in each `Vocalist_gender` column to type `sex of humans` (Q4369513).
  - Manually match the cells.
- Split the column `Recorded_by` into several columns using `;` as the separator.
- Reconcile the cells in each `Recorded_by` column to type `human` (Q5).
  - Manually match the cells.

# Phonotactics

## Phonotactics

- Reconcile the cells in column `Region` to type `geographic region` (Q82794).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `Division` to type `geographic region` (Q82794).
  - Manually match "Central Africa" to `Central Africa` (Q27433).
  - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
  - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
  - Match the cells using `reconcile > actions > match each cell to its best candidate`.
  - Remove both facets.
- Reconcile the cells in column `Subegion` to type `geographic region` (Q82794).
  - Manually match the cells.
- Reconcile the cells in column `Area/Kingdom` to type `human settlement` (Q486972).
  - Manually match the cells.
- Reconcile the cells in column `Culture` to type `ethnic group` (Q41710).
  - Manually match the cells.
- Split the column `Culture_loc` into several columns using `,` as the separator.
- Reconcile the `Culture_loc` columns to type `sovereign state` (Q3624078) or `human settlement` (Q486972), as appropriate.
  - Manually match the cells.
- Split the column `Genre` into several columns using `;` as the separator.
- Reconcile the cells in each `Genre` column to type `song type` (Q107356781).
  - Manually match the cells.
- Split the column `Instruments` into several columns using `;` as the separator.
- Reconcile the cells in each `Instruments` column to type type `family of musical instruments` (Q1254773) or `voice type` (Q1063547), as appropriate.
  - Manually match the cells.

## Societies

- Follow the instructions for the [Cantometrics Societies](#societies-1) file.

# Parlametrics

## Conversation

- Reconcile the cells in column `CultureName_Speaker1` to type `ethnic group` (Q41710).
  - Manually match the items.
  - If the culture does not exist in WikiData, match with the location or the language, whichever is more specific.
- In `Type_TypeCategory`, match "raw audio" to `Raw audio (Q3415066)`
- In `Monologue/Dialogue`, match "monologue" to `monologue (Q261197)` and "dialogue" to `dialogue (Q131395)`.
- Create a new column `speaker gender` based on the column `Speakers_Gender/Number/Age` using the GREL regex `value.replace(/[0-9]+/, "").toLowercase().replace(/\b(in|his|their|speaker|subject|her|and|age|several|s|ages)\b/, "").replace(/\(.*?\)/, "").replace(/s\b/, "").replace(/s\b/, "").replace(/s\b/, "").replace(/;/, ",").replace(/;/, ",").replace(/;/, ",").replace(/-/, "")` (There is definitely a more concise way to isolate the words "male" and "female" but value.match did not seem to work)
- Split the new `speaker gender` column into several columns using "," as the separator.
- Reconcile each `speaker gender` column against `sex of humans (Q4369513)`.
- Reconcile the cells in column `SubjectLanugage_SIL` and `SubjectLanguage_Given` to `modern language (Q1288568)`.
- Reconcile the cells in column `SubjectDialect_Given` to `dialect (Q33384)` using `SubjectLanguage_SIL` as property `part of (P361)`
  - Manually match the items.
- Split the column `Location_Recorded` into several columns using "," as the separator
- Reconcile each `Location_Recorded` column against `sovereign state (Q3624078)` or `human settlement (Q486972)` or both, depending on the values
  - Manually match the items
- Split the column `Coverage` into several columns using "," as the separator
- Reconcile each `Coverage` column against `sovereign state (Q3624078)` or `human settlement (Q486972)` or both, depending on the values
  - Manually match the items
- Split the column `All_Languages_On_Tape` into several columns using "," and then again using ";" as the separator
  - Reconcile each `All_Languages_On_Tape` column against `modern language (Q1288568)`
- Reconcile the column `Digitized.On` against `business (Q1317270)`
- Reconcile the column `Resource_Type` against `document genre (Q107478770)`.
- Match "primary text" in the column `Linguistic-Type` with `primary source (Q112754)`.

## Societies

- Follow the instructions for the [Cantometrics Societies](#societies-1) file.

## Data

- Reconcile the `Parla_Language_Name` column against `modern language (Q1288568)`
- Reconcile the `Culture` column against `ethnic group` (Q41710).

# Minutage

## Phrasing

- Reconcile the cells in column `Region` to type `geographic region` (Q82794).
- Reconcile the cells in column `Division` to type `geographic region` (Q82794).
- Split the column `Area/Kingdom` into several columns using "/" as the separator.
- Reconcile each `Area/Kingdom` column to type `area (Q1414991)`.
- Reconcile the cells in column `Culture` to type `ethnic group` (Q41710).
- Split the column `Culture_loc` into several columns using "," as the separator.
- Reconcile each `Culture_loc` column against `sovereign state (Q3624078)` or `human settlement (Q486972)` or both, depending on the values
  > Note: You may need to split the columns again using "/" or ";" as the separator.
- Split the column `Genre` into several columns using ";" as the separator.
- Reconcile each `Genre` column against `song type (Q107356781)`.
- Split the column `Instruments` into several columns using ";" as the separator.
- Reconcile the column `Instruments 1` against `voice type (Q1063547)`.
- Reconcile the other `Instruments` columns against `type of musical instrument (Q17362829)`.

## Societies

- Follow the instructions for the [Cantometrics Societies](#societies-1) file.

# Ensembles

## Ensembles

- Reconcile the cells in column `Archival_Culture_Name` to type `ethnic group` (Q41710).
- Split the column `Ensemble/Song_name` into several columns using "," as the separator.
- Reconcile each `Ensemble/Song_name` column against `song type (Q107356781)`.
  > Note: This column seems to contain a mix of instrument, performer, and song type
- Split the column `Instruments_in_Ensemble` into several columns using ";" as the separator.
- Use the GREL regex `value.trim().replace(/^\d+/, "")` to remove any numbers from the beginning of each entry.
- Reconcile each `Instruments_in_Ensemble` column against `type of musical instrument (Q17362829)`

## Societies

> Note: This file appears significantly more difficult to reconcile, as the `society` and `People` columns seem to contain a mix of ethnic groups, locations, languages, and professions.

- Follow the instructions for the [Cantometrics Societies](#societies-1) file.

# Urban Strain

## Data

- Split the column `category` into several columns using "–" (m-dash) as the separator.
- Split the column `category 1` into several columns using " " as the separator.
- Reconcile the cells in column `year` against `calendar year (Q3186692)`.
- Reconcile the cells in column `category 1 1` against `music genre (Q188451)`.
  - Manually match the cells.
    > Note: "Black" should be matched with `African-American music (Q388207)`
    > Note: "1800s" should be matched with `19th century (Q6955)`
- Reconcile the cells in column `category 1 2` against `decade (Q39911)`.
- Reconcile the cells in column `category 1 2` against `music genre (Q188451)`.
- In column `category 2`, match `early 1900s` to `20th century (Q6927)`.

## Metadata

> Note: for the first several columns in this file, there are only a few entries, which is why the reconciliation categories are more specific than for the other files in this database.
> Note: for the Performers sub-columns, it becomes difficult to manually reconcile all the entries efficiently, so automatic reconciliation may be preferable.

- Reconcile the cells in column `Region` to type `geographic region` (Q82794).
- Reconcile the cells in column `Division` to type `sovereign state` (Q3624078).
- Reconcile the cells in column `Subregion` to type `U.S. region` (Q123615496).
- Match the item `Music Scene` in column `People` to type `musical scene (Q28820001)`.
- Reconcile the cells in column `Region2` to type `geographic region` (Q82794).
- Reconcile the cells in column `Division2` to type `sovereign state` (Q3624078).
- Reconcile the cells in column `Subregion2` to type `U.S. region` (Q123615496).
- Reconcile the cells in column `Area/Kingdom` to type `U.S. state` (Q35657).
- Split the column `Cu_location` into several columns using "," as the separator.
- Reconcile the cells in column `Cu_location 1` to type `city in the United States` (Q1093829).
- Copy the column `Peoplex` and name the new column `Peoplex2`.
- Edit the "Deep South White" entry so that it says "Deep South" in column `Peoplex` and "White" in `Peoplex2`.
- Match "Deep South" in column `Peoplex` to `Deep South` (Q864007).
- Match "White" in column `Peoplex2` to `White people` (Q235155).
- Reconcile the cells in column `society` to type `ethnic group` (Q41710).
- Text transform the cells in column `Culture_location` using the GREL regex `value.replace(/\[.*\].*$/, "")`.
- Split the column `Culture_location` into several columns using "," as the separator.
- Reconcile the cells in column `Culture_location 2` to type `U.S. state` (Q35657).
- Manually match the remaining cells to their appropriate countries or Canadian provinces.
- Reconcile the cells in column `Culture_location 1` against `sovereign state (Q3624078)`, using `Culture_location 2` as Property `located in the administrative territorial entity` (P131).
- Reconcile the cells in column `Song Title` to type `musical work/composition` (Q105543609).
- Split the column `Genre` into several columns using ";" as the separator.
- Reconcile the cells in each `Genre` column to type `music genre` (Q188451).
- Split the column `Performers` into several columns using ";" as the separator.
- Split the column `Performers 1` into several columns using ":" as the separator.
- Split each `Performers` column into several columns using "," as the separator.
- If necessary, split the column again into several columns using "&" as the separator.
- Reconcile the cells in column `Performers 1 1 1` to type `musical group` (Q215380).
  - Re-reconcile the remaining cells to type `human` (Q5). The `Song_notes` column provides details on the artists.
- Reconcile the rest of the `Performers` columns to type `human` (Q5) or `type of musical instrument (Q17362829)`, as appropriate.
- Reconcile the cells in column `Recorded_by` to type `record label` (Q18127).
- Reconcile the cells in column `Year` to type `calendar year` (Q3186692).
- Reconcile the cells in column `Publisher` to type `record label` (Q18127).
- Reconcile the cells in column `Column` to type `album` (Q482994).

# Social Factors
