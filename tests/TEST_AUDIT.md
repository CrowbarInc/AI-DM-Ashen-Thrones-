# Test suite audit (Block 15A)

Diagnostic inventory of `tests/` only: no runtime code or assertions were changed for this pass.

**Regenerate artifacts:** from repo root run `py -3 tools/test_audit.py` (or `python tools/test_audit.py`). That refreshes `tests/test_inventory.json` using `pytest --collect-only` plus static heuristics.

**Block 20 — feature ownership:** Inventory `feature_areas` now honor optional per-test `# feature: tag1, tag2` lines (immediately above the test, optionally above `@pytest.mark.*`), module-level `# feature:` before the first top-level `def test_`, and `@pytest.mark.routing|retry|fallback|social|continuity|clues|leads|emission|legality` when present. Tags map into the existing inventory labels (e.g. `clues` → `clue system`, `leads` → `lead extraction`). See `pytest.ini` for registered markers.

**Per-test rows:** `tests/test_inventory.json` — each collected pytest item includes `nodeid`, heuristic `primary_bucket`, `feature_areas`, `historically_motivated`, `assertion_style`, `brittleness`, and `redundancy_flag` (cross-file name collisions are rare; see limitations below).

---

## Executive counts

| Metric | Value |
| --- | ---: |
| Test files (`tests/test_*.py`) | 59 |
| Pytest collected items | 639 |
| Module-level `def test_*` lines (AST) | 656 |
| Unique test names per module (AST, one per name) | 631 |
| Parametrized expansion beyond unique names | 8 (`tests/test_prompt_and_guard.py`) |
| Items flagged `historically_motivated` (heuristic) | 66 |
| Assertion style (heuristic, per collected item) | structural 170, behavioral 438, mixed 24, prose-sensitive 7 |
| Brittleness (heuristic) | low 480, medium 114, high 45 |
| Redundancy flag `possible_overlap` from identical test names across files | 0 |

### Counts by test-level primary bucket

Derived per collected item (filename hint + body heuristics): **integration** 322, **unit** 254, **regression** 45, **transcript_gauntlet** 18.

### Counts by file-level primary bucket

`primary_bucket` on each file record is the **majority** bucket among that file’s collected tests: **integration** 31 files, **unit** 19, **transcript_gauntlet** 3, **regression** 6. The JSON field `filename_bucket` records path-pattern hints only (`transcript_gauntlet`, `regression`, or `mixed/unclear`).

---

## Critical data-quality issue: shadowed duplicate defs

`tests/test_exploration_resolution.py` defines **41** `def test_*` lines but only **16** unique names: earlier bodies are overwritten by later redefinitions. Pytest runs **16** tests from this module; **25** intended cases are currently unreachable. Treat any “inventory” that counts raw `def test_*` lines as overstated until this file is deduplicated (future block; not fixed here).

---

## Top 10 files by count of high-brittleness tests (heuristic)

1. `tests/test_transcript_regression.py` — 10  
2. `tests/test_transcript_gauntlet_lead_to_consequence.py` — 8  
3. `tests/test_mixed_state_recovery_regressions.py` — 6  
4. `tests/test_transcript_gauntlet_actor_addressing.py` — 6  
5. `tests/test_empty_social_retry_regressions.py` — 4  
6. `tests/test_transcript_gauntlet_campaign_cleanliness.py` — 4  
7. `tests/test_prompt_and_guard.py` — 3  
8. `tests/test_agenda_simulation.py` — 1  
9. `tests/test_clue_discovery.py` — 1  
10. `tests/test_emergent_scene_actors.py` — 1  

(Next: `tests/test_gauntlet_regressions.py` — 1.)

---

## Top 10 “likely overlap” **areas** (by spread across files)

These are **feature tags** (keyword heuristics), not proof of duplicate tests. High file counts mean trims/consolidation require reading tests, not deleting by tag.

| Rank | Feature tag (heuristic) | Distinct files touching tag (any position) |
| --- | --- | ---: |
| 1 | general | 24 |
| 2 | clue system | 19 |
| 3 | legality/sanitizer | 14 |
| 4 | fallback | 13 |
| 5 | resolution/emission | 12 |
| 6 | routing | 11 |
| 7 | world/state | 11 |
| 8 | combat/skill | 10 |
| 9 | social continuity | 8 |
| 10 | lead extraction | 7 |

