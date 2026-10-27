# Reconciled identifier validation

Implemented 21 October 2026. The `matched_wikidata` predicate now accepts only
complete bare item IDs matching `Q[1-9][0-9]*`. Missing or non-string values
return false. This repairs acceptance of `Q42suffix`, `Q42 / Q43`, zero,
leading-zero IDs, Unicode digits and trailing whitespace. It also avoids a
TypeError for blank CSV cells converted by pandas to null.

## Export evidence and scope

The [reconciliation procedure](reconciliation.md) and all nine tracked
[OpenRefine export templates](../openrefine/export/) separate original text
from copied `*_@id` columns. The histories create those columns with `grel:value`
or documented name transformations before reconciliation. Every `*_@id` export
column requests `output="entity-id"`, retains unmatched cells with
`blankUnmatchedCells=false`, and sets `linkToEntityPages=true`.

The existing converter concatenates accepted IDs onto the Wikidata namespace.
We retain its bare-ID input contract: neither the link-display setting nor the
histories establish a requirement to parse full URLs in this route. Full URLs,
`wd:Q42`, property IDs, prose and candidate lists are therefore not accepted as
matches. No whitespace stripping, substring extraction or candidate selection
occurs. This inspects checked-in contracts, not actual historical exports.
Verify real exported cell shapes when snapshot access returns before broadening
this contract or assessing impact.

For archive, city, country, organization, person and region name matches, a
complete QID yields a canonical P2888 object while the DIAMM subject and original
label remain. Invalid or missing IDs produce no P2888 link; original names remain
labels. Genre and organization/set/source type mappings fall back to their
original text columns, not the rejected `*_@id` value. A value that looks like
an ID does not independently establish reconciliation correctness.

The 21 October change applied to the existing helper's ten call sites and did
not redesign dates. The separate people `earliest_year_@id` and `latest_year_@id`
branches were repaired on 26 October under the
[person-year contract](person_years.md): they now use this validator and retain
original year/ID/approximation evidence. Direct date objects now use year
literals; validated year-item links belong to observations. Outside those year
observations, no lossless audit of rejected identifier-cell text is added;
the original label remains the documented fallback.

## Import-safe conversion and tests

`build_rdf_graph(base_path, relations_path, relations_mapping_path)` now contains
the existing file reads and conversion loops and returns the graph. Imports do
not read CSVs or relations JSON, create output directories or run conversion.
`main()` creates output and serializes, guarded by `if __name__ == "__main__"`.
Running `python convert_rdf.py` from `diamm/src/` retains the existing relative
input/output paths. The main diff is indentation of the unchanged conversion
loops; relations mapping is now local to each call.

Five [offline tests](../tests/test_identifier_conversion.py) cover:

- Complete bare IDs and negative controls, including None, NaN and numbers.
- Temporary CSVs with all nine export column layouts, exercising every helper
  call site with valid, partial, ambiguous, blank and full-URL values. Expected
  triples independently specify source subjects, labels, types and relations.
- Exact graph comparison and a Turtle round trip, preserving local composition
  → person and source → archive relationships.
- Importing from an empty working directory with no conversion output.
- Running the actual script with its default relative layout and reading its
  resulting Turtle from a temporary directory.

After the import refactor but before the validator change, these tests reported
nine failures and four errors. They now pass. At that repair, the unified offline
command included `diamm/tests` and passed **74 tests and 14 competency fixture
queries**, up from 69 and 14. Black and diff checks passed. The later person-year
repair brought the total to 95 tests; the person-name preservation follow-up
brought the total to **99 tests and 14 competency fixture queries**. The later
[external identifier text repair](external_identifier_text.md) protects archive
RISM and person RISM/VIAF cells from numeric and null inference; it adds five tests.
No historical files are needed by the tests.

Snapshot validation, affected-population counts and regeneration remain deferred.
Before any production replacement, obtain matching reconciled CSVs, record their
checksums and conversion version, classify actual ID-cell values, verify label
fallbacks and source relationships, and regenerate into a separate directory.
Apply the person-year contract's additional date/flag checks. Do not rewrite
existing malformed IRIs without their source cells. This local repair changes
no stored or live RDF.
