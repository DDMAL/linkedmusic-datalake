NLQ2SPARQL Project Status (Living Document)
==========================================

Purpose
-------
Provide natural‑language to SPARQL generation for LinkedMusic datasets (e.g. MusicBrainz, The Global Jukebox, Dig That Lick, DIAMM, The Session) using a multi‑step agent architecture: a supervising (router) agent orchestrates specialized sub‑agents for entity/property resolution, ontology extraction, example retrieval, and final SPARQL synthesis, with systematic evaluation across multiple LLM providers.

High‑Level Goals
----------------
1. Accept an NL question and return a validated, minimal SPARQL query scoped to the correct named graph.
2. Use a Supervisor Agent to coordinate:
   - Entity/Property Agent (Wikidata QID / PID lookup via tool calls).
   - Ontology Agent (on‑demand, filtered schema extraction from large TTL files).
   - Example Retrieval Agent (surface relevant NLQ↔SPARQL exemplars from curated dataset for few‑shot prompting).
   - (Future) Verification / Repair Agent (syntax + semantic checks; auto‑repair strategies).
3. Reduce hallucination and over‑generalization through constrained inputs (ontology slice, explicit mappings, resolved IDs).
4. Track per‑LLM performance (accuracy, token usage, latency) over time and store run metadata for regression analysis.
5. Support experimentation with multiple providers (Gemini, OpenAI, Anthropic, others) under a unified interface.
6. Provide reproducible evaluation harness and clear incremental roadmap.

Current Components
------------------
- Unified Ontology Slice: `ontology/11Aug2025_ontology.ttl` (single cross‑dataset snapshot; DO NOT MODIFY CONTENTS – authoritative despite reconciliation imperfections).
- (Legacy per‑dataset ontology files slated for removal; no longer used for prompt grounding.)
- OntologyAgent (to be refactored) currently extracts simplified schema; will evolve into UnifiedOntologySubagent working off the unified TTL.
- Wikidata tools: `tools/wikidata_tool.py` (entity & property ID resolution).
- LLM integration scaffolding: base + Gemini integration (function calling only).
- Evaluation dataset: `query_database_10july2025.csv` (multi‑model attempts + gold SPARQL).
 - NEW: Consolidated dataset & mapping reference: `docs/dataset_mapping_cheatsheet.md` (lexicon seeding source).

Recent Changes (this branch)
----------------------------
- Added async Wikidata resolution tool functions (`find_entity_id`, `find_property_id`).
- Added package initializers for clean imports.
- Phase 1 skeleton architecture added: base, ontology, example, supervisor agents; prompt builder; property mappings stub + builder.
- Added outcome‑focused tests (ontology slice determinism, example ranking, prompt structure, supervisor end‑to‑end).
- Adjusted Wikidata precise search limits to 1 (entity/property) to match tests & reduce response noise.
- Root `conftest.py` ensures repository `code` package shadows stdlib `code` during pytest collection.
- Implemented automated property mappings extractor (`ontology/extract_property_mappings.py`) producing coverage + conflict metrics and updating `property_mappings.json`.
- Added raw TTL slice mode (`mode="ttl"`) to `UnifiedOntologyAgent` returning verbatim triple snippets (`ttl_snippets`).
- Supervisor now explicitly sets `ontology_mode=ttl` (future‑proofing for alternative modes).
- Added ontology agent mode test (ttl vs structured) raising total tests to 43 (all passing).
- Extended STATUS with future investigation note for intermediate mapping layer.

Completed (Phase 1 Skeleton Scope)
----------------------------------
- Supervisor skeleton orchestration flow.
- Prompt builder (structured payload assembly).
- Baseline ExampleRetrievalAgent (token overlap heuristic).
- UnifiedOntologyAgent loading immutable unified TTL.
- Property mappings stub + automated extractor + coverage metrics (current coverage ~81%).
- Raw TTL slice mode implemented & integrated (supervisor explicit mode call).
- Foundational behavioral tests.

