# Cycle AL — Downstream Assertion Convergence Closure

**Date:** 2026-06-01  
**Status:** AL1–AL6 complete. Cycle AL closed.

**Goal:** Stop downstream smoke/integration suites from restating gate, sanitizer, social, and FEM owner legality. Downstream asserts **wiring only**; owners retain full matrices and route tables.

**Recon:** [cycle_al_downstream_assertion_convergence_recon_2026-06-01.md](./cycle_al_downstream_assertion_convergence_recon_2026-06-01.md)

---

## AL1 — Fixture / import cleanup

- Extracted shared HTTP/pipeline fixtures to `tests/helpers/turn_pipeline_http_fixtures.py` (`FAKE_GPT_RESPONSE`, `_gm_response`, `_seed_shared_world`, `_seed_runner_dialogue_context`, `_patch_storage`).
- Re-exported `gm_response_stub` through the fixtures module for consumers that previously imported from `test_turn_pipeline_shared.py`.
- Reduced test-to-test imports from `test_turn_pipeline_shared` in playability/API smoke consumers (per AD/AL recon targets).

## AL1b — Remaining fixture cleanup

- Completed migration of turn-pipeline HTTP consumers off direct `test_turn_pipeline_shared` symbol imports where blocking ownership clarity.
- Left intentional test-to-test imports deferred unless they obscured legality boundaries (see Deferred work).

## AL2 — Phrase assertion thinning

**Facade extended:** `tests/helpers/emission_smoke_assertions.py`

- Phrase smoke tuples: `SMOKE_PROCEDURAL_ADJUDICATION_PHRASES`, `SMOKE_VALIDATOR_VOICE_PHRASES`, `SMOKE_RETRY_COACHING_LEAK_PHRASES`, `SMOKE_SOCIAL_VISIBLE_INTRO_FILLER_PHRASES`, `SMOKE_UNCERTAINTY_FALLBACK_STOCK_PHRASES`
- Synthetic harness regex tuples: `SMOKE_SYNTHETIC_*_PATTERNS`
- Helpers: `assert_procedural_adjudication_smoke`, `assert_no_validator_voice_smoke`, `assert_no_retry_coaching_leak_smoke`, `assert_no_social_visible_intro_filler_smoke`, `assert_no_uncertainty_fallback_stock_smoke`

**Thinned downstream:**

- `tests/test_turn_pipeline_shared.py` — replaced inline `low = ...; assert phrase not in low` blocks with facade helpers on retry/adjudication/social HTTP smoke paths.
- `tests/test_synthetic_smoke.py` — removed local `_FOLLOWUP_*_PATTERNS` matrices; imports shared synthetic patterns from facade.

**Owners untouched:** `test_output_sanitizer.py`, `test_social_exchange_emission.py`, `test_final_emission_visibility.py`.

## AL3 — Final-route smoke thinning

**Facade extended:**

- `assert_final_route_present_smoke`, `assert_final_route_accept_candidate_smoke`, `assert_final_route_not_replaced_smoke`
- Reused `assert_final_route_replaced_or_not_accept` for non-accept wiring

**Thinned downstream:**

- `tests/test_c4_narrative_mode_live_pipeline.py` — exact `final_route == "replaced"` / `"accept_candidate"` → smoke helpers where route value was not the direct subject; retained exact `final_emitted_source` where it was.
- `tests/test_social_exchange_emission.py` — one integration case (`answer_completeness` boundary) thinned to `assert_final_route_replaced_or_not_accept`; phrase/source owner assertions retained.
- `tests/test_interaction_continuity_repair.py` — `final_route` wiring checks → facade helpers.

**Owners untouched:** `test_final_emission_gate.py`, `test_final_emission_meta.py`, `test_dialogue_routing_lock.py`.

## AL4 — Registry and facade documentation lock-in

- `tests/test_ownership_registry.py` — Cycle AL4 module docstring quick reference; `_DOWNSTREAM_SMOKE_FACADE`, `_AL4_LEGALITY_OWNER_PATHS`; governance test `test_al4_legality_owners_and_smoke_facade_locked`.
- `tests/helpers/emission_smoke_assertions.py` — expanded facade docstring (owners vs smoke vs replay separation).
- This closure note.

## AL5 — Broadcast / open-call downstream migration

**Facade extended (AL5):** `assert_open_social_solicitation_route`, `assert_broadcast_open_call_rejected_smoke`, `assert_open_call_crowd_reaction_wiring_smoke`, `assert_open_call_no_unresolved_retry_smoke`.

**Thinned downstream:**

- `tests/test_broadcast_open_call_social.py` — route/detector wiring via facade; direct `question_resolution_rule_check` / `detect_retry_failures` calls kept as unique wiring harness only.
- `tests/test_broad_address_social_bid.py` — open-solicitation route smoke via facade on `resolve_directed_social_entry`.

**Owners untouched:** `tests/test_social_exchange_emission.py`, `tests/test_dialogue_routing_lock.py`.

## AL6 — Final redundant assertion deletion pass

**Deleted / thinned downstream duplicates:**

| File | Change |
| --- | --- |
| `tests/test_turn_pipeline_shared.py` | Removed duplicate HTTP sanitizer test (`test_chat_final_output_sanitizer_blocks_adjudication_procedural_leak`); procedural smoke folded into `test_chat_adjudication_refuses_over_answer_without_basis`. Removed redundant `test_chat_social_exchange_strips_unresolved_stock_phrases` (covered by invalid-blob + facade). Dropped repeated `assert_no_unresolved_stock_phrases` / `assert_no_advisory_prose` from repeated-questioning and interruption-denial paths where other cases already cover HTTP phrase smoke. |
| `tests/test_c4_narrative_mode_live_pipeline.py` | Removed exact `final_emitted_source == minimal_social_emergency_fallback`; retained `assert_final_route_replaced_or_not_accept` + narrative-mode FEM wiring. |
| `tests/test_broad_address_social_bid.py` | Replaced inline uncertainty-stock phrase bans with `assert_no_unresolved_stock_phrases`; removed strict-social phrase ban (`pin down who they meet`) owned by `test_social_exchange_emission.py`. |
| `tests/test_mixed_state_recovery_regressions.py` | Replaced inline global-visibility / intro-filler bans with facade helpers. |

**Owner suites retaining full legality (unchanged):**

- `tests/test_final_emission_gate.py`
- `tests/test_final_emission_meta.py`
- `tests/test_dialogue_routing_lock.py`
- `tests/test_output_sanitizer.py`
- `tests/test_social_exchange_emission.py`
- `tests/test_final_emission_visibility.py`

**Intentional overlaps retained:**

- Golden replay / classifier FEM bucket projection (`tests/helpers/golden_replay_projection.py`, `tests/test_failure_classifier.py`, `tests/test_golden_replay.py`) — diagnostic drift protection, not downstream smoke.
- `tests/test_narration_transcript_regressions.py` FEM `meta_exact` / `required_substrings` — transcript regression locks, not HTTP smoke duplication.
- `tests/test_broadcast_open_call_social.py` direct calls to `question_resolution_rule_check` / `detect_retry_failures` — prove open-call exemption wiring at the GM retry seam.
- One representative HTTP sanitizer smoke per category in `test_turn_pipeline_shared.py` (scaffold labels, unresolved stock, advisory prose, global visibility).

**Final verification (AL6):** see commands below; owner + downstream + registry + golden_replay green baseline expected after AL5 strict-social seam fix.

---

## Ownership boundaries (locked)

| Responsibility | Direct owner | Downstream smoke surface |
| --- | --- | --- |
| Gate orchestration / route tables | `tests/test_final_emission_gate.py` | `emission_smoke_assertions` route smoke helpers |
| FEM projection / lineage | `tests/test_final_emission_meta.py` | — |
| Dialogue route classification | `tests/test_dialogue_routing_lock.py` | `tests/test_turn_pipeline_shared.py` (HTTP packaging) |
| Sanitizer phrase legality | `tests/test_output_sanitizer.py` | facade phrase smoke helpers |
| Strict-social phrase/source | `tests/test_social_exchange_emission.py` | facade phrase/route smoke helpers |
| HTTP integration smoke | `tests/test_turn_pipeline_shared.py` | registered `downstream_consumer_suites` neighbor |

---

## Known pre-existing failure (resolved by AL5)

The prior `AttributeError: module 'game.gm' has no attribute 'effective_strict_social_resolution_for_emission'` blocked strict-social HTTP retry paths. AL5 fixed the gm seam; AL6 verification assumes that baseline is green.

---

## Deferred work

| Item | Rationale |
| --- | --- |
| Golden replay / classifier FEM bucket overlap | Intentional diagnostic projection — not downstream to thin (AD-3 / AL4 locked) |
| Remaining test-to-test imports | Deferred unless they block ownership clarity (e.g. `test_narration_transcript_regressions` ← `test_fallback_behavior_gate`) |

---

## Verification commands (AL6)

```powershell
py -3 -m pytest tests/test_turn_pipeline_shared.py -q --tb=line
py -3 -m pytest tests/test_synthetic_smoke.py -q --tb=line
py -3 -m pytest tests/test_c4_narrative_mode_live_pipeline.py -q --tb=line
py -3 -m pytest tests/test_broadcast_open_call_social.py tests/test_broad_address_social_bid.py -q --tb=line
py -3 -m pytest tests/test_final_emission_gate.py tests/test_final_emission_meta.py tests/test_dialogue_routing_lock.py tests/test_output_sanitizer.py tests/test_social_exchange_emission.py tests/test_final_emission_visibility.py -q --tb=line
py -3 -m pytest tests/test_ownership_registry.py -q
py -3 -m pytest -m golden_replay -q
```

Owner regression (unchanged):

```powershell
py -3 -m pytest tests/test_final_emission_gate.py tests/test_final_emission_meta.py tests/test_output_sanitizer.py tests/test_social_exchange_emission.py -q --tb=line
```
