# Cycle AC — Replay Surface Compression Recon (2026-05-31)

Goal: identify safe replay-surface compression opportunities without changing replay authority, coverage, or behavioral expectations. **Recon only** — no runtime changes, no test deletion, no fixture rewrites.

## Executive Summary

Golden replay is authoritative and well-factored at the projection layer (`golden_replay_projection.py`, Cycle T1) and expectation-fragment layer (`protected_*_expectation` helpers, Cycle Q). Remaining maintenance drag concentrates in **`tests/test_golden_replay.py`** (~2,620 lines, 56 tests): local seed builders, repeated API monkeypatch stubs, hand-built direct-seam observed-turn dicts, and per-scenario expectation boilerplate that already partially uses shared fragments.

Safest first implementation block: **extract replay scenario harness utilities** (seed functions + standard `call_gpt`/intent-parser monkeypatch context) and **add a direct-seam observed-turn builder** that wraps `project_turn_observation` / `project_replay_fallback_family_from_fem` instead of manual FEM field reads. These are test-only, low blast radius, and do not touch protected field paths or assertion semantics.

Cycle Q recon items for `protected_*_expectation` and Frontier Gate fixture readers are **already landed**. AC should not re-implement them.

Validation run (2026-05-31):

- `python -m pytest tests/test_golden_replay.py -q` — **58 passed**
- `python -m pytest tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py -q` — **passed**
- Broad `pytest tests -k "replay or golden or final_emission"` collection blocked by unrelated import error in `tests/test_narration_transcript_regressions.py` (`_response_type_contract`); not replay-caused.

---

## 1. Replay Surface Inventory

### Core replay / golden files

| Path | Purpose | Tests / funcs / classes | Main local project imports |
|---|---|---:|---|
| `tests/test_golden_replay.py` | Authoritative golden replay suite: projection contracts, protected E2E scenarios, direct-seam locks, long-session stability, rerun drift, report renderers | 56 tests, 7 `_seed_*` helpers, 1 `_gm_response` | `tests.helpers.golden_replay`, `golden_replay_projection`, `opening_fallback_evidence`, `final_emission_gate_fixtures`, `transcript_runner`, `failure_dashboard_report`, `game.api`, `game.final_emission_gate`, `game.scenario_spine*` |
| `tests/helpers/golden_replay.py` | Runner, drift assert/classify, protected expectation fragments, long-session summaries, rerun comparator, scenario-spine bridge | ~45 functions | `golden_replay_projection`, `transcript_runner`, `failure_classifier`, `failure_dashboard_report`, `runtime_lineage_reporting`, `game.api`, `game.scenario_spine_eval`, `game.storage` |
| `tests/helpers/golden_replay_projection.py` | Payload/snapshot → observed-turn projection; protected field registry (41 paths) | ~24 functions, 1 dataclass | `game.final_emission_meta`, `game.final_emission_replay_projection`, `transcript_runner`, `tests.debug_trace_utils` |
| `game/final_emission_replay_projection.py` | Runtime read-side FEM → lineage projection (sealed sub-kinds, opening/strict-social owners) | ~15 functions | `game.runtime_lineage_telemetry`, `game.telemetry_vocab` |
| `docs/testing/protected_replay_manifest.md` | Governance: protected/supporting/advisory scenarios, dual fallback-family contract, generated field-path table | doc | references `golden_replay_projection`, `refresh_protected_replay_manifest.py` |
| `tools/refresh_protected_replay_manifest.py` | Regenerate/check manifest protected-field section | 1 script | `golden_replay_projection.protected_field_paths` |

### Golden fixtures (data)

| Path | Purpose | Notes |
|---|---|---|
| `data/validation/scenario_spines/frontier_gate_long_session.json` | Canonical 25-turn long-session spine; `branch_social_inquiry` feeds protected replay | Authoritative fixture |
| `data/validation/scenario_spines/c1a_opening_convergence_paths.json` | Opening convergence spine smoke | Supporting; not golden-protected |

### Replay-adjacent helpers (fixture factories / smoke / metadata)