Outstanding Gaps / Risks
------------------------
1. Property mappings enrichment: alias expansion, conflict resolution workflow, PID suggestion heuristics not yet implemented (only baseline extraction).
2. No caching (Wikidata lookups & ontology slices) → latency + rate limit exposure.
3. google-genai version drift / lack of extras grouping.
4. Broader tests absent (Wikidata tool mock, regression dataset harness, negative cases).
5. Runtime config consolidation (endpoints, prefixes, rate limits) incomplete.
6. Evaluation harness (accuracy/latency/token metrics) not built.
7. CI pipeline absent (lint + tests + mini eval + ontology immutability + coverage guard).
8. Multi‑provider expansion (OpenAI / Anthropic) missing.
9. Error handling / retry/backoff minimal.
10. Example retrieval semantic upgrade (embeddings) not implemented.
11. Ontology relevance heuristic simplistic (lexical only; no alias weighting or pruning scores).
12. Prompt size budgeting strategy absent (risk of token overflow later).
13. Query verification / repair loop missing.
14. Self‑healing / iterative refinement not started.

Assumptions (To Validate / Document)
------------------------------------
- Named graphs deployed at Virtuoso with prefixes like `ts:` and `diamm:` pointing to canonical IRIs.
- LLM should generate queries WITHOUT SERVICE / OPTIONAL unless explicitly allowed.
- Post‑generation validation (syntax + dry‑run) desirable before presenting to user.

Short‑Term Roadmap (Next Focus)
--------------------------------
1. Property mappings enrichment: alias sidecar file + conflict resolution + candidate PID suggestion scaffold.
2. Ontology relevance: integrate alias expansion & scoring; deterministic pruning and token budgeting heuristic.
3. Caching layer (LRU) for Wikidata & ontology slices w/ metrics (hit%, size).
4. Evaluation harness v1 -> JSONL (provider, latency_ms, tokens_in/out, success, error_type).
5. Runtime config consolidation (prefixes, endpoints, rate limits, provider keys via .env).
6. CI pipeline (GitHub Actions): lint, unit tests, ontology hash check, property coverage floor, tiny eval subset.
7. Provider stubs (OpenAI, Anthropic) reusing prompt + tool interface.
8. Prompt budgeting & trimming strategy (score-based node/property ranking) leveraging coverage + frequency.
9. Query verification module (syntax parse, allowed prefixes, graph scoping).
10. Example retrieval semantic upgrade (embedding model optional path).
11. Robust error handling utilities (retry w/ backoff + circuit breaker).
12. Self‑healing refinement loop (post-baseline).

Stretch Items
-------------
- Self‑healing loop: execute query; if empty & heuristics indicate mis-specified property, attempt auto‑repair using property mappings.
- Few‑shot library: curate minimal high‑value examples per dataset.
- Chain of Thought / tool call reasoning logging & anonymized analytics.
- Fine‑tuning / RAG over ontology + historical successful queries.
 - Embedding-based retrieval (vector DB) to replace baseline TF‑IDF retrieval.
 - Cost tracking & optimization (token economy dashboard).
 - SPARQL execution sandbox with timeout & result shape validation.

Metrics & Success Criteria
--------------------------
- Baseline accuracy (correct SPARQL) vs. after ontology + mapping injection.
- Average token count of prompts (target: keep schema segment < 1.5 KB).
- Median latency (goal: < 3s end‑to‑end for warm cache simple queries).
- Tool call success rate (entity/property resolved on first attempt ≥ 90%).
 - Per‑provider comparative accuracy & latency dashboard.
 - Prompt assembly determinism (hash stable given same inputs).
 - Property lexicon coverage: % NL test phrases resolved deterministically (target ≥70% initial, ≥90% after refinement cycle).
 - Ontology slice recall: % of gold query properties/classes present in extracted slice (target ≥95%) while keeping slice token size manageable (< configurable soft cap; no hard limit enforced per user guidance).
 - Zero mutation guarantee: hash of source ontology TTL remains unchanged across runs (guardrail test).

Open Questions
--------------
1. Do we support multi‑graph queries in first phase?
2. Should property mappings store disambiguation examples (e.g., "genre/style" → P136)?
3. Where to persist evaluation results (CSV extension vs. separate table)?
4. Minimum viable verification (syntax only vs. executing limited row sample)?
5. Do we need language localization support (non‑English queries)?

