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

Outstanding Gaps / Risks
------------------------
1. Supervisor + sub‑agent orchestration layer absent (currently only individual pieces).
2. Prompt builder module missing (no unified assembly of instructions + ontology + mappings + examples).
3. `property_mappings.json` absent (can now be auto‑seeded from existing dataset assets; extractor script required).
4. No caching layer for repeated lookups (risk: latency, rate limits).
5. google-genai dependency not yet explicitly pinned (Gemini integration requires it).
6. Missing tests (OntologyAgent, wikidata_tool, integration flows, regression on CSV dataset).
7. No runtime configuration (SPARQL endpoint URL, graph prefix map, rate limit overrides).
8. No automated evaluation script / harness to recompute correctness & log provider metrics.
9. No CI pipeline (lint + tests).
10. Multi‑provider architecture incomplete (only Gemini; OpenAI / Anthropic placeholders absent).
11. Error handling / retries around network calls minimal.
12. Example retrieval agent not implemented (no similarity search / indexing over existing NLQ/SPARQL pairs).
13. Unified ontology not yet parsed into an internal query‑time index; current OntologyAgent logic assumes smaller per‑dataset TTLs.
14. Risk of prompt bloat or omission without a relevance extraction algorithm over growing unified ontology.

Assumptions (To Validate / Document)
------------------------------------
- Named graphs deployed at Virtuoso with prefixes like `ts:` and `diamm:` pointing to canonical IRIs.
- LLM should generate queries WITHOUT SERVICE / OPTIONAL unless explicitly allowed.
- Post‑generation validation (syntax + dry‑run) desirable before presenting to user.

Short‑Term Roadmap (Priority Ordered)
-------------------------------------
1. Add tests for new skeleton (ontology slice hash guardrail, example retrieval ordering, supervisor prompt keys).
2. Enhance ontology relevance (property alias expansion using property_mappings stub).
3. Implement real property mappings extractor to populate stub JSON (metrics: mapped %, unmapped count).
4. Introduce caching (LRU) for Wikidata + ontology slices.
5. Evaluation harness generating per‑provider JSONL metrics.
6. Runtime config consolidation (prefix map, endpoints, provider keys via env).
7. Provider expansion (OpenAI / Anthropic stubs).
8. Prompt optimization & size budgeting.
9. Query verification (syntax + prefix filtering; later semantic dry‑run).
10. CI workflow (lint, unit tests, smoke eval) incl. ontology hash check.
11. Upgrade example retrieval to embedding similarity.
12. Self‑healing loop (post baseline accuracy).

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

Last Updated: 2025-08-11 (added skeleton multi-agent architecture & updated roadmap)
