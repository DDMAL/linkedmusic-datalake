# Applying Histories:
> Do this before reading further.
- In the `reconciliation_history` folder, JSON files are generated in OpenRefine via `Undo/Redo > Extract... > Export`.
- These files can be applied to a specific CSV in OpenRefine by using `Undo/Redo > Apply...` and selecting the corresponding JSON.
- This process might cause errors during reconciliation. If this happens, please check below for detailed reconciliation instructions.

# Instruments

## Data

> Note: This dataset is small, so it is possible to manually reconcile much of the instrument and culture columns.
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

> Note: This dataset is small, so it is possible to manually reconcile much of the instrument and culture columns.
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

> Note: This dataset is small, so it is possible to manually reconcile much of the instrument and culture columns.
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