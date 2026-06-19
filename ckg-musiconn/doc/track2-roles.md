# musiconn Track 2 — native-API role supplement (planned)

**Status: scoped and feasible, not yet built.** CKG flattens musiconn's
performer/composer/conductor **roles**: all 128,205 person↔event links are role-agnostic
(`cto:CTO_0001009`, no role qualifier). The roles still exist at the source — Track 2
recovers them and emits them as a separate, additive graph that joins to the Track-1 spine
via the same person nodes.

Output graph: `https://linkedmusic.ca/graphs/musiconn/` (parallel to the spine
`ckg-musiconn`). Planned script: `src/fetch_musiconn.py`. Full spike findings:
[`_archive/musiconn-api-spike.md`](_archive/musiconn-api-spike.md).

## Access route: HTML scraping (no JSON API yet)

There is **no public JSON/REST API**. The `CTO_0001080` value
`https://performance.musiconn.de/api` in the dump is a placeholder — all `/api/*` paths 404,
and the site FAQ says a GraphQL interface is "coming soon". The site is server-rendered, so
the only route is HTML scraping. **Check whether GraphQL has launched before building the
scraper** — if it has, the scraper is disposable.

All three feasibility checks pass via HTML:

- **Event page** `performance.musiconn.de/event/<slug>` — the CKG event URIs *are* these
  slugs, so they are direct join keys. The "Beteiligte Personen" section lists, per person, a
  **numeric site-ID**, **display name**, and **role string(s)** in German (e.g. `Dirigat`,
  `Tenor (Stimmlage)`, `Inszenierung`). A parallel "Beteiligte Körperschaften" section does
  the same for organizations (e.g. `Veranstalter`).
- **Person page** `performance.musiconn.de/person/id/<numeric-id>/` exposes the **Wikidata QID
  directly**, plus GND/VIAF. Note: the **slug** form (`/person/kaufmann-f`) returns an empty
  shell — only the **numeric-ID** form works, so residue (slug-only) persons can't be looked up.

## Join strategy

Two person populations in the event graph:

- **Authority-backed** (the collapsed GND/VIAF nodes already in `crosswalk.json`): event HTML
  → person numeric ID → person page → read the Wikidata QID directly off the page (fallback:
  GND/VIAF → crosswalk). ~79% of relation-weighted persons.
- **Residue** (bare slug URIs, no authority): emit the role triple against the CKG slug URI
  with **no `P2888`**, leave for OpenRefine later. Do **not** skip — the role is still worth
  keeping.

## Role string → Wikidata property

German role strings need a `role_map.json`. The verified mappings so far (PIDs/QIDs confirmed
in [`_archive/pid-qid-verification.md`](_archive/pid-qid-verification.md)):

| German string | Wikidata property | Notes |
|---|---|---|
| `Dirigat` | `wdt:P3300` musical conductor | unambiguous |
| `Komposition` | `wdt:P86` composer | |
| `Libretto` | `wdt:P87` librettist | |
| `Inszenierung` | `wdt:P57` director | covers opera/stageplay direction |
| `Veranstalter` | `wdt:P664` organizer | direct property (cleaner than a P710+P3831 qualifier) |
| `Tenor`/`Sopran`/`Bass`/… `(Stimmlage)` | `wdt:P175` performer **on the event** + `wdt:P412` voice-type QID **on the person** | P412 is a person-level property; emit both |
| anything unrecognised | `wdt:P710` participant | fallback (role detail lost) |

Voice-type QIDs (emitted as `<person> wdt:P412 wd:Q…`): Q27914 tenor, Q30903 soprano,
Q27911 bass, Q186506 mezzo-soprano, Q31687 baritone, Q6983813 alto, Q223166 countertenor.

> **`P3831` (object has role) is deliberately not used** — it is a Wikidata *qualifier* and
> would require blank-node reification, which violates the no-blank-nodes rule. Use the direct
> properties above; fall back to `P710` for the truly unresolvable.

## Before a full run

- **Enumerate the role strings first.** Do a ~1k-event dry run to collect every `<li>` role
  string in the wild, then complete `role_map.json`. Strings seen-but-not-yet-mapped include
  `Leitung`, `Choreographie`, `Bühnenbild`, `Dramaturgie`, `Lichtgestaltung`, `Kostüm`, `Text`
  — each needs a property lookup added to the verification doc before use.
- **Scale + etiquette.** 65,359 events × ~1 req/s ≈ days of crawling. Cache `numeric_id → QID`
  across events. Rate-limit to ≤1 req/s, set `User-Agent: LinkedMusic-datalake/1.0
  (liam.pond@mail.mcgill.ca)`, don't parallelise across IPs, and contact
  `musiconn.performance(at)slub-dresden.de` before any full-scale crawl. Start with one series
  (e.g. Staatsoper Dresden) to validate the shape.