The large **general** bucket indicates tagging debt: many modules do not match current keyword rules and default to `general`; refine rules or add explicit markers over time.

---

## Candidate canonical suites by feature area

Use as starting points when deciding where new coverage should live first.

| Area | Strong candidate files |
| --- | --- |
| End-to-end / session transcript flows | `test_transcript_regression.py`, `test_gauntlet_regressions.py` |
| Transcript gauntlet (LTC slice / harness) | `test_transcript_gauntlet_*.py`, `test_transcript_runner_smoke.py` |
| Mixed-state & social continuity | `test_mixed_state_recovery_regressions.py`, `test_dialogue_interaction_establishment.py` |
| Retry / empty social / terminal fallback | `test_empty_social_retry_regressions.py`, `test_social_answer_retry_prioritization.py` |
| Contextual minimal repair | `test_contextual_minimal_repair_regressions.py` |
| Shared chat/action pipeline | `test_turn_pipeline_shared.py` |
| Social emission / strict social | `test_social_exchange_emission.py`, `test_social_answer_candidate.py` |
| Directed routing & dialogue lock | `test_directed_social_routing.py`, `test_dialogue_routing_lock.py` |
| Clue knowledge & inference | `test_clue_knowledge.py`, `test_world_updates_and_clue_normalization.py` |
| Output / legality | `test_output_sanitizer.py`, `test_prompt_and_guard.py`, `test_debug_payload_spoiler_safety.py` |
| Exploration resolution | `test_exploration_resolution.py` (after dedup), `test_exploration_skill_checks.py` |

---

## Recommended canonical coverage map

Concrete “source of truth” examples for recurring themes (prefer extending these before adding parallel modules).

| Theme | Canonical example |
| --- | --- |
| Retry termination / empty social repair | `tests/test_empty_social_retry_regressions.py::test_force_terminal_retry_fallback_repairs_empty_social_candidate` |
| Final emission continuity after terminal retry | `tests/test_empty_social_retry_regressions.py::test_force_terminal_retry_fallback_preserves_final_emission_meta_continuity` |
| API-level empty-social repair | `tests/test_empty_social_retry_regressions.py::test_api_repairs_empty_social_after_force_terminal_retry_fallback` |
| Clue idempotency / no double inference | `tests/test_clue_knowledge.py::test_reveal_clue_duplicate_does_not_reinvoke_inference` |
| Authoritative clue gateway dedupe | `tests/test_clue_knowledge.py::test_authoritative_clue_gateway_dedupes_duplicate_writes` |
| Social continuity & routing through mixed narration | `tests/test_mixed_state_recovery_regressions.py::test_approach_visible_figure_then_question_routes_social` |
| No “no new information” dead-end when hook present | `tests/test_mixed_state_recovery_regressions.py::test_social_text_with_hook_cannot_end_with_no_new_information_state` |
| Contextual repair must not inject clue/resolution payloads | `tests/test_contextual_minimal_repair_regressions.py::test_contextual_minimal_repair_does_not_add_clue_or_resolution_payload` |
| Repair lines pass legality | `tests/test_contextual_minimal_repair_regressions.py::test_contextual_repair_lines_pass_legality_checks` |
| Dialogue lock → social lane | `tests/test_turn_pipeline_shared.py::test_chat_dialogue_lock_routes_npc_directed_question_regressions` |
| Final emission gate (invalid blob replacement) | `tests/test_turn_pipeline_shared.py::test_final_emission_gate_replaces_invalid_social_exchange_blob_before_emit` |
| Retry prioritization (structured vs stall) | `tests/test_social_answer_retry_prioritization.py::test_prioritize_suppresses_scene_stall_when_structured_candidate_exists` |
| Transcript gauntlet: explicit address stability | `tests/test_transcript_gauntlet_actor_addressing.py::test_explicit_address_never_gets_wiped_by_later_validation` |

---

## Safe consolidation candidates (recommendations only)

1. **`test_contextual_minimal_repair_regressions.py` vs `test_empty_social_retry_regressions.py`**  
   - **Overlap:** Both cover contextual / minimal repair paths for social and non-social empties; some assertions orbit the same helper behaviors.  
   - **Canonical:** Keep `test_empty_social_retry_regressions.py` for **retry termination + API**; keep `test_contextual_minimal_repair_regressions.py` for **payload/legality invariants** on repair text.  
   - **Merge/weaken:** Share fixtures/helpers only; avoid merging scenarios until one file owns “retry policy” and the other “repair content shape.”

2. **`test_turn_pipeline_shared.py` vs `test_directed_social_routing.py` vs `test_dialogue_routing_lock.py`**  
   - **Overlap:** Routing, dialogue lock, and social/adjudication boundaries appear in all three at different depths.  
   - **Canonical:** `test_turn_pipeline_shared.py` for **full `/api/chat` pipeline** locks; smaller files for **focused routing tables**.  
   - **Merge/weaken:** Prefer new routing cases in `test_directed_social_routing.py` unless they require full pipeline; avoid a third parallel file for the same lock.

3. **`test_output_sanitizer.py` vs `test_prompt_and_guard.py` (validator / guard / prose)**  
   - **Overlap:** Legality, validator voice, and sanitization strings.  
   - **Canonical:** `test_output_sanitizer.py` for **emit-time sanitizer**; `test_prompt_and_guard.py` for **prompt construction + guard contracts**.  
   - **Merge/weaken:** When a failure is “output shape after GM,” add sanitizer tests; when “messages to model,” add prompt/guard tests.

4. **`test_social.py` vs `test_social_exchange_emission.py` vs `test_social_escalation.py`**  
   - **Overlap:** Broad social behavior, escalation, and emission formatting share vocabulary.  
   - **Canonical:** `test_social_exchange_emission.py` for **strict social / emission**; `test_social_escalation.py` for **pressure/escalation state machine**; `test_social.py` as **misc integration** only if no better home.  
   - **Merge/weaken:** New strict-social assertions should default to `test_social_exchange_emission.py`.

5. **`test_exploration_resolution.py` (internal duplication)**  
   - **Overlap:** Repeated function names shadow earlier tests (see above).  
   - **Canonical:** After cleanup, one named test per behavior; use **parametrize** or distinct names for variants.  
   - **Merge/weaken:** No merge across files needed first—fix shadowing to restore intended coverage.

---

## Full file index

`primary_bucket` = majority of tests in that file. `High-brittleness` = count of tests with heuristic `brittleness: high` in that file. Feature tags = top primary feature labels (first keyword hit per test, aggregated).

