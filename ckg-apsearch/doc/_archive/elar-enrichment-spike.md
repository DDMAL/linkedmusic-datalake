# APSearch / ELAR enrichment spike — findings (2026-06-17)

Spike for **open decision #3** in [`HANDOFF-apsearch.md`](HANDOFF-apsearch.md): can we enrich
APSearch (`E6304`) records from the **ELAR source** with the fields that reconcile well to
Wikidata (languages, countries, depositors), keyed on the CKG record? Modelled on
[`musiconn-api-spike.md`](musiconn-api-spike.md). All probes were single, polite GETs with
`User-Agent: LinkedMusic-datalake/1.0 (liam.pond@mail.mcgill.ca)`.

## Summary

**The reconcilable fields exist in ELAR's metadata, but there is no public, machine-readable,
join-able source keyed to the CKG records. Recommendation: ship CKG-only APSearch for the
2026-06-30 deadline; treat enrichment as a post-deadline follow-up that requires authenticated
ELAR/BBAW catalog access.**

| Feasibility check | Result | Notes |
|---|---|---|
| 1. Do the CKG join keys resolve to a source record? | **YES** | content-URL handle `hdl:2196/…` → 302 → ELAR catalog page; `apsearch.org/record/<hash>` → 200 |
| 2. Does a source expose languages / countries / depositors? | **YES** | ELAR's IMDI/OLAC metadata carries all three (sample below) |
| 3. Are those fields reachable **anonymously + machine-readable**? | **NO** | new ELAR catalog API/OAI-PMH = auth-required; apsearch API = down; OLAC mirror = frozen + not join-able |
| 4. Can the metadata be **deterministically joined** to a CKG record? | **NO (public)** | the only public mirror is keyed by old SOAS IDs, not the `hdl:2196` handles in the dump |

So unlike musiconn Track-2 (where HTML scraping *did* recover the missing roles), APSearch
enrichment has no comparable anonymous route.

---

## What APSearch actually is (corrects HANDOFF §2)

Profiled from the dump (`profile_predicate.py` + joins over
`raw_data/ckg/mnt/data/culture-kg-kitchen/data/production/E6304/nt/E6304.nt`):

