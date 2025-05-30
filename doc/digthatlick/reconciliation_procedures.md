
# dtl1000_solos.csv:
1. Go to column `solo_performer_name`, select `Edit column > Add column based on this column...` and write `"musician"` in the expression box so that every cell of this new column contains the word `musician`. Name the column `occupation`.
2. Go to column `solo_performer_name`, select `Edit column > Add column based on this column...` and write `"jazz"` in the expression box so that every cell of this new column contains the word `jazz`. Name the column `genre`.
3. Make a text filter for the column `solo_performer_name`, and put `George Johnson` in the filter. Make new item for George Johnson. Because in wikidata there is a jazz musician George Johnson but he is the wrong one, and if we reconcile without doing this, it will match to the wrong George Johnson.
5. 
In the same column `solo_performer_name`, go to `Edit cells > Transform...` and use the expression:
```
if(value == "Flip Philips", "Flip Phillips",
if(value == "Allen", "J.D. Allen III", value
))
```
To change Flip Philips to Flip Phillips, since although they are techinically the same person, wikidata only has an entry for Flip Phillips, and to change Allen to J.D. Allen III, since the Allen in this column is referring to J.D. Allen III. 4 cells should be changed after this transformation.
6. Go to column `solo_performer_name`, reconcile against `human` (Q5) and add `instrument_label` as property `instrument` (P1303).
7. Set the judgment facet to `none`, set the candidates score to be from 0-99 and reconcile the same column against `human` but with `genre` as property `genre` (P136)
8. Set the judgment facet to `none`, set the candidates score to be from 0-99 and reconcile the same column against `human` but with `occupation` as property `occupation` (P106)
9. In the text filter for the column `solo_performer_name` search for the following people:
    - Milton Nascimento
    - Lionel Hampton
    - Milt Jackson
    - Stephane Grappelli
    - John Hines
    - Jeremy Udden
    - Michael Franks
    - Joe Thomas
    - Howie Smith
    If they are not already matched, then match them to their top candidate
10. Select `none` in the judgment facet and go to `Reconcile > Actions > Create one new item for similar cells ... ` to create new items for all the unmatched people.
TODO: check through all the people that were matched, make sure they are all matched correctly (don't want another george johnson situation)


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
- Then there are some people that have a match in wikidata, but in wikidata it is not very clear it is them, but after research I have found it is correct but openrefine is not super confident, so may have to manualy match these people:
    - Paul Austerlitz should be matched to Q131779276 


### For column area:
1. For the cell that looks like this: `New York, Mumbai & Chennai, India, Saylorsburg, PA, Encino, CA, & Chicago, IL, November 2006-` use this Grel transformation: 
```
value.replace(/,(?= [A-Z]{2})/, ".").replace("India,", "").replace(", November 2006-", "").replace("& Chi", "Chi")
```
Then split multi-valued cells by separator : `,|&` (make sure to check the regular expression button)
This allows us to reconcile each place individually.
TODO: the rest of this column


TODO: dtl1000_performers.csv