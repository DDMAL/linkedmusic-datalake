# Applying Histories:
> **Do this before reading further.**
- In the `reconciliation_history` folder, JSON files are generated in OpenRefine via `Undo/Redo > Extract... > Export`.
- These files can be applied to a specific CSV in OpenRefine by using `Undo/Redo > Apply...` and selecting the corresponding JSON.
- **This process might cause errors during reconciliation.** If this happens, please check below for detailed reconciliation instructions.
- **Please note** that these files do not do everything:
    - `dtl_solos_history.json` is for `dtl1000_solo.csv`. It takes you to step 22 of the reconciliation procedures, but the steps in Export procedures must still be applied.
    - `dtl_tracks_history.json` is for `dtl1000_tracks.csv`. It takes you to the final step of that file, but the steps in Export procedures must still be applied.
    - `dtl_performers_history.json` is for `dtl1000_performers.csv`. Same as above.

# dtl1000_solos.csv:
1. Go to column `solo_performer_name`, select `Edit column > Add column based on this column...` and write `"musician"` in the expression box so that every cell of this new column contains the word `musician`. Name the column `occupation musician`.
2. Go to column `solo_performer_name`, select `Edit column > Add column based on this column...` and write `"jazz musician"` in the expression box so that every cell of this new column contains the word `jazz musician`. Name the column `occupation jazz musician`.
3. Go to column `solo_performer_name`, select `Edit column > Add column based on this column...` and write `"jazz"` in the expression box so that every cell of this new column contains the word `jazz`. Name the column `genre jazz`.

4. In the same column `solo_performer_name`, go to `Edit cells > Transform...` and use the expression:
```
if(value == "Flip Philips", "Flip Phillips",
if(value == "Allen", "J.D. Allen III", 
if(value == "Earl Warren", "Earle Warren", value)
))
```
This will:
- Change "Flip Philips" to "Flip Phillips" (Wikidata only has an entry for Flip Phillips).
- Change "Allen" to "J.D. Allen III" (the Allen in this column refers to J.D. Allen III).
- Change "Earl Warren" to "Earle Warren" (Earl Warren is not in Wikidata, but Earle Warren is).

5. Go to column `solo_performer_name`, reconcile against `human` (Q5) and add `instrument_label` as property `instrument` (P1303).
6. Set the judgment facet to `none` and reconcile the same column against `human` but with `genre jazz` as property `genre` (P136).
7. Set the judgment facet to `none` and reconcile the same column against `human` but with `occupation jazz musician` as property `occupation` (P106).
8. Set the judgment facet to `none` and reconcile the same column against `human` but with `occupation musician` as property `occupation` (P106).
9. Use a text filter for the column `solo_performer_name`, and filter by `George Johnson`. Create a new item for George Johnson because the jazz musician George Johnson in Wikidata is the wrong one. Without this step, reconciliation will match to the incorrect George Johnson.
10. Flag and mark the following people as new items in the column `solo_performer_name` because their reconciliation is uncertain:
    - Aleksander Gajic
    - Arville Harris
    - Bobby Bruce
    - Bobby Lewis
    - Bobby Sands
    - Chuck Carter
    - Colin Dawson
    - Dave Klein
    - Dave Young
    - David Stump
    - Don Landis
    - Eli Asher
    - Florencia Gonzalez
    - Garry Lee
    - George Johnson
    - Harold Alexander
    - Howie Smith
    - Jared Sims
    - Jerry Elliot
    - Jesse Davis
    - Jim Reider
    - Joe Ellis
    - Joe Thomas
    - Junie (E. C.) Cobb
    - Ken Shroyer
    - Kenny Faulk
    - Louis Stockwell
    - Mark McGowan
    - Mark Weinstein
    - Melvin Butler
    - Michael Bard
    - Paul Austerlitz
    - Pete Clark
    - Raymond Williams
    - Robeson
    - Sean Corby
    - Tom Morris
    - Tony Owens

    Use this GREL transformation:
```
if("Aleksander Gajic
    Arville Harris
    Bobby Bruce
    Bobby Lewis
    Bobby Sands
    Chuck Carter
    Colin Dawson
    Dave Klein
    Dave Young
    David Stump
    Don Landis
    Eli Asher
    Florencia Gonzalez
    Garry Lee
    George Johnson
    Harold Alexander
    Howie Smith
    Jared Sims
    Jerry Elliot
    Jesse Davis
    Jim Reider
    Joe Ellis
    Joe Thomas
    Junie (E. C.) Cobb
    Ken Shroyer
    Kenny Faulk
    Louis Stockwell
    Mark McGowan
    Mark Weinstein
    Melvin Butler
    Michael Bard
    Paul Austerlitz
    Pete Clark
    Raymond Williams
    Robeson
    Sean Corby
    Tom Morris
    Tony Owens".contains(value), value, "")
```
Name the new column `flagged_solo_performer`.

11. Select `none` in the judgment facet and go to `Reconcile > Actions > Create one new item for similar cells ...` to create new items for all unmatched people.
- **Note**: Perform a trim operation on all names in the column `possible_solo_performer_names` before proceeding.

12. Repeat steps 5-8 for the column `possible_solo_performer_names`.

13. Flag and mark the following people as new items in the column `possible_solo_performer_names` because their reconciliation is uncertain:
    - Elmer “Skippy” Williams
    - Milton Fletcher
    - Bob Burnett
    - Harvey Boone
    - Dave Richards
    - Ed Hudson
    - Gene Johnson
    - Henry Hicks
    - Irving Mouse
    - Jack Ferrier
    - Jay Brower
    - Joe Thomas
    - John Youngman
    - Mike Young
    - Milton Fletcher
    - Money
    - Pete Brown
    - Richard Torres
    - Robeson
    - Russell Smith
    - Tito Puente
    - William Johnson
    - Alfie Evans
    - Alfred Bell
    - Earl(e) Warren
    - Easy Mo Bee
    - Gene Jefferson
    - George Oldham
    - James King
    - John Walsh
    - Ray Reed

    Use this GREL transformation:
```
if("Elmer 'Skippy' Williams
    Milton Fletcher
    Bob Burnett
    Harvey Boone
    Dave Richards
    Ed Hudson
    Gene Johnson
    Henry Hicks
    Irving Mouse
    Jack Ferrier
    Jay Brower
    Joe Thomas
    John Youngman
    Mike Young
    Milton Fletcher
    Money
    Pete Brown
    Richard Torres
    Robeson
    Russell Smith
    Tito Puente
    William Johnson
    Alfie Evans
    Alfred Bell
    Earl(e) Warren
    Easy mo bee
    Gene Jefferson
    George Oldham
    James King
    John Walsh
    Ray Reed".contains(value), "flag", "")
```
Name the new column `flagged_possible_solo_performers`.

14. In the column `flagged_possible_solo_performers`, go to `Facet > Customized facets > Facet by blank (null or empty string)`. Select `false` in that facet. Then go to the column `possible_solo_performer_names` and go to `Reconcile > Actions > Create one new item for similar cells ...`.

15. Select `none` in the judgment facet for `possible_solo_performer_names` and create one new item for similar cells for all of them.

16. Create columns for reconciled entries and name them `possible_solo_performer_names_reconciled` and `solo_performer_name_reconciled`.

17. In the column `instrument_label`, go to `Edit cells > Transform ...` and use this GREL expression:
```
if(value=="saxophone", "tenor saxophone", 
if(value=="bari saxophone", "baritone saxophone", value))
```
This will make all the saxophones transform back into tenor saxophones and make bari sax tranform into baritone saxophone.

18. Reconcile this column against `type of musical instrument` (Q110295396).

19. Set the judgment facet to none and match clarinet to `soprano clarinet` (Q7563204).

20. Reconcile against no particular type. After this, most items should be matched. For the remaining items, set the judgment facet to none and match all items to their top candidate.

21. Delete the columns added at the beginning (`occupation musician`, `occupation jazz musician`, `genre jazz`).

22. Select the column `solo_performer_name`, go to `Reconcile > Add entity identifiers column ...`, and name the new column `solo_performer_reconciled`. Repeat this for the column `possible_solo_performer_names`, naming the new column `possible_performer_reconciled`. For each of the new columns, go to `Facet > Customized facets > Facet by blank (null or empty string)`. Set the facet to True, and then go to `Edit cells > Transform > and make the value "new"`. This will create two additional columns containing the QID of matched items or the word "new" for unmatched items.

