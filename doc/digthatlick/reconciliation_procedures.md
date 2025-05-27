# Applying Histories:
> Do this before reading further.
- In the `reconciliation_history` folder, JSON files are generated in OpenRefine via `Undo/Redo > Extract... > Export`.
- These files can be applied to a specific CSV in OpenRefine by using `Undo/Redo > Apply...` and selecting the corresponding JSON.
- This process might cause errors during reconciliation. If this happens, please check below for detailed reconciliation instructions.


# Reconciling dtl_metadata_v0.9.csv:
1. Go to column `Instrument_label`, and select `Edit column > Add column based on this column...`. In the Expression box enter the following GREL expression:
```
if(value == "as", "alto saxophone", 
if(value == "bs", "bari saxophone", 
if(value == "cl", "clarinet", 
if(value == "cor", "cornet", 
if(value == "fl", "flute", 
if(value == "flg", "flugelhorn", 
if(value == "ss", "soprano saxophone", 
if(value == "tb", "trombone", 
if(value == "tp", "trumpet", 
if(value == "ts", "saxophone", 
if(value == "vib", "vibraphone", 
if(value == "vln", "violin", 
if(value == "voc", "voice", value ))))))))) ) ) ) )
```
Name the new column `instrument_mapped`.
2. Go to column `solo_performer_name`, select `Edit column > Add column based on this column...` and write `"musician"` in the expression box so that every cell of this new column contains the word `musician`. Name the column `occupation`.
3. Go to column `solo_performer_name`, select `Edit column > Add column based on this column...` and write `"jazz"` in the expression box so that every cell of this new column contains the word `jazz`. Name the column `genre`.
4. 