| Path | Purpose | Funcs | Main imports |
|---|---|---:|---|
| `tests/helpers/final_emission_gate_fixtures.py` | Gate harness: `opening_gm_output`, `runner_strict_bundle`, FEM assert helpers, opening validation context | 14 | `game.final_emission_gate`, `opening_fallback_evidence`, `game.interaction_context` |
| `tests/helpers/opening_fallback_evidence.py` | Canonical opening FEM + observed-field builders | 4 | `game.final_emission_meta`, `game.upstream_response_repairs` |
| `tests/helpers/emission_smoke_assertions.py` | HTTP/pipeline smoke: player text hygiene, repair evidence, response-type meta | 13 | `game.final_emission_meta` |
| `tests/helpers/transcript_runner.py` | Transcript harness: storage patch, bootstrap, clean campaign, snapshots | 5 | `game.storage`, `game.defaults` |
| `tests/helpers/transcript_snapshots.py` | Snapshot projection, target/source extraction | 8 | transcript-local |
| `tests/helpers/failure_classifier.py` | Replay drift → category/owner/severity taxonomy | 30 | contract constants |
| `tests/helpers/failure_dashboard_report.py` | Protected replay failure report + dashboard rows | 34 | `golden_replay_projection`, `failure_classifier` |
| `tests/helpers/failure_classification_sync.py` | Contract ↔ classifier alignment checks | 10 | `failure_classification_contract`, `golden_replay_projection` |
| `tests/helpers/runtime_lineage_reporting.py` | Lineage summary for rerun comparison | 7 | `game.runtime_lineage_telemetry` |

### Replay-adjacent test files (not golden-marked but replay-shaped)

| Path | Purpose | Replay relevance |
|---|---|---|
| `tests/test_failure_classifier.py` | Classifier behavior on synthetic observed rows | Uses `opening_fallback_evidence` observed builders |
| `tests/test_failure_dashboard_controlled_failures.py` | Known-bad rows for dashboard/report | Uses `project_turn_observation`, `protected_field_paths` |
| `tests/test_failure_classification_contract.py` | Schema lock for classifier rows | Taxonomy authority |
| `tests/test_run_scenario_spine_validation.py` | Scenario-spine CLI artifact contracts | Uses `successful_opening_fem_meta`, opening fixtures |
| `tests/test_ownership_registry.py` | Documents golden replay as gauntlet neighbor | Registry only |

### Final-emission tests (projection consumers, not replay owners)

~20 `tests/test_final_emission_*.py` modules exercise gate/FEM contracts directly. They share fixture helpers with replay but are **gate-owner** suites, not compression targets unless explicitly importing replay helpers incorrectly.

---

## 2. Duplication Findings

### Group A — Protected expectation boilerplate (partially consolidated)

| Theme | Files | Repeated structure | Safe to centralize? | Canonical home | Risk |
|---|---|---|---|---|---|
| No-scaffold lock | `golden_replay.py` (`protected_no_scaffold_expectation`), `test_golden_replay.py` (1 inline override in sanitizer test) | `text_must_not_include` + `scaffold_leakage: False` | **Yes** — replace sanitizer inline list with helper + case variants | `tests/helpers/golden_replay.py` | **Low** |
| Route metadata | `golden_replay.py` (`protected_route_expectation`, constants `PROTECTED_SOCIAL_*`) | `one_of` for `route_kind`, `resolution_kind`, trace route | Already centralized; callers still repeat `**protected_route_expectation(...)` spreads | `golden_replay.py` | **Low** |
| Source lock | `protected_source_expectation` | `not_equals: {final_emitted_source: global_scene_fallback}` | Centralized | `golden_replay.py` | **Low** |
| Unavailable fields | `protected_unavailable_expectation` | Per-scenario allowlists for optional projection fields | Centralized fragments; per-scenario field lists remain intentional | `golden_replay.py` | **Low** |
| Full social structural bundle | 7 protected E2E tests | `require_present` + 3–5 `protected_*` spreads + scenario-specific `equals` | **Yes** — add optional composer e.g. `protected_social_structural_base(...)` | `golden_replay.py` | **Medium** (must preserve per-scenario deltas) |

### Group B — Scenario seed / world setup

