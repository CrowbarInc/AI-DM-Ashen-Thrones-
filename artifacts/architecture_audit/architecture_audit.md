# Architecture Audit

## Executive verdict

- Repo-level verdict: **mixed / caution**
- Confidence: **medium**
- Recommended action mode: **needs targeted ownership cleanup before more features**
- Legacy subsystem roll-up color: **red**
- Modules analyzed: **86**
- Docs analyzed: **20**
- Test files analyzed: **186**

- Repo-level verdict: **mixed / caution** with scorecard total 10/18.
- Action mode: **needs targeted ownership cleanup before more features**.
- Hotspot mix: 4 localized, 4 transitional, 0 possible smear, 0 unclear.

## Repo-level scorecard

| Dimension | Status | Points |
| --- | --- | ---: |
| ownership clarity | clear | 3/3 |
| overlap severity | localized hotspots | 2/3 |
| archaeology burden | heavy | 0/3 |
| coupling centrality | highly central | 0/3 |
| test alignment | aligned | 3/3 |
| documentation coherence | patchy | 2/3 |

## Subsystem verdicts

| Subsystem | Verdict | Owner | Test alignment |
| --- | --- | --- | --- |
| prompt contracts | red | game/prompt_context.py | aligned |
| response policy contracts | red | game/response_policy_contracts.py | aligned |
| final emission validators | yellow | game/final_emission_validators.py | partial |
| final emission repairs | red | game/final_emission_repairs.py | partial |
| final emission gate orchestration | red | game/final_emission_gate.py | aligned |
| narrative authenticity | red | game/narrative_authenticity.py | partial |
| stage diff telemetry | yellow | game/stage_diff_telemetry.py | aligned |
| test ownership / inventory docs | yellow | unknown | partial |

## Strongest evidence that the architecture is real

- `final emission gate orchestration` still resolves to `game/final_emission_gate.py` (high ownership confidence; test alignment `aligned`).
- `prompt contracts` still resolves to `game/prompt_context.py` (high ownership confidence; test alignment `aligned`).
- `response policy contracts` still resolves to `game/response_policy_contracts.py` (high ownership confidence; test alignment `aligned`).

## Strongest evidence that the architecture may be patch-accumulating

- `test ownership / inventory docs` is `partial` with practical tests centered in `unknown`; evidence: No related test file accumulated enough concern-specific affinity.
- `final emission repairs` is `partial` with practical tests centered in `tests/test_final_emission_repairs.py`; evidence: Docs name a canonical test owner, but practical coverage concentrates elsewhere.

## Known ambiguity hotspots

- `prompt contracts conflict` -> localized under-consolidation; primary home `tests/test_prompt_context.py` (integration / layer interaction; score 10.0)
- `response policy contracts localized residue` -> transitional residue; primary home `tests/test_response_policy_contracts.py` (integration / layer interaction; score 12.0)
- `final emission gate orchestration partial mismatch` -> localized under-consolidation; primary home `tests/test_final_emission_gate.py` (integration / layer interaction; score 12.0)
- `stage diff telemetry partial mismatch` -> localized under-consolidation; primary home `tests/test_stage_diff_telemetry.py` (integration / layer interaction; score 10.0)
- `test ownership / inventory docs still unclear` -> localized under-consolidation; No related test file accumulated enough concern-specific affinity.
- `prompt_context_leads residue` -> transitional residue; primary home `tests/test_prompt_context.py` (integration / layer interaction; score 10.0)
- `turn_packet telemetry adjacency residue` -> transitional residue; primary home `tests/test_stage_diff_telemetry.py` (integration / layer interaction; score 10.0)
- `social_exchange_emission mixed repair/contract role` -> transitional residue; primary home `tests/test_final_emission_gate.py` (integration / layer interaction; score 12.0)

## Runtime/test/doc mismatch review

- `test ownership / inventory docs` -> runtime `unknown` vs practical `unknown` (partial; high; spread 0); evidence: No related test file accumulated enough concern-specific affinity.
- `final emission repairs` -> runtime `game/final_emission_repairs.py` vs practical `tests/test_final_emission_repairs.py` (partial; medium; spread 7); evidence: Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `final emission validators` -> runtime `game/final_emission_validators.py` vs practical `mixed: tests/test_final_emission_repairs.py, tests/test_final_emission_validators.py` (partial; medium; spread 7); evidence: Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `narrative authenticity` -> runtime `game/narrative_authenticity.py` vs practical `mixed: tests/test_narrative_authenticity.py, tests/test_narrative_authenticity_aer4.py, tests/test_narrative_authenticity_aer5.py` (partial; medium; spread 4); evidence: Docs name a canonical test owner, but practical coverage concentrates elsewhere.

## Transcript-lock vs contract-lock risk summary

- Transcript locks look secondary to direct owner tests in this pass.

## Manual spot-check list

- `test ownership / inventory docs` -> runtime `unknown`, practical `unknown` (partial; high)
- `response policy contracts` -> runtime `game/response_policy_contracts.py`, practical `tests/test_response_policy_contracts.py` (aligned; low)
- `prompt contracts` -> runtime `game/prompt_context.py`, practical `tests/test_prompt_context.py` (aligned; low)
- `stage diff telemetry` -> runtime `game/stage_diff_telemetry.py`, practical `mixed: tests/test_stage_diff_telemetry.py, tests/test_turn_packet_stage_diff_integration.py` (aligned; low)
- `final emission gate orchestration` -> runtime `game/final_emission_gate.py`, practical `tests/test_final_emission_gate.py` (aligned; low)

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
