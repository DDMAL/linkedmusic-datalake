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
