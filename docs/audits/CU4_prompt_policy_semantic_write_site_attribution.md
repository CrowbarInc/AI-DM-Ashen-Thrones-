# CU4 Prompt & Policy Semantic Write-Site Attribution

## Producer Surfaces Instrumented

- `game.response_policy_enforcement`: policy-family write-site evidence is recorded around active output-changing policy passes. No record is emitted when a policy evaluates without changing `player_facing_text`.
- `game.upstream_response_repairs`: upstream prepared response payload construction records candidate-only repair evidence. Spoken state refinement cash-out records prompt-family evidence when prompt/contract-derived pre-gate processing appends player-facing semantic content.
- `game.final_emission_response_type`: upstream prepared answer/action selection records selected active-stream repair evidence when prepared text is chosen into emission.
- `game.final_emission_meta` and `game.final_emission_gate_preflight_defaults`: prompt/policy/upstream write-site records are carried from early metadata surfaces into FEM diagnostics.
- `tests/helpers/golden_replay_projection.py`: replay projection exposes optional `first_prompt_write`, `first_policy_write`, authoritative owner, and authoritative evidence source diagnostics without adding protected fields.

## Candidate vs Selected Rules

- Candidate creation uses `selected_active_stream=false` and `candidate_only=true`.
- Candidate selection into emitted processing uses `selected_active_stream=true` and `candidate_only=false`.
- Candidate-only records are preserved diagnostically but ignored by authoritative reconciliation.
- Selected prompt and policy records participate normally once `selected_active_stream=true`.

## Reconciliation Changes

- Allowed write-site families now include `prompt` and `policy` alongside `sanitizer`, `repair`, `fallback`, and `final_emission`.
- `game.semantic_mutation_attribution` ignores records unless they are selected active-stream evidence.
- Existing precedence is unchanged: explicit write-site evidence still outranks runtime lineage, fallback provenance, sanitizer lineage, FEM mutation lineage, stage diff, and projection inference.

## Examples

- Policy rewrite: validator voice removal records `write_site_family=policy`, source `diegetic_only.no_validator_voice`, and owner `game.response_policy_enforcement`.
- Policy no-op: valid diegetic output records no policy write site.
- Prompt semantic transformation: spoken state refinement cash-out records `write_site_family=prompt` with owner `game.upstream_response_repairs`.
- Upstream prepared response: payload creation records candidate-only repair evidence; response-type selection records active selected repair evidence.

## Compatibility Notes

- Runtime prompt behavior, policy logic, and emitted text are unchanged.
- Replay protected schemas are unchanged; new projection fields are optional diagnostics only.
- Candidate-only records remain visible for debugging but cannot become authoritative.
- Early records are copied through emission debug / FEM merge paths so downstream projection does not need to infer ownership from later sanitizer/fallback evidence.

## Tests Executed

- `tests/test_semantic_mutation_attribution_cu4.py`
- `tests/test_golden_replay_projection_semantic.py`
- `tests/test_response_policy_contracts.py`
- `tests/test_upstream_response_repairs.py`
- `tests/test_failure_classifier.py`
- Narrow final-emission-meta write-site coverage:
  `tests/test_final_emission_meta.py -k semantic_mutation_write_site`
- Targeted combined rerun:
  `-k "cu4 or cu3 or semantic_mutation_write_site or upstream_prepared or response_policy_accessors or final_gate_upstream_prepared"`

Observed unrelated pre-existing failure when running the broader `tests/test_final_emission_meta.py` file: `test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only` reports a raw `compatibility_local_opening_deterministic` token in `tests/test_fallback_incidence_report.py`.

## Remaining Inference-Only Situations

- Legacy payloads without `semantic_mutation_write_sites` still fall back to runtime lineage, sanitizer lineage, FEM mutation lineage, stage diff, or projection-derived inference.
- Policy branches that only mutate state updates, tags, debug notes, or metadata remain intentionally unrecorded unless player-facing semantic text changes.
- Prompt assembly that only ships context, contracts, or non-public debug data remains intentionally unrecorded.

## Remaining Work Before Governance Promotion

- Decide whether prompt-family ownership should be split further between prompt-contract assembly and upstream response preparation in a promoted schema.
- Promote optional diagnostics only after replay governance accepts field names and compatibility expectations.
- Expand corpus coverage only if future governance requires observed end-to-end replay examples for prompt/policy families.
