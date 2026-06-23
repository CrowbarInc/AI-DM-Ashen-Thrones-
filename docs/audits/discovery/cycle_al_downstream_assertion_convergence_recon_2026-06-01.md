# Cycle AL — Downstream Assertion Convergence Recon

**Date:** 2026-06-01  
**Scope:** Recon only — no refactors. Goal: plan Cycle AL implementation blocks (AL1, AL2, …) to stop downstream smoke/route/projection suites from restating gate/fallback/FEM owner legality; downstream should assert **wiring** only.

**Ground truth:** `tests/test_ownership_registry.py` defines 18 governed responsibility groups with explicit `direct_owner` vs `downstream_consumer_suites` vs `smoke_suites`. Prior cycles AD/AE/AG extracted `emission_smoke_assertions.py` and `turn_pipeline_http_fixtures.py` but several suites still inline owner-level phrase/route/FEM locks.

**Live collect (spot check):** `test_turn_pipeline_shared.py` → **70** tests; `test_response_delta_requirement.py` → **46**; `test_answer_completeness_rules.py` → **~40+** (same collect batch).

---

## 1. Candidate downstream suites

Legend: **Owner** = normative legality home; **Downstream wiring** = HTTP/API/packaging/threading only; **Mixed** = needs thinning.

### HTTP / turn-pipeline smoke

| File | Representative tests | Current behavior / assertions | Classification |
| --- | --- | --- | --- |
| `tests/test_turn_pipeline_shared.py` | 70 tests incl. `test_chat_dialogue_lock_*`, `test_chat_final_output_sanitizer_*`, `test_chat_social_exchange_*`, `test_emission_smoke_helpers_*` | `/api/chat` + `/api/action` E2E: routing, retry tags, dialogue contract meta, **inline procedural phrase bans** (`resolve that procedurally`, `state exactly what you do`, `scene offers no clear answer yet`), scaffold bans via `assert_no_internal_scaffold_labels`, stock phrases via `assert_no_unresolved_stock_phrases` / `assert_no_advisory_prose`, visibility stock via `assert_global_visibility_stock_absent`, repair evidence via `assert_emission_repair_evidence` | **Mixed → target Downstream wiring**. Docstring (Cycle AD-1) already claims HTTP-only; still duplicates sanitizer/social phrase matrices on ~8 tests. |
| `tests/test_playability_smoke.py` | `test_playability_smoke_direct_answer_pressure`, `narrowing_player_intent`, `escalation_under_pressure`, `immersion_guard_adversarial_upstream` | Offline playability axes over seeded HTTP context (`turn_pipeline_http_fixtures`); checks evaluator-facing outcomes, not full gate tables | **Downstream wiring** (evaluator smoke neighbor) |
| `tests/test_gauntlet_regressions.py` | API gauntlet routing / strict-social E2E | FastAPI client smoke; docstring defers phrase families to `test_output_sanitizer.py` / `test_prompt_and_guard.py` | **Downstream wiring** (thin substring locks OK) |
| `tests/test_start_campaign_api.py`, `tests/test_manual_play_latency.py`, `tests/test_empty_social_retry_regressions.py`, `tests/test_opening_start_seam_regressions.py`, `tests/test_turn_trace_contract.py` | Various API seams | Import symbols from `test_turn_pipeline_shared` or `turn_pipeline_http_fixtures` | **Downstream wiring** (fixture coupling risk) |
| `tests/test_c4_narrative_mode_live_pipeline.py` | `test_c4_smoke_*`, `test_c4_prompt_debug_*` | Planner→prompt→gate compact smoke; **`fem.get("final_route") == "accept_candidate"` / `"replaced"`** (4 sites) | **Mixed** — telemetry-first but restates gate route enum |
| `tests/helpers/turn_pipeline_http_fixtures.py` | (fixtures, not tests) | Re-exports `gm_response_stub` from `emission_smoke_assertions` | **Wiring support** |

### Social smoke

| File | Representative tests | Current behavior / assertions | Classification |
| --- | --- | --- | --- |
| `tests/test_social_speaker_grounding.py` | grounding follow-up tests | `assert_social_grounding_smoke` (npc_id, authority_source, no neutral bridge) | **Downstream wiring** (already on facade) |
| `tests/test_broadcast_open_call_social.py` | `test_who_wants_routes_open_social_with_broadcast_flag`, `test_broadcast_detector_rejects_local_observation` | `resolve_directed_social_entry` + `assert_open_social_solicitation_route`; also calls `question_resolution_rule_check` / `detect_retry_failures` directly | **Mixed** — route table is engine owner; broadcast file should be outcome smoke |
| `tests/test_synthetic_smoke.py` | `test_synthetic_smoke_run_*`, `test_fake_gm_*`, `test_fake_gm_regression_*` | Deterministic fake-GM runs; **local regex phrase matrices** (`_FOLLOWUP_VAGUE_FILLER_PATTERNS` includes `for a breath`, `scene holds`) parallel to sanitizer/smoke helper | **Mixed** — harness quality, not gate owner; high duplication cost with turn_pipeline |
| `tests/test_social_emission_quality.py` | `test_emission_quality_*` | Quality harness over emission paths (renamed from transcript-style names) | **Downstream wiring** neighbor of `test_social_exchange_emission.py` |
| `tests/test_playability_smoke.py` | (see HTTP) | Social pressure via HTTP | **Downstream wiring** |

### Route validation duplication

| File | Representative tests | Current behavior / assertions | Classification |
| --- | --- | --- | --- |
| `tests/test_dialogue_routing_lock.py` | `test_choose_interaction_route_dialogue_lock_pure_contract` | Pure `choose_interaction_route` table (parametrized) | **Owner** (route legality) |
| `tests/test_turn_pipeline_shared.py` | `test_chat_dialogue_lock_routes_*`, `test_chat_active_target_*`, `test_chat_roll_requirement_*` | Same routing decisions via HTTP + stubs | **Downstream wiring** (must not re-assert full route matrix) |
| `tests/test_broadcast_open_call_social.py` | `test_who_wants_routes_open_social_with_broadcast_flag` | Open-call classification fields + phrase match | **Downstream wiring** if thinned to `assert_open_social_solicitation_route` only |
| `tests/test_synthetic_smoke.py` | `test_fake_gm_regression_*_routing_*` | Fake-GM routing confusion guards | **Downstream wiring** (profile-level) |

### FEM projection duplication

| File | Representative tests | Current behavior / assertions | Classification |
| --- | --- | --- | --- |
| `tests/test_final_emission_meta.py` | `test_infer_accept_path_final_emitted_source_*`, `test_opening_fallback_projection_*`, merge/round-trip tests | FEM read/normalize/project; **`final_route` / `final_emitted_source` inference tables** | **Owner** (FEM projection) |
| `tests/test_opening_fallback_owner_bucket.py` | owner-bucket mapping tests | Canonical bucket read mapping | **Owner** (bucket semantics) |
| `tests/test_golden_replay.py` | protected replay locks | `project_turn_observation`, `golden_text_hash`, FEM path drift, opening bucket columns | **Intentional diagnostic** (not downstream to thin) |
| `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py` | classifier/dashboard rows | FEM bucket columns via `opening_fallback_evidence` + `golden_replay_projection` | **Intentional diagnostic** |
| `tests/test_turn_packet_stage_diff_integration.py` | stage-diff + FEM threading | Integration-visible FEM fields | **Downstream wiring** |
| `tests/test_answer_completeness_rules.py` | completeness + gate integration | Owns `answer_completeness_*` / `response_delta_*` consumer fields; uses `assert_no_boundary_reorder_repair`; occasional `final_emitted_source` in fixtures | **Downstream consumer** (registry) |
| `tests/test_response_delta_requirement.py` | 46 tests on `validate_response_delta` / gate layer | Owns delta semantics + `assert_response_delta_boundary_validate_only`; references `final_emitted_source` in strict-social details | **Downstream consumer** (registry) |
| `tests/test_run_scenario_spine_validation.py` | spine smoke paths | Imports `successful_opening_fem_meta`, gate fixtures on some branches | **Downstream wiring** (tooling smoke) |