| Theme | Files | Repeated structure | Safe? | Home | Risk |
|---|---|---|---|---|---|
| Investigator scene + runner NPC | `_seed_directed_runner_question_context`, `_seed_runner_and_guard_context`, overlap with `runner_strict_bundle` in `final_emission_gate_fixtures.py` | `default_scene("scene_investigate")`, runner NPC topics, session active scene | **Partly** — extract shared `seed_investigator_runner_world()`; keep scenario-specific NPC additions local | New `tests/helpers/golden_replay_fixtures.py` or extend `golden_replay.py` | **Medium** |
| Frontier Gate long session | `_seed_frontier_gate_long_session_context` | world/scene bootstrap for 25-turn replay | Yes as named helper (already have spine JSON loaders) | `golden_replay.py` (loaders exist) + seed helper extraction | **Low** |
| Opening curated facts prose | `final_emission_gate_fixtures.opening_validation_context`, `EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` | Same 3 visible facts / 4-sentence fallback paragraph | **Partly** — facts list already shared; full prose constant is gate-contract locked | `final_emission_gate_fixtures.py` | **High** if prose bytes change |

### Group C — API monkeypatch harness

| Theme | Files | Repeated structure | Safe? | Home | Risk |
|---|---|---|---|---|---|
| Intent parser null stubs + `call_gpt` patch | 9 integration scenarios in `test_golden_replay.py` | `monkeypatch.context()` + 3× `parse_*_intent → None` + fake GPT | **Yes** | `golden_replay_fixtures.golden_replay_chat_stubs(monkeypatch, gpt_fn)` | **Low** |

### Group D — Direct-seam observed-turn scaffolds

| Theme | Files | Repeated structure | Safe? | Home | Risk |
|---|---|---|---|---|---|
| Manual turn dict from gate output | `test_golden_direct_seam_declared_alias_*`, `test_golden_direct_seam_canonical_opening_*` | Hand-built dict: `final_text`, FEM fields, `fallback_family` via manual OR, `scaffold_leakage`, `unavailable`, partial `trace` | **Yes** — wrap `project_turn_observation` with synthetic snap/payload or thin `observed_turn_from_gate_output(out, resolution, ...)` | `golden_replay.py` or `golden_replay_projection.py` (test-only) | **Medium** — must not drop fields assertions rely on |
| Dual-family read | 2 direct-seam sites | `meta.get("fallback_family_used") or meta.get("realization_fallback_family")` | **Yes** — use `project_replay_fallback_family_from_fem(meta)` | `golden_replay_projection.py` | **Low** |

### Group E — Drift assertion mirror logic

| Theme | Files | Repeated structure | Safe? | Home | Risk |
|---|---|---|---|---|---|
| Expectation evaluation | `assert_golden_turn_observation` vs `classify_golden_drift` in `golden_replay.py` | ~120 lines parallel: equals/one_of/not_equals/text/scaffold/unavailable | **Partly** — internal `_evaluate_golden_expectation` shared by assert + classify | `golden_replay.py` | **Medium** — regression-sensitive |

### Group F — Golden replay expected outputs / classifier rows

| Theme | Files | Repeated structure | Safe? | Home | Risk |
|---|---|---|---|---|---|
| Opening success/fail observed rows | `opening_fallback_evidence.py`, `test_failure_classifier.py`, inline synthetic rows in `test_golden_replay.py` | Same FEM/observed field sets for opening ownership | Partially consolidated (AD-4); inline synthetic IDs in golden tests remain intentional | `opening_fallback_evidence.py` | **Low** for new consumers; **High** to change classifier rows |

### Group G — Smoke vs replay scaffold checks

| Theme | Files | Repeated structure | Safe? | Home | Risk |
|---|---|---|---|---|---|
| Scaffold term bans | `emission_smoke_assertions.assert_no_internal_scaffold_labels`, `golden_replay_projection.final_text_has_scaffold_leakage`, `protected_no_scaffold_expectation` | Overlapping forbidden tokens (`planner`, `router`, `validator`, `scaffold`) | **Document only** — different layers (HTTP smoke vs replay projection vs expectation dict) | Keep separate; optional shared constant tuple | **High** if unified enforcement diverges |

---

## 3. Metadata Normalization Findings

### Repeated metadata shapes

