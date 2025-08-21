# Reconciliation for Cantus Index

## Applying Histories:
> Do this before reading further.
- In `cantus_index/openrefine/history/` the JSON file `history.json` is generated in OpenRefine via `Undo/Redo > Extract... > Export`.
- This file can be applied to a specific CSV in OpenRefine by using `Undo/Redo > Apply...` and selecting the corresponding JSON.
- This process might cause errors during reconciliation. If this happens, please check below for detailed reconciliation instructions.


## Reconciliation Procedures

- Open the file `cantus_items.json` in OpenRefine, before clicking `Create project >>`, click on the first curly bracket to specify a record path.
- Go to column `_ - feast` and select `Edit column > Add column based on this column...` then name the new columnn `feast_original`, and leave the expression as "value".
- First reconcile the column `_ - feast` against `Christian holy day` (Q60075825)
- Set the judgment facet to `none`, and set the best candidate's score facet to 99-101, and go to the column `_ - feast` and go to `Reconcile > Actions > Match each cell to its best candidate`.
- Keep the judgement facet to `none`, reset the best candidate's score facet to 0-101, and go to the column `_ - feast` and go to `Reconcile > Actions > Create one new item for similar cells...` .
- Close all facets.
- Go to column `_ - genre` and select `Edit column > Add column based on this column...` then name the new columnn `genre_original`, and leave the expression as "value".
- In the column `_ - genre`, go to `Edit cells > Transform... `, and then use this GREL transformation:
```
if(value == "[?]", "Unknowable / Ambiguous",
if(value == "[G]", "Mass chant",
if(value == "[GV]", "Verse of a Mass chant",
if(value == "[M]", "Miscellaneous",
if(value == "[MO]", "Mass Ordinary",
if(value == "A", "Antiphon",
if(value == "ACC", "Ad accedentes",
if(value == "ACCV", "Ad accedentes verse",
if(value == "Ag", "Agnus dei",
if(value == "Al", "Alleluia",
if(value == "ALL", "Alleluiaticus",
if(value == "ALLV", "Alleluiaticus verse",
if(value == "AlV", "Alleluia verse",
if(value == "ANT", "Antiphon (Hispanic rite)",
if(value == "ANTV", "Antiphon verse (Hispanic rite)",
if(value == "AP", "Processional antiphon",
if(value == "AV", "Antiphon verse",
if(value == "BD", "Benedicamus domino",
if(value == "BNMT", "Benedictiones (matutinum)",
if(value == "BNMTV", "Benedictiones (matutinum) verse",
if(value == "BNOF", "Benedictiones (office)",
if(value == "BNOFV", "Benedictiones (office) verse",
if(value == "BNS", "Benedictiones (mass)",
if(value == "BNSV", "Benedictiones (mass) verse",
if(value == "Ca", "Canticle",
if(value == "CaH", "Canticle (Hispanic rite)",
if(value == "Cap", "Capitulum",
if(value == "CaV", "Canticle verse",
if(value == "CaVH", "Canticle verse (Hispanic rite)",
if(value == "CFP", "Ad confractionem panis",
if(value == "CFPV", "Ad confractionem panis verse",
if(value == "CLM", "Clamores (mass)",
if(value == "CLMO", "Clamores (office)",
if(value == "CLMOV", "Clamores (office) verse",
if(value == "CLMV", "Clamores (mass) verse",
if(value == "Cm", "Communion",
if(value == "CmR", "Versus ad repetendum for the communion",
if(value == "CmV", "Communion verse",
if(value == "Cn", "Cantio, Cantiones",
if(value == "CnV", "Cantio Verse",
if(value == "Cr", "Credo",
if(value == "D", "Dramatic element",
if(value == "Gl", "Gloria",
if(value == "Gr", "Gradual",
if(value == "GRC", "Graecus",
if(value == "GrV", "Gradual verse",
if(value == "H", "Hymn",
if(value == "HV", "Hymn verse",
if(value == "HYMN", "Hymn",
if(value == "I", "Invitatory antiphon",
if(value == "Ig", "Ingressa",
if(value == "In", "Introit",
if(value == "InR", "Versus ad repetendum for the Introit",
if(value == "InV", "Introit verse",
if(value == "IP", "Invitatory psalm",
if(value == "Ite", "Ite missa est",
if(value == "Ky", "Kyrie",
if(value == "L", "Lesson",
if(value == "LDMT", "Laudes (matutinum)",
if(value == "LDMTV", "Laudes (matutinum) verse",
if(value == "LDOF", "Laudes (office)",
if(value == "LDOFV", "Laudes (office) verse",
if(value == "LDS", "Laudes (mass)",
if(value == "LDSV", "Laudes (mass) verse",
if(value == "Li", "Litany",
if(value == "LiV", "Litany verse",
if(value == "MSR", "Miserationes",
if(value == "MSRV", "Miserationes verse",
if(value == "MT", "Matutinarium",
if(value == "MTV", "Matutinarium verse",
if(value == "Of", "Offertory",
if(value == "OfV", "Offertory verse",
if(value == "Or", "Oratio / Prayer",
if(value == "PAC", "Ad pacem",
if(value == "PACV", "Ad pacem verse",
if(value == "Pn", "Pater noster",
if(value == "Pr", "Prefatio",
if(value == "PRCS", "Preces",
if(value == "PRCSV", "Preces verse",
if(value == "PRLG", "Praelegendum",
if(value == "PRLGV", "Praelegendum verse",
if(value == "PS", "Psalm",
if(value == "Psa", "Prosa",
if(value == "Psl", "Prosula",
if(value == "PSLD", "Psallendo",
if(value == "PSLDV", "Psallendo verse",
if(value == "PSLM", "Psalmo",
if(value == "PSLMV", "Psalmo verse",
if(value == "R", "Responsory",
if(value == "RS", "Responsory (Hispanic rite)",
if(value == "RSV", "Responsory verse (Hispanic rite)",
if(value == "Sa", "Sanctus",
if(value == "SCR", "Sacrificium",
if(value == "SCRV", "Sacrificium verse",
if(value == "SNCT", "Ad sanctus",
if(value == "SNCTV", "Ad sanctus verse",
if(value == "SNO", "Sono",
if(value == "SNOV", "Sono verse",
if(value == "Sq", "Sequence",
if(value == "SqV", "Sequence verse",
if(value == "Tc", "Tract",
if(value == "TcV", "Tract verse",
if(value == "Tp", "Trope",
if(value == "TpBD", "Troped Benedicamus domino",
if(value == "TpIte", "Troped Ite missa est",
if(value == "TRN", "Threno",
if(value == "TRNV", "Threno verse",
if(value == "V", "Responsory verse",
if(value == "Va", "Varia",
if(value == "VaHW", "Varia within Holy Week",
if(value == "VAR", "Varia (Hispanic rite)",
if(value == "VARV", "Varia verse (Hispanic rite)",
if(value == "VPR", "Vespertinus",
if(value == "VPRV", "Vespertinus verse",
if(value == "VRS", "Versus (Hispanic rite...)",
if(value == "W", "Versicle",
value))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))
```
- Reconcile the `_ - genre` column against musical form (Q862597), then set the judgment facet to `none` and reconcile against christian liturgical element (Q22687823)
- Do the same for hymn (Q484692), music genre (Q188451) (after this one, set best candidats score facet to 99-101 and select `reconcile > Actions > Match each cell to its best candidate`. Reset best candidates score facet and continue), christian prayer (Q3627146), genre of piyyut (Q106238462), prayer (Q40953).
- Keep the judgement facet to `none`, reset the best candidate's score facet to 0-101, and go to the column `_ - genre` and go to `Reconcile > Actions > Create one new item for similar cells...` .
- Close all facets.