# dtl1000_tracks.csv:
### For column leader_name
1. create a column titled `occupation bandleader` and make every cell in it: `bandleader`
2. create a column titled `occupation composer` and make every cell in it: `composer`
3. create a column titled `occupation jazz musician` and make every cell in it: `jazz musician`
4.  Reconcile the column `leader_name` against type `human` (Q5) with `occupation bandleader` as property `occupation`
5. go to not matched, repeat the above but with occupation composer as property occupation
6. same as above, but with jazz musician as property occupation
- After this, most of them should be reconciled.
- There are some band leaders who share names with other musicians in wikidata, so to make sure they are properly reconciled check:
    - Bobby Lewis should be matched to Q888607
    - Tom Dempsey should be matched to Q66709154
- There are also some that are not in wikidata, but there is someone with their name in wikidata and they should not be matched to them, check that all of these people are not matched:
    - Dennis Warren
    - Mark Weinstein
    - Mitch Marcus
    - Steven Kroon
    - Nolan Welsh
    - Garry Lee
- May have to manually match this person if OpenRefine did not match correctly:
    - Paul Austerlitz should be matched to Q131779276 

7. Select the column `leader_name`, go to `Reconcile > Add entity identifiers column ...`, and name the new column `band_leader_reconciled`. In the new column, go to `Facet > Customized facets > Facet by blank (null or empty string)`. Set the facet to True, and then go to `Edit cells > Transform > and make the value "new"`. This will create an additional column that contains the QID of the items that were matched in each column, and contain the word "new" for any items that were not matched. We will use this for exporting as well as to make reconciling the performers.csv file more efficient.

### For column band_name
1. copy reconciled values from column leader name by going to column `leader_name`, going to `Reconcile > Copy reconciliation data...`, and selecting band_name as the column to copy to. (make sure that the copy options on the right are all selected)
2. Open a judgment facet and facet by unreconciled. Then reconcile column `band_names` against `musical group` (Q215380).
3. Do step 2 again but with `leader_name` as property `has_parts` P(527).
4. Then reconcile against `album` (Q482994) since some of the band names are actually album names
4. Then reconcile against `human` (Q5) with `jazz musician` as property `occupation` (P106), since of the band names are just musicians.
3. The rest are not in wikidata, mark to create new item


### For column medium_title
1. nothing to reconcile, they are too specific and either not in wikidata or not helpful metadata. (Maybe later if we find a good way to reconcile we can)

### For column disk_title
1. make new column based on this column, using this GREL expression:
```
if (value.startsWith("The Encyclopedia of Jazz"), "The Encyclopedia of Jazz", value) (makes copies)
```
2. Reconcile the column against `creative work` (Q17537576).
3. Match `encyclopedia of jazz` to its top match (Q42189397)
4. Set the judgment facet to none, and reconcile against `album` (QQ482994).
5. Do the same as 3 but against album with `leader_name` as property `performer`.
6. Do the same as 3, against album, but with `band_name` as property `performer`.
7. set best candidates score facet to 100-101, match to top candidate
8. Create new column for similar entries for all the unreconciled items


### For column track_title
1. Reconcile against musical work with `leader_name` as performer.
2. Match `Merry-Go-Round` to (Q98687908).
3. Mark the rest as new items.


### For column area:
1. For the cell that looks like this: `New York, Mumbai & Chennai, India, Saylorsburg, PA, Encino, CA, & Chicago, IL, November 2006-` use this Grel transformation: 
```
value.replace(/,(?= [A-Z]{2})/, ".").replace("India,", "").replace(", November 2006-", "").replace("& Chi", "Chi")
```
Then split multi-valued cells by separator : `,|&` (make sure to check the regular expression button)
This allows us to reconcile each place individually.
2.  Use 
```
value.replace(/^Live/, "").replace(/["']/,"")
```
 to remove the word live and the quotation marks from some of the entries

then do a value.trim() on all of them

> Note: when reconciling make sure you have rows selected instead of records.