| File | Collected | Primary bucket (majority of tests) | High-brittleness tests | Top primary feature tags |
| --- | ---: | --- | ---: | --- |
| test_activate_scene_validation_and_get_persistence.py | 6 | integration | 0 | general |
| test_affordance_generation.py | 12 | integration | 0 | general |
| test_agenda_simulation.py | 9 | unit | 1 | general |
| test_campaign_reset.py | 5 | integration | 0 | world/state |
| test_campaign_state_factory.py | 3 | unit | 0 | world/state |
| test_clocks_projects_logging_lint.py | 5 | integration | 0 | general, clue system |
| test_clue_discovery.py | 4 | integration | 1 | clue system |
| test_clue_knowledge.py | 10 | integration | 0 | clue system |
| test_combat_resolution.py | 6 | integration | 0 | resolution/emission |
| test_conditional_affordances.py | 14 | unit | 0 | general, clue system |
| test_contextual_minimal_repair_regressions.py | 6 | regression | 0 | fallback |
| test_debug_payload_spoiler_safety.py | 3 | integration | 0 | legality/sanitizer |
| test_dialogue_interaction_establishment.py | 10 | integration | 0 | social continuity |
| test_dialogue_routing_lock.py | 5 | unit | 0 | routing |
| test_directed_social_routing.py | 21 | integration | 0 | routing, social continuity |
| test_discovery_memory.py | 8 | integration | 0 | clue system |
| test_emergent_scene_actors.py | 6 | unit | 1 | general |
| test_empty_social_retry_regressions.py | 8 | regression | 4 | retry |
| test_exploration_resolution.py | 16 | integration | 0 | resolution/emission, routing, clue system |
| test_exploration_skill_checks.py | 5 | integration | 0 | combat/skill |
| test_gauntlet_regressions.py | 5 | regression | 1 | transcript regression |
| test_intent_and_runtime.py | 2 | unit | 0 | routing |
| test_intent_parser.py | 18 | unit | 0 | routing, fallback |
| test_interaction_context_owner.py | 8 | unit | 0 | general, social continuity |
| test_mixed_state_recovery_regressions.py | 6 | regression | 6 | mixed-state recovery |
| test_narration_state_consistency.py | 9 | unit | 0 | general, fallback, clue system |
| test_output_sanitizer.py | 41 | unit | 0 | legality/sanitizer, fallback, routing, transcript regression |
| test_project_schema.py | 4 | integration | 0 | general |
| test_prompt_and_guard.py | 67 | integration | 3 | legality/sanitizer, fallback, lead extraction, clue system |
| test_prompt_compression.py | 17 | integration | 0 | general, world/state, fallback |
| test_save_load.py | 5 | integration | 0 | world/state, clue system |
| test_scene_advancement_signals.py | 3 | integration | 0 | general, world/state |
| test_scene_entity_lock.py | 4 | integration | 0 | social continuity, general |
| test_scene_graph.py | 6 | integration | 0 | world/state, routing |
| test_scene_layers.py | 2 | integration | 0 | clue system, general |
| test_scene_transition_authority.py | 3 | integration | 0 | general |
| test_scene_validation.py | 17 | unit | 0 | general, clue system |
| test_skill_checks.py | 9 | unit | 0 | combat/skill, fallback |
| test_snapshots.py | 5 | integration | 0 | general, world/state |
| test_social.py | 23 | integration | 0 | general, clue system, social continuity, legality/sanitizer |
| test_social_answer_candidate.py | 7 | unit | 0 | general, fallback |
| test_social_answer_retry_prioritization.py | 4 | integration | 0 | retry |
| test_social_escalation.py | 16 | unit | 0 | general |
| test_social_exchange_emission.py | 43 | unit | 0 | resolution/emission, fallback, retry, clue system |
| test_social_interaction_authority.py | 7 | integration | 0 | general, fallback, resolution/emission |
| test_social_lead_landing.py | 17 | integration | 0 | lead extraction, clue system |
| test_social_probe_determinism.py | 6 | integration | 0 | general, legality/sanitizer, lead extraction |
| test_social_target_authority_regressions.py | 10 | regression | 0 | social continuity |
| test_startup_and_timestamps.py | 4 | unit | 0 | general |
| test_transcript_gauntlet_actor_addressing.py | 6 | transcript_gauntlet | 6 | transcript regression |
| test_transcript_gauntlet_campaign_cleanliness.py | 4 | transcript_gauntlet | 4 | transcript regression |
| test_transcript_gauntlet_lead_to_consequence.py | 8 | transcript_gauntlet | 8 | transcript regression |
| test_transcript_regression.py | 10 | regression | 10 | transcript regression |
| test_transcript_runner_smoke.py | 1 | integration | 0 | transcript regression |
| test_turn_pipeline_shared.py | 46 | integration | 0 | general, routing, retry, combat/skill |
| test_validation_journal_affordances.py | 10 | unit | 0 | general, clue system |
| test_world_engine_updates.py | 9 | unit | 0 | resolution/emission |
| test_world_state.py | 8 | unit | 0 | world/state |
| test_world_updates_and_clue_normalization.py | 7 | integration | 0 | clue system |

---

## Methodology & limitations

- **Ground truth for “what runs”:** pytest collection (`639` items). AST line counts include shadowed defs in `test_exploration_resolution.py`.  
- **Buckets:** Test-level buckets use filename patterns (`transcript_gauntlet`, `regression`) then body signals (`TestClient`, `tmp_path`, length).  
- **Feature areas:** Substring rules on `nodeid`, merged with explicit `# feature:` / ownership `pytest.mark.*` when present; unannotated tests may still land on **general**.  
- **Assertion style / brittleness:** Regex on function source (long string `==`, `in "..."`, structural calls). Transcript/regression modules biased to **high** brittleness.  
- **Redundancy:** `possible_overlap` only triggers on identical **base** test names in different files (none found). Semantic duplicates are **not** auto-detected.  
- **Pytest markers:** `pytest.ini` defines `unit`, `integration`, `regression`, `transcript`, `slow`, `brittle`, plus optional ownership markers (`routing`, `retry`, `fallback`, `social`, `continuity`, `clues`, `leads`, `emission`, `legality`). `tools/test_audit.py` reads those ownership markers and `# feature:` comments when building `feature_areas`.

---

## Optional metadata comments

Use `# feature: routing, fallback` on the line before a test (or once per file before the first top-level `def test_`) so `test_inventory.json` picks up ownership without relying on `nodeid` keywords. Equivalent: `@pytest.mark.routing` (see `pytest.ini`). Large or previously-`general` modules are partially tagged; extend over time.
