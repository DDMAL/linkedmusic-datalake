# Time signatures

1. Go to column `https://rism.online/api/v1#hasPAETimesig` and go to `Edit column > Add column based on this column`, leave the GREL expression as `value` and name the new column `time signatures`.
2. In `time signatures` go to `Reconcile > Start reconciling` and reconcile against type `time signature` (Q155234). 
3. Match the cells containing "c" to `common time` (Q27955141) and match the cells containing "c/" to `alla breve` (Q249261) (this can be done by going to search for match and typine in commontime and alla breve respectively).
4. Ignore the unmatched cells by selecting none in the judgment facet and going to `Reconcile > Actions > Create one new item for similar cells...`.
5. Create a new column of the wikidata urls by going to `Reconcile > Add column with URLs of matched entities..`, and name it `http://www.wikidata.org/prop/direct/P3440`
6. Remove column `time signatures`.