Update Process
--------------
- Edit this file on each milestone (add date + summary under a new heading if preferred later).

Last Updated: 2025-08-11 (phase 1 skeleton complete; ontology TTL slice mode + extractor automation + mode tests added)

Future Investigation Note (Intermediate Mapping Layer vs Direct TTL)
--------------------------------------------------------------------
Context (Added 2025-08-11): During early Phase 1 we discussed two alternative strategies for how the OntologyAgent supplies schema context to the LLM:
1. Direct TTL Slicing (CURRENT V1 CHOICE): Read the unified ontology file (`ontology/11Aug2025_ontology.ttl`) and extract ONLY the raw TTL blocks (verbatim triples) for subjects judged relevant to the user question. The agent returns these snippets unchanged (e.g., if only `ts:Tuneset` is relevant, it emits exactly that subject block with its predicates/objects). No NL paraphrasing, no restructuring.  This keeps implementation simple and guarantees fidelity to source.
2. Intermediate Mapping / Abstraction Layer (DEFERRED): Pre‑process ontology & relation inventories into a compact, NL‑oriented, alias‑rich JSON (e.g., `property_mappings.json` plus potential class/property summaries) that the LLM can ingest more economically. This layer would add curated aliases, confidence scores, usage frequencies, and allow coverage metrics & regression checks.

Decision for V1: Stick with (1) to minimize scope & moving parts. The OntologyAgent has been (or will be) adjusted to output raw TTL slices under a `raw_ttl` (and/or `ttl_snippets`) field so the Supervisor can inject those directly into prompts. No transformation beyond selecting which subject blocks to include.

Why Revisit Later:
- Token Efficiency: Raw TTL grows linearly with dataset count; many triples are irrelevant noise in prompts. A distilled mapping layer can cut prompt size while preserving semantic recall.
- Alias / Phrase Matching: User queries rarely mirror RDF labels exactly; intermediate layer supports robust normalization (aliases, inflections, synonyms) and property disambiguation.
- Governance & Metrics: JSON layer enables explicit coverage (%) of NL phrases → properties, conflict detection, and CI guardrails (fail builds if coverage regresses).
- Caching & Retrieval: Structured layer supports per‑query retrieval (fetch only N most relevant properties) vs. coarse TTL slicing.
- Extensibility: New datasets (future interns) just add an `extract_relations` script; unified harvester updates mappings automatically; less RDF parsing logic baked into agent code.

Deferred Architecture Sketch (for future implementers):
1. Standard Relation Export: Each dataset provides `extract_relations.py` emitting JSON objects: `{source, subject_type, raw_phrase, direction, object_type, candidate_pid?, evidence}`.
2. Harvester (existing prototype: `extract_property_mappings.py`): Merges all relation exports + existing mappings; normalizes phrases; tracks metrics (`mapped_count`, `unmapped_count`, `coverage`, `conflicts`).
3. Alias Sidecar: Human‑curated `alias_rules.yml` merged in (never overwritten by generator) to enrich matching without touching auto file.
4. PID Suggestion (future): Lightweight Wikidata search for unmapped phrases -> `candidate_pid_suggestions` with confidence scores.
5. CI Gates: (a) Coverage floor, (b) Zero conflicts, (c) Ontology TTL hash unchanged, (d) Report freshness check.
6. Query-Time Retrieval: Given user question -> extract phrases/tokens -> retrieve only needed subset of mappings (plus a few high‑scoring expansions) -> inject into prompt. Avoids dumping entire TTL or entire mappings file.
7. Optional Sharding: If mappings become large, shard by initial letter or semantic cluster; loader provides unified view.

Migration Plan When Revisiting:
Phase A (Introduce Safely): Keep raw TTL slice path; add optional `mode="mappings"` to OntologyAgent returning curated subset from mapping layer. Run dual‑path evaluation (A/B) to quantify token savings & accuracy impact.
Phase B (Optimize): Add caching & retrieval scoring (frequency * semantic similarity). Implement PID suggestion workflow & alias governance.
Phase C (Enforce): Switch Supervisor default to mapping mode; retain TTL fallback for debugging / explainability.