`benidacmus domino` ? what should it be reconciled to?
`benedictiones` ?


- Go to column `_ - cao_concordances`, select `Edit cells > Transform...` and use this transformation: 
```
value.replace(" ", "")
```
to get rid of empty spaces.
- Then go to `Edit cells > Split multi-valued cells...`, use this regular expression: `(?<=\w)(?=\w)`, and select regular expression.
- Go to column `_ - cao_concordances` and select `Edit column > Add column based on this column...` then name the new columnn `cao_concordances_original`, and leave the expression as "value".
- open a text facet. Make sure you are in row view.
- Facet by `C`, go to `Reconcile > Actions > Match all filtered cells to...` and reconcile to `Antiphonaire de Compiègne - BNF Lat17436` (Q26833944).
> Note: If it says a problem occured pleae try again later when you try to match all filtered cells and no results appear, you can reconcile to no particular type, and then search for a match and then type `Antiphonaire de Compiègne - BNF Lat17436 `and it should show up.
- Facet by `D`, go to `Reconcile > Actions > Match all filtered cells to...` and reconcile to (Q125136886).
- Facet by `F`, go to `Reconcile > Actions > Match all filtered cells to...` and reconcile to (Q125136090).
- The other entries in `_ - cao_concordances` are not reconcilied at this moment, we are unable currently to find their entries in wikidata if they exist. Create new items for the rest.

- Rename the columns `_ - cid`, `_ - genre`, `_ - feast`, `_ - text`, `_ - related`, `_ - similar`, `_ - troped`, `_ - source`, `_ - language`, `_ - tags`, `_ - cao`, `_ - cao_concordances`, `_ - ah_volume`, `_ - ah_item`, `_ - notes`, `_ - author`, `_ - fulltext_submitted_by`, `_ - proofread_by` to be `cid`, `genre`, `feast`, `text`, `related`, `similar`, `troped`, `source`, `language`, `tags`, `cao`, `cao_concordances`, `ah_volume`, `ah_item`, `notes`, `author`, `fulltext_submitted_by`, `proofread_by`, respectively. (i.e. remove the "_ - ")

## Exporting

- In `Export > Custom tabular... `, you can navigate to Option Code and apply the file `export.json` from `cantus_index/openrefine/export/` to automatically apply the following changes, and then download as CSV.
- If there are errors with the above step, go to `Export > Custom tabular...`, and for the columns `genre`, `feast`, and `cao_concordances`, select `Matched entity's ID` under "For reconciled cells, output". Then download as CSV.