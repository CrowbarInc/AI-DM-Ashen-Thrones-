# Cycle R / R2 — Passive Phrase-Ban Thinning

**Date:** 2026-05-30  
**Status:** Complete — all targeted pytest commands green.

---

## Phrase families found (repo scan)

| Family | Example markers | Canonical owner (preserved) |
| --- | --- | --- |
| **Global visibility stock** | `for a breath, the scene holds`, `voices shift around you` | `tests/test_final_emission_visibility.py` (semantic replace path); `tests/test_output_sanitizer.py` (string rewrite) |
| **Procedural / instructional** | `state exactly what you do`, `resolve that procedurally`, `adjudication:`, `authoritative state` | `tests/test_output_sanitizer.py` |
| **Uncertainty / non-answer stock** | `no answer presents itself from here`, `nothing in the scene points to a clear answer yet`, `answer has not formed yet`, `scene offers no clear answer yet` | `tests/test_output_sanitizer.py` |
| **Question-resolution legality** | `question_resolution_rule_check` `applies` / `ok` / `reasons` | `tests/test_social_exchange_emission.py` |

**Replay / structural (not thinned):** `tests/test_golden_replay.py`, long-session replays, transcript gauntlets, `test_scenario_spine_continuation_convergence.py`, etc.

---

## Classification of hits in R2 target files (before)

| File | Hit context | Classification |
| --- | --- | --- |
| `test_turn_pipeline_shared.py` | Repeated `scene holds` / `for a breath` across dialogue-lock, direct NPC question, action-outcome, interruption tests | **Passive duplicate** (HTTP routing/emission primary) |
| `test_turn_pipeline_shared.py` | `state exactly what you do` in repeated-social + mixed-investigate | **Passive duplicate** |
| `test_turn_pipeline_shared.py` | Long OR lists of allowed uncertainty phrases in two adjudication HTTP tests | **Passive duplicate** (sanitizer owner holds matrix) |
| `test_turn_pipeline_shared.py` | `test_chat_final_output_sanitizer_blocks_adjudication_procedural_leak` procedural bans | **Downstream smoke (kept)** — one HTTP legality path for adjudication leak |
| `test_turn_pipeline_shared.py` | `test_chat_adjudication_refuses_over_answer_without_basis` | **Owner assertion (routing)** — narrowed to adjudication metadata + non-empty output |
| `test_turn_pipeline_shared.py` | Wait/pressure path `for a breath, the scene holds` ban | **Downstream smoke (kept)** — single HTTP visibility-stock check via helper |
| `test_social_speaker_grounding.py` | `scene holds` substring ban on neutral-bridge test | **Passive duplicate** (grounding meta is primary) |
| `test_social_answer_candidate.py` | Triple substring ban after strict-social build | **Passive duplicate** (structured-fact vs fallback source is primary) |
| `test_broadcast_open_call_social.py` | Three-loop `question_resolution_rule_check` on crowd lines | **Passive duplicate** (outcome smoke sufficient) |

---

## Owner files preserved (not modified)

- `tests/test_output_sanitizer.py`
- `tests/test_final_emission_visibility.py`
- `tests/test_social_exchange_emission.py`
- `tests/test_golden_replay.py`

---

## Downstream assertions narrowed / removed

### `tests/test_turn_pipeline_shared.py`