Risks If Deferred Too Long:
- Prompt bloat as ontology grows (The Session, DIAMM, RISM, etc.) leading to truncated or degraded model performance.
- Lack of measurable progress on property coverage; regressions may slip through unnoticed.
- Increasing manual burden to add aliases directly in code instead of structured sidecar.

Explicit TODO Trigger for Future Team:
Reassess once (a) raw TTL slice injected into prompts routinely exceeds a configurable soft token budget (e.g., >1500 tokens for schema section) OR (b) unmapped NL test set phrases exceed 15% of total queries. At that point, implement Phase A of the migration plan above.

Summary: V1 intentionally prioritizes simplicity & fidelity via direct TTL slicing. This note records the rationale and supplies a concrete, testable roadmap so a future contributor (or LLM agent) can implement the abstraction layer without rediscovery effort.


Step 1 (MVP) Scope Definition (Added 2025-08-11)
------------------------------------------------
Purpose: Deliver a lean, demonstrable NLQ→(proto)SPARQL preparation path for a narrow subset WITHOUT optimization layers or finalized example retrieval. Examples are explicitly deferred until external curated pairs arrive.

In-Scope (strict minimum RIGHT NOW):
1. Dataset Coverage: Single primary graph (choose ONE early: MusicBrainz OR The Session) for baseline queries (works ↔ artists OR tunesets ↔ tunes). Seed questions can exist as a simple list (no examples pairing required yet).
2. Ontology Context: Raw TTL slice mode (mode="ttl") – lexical token match + neighbor cap only.
3. Entity/Property Resolution: Minimal Wikidata lookup (top-1) with graceful fallback (missing IDs allowed).
4. Prompt Assembly: Existing prompt_builder producing system + user_question + ontology_context + resolved_ids. (NOTE: examples_text may be empty or contain a placeholder string.)
5. Query Output (Provisional): We may stub actual SPARQL generation for Step 1 if LLM integration waits on examples. Accept a placeholder or skeletal SELECT template.
6. Evaluation: Manual smoke list (seed_questions.md) asserting ontology slice non-empty + no crashes.
7. Determinism: Same question => identical ontology slice + prompt payload hash (excluding timestamps).

Explicitly Deferred (Requires external curated data):
- Example pairs (NLQ ↔ SPARQL) collection & relevance sub-agent scoring.
- ExampleRetrievalAgent enhancement beyond trivial placeholder.

Temporary Placeholder Behavior:
- ExampleRetrievalAgent returns a single static placeholder entry: `{question: "(examples deferred)", sparql: null}` until real dataset arrives.

Success Criteria (Objective for Deferred-Examples MVP):
- ≥80% seed questions yield: (a) non-empty ttl_snippets, (b) no unhandled exceptions, (c) deterministic ontology slice.
- Ontology slice token size < 1.5 KB (current heuristic).
- Zero mutation to source ontology TTL (hash stable).
- Placeholder examples pathway functional (prompt still serializable) even with empty real examples.

Explicitly Out-of-Scope (Deferred to Step 2+):
- Multi-dataset / multi-graph queries.
- Advanced alias / synonym expansion or property disambiguation scoring.
- Property mappings enrichment / coverage gating.
- Caching (ontology slice, Wikidata results).
- CI pipeline & automated evaluation harness.
- Embedding-based example retrieval or semantic ranking.
- Query verification / repair loop, self-healing retries.
- Token budgeting / prompt trimming heuristics beyond fixed neighbor cap.
- Multi-provider abstraction (stick to single provider binding or mock layer).
- Performance metrics dashboard & cost tracking.

Minimal Implementation Checklist (Revised MVP Step 1):
 [ ] Select target dataset subset (MusicBrainz OR The Session) and record decision in STATUS.
 [ ] Create `seed_questions.md` listing 5–10 NL questions (no answers required yet) + brief intent notes.
 [ ] Adjust ExampleRetrievalAgent to supply a static placeholder when no examples file present.
 [ ] Add pytest smoke test: for each seed question -> supervisor.run() returns ontology_slice.ttl_snippets non-empty.
 [ ] README: Add "MVP Step 1 Run" section (how to invoke smoke test & inspect a sample prompt JSON).
 [ ] Tag `nlq2sparql-mvp-step1` once above complete.

