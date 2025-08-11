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
- Ontologies: `ontology/diamm_ontology.ttl`, `ontology/session_ontology.ttl`.
- OntologyAgent: extracts simplified schema for prompt grounding.
- Wikidata tools: `tools/wikidata_tool.py` (entity & property ID resolution).
- LLM integration scaffolding: base + Gemini integration (function calling only).
- Evaluation dataset: `query_database_10july2025.csv` (multi‑model attempts + gold SPARQL).
 - NEW: Consolidated dataset & mapping reference: `docs/dataset_mapping_cheatsheet.md` (lexicon seeding source).

Recent Changes (this branch)
----------------------------
- Added async Wikidata resolution tool functions (`find_entity_id`, `find_property_id`).
- Added package initializers for clean imports.

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

Assumptions (To Validate / Document)
------------------------------------
- Named graphs deployed at Virtuoso with prefixes like `ts:` and `diamm:` pointing to canonical IRIs.
- LLM should generate queries WITHOUT SERVICE / OPTIONAL unless explicitly allowed.
- Post‑generation validation (syntax + dry‑run) desirable before presenting to user.

Short‑Term Roadmap (Priority Ordered)
-------------------------------------
1. Supervisor Orchestrator (`supervisor.py`): dispatch order & data passing between sub‑agents; define interaction protocol (simple dataclass messages).
2. Prompt Builder (`prompt_builder.py`): unify system prompt assembly (ontology slice + examples + mappings + task instructions + resolved IDs placeholder region).
3. Example Retrieval Agent (`agents/example_agent.py`): similarity search over NLQ text (baseline: TF‑IDF / RapidFuzz; later upgrade to embedding index) returning k examples.
4. Build & populate `ontology/property_mappings.json` via automated extractor (inputs: DIAMM_SCHEMA, DIAMM relations.json, MusicBrainz mappings + relations, RISM mapping.json non‑empty values) plus curated synonyms (composer→P86, birth date→P569, genre→P136, performer→P175, location→P276, administrative area→P131, country→P17, part of→P361, instance of→P31, member of→P463, has part(s)→P527, shelfmark→P217, patron→P859, commissioned by→P88, dedicatee→P825, transcribed by→P11603, incipit→P1922, subject→P921, exact match→P2888).
5. Tests (phase 1):
   - Unit: OntologyAgent determinism.
   - Unit: wikidata_tool (mock network).
   - Unit: Example retrieval ranking.
   - Integration: supervisor end‑to‑end dry run (mock LLM) producing assembled prompt JSON.
6. Add `google-genai` dependency & feature gate via extras (e.g. `[gemini]`).
7. Caching layer (simple in‑memory LRU) for entity/property lookups.
8. Evaluation Harness (`evaluate_queries.py`): run N queries per provider, store JSONL with: provider, latency_ms, token_in/out (if available), correctness flags.
9. Runtime config (`config.py`): endpoints, graph prefix map, provider keys via env.
10. CI workflow: lint + tests + evaluation smoke (subset size=5) to catch regressions.
11. Add OpenAI & Anthropic provider stubs reusing BaseLLMIntegration.
12. Query verification module: parse & validate allowed prefixes, named graph scoping, disallow disallowed constructs.

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

Last Updated: 2025-08-11 (added dataset mapping cheat sheet + lexicon coverage metric)
