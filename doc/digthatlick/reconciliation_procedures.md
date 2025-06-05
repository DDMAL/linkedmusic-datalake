
# dtl1000_solos.csv:
1. Go to column `solo_performer_name`, select `Edit column > Add column based on this column...` and write `"musician"` in the expression box so that every cell of this new column contains the word `musician`. Name the column `occupation musician`.
2. Go to column `solo_performer_name`, select `Edit column > Add column based on this column...` and write `"jazz musician"` in the expression box so that every cell of this new column contains the word `jazz musician`. Name the column `occupation jazz musician`.
3. Go to column `solo_performer_name`, select `Edit column > Add column based on this column...` and write `"jazz"` in the expression box so that every cell of this new column contains the word `jazz`. Name the column `genre jazz`.

4.  In the same column `solo_performer_name`, go to `Edit cells > Transform...` and use the expression:
```
if(value == "Flip Philips", "Flip Phillips",
if(value == "Allen", "J.D. Allen III", 
if(value == "Earl Warren", "Earle Warren", value)
))
```
To change Flip Philips to Flip Phillips, since although they are techinically the same person, wikidata only has an entry for Flip Phillips, and to change Allen to J.D. Allen III, since the Allen in this column is referring to J.D. Allen III. Also change Earl Warren to Earle Warren (since Earl Warren is not in wikidata, but Earle Warren is). 5 cells should be changed after this transformation.

5. Go to column `solo_performer_name`, reconcile against `human` (Q5) and add `instrument_label` as property `instrument` (P1303).
6. Set the judgment facet to `none` and reconcile the same column against `human` but with `genre jazz` as property `genre` (P136)
7. Set the judgment facet to `none` and reconcile the same column against `human` but with `occupation jazz musician` as property `occupation` (P106)
8. Set the judgment facet to `none` and reconcile the same column against `human` but with `occupation musician` as property `occupation` (P106)
9. Make a text filter for the column `solo_performer_name`, and put `George Johnson` in the filter. Make new item for George Johnson. Because in wikidata there is a jazz musician George Johnson but he is the wrong one, and if we reconcile without doing this, it will match to the wrong George Johnson.
10. In the column `solo_performer_name`, the following people should be flagged and marked as new item, as we are unsure about their reconciliation:

    Aleksander Gajic
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
    Tony Owens

11. Select `none` in the judgment facet and go to `Reconcile > Actions > Create one new item for similar cells ... ` to create new items for all the unmatched people.
- should do a trim on all these guys in the column possible solo peformer names first
12. Repeat steps 5-8 for the column `possible_solo_performer_names`
13. trouble reconciling these people, flag them and mark as new item:
    Elmer “skippy” williams
    Milton Fletcher
    Bob Burnett
    Harvey Boone
    Dave Richards
    Ed hudson
    Gene Johnson
    Henry hicks
    Irving mouse
    Jack ferrier
    Jay brower
    Joe Thomas
    John youngman
    Mike young
    Milton fletcher
    Money
    Pete brown
    Richard torres
    Robeson
    Russell smith
    Tito puente
    William johnson
    Alfie evans
    Alfred bell
    Earl(e) warren
    Easy mo bee
    Gene jefferson
    George oldham
    James king
    John walsh
    Ray reed
14. To do this, go to `Add new column based on this column`, use this GREL expression:
```
if("Elmer  'Skippy' Williams
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
    Ray Reed".contains(value),"flag","")
```
Name the new column `flagged`.
Then in that column go to `Facet > Customized facets > Facet by blank (null or empty string)`. Select `false` in that facet.
Then go to the column `possible_solo_performer_names` and go to `Reconcile > Actions > Create one new item for similar cells ...`.
Then you can unselect the facet

15. Now select `none` in the judgment facet for `possible_solo_performer_names` and create one new item for similar cells for all of them.

16. make columns of reconciled entries, name it `possible_solo_performer_names_reconciled`. do the same for solo_performer_name

17. In the column `instrument_label`, go to `Edit cells > Transform ...` and use this Grel expression:
```
if(value=="saxophone", "tenor saxophone", value)
```
to make all the saxophones back into tenor saxophones. (also maybe need to make bari sax into baritone saxophone)

18. Reconcile this column against no particular type

^ find a way to reconcile the instruments well

and then delete extra columns



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
- Then there are some people that have a match in wikidata, but in wikidata it is not very clear it is them, but after research I have found it is correct but openrefine is not super confident, so may have to manually match these people:
    - Paul Austerlitz should be matched to Q131779276 


### For column band_name
1. copy reconciled values from column leader name by going to column `leader_name`, going to `Reconcile > Copy reconciliation data...`, and selecting band_name as the column to copy to. (make sure that the copy options on the right are all selected)
2. Then reconcile column `band_names` against `musical group` (Q215380).
3. Do step 2 again but with `leader_name` as property `has_parts` P(527).
4. Then reconcile against `album` (Q482994) since some of the band names are actually album names
4. Then reconcile against `human` (Q5) with `jazz musician` as property `occupation` (P106), since of the band names are just musicians.
3. The rest are not in wikidata, mark to create new item


delete the extra columns

### For column medium_title
1. nothing to reconcile, they too specific its not in wikidata

### For column disk_title
1. idk try album first with band leader as performer
without its matched 105, 125
3. make new column based on this column, but do this transformation:
```
if (value.startsWith("The Encyclopedia of Jazz"), "The Encyclopedia of Jazz", value) (makes copies)
```
2. also do creative work to get that the encyclopedia of jazz 
    and then do album, and album with leader name as performer 
    and album with band name as performer

for some reason Feelin's has two entries, just match to top one
set best candidates score facet to 100-101, match to top candidate
i think the rest are not in wikidata, do new for them all


### For column track_title
1. i think add column jazz standard or something to help (think example merry-go-round)
2. reconcile against musical work
Merry-Go-Round is the one by charlie parker (probably)


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


big city first
go to 100, do match to top candidate
then do us state
then country
go to 100, match to best candidate
then canadian province

then no particular type?

human settlement?
city?

richmond virginia
schaumberg create new item
alameda california
camden new jersey
wilmington north carolina
concert philharmonic hall in berlin germany is berliner philarmonie
Im assuming New York is the city  as the states are abbreviated in two letters, like NY




figure out something to have some new yorks go to new york city, but have NY do new york state
try this:
```
if(value==null,"prob_not_city", "prob_city")
```
this in colmn `session date`, what this does is separate the cities from the states and countries in the area column, since we split multivalued cells
then facet by prob_city, reconcile the area column against `big city` (Q1549591)
move candidate facet to 100, and judgment to none, match to best candidate



for faet by prob_not_city(i.e. probable states and stuff)
u.s. state (Q35657)
then country (Q6256), move candidate facet to 100, reconcile > match each cell to its best candidate







3. then reconcile the column `area` against `no particular type` first, to get the small specific venues.
4. Set the judgment facet to none and reconcile the same column against `human settlement` (Q486972) to get generally most of them
5. Set the judgment facet to none and reconcile the same column against `state` (Q7275) some of the entries are abbreviated states, this will match them well
6. Set the judgment facet to none and reconcile the same column against `country` (Q6256) there are some countries, this maps them well
7. Set the judgment facet to none and reconcile the same column against `big city` (Q1549591) (maybe dont need this one)
8. Set the judgment facet to none and reconcile the same column against `city` (Q515), map the remaining to cities, as thats all that should be left
9. the rest become create new item

province for canada
city first? to get nyc over new york

camden new jersey
berliner philharmonie
wilmington north carolina
woodstock new york
maybe just do these guys automatically


TODO: 

# dtl1000_performers.csv
making it so u use all the other things already reconciled, and then u dont have to reconcile as much
(so basically do tracks and solos before doing performers, and have the projects in openrefine)

cell.cross("dtl1000 solos csv testing", "possible_solo_performer_names")[0].cells["reconciled"].value

also cross with the flagged columns values to get all the ones we will mark new, and then the rest try and reconcile them