Post-External-Data TODO (Examples Phase Re-entry):
- Replace placeholder with `seed_examples.json` once curated pairs delivered by domain contributors.
- Introduce overlap scoring test & minimal accuracy metric.

Reasoning: This sharply delimits baseline so subsequent optimizations (caching, mapping abstraction, alias expansion) can be measured for delta impact instead of conflated with initial bring-up complexity.

Next Action Toward MVP: Curate seed question list + minimal examples file (no code changes needed to architecture) → add smoke test harness.


Multi-Dataset Federated Planning (Added 2025-08-11)
---------------------------------------------------
Context: All five datasets (MusicBrainz, The Session, DIAMM, The Global Jukebox, Dig That Lick) must be addressable transparently. The system should infer at runtime which graphs participate while hiding internal dataset boundaries from end users unless an explicit explain/debug mode is enabled.

Catalog Skeleton (INITIAL – CREATED):
- `catalog/concepts.json` – Abstract concepts (Artist, Work, Recording, Tune, TuneSet, Manuscript, Culture).
- `catalog/capabilities.musicbrainz.json` – MusicBrainz capability manifest (entities, relations, strengths, limitations).
- `catalog/router_rules.yml` – Ordered keyword/pattern rules mapping NL tokens → candidate datasets + concept hints.

Planned Additional Capability Files (PENDING):
- `catalog/capabilities.diamm.json`
- `catalog/capabilities.thesession.json`
- `catalog/capabilities.gj.json` (Global Jukebox)
- `catalog/capabilities.dtl.json` (Dig That Lick)

Future Linking Layer (NOT STARTED):
- `catalog/linking_rules.json` – Declarative join strategies (e.g., Artist via shared Wikidata QID across MusicBrainz & DIAMM; Tune ↔ Work heuristics; Culture ↔ Area mappings; instrumentation alignment).

Federated Query Planning Roadmap:
1. RouterAgent: loads router_rules.yml, scores patterns, outputs: `{dataset_candidates, concept_hints, rationale}`. (Rules file present; code NOT IMPLEMENTED.)
2. CapabilityLoader: merges capabilities.*.json to expose predicates/classes per candidate dataset. (PENDING)
3. OntologyAgent Enhancement: accept dataset list → filter TTL snippets by dataset prefix/namespace. (PENDING; current global slice.)
4. Plan Builder: produce intermediate plan JSON: `{concepts, datasets, steps:[{graph, rationale}]}` for prompt injection & testing. (PENDING)
5. Join Strategy Resolver: consult linking_rules.json to propose merge keys / alignment predicates. (PENDING)
6. Prompt Assembly Update: embed plan summary + per-dataset TTL sections (ordered by confidence). (PENDING)
7. Pre-SPARQL Validation: sanity check coverage (all required concepts represented) before generation. (PENDING)

Design Principles:
- Layer separation: Concepts (what) vs capabilities (how) vs router rules (when) vs linking rules (join logic).
- Determinism & Inspectability: plan JSON persisted (optional) to enable reproducible evaluation & diffing.
- Conservative Inclusion: prefer minimal dataset set satisfying concepts; add others only if high-confidence overlap or explicit mention.

Open Federation Questions:
F1. Multi-dataset inclusion threshold (absolute score vs margin vs concept coverage gap)?
F2. Conflict resolution when predicates differ semantically (pick richest / most specific?).
F3. Strategy decision for UNION vs multi-subquery with post-hoc join (cost vs completeness)?
F4. Soft cap on datasets per initial plan (2–3?) to control prompt size.
F5. Precomputed concept frequency metrics to rank fallback datasets? (future enhancement)

