# 27 — Source and Evidence Inventory

PR-EG-R5 · 2026-10-17 · investigation only

Evidence classes used throughout:

| Class | R5 use | Artifacts |
|---|---|---|
| A source inspection | production routes and runtime prompt dependencies | source_inventory.json, bundled source files and linked anchors |
| B historical production | R4 69 turns and R4-R1 24 turns | predecessor raw turns, metrics, JUnit comparison, source snapshots/hashes, provider usage |
| C controlled current production | seven local function probes, three prompt captures, selected existing tests incl. HTTP and snapshot checks | controlled_probes.json, payload_captures.json, checks_junit.xml, checks_run.json, controlled_replay |
| D isolated provider | not performed | no proposed-plan provider prompts/outputs claimed |
| E fresh-provider final code | not performed by R5 | predecessor fresh traffic is historical only |
| F architectural hypotheses | C’s expected quality/latency and boundary design | reports 15–26; thresholds are proposals |

`source_inventory.json` inventories 227 source modules; this is not a claim of equally deep manual review of every module. The pipeline map identifies the inspected core. Additional relevant production files included for review: interaction_routing, interaction_completion, intent_parser, noncombat_resolution, resolution_contract, gm_resolution_decision, proposition_authority, discourse_state, semantic_interpreter, bounded_improvisation, dialogue_social_plan, social_exchange_emission/policy/fallback_catalog, speaker_contract_enforcement, final_emission_gate/strict_social_stack/visibility_fallback/response_type, narration_state_consistency, upstream_response_repairs, prompt_context, response_policy_enforcement, models, storage and provider_budget. Experimental-directory adapter/schema/eligibility/prompt code is included because it executes in production.

Primary preserved raw histories: [artifacts/pr_eg_r4/turns.jsonl](../../artifacts/pr_eg_r4/turns.jsonl) and [artifacts/pr_eg_r4_r1/live_turns.json](../../artifacts/pr_eg_r4_r1/live_turns.json). R5 extracts retain complete metadata for 13 identities, avoiding a misleading reconstruction of unavailable provider interpretation. Historical response IDs and token usage are evidence of past calls only.

Reproduce local analysis with `.venv/Scripts/python.exe artifacts/pr_eg_r5/investigate.py`, payload capture with `payload_probe.py`, selected checks with `run_checks.py`, and reports/package with `build_reports.py`. Run from the repository root. All new helper paths are analysis artifacts, not runtime imports. Existing predecessor replay output is redirected under R5 during checks. Baseline hashes and preservation_check.json verify no edits to game/data/tests/experiments or predecessor evidence.

The standard `tools/build_review_handoff.py` produces CURRENT_REVIEW.md, REVIEW_MANIFEST.json and CURRENT_REVIEW.zip. The manifest identifies included canonical sources, sizes, SHA256 and omissions. Production .env, credentials, caches, venv and disposable runtime trees are excluded. The previous CURRENT_REVIEW is archived before replacement. R5 bundle verification checks every declared payload hash, required 27 reports, source links and preservation.
