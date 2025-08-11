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

Completed (Phase 1 Skeleton Scope)
----------------------------------
- Supervisor skeleton orchestration flow.
- Prompt builder (structured payload assembly).
- Baseline ExampleRetrievalAgent (token overlap heuristic).
- UnifiedOntologyAgent loading immutable unified TTL.
- Property mappings stub & manual builder script.
- Foundational behavioral tests.

Outstanding Gaps / Risks
------------------------
1. Property mappings extractor automation & coverage metrics missing (stub is manual).
2. No caching (Wikidata lookups & ontology slices) → latency + rate limit exposure.
3. google-genai version drift / lack of extras grouping.
4. Broader tests absent (Wikidata tool mock, regression dataset harness, negative cases).
5. Runtime config consolidation (endpoints, prefixes, rate limits) incomplete.
6. Evaluation harness (accuracy/latency/token metrics) not built.
7. CI pipeline absent (lint + tests + mini eval + ontology immutability guard).
8. Multi‑provider expansion (OpenAI / Anthropic) missing.
9. Error handling / retry/backoff minimal.
10. Example retrieval semantic upgrade (embeddings) not implemented.
11. Ontology relevance heuristic simplistic (lexical only; no alias weighting).
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
1. Property mappings extractor + coverage report (mapped %, unresolved terms list, alias suggestions).
2. Ontology relevance: integrate alias expansion & scoring; deterministic pruning.
3. Caching layer (LRU) for Wikidata & ontology slices w/ metrics (hit%, size).
4. Evaluation harness v1 -> JSONL (provider, latency_ms, tokens_in/out, success, error_type).
5. Runtime config consolidation (prefixes, endpoints, rate limits, provider keys via .env).
6. CI pipeline (GitHub Actions): lint, unit tests, ontology hash check, tiny eval subset.
7. Provider stubs (OpenAI, Anthropic) reusing prompt + tool interface.
8. Prompt budgeting & trimming strategy (score-based node/property ranking).
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

Last Updated: 2025-08-11 (phase 1 skeleton complete; roadmap reprioritized)

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