| Shape | Fields | Where constructed |
|---|---|---|
| Golden observed turn | `route_kind`, `selected_speaker_id`, `final_emitted_source`, `fallback_family`, owner buckets, `response_type_*`, sanitizer lineage, `trace.*`, `runtime_lineage_events`, `unavailable` | `project_turn_observation` (canonical) |
| Protected expectation dict | `require_present`, `allow_unavailable`, `equals`, `one_of`, `not_equals`, `text_must_*`, `scaffold_leakage` | per test + `protected_*_expectation` fragments |
| Opening fallback FEM | `final_emitted_source`, `opening_recovered_via_fallback`, `opening_fallback_authorship_source`, `fallback_family_used` | `opening_fallback_evidence.successful_opening_fem_meta` |
| Opening observed (classifier/replay) | above + `fallback_family`, `fallback_temporal_frame`, optional `opening_fallback_owner_bucket` | `opening_fallback_evidence.successful_opening_observed_fields` |
| Direct-seam hand turn | subset of observed turn + manual `unavailable` | 2–3 tests in `test_golden_replay.py` |
| Scenario-spine row meta | `spine_id`, `branch_id`, `turn_id`, `golden_replay_observation` embed | `project_golden_replay_turns_to_scenario_spine_rows` |

### Inconsistent naming (intentional layer projections — do not collapse)

| Concept | Variants | Notes |
|---|---|---|
| Scenario identity | `scenario_id` (replay), `spine_id` (fixture), `scenario_spine_id` (N1) | Documented in manifest |
| Player text | `player_facing_text` → `gm_text` (snap) → `final_text` (observed) | Layer-specific |
| Fallback family | `fallback_family_used`, `realization_fallback_family`, projected `fallback_family` | Cycle AB dual-field contract |
| Route | `route_kind`, `resolution.kind`, `trace.social_contract_trace.route_selected` | Projection picks first present |

### Helper candidates for normalized metadata construction

1. **`observed_turn_from_gate_output(gm_output, resolution, *, scenario_id, extra_fields)`** — eliminates manual FEM reads in direct-seam tests.
2. **`protected_structural_expectation(*, require=(), unavailable=(), equals=None, extra_no_scaffold=())`** — composes existing `protected_*` fragments with scenario-specific overrides.
3. **`minimal_golden_chat_payload(gm_output_dict)`** — standard `{gm_output: {_final_emission_meta: ...}}` wrapper for projection unit tests (15+ inline payloads).

### Tests simplified after normalization

- `test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants`
- `test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership`
- All 7 protected E2E structural tests (monkeypatch + expectation composition)
- Synthetic projection tests block (~lines 1221–1810 in `test_golden_replay.py`)

---

## 4. Helper Consolidation Findings

| Helper | File | Overlaps with | Callers | Recommendation | Blast radius |
|---|---|---|---|---|---|
| `protected_no_scaffold_expectation` | `golden_replay.py` | inline sanitizer expectation | 8+ protected tests | **Keep**; extend usage to sanitizer test | 1 test |
| `protected_route/source/unavailable_expectation` | `golden_replay.py` | — | protected tests | **Keep** | — |
| `assert_golden_turn_observation` / `classify_golden_drift` | `golden_replay.py` | each other (logic duplicate) | golden tests, dashboard | **Merge internal eval** later | `golden_replay.py` only |
| `project_turn_observation` | `golden_replay_projection.py` | manual direct-seam dicts | golden tests, failure dashboard | **Reuse** in direct-seam tests | 2–3 tests |
| `project_replay_fallback_family_from_fem` | `golden_replay_projection.py` | manual OR in direct-seam | projection tests | **Reuse** in direct-seam | 2 sites |
| `successful_opening_fem_meta` / `*_observed_fields` | `opening_fallback_evidence.py` | inline FEM in projection tests | golden, classifier, dashboard, scenario_spine | **Keep**; prefer over inline FEM | low |
| `opening_gm_output` / `runner_strict_bundle` | `final_emission_gate_fixtures.py` | `_seed_*` partial overlap | gate tests, golden direct-seam, block S/T/U | **Keep**; do not merge seeds into gate fixtures | high if blurred |
| `assert_final_emission_meta_contains` | `final_emission_gate_fixtures.py` | `assert_response_type_meta`, golden `equals` | gate tests, answer_completeness, response_delta | **Keep separate** — gate vs smoke vs replay layers | — |
| `assert_response_type_meta` | `emission_smoke_assertions.py` | FEM assert helpers | turn_pipeline_shared | **Keep** | — |
| `final_emission_meta_from_output` | `final_emission_gate_fixtures.py` | `read_final_emission_meta_dict` direct calls | many gate-adjacent tests | **Keep** | — |
| `run_golden_replay` | `golden_replay.py` | transcript_runner + manual loops | protected E2E tests | **Keep** | — |
| `frontier_gate_branch_prompts/turn_ids` | `golden_replay.py` | — | long-session tests | **Keep** (Cycle Q landed) | — |
| `_gm_response` | `test_golden_replay.py` | `emission_smoke_assertions.gm_response_stub` | golden integration tests | **Move** to shared stub helper | 9 tests |
| 7× `_seed_*` | `test_golden_replay.py` | `runner_strict_bundle`, transcript seeds | protected scenarios | **Move** to `golden_replay_fixtures.py` | 7 tests |

---

## 5. Redundant Scenario Findings

| Scenario / test | Covers | Overlap | Recommendation | Risk |
|---|---|---|---|---|
| `test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership` | Full opening FEM ownership + scaffold + dual-family raw keys | `test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership` asserts subset (authorship + owner bucket only) | **Keep both** — manifest documents companion lock; second is cheap regression guard | Low |
| `test_golden_replay_sanitizer_scaffold_leakage_*` vs `protected_no_scaffold_expectation` usage elsewhere | Scaffold leak containment | Same invariant as all protected tests' no-scaffold fragment | **Merge assertions** to use `protected_no_scaffold_expectation(extra_terms=...)` only — not delete scenario | Low |
| 15+ synthetic `test_golden_observed_turn_projects_*` | FEM/projection field wiring | Each targets distinct FEM stamp (opening, sealed, visibility, sanitizer, prepared emission) | **Keep all** — supporting projection contracts, not duplicate scenarios | — |
| `test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability` vs `_resume_persistence_supporting` | 25-turn stability vs resume/session persistence | Same spine branch, different persistence dimension | **Keep both** | Medium if merged |
| `test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability` | Advisory alternate branch | Different branch intent | **Keep** (ADVISORY per manifest) | — |
| `test_golden_replay_vocative_override_*` multi `assert_protected_golden_turn_observation` blocks | Conditional assertions when trace fields present | Not redundant — models optional projection availability | **Keep** | — |
| `directed_npc_question` vs speaker contract unit tests | E2E speaker routing | Defense-in-depth with fine-grained owner tests | **Keep both** | — |

**No scenario recommends deletion** — overlaps are either companion locks, advisory lanes, or layer-separated defense-in-depth.

---

## 6. Maintenance Burden Metrics

| Metric | Count |
|---|---:|
| Golden replay fixture JSON files | 2 (1 authoritative long-session) |
| Golden replay test files (`pytest.mark.golden_replay`) | 1 module, **56 tests** |
| Replay helper modules (primary) | 4 (`golden_replay`, `golden_replay_projection`, `opening_fallback_evidence`, `failure_classifier` neighbors) |
| Obvious duplicate fixture groups (remaining after Cycle Q) | **6** (seeds, monkeypatch, direct-seam turn dict, sanitizer inline scaffold, drift mirror logic, `_gm_response` stub) |
| Helper consolidation candidates | **8** actionable (see §4) |
| Possible redundant scenarios | **0 deletions**; **1** assertion merge candidate (sanitizer scaffold terms) |
| Protected observation field paths | 41 |

### Top 3 files by replay maintenance burden

1. **`tests/test_golden_replay.py`** — 2,620 lines; hosts all protected scenarios, seeds, inline payloads, direct-seam dicts.
2. **`tests/helpers/golden_replay.py`** — 1,379 lines; runner, drift, summaries, duplicated assert/classify logic.
3. **`tests/helpers/golden_replay_projection.py`** — 610 lines; authority-critical projection registry (touch rarely, but high impact).

---

## 7. Risk Notes

- **Do not** merge `fallback_family_used` and `realization_fallback_family` at write time or in projection preference order (Cycle AB contract).
- **Do not** change `PROTECTED_OBSERVATION_FIELDS` or manifest generated section without `refresh_protected_replay_manifest.py --write` + review.
- **Do not** move gate orchestration semantics into replay helpers (`final_emission_gate_fixtures` boundary documented in AD-4).
- Seed extraction must preserve exact NPC ids (`runner` vs `tavern_runner`) — tests assert specific speaker targets.
- `classify_golden_drift` / `assert_golden_turn_observation` internal merge needs golden replay full suite + classifier probes.
- Broader pytest collection currently fails on unrelated import in `test_narration_transcript_regressions.py`; fix separately from AC.

---

## 8. Recommended Implementation Blocks

### Block AC-1 (safest first): Scenario harness extraction

- Create `tests/helpers/golden_replay_fixtures.py` (or section in `golden_replay.py` if prefer single module).
- Move: `_seed_*` (7), `_gm_response`, `golden_replay_chat_stubs(monkeypatch, gpt_fn)`.
- Repoint `test_golden_replay.py` imports only.
- **Preserves** all scenario IDs, seeds, and monkeypatch behavior.

### Block AC-2: Direct-seam observed-turn normalization

- Add `observed_turn_from_gate_output(...)` using `project_turn_observation` + `project_replay_fallback_family_from_fem`.
- Repoint direct-seam tests; remove manual `fallback_family` OR reads.
- **Preserves** assertion dicts unchanged.

### Block AC-3: Expectation composition + sanitizer helper adoption

- Add `protected_structural_expectation_base(**overrides)` composing existing fragments.
- Switch `sanitizer_scaffold_leakage` test to `protected_no_scaffold_expectation(extra_terms=(...))`.
- **Preserves** forbidden term coverage (may add case variants already in inline list).

### Block AC-4 (defer): Drift assert/classify internal dedup

- Extract shared `_evaluate_expectation_fields(observed, expectation) -> drift_rows`.
- Higher regression risk; run full golden + failure dashboard probes.

### Block AC-5 (defer): Synthetic projection payload builders

- `minimal_turn_payload(fem_meta, gm_text=...)` for unit tests only.
- Reduces ~200 lines of inline dict noise; low authority risk.

---

## Files to Pass Back to ChatGPT

### Required

- `tests/helpers/golden_replay.py` — existing expectation fragments, runner, extension point for AC-1/AC-3
- `tests/helpers/golden_replay_projection.py` — canonical projection + `project_replay_fallback_family_from_fem` for AC-2
- `tests/test_golden_replay.py` — all repoint targets; seed/monkeypatch/direct-seam call sites
- `docs/testing/protected_replay_manifest.md` — protected scenario inventory; verify no scenario ID changes

### Optional but useful

- `tests/helpers/opening_fallback_evidence.py` — opening FEM/observed canonical shapes for direct-seam alignment
- `tests/helpers/final_emission_gate_fixtures.py` — `opening_gm_output`, `runner_strict_bundle` used by direct-seam tests
- `tests/helpers/emission_smoke_assertions.py` — boundary vs smoke scaffold checks (avoid merging incorrectly)
- `audits/cycle_q_replay_cost_compression_recon_2026-05-29.md` — prior cycle baseline; note Q items already landed
- `game/final_emission_replay_projection.py` — read-side lineage semantics if AC-2 touches synthetic payloads with lineage

---

## Appendix: Cycle Q → AC Delta

Already implemented since Cycle Q recon (do not re-do):

- `protected_no_scaffold_expectation`, `protected_route_expectation`, `protected_source_expectation`, `protected_unavailable_expectation`
- `load_frontier_gate_long_session_spine`, `frontier_gate_branch_prompts`, `frontier_gate_branch_turn_ids`
- `golden_replay_projection.py` as centralized projection adapter (Cycle T1)
- `opening_fallback_evidence.py` FEM/observed builders (Cycle AD-4)
- `final_emission_gate_fixtures.py` extraction from gate test module (Cycle R)

AC focus = **test file bulk reduction** and **direct-seam normalization**, not re-projection or re-manifest work.
