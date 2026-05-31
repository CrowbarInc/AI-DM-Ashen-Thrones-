# Cycle R — Test Fanout Reduction Recon

**Date:** 2026-05-30  
**Scope:** Recon only — no test or production changes.  
**Ground truth:** Live `pytest --collect-only` → **4247 tests** across **~260+ modules**; governed ownership in `tests/test_ownership_registry.py` (15 responsibility groups, **~30 files** with explicit registry positions). Stale inventory snapshot in `tests/test_inventory.json` (`generated_utc`: 2026-04-25, **3419 items**) — regenerate before relying on per-file counts.

---

## 1. Summary

The suite is **governed but broad**. Machine-checked ownership exists for fifteen high-risk seams (gate orchestration, validators, repairs, prompt bundle, sanitizer, strict-social emission, transcript, gauntlet, etc.), yet **~230 test modules sit outside the registry** and assert downstream behavior through integration, replay, and transcript harnesses.

**Fanout problem:** The same downstream artifacts — `final_route`, FEM owner buckets, procedural fallback phrases, `question_resolution_rule_check` outcomes, visibility stock fallbacks, speaker-contract reason codes — are re-locked in many files because different harness depths (unit → gate → API → replay) each need *some* signal, but several files restate **full** assertion matrices where a **smoke or presence check** would suffice given an identified owner.

**Reduction safety:** Reduction is **safe in small blocks** when:
- The **canonical owner** is clear (registry + module docstrings + `TEST_AUDIT.md` governance notes).
- The assertion family is **metadata packaging** or **phrase-level legality** already owned elsewhere.
- **Golden replay / long-session / structural-invariant** tests remain untouched.

**Not safe to bulk-reduce:** `tests/test_golden_replay.py` (53 collected items, `@pytest.mark.golden_replay`), frontier-gate 25-turn replays, failure classifier/dashboard projection contracts, and cross-layer phrase locks that guard **different routes** (HTTP vs pure table vs gate unit).

Prior consolidation (Blocks A–D, C3–C4, SE2-R, FG2-R, GC2-R, TD2-R, RT7-R) already thinned prompt/sanitizer and strict-social splits; **Cycle R targets the remaining cross-layer fanout**, especially metadata projection, passive phrase bans, and helper leakage from owner modules.

---

## 2. Ownership Layer Map

**Layer legend**

| Layer | Meaning in this repo |
| --- | --- |
| **Owner** | Practical direct-owner suite in `test_ownership_registry.py` or `TEST_AUDIT.md` canonical table |
| **Downstream** | Consumes owner boundary; may assert emitted outcomes, not derivation/orchestration order |
| **Smoke** | Thin wiring / presence / one-phrase check |
| **Replay / integration** | Full-stack or multi-turn protection; often intentionally redundant at observation layer |

