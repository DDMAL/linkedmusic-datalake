# DIAMM Database Reconciliation Details

This file describes the reconciliation steps taken in OpenRefine for each data type. All these steps are also reflected in the history files located in the `diamm/doc/reconciliation_files` folder

During every reconciliation step, if OpenRefine gives an error, select the entries that gave error messages and re-run the same reconciliation. This seems to happen when we run too many reconciliations in parallel, and/or when the reconciliation API server is overwhelmed.

## Archives

1. Create a column `name_@id` as a copy of `name`
2. Reconcile `name_@id` against Q43229 using the `siglum` column as P11550 and the `rism_id` column as P5504
3. Some names might give error messages, in that case select only those that caused errors and re-run the reconciliation
4. Set the best candidate score window to 99-101 and match each entry to its best candidate
5. Reset the score window and create new entries for everything else

## Cities

1. Create a column `country_@id` as a copy of `country`
2. Reconcile `country_@id` against Q6256
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Reset the score window and fix the remaining countries
5. Create a column `name_@id` as a copy of `name` using the GREL formula `value.replace(/(.*?)(?: \(.*\))?/, "$1")`
6. Reconcile `name_@id` against Q515 using the `country_@id` column as P17
7. Set the best candidate score window to 99-101 and match each entry to its best candidate
8. Reset the score window and select only the remaining unmatched entries
9. Reconcile `name_@id` against Q3957 using the `country_@id` column as P17
10. Set the best candidate score window to 99-101 and match each entry to its best candidate
11. Reset the score window and select only the remaining unmatched entries
12. Reconcile `name_@id` against Q15284 using the `country_@id` column as P17
13. Set the best candidate score window to 99-101 and match each entry to its best candidate
14. Reset the score window and fix the remaining cities, marking them as new items if needed

## Compositions

1. On the `genres` column, use `edit cells -> split multi-valued cells` and split using the delimiter `;`
2. Create a column `genres_@id` as a copy of `genres`
3. Reconcile `genres_@id` against Q188451
4. Set the best candidate score window to 99-101 and match each entry to its best candidate
5. Reset the score window and create new entries for everything else

## Countries

1. Create a column `name_@id` as a copy of `name`
2. Reconcile `name_@id` against Q6256
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Reset the score window and fix the remaining countries, if any

## Organizations

1. Create a column `country_@id` as a copy of `country`
2. Reconcile `country_@id` against Q6256
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Reset the score window and fix the remaining countries
5. Create a column `name_@id` as a copy of `name` using the GREL formula `value.trim().toLowercase().replace("^the ", "").replace(/\\s/, " ").replace(/[^A-Za-z0-9 ]/, "")`
6. Reconcile `name_@id` against Q16970 using the `country_@id` column as P17
7. Set the best candidate score window to 99-101 and match each entry to its best candidate
8. Reset the score window and select only the remaining unmatched entries
9. Reconcile `name_@id` against Q44613 using the `country_@id` column as P17
10. Set the best candidate score window to 99-101 and match each entry to its best candidate
11. Reset the score window and select only the remaining unmatched entries
12. Reconcile `name_@id` against Q24398318 using the `country_@id` column as P17
13. Set the best candidate score window to 99-101 and match each entry to its best candidate
14. Reset the score window and select only the remaining unmatched entries
15. Reconcile `name_@id` against Q43229 using the `country_@id` column as P17
16. Set the best candidate score window to 99-101 and match each entry to its best candidate
17. Reset the score window and select only the remaining unmatched entries
18. Reconcile `name_@id` against no type using the `country_@id` column as P17
19. Set the best candidate score window to 91-101 and match each entry to its best candidate
20. Reset the score window and select only the remaining unmatched entries
21. Create new entries for all of them
22. On the `organization_type` column, use `edit cells -> split multi-valued cells` and split using the delimiter `", "`
23. On the `organization_type` column, run the transformation using the Python formula `import re; return re.sub(r"^(?:and|or) ", "", value, flags=re.I)`
24. Create a column `organization_type_@id` as a copy of `organization_type` using the GREL formula `value.toLowercase()`
25. Reconcile `organization_type_@id` against Q811102
26. Set the best candidate score window to 99-101 and match each entry to its best candidate
27. Reset the score window and manually fix the remaining entries, creating new entries where necessary

## People

1. Create a column `earliest_year_@id` as a copy of `earliest_year`
2. Reconcile `earliest_year_@id` against Q577
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Create a column `latest_year_@id` as a copy of `latest_year`
5. Reconcile `latest_year_@id` against Q577
6. Set the best candidate score window to 99-101 and match each entry to its best candidate
7. Create a column `full_name_@id` as a copy of `full_name` using the GREL formula `value.replace(".", "").replace(/(.*?), (.*)/, "$2 $1")`
8. Reconcile `full_name_@id` against Q5 using the `rism_id` column as P5504
9. Set the best candidate score window to 99-101 and match each entry to its best candidate
10. Reset the score window and select only the remaining unmatched entries
11. Reconcile `full_name_@id` against Q5 using the `viaf_id` column as P214
12. Set the best candidate score window to 99-101 and match each entry to its best candidate
13. Reset the score window and create new entries for everything else

## Regions

1. Create a column `country_@id` as a copy of `country`
2. Reconcile `country_@id` against Q6256
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Reset the score window and manually fix the remaining entries, if any
5. Create a column `name_@id` as a copy of `name` using the GREL formula `value.replace(/(.*?)(?: \(.*\))?/, "$1")`
6. Reconcile `name_@id` against Q56061 using the `country_@id` column as P17
7. Set the best candidate score window to 99-101 and match each entry to its best candidate
8. Reset the score window and select only the remaining unmatched entries
9. Reconcile `name_@id` against Q82794
10. Set the best candidate score window to 99-101 and match each entry to its best candidate
11. Reset the score window and manually fix the remaining entries, creating new entries where necessary

## Sets

1. Create a column `type_@id` as a copy of `type`
2. Reconcile `type_@id` against no type
3. Set the best candidate score window to 90-101 and match each entry to its best candidate
4. Reset the score window and create new entries for everything else

## Sources

1. Create a column `source_type_@id` as a copy of `source_type`
2. Reconcile `source_type_@id` against no type
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Reset the score window and create new entries for everything else