Incremental Implementation Order (Suggested):
 [ ] Implement RouterAgent stub returning dataset_candidates (musicbrainz only for now).
 [ ] Add capabilities loader (musicbrainz) & assert shape via test.
 [ ] Wire Supervisor -> RouterAgent -> OntologyAgent (still unfiltered TTL initially).
 [ ] Extend OntologyAgent to filter TTL by namespace (dataset-aware slices).
 [ ] Introduce plan object into prompt payload (tests for presence & determinism).
 [ ] Add negative test: question with domain-specific token routes away from unrelated dataset.
 [ ] Prepare placeholder capability files for at least one additional dataset to validate multi-load path.

Metrics (Future Federation Layer):
- Dataset routing precision/recall against labeled evaluation set.
- Plan size (tokens) vs single-dataset baseline.
- Join success rate (correct cross-dataset alignments present in gold queries).
- Time added by routing + capability loading (< 150ms target cached).

Risk Mitigation:
- Start with single dataset capability; others incremental to avoid speculative modeling.
- Keep router rules purely lexical first pass; later augment with embedding similarity if needed.
- Maintain fallback to single best dataset if federation confidence low.

Single vs Multiple STATUS Files Decision:
Decision: KEEP A SINGLE STATUS.md
Rationale: Central narrative avoids fragmentation & stale divergence. For deep dives (e.g., federation, mapping abstraction) create anchored subsections here first. Only if a subsection becomes disproportionately large or process-heavy, spin out a focused doc under `docs/` (e.g., `docs/federation.md`) and link back, while STATUS remains the authoritative timeline & milestone ledger.

Routing Layer Documentation (Added 2025-08-11)
---------------------------------------------
Purpose: Record the initial implementation details of the lexical routing layer so future sessions can continue federation work without re-deriving design intent.

Implemented Component:
- `RouterAgent` (`agents/router_agent.py`): Loads `catalog/router_rules.yml`, tokenizes question, applies additive boost scoring per matched rule.

Current Data Flow Order (Supervisor):
1. RouterAgent (if present) → routing dict.
2. OntologyAgent (still global TTL slice, not dataset-filtered yet).
3. WikidataAgent → entity/property IDs.
4. ExampleRetrievalAgent → baseline examples list.
5. Prompt assembly (injects routing under `config_meta.routing`).

Routing Output Fields (stored in `SupervisorResult.routing` and prompt config):
- `ranked_datasets` (List[str]): Dataset codes sorted by descending accumulated score.
- `dataset_scores` (Dict[str,float]): Raw additive scores per dataset.
- `concept_hints` (List[str]): Sorted unique abstract concepts implicated by matched rules.
- `matched_rules` (List[Object]): Trace objects containing:
   - `rule_index`: 0-based index within YAML.
   - `matched_patterns`: Patterns from that rule found in question.
   - `datasets`: Datasets boosted by this rule.
   - `boost`: Numeric weight applied.
   - `concepts`: Concept hints contributed.
- `tokens` (List[str]): Basic alphanumeric tokens (length ≥3) extracted from the NL question.
- `rule_count` (int): Total rules loaded (sanity/debug value).

Why Keep All Trace Data:
- Determinism / Repro: Matched rule indices + patterns allow regression tests to pinpoint changes when rules evolve.
- Explainability: Future `--explain` mode can surface rationale directly from this structure.

Separation of Layers (Recap):
- Concepts (`catalog/concepts.json`): Semantic WHAT the user asks about (Artist, Work, Manuscript...).
- Router Rules (`catalog/router_rules.yml`): Lexical WHEN/IF heuristics mapping surface tokens → datasets + concept hints.
- Capabilities (`catalog/capabilities.*.json`): HOW each dataset can answer (entities, predicates, limitations). Only MusicBrainz file exists now.
- (Future) Linking Rules: HOW TO JOIN across datasets when multiple chosen.

Dataset Code Legend:
- musicbrainz = `musicbrainz` (prefix target `mb:` later)
- The Session = `thesession` (prefix `ts:`)
- DIAMM = `diamm`
- The Global Jukebox = `gj`
- Dig That Lick = `dtl`

