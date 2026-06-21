# BV14 — Usage Classification

**Date:** 2026-06-21

---

## Consumer groups (BV14 taxonomy)

| Usage class | Tag assignments | Share | Typical symbols |
| --- | --- | --- | --- |
| **tests** | 25 | 31% | module monkeypatch + legality owner suite |
| **strict-social pipeline** | 23 | 29% | `build_final_strict_social_response`, `effective_strict_social_resolution_for_emission` |
| **terminal emission** | 16 | 20% | `minimal_social_emergency_fallback_line`, `strict_social_ownership_terminal_fallback` |
| **validators** | 7 | 8% | `is_route_illegal_global_or_sanitizer_fallback_text`, `replacement_is_route_legal_social` |
| **gate** | 6 | 7% | `strict_social_emission_will_apply`, `merged_player_prompt_for_gate` |
| **replay** | 1 | 1% | `build_final_strict_social_response` (transcript regressions) |
| **diagnostics** | 1 | 1% | ownership registry + gate delegator governance strings |

> **Note:** Importers may appear in multiple classes. Totals sum to **79** tag assignments across **52** files.

## Strict-social pipeline cluster (23 tagged)

Primary composition path: `final_emission_strict_social_stack` → `build_final_strict_social_response`. Upstream narrative modules consume `merged_player_prompt_for_gate` for gate-aligned player text.

Representative: `final_emission_strict_social_stack`, `interaction_context`, `final_emission_*` policy modules, `gm_retry`.

## Gate cluster (6 tagged)

Preflight strict-social (`final_emission_gate_preflight_strict_social`), API turn routing (`api`, `api_turn_support`), sanitizer boundary (`output_sanitizer`), anti-reset guard.

**Dominant imports:** `strict_social_emission_will_apply`, `merged_player_prompt_for_gate`, `effective_strict_social_resolution_for_emission`.

## Terminal emission cluster (16 tagged)

Fallback line selection and ownership terminal paths across visibility, sealed fallback, terminal pipeline, response_type, speaker contract, interaction continuity.

**Dominant import:** `minimal_social_emergency_fallback_line` (BU FI 10).

## Validators cluster (7 tagged)

`final_emission_validators`, `final_emission_referential_clarity`, `gm.py`, contextual repair regressions. Route-legality predicates for social replacement acceptance.

## Tests cluster (25 importers)

`tests/test_social_exchange_emission.py` is the **BD-2 KEEP** legality owner. Additional social/speaker/transcript suites import composition and fallback symbols directly.

## Replay cluster (1 tagged)

`tests/test_narration_transcript_regressions.py` — imports `build_final_strict_social_response` and module-level patches. Replay risk is **behavioral** (strict-social terminal text), not import-graph direct.

## Diagnostics cluster (1 tagged)

`tests/test_ownership_registry.py` — BJ-115/116 delegate verification, BN8 strict-social boundary locks, gate delegator governance map entry for `game.social_exchange_emission`.

## Ownership bucket cross-cut

| Bucket | Importers |
| --- | --- |
| fallback-emission | 16 |
| strict-social-composition | 13 |
| gate-preflight-policy | 8 |
| realization-projection | 4 |
| route-legality-validator | 4 |
| module-monkeypatch | 4 |
| eligibility-policy | 1 |
| telemetry-projection | 1 |
| ownership-governance | 1 |
