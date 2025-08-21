# Institute (and Source):
- Create a text facet of column `http://wikidata.org/prop/direct/P31` and filter by `https://www.wikidata.org/wiki/Q166118`.
- Create a new column `institute name` based on the column `http://www.w3.org/2000/01/rdf-schema#label` and using the GREL regex `value.replace(/,.*/,"").replace(/@none$/, "")`.
- Create a new column `institute location` based on the column `http://www.w3.org/2000/01/rdf-schema#label` and using the GREL regex `value.substring(0,-5).replace(/^[^,]*,/, "").replace(/^[^,]*,/, "").replace(/\s*\(.*?\)\s*/, "")`.
- Reconcile the cells in column `institute location` to type `human settlement` (Q486972).
- Create a new column `https://www.wikidata.org/wiki/Property:P5504` based on the column `subject` using the GREL regex `value.replace(/^.*?institutions/, "institutions")`.
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
- Match the cells using `reconcile > actions > match each cell to its best candidate`.
- Text transform the cells in `institute location` using the GREL regex `value.replace(/\s*\(.*?\)\s*/, "")`.
- Reconcile the cells in column `institute name` to type `organization` (Q43229). In the reconciliation window, choose "institute location" as the property `located in the administrative territorial entity` (P131).
- Create a `reconcile > facet > By judgment` facet and a `reconcile > facet > Best candidate's score` facet if they are not already present.
- In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
- Match the cells using `reconcile > actions > match each cell to its best candidate`.
- Reset the `Best candidate's score` facet.
- Reconcile the cells in column `institute name` against no particular type. In the reconciliation window, choose 
"https://www.wikidata.org/wiki/Property:P5504" as the property `RISM ID` (P5504).
- In the `Best candidate's score` facet, move the slider to 99-101. In the `judgment` facet, choose "none."
- Match the cells using `reconcile > actions > match each cell to its best candidate`.
- Close both facets. Go to `reconcile > add column with URLs of matched entities`, and name the new column `institute_wiki`.
- Delete the column `institute name`.
- Join the columns `http://wikidata.org/prop/direct/P2888` and `institute_wiki`.
- Delete the column `institute_wiki`.
- Go to `reconcile > add column with URLs of matched entities`, and name the new column `institutehttps://www.wikidata.org/wiki/Property:P131_wiki`.
- Delete the column `institute location`.
- Select `https://www.wikidata.org/wiki/Q31464082` in the `http://wikidata.org/prop/direct/P31` facet.
- Create a new column `RISM id` based on the column `subject` and using the GREL regex `value.replace(/^.*?sources/, "sources")`.
Join the columns `https://www.wikidata.org/wiki/Property:P5504` and `RISM id`.
Delete the column `RISM id`.