Current Limitations:
1. Ontology slice not filtered by `ranked_datasets` (still global TTL snippet selection).
2. Scores unnormalized (pure additive boosts; no thresholding).
3. No negative / exclusion rules or phrase boundary sensitivity (substring match only).
4. Capability validation not yet used to prune false-positive datasets.
5. Multi-dataset plan & join strategy unresolved (no linking rules file yet).

Planned Near-Term Enhancements (Routing → Planning Evolution):
 [ ] Introduce capability loader (start with existing musicbrainz file) to check if required concept hints are supported; drop unsupported datasets.
 [ ] Apply a simple threshold or top-N cap (e.g., keep datasets with score ≥0.6 * top_score or max 2) to stabilize prompt size.
 [ ] Pass filtered dataset list into OntologyAgent so TTL slicing can restrict subjects by namespace/prefix (add param `datasets`).
 [ ] Emit a structured `plan` object (separate from raw routing) summarizing: {datasets_selected, concepts, rationale_summary}.
 [ ] Add tests: (a) rule match triggers dataset inclusion, (b) unrelated query yields empty or single default dataset, (c) plan JSON stable for identical input.
 [ ] Prepare at least one additional capability stub (e.g., `capabilities.thesession.json`) to validate multi-load path.

Future (Beyond Immediate Increment):
- Introduce weight decay / tie-break on longer pattern lists to reduce overfitting.
- Add phrase boundary detection (`\bpattern\b`) to avoid accidental substring matches.
- Hybrid lexical + embedding similarity scoring (keep lexical deterministic path as primary).
- Confidence metric (e.g., softmax over scores) to drive fallback behavior.
- Linkage feasibility pre-check: only select multi-dataset if at least one linking rule exists connecting their concepts.

Testing Notes:
- New test (`test_supervisor_end_to_end_minimal`) now asserts routing dict presence and prompt config embedding.
- RouterAgent currently not directly unit-tested in isolation; future test could provide synthetic rules file to assert scoring merges.

Pickup Instructions for Next Session:
1. Implement capability loader (start by reading existing musicbrainz JSON; design interface returning entity & relation maps).
2. Extend OntologyAgent: accept `datasets` list -> filter TTL snippets whose compacted prefix matches allowed dataset prefixes (mb:, ts:, diamm:, dtl:, gj:).
3. Insert plan object (distinct from raw routing) into SupervisorResult & prompt.
4. Add tests covering dataset filtering & plan shape.
5. Create additional capability stub (`catalog/capabilities.thesession.json`) with minimal fields to exercise multi-capability load.

Reference SHA / Date: Commit after RouterAgent integration & tests passing (2025-08-11). All 43 tests green under Poetry environment.


Scope Guardrails & Adapter Plan (Added 2025-08-12)
--------------------------------------------------
Context: To avoid impacting other teams, keep functional changes within `code/nlq2sparql` and avoid edits to shared libs (e.g., `code/wikidata_utils`).

Guardrails:
- Scope: Only modify files under `code/nlq2sparql/` (docs/tests included). Shared modules remain untouched; if behavior is needed, use adapters.
- Adapters: Introduce a thin wrapper `code/nlq2sparql/integrations/wikidata_adapter.py` that owns `WikidataAPIClient` creation, session/loop handling, and any local fallbacks. Tools/agents import this adapter instead of importing `wikidata_utils` directly.
- Testing: Patch adapter functions/classes in tests, not shared libs, to keep test doubles isolated to nlq2sparql.
- Config: If necessary, expose minimal flags in `code/nlq2sparql/config.py` for timeouts/rate limits without touching shared code.
- Dependencies: pyproject updates allowed if needed for nlq2sparql; use conservative pins.

Status:
- Restored `code/wikidata_utils/` from `origin/main` to prevent cross-team drift; all tests pass (44/44) with nlq2sparql-local fixes only.

Action Items:
- [ ] Add `integrations/wikidata_adapter.py` and re-export a factory/getter for the Wikidata client.
- [ ] Route `tools/wikidata_tool.py` and `agents/wikidata_agent.py` through the adapter.
- [ ] Add a brief README note documenting the adapter boundary and patching guidance for tests.
- [ ] Keep `conftest.py` ensuring the repo `code` package shadows stdlib `code` during test collection.

