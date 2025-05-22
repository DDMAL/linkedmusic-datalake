# Applying Histories:
> Do this before reading further.
- In the `reconciliation_history` folder, JSON files are generated in OpenRefine via `Undo/Redo > Extract... > Export`.
- These files can be applied to a specific CSV in OpenRefine by using `Undo/Redo > Apply...` and selecting the corresponding JSON.
- This process might cause errors during reconciliation. If this happens, please check below for detailed reconciliation instructions.

# Instruments
> Note: This dataset is small, so it is possible to manually reconcile many of the columns after a first automatic pass.

## Data

- Reconcile the cells in column `Instrument_Name` to type `family of musical instruments` (Q1254773) using `Sachs_Number` as property `Hornbostel-Sachs classification` (P1762).
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
- Reconcile the cells in column `society` to type `ethnic group` (Q41710).
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
- Reconcile the cells in column `Language` to type `modern language` (Q1288568).
    - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
    - In the `Best candidate's score` facet, move the slider to 62-101. In the `judgment` facet, choose "none."
    - Match the cells using `reconcile > actions > match each cell to its best candidate`.
    - Remove both facets.
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
- Reconcile the cells in column `Instrument_Name` to type `family of musical instruments` (Q1254773) using `Sachs_Number` as property `Hornbostel-Sachs classification` (P1762) and `Alt_Instrument_Names` as property `alternative name` (P4970).
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
- Reconcile the cells in column `Division` to type `geographic region` (Q82794).
    - Manually match "Central Africa" to `Central Africa` (Q27433).
    - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
    - In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
    - Match the cells using `reconcile > actions > match each cell to its best candidate`.
    - Remove both facets.
- Reconcile the cells in column `society` to type `ethnic group` (Q41710).
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
- Reconcile the cells in column `Language` to type `modern language` (Q1288568).
    - Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
    - In the `Best candidate's score` facet, move the slider to 62-101. In the `judgment` facet, choose "none."
    - Match the cells using `reconcile > actions > match each cell to its best candidate`.
    - Reset the `Best candidate's score` facet.
    - Rereconcile the cells in column `Language` to type `dialect` (Q33384).
    - Remove both facets.
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
- Follow the instructions for the Cantometrics Societies file.