### Repeated phrase / string checks

| File | Pattern / tests | Owner overlap | Classification |
| --- | --- | --- | --- |
| `tests/test_output_sanitizer.py` | Full procedural/scaffold/validator matrix (`test_sanitizer_*`) | **Owner** (post-process string cleanup) | Owner |
| `tests/test_social_exchange_emission.py` | 20+ tests with `for a breath`, `no certain answer`, `truth is still buried`, `scene holds` | **Owner** (strict-social legality application) | Owner |
| `tests/test_turn_pipeline_shared.py` | HTTP tests + helper unit tests `test_emission_smoke_helpers_*` | Sanitizer + social + visibility | **Downstream** (should use facade only) |
| `tests/helpers/emission_smoke_assertions.py` | Centralized smoke bans (subset of sanitizer/social) | Facade for downstream | **Wiring facade** |
| `tests/test_prompt_and_guard.py` | `for a breath` ban in uncertainty tests; validator voice tags | Pre-GM policy; doc says thin to smoke | **Mixed** downstream of sanitizer |
| `tests/test_narration_transcript_regressions.py` | `required_substrings=("for a breath", "voices shift")` on fallback paths | Gate + visibility semantics | **Transcript neighbor** — structural + prose pins |
| `tests/test_final_emission_gate.py` | Stock phrase inputs in gate replace paths (`no certain answer`, `truth is still buried`) | **Owner** | Owner |
| `tests/test_final_emission_visibility.py` | Visibility pool / stock semantics | **Owner** | Owner |
| `tests/test_synthetic_smoke.py` | `_FOLLOWUP_*_PATTERNS` regex lists | Sanitizer/social overlap | **Downstream** — consolidate to shared tuple or smoke helper |
| `tests/helpers/golden_replay_projection.py` | `final_text_has_scaffold_leakage` (regex `_SCAFFOLD_LEAK_RE`) | Replay layer | **Intentional** (different layer than HTTP smoke) |

### Imports / duplication from gate · fallback · FEM areas

| File | Imports from owner/fixture modules | Duplication risk |
| --- | --- | --- |
| `tests/test_final_emission_gate.py` | `final_emission_gate_fixtures`, `opening_fallback_evidence` | Correct owner + support fixtures |
| `tests/test_fallback_behavior_gate.py` | `response_type_contract` from fixtures | Gate-adjacent; owns fallback-behavior **at gate** |
| `tests/test_fallback_behavior_repairs.py` | `apply_final_emission_gate`, `response_type_contract` | **Downstream consumer** per module docstring |
| `tests/test_final_emission_opening_fallback.py` | gate fixtures + opening evidence | **Owner** for adapter/composer (22 tests) |
| `tests/test_narration_transcript_regressions.py` | `test_fallback_behavior_gate._fallback_contract`, `_answer_contract` | **Anti-pattern** — test-to-test import of gate contracts |
| `tests/test_final_emission_gate.py`, `test_c4_*`, `test_final_emission_boundary_no_semantic_repair.py` | `test_narrative_mode_output_validator._minimal_ctir_continuation` | Test-to-test import |
| `tests/test_golden_replay.py`, block S/T/U | `test_block_s_speaker_local_rebind_equivalence` | Equivalence harness coupling |
| `tests/test_answer_completeness_rules.py` | `test_social_escalation._session_with_pressure` | Test-to-test import |

---

## 2. Assertion ownership map

| Owned behavior | Owner file(s) | Downstream file(s) duplicating | Duplicated assertion / pattern |
| --- | --- | --- | --- |
| Final emission gate orchestration (layer order, `final_route`, `final_emitted_source`, repair-kind tables) | `tests/test_final_emission_gate.py` | `test_c4_narrative_mode_live_pipeline.py`, `test_narration_transcript_regressions.py`, `test_social_exchange_emission.py` (gate replace cases), `test_golden_replay.py`, `test_diegetic_fallback_narration.py`, `test_interaction_continuity_repair.py` | `fem.get("final_route") == "replaced"` / `"accept_candidate"`; exact `final_emitted_source` strings |
| Fallback behavior repair semantics | `tests/test_final_emission_repairs.py`, `tests/test_fallback_behavior_gate.py` | `tests/test_fallback_behavior_repairs.py`, `tests/test_narration_transcript_regressions.py` (imports `_fallback_contract`) | Full `fallback_behavior` contract dicts; meta materialization |
| Opening fallback selection / adapter | `tests/test_final_emission_opening_fallback.py`, `game/opening_deterministic_fallback.py` | `test_upstream_response_repairs.py`, `test_api_narration_path_selection.py`, `test_golden_replay.py`, `test_run_scenario_spine_validation.py` | `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` prose pin; `opening_fallback_source` |
| FEM projection / normalize / merge | `tests/test_final_emission_meta.py` | `test_turn_packet_stage_diff_integration.py`, classifier/dashboard/golden | `opening_fallback_owner_bucket`, `infer_accept_path_final_emitted_source_*` tables |
| Opening owner-bucket read mapping | `tests/test_opening_fallback_owner_bucket.py` | `test_failure_classifier.py`, `test_golden_replay.py`, `helpers/golden_replay_projection.py`, `helpers/failure_classifier.py` | `assert_fallback_owner_bucket` / bucket column equality — **intentional for replay diagnostics** |
| Visibility fallback semantics | `tests/test_final_emission_visibility.py`, `tests/test_final_emission_visibility_fallback.py` | `test_turn_pipeline_shared.py`, `test_social_exchange_emission.py` | `"for a breath, the scene holds"` / `"for a breath"` bans |
| Output sanitizer phrase matrix | `tests/test_output_sanitizer.py` | `test_turn_pipeline_shared.py` (`test_chat_final_output_sanitizer_blocks_adjudication_procedural_leak`), `test_prompt_and_guard.py` | `planner:`/`validator:`/`router`, `state exactly what you do`, `scene offers no clear answer yet`, procedural insufficiency |
| Strict-social emission legality | `tests/test_social_exchange_emission.py` | `test_turn_pipeline_shared.py`, `test_answer_completeness_rules.py`, `test_response_delta_requirement.py`, `test_broadcast_open_call_social.py` | Stock phrase bans; `question_resolution_rule_check` outcomes |
| Response delta boundary validate-only | `tests/test_response_delta_requirement.py` | `test_final_emission_boundary_convergence.py` | `response_delta_unsatisfied_at_boundary_no_reorder` via `assert_response_delta_boundary_validate_only` |
| Answer completeness consumer semantics | `tests/test_answer_completeness_rules.py` | (minimal `final_emitted_source` in fixtures only) | `answer_completeness_failed`, `assert_no_boundary_reorder_repair` — **mostly aligned** |
| Route legality (`choose_interaction_route`) | `tests/test_dialogue_routing_lock.py` | `test_turn_pipeline_shared.py` (HTTP parametrized routing) | Same route decisions via full pipeline |
| Open broadcast social classification | `game/interaction_context` + `tests/test_broadcast_open_call_social.py` | — | `should_route_social`, `open_social_solicitation` field matrix |
| Smoke / HTTP wiring | (no single owner; registry lists neighbors) | `test_turn_pipeline_shared.py`, `test_playability_smoke.py`, `test_gauntlet_regressions.py` | Non-empty text, repair tags, one-phrase hygiene |

---

## 3. Shared assertion facade inventory

| Path | Public API (functions/classes) | Current consumers | Suitable for downstream wiring? | Gap / missing helper |
| --- | --- | --- | --- | --- |
| `tests/helpers/emission_smoke_assertions.py` | `gm_response_stub`, `assert_player_text_present`, `assert_global_visibility_stock_absent`, `assert_no_internal_scaffold_labels`, `assert_no_advisory_prose`, `assert_no_unresolved_stock_phrases`, `assert_emission_repair_evidence`, `assert_response_type_meta`, `assert_social_grounding_smoke`, `assert_continuity_validation_failed_without_repair`, `assert_open_social_solicitation_route`, `assert_final_route_replaced_or_not_accept`, `assert_no_boundary_reorder_repair`, `assert_response_delta_boundary_validate_only` | `test_turn_pipeline_shared.py`, `test_answer_completeness_rules.py`, `test_response_delta_requirement.py`, `test_interaction_continuity_repair.py`, `test_broadcast_open_call_social.py`, `test_social_speaker_grounding.py`, `turn_pipeline_http_fixtures.py` | **Yes** — canonical downstream HTTP smoke surface | `assert_procedural_adjudication_smoke(low)` for turn_pipeline adjudication test; shared `PHRASE_SMOKE_*` constants tuple for synthetic_smoke |
| `tests/helpers/final_emission_gate_fixtures.py` | `response_type_contract`, `opening_validation_context`, `opening_gm_output`, `runner_strict_bundle`, `final_emission_meta_from_output`, `assert_final_emission_meta_contains`, `assert_fallback_owner_bucket`, `assert_opening_fallback_source`, `assert_sealed_fallback_owner_bucket`, `assert_visibility_pool`, `run_strict_social_motive_overclaim_gate_case` | 15+ files (gate, golden, block S/T/U, opening fallback, API narration, …) | **Partial** — harness/fixture yes; **assert_* bucket helpers are owner-adjacent**, not generic downstream | Split: keep harness here; move bucket asserts next to `opening_fallback_evidence.py` per Cycle AD note |
| `tests/helpers/opening_fallback_evidence.py` | `successful_opening_fem_meta`, `fail_closed_opening_fem_meta`, observed-field builders, `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` | gate, meta, golden, classifier, dashboard, scenario spine | **Yes** for FEM-shaped wiring evidence | — |
| `tests/helpers/golden_replay_projection.py` | `project_turn_observation`, `golden_text_hash`, `final_text_has_scaffold_leakage`, protected field registry | `test_golden_replay.py`, failure dashboard | **Replay only** — do not use for HTTP smoke | Optional doc-only link to `emission_smoke_assertions` scaffold subset |
| `tests/helpers/turn_pipeline_http_fixtures.py` | `_gm_response`, `_seed_runner_dialogue_context`, … | `test_playability_smoke.py`, others | **Yes** | Finish migrating imports off `test_turn_pipeline_shared` |
| `tests/helpers/transcript_runner.py` | bootstrap / snapshot | transcript modules | Wiring | — |
| `tests/helpers/failure_classifier.py` | classify + row validation | golden, dashboard | Diagnostic | — |
| `tests/validation_coverage_registry.py` | coverage metadata | audit tools | N/A | — |

**Facade consumer count (import grep):** `emission_smoke_assertions` → **7** modules; `final_emission_gate_fixtures` → **15+**; `opening_fallback_evidence` → **7+**.

---

## 4. Duplication hotspots (ranked by maintenance cost)

| Rank | Hotspot | Duplicated files | Duplicated pattern | Retain legality in | Reduce to wiring in | Recommended move |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | HTTP phrase-ban matrix | `test_turn_pipeline_shared.py`, `test_output_sanitizer.py`, `test_social_exchange_emission.py`, `emission_smoke_assertions.py` | Procedural/scaffold/stock phrase `assert ... not in low` | `test_output_sanitizer.py` + `test_social_exchange_emission.py` | `test_turn_pipeline_shared.py` | AL2: Replace inline bans in `test_chat_final_output_sanitizer_blocks_adjudication_procedural_leak` with one `assert_procedural_adjudication_smoke` helper; keep single HTTP test per route class |
| 2 | Global visibility stock | `test_final_emission_visibility.py`, `test_social_exchange_emission.py`, `test_turn_pipeline_shared.py`, `test_synthetic_smoke.py` | `"for a breath"` / `"scene holds"` | Visibility + social owners | Pipeline, synthetic smoke | AL2: Pipeline already uses `assert_global_visibility_stock_absent`; migrate `test_synthetic_smoke` regex to import shared constant |
| 3 | `final_route` exact enum | `test_final_emission_gate.py`, `test_c4_narrative_mode_live_pipeline.py`, `test_golden_replay.py`, `test_social_exchange_emission.py` | `final_route == "replaced"` / `"accept_candidate"` | Gate | C4, social gate-integration cases where branch not under test | AL3: Use `assert_final_route_replaced_or_not_accept` in C4 unless asserting accept path |
| 4 | Scaffold leak triple | `test_output_sanitizer.py`, `emission_smoke_assertions.py`, `golden_replay_projection.final_text_has_scaffold_leakage` | `planner:` / `validator:` / `router` | Sanitizer (full matrix); replay (regex) | HTTP smoke helper only | AL1: Document three-layer split; **do not merge** replay regex into HTTP helper |
| 5 | Opening FEM bucket columns | `test_opening_fallback_owner_bucket.py`, `test_failure_classifier.py`, `test_golden_replay.py`, `golden_replay_projection` | `opening_fallback_owner_bucket` equality | Owner-bucket + meta | Classifier/golden | **No reduction** in replay/classifier (intentional); AL4 doc-only |
| 6 | Fallback contract dicts | `test_fallback_behavior_gate.py`, `test_narration_transcript_regressions.py` | `_fallback_contract`, `_answer_contract` test-to-test import | `test_fallback_behavior_gate.py` | Transcript | AL1: Extract contracts to `tests/helpers/fallback_behavior_fixtures.py` |
| 7 | Open-call route field matrix | `test_broadcast_open_call_social.py` | Full `resolve_directed_social_entry` field asserts | Engine + broadcast owner | — | AL2: Keep `assert_open_social_solicitation_route`; drop redundant `question_resolution_rule_check` table duplication if outcome smoke suffices |
| 8 | Response-delta boundary reason | `test_response_delta_requirement.py`, `test_final_emission_boundary_convergence.py` | `response_delta_unsatisfied_at_boundary_no_reorder` | `test_response_delta_requirement.py` | Boundary convergence | Already on facade — verify convergence uses helper only |
| 9 | `response_type_contract` local defs | `test_fallback_behavior_gate.py`, `test_fallback_behavior_repairs.py` | Local vs `final_emission_gate_fixtures.response_type_contract` | Gate fixtures | Both fallback tests | AL1: Ensure both use shared `response_type_contract` only (partially done) |
| 10 | Test-to-test HTTP imports | `test_playability_smoke.py`, `test_start_campaign_api.py`, … → `test_turn_pipeline_shared` | Shared seeds/`_chat` | `turn_pipeline_http_fixtures.py` | Consumers | AL1: Complete fixture extraction (started in AD) |

---

## 5. Safe implementation sequence (Cycle AL blocks)

| Block | Purpose | Files likely touched | Tests to run | Parallel? | Risk |
| --- | --- | --- | --- | --- | --- |
| **AL1** | Fixture extraction + fallback contract helper; eliminate test-to-test imports for HTTP/fallback | New `tests/helpers/fallback_behavior_fixtures.py` (optional), `test_narration_transcript_regressions.py`, `test_turn_pipeline_shared.py` consumers, `test_fallback_behavior_*.py` | `test_fallback_behavior_gate.py`, `test_fallback_behavior_repairs.py`, `test_narration_transcript_regressions.py`, `test_playability_smoke.py`, `test_start_campaign_api.py` | Yes with AL4 (docs) | **Low** |
| **AL2** | Downstream phrase thinning — pipeline + synthetic smoke → `emission_smoke_assertions` | `test_turn_pipeline_shared.py`, `test_synthetic_smoke.py`, extend `emission_smoke_assertions.py` | `test_turn_pipeline_shared.py`, `test_output_sanitizer.py` (regression), `test_synthetic_smoke.py` | After AL1 | **Medium** |
| **AL3** | FEM route smoke thinning — `final_route` exact locks → `assert_final_route_replaced_or_not_accept` where branch not under test | `test_c4_narrative_mode_live_pipeline.py`, selective cases in `test_social_exchange_emission.py`, `test_interaction_continuity_repair.py` | C4 module + AD subset: gate/meta/visibility/response_delta/answer_completeness/turn_pipeline | After AL2 | **Medium** |
| **AL4** | Registry + facade documentation — formalize AL downstream list; optional shared `PHRASE_SMOKE_STOCK_TUPLE` constant (doc-linked, not merged with replay) | `test_ownership_registry.py`, `emission_smoke_assertions.py` docstring, `tests/README_TESTS.md` | `test_ownership_registry.py`, `py -3 tools/test_audit.py` | Yes with AL1 | **Low** |
| **AL5** | Broadcast + social downstream migration completion | `test_broadcast_open_call_social.py`, `test_social_answer_candidate.py` (if phrase asserts remain), any AG-listed unmigrated files | `test_broadcast_open_call_social.py`, `test_social_speaker_grounding.py` | After AL2 | **Low–medium** |
| **AL6** | Deletion pass — remove redundant inline asserts only after AL2–AL3 green | Parametrized duplicates in `test_turn_pipeline_shared.py`, redundant FEM literals in classifier tests covered by `opening_fallback_evidence` | AD subset (~809 tests) + `pytest -m golden_replay -q` | **No** — after AL2–AL3 | **Medium–high** |

**Suggested verification loop (from Cycle AD, still valid):**

```powershell
py -3 -m pytest tests/test_ownership_registry.py -q
py -3 -m pytest tests/test_turn_pipeline_shared.py tests/test_answer_completeness_rules.py tests/test_response_delta_requirement.py tests/test_output_sanitizer.py tests/test_social_exchange_emission.py tests/test_c4_narrative_mode_live_pipeline.py -q --tb=line
py -3 -m pytest -m golden_replay -q
```

---

## 6. Files to pass back to ChatGPT

Minimum set to generate AL implementation blocks (ordered):

1. **This recon:** `docs/cycles/cycle_al_downstream_assertion_convergence_recon_2026-06-01.md`
2. **Governance:** `tests/test_ownership_registry.py` (RESPONSIBILITY_REGISTRY + downstream_consumer fields)
3. **Downstream smoke facade:** `tests/helpers/emission_smoke_assertions.py`
4. **Primary downstream target:** `tests/test_turn_pipeline_shared.py` (largest mixed suite; 70 tests)
5. **Gate owner (do not thin):** `tests/test_final_emission_gate.py` (reference only — first ~200 lines + any helper imports)
6. **Phrase owners:** `tests/test_output_sanitizer.py`, `tests/test_social_exchange_emission.py` (module docstrings + representative `test_sanitizer_*` / `test_strict_social_pipeline_forbids_*`)
7. **Consumer owners:** `tests/test_answer_completeness_rules.py`, `tests/test_response_delta_requirement.py` (module docstrings)
8. **FEM / replay intentional overlap:** `tests/helpers/opening_fallback_evidence.py`, `tests/helpers/golden_replay_projection.py` (first ~200 lines), `tests/test_opening_fallback_owner_bucket.py`
9. **HTTP fixtures:** `tests/helpers/turn_pipeline_http_fixtures.py`
10. **Prior recon for block numbering context:** `docs/cycles/cycle_ad_test_authority_consolidation_recon_2026-05-31.md`, `docs/cycles/cycle_ae_change_locality_optimization_closure_2026-05-31.md`

**Do not pass whole repo.** Skip full `test_final_emission_gate.py` (6715 lines) unless editing gate — use registry + fixtures instead.

---

## Summary

Downstream convergence work is **partially done** (Cycle AD/AE): `emission_smoke_assertions.py` and registry `downstream_consumer_suites` exist, and `test_turn_pipeline_shared.py` documents HTTP-only scope. Remaining pain is **concentrated**:

- **`test_turn_pipeline_shared.py`** still inlines sanitizer-grade phrase bans on adjudication/social HTTP paths despite helper coverage elsewhere.
- **`test_c4_narrative_mode_live_pipeline.py`** and some social/gate-integration tests still lock exact `final_route` values.
- **`test_synthetic_smoke.py`** maintains a parallel phrase regex matrix.
- **Test-to-test imports** (`narration_transcript` ← `fallback_behavior_gate`, consumers ← `turn_pipeline_shared`) obscure ownership and block safe thinning.

Cycle AL should treat **golden replay / classifier FEM bucket columns as intentional**, thin **HTTP and consumer suites** via the existing smoke facade, and avoid merging replay scaffold detection with HTTP smoke helpers.
