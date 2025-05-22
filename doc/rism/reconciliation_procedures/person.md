# Person 

1. Select column `http://www.w3.org/1999/02/22-rdf-syntax-ns#type` and go to `Facet > Text facet `, then in the text facet select the one containing `#Person`, to isolate just the cells containing `Person`. This can also be done by creating a text filter for this column and filtering for `Person`.
2. Now select column `http://www.w3.org/2000/01/rdf-schema#label`, go to `Edit column > Add column based on this column`, name the new column `p` and use the jython/python expression `return value[:-5]` to create a new column with the @none removed from the cells.
3. Select the new column `p` and go to `Edit column > Split into several columns`, use `(` as the separator, and split into 2 columns at most. You should now have a column `p 1` with just names, and a column `p 2` with dates.
4. In column `p 2` go to `Edit column > Split into several columns`, use `-` as the separator, and split into 2 columns at most. Now instead of column `p 2` you should have two columns, `p 2 1` and `p 2 2`
5. In column `p 2 2` go to `Edit cells > Transform ...` and use the python/jython expression: `return value[:4]`.
6. Now in column `p 1` go to `Reconcile > start reconciling...` and reconcile against `human` (Q5). In the reconciliation window, choose "p 2 1" as the property `date of birth` (P569) and "p 2 2" as the property `date of death` (P570). If there is an error, repeat this step.

# Person 2

1. Remove the columns `p 2 1` and `p 2 2`.
2. From column `p 1` create a column of matched wikidata urls by going to colun `p 1` and going to `Reconcile > Add column with URLs of matched entities`. Name the new column `pr`.
3. Remove column `p 1`, and rename column `pr` to `http://wikidata.org/prop/direct/P2888`.