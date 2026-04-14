# Architecture Audit

## Executive verdict

- Repo-level verdict: **mixed / caution**
- Confidence: **medium**
- Recommended action mode: **needs targeted ownership cleanup before more features**
- Legacy subsystem roll-up color: **red**
- Modules analyzed: **86**
- Docs analyzed: **18**
- Test files analyzed: **185**

- Repo-level verdict: **mixed / caution** with scorecard total 9/18.
- Action mode: **needs targeted ownership cleanup before more features**.
- Hotspot mix: 3 localized, 1 transitional, 3 possible smear, 1 unclear.

## Repo-level scorecard

| Dimension | Status | Points |
| --- | --- | ---: |
| ownership clarity | clear | 3/3 |
| overlap severity | localized hotspots | 2/3 |
| archaeology burden | moderate | 2/3 |
| coupling centrality | highly central | 0/3 |
| test alignment | drifting | 2/3 |
| documentation coherence | weak | 0/3 |

## Subsystem verdicts

| Subsystem | Verdict | Owner | Test alignment |
| --- | --- | --- | --- |
| prompt contracts | red | game/prompt_context.py | conflict |
| response policy contracts | red | game/final_emission_repairs.py | partial |
| final emission validators | yellow | game/final_emission_validators.py | partial |
| final emission repairs | red | game/final_emission_repairs.py | partial |
| final emission gate orchestration | red | game/final_emission_gate.py | partial |
| narrative authenticity | red | game/narrative_authenticity.py | partial |
| stage diff telemetry | yellow | game/stage_diff_telemetry.py | partial |
| test ownership / inventory docs | red | unknown | unclear |

## Strongest evidence that the architecture is real

- `final emission gate orchestration` still resolves to `game/final_emission_gate.py` (high ownership confidence; test alignment `partial`).
- `final emission repairs` still resolves to `game/final_emission_repairs.py` (high ownership confidence; test alignment `partial`).
- `final emission validators` still resolves to `game/final_emission_validators.py` (high ownership confidence; test alignment `partial`).

## Strongest evidence that the architecture may be patch-accumulating

- `prompt contracts` is `conflict` with practical tests centered in `mixed: tests/test_response_delta_requirement.py, tests/test_opening_visible_fact_selection.py, tests/test_prompt_context.py`; evidence: Transcript-style tests dominate a concern that looks contract-owned at runtime.
- `response policy contracts` is `partial` with practical tests centered in `mixed: tests/test_fallback_behavior_repairs.py, tests/test_bounded_partial_quality.py, tests/test_final_emission_validators.py`; evidence: Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- 4 hotspot(s) still look like ownership-smear or unclear-review candidates, led by `prompt contracts conflict`.
- Documentation coherence is still weak enough to add uncertainty: 18 broken reference(s).

## Known ambiguity hotspots

- `prompt contracts conflict` -> possible ownership smear; Transcript-style tests dominate a concern that looks contract-owned at runtime.
- `response policy contracts partial drift toward repairs` -> localized under-consolidation; Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `final emission gate orchestration partial mismatch` -> localized under-consolidation; Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `stage diff telemetry partial mismatch` -> localized under-consolidation; Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `test ownership / inventory docs still unclear` -> unclear / needs human review; No related test file accumulated enough concern-specific affinity.
- `prompt_context_leads residue` -> transitional residue; Transcript-style tests dominate a concern that looks contract-owned at runtime.
- `turn_packet mixed contract/telemetry role` -> possible ownership smear; Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `social_exchange_emission mixed repair/contract role` -> possible ownership smear; Docs name a canonical test owner, but practical coverage concentrates elsewhere.

## Runtime/test/doc mismatch review

- `prompt contracts` -> runtime `game/prompt_context.py` vs practical `mixed: tests/test_response_delta_requirement.py, tests/test_opening_visible_fact_selection.py, tests/test_prompt_context.py` (conflict; high; spread 9); evidence: Transcript-style tests dominate a concern that looks contract-owned at runtime.
- `response policy contracts` -> runtime `game/final_emission_repairs.py` vs practical `mixed: tests/test_fallback_behavior_repairs.py, tests/test_bounded_partial_quality.py, tests/test_final_emission_validators.py` (partial; high; spread 9); evidence: Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `final emission gate orchestration` -> runtime `game/final_emission_gate.py` vs practical `mixed: tests/test_final_emission_meta.py, tests/test_final_emission_gate.py` (partial; high; spread 8); evidence: Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `stage diff telemetry` -> runtime `game/stage_diff_telemetry.py` vs practical `mixed: tests/test_turn_packet_stage_diff_integration.py, tests/test_stage_diff_telemetry.py, tests/test_narrative_authenticity_aer4.py` (partial; high; spread 5); evidence: Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- `test ownership / inventory docs` -> runtime `unknown` vs practical `unknown` (unclear; high; spread 0); evidence: No related test file accumulated enough concern-specific affinity.

## Transcript-lock vs contract-lock risk summary

- Transcript-style protection is starting to compete with direct contract-owner tests.
- Transcript-heavy seam: `final emission gate orchestration` -> Docs name a canonical test owner, but practical coverage concentrates elsewhere.
- Transcript-heavy seam: `prompt contracts` -> Transcript-style tests dominate a concern that looks contract-owned at runtime.
- Transcript-heavy seam: `stage diff telemetry` -> Docs name a canonical test owner, but practical coverage concentrates elsewhere.

## Manual spot-check list

- `test ownership / inventory docs` -> runtime `unknown`, practical `unknown` (unclear; high)
- `response policy contracts` -> runtime `game/final_emission_repairs.py`, practical `mixed: tests/test_fallback_behavior_repairs.py, tests/test_bounded_partial_quality.py, tests/test_final_emission_validators.py` (partial; high)
- `prompt contracts` -> runtime `game/prompt_context.py`, practical `mixed: tests/test_response_delta_requirement.py, tests/test_opening_visible_fact_selection.py, tests/test_prompt_context.py` (conflict; high)
- `stage diff telemetry` -> runtime `game/stage_diff_telemetry.py`, practical `mixed: tests/test_turn_packet_stage_diff_integration.py, tests/test_stage_diff_telemetry.py, tests/test_narrative_authenticity_aer4.py` (partial; high)
- `final emission gate orchestration` -> runtime `game/final_emission_gate.py`, practical `mixed: tests/test_final_emission_meta.py, tests/test_final_emission_gate.py` (partial; high)

## Cleanup-only opportunities

- Re-anchor response-policy ownership between `game/response_policy_contracts.py` and `game/final_emission_repairs.py`, then relink the canonical test/doc home to that choice.
- Thin the `final_emission_gate` vs `final_emission_meta` overlap so orchestration remains primary and metadata packaging stays secondary.
- Re-state whether `game/stage_diff_telemetry.py` or `game/turn_packet.py` owns the contract boundary, then tighten tests to that owner.
- Convert `game/prompt_context_leads.py` from residue wording into a clearly subordinate helper or document it as retired sediment only.

## Stop-before-feature warnings

- Stop before adding new prompt-contract obligations until `game/prompt_context.py`, `game/prompt_context_leads.py`, and `game/response_policy_contracts.py` stop co-presenting as owners.
- Stop before treating inventory docs as canonical governance while practical test ownership remains unclear.
- Stop before growing telemetry-dependent features until `game/turn_packet.py` stops carrying both packet-contract and telemetry-home signals.
- Stop before adding more social-emission repair behavior until `game/social_exchange_emission.py` is either a contract owner or a repair consumer, not both.

## Schema notes

- subsystem_reports now include inferred_owner, ownership_confidence, owner_evidence, role_labels, ownership_findings, overlap_findings, coupling_indicators, and archaeology_markers.
- modules_analyzed.files now surface ownership role_labels and ownership_confidence for runtime focus modules.
- Overlap findings are heuristic triage signals, not proof of semantic duplication or the true canonical owner.
- subsystem_reports now include test_ownership_alignment with runtime/doc/test reconciliation fields.
- tests_analyzed now includes deterministic file/test category counts and per-file inferred categories.
- summary now includes top_test_runtime_doc_mismatches, concerns_with_widest_test_ownership_spread, likely_transcript_lock_seams, likely_contract_owned_seams_with_weak_direct_tests, inventory_docs_authority_status, and manual_review_shortlist.
