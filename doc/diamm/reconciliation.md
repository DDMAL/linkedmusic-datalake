# DIAMM Database Reconciliation Details

This file describes the reconciliation steps taken in OpenRefine for each data type. All these steps are also reflected in the history files located in the `doc/diamm/reconciliation_files` folder

During every reconciliation step, if OpenRefine gives an error, select the entries that gave error messages and re-run the same reconciliation. This seems to happen when we run too many reconciliations in parallel, and/or when the reconciliation API server is overwhelmed.

## Archives

1. Create a column `country_@id` as a copy of `country`
2. Reconcile `country_@id` against Q6256
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Reset the score window and fix the remaining countries
5. Create a column `city_@id` as a copy of `city`
6. Reconcile `city_@id` against Q515
7. Set the best candidate score window to 99-101 and match each entry to its best candidate
8. Reset the score window and create new entries for everything else
9. Create a column `name_@id` as a copy of `name`
10. Reconcile `name_@id` against Q43229 using the `siglum` column as P11550 and the `rism_id` column as P5504
11. Some names might give error messages, in that case select only those that caused errors and re-run the reconciliation
12. Set the best candidate score window to 99-101 and match each entry to its best candidate
13. Reset the score window and create new entries for everything else

## Compositions

1. On the `genres` column, use `edit cells -> split multi-valued cells` and split using the delimiter `;`
2. Create a column `genres_@id` as a copy of `genres`
3. Reconcile `genres_@id` against Q188451
4. Set the best candidate score window to 99-101 and match each entry to its best candidate
5. Reset the score window and create new entries for everything else

## Organizations

1. Create a column `country_@id` as a copy of `country`
2. Reconcile `country_@id` against Q6256
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Reset the score window and fix the remaining countries
5. Create a column `city_@id` as a copy of `city`
6. Reconcile `city_@id` against Q515
7. Set the best candidate score window to 99-101 and match each entry to its best candidate
8. Reset the score window and create new entries for everything else
9. Create a column `name_@id` as a copy of `name` using the GREL formula `value.trim().toLowercase().replace("^the ", "").replace(/\\s/, " ").replace(/[^A-Za-z0-9 ]/, "")`
10. Reconcile `name_@id` against Q16970 using the `country_@id` column as P17
11. Set the best candidate score window to 99-101 and match each entry to its best candidate
12. Reset the score window and select only the remaining unmatched entries
13. Reconcile `name_@id` against Q44613 using the `country_@id` column as P17
14. Set the best candidate score window to 99-101 and match each entry to its best candidate
15. Reset the score window and select only the remaining unmatched entries
16. Reconcile `name_@id` against Q24398318 using the `country_@id` column as P17
17. Set the best candidate score window to 99-101 and match each entry to its best candidate
18. Reset the score window and select only the remaining unmatched entries
19. Reconcile `name_@id` against Q43229 using the `country_@id` column as P17
20. Set the best candidate score window to 99-101 and match each entry to its best candidate
21. Reset the score window and select only the remaining unmatched entries
22. Reconcile `name_@id` against no type using the `country_@id` column as P17
23. Set the best candidate score window to 91-101 and match each entry to its best candidate
24. Reset the score window and select only the remaining unmatched entries
25. Create new entries for all of them
26. On the `organization_type` column, use `edit cells -> split multi-valued cells` and split using the delimiter `", "`
27. On the `organization_type` column, run the transformation using the Python formula `import re; return re.sub(r"^(?:and|or) ", "", value, flags=re.I)`
28. Create a column `organization_type_@id` as a copy of `organization_type` using the GREL formula `value.toLowercase()`
29. Reconcile `organization_type_@id` against Q811102
30. Set the best candidate score window to 99-101 and match each entry to its best candidate
31. Reset the score window and manually fix the remaining entries, creating new entries where necessary

## People

1. Create a column `earliest_year_@id` as a copy of `earliest_year`
2. Reconcile `earliest_year_@id` against Q577
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Create a column `latest_year_@id` as a copy of `latest_year`
5. Reconcile `latest_year_@id` against Q577
6. Set the best candidate score window to 99-101 and match each entry to its best candidate
7. Create a column `full_name_@id` as a copy of `full_name` using the GEL formula `value.replace(".", "").replace(/(.*?), (.*)/, "$2 $1")`
8. Reconcile `full_name_@id` against Q5 using the `rism_id` column as P5504
9. Set the best candidate score window to 99-101 and match each entry to its best candidate
10. Reset the score window and select only the remaining unmatched entries
11. Reconcile `full_name_@id` against Q5 using the `viaf_id` column as P214
12. Set the best candidate score window to 99-101 and match each entry to its best candidate
13. Reset the score window and create new entries for everything else

## Sets

1. Create a column `sets_@id` as a copy of `sets`
2. Reconcile `sets_@id` against no type
3. Set the best candidate score window to 90-101 and match each entry to its best candidate
4. Reset the score window and create new entries for everything else

## Sources

1. Create a column `source_type_@id` as a copy of `source_type`
2. Reconcile `source_type_@id` against no type
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Reset the score window and create new entries for everything else
