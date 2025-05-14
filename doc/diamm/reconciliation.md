# DIAMM Database Reconciliation

## Archives

1. Create a column `country_@id` as a copy of `country`
2. Reconcile `country_@id` against Q6256
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Reset the score window and fix the remaining countries
5. Create a column `city_@id` as a copy of `city`
6. Reconcile `city_@id` against Q515 (using column `country` as property country (Pxxx))?
7. Set the best candidate score window to 99-101 and match each entry to its best candidate

## Compositions

1. On the `genres` column, use `edit cells -> split multi-valued cells` and split using the delimiter `;`
2. Create a column `genres_@id` as a copy of `genres`
3. Reconcile `genres_@id` against Q188451
4. Set the best candidate score window to 99-101 and match each entry to its best candidate
5. Reset the score window and create new entries for everything else
6. On the `genres` column, (but **not** on the `genres_@id` column), use `edit cells -> join multi-valued cells` and join using the delimiter `;`

## Organizations

1. Create a column `country_@id` as a copy of `country`
2. Reconcile `country_@id` against Q6256
3. Set the best candidate score window to 99-101 and match each entry to its best candidate
4. Reset the score window and fix the remaining countries
5. Create a column `city_@id` as a copy of `city`
6. Reconcile `city_@id` against Q515 (using column `country` as property country (Pxxx))?
7. Set the best candidate score window to 99-101 and match each entry to its best candidate

## People

1.

## Sets

1.

## Sources

1.
