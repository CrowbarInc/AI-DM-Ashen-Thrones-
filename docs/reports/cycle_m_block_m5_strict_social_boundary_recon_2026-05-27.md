# Cycle M Block M5 - Strict-Social Boundary Recon

Date: 2026-05-27

Scope: map strict-social ownership boundaries before any future extraction. Report-only; no runtime behavior changes.

Recommendation: defer implementation. The current strict-social surfaces are mostly well-owned, and the unclear pieces are integration-heavy enough that extraction should wait for a dedicated, test-backed block.

## Current Owner Map

| Surface | Current owner | Role |
| --- | --- | --- |
| Strict-social emitted prose and downstream exchange emission | `game/social_exchange_emission.py` | Owns strict-social routing checks, speaker grounding, candidate normalization, sentence ownership enforcement, deterministic social fallback lines, and `build_final_strict_social_response()`. |
| Terminal emergency fallback prose | `game/social_exchange_emission.py` | Owns `minimal_social_emergency_fallback_line()`, `lawful_strict_social_dialogue_emergency_fallback_line()`, `strict_social_terminal_dialogue_fallback_valid()`, `apply_strict_social_terminal_dialogue_fallback_if_needed()`, and `strict_social_ownership_terminal_fallback()`. |
| Answer-pressure cash-out | `game/upstream_response_repairs.py` | Owns `apply_spoken_state_refinement_cash_out()` and the strict-social answer-pressure contract probes used to decide whether promoted lead/clue refinement should be appended before final emission. |
| Final-emission repair layers | `game/final_emission_repairs.py` | Owns validation/repair layer plumbing and skip decisions. It explicitly does not author answer/action fallback prose or spoken cash-out text. |
| Strict-social local referential repair | `game/final_emission_gate.py` | Owns the gate-local pronoun substitution path for strict-social dialogue after referential clarity validation, via `_try_strict_social_local_pronoun_substitution_repair()` and `_apply_referential_clarity_enforcement()`. |
| Anti-reset local continuation fallback | `game/anti_reset_emission_guard.py` | Owns detection of established local exchanges and local continuation fallback text. It may reuse `minimal_social_emergency_fallback_line()` when a strict-social effective resolution exists. |
| Gate integration | `game/final_emission_gate.py` | Legitimately orchestrates strict-social application, response-type enforcement, final source attribution, final-emission metadata, visibility/first-mention/referential clarity integration, NMO/AQ floor checks, and fallback stamping. |

## Test Ownership Map

| Test file | Current responsibility |
| --- | --- |
| `tests/test_social_exchange_emission.py` | Primary owner for downstream strict-social exchange emission and terminal dialogue application semantics. |
| `tests/test_strict_social_emergency_fallback_dialogue.py` | Secondary downstream coverage for retry-exhaustion wiring, first-mention gate integration, and compatibility alias behavior. |
| `tests/test_strict_social_answer_pressure_cashout.py` | Owns strict-social answer-pressure cash-out behavior and AC/RD skip interactions around that path. |
| `tests/test_referential_clarity_strict_social_local_repair.py` | Owns strict-social local pronoun substitution behavior and fallback-after-failed-local-repair cases. |
| `tests/test_final_emission_gate.py` | Owns gate integration, final routing, metadata attachment, mutation taxonomy, and final-emission orchestration checks. |

## Duplicated Or Unclear Boundaries

### Terminal Emergency Fallback

`game/social_exchange_emission.py` contains several closely related terminal fallback helpers:

- `minimal_social_emergency_fallback_line()`
- `lawful_strict_social_dialogue_emergency_fallback_line()`
- `strict_social_ownership_terminal_fallback()`
- `deterministic_social_fallback_line()`
- `social_fallback_line_for_sanitizer()`

This is a dense but coherent ownership cluster. The duplication is mostly overlapping deterministic line pools, not duplicated gate policy. A future extraction could centralize the small terminal-line registry, but doing it now risks changing emitted prose or deterministic selection.

### Gate-Local Strict-Social Referential Repair

`game/final_emission_gate.py` owns `_strict_social_answer_payload_signals()`, `_strict_social_dialogue_substantive_for_local_ref_repair()`, `_strict_social_terminal_grounded_speaker_first_mention_exemption_entity_id()`, `_grounded_speaker_phrase_for_pronoun_substitution()`, and `_try_strict_social_local_pronoun_substitution_repair()`.

This boundary is the least clean. The code is gate-local because it depends on final gate metadata, visibility/referential clarity validation, active interlocutor state, first-mention exemption, and mutation logging. It is a candidate for future extraction only as a small helper module that remains gate-owned, not as social prose ownership in `social_exchange_emission.py`.

### Strict-Social Answer-Pressure Contract Probes

Strict-social answer-pressure probes exist in both:

- `game/final_emission_repairs.py`: `_strict_social_answer_pressure_ac_contract_active()` and `_strict_social_answer_pressure_rd_contract_active()`
- `game/upstream_response_repairs.py`: `_strict_social_answer_pressure_ac_contract_active_upstream()` and `_strict_social_answer_pressure_rd_contract_active_upstream()`

These are near-duplicate read-side contract checks. Their consumers differ: final-emission repairs use them for skip decisions, upstream response repairs use them for pre-gate spoken cash-out. This is the clearest future low-risk extraction candidate if a tiny shared read helper can be introduced without changing text or policy.

### Anti-Reset Strict-Social Reuse

`game/anti_reset_emission_guard.py` uses `effective_strict_social_resolution_for_emission()` and `minimal_social_emergency_fallback_line()` to produce local exchange continuation text when a strict-social effective resolution exists. This is legitimate reuse of strict-social prose, but it means terminal fallback text is consumed outside `social_exchange_emission.py`.

### Gate Integration That Should Stay In Gate

The following pieces are legitimate gate integration, not duplication:

- Calling `build_final_strict_social_response()`.
- Running response-type enforcement after strict-social composition.
- Replacing failed strict-social response-type/NMO output with `minimal_social_emergency_fallback_line()`.
- Applying final-emission repair layers with `strict_social_path=True`.
- Applying visibility, first-mention, referential clarity, interaction-continuity, NMO, and AQ checks.
- Updating `_final_emission_meta`, `final_emitted_source`, tags, debug notes, and runtime lineage surfaces.

## Future Extraction Candidates

### Candidate 1: Strict-Social Answer-Pressure Contract Probe Helper

Goal: remove duplicated AC/RD answer-pressure probe logic.

Likely future files:

- `game/response_policy_contracts.py` or a small adjacent read-side helper module
- `game/final_emission_repairs.py`
- `game/upstream_response_repairs.py`
- `tests/test_strict_social_answer_pressure_cashout.py`

Risk: low to medium. The logic is read-side, but a mistake could alter whether cash-out or repair-layer skips occur.

Recommendation: implement later only if another answer-pressure fix touches both files.

### Candidate 2: Gate-Owned Strict-Social Referential Repair Helper

Goal: move the local-pronoun-substitution cluster out of the large gate file while keeping gate semantics unchanged.

Likely future files:

- `game/final_emission_gate.py`
- New `game/final_emission_strict_social_referential_repair.py` or similarly narrow gate-adjacent module
- `tests/test_referential_clarity_strict_social_local_repair.py`
- `tests/test_final_emission_gate.py`

Risk: medium. This cluster depends on active interlocutor, visibility, first-mention grounding, metadata mutation, and fallback-after-failed-local-repair behavior.

Recommendation: defer until the gate extraction plan is ready.

### Candidate 3: Terminal Strict-Social Fallback Line Registry

Goal: centralize deterministic terminal fallback line pools and source IDs.

Likely future files:

- `game/social_exchange_emission.py`
- Possibly new `game/strict_social_terminal_fallbacks.py`
- `game/anti_reset_emission_guard.py`
- `tests/test_social_exchange_emission.py`
- `tests/test_strict_social_emergency_fallback_dialogue.py`
- `tests/test_final_emission_gate.py`

Risk: medium to high. Even small edits could alter emitted prose, deterministic selection, sanitizer rescue behavior, or emergency fallback validity.

Recommendation: no-op for Cycle M unless a future change must touch multiple terminal fallback helpers.

## Risks

- Moving strict-social prose helpers out of `game/social_exchange_emission.py` could blur the current downstream emission ownership boundary.
- Moving local referential repair too early could separate metadata mutation from the gate state it depends on.
- Centralizing terminal fallback text may accidentally change emitted prose or deterministic seed behavior.
- Treating answer-pressure cash-out as final-emission repair would undo the current ownership boundary: upstream packaging owns cash-out, the gate consumes it.
- Some duplication is deliberate compatibility residue, especially repair-shaped aliases that tests still lock.

## Recommendation

Defer implementation. Do not extract gate logic in M5.

The only near-term candidate worth considering is a tiny read-side helper for strict-social answer-pressure AC/RD contract probes. Even that should wait until a concrete edit needs it, because the current duplication is small and covered by focused tests.

No production or test characterization gap was found that requires immediate test additions. Existing tests already lock:

- strict-social exchange emission and terminal fallback semantics;
- retry/emergency dialogue wiring;
- answer-pressure cash-out;
- local referential repair;
- gate integration, routing, and metadata.

## Exact Files For Future Implementation

If consolidating answer-pressure contract probes:

- `game/response_policy_contracts.py` or a new narrow read helper
- `game/final_emission_repairs.py`
- `game/upstream_response_repairs.py`
- `tests/test_strict_social_answer_pressure_cashout.py`
- `tests/test_final_emission_gate.py`

If extracting gate-owned strict-social referential repair:

- `game/final_emission_gate.py`
- New `game/final_emission_strict_social_referential_repair.py`
- `tests/test_referential_clarity_strict_social_local_repair.py`
- `tests/test_final_emission_gate.py`

If consolidating terminal strict-social fallback line pools:

- `game/social_exchange_emission.py`
- Optional new `game/strict_social_terminal_fallbacks.py`
- `game/anti_reset_emission_guard.py`
- `tests/test_social_exchange_emission.py`
- `tests/test_strict_social_emergency_fallback_dialogue.py`
- `tests/test_final_emission_gate.py`

## Validation

Report-only block. No code or test files were changed, so no test run is required by the M5 validation rule.
