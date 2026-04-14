# Architecture Audit

## Executive verdict

- Repo-level verdict: **mixed / caution**
- Confidence: **medium**
- Recommended action mode: **needs targeted ownership cleanup before more features**
- Legacy subsystem roll-up color: **red**
- Modules analyzed: **86**
- Docs analyzed: **20**
- Test files analyzed: **186**

- Repo-level verdict: **mixed / caution** with scorecard total 9/18.
- Action mode: **needs targeted ownership cleanup before more features**.
- Hotspot mix: 5 localized, 3 transitional, 0 possible smear, 0 unclear.

## Repo-level scorecard

| Dimension | Status | Points |
| --- | --- | ---: |
| ownership clarity | clear | 3/3 |
| overlap severity | localized hotspots | 2/3 |
| archaeology burden | heavy | 0/3 |
| coupling centrality | highly central | 0/3 |
| test alignment | drifting | 2/3 |
| documentation coherence | patchy | 2/3 |

## Subsystem verdicts

| Subsystem | Verdict | Owner | Test alignment |
| --- | --- | --- | --- |
| prompt contracts | red | game/prompt_context.py | partial |
| response policy contracts | red | game/response_policy_contracts.py | partial |
| final emission validators | yellow | game/final_emission_validators.py | partial |
| final emission repairs | red | game/final_emission_repairs.py | partial |
| final emission gate orchestration | red | game/final_emission_gate.py | partial |
| narrative authenticity | red | game/narrative_authenticity.py | partial |
| stage diff telemetry | yellow | game/stage_diff_telemetry.py | partial |
| test ownership / inventory docs | yellow | unknown | partial |

## Strongest evidence that the architecture is real

- `final emission gate orchestration` still resolves to `game/final_emission_gate.py` (high ownership confidence; test alignment `partial`).
- `final emission repairs` still resolves to `game/final_emission_repairs.py` (high ownership confidence; test alignment `partial`).
- `final emission validators` still resolves to `game/final_emission_validators.py` (high ownership confidence; test alignment `partial`).

## Strongest evidence that the architecture may be patch-accumulating

- `final emission gate orchestration` is `partial` with practical tests centered in `mixed: tests/test_final_emission_gate.py, tests/test_final_emission_scene_integrity.py, tests/test_final_emission_visibility.py`; evidence: Coverage is spread across many homes rather than anchored in one direct owner suite.
- `prompt contracts` is `partial` with practical tests centered in `mixed: tests/test_prompt_context.py, tests/test_social_escalation.py, tests/test_social_interaction_authority.py`; evidence: Coverage is spread across many homes rather than anchored in one direct owner suite.

## Known ambiguity hotspots

- `prompt contracts conflict` -> localized under-consolidation; Coverage is spread across many homes rather than anchored in one direct owner suite.
- `response policy contracts localized residue` -> localized under-consolidation; Coverage is spread across many homes rather than anchored in one direct owner suite.
- `final emission gate orchestration partial mismatch` -> localized under-consolidation; Coverage is spread across many homes rather than anchored in one direct owner suite.
- `stage diff telemetry partial mismatch` -> localized under-consolidation; Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `test ownership / inventory docs still unclear` -> localized under-consolidation; No related test file accumulated enough concern-specific affinity.
- `prompt_context_leads residue` -> transitional residue; Coverage is spread across many homes rather than anchored in one direct owner suite.
- `turn_packet telemetry adjacency residue` -> transitional residue; Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `social_exchange_emission mixed repair/contract role` -> transitional residue; Coverage is spread across many homes rather than anchored in one direct owner suite.

## Runtime/test/doc mismatch review