| Test File | Apparent Layer | Primary Owner Concern | Downstream/Smoke Concerns Mixed In | Notes |
| --- | --- | --- | --- | --- |
| `tests/test_ownership_registry.py` | Governance | Registry + inventory schema v2 | — | 15 groups; neighbors mostly empty for downstream_consumer |
| `tests/test_final_emission_gate.py` | **Owner** (gate) | `apply_final_emission_gate` orchestration, layer order, continuity-adjacent gate steps | Opening fallback integration, strict-social coercions, FEM merge | ~100 test defs; exports `_runner_strict_bundle`, `_opening_gm_output` (helper leakage) |
| `tests/test_final_emission_validators.py` | **Owner** (gate) | Validator semantics, referent clarity layer | — | RT7-R co-owner for post-GM referent check |
| `tests/test_final_emission_repairs.py` | **Owner** (gate) | Repair derivation, `_apply_fallback_behavior_layer` | — | FR1-R |
| `tests/test_final_emission_meta.py` | **Owner** (meta read-side) | FEM schema, normalization, projection helpers | Opening owner-bucket projection | Not in registry; de facto owner for meta packaging |
| `tests/test_opening_fallback_owner_bucket.py` | **Owner** (meta mapping) | `opening_fallback_owner_bucket_from_meta` read mapping | — | Explicit split from gate/replay |
| `tests/test_final_emission_visibility.py` | **Owner** (visibility legality) | Player-facing visibility / first-mention / referential clarity | FEM `final_route`, sealed bucket **smoke** | Module docstring: gate owns ordering only |
| `tests/test_output_sanitizer.py` | **Owner** (gate) | Post-GM string cleanup, procedural phrase bans | — | Canonical phrase-level locks |
| `tests/test_prompt_and_guard.py` | **Owner-adjacent** (pre-GM) | Retry prompts, guard policy, validator-voice GM layer | Legality/sanitizer phrase overlap (partially thinned Block C3) | 56 collected; not registry direct owner |
| `tests/test_prompt_context.py` | **Owner** (engine/planner) | Prompt bundle / exported contract accessors | Response-policy materialization smoke | PC2-R |
| `tests/test_response_policy_contracts.py` | **Owner** (engine) | Shipped response-policy bundle | — | RP2-R |
| `tests/test_social_exchange_emission.py` | **Owner** (gate) | Strict-social emission, first-sentence / question-resolution tables | `final_route` on application paths | SE2-R; 81 collected |
| `tests/test_social.py` | **Owner** (engine) | `resolve_social_action` engine shape | Strict-social **smoke only** | Block C4 docstring |
| `tests/test_speaker_contract_enforcement.py` | **Transcript neighbor** | Speaker contract enforcement stories | `canonical_speaker_rewrite` codes | Registry: transcript_suite under social emission |
| `tests/test_turn_pipeline_shared.py` | **Downstream / smoke** | Full `/api/chat` + `/api/action` stack | Routing, continuity, legality phrase bans, FEM fields | Explicit docstring: not gate orchestration owner; 62 collected |
| `tests/test_directed_social_routing.py` | **Owner** (routing table) | Directed-social precedence, vocative, segmentation | HTTP smoke | Block 3 routing split |
| `tests/test_dialogue_routing_lock.py` | **Owner** (pure routing) | `choose_interaction_route` table | — | No TestClient |
| `tests/test_interaction_continuity_repair.py` | **Downstream** | Continuity repair **consumer** outcomes | `final_route` presence | GC2-R; uses public `apply_final_emission_gate` only |
| `tests/test_interaction_continuity_validation.py` | **Downstream** | Continuity validation consumption | — | |
| `tests/test_interaction_continuity_speaker_bridge.py` | **Downstream** | Bridge-shaped failure consumption | — | |
| `tests/test_c4_narrative_mode_live_pipeline.py` | **Smoke** | C4 narrative-mode wiring | `final_route` smoke | Registry: gpt_expression smoke_suite |
| `tests/test_answer_completeness_rules.py` | **Downstream** | Answer-completeness / response-delta consumer | Repeated `final_route == "replaced"` | Prompt-adjacent per PC2-R |
| `tests/test_golden_replay.py` | **Replay protection** | Observation/projection/drift contracts | Route, speaker, fallback, FEM fields | **Not in inventory**; 53 tests; do not reduce |
| `tests/test_failure_classifier.py` | **Owner** (diagnostics) | Replay failure routing / row shape | FEM bucket fields | Pairs with `helpers/failure_classifier.py` |
| `tests/test_failure_dashboard_controlled_failures.py` | **Smoke / contract** | Dashboard row rendering on known-bad shapes | FEM bucket columns | |
| `tests/test_narration_transcript_regressions.py` | **Transcript** | Multi-turn narration sequencing | Gate-adjacent outcomes | Registry: transcript_suite ×2 |
| `tests/test_transcript_regression.py` | **Owner** (transcript) | General play-loop sequencing | — | |
| `tests/test_social_emission_quality.py` | **Harness** | Multi-turn quality / grounding | Gate meta smoke | Renamed from `test_transcript_*` (C4) |
| `tests/test_stage_diff_telemetry.py` | **Owner** | Stage-diff helper semantics | — | TD2-R |
| `tests/test_turn_packet_stage_diff_integration.py` | **Downstream** | Turn-packet + gate consumer | `"final_route" in fem` presence | |
| `tests/test_clue_lead_registry_integration.py` | **Owner** (engine) | Clue↔lead registry wiring | — | Lead/clue batch **deferred** |
| `tests/test_referent_tracking.py` | **Owner** (engine) | Full referent artifact construction | — | RT7-R |
| `tests/test_empty_social_retry_regressions.py` | **Owner** (retry cluster) | Retry metadata, `targeted_retry_terminal`, `final_route` | `/api/chat` integration | Repair cluster closed |
| `tests/test_contextual_minimal_repair_regressions.py` | **Owner** (repair cluster) | Branch-specific repair legality | — | |
| `tests/test_broadcast_open_call_social.py` | **Mixed** | Broadcast open-call social behavior | Direct `question_resolution_rule_check` call | Owner overlap with `test_social_exchange_emission.py` |

