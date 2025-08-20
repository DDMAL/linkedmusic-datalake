# Topic

- Create a text facet of column `http://wikidata.org/prop/direct/P31` and filter by `https://www.wikidata.org/wiki/Q26256810`.
- Create a new column `topic` based on the column `http://www.w3.org/2000/01/rdf-schema#label` and using the GREL regex `value.replace(/@.*/, "").replace(/\s*\([^)]*\)$/, "")`.
- Reconcile the cells in the column `topic` to type `music genre` (Q188451).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
- Match the cells using `reconcile > actions > match each cell to its best candidate`.
- Reset the `Best candidate's score` facet.
- Reconcile the cells in column `topic` to no particular type.
- In the `Best candidate's score` facet, move the slider to 99-101.
- Match the cells using `reconcile > actions > match each cell to its best candidate`.
- Manually match any items as necessary e.g., "Duets" to `duet` (Q109940).
- Close both facets. Go to `reconcile > add column with URLs of matched entities`, and name the new column `topic_wiki`.
- Join the columns `http://wikidata.org/prop/direct/P2888` and `topic_wiki`.
- Delete the column `topic_wiki`.
- Delete the column `topic`.