- `final emission gate orchestration` -> runtime `game/final_emission_gate.py` vs practical `mixed: tests/test_final_emission_gate.py, tests/test_final_emission_scene_integrity.py, tests/test_final_emission_visibility.py` (partial; high; spread 10); evidence: Coverage is spread across many homes rather than anchored in one direct owner suite.
- `prompt contracts` -> runtime `game/prompt_context.py` vs practical `mixed: tests/test_prompt_context.py, tests/test_social_escalation.py, tests/test_social_interaction_authority.py` (partial; high; spread 10); evidence: Coverage is spread across many homes rather than anchored in one direct owner suite.
- `response policy contracts` -> runtime `game/response_policy_contracts.py` vs practical `mixed: tests/test_response_policy_contracts.py, tests/test_interaction_continuity_contract.py, tests/test_interaction_continuity_validation.py` (partial; high; spread 6); evidence: Coverage is spread across many homes rather than anchored in one direct owner suite.
- `stage diff telemetry` -> runtime `game/stage_diff_telemetry.py` vs practical `mixed: tests/test_turn_packet_stage_diff_integration.py, tests/test_stage_diff_telemetry.py, tests/test_narrative_authenticity_aer4.py` (partial; high; spread 4); evidence: Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `test ownership / inventory docs` -> runtime `unknown` vs practical `unknown` (partial; high; spread 0); evidence: No related test file accumulated enough concern-specific affinity.

## Transcript-lock vs contract-lock risk summary

- Transcript locks look secondary to direct owner tests in this pass.

## Manual spot-check list

- `test ownership / inventory docs` -> runtime `unknown`, practical `unknown` (partial; high)
- `response policy contracts` -> runtime `game/response_policy_contracts.py`, practical `mixed: tests/test_response_policy_contracts.py, tests/test_interaction_continuity_contract.py, tests/test_interaction_continuity_validation.py` (partial; high)
- `prompt contracts` -> runtime `game/prompt_context.py`, practical `mixed: tests/test_prompt_context.py, tests/test_social_escalation.py, tests/test_social_interaction_authority.py` (partial; high)
- `stage diff telemetry` -> runtime `game/stage_diff_telemetry.py`, practical `mixed: tests/test_turn_packet_stage_diff_integration.py, tests/test_stage_diff_telemetry.py, tests/test_narrative_authenticity_aer4.py` (partial; high)
- `final emission gate orchestration` -> runtime `game/final_emission_gate.py`, practical `mixed: tests/test_final_emission_gate.py, tests/test_final_emission_scene_integrity.py, tests/test_final_emission_visibility.py` (partial; high)

## Cleanup-only opportunities

- Keep `game/response_policy_contracts.py` as the runtime owner and `tests/test_response_policy_contracts.py` as the direct-owner suite; treat remaining downstream usage as compatibility/adjacency residue only.
- Thin the `final_emission_gate` vs `final_emission_meta` overlap so orchestration remains primary and metadata packaging stays secondary.
- Tighten tests/docs so `game/stage_diff_telemetry.py` stays the telemetry owner while `game.turn_packet.py` remains the packet-boundary owner.
- Convert `game/prompt_context_leads.py` from residue wording into a clearly subordinate helper or document it as retired sediment only.
- Continue trimming compatibility wrappers/import paths so telemetry derives from `game.turn_packet.py` without implying a second packet owner.

## Stop-before-feature warnings

- No stop-before-feature warnings were triggered by the current rubric.

## Schema notes

- subsystem_reports now include inferred_owner, ownership_confidence, owner_evidence, role_labels, ownership_findings, overlap_findings, coupling_indicators, and archaeology_markers.
- modules_analyzed.files now surface ownership role_labels and ownership_confidence for runtime focus modules.
- Overlap findings are heuristic triage signals, not proof of semantic duplication or the true canonical owner.
- subsystem_reports now include test_ownership_alignment with runtime/doc/test reconciliation fields.
- tests_analyzed now includes deterministic file/test category counts and per-file inferred categories.
- summary now includes top_test_runtime_doc_mismatches, concerns_with_widest_test_ownership_spread, likely_transcript_lock_seams, likely_contract_owned_seams_with_weak_direct_tests, inventory_docs_authority_status, and manual_review_shortlist.
- summary now includes ownership_declaration_consistency for ledger-vs-module declaration checks.
