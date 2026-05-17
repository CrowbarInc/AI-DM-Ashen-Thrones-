# Cycle D Sealed Fallback Contraction Closure

Date: 2026-05-13

## Executive summary

Cycle D sealed fallback contraction is complete for this cycle. The work reduced pressure in
`game/final_emission_gate.py` by isolating sealed fallback metadata stamping, owner telemetry,
selector mechanics, typed selection data, and non-strict assembly ordering while preserving gate
ownership of prose providers, output writes, tag/debug mutation, branch order, and route/FEM
orchestration.

No emitted prose was intentionally changed. Fallback source values, fallback family values, route
behavior, and `sealed_fallback_owner_bucket` values were preserved by focused tests.

## Files changed across Cycle D

- `game/final_emission_sealed_fallback.py`
- `game/final_emission_gate.py`
- `game/final_emission_meta.py`
- `game/diegetic_fallback_narration.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/failure_classification_contract.py`
- `tests/test_final_emission_gate.py`
- `tests/test_golden_replay.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_failure_classification_contract.py`

## Extracted helpers

`game/final_emission_sealed_fallback.py` now owns sealed fallback helper mechanics that do not
author fallback prose:

- `stamp_sealed_fallback_realization_family`
- `prepare_sealed_replacement_route_meta`
- `finalize_n4_sealed_replace_fem_route_meta`
- `select_acceptance_quality_n4_sealed_fallback_line`
- `select_non_strict_replace_path_terminal_sealed_fallback_branch`
- `assemble_non_strict_sealed_fallback_selection`

The N4 selector uses injected prose builders. The non-strict assembler chooses among provided
candidate providers and does not contain fallback prose literals.

## Telemetry added

Added supplemental sealed fallback ownership evidence:

- Field: `sealed_fallback_owner_bucket`
- Values:
  - `sealed-gate`
  - `strict-social-sealed`
  - `unknown-none`
  - `unknown-ambiguous`

Projection and evidence surfaces now include this field:

- golden replay observed rows
- failure classifier rows and validation contract
- failure dashboard compact evidence as `sealed_owner=...`

This telemetry is additive. It does not replace `realization_fallback_family`.

## Typed result shape

Added `SealedFallbackSelection` in `game/final_emission_sealed_fallback.py`.

Fields:

- `text`
- `fallback_pool`
- `fallback_kind`
- `final_emitted_source`
- `composition_meta`

Adapters:

- `from_legacy_tuple`
- `as_legacy_tuple`

The legacy private gate wrapper still returns the historical tuple shape for compatibility.

## Provider ownership status

Fallback prose providers remain owned outside the sealed helper assembler.

`game/final_emission_gate.py` still builds gate-side provider closures for:

- opening fallback tuple selection
- active-social-interlocutor minimal fallback
- passive scene pressure candidates
- neutral NPC-pursuit nonprogress fallback
- anti-reset local continuation fallback
- global scene-integrity fallback tuple

The local neutral nonprogress prose literal was assigned to `game/diegetic_fallback_narration.py`:

- `NPC_PURSUIT_NEUTRAL_NONPROGRESS_FALLBACK_LINE`
- `npc_pursuit_neutral_nonprogress_fallback_line`

The exact text was preserved.

## Remaining gate responsibilities

`game/final_emission_gate.py` remains responsible for:

- orchestration and branch context
- building prose provider closures
- calling prose-owner functions
- `out["player_facing_text"]` writes
- tag/debug mutation
- route/FEM stamping and merge order
- compatibility private aliases/wrappers
- final output packaging

This keeps prose ownership and runtime output mutation explicit at the gate boundary.

## Behavior confirmation

Cycle D did not intentionally change:

- emitted player-facing text
- fallback prose
- fallback selector branch order
- fallback source values
- fallback family values
- route behavior
- `sealed_fallback_owner_bucket` values
- `out["player_facing_text"]` write ownership

## Final verification

Command:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_final_emission_gate.py tests\test_final_emission_visibility.py tests\test_golden_replay.py tests\test_failure_classifier.py tests\test_failure_dashboard_controlled_failures.py tests\test_failure_classification_contract.py -q --tb=short --basetemp=codex_pytest_tmp_d8
```

Result: passed.

## Remaining risks

Sealed fallback contraction is complete for this cycle. Further extraction should wait unless there
is a separate design decision about moving provider ownership out of `game/final_emission_gate.py`.

The main residual risk is over-extracting prose-provider ownership before there is a clear owner
contract for each fallback family. The current boundary is intentionally conservative: the sealed
helper module selects among providers; the gate still wires providers and writes output.

## Recommended next cluster

Candidate clusters:

- Visibility fallback: likely the cleanest next target because visibility replacement already has
  crisp route markers and appears more mechanical than strict-social fallback.
- Opening fallback: important, but more recently churned and has upstream-prepared authorship
  subtleties.
- Strict-social fallback: high value, but more coupled to social route legality, speaker ownership,
  and sanitizer/prose ownership splits.

Recommendation: take visibility fallback next, assuming local inventory confirms fewer prose-owner
ambiguities than strict-social and less recent churn than opening fallback.
