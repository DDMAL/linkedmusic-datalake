# APSearch — ELAR enrichment (post-deadline track)

**Status: scoped, recommended *not* to attempt before the deadline.** The CKG dump gives
APSearch its media classes, licenses, publisher, dates and content URLs — but **not** the
fields that reconcile beautifully to Wikidata: documented **language**, **country**, and
**depositor/speaker**. Those live in the ELAR source. This is the APSearch analogue of
musiconn's Track 2, but unlike Track 2 there is **no anonymous, machine-readable, join-able
route** to the source. Ship CKG-only APSearch; pursue enrichment afterward with authenticated
access. Full spike: [`_archive/elar-enrichment-spike.md`](_archive/elar-enrichment-spike.md).

## Why it's blocked (the four sources investigated)

| Route | Result |
|---|---|
| **apsearch.org/record/<hash>** | 200 but a ~565-byte SPA shell, no embedded metadata; the feed's API base (`apsearch.org/api/ckg`) → 503 (down) |
| **ELAR new catalogue** (`elararchive.org`, Preservica) | the `hdl:2196` handle resolves (302 → an `IO_<uuid>` page), but the anonymous page is metadata-poor and the Entity API / OAI-PMH are **auth-walled** (401) |
| **OLAC mirror** (`language-archives.org/archive/soas.ac.uk`) | public + rich (93,687 records) but **frozen at 2021-11-01** (pre-migration) and keyed by old **SOAS IDs**, *not* the `hdl:2196` handles — no deterministic join |
| **id.smb.museum** (the 72 SMB records) | resolves, but a different catalogue/model — a separate problem |

So the join key reaches a real ELAR page, and the fields are demonstrably there — the blocker
is purely **access + join**, not field availability.

## The enrichment target (when access is obtained)

ELAR's IMDI/OLAC metadata carries the reconcilable fields. Verified property mappings (PIDs
confirmed in [`_archive/apsearch-pid-qid-verification.md`](_archive/apsearch-pid-qid-verification.md) §1b):

| ELAR/IMDI field | Wikidata property | Reconciliation route |
|---|---|---|
| documented language | `wdt:P407` language of work | name → `P220` (ISO 639-3) / `P1394` (Glottolog) → QID — **not** code-direct (codes are often `und`) |
| country | `wdt:P17` | name → Wikidata country item |
| location / region | `wdt:P276` (or `P131` admin / `P706` terrain) | name match (namesake-prone) |
| depositor / recorder / speaker | `wdt:P170` creator | no dedicated "depositor" property exists |
| creation date | `wdt:P571` inception | already emitted from the CKG dump |

This is high value — every ISO 639-3 language has a Wikidata item, so languages/countries
reconcile excellently — which is why the track is worth keeping.

## Path forward

1. **Authenticated ELAR/BBAW Preservica access**, keyed `hdl:2196` handle → `IO_<uuid>` →
   Entity API (or an authenticated OAI-PMH harvest). Free registration exists; a bulk harvest
   needs ELAR/BBAW sign-off — contact `elararchive@soas.ac.uk` / BBAW. **Tell the user before
   any such fetch** (it is an outward-facing, credentialed bulk request).
2. **Name-based language reconciliation** (language name → Glottolog/ISO 639-3 → Wikidata),
   since the source codes are frequently `und`.
3. Handle the **72 SMB-Berlin** records via `id.smb.museum` separately if wanted.
4. **Low-confidence quick win (not recommended):** a *title-based* match of the 6,271 records
   against the frozen public OLAC mirror could recover language/country for the pre-2021
   subset — but it is heuristic, partial, and namesake-prone; flag for manual review only.

**Open question for the user:** pursue the authenticated ELAR/BBAW harvest as a post-deadline
follow-up (Claude can draft the access request), or close the enrichment track and keep
CKG-only APSearch?
