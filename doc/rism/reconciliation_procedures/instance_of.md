
# Instance of

1. Select column `http://www.w3.org/1999/02/22-rdf-syntax-ns#type` and go to `Edit column > Add column based on this column`. From there leave the GREL expression as `value`, and name the New column t.
2. In the same column, go to `Edit cells > Transform...` and use the GREl expression `value.split('#')[-1]` to transform the text in the cells of column t.
3. Since some cells in column t don't have `#` in them, select the column, go to `Facet > Text facet` and select the text `http://purl.org/dc/terms/type`, to get only the cells with this text. Then go to `Edit cells > Transform...` and use the jython/python code: `return value[-4:]` to get just `type` in the cell.
4. Then in column t, go to `Reconcile > start reconciling...` and reconcile against no particular type.
5. In column t Match the cells containing "Instiution" to item `archive` (Q166118), match the cells containing "Exemplar" to the item `exemplar` (Q166118), match the cells containing "Source" to the item `source` (Q31464082), match the cells containing "Person" to item `human` (Q5), match the cells containing "Incipit" to the item `incipit` (Q1161138), match the cells containing "type" to the item `instance of` (Q21503252), match the cells containing "Subject" to the item `topic` (Q26256810), and for the cells containig "ExemplarsSection" create mew items.
6. Create new column titled tw, by selecting column t and going to `Reconcile > Add column with URLs of matched entities`, then remove column t.
7. Rename column tw to `htp://wikidata.org/prop/direct/P31`