| Test / area | Removed / narrowed | Kept (primary concern) |
| --- | --- | --- |
| `test_chat_dialogue_lock_final_output_beats_generic_fillers_and_keeps_contract_meta` | Separate `for a breath` + `scene holds` asserts | `_assert_global_visibility_stock_absent` when stub contains stock; `stands nearby` for intro filler; `final_emitted_source != global_scene_fallback`; dialogue contract meta |
| `test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback` | `for a breath` / `scene holds` bans | Dialogue contract, answer-completeness meta, NPC answer-shape phrases |
| `test_chat_repeated_social_questions_keep_npc_uncertainty_voice` | `state exactly what you do` ban | NPC voice (`tavern runner`, quotes), `resolve that procedurally` smoke |
| `test_chat_adjudication_refuses_over_answer_without_basis` | Full phrase ban + allowed-fallback OR matrix | `answer_type == needs_concrete_action`, non-empty output |
| `test_chat_mixed_scene_object_investigation_question_recovers_action_outcome` | `state exactly what you do` ban | Action-outcome recovery, stub-specific `scene pauses` / `nothing concrete` |
| `test_chat_action_outcome_contract_survives_inside_active_social_scene` | `for a breath` / `scene holds` bans | Clue emission meta, desk/clue content, `action_outcome_upstream_prepared_repair` |
| `test_chat_final_output_sanitizer_blocks_adjudication_procedural_leak` | Allowed-fallback OR matrix | Procedural leak bans + non-empty output (HTTP legality smoke) |
| `test_chat_repeated_interruption_progresses_without_losing_dialogue_contract` | `for a breath` / `scene holds` on second turn | Progression + `final_emitted_source != global_scene_fallback` |
| Wait/pressure HTTP path | — | `_assert_global_visibility_stock_absent` (canonical single stock phrase smoke) |

**Added:** `_assert_global_visibility_stock_absent(low)` — one combined marker for global visibility stock on HTTP paths.

### `tests/test_social_speaker_grounding.py`

| Test | Removed | Kept |
| --- | --- | --- |
| `test_build_final_strict_social_emits_neutral_bridge_when_grounding_denied` | `scene holds` substring ban | `final_emitted_source`, `fallback_kind`, grounding bridge flags |

### `tests/test_social_answer_candidate.py`

| Test | Removed | Kept |
| --- | --- | --- |
| `test_build_final_route_illegal_without_topic_fact_does_not_emit_structured_fact` | `for a breath` / `scene holds` / `voices shift` matrix | `final_emitted_source != structured_fact_candidate_emission`, `tavern runner` in output |

### `tests/test_broadcast_open_call_social.py`

| Test | Removed | Kept |
| --- | --- | --- |
| `test_question_resolution_exempt_for_open_call_crowd_reaction` | Three-line loop re-checking same exemption | One crowd-reaction line; `applies is False`, `ok is True`, `reasons == []` |

---

## Files changed

| File | Change |
| --- | --- |
| `tests/test_turn_pipeline_shared.py` | Phrase-matrix thinning; `_assert_global_visibility_stock_absent` helper |
| `tests/test_social_speaker_grounding.py` | Dropped redundant stock phrase ban |
| `tests/test_social_answer_candidate.py` | Dropped redundant stock phrase matrix |
| `tests/test_broadcast_open_call_social.py` | Single outcome smoke for open-call question-resolution exemption |

**Production code:** none modified.

---

## Tests run and results

| Command | Result |
| --- | --- |
| `py -3 -m pytest tests/test_turn_pipeline_shared.py tests/test_social_speaker_grounding.py tests/test_social_answer_candidate.py tests/test_broadcast_open_call_social.py -q` | **PASS** (96 items) |
| `py -3 -m pytest tests/test_output_sanitizer.py tests/test_final_emission_visibility.py tests/test_social_exchange_emission.py -q` | **PASS** (182 items) |
| `py -3 -m pytest tests/test_golden_replay.py -m golden_replay -q` | **PASS** (53 items) |

---

## Coverage confirmation

- **Owner phrase coverage:** unchanged — sanitizer, visibility, and social-emission owner modules not edited; full phrase matrices and legality tables remain there.
- **Replay coverage:** unchanged — `test_golden_replay.py` not touched; golden lane (53 tests) passed.
- **HTTP visible-output protection:** preserved — one combined global-visibility-stock smoke (`_assert_global_visibility_stock_absent`) on wait/pressure and dialogue-lock stock stubs; adjudication procedural-leak HTTP test retains procedural substring bans; dialogue/social tests retain routing, FEM meta, and NPC-voice assertions.
- **No tests removed:** assertion count reduced only by dropping duplicate substring matrices, not by deleting test functions.
