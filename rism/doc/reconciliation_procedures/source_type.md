# Source Type

- Create a text facet of column `http://wikidata.org/prop/direct/P31` and filter by `https://www.wikidata.org/wiki/Q21503252`.
- Create a new column `manuscript type` based on the column `http://www.w3.org/1999/02/22-rdf-syntax-ns#value` and using the GREL regex `value.replace(/@.*/, "")`.
- Reconcile the cells in the column `manuscript type` to type `physical media format` (Q82036085).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
- Match the cells using `reconcile > actions > match each cell to its best candidate`.
- Manually match "Manuscript copy" to `manuscript` (Q87167).
- Close both facets. Go to `reconcile > add column with URLs of matched entities`, and name the new column `https://www.wikidata.org/wiki/Q82036085`.
- Join the columns `http://wikidata.org/prop/direct/P2888` and `https://www.wikidata.org/wiki/Q82036085`.
- Delete the column `https://www.wikidata.org/wiki/Q82036085`.
- Delete the column `manuscript type`.