3. then reconcile the column `area` against `big city` (Q1549591), to get most of the items which are big cities. first, to get the small specific venues.
4. Set the candidates score facet to 99-101 and go to the column `area` and go to `Reconcile > Actions > Match each cell to its best candidate`.
5. Set the judgment facet to none and reconcile the same column against `U.S. state` (Q35657) to get all the abbreviated states.
6. Set the candidates score facet to 99-101 and go to the column `area` and go to `Reconcile > Actions > Match each cell to its best candidate`.
7. Keep the judgment facet as none, but reset the candidate's score facet to be everything and reconcile the same column against `country` (Q6256) to match the countries.
8. Set the candidates score facet to 99-101 and go to the column `area` and go to `Reconcile > Actions > Match each cell to its best candidate`.
9. Keep the judgment facet as none, but reset the candidate's score facet to be everything and reconcile the same column against `province or territory of Canada` (Q2879) to get some of the abbreviated provinces.
10. Set the candidates score facet to 99-101 and go to the column `area` and go to `Reconcile > Actions > Match each cell to its best candidate`.
11. Keep the judgment facet as none, but reset the candidate's score facet to be everything and reconcile the same column against `city` (Q515), to match the smaller cities.
12. Keep the judgment facet as none, but reset the candidate's score facet to be everything and reconcile the same column against `no particular type` to match some of the obscure smaller venues.
13. Keep the judgment facet as none, but reset the candidate's score facet to be everything, and manually reconcile these places:
```
    Camden (Q138367)
    Woodstock (Q608293)
    Concert Philharmonic Hall should match to Berliner Philharmonie (Q32653910)
    stroudsberg should be Stroudsburg (Q1185729)
    Clayton (Q1099274)
    the Village Vanguard (and Village Vanguard) should be Village Vanguard (Q670623)
    Cellar door should be The Cellar Door (Q7721848)
    Wilmington (Q659400)
    White Plains (Q462177)
    Palatine (Q998726)
    Brooklyn (Q18419)
    Union City (Q588834)
    Englewood (Q986210)
    Hackensack (Q138458)
    West Greenwich (Q1644523)
    Musikhalle should be Kaeiszhalle (Q881121)
    Dobbs Ferry (Q1233173)
    Birdland (Q256347)
    Hilversum (Q9934)
    River Edge (Q928724)
    Smoke (Q15278253)
    University of Illinois (Q457281)
    University of Washington (Q219563)
    Meany Hall (Q6804124)
    Montreux Jazz Festival (Q669118)
    Western Australia (Q3206)
    Sydney Opera House (Q45178)
    Shokan (Q2771880)
    Ronnie Scotts club (Q1296978)
    Bearsville (Q4876785)
    Knitting factory (Q838068)
    Carnegie Hall (Q200959)
    Westwood (Q2304357)
    Blue note (Q885822)
    Judson Hall is (probably) Judson Memorial Church (Q3111397)
    Northbrook (Q570986)
```
> Note: NY should be matched to the state New York, and New York should be matched to New York City, since all the states are abbreviated as two letters, but there was no way to automatically reconcile that would match NY to the state and New York to the city, so manually have to do one of them.

these ones are unsure: Vignola unsure actually
not sure what to do with broadcast
Famous Ballroom
Afternoon set
evening set
North Park Hotel
prob c?
S/S Norway?

16. Mark the rest as new item


# dtl1000_performers.csv

1. Go to column `performer_names`, select `Edit column > Add column based on this column...` and write `"musician"` in the expression box so that every cell of this new column contains the word `musician`. Name the column `occupation musician`.
2. Go to column `performer_names`, select `Edit column > Add column based on this column...` and write `"jazz musician"` in the expression box so that every cell of this new column contains the word `jazz musician`. Name the column `occupation jazz musician`.
3. Go to column `performer_names`, select `Edit column > Add column based on this column...` and write `"jazz"` in the expression box so that every cell of this new column contains the word `jazz`. Name the column `genre jazz`.
> Note: Make sure you also have the projects `dtl1000_solos.csv` and `dtl1000_tracks.csv` open in OpenRefine for the following steps

4. Go to the column `performer_names`, go to `Edit column > Add column based on this column ...` and use the following Grel expression:
```
if(
  cell.cross("dtl1000 tracks csv", "leader_name").length() > 0,
  cell.cross("dtl1000 tracks csv", "leader_name")[0].cells[band_leader_reconciled].value,
  if(
    cell.cross("dtl1000 solos csv", "possible_solo_performer_names").length() > 0,
    cell.cross("dtl1000 solos csv", "possible_solo_performer_names")[0].cells[“possible_performer_reconciled”].value,
    if(
      cell.cross("dtl1000 solos csv", "solo_performer_name_original").length() > 0,
      cell.cross("dtl1000 solos csv", "solo_performer_name_original")[0].cells[“solo_performer_reconciled”].value,
      “”
    )
  )
)
```
Name the new column `already_reconciled`.
This will take the values from the other projects where they have already been reconciled, since the performers includes the soloists, sometimes the bandleader, so we don't have to reconciled things we have already reconciled. It will place the Qid into the rows of the already reconciled items, and put "new" into rows where the performer was marked new in the other files.

5. Then in the new column go to `Facet > Customized facets > Facet by blank (null or empty string)`. Set the facet to True, so that we will now reconcile only the performers that we haven't already reconciled.

6. Reconcile the column `performer_names` against type `human` (Q5), with `occupation jazz musician` as property `occupation` (P106)
7. Set the judgment facet to none and Reconcile the column `performer_names` against type `human` (Q5), with `occupation musician` as property `occupation` (P106)
8. Set the judgment facet to none and Reconcile the column `performer_names` against type `human` (Q5), with `genre jazz` as property `genre` (P136)
9. Go to none, and in candidate's score facet by 100-101, match item to best match.
10. Reset candidates score to everything, make new item for similar cells for the rest.
11. In column `performer_names` go to `Reconcile > Add entity identifiers column... `, name it `reconciled_performer_names`.
12. Go to column `reconciled_performer_names`,then `Edit column > Join columns...` and join it with `already_reconciled`, you don't have to make a new column.
13. Use a text filter on the column `reconciled_performer_names`, filter by the word "new", and make those all blank using a transform with Grel expression `""`.
14. Then in the same column, go to `Facet > customized facet > facet by blank`, select `true` in the facet, and use this transform on cells: cells["performer_names"].value.
15. Select column `performer_names`, go to `Edit column > Add column based on this column`, leave the Grel expression as value, name the new column `performer_names_original`, and then delete the old column `performer_names` and rename `reconciled_performer_names` to `performer_names`.
16. Remove the columns `already_reconciled`,  `occupation musician`, `occupation jazz musician`, `genre jazz`.


# Export procedures

## For dtl1000_solos.csv:

1. Delete the columns `possible_performer_reconciled`, `flagged_possible_solo_performers`, `solo_performer_reconciled`, `flagged_solo_performer`.
2. Select column `possible_solo_performer_names`, go to `Edit column > Add column based on this column`, leave the Grel expression as value, name the new column `possible_solo_performer_names_original`.
3. Select column `solo_performer_name`, go to `Edit column > Add column based on this column`, leave the Grel expression as value, name the new column `solo_performer_name_original`.
4. Select column `instrument_label`, go to `Edit column > Add column based on this column`, leave the Grel expression as value, name the new column `instrument_label_original`.
5. Go to `export > custom tabular `, and then for the columns `possible_solo_performer_names`, `solo_performer_name`, and `instrument_label`, on the right side under `For reconciled cells, output`, select `Matched entity's ID`.

## For dtl1000_tracks.csv:

1. Delete the columns `band_leader_reconciled`, `occupation bandleader`, `occupation composer`, `occupation jazz musician`.
2. Select column `band_name`, go to `Edit column > Add column based on this column`, leave the Grel expression as value, name the new column `band_name_original`.
3. Select column `leader_name`, go to `Edit column > Add column based on this column`, leave the Grel expression as value, name the new column `leader_name_original`.
4. Rename `disk_title` to `disk_title_original`, and then rename `disk_title_copy` to `disk_title`.
5. Select column `track_title`, go to `Edit column > Add column based on this column`, leave the Grel expression as value, name the new column`track_title_original`
6. Select column `area`, go to `Edit column > Add column based on this column`, leave the Grel expression as value, name the new column`area_original`.
7. Go to `export > custom tabular`, and then for the columns `band_name`, `leader_name`, `disk_title`, `track_title`, and `area`, on the right side under `For reconciled cells output`, select `Matched entity's ID`.

## For dtl1000_performers.csv:

1. Export as csv.