- **6,271 records.** Content URLs split **two** ways, not one:
  - **3,711 → `hdl.loc.gov/hdl:2196/…`** — ELAR handles (Library of Congress handle proxy;
    prefix `2196` is ELAR's). These 302-redirect to ELAR's catalogue.
  - **72 → `id.smb.museum/digital-asset/…`** — **Staatliche Museen zu Berlin** objects. These
    are exactly the 72 records carrying `creativecommons.org/by-nc-sa/4.0`. So APSearch is
    ~98.9 % ELAR + ~1.1 % SMB-Berlin, *not* 100 % ELAR.
  - (the remaining records have no `associatedMedia` content URL at all)
- Publisher (`NFDI_0000191`) is the constant `…/id/E2431` = **Berlin-Brandenburg Academy of
  Sciences and Humanities (BBAW)** — confirming ELAR's 2021 move to BBAW (see verification doc).

## The four sources investigated

### A. `apsearch.org/record/<hash>` — dead end
- `GET` → **HTTP 200**, but the body is a **565-byte SPA shell** (no embedded metadata, no
  JSON-LD, no `__NEXT_DATA__`). All data is loaded client-side from the API.
- The API base in the feed (`CTO_0001080` = `https://apsearch.org/api/ckg`) → **HTTP 503**
  (down). Same situation as musiconn's placeholder API.

### B. ELAR's *new* catalogue (`elararchive.org`, Preservica) — gated
- The handle resolves: `hdl:2196/00-0000-0000-0008-9FF2-4` → **302** →
  `https://www.elararchive.org/uncategorized/IO_7703316b-…/`. So the join key reaches a real
  ELAR "Information Object" page. ✅
- But the **anonymous asset page is metadata-poor**: it shows only "Asset" + folder name and
  *"you do not have permission to access the full content."*
- The Preservica **Entity API** (`/api/entity/information-objects/<uuid>`) → **HTTP 401**
  `not.authenticated` / `no.token.header`.
- Preservica's **OAI-PMH** Data Provider requires authentication by policy ("unauthenticated
  access … is no longer supported"; per `developers.preservica.com`).
- → The route that *would* join deterministically (handle → `IO_<uuid>` → entity metadata)
  is **credential-walled**. Free registration exists; a bulk programmatic harvest would need
  ELAR/BBAW permission.

### C. OLAC mirror (`language-archives.org/archive/soas.ac.uk`) — public but unusable here
- ELAR **is** an OLAC archive (id `soas.ac.uk`, "IMDI-OAI-OLAC", **93,687 item-level
  records**, free public access) — and OLAC republishes the metadata publicly, so it is *not*
  auth-walled.
- **But it is frozen.** `Last Harvested: 2021-11-01`, `Latest Datestamp: 2021-04-28`; the base
  URL is the dead SOAS host `https://lat1.lis.soas.ac.uk/ds/oaiprovider/oai2`. OLAC marks the
  archive **inactive** (red-cross icon). It captured the **SOAS-era** catalogue, before the
  BBAW/Preservica migration that produced the handles in the CKG dump.
- **No join key.** OLAC records are identified as `oai:soas.ac.uk:MPI549741`, deposit code
  `IGS0125`, and `lat1.lis.soas.ac.uk/ds/asv?openpath=MPI549741#`. **None of these is the
  `hdl:2196` handle** the CKG dump carries. The only possible bridge is the free-text title —
  namesake-prone and incomplete (post-2021 deposits are absent), exactly the failure mode the
  musiconn/Detmold lessons warn against.
- **ISO 639-3 is unreliable** in the export: the sample's language is
  `dc:subject olac:code="und"` (Undetermined) with the name "Dalabon" in text — so even with a
  join, language reconciliation would be **by name**, not by code.

### D. `id.smb.museum` (the 72 SMB records) — resolves, separate problem
- `id.smb.museum/digital-asset/<n>` → 301 → `getAssetId.php?objectId=<n>` → 200. A different
  catalogue (Berlin museums) with its own metadata model; out of scope for an ELAR spike.

---

## The enrichment target shape (sample OLAC record, for the eventual harvest)

`http://www.language-archives.org/sample/soas.ac.uk` (record `oai:soas.ac.uk:MPI549741`):

```
dc:coverage          Australia                         → country  (P17)
dc:contributor (speaker)  Maggie Tukumba               → P170 (no dedicated "depositor" property)
dc:contributor (recorder) Maïa Ponsonnet, M. Rabusseau → P170
dc:subject olac:language code="und"  Dalabon           → language (P407); reconcile name→P220/P1394
dc:date              2010-07-23                         → P571 (already in the CKG dump too)
dc:description       Language_Name: Dalabon; Country: Australia; …
```

So the fields are real and rich — language, region/country, speaker/recorder/depositor, date —
and *would* reconcile well (every ISO 639-3 language has a Wikidata item). The blocker is purely
**access + join**, not field availability.

### Field → Wikidata property mapping (draft; all PIDs verified — see verification doc)

| ELAR/IMDI field | Wikidata property | Reconciliation route |
|---|---|---|
| documented language | **P407** language of work or name | name → **P220** (ISO 639-3) / **P1394** (Glottolog) → QID; *not* code-direct (codes are often `und`) |
| country | **P17** country | name → Wikidata country item |
| location / region | **P276** location | name match (namesake-prone) |
| depositor / recorder / speaker | **P170** creator | no dedicated "depositor" property exists on Wikidata; P170 is the generic fallback |
| date / creation period | **P571** inception | already emitted from the CKG dump |

---

## Recommendation

1. **Ship CKG-only APSearch for 2026-06-30.** The structured reconciliation surface in the dump
   itself is small (licenses, publisher, media classes, AAT codes — all handled in the
   conversion + verification doc). Don't block the deadline on enrichment.
2. **Do *not* attempt an anonymous bulk enrichment.** There is no public source that is both
   join-able to the CKG handles and current. Any real harvest hits the auth wall (B) or the
   frozen/un-join-able mirror (C).
3. **Post-deadline path (worth doing).** Enrichment is genuinely valuable (ELAR is endangered
   languages → ISO 639-3 / Glottolog / country reconcile excellently). It requires:
   - **Authenticated ELAR/BBAW Preservica access**, keyed by `hdl:2196` handle → `IO_<uuid>` →
     Entity API or an authenticated OAI-PMH harvest. Contact `elararchive@soas.ac.uk` / BBAW
     (free registration exists; a bulk crawl needs their sign-off). **Tell the user before any
     such fetch.**
   - **Name-based language reconciliation** (language name → Glottolog/ISO 639-3 → Wikidata),
     since the codes are often `und`.
   - Handling the 72 SMB-Berlin records via `id.smb.museum` separately if desired.
4. **If a quick partial win is wanted:** a *title-based* match of the 6,271 CKG records against
   the public OLAC mirror (93,687 SOAS-era records) could recover language/country for the
   subset that pre-dates the 2021 migration — but it is heuristic, partial, and namesake-prone.
   Flag as low-confidence; not recommended without manual review.

**Open question for the user:** pursue the authenticated ELAR/BBAW harvest as a post-deadline
follow-up (I can draft the access request), or close the enrichment track and ship CKG-only?