**Files where layers are mixed (highest risk):**

- `test_turn_pipeline_shared.py` — routing + continuity + sanitizer phrase bans + emission metadata in one HTTP module.
- `test_final_emission_gate.py` — orchestration owner **and** shared fixture exports consumed by replay/upstream tests.
- `test_final_emission_visibility.py` — visibility owner **and** FEM projection smoke (`sealed_fallback_owner_bucket`, `final_route`).
- `test_prompt_and_guard.py` — pre-GM owner **and** residual legality/sanitizer theme tags (29 legality/sanitizer feature hits in inventory).
- `test_golden_replay.py` — replay owner **and** imports gate-private fixtures from `test_final_emission_gate.py` / block-S harness.

---

## 3. Assertion Overlap Families

| Family | Files Involved | Assertion Pattern | Likely Canonical Owner | Duplicate/Valuable/Unclear | Recommendation |
| --- | --- | --- | --- | --- | --- |
| **Procedural / instructional phrase bans** | `test_output_sanitizer.py`, `test_prompt_and_guard.py`, `test_turn_pipeline_shared.py`, `test_social_answer_candidate.py`, `test_social_speaker_grounding.py`, transcript modules | `assert "state exactly what you do" not in low`, `no answer presents itself`, `nothing in the scene points` | `test_output_sanitizer.py` | Owner/downstream overlap (partially thinned C3) | **Narrow** pipeline/transcript to absence smoke or tag checks; keep full phrase matrix in sanitizer |
| **Global visibility stock fallback** | `test_output_sanitizer.py`, `test_final_emission_visibility.py`, `test_turn_pipeline_shared.py`, `test_social_answer_candidate.py`, `test_scene_entity_lock.py` (thinned) | `scene holds` / `voices shift around you` banned or replaced | `test_final_emission_visibility.py` (semantic); sanitizer (string) | Duplicate downstream + valuable replay in pipeline for **HTTP path** | Pipeline: keep **one** HTTP smoke per route class; drop duplicate substring checks where visibility owner covers replace path |
| **FEM `final_route`** | `test_final_emission_gate.py` (many), `test_social_exchange_emission.py`, `test_c4_narrative_mode_live_pipeline.py`, `test_answer_completeness_rules.py`, `test_response_delta_requirement.py`, `test_interaction_continuity_repair.py`, `test_diegetic_fallback_narration.py`, `test_empty_social_retry_regressions.py`, `test_turn_packet_stage_diff_integration.py` | `assert fem.get("final_route") == "replaced"` / `"accept_candidate"` | `test_final_emission_gate.py` for orchestration semantics; `test_final_emission_meta.py` for read/normalize | Owner/downstream overlap | Downstream: assert **route class** or key presence unless testing a **distinct branch**; gate keeps exact route tables |
| **Sealed / visibility fallback owner buckets** | `test_opening_fallback_owner_bucket.py`, `test_final_emission_meta.py`, `test_final_emission_visibility.py`, `test_golden_replay.py`, `test_failure_classifier.py`, `test_failure_dashboard_controlled_failures.py`, `test_run_scenario_spine_validation.py` | `sealed_fallback_owner_bucket`, `visibility_fallback_*` projection | `test_opening_fallback_owner_bucket.py` + `test_final_emission_meta.py` (projection); golden replay (end-to-end observation) | **Valuable replay coverage** in golden/classifier; duplicate in visibility gate integration | Do **not** remove golden/classifier locks; narrow visibility file to **mapping smoke** only |
| **Opening fallback authorship / upstream-prepared** | `test_final_emission_gate.py`, `test_upstream_response_repairs.py`, `test_diegetic_fallback_narration.py`, `test_api_narration_path_selection.py`, `helpers/opening_fallback_evidence.py`, `test_golden_replay.py` | `opening_fallback_authorship_source`, `opening_recovered_via_fallback`, expected frontier gate fallback text | Gate (selection/orchestration); upstream repairs (packaging); meta (projection) | Owner/downstream overlap + valuable replay | Consolidate **fixtures** via `opening_fallback_evidence.py`; keep gate owner tests for orchestration |
| **`question_resolution_rule_check` / first-sentence legality** | `test_social_exchange_emission.py` (large table), `test_prompt_and_guard.py` (smoke), `test_broadcast_open_call_social.py` | Direct `question_resolution_rule_check(...)` reasons / first-sentence flags | `test_social_exchange_emission.py` | Duplicate downstream in broadcast | Move broadcast checks to **outcome smoke** (pass/fail + one reason code) or parametrize from owner table |
| **Speaker contract / `canonical_speaker_rewrite`** | `test_speaker_contract_enforcement.py`, `test_final_emission_gate.py`, `test_turn_pipeline_shared.py`, `test_golden_replay.py`, block-S/T/U equivalence suites | `speaker_contract_enforcement_reason`, rewrite family codes | `test_speaker_contract_enforcement.py` + gate orchestration integration | **Valuable** when route/speaker/continuity differ (replay, HTTP) | Pipeline: keep HTTP locks; gate: keep ordering; do not dedupe golden structural invariants |
| **Strict-social `final_route` on emission application** | `test_social_exchange_emission.py`, `test_strict_social_emergency_fallback_dialogue.py`, `test_social_emission_quality.py` | Application-layer replaced/accept paths | `test_social_exchange_emission.py` | Owner/downstream overlap | Emergency fallback file stays **retry-terminal / compatibility**; narrow quality harness to harness metrics not legality tables |
| **Interaction continuity gate steps** | `test_final_emission_gate.py`, `test_fallback_behavior_gate.py`, `test_interaction_continuity_*.py`, `helpers/post_speaker_finalize_probe.py` | `_apply_interaction_continuity_emission_step`, `_attach_interaction_continuity_validation` | `test_final_emission_gate.py` | Owner/downstream overlap (GC2-R residue) | Repair/validation suites: **public outcomes only**; remove private step imports if any remain |
| **Referent clarity (Objective #7 vs player-facing)** | `test_referent_tracking.py`, `test_prompt_context.py`, `test_final_emission_validators.py`, `test_final_emission_gate.py`, `test_referential_clarity_*.py`, `helpers/objective7_referent_fixtures.py` | Full artifact vs compact mirror vs player-facing clarity | Split per RT7-R | Intentionally **orthogonal** seams | Do not merge; optional shared stubs already exist |
| **Stage-diff telemetry fields** | `test_stage_diff_telemetry.py`, `test_turn_packet_stage_diff_integration.py`, `test_narrative_authenticity_aer4.py` | Snapshot/diff helper semantics vs packet consumer | `test_stage_diff_telemetry.py` | Downstream consumer | Integration file: presence + consumer framing only |
| **Response-policy bundle materialization** | `test_response_policy_contracts.py`, `test_fallback_shipped_contract_propagation.py`, `test_interaction_continuity_contract.py`, `test_final_emission_validators.py` | `materialize_response_policy_bundle()` shapes | `test_response_policy_contracts.py` | Passive overlap in continuity/validator suites | Narrow continuity suites to **consumption** assertions |
| **Cross-file duplicate test base names** | `test_narrative_planning.py` + `test_referent_tracking.py`; evaluator env-guard smokes | `test_deterministic_json_stable`, `test_version_constant`, `test_maybe_attach_respects_env` | Per-module contract surface | **Intentional** (allowlisted) | Preserve; do not merge modules |

---

## 4. Structurally Identical Helpers

| Helper/Fixture Pattern | Files Involved | Same Structure? | Same Semantics? | Merge Recommendation | Risk |
| --- | --- | --- | --- | --- | --- |
| **`_opening_gm_output()` / `_runner_strict_bundle()`** | Defined in `test_final_emission_gate.py`; imported by `test_golden_replay.py`, `test_upstream_response_repairs.py`, `test_diegetic_fallback_narration.py`, `test_api_narration_path_selection.py`, `test_run_scenario_spine_validation.py`, `test_block_s/t/u_*.py`, `test_final_emission_boundary_convergence.py` | Yes | Mostly yes (strict-social / opening scenarios) | **Extract** to `tests/helpers/final_emission_gate_fixtures.py` (or extend `opening_fallback_evidence.py`); gate tests remain semantic owner | Low — import-only move; preserves ownership |
| **`_gm_response(text, tags, debug_notes)`** | `test_golden_replay.py`, `test_lead_lifecycle_block3_transcript_regression.py`, others | Yes | Yes (minimal GM dict) | Merge into `tests/helpers/synthetic_fake_gm.py` or small `gm_output_stubs.py` | Low |
| **`successful_opening_fem_meta` / `fail_closed_opening_fem_meta`** | `helpers/opening_fallback_evidence.py`; inline duplicates in classifier/dashboard/golden tests | Yes | Yes | **Prefer helper** everywhere; remove inline FEM dict literals in downstream tests | Low |
| **`make_valid_dialogue_social_plan` / `attach_dialogue_social_plan_to_resolution`** | `helpers/dialogue_social_plan.py` (canonical); used across dialogue plan / strict-social / golden tests | Yes | Yes | **Already merged** — preserve; do not re-inline | N/A |
| **`_base_visibility_bundle` / `_rich_scene_visibility_bundle`** | `test_final_emission_visibility.py` only (local) | — | — | Optional extract if gate/visibility convergence tests multiply | Low |
| **`_seed_scene_with_runner` / directed social seeds** | `test_directed_social_routing.py`, `test_golden_replay.py`, `test_broadcast_open_call_social.py` | Near-identical | Scene-specific variants | Extract shared **runner+guard seed** to `tests/helpers/directed_social_seeds.py` if thinning seeds replay drift | Medium — replay tests sensitive to fixture shape |
| **`classify_replay_failure` / dashboard row builders** | `helpers/failure_classifier.py`, `helpers/failure_dashboard_report.py`; consumed by `test_failure_classifier.py`, `test_failure_dashboard_controlled_failures.py`, golden replay | Yes | Classifier owns semantics; dashboard owns rendering | **Preserve split** — classifier ≠ dashboard owner | Low |
| **`run_golden_replay` / `assert_golden_turn_observation`** | `helpers/golden_replay.py`; `test_golden_replay.py` | Yes | Replay observation contract | **Do not merge into gate helpers** — intentional replay boundary | High if merged incorrectly |
| **`objective7_referent_fixtures`** | `helpers/objective7_referent_fixtures.py`; 6+ test consumers | Yes | JSON-safe artifact stubs | **Preserve**; extend rather than duplicate stubs in gate/validator tests | Low |
| **`_minimal_ctir()` builders** | `test_planner_input_manifest_ctir.py`, `test_narrative_planning_transition_node.py`, `test_c4_narrative_mode_live_pipeline.py`, many CTIR tests | Near-identical | Scenario-specific fields | Optional `tests/helpers/minimal_ctir.py` for generic shell; keep scenario fields local | Medium |
| **Imports of gate **tests** from other tests** | `test_gauntlet_regressions.py` imports `test_strict_social_gate_repairs_*` from gate module | Unusual | Reuses test function as helper | Replace with shared **fixture function** in helpers (not test-to-test import) | Medium — pytest collection coupling |

---

## 5. Passive Overlap Families

| Passive Overlap | Files Involved | Why It Is Passive | Can Narrow? | Recommended Treatment |
| --- | --- | --- | --- | --- |
| **Phrase bans while testing routing** | `test_turn_pipeline_shared.py` | Primary concern is HTTP route/resolution; phrase checks guard player-visible output | Yes | Keep **one** ban smoke per parametrized block; rely on `test_output_sanitizer.py` for phrase matrix |
| **FEM `final_route` while testing response-delta / answer completeness** | `test_answer_completeness_rules.py`, `test_response_delta_requirement.py` | Primary concern is delta semantics / completeness rules | Yes | Assert `response_delta` / completeness fields; replace exact `final_route` with `in {"replaced","accept_candidate"}` smoke |
| **Gate meta while testing C4 wiring** | `test_c4_narrative_mode_live_pipeline.py` | Primary concern is narrative-mode orchestration smoke | Partially | Keep `final_route` **smoke** (already documented); do not add new legality tables here |
| **Continuity repair + `final_route`** | `test_interaction_continuity_repair.py` | Tests repair **effects** on emitted output | Yes | Keep repair outcome assertions; `final_route` → optional presence only |
| **Speaker grounding + visibility stock ban** | `test_social_speaker_grounding.py` | Tests speaker grounding consumption | Yes | Drop redundant `scene holds` ban if sanitizer/visibility owners cover |
| **Social answer candidate + stock fallback** | `test_social_answer_candidate.py` | Tests candidate selection logic | Yes | Use shorter marker assertion (already partially done); not full stock sentence lock |
| **Broadcast social + question_resolution table** | `test_broadcast_open_call_social.py` | Tests open-call broadcast behavior | Yes | Single check: `check["ok"]` or one reason code, not full reason list |
| **Failure dashboard + FEM bucket columns** | `test_failure_dashboard_controlled_failures.py` | Tests dashboard **rendering** | No (contract lock) | Passive for classifier semantics but **active** for operator UX — preserve column presence |
| **Golden replay projection unit tests** | `test_golden_replay.py` (non-replay tests) | Tests projection helper semantics | No | These **are** the owner for observation shape — not passive |

---

## 6. Replay Coverage To Preserve

**Do not reduce assertions in these tests/modules:**

| Test / group | Why preserve |
| --- | --- |
| **`test_golden_replay.py`** — all `@pytest.mark.golden_replay` (53 items) | Owns replay observation, drift classification, rerun scorecards, protected structural invariants |
| **Structural replay scenarios** | `test_golden_replay_directed_npc_question_structural_invariants`, `vocative_override_*`, `wrong_speaker_strict_social_*`, `thin_answer_action_outcome_*`, `sanitizer_scaffold_leakage_*`, `lead_followup_with_dialogue_lock_*` |
| **Long-session replays** | `test_golden_replay_frontier_gate_social_inquiry_25_turn_*`, `frontier_gate_direct_intrusion_25_turn_*`, `scenario_spine_three_branch_structural_smoke` |
| **Golden projection locks** | Owner bucket projection (`upstream_prepared`, `sealed_gate`, `strict_social_sealed`), visibility fallback evidence, sanitizer lineage, neutral speaker grounding bridge — **different routes/fallbacks** |
| **`test_failure_classifier.py`** + **`test_failure_classification_contract.py`** | Routes replay failures to investigate-first paths; FEM bucket validation is diagnostic contract |
| **`test_failure_dashboard_controlled_failures.py`** | Controlled probes for operator reports |
| **`test_run_scenario_spine_validation.py`** (opening FEM scenarios) | Spine eval + opening fallback cross-layer locks |
| **Transcript / gauntlet harnesses** | `test_transcript_regression.py`, `test_narration_transcript_regressions.py`, `test_lead_lifecycle_block3_transcript_regression.py`, `test_mixed_state_recovery_regressions.py`, `test_transcript_gauntlet_*.py` — **sequencing** assertions; only thin **duplicate phrase** locks (already started C4) |
| **Routing cross-layer locks** | Same phrase in `test_dialogue_routing_lock.py` **and** `test_turn_pipeline_shared.py` when layers differ (table vs HTTP) — documented intentional |
| **Repair/retry cluster** | `test_empty_social_retry_regressions.py` + `test_contextual_minimal_repair_regressions.py` — cluster **closed**; phrase split by branch is intentional |
| **Speaker equivalence blocks** | `test_block_s_speaker_local_rebind_equivalence.py`, `test_block_t_*`, `test_block_u_*` — regression equivalence, not fanout targets |

**Duplicated-looking but valuable (different behavior):**

- `final_route == "replaced"` in **strict-social gate** vs **continuity repair** vs **answer-completeness** — different triggering inputs and repair layers.
- `canonical_speaker_rewrite` in **speaker contract transcript** vs **pipeline HTTP** vs **golden replay** — different speaker/route/continuity context.
- Opening owner buckets in **unit mapping** vs **golden observed_turn projection** vs **classifier row** — different layers (read helper vs end-to-end vs diagnostics).

---

## 7. Proposed Implementation Blocks

### R1: Gate fixture extraction + test-to-test import cleanup

- **Goal:** Stop `test_final_emission_gate.py` from being a helper hub; preserve gate as orchestration owner.
- **Files touched:** `tests/helpers/final_emission_gate_fixtures.py` (new), `tests/test_final_emission_gate.py`, `tests/test_golden_replay.py`, `tests/test_upstream_response_repairs.py`, `tests/test_diegetic_fallback_narration.py`, `tests/test_api_narration_path_selection.py`, `tests/test_run_scenario_spine_validation.py`, `tests/test_block_s/t/u_*.py`, `tests/test_final_emission_boundary_convergence.py`, `tests/test_gauntlet_regressions.py`
- **Overlap family:** Opening/strict-social fixture duplication; test-to-test imports
- **Current owner:** `test_final_emission_gate.py` (semantics); fixtures become **support residue**
- **Downstream affected:** All importers listed above
- **Remove/narrow/move:** Move `_opening_gm_output`, `_runner_strict_bundle`, `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` to helper; replace gauntlet's import of gate **test function** with helper callable
- **Helpers:** Merge into new helper module; keep `opening_fallback_evidence.py` for FEM-shaped evidence
- **Do not touch:** Gate orchestration assertions; golden replay structural invariants
- **Test command(s):** `py -3 -m pytest tests/test_final_emission_gate.py tests/test_golden_replay.py -q` then `py -3 -m pytest tests/test_upstream_response_repairs.py tests/test_diegetic_fallback_narration.py tests/test_api_narration_path_selection.py -q`
- **Risk:** **Low**

### R2: Passive phrase-ban thinning in HTTP / downstream suites

- **Goal:** Reduce cross-layer legality fanout without weakening sanitizer owner.
- **Files touched:** `tests/test_turn_pipeline_shared.py`, `test_social_speaker_grounding.py`, `test_social_answer_candidate.py`, `test_broadcast_open_call_social.py` (question_resolution narrowing)
- **Overlap family:** Procedural phrase bans; global visibility stock; question_resolution table duplication
- **Current owner:** `test_output_sanitizer.py` (phrases); `test_social_exchange_emission.py` (question_resolution); `test_final_emission_visibility.py` (visibility semantic)
- **Downstream affected:** Listed files
- **Remove/narrow/move:** Collapse repeated `scene holds` / instructional phrase asserts to **one smoke per HTTP scenario**; broadcast → outcome-level check
- **Helpers:** None required
- **Do not touch:** `test_output_sanitizer.py` canonical tables; golden replay
- **Test command(s):** `py -3 -m pytest tests/test_turn_pipeline_shared.py tests/test_output_sanitizer.py tests/test_social_exchange_emission.py -q`
- **Risk:** **Low–medium** (verify HTTP regressions still catch wiring breaks)

### R3: FEM `final_route` downstream narrowing

- **Goal:** Stop downstream suites from re-locking exact gate route values when testing other concerns.
- **Files touched:** `tests/test_answer_completeness_rules.py`, `tests/test_response_delta_requirement.py`, `tests/test_interaction_continuity_repair.py`, `tests/test_turn_packet_stage_diff_integration.py`, `tests/test_diegetic_fallback_narration.py` (where passive)
- **Overlap family:** FEM `final_route`
- **Current owner:** `test_final_emission_gate.py`, `test_final_emission_meta.py`
- **Downstream affected:** Listed files
- **Remove/narrow/move:** Replace exact `== "replaced"` with route-class checks or key presence where primary assertion is elsewhere
- **Do not touch:** Gate route tables; golden replay; retry cluster (`test_empty_social_retry_regressions.py`) — `final_route` is **primary** there
- **Test command(s):** `py -3 -m pytest tests/test_answer_completeness_rules.py tests/test_response_delta_requirement.py tests/test_interaction_continuity_repair.py tests/test_final_emission_gate.py -q`
- **Risk:** **Medium** — confirm each narrowed case has owner coverage for the specific branch

### R4: Inventory refresh + registry neighbor expansion (governance)

- **Goal:** Close governance gap for new replay module and downstream_consumer slots.
- **Files touched:** `tools/test_audit.py` run → `tests/test_inventory.json`; optionally `tests/test_ownership_registry.py` (add `test_golden_replay.py` as neighbor under gate or new replay group; populate `downstream_consumer_suites` for `test_turn_pipeline_shared.py`, `test_prompt_and_guard.py` per TEST_AUDIT tables)
- **Overlap family:** Governance visibility (not runtime)
- **Current owner:** `test_ownership_registry.py`
- **Remove/narrow/move:** None — additive registry/documentation
- **Test command(s):** `py -3 tools/test_audit.py` then `py -3 -m pytest tests/test_ownership_registry.py tests/test_test_audit_tool.py -q`
- **Risk:** **Low**

**Deferred (post R1–R4):** Lead/clue cluster (`test_social_lead_landing.py`, `test_clue_lead_registry_integration.py`, `test_social_destination_redirect_leads.py`); transcript substring thinning beyond C4; prompt_context downstream narrowing (PC2-R) — per `TEST_CONSOLIDATION_PLAN.md` step 6.

---

## 8. Open Questions / Files Needed

1. **Regenerate `tests/test_inventory.json`** — current JSON predates `test_golden_replay.py` and ~800+ new collected items; rerun `py -3 tools/test_audit.py` before Cycle R implementation PRs.
2. **`pytest -m "not transcript and not slow"` collect-only delta** — quantify fast-lane impact after R2/R3 (not run in this recon).
3. **Full `pytest -q` baseline** — establish green baseline before first reduction block (4247 tests).
4. **`tests/test_prompt_and_guard.py` deep read** — inventory shows 29 legality/sanitizer-tagged tests; manual pass needed to list remaining duplicate phrases post-C3.
5. **`test_final_emission_gate.py` collected node count** — file grew beyond inventory's collected count; refresh for R1 impact sizing.
6. **Block B `downstream_consumer_suites` emptiness** — confirm whether `test_turn_pipeline_shared.py` and peers should be registered as neighbors (documentation vs enforcement).
7. **Cross-layer equivalence suites (block S/T/U)** — confirm with maintainers whether fixture extraction affects equivalence contracts.
8. **Command outputs to attach in follow-up PRs:**
   - `rg "assert.*final_route" tests`
   - `rg "scene holds|state exactly what you do" tests`
   - `py -3 -m pytest tests/test_golden_replay.py -q` (baseline timing for replay lane)

---

*Recon complete. No tests or production code modified.*
