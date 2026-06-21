# Protected Replay Manifest

## Purpose

This manifest declares the canonical protected replay set for acceptance review. It is governance-only: it does not change runtime behavior, pytest assertions, markers, selection, or CI wiring.

**Canonical governance inventory:** [`docs/convergence_ci_inventory.md`](../convergence_ci_inventory.md) (protected replay hard-fail step and local reproduction commands).

Classification meanings:

| Status | Meaning |
|---|---|
| `PROTECTED` | A failure should block acceptance. |
| `SUPPORTING` | Useful replay signal, but not itself an acceptance blocker. |
| `ADVISORY` | Informational or exploratory evidence only. |
| `DEPRECATED` | No longer intended for long-term protection. |

Current executable location: `tests/test_golden_replay.py`. Current helper/projection location: `tests/helpers/golden_replay.py`. Historical replay baseline archived under `docs/archive/dead_governance/2026-05-31/golden_replay_baseline_2026-05-11.md`; this manifest is the sole current protected replay acceptance authority.

Protected replay reproduction command:

```bash
python -m pytest tests/test_golden_replay.py -q
```

`tests/test_golden_replay.py` currently contains protected and supporting tests in one pytest module. This manifest classifies their acceptance ownership; it does not alter today's test execution behavior.

Inventory-only regeneration is a maintenance workflow, not logic ownership. Run `python tools/test_audit.py` only when refreshing `tests/test_inventory_governance.json` and keep that generated JSON output separate from behavior, replay, or protected-observation changes. Protected observation field paths are **generated only** from `PROTECTED_OBSERVATION_FIELDS` in `tests/helpers/golden_replay_projection.py`; refresh with `python tools/refresh_protected_replay_manifest.py --write` and verify with `--check` (also enforced in CI).

## Metadata Ownership

Golden replay owns `scenario_id` as the replay acceptance identifier. Scenario-spine fixtures own `spine_id`, `branch_id`, and per-turn `turn_id`; when a golden replay is scenario-spine-backed, those fixture identifiers remain source metadata rather than replacing the golden `scenario_id`. The N1 longitudinal lane uses `scenario_spine_id` and remains a separate synthetic/advisory lane, not a silent extension of protected golden replay.

Text fields are layer-specific projections: `player_facing_text` is the runtime response field, `gm_text` is a snapshot/transcript projection, and `final_text` is the golden replay observed assertion surface. Protected replay failure reports may include `source_path`, `branch_id`, and `turn_id` when a replay row can be traced back to a scenario-spine fixture.

## Cycle AO5 Runtime vs Acceptance Projection Boundary

Replay projection is intentionally split across two modules that must **not** be merged:

| Layer | Module | Owns |
|---|---|---|
| **Runtime (diagnostic/read-side)** | `game/final_emission_replay_projection.py` | `fem_runtime_lineage_events` derivation from finalized FEM; sealed replacement sub-kinds; lineage selection/content owner fields on events |
| **Acceptance (test-only)** | `tests/helpers/golden_replay_projection.py` | canonical protected observation paths (`PROTECTED_OBSERVATION_FIELDS`; generated table below); `project_turn_observation`; drift buckets; classifier evidence overlap derivation |

Rules:

- Runtime lineage is **diagnostic/read-side** — it does not define protected golden replay fields or CI acceptance locks.
- Golden replay protected fields are **acceptance authority** — registry + projection adapter in the test helper module.
- Golden replay may **consume** runtime lineage output (or payload-stamped `fem_runtime_lineage_events`) for reports and supporting tests.
- **Lineage owner mismatch remains excluded from protected drift** unless explicitly promoted in a future cycle; drift classification ignores runtime-lineage diagnostic-only owner semantics today.

Direct-seam and E2E golden replay both flow through the acceptance projection adapter; runtime lineage projection is supporting evidence only.

## Cycle AB Dual Fallback-Family Contract

Runtime FEM may carry **two independent fallback-family fields**:

| FEM field | Taxonomy | Owner module | Examples |
|---|---|---|---|
| `fallback_family_used` | Diegetic / template | `game/diegetic_fallback_narration.py` | `scene_opening`, `observe`, `social` |
| `realization_fallback_family` | Governed provenance | `game/realization_provenance.py` | `legacy_diegetic_fallback`, `upstream_prepared_emission`, `gate_terminal_repair` |

Protected golden replay observes a **single** projected field, `fallback_family`, for structural drift checks. Projection is implemented in `tests/helpers/golden_replay_projection.py::project_replay_fallback_family_from_fem` and prefers `fallback_family_used` first, falling back to `realization_fallback_family` only when diegetic classification is absent. That preference is a **read-side compatibility projection only**; runtime code must not rewrite either FEM field to force one taxonomy into the other.

Canonical opening fallback may therefore carry both `fallback_family_used=scene_opening` and `realization_fallback_family=upstream_prepared_emission` on the same turn (AB4). Protected replay locks the **projected** `fallback_family` to the diegetic value (`scene_opening`) while both raw FEM fields remain distinct.

Topology collapse (merging diegetic and provenance stamps into one runtime field) is **deferred** until AB4+ replay proof; this manifest documents the contract but does not change protected assertion behavior.

## Cycle AB6 Sealed Replacement Sub-Kind Projection

Runtime terminal replace turns keep ``final_route=replaced``, ``final_emitted_source``,
``fallback_pool``, and ``fallback_kind`` unchanged. Read-side lineage projection in
``game/final_emission_replay_projection.py::project_sealed_replacement_subkind_from_fem``
refines the former catch-all lineage bucket ``sealed_or_global_replacement`` into stable
sub-kinds (for example ``sealed_global_scene_fallback``, ``sealed_passive_scene_pressure_fallback``).

These sub-kinds appear on projected ``fem_runtime_lineage_events[*].fallback_kind`` only.
They are **not** protected golden replay observation fields and do not rewrite runtime FEM.

<!-- BEGIN GENERATED: protected_field_paths -->

## Protected Observation Field Paths (Generated)

Bounded registry of golden replay observation paths locked by protected replay.
Source: `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS`.

Refresh this section:

```bash
python tools/refresh_protected_replay_manifest.py --write
```

Verify without writing:

```bash
python tools/refresh_protected_replay_manifest.py --check
```

- **Path count:** 41
- **Structural drift fields:** 39
- **Semantic drift fields:** 2

| Field path | Drift bucket |
|---|---|
| `fallback_family` | `structural_drift` |
| `fallback_temporal_frame` | `structural_drift` |
| `final_emission_mutation_lineage` | `structural_drift` |
| `final_emitted_source` | `structural_drift` |
| `final_text` | `semantic_drift` |
| `opening_fallback_authorship_source` | `structural_drift` |
| `opening_fallback_owner_bucket` | `structural_drift` |
| `opening_recovered_via_fallback` | `structural_drift` |
| `resolution_kind` | `structural_drift` |
| `response_type_candidate_ok` | `structural_drift` |
| `response_type_repair_kind` | `structural_drift` |
| `response_type_repair_used` | `structural_drift` |
| `response_type_required` | `structural_drift` |
| `route_kind` | `structural_drift` |
| `sanitizer_empty_fallback_owner` | `structural_drift` |
| `sanitizer_empty_fallback_source` | `structural_drift` |
| `sanitizer_empty_fallback_used` | `structural_drift` |
| `sanitizer_lineage_changed_count` | `structural_drift` |
| `sanitizer_lineage_dropped_count` | `structural_drift` |
| `sanitizer_lineage_empty_fallback_used` | `structural_drift` |
| `sanitizer_lineage_legacy_rewrite_active` | `structural_drift` |
| `sanitizer_lineage_mode` | `structural_drift` |
| `sanitizer_strict_social_fallback_used` | `structural_drift` |
| `sanitizer_strict_social_prose_owner` | `structural_drift` |
| `sanitizer_strict_social_selection_owner` | `structural_drift` |
| `sanitizer_strict_social_source` | `structural_drift` |
| `scaffold_leakage` | `semantic_drift` |
| `sealed_fallback_owner_bucket` | `structural_drift` |
| `selected_speaker_id` | `structural_drift` |
| `trace.canonical_entry.reason` | `structural_drift` |
| `trace.canonical_entry.target_actor_id` | `structural_drift` |
| `trace.canonical_entry.target_source` | `structural_drift` |
| `trace.social_contract_trace.route_selected` | `structural_drift` |
| `upstream_prepared_emission_reject_reason` | `structural_drift` |
| `upstream_prepared_emission_source` | `structural_drift` |
| `upstream_prepared_emission_used` | `structural_drift` |
| `upstream_prepared_emission_valid` | `structural_drift` |
| `visibility_fallback_kind` | `structural_drift` |
| `visibility_fallback_owner_bucket` | `structural_drift` |
| `visibility_fallback_pool` | `structural_drift` |
| `visibility_replacement_applied` | `structural_drift` |

<!-- END GENERATED: protected_field_paths -->

## Cycle S Drift Policy Addendum

Cycle S adds rerun drift measurement and seed-seam audit coverage without promoting new drift thresholds into protected acceptance gates.

Policy:

- Golden rerun drift scorecards are `ADVISORY` / report-only. They summarize successful-run differences; they do not change protected replay pass/fail behavior.
- Exact prose identity is not a default protected gate. Exact text comparison remains opt-in for explicitly curated expectations, while protected replay continues to enforce structural and player-facing semantic invariants.
- Semantic delta frequency uses existing `response_delta_*` and FEM metadata only. Cycle S does not add a semantic similarity judge, semantic rewrite behavior, or prose-quality scoring gate.
- Scenario-spine rerun comparison is advisory and separate from CI hard gates. It compares already-written artifact directories and reports identity, transcript, health, lineage, and text-fingerprint deltas for operator review.
- The stable-seed audit protects replay-sensitive speaker/fallback/final-emission paths from process-randomized seed seams such as Python `hash(...)`, `random`, `uuid`, or wall-clock `time` inputs.
- Future hard thresholds require repeated evidence across advisory scorecards, explicit review, and an update to this protected manifest before they may become acceptance-blocking.

Write the golden rerun drift scorecard locally with:

```powershell
.\.venv\Scripts\python.exe -m pytest -m golden_replay -q --write-rerun-drift-scorecard --basetemp=codex_pytest_tmp_cycle_s_scorecard
```

Compare two scenario-spine rerun artifact directories with:

```powershell
.\.venv\Scripts\python.exe tools/compare_scenario_spine_reruns.py --previous <dir> --current <dir> --out artifacts/scenario_spine/rerun_delta.md --json-out artifacts/scenario_spine/rerun_delta.json
```

## Cycle AR Reporting Addendum

Cycle AR adds **owner-oriented drift bucket** reporting on top of existing replay failure classification. This is **reporting-only** vocabulary for operator diagnostics.

Policy:

- `owner_drift_bucket` is an **additive reporting field** on classified failure rows and rerun scorecards. It does not replace `category`, `primary_owner`, `secondary_owner`, measurement drift buckets (`exact_drift`, `structural_drift`, `semantic_drift`), or `replay_tags`.
- Owner drift buckets are **not acceptance-blocking**. Protected replay pass/fail remains governed by existing structural and semantic invariants only.
- Rerun scorecard owner drift summaries remain **`ADVISORY`** / `report_only: true` alongside Cycle S rerun drift policy.
- Lineage-derived `lineage_drift` buckets surface in advisory rerun reports only; lineage owner mismatch remains excluded from protected drift classification unless explicitly promoted in a future cycle.

Canonical owner drift bucket vocabulary (9 buckets):

| Bucket | Reporting role |
|---|---|
| `route_drift` | Route / interaction-context drift |
| `speaker_drift` | Speaker contract drift |
| `fallback_drift` | Fallback family / source drift |
| `ownership_drift` | Fallback authorship / owner-bucket drift |
| `emission_drift` | Gate emission / repair drift |
| `semantic_drift` | Scaffold / semantic predicate drift |
| `lineage_drift` | Runtime lineage frequency drift (advisory) |
| `projection_drift` | Observation projection / unavailable drift |
| `replay_drift_unclassified` | Exact-text fingerprint / catch-all reporting |

Implementation surfaces:

- Protected failure report: `Owner Drift Bucket` column + `Owner Drift Breakdown` rollup
- Failure dashboard: `Owner Drift Bucket` column + breakdown rollup
- Rerun scorecard markdown: `Owner Drift Summary` table from `owner_drift_classifications`

## Cycle AY Recurrence Reporting Addendum

Cycle AY adds **bug-class recurrence tracking** as a report-only layer over
existing replay failure classification and owner drift reporting. It is
diagnostic vocabulary for operator review, not a replay acceptance rule.

Policy:

- Recurrence tracking remains **`report_only: true`** and **`advisory_only: true`**.
- Recurrence keys are derived from existing classification fields:
  `owner_drift_bucket`, `category`, `field_path`, and `investigate_first`.
- Recurrence statuses are diagnostic only:
  - `active` means the same recurrence key appears repeatedly in the available report history.
  - `watch` means the recurrence key has only a single event or insufficient history.
  - `retired` means an input explicitly marked the recurrence as retired or deprecated.
- `retired` is explicit-only. Absence from a short history must never be interpreted as retirement.
- Recurrence artifacts do not change protected replay pass/fail behavior, drift thresholds,
  governance registry decisions, or runtime gameplay behavior.

Implementation surfaces:

- Recurrence projection and aggregation: `tests/helpers/replay_bug_recurrence.py`
- Recurrence JSON/Markdown artifact emission: `tests/helpers/failure_dashboard_report.py`
- Artifact paths:
  - `artifacts/golden_replay/bug_recurrence_history.json`
  - `artifacts/golden_replay/bug_recurrence_history.md`

## Cycle AT Reporting Addendum

Cycle AT adds **long-session stability scorecards** as advisory/reporting artifacts derived from existing golden replay long-session metrics.

Policy:

- Long-session stability scorecards are **`report_only: true`** and **`advisory_only`** at the artifact boundary.
- They package route/speaker/fallback/lineage/degradation aggregates already computed by golden replay helpers; they do **not** introduce new protected observation paths or acceptance thresholds.
- Protected replay pass/fail remains owned by existing golden replay tests and structural invariants only.
- Generated artifacts under `artifacts/golden_replay/` must not be edited directly.

Opt-in emission:

```powershell
python -m pytest -m golden_replay -q --write-long-session-stability-scorecard
```

Environment alias: `ASHEN_WRITE_LONG_SESSION_STABILITY_SCORECARD=1`

Artifact paths:

- `artifacts/golden_replay/long_session_stability_scorecard.json`
- `artifacts/golden_replay/long_session_stability_scorecard.md`

## Cycle AT6 Stability Governance Closure

Cycle AT6 locks the AT1–AT5 stability reporting ecosystem into a contract-backed,
maintenance-friendly structure. This is **governance only** — no gameplay changes,
no replay behavior changes, no new metrics, no ranking logic changes, and no
acceptance-threshold changes.

Policy:

- Stability reporting remains **`advisory_only: true`** and **`report_only: true`**.
- Stability scorecards, ownership attribution, trend history, and hotspot ranking
  do **not** own gameplay behavior, protected replay pass/fail, or acceptance
  thresholds.
- Future consumers should extend reporting surfaces through the public contract
  in `tests/stability_reporting_contract.py` rather than ad hoc field growth.

Schema authority:

| Surface | Contract module | Projection / generation owner |
|---|---|---|
| Long-session stability scorecard | `tests/stability_reporting_contract.py` | `tests/helpers/golden_replay.py` |
| Stability ownership classification rows | `tests/stability_reporting_contract.py` | `tests/helpers/replay_drift_taxonomy.py` |
| Stability trend rows | `tests/stability_reporting_contract.py` | `tests/helpers/replay_drift_taxonomy.py` |
| Stability hotspot rows | `tests/stability_reporting_contract.py` | `tests/helpers/replay_drift_taxonomy.py` |
| Stability ownership risk payload | `tests/stability_reporting_contract.py` | `tests/helpers/replay_drift_risk.py` |

Ownership boundaries:

- **Taxonomy** (`tests/helpers/replay_drift_taxonomy.py`): classification, trend
  projection, hotspot projection.
- **Risk reporting** (`tests/helpers/replay_drift_risk.py`): enrichment and risk
  report presentation hooks only.
- **Dashboard/reporting** (`tests/helpers/failure_dashboard_report.py`): markdown
  rendering and artifact emission only.
- **Golden replay** (`tests/helpers/golden_replay.py`): long-session metric
  generation only.

Structural validation and drift-prevention tests live in
`tests/test_stability_reporting_contract.py` and
`tests/helpers/stability_reporting_sync.py`.

Contract reproduction command:

```powershell
python -m pytest tests/test_stability_reporting_contract.py -q
```

## End-To-End Protected Scenarios

Category: `END_TO_END_PROTECTED`. These cases execute turns through `run_golden_replay(...)` and the chat pipeline with deterministic test setup/model responses.

| Scenario ID | Test | Purpose | Invariant Protected | Status | Reproduction Command |
|---|---|---|---|---|---|
| `directed_npc_question` | `test_golden_replay_directed_npc_question_structural_invariants` | Preserve directed NPC question routing through final output. | Runner remains target/speaker; route remains social/dialogue-shaped; output has a non-global emitted source and no scaffold leakage. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_directed_npc_question_structural_invariants -q` |
| `vocative_override_after_prior_continuity` | `test_golden_replay_vocative_override_after_prior_continuity_structural_invariants` | Preserve explicit address override after an established interaction. | Guard becomes selected speaker after direct vocative; observable route/trace, when emitted, agrees with the switch; output does not leak scaffolding. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants -q` |
| `wrong_speaker_strict_social_emission` | `test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants` | Prevent illegal speaker attribution from surviving strict-social finalization. | Canonical runner owns the reply; injected `Merchant` attribution is absent from final text; output has no scaffold leakage. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants -q` |
| `thin_answer_action_outcome_final_emission` | `test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants` | Preserve concrete action outcome repair across final emission. | `action_outcome` remains required and repaired; final source is not global fallback; final text remains concrete and non-scaffold. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants -q` |
| `sanitizer_scaffold_leakage` | `test_golden_replay_sanitizer_scaffold_leakage_structural_invariants` | Prevent internal planning/validation text from reaching the player. | Planner/router/validator/scaffold terms are absent; emitted text remains non-empty; legacy sanitizer rewrite is not reactivated. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_sanitizer_scaffold_leakage_structural_invariants -q` |
| `lead_followup_with_dialogue_lock` | `test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants` | Preserve multi-turn NPC follow-up continuity after a lead is established. | Tavern runner remains selected speaker; dialogue/social route persists; observable canonical target remains the runner; no scaffold leakage. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants -q` |
| `frontier_gate_social_inquiry_25_turn` | `test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability` | Preserve sustained-play structural stability across the full canonical 25-turn social inquiry branch. | Replay completes all 25 deterministic turns with bounded route/speaker drift, no scaffold leakage, clean/warning continuity classification, no progressive degradation, no late fallback spike, no fallback owner oscillation, no fallback behavior repair loop, bounded unavailable/fallback coupling, and compact lineage-backed artifact output. This protected golden replay is backed by `data/validation/scenario_spines/frontier_gate_long_session.json` branch `branch_social_inquiry`. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability -q` |

## Direct-Seam Protected Scenarios

Category: `DIRECT_SEAM_PROTECTED`. A direct-seam scenario is protected where the acceptance-critical invariant is owned at final-emission/gate composition and a full chat run would add routing/setup noise without improving the ownership check.

These cases are not redundant with end-to-end replay:

- End-to-end replay verifies that the full pipeline reaches an acceptable player-facing outcome.
- Direct-seam replay verifies specific ownership boundaries and metadata/source contracts at the seam that decides the final emitted output.
- A full-pipeline pass can hide a wrong ownership source when later output still appears plausible; these direct-seam checks keep that contract visible.

| Scenario ID | Test | Purpose | Invariant Protected | Why Direct-Seam Is Needed | Status | Reproduction Command |
|---|---|---|---|---|---|---|
| `declared_alias_dialogue_plan` | `test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants` | Preserve declared speaker alias handling at strict-social final emission. | A permitted alias is accepted without losing the canonical runner target; dialogue plan remains valid; final text is non-scaffold. | It directly checks gate/dialogue-plan alias ownership; an end-to-end prompt could pass while masking whether alias admission occurred at the correct contract boundary. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants -q` |
| `opening_fallback_path` | `test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership`; companion lock `test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership` | Preserve canonical opening fallback authorship and source ownership. | Opening repair is selected from the upstream-prepared deterministic fallback, reports the upstream owner bucket/family/timeframe, and never reports compatibility-local authorship. | It protects final source/ownership metadata that is acceptance-relevant even when opening prose would look acceptable through a full chat path. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership tests/test_golden_replay.py::test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership -q` |

## Supporting Replay Scenarios

| Scenario ID / Group | Test / Path | Purpose | Status | Reason It Is Not Protected |
|---|---|---|---|---|
| `scenario_spine_three_branch` | `tests/test_golden_replay.py::test_golden_replay_scenario_spine_three_branch_structural_smoke` | Confirm compact branch representation, per-branch execution, minimal structural divergence, and no scaffold leakage. | `SUPPORTING` | It is a locally constructed one-turn-per-branch schema smoke and does not execute the committed long-session scenario-spine fixture. |
| Golden observation/projection contract rows | `tests/test_golden_replay.py` tests before the named baseline scenarios; `tests/helpers/golden_replay.py` | Protect projection of FEM, owner buckets, prepared emissions, sanitizer lineage, runtime lineage, drift classification, and report formatting. | `SUPPORTING` | These are test-harness and diagnostic contracts, not replay scenarios asserting player-facing acceptance. Synthetic `scenario_id` values in those tests are not protected scenarios. |
| Failure classification/dashboard controlled probes | `tests/test_failure_classifier.py`; `tests/test_failure_dashboard_controlled_failures.py`; `tests/test_failure_classification_contract.py` | Ensure replay failure explanation remains classifiable and readable. | `SUPPORTING` | They validate diagnostic behavior with known-bad rows; they do not define acceptable gameplay output. |

Replay-shaped synthetic identifiers in the golden module are classified as follows:

| Synthetic Identifier(s) | Supporting Purpose | Status |
|---|---|---|
| `lineage_diagnostic_only`; `recorded_lineage`; `existing_lineage_projection`; `fem_lineage_projection`; `missing_lineage_projection` | Runtime-lineage projection and opt-in dashboard behavior. | `SUPPORTING` |
| `synthetic_opening_owner`; `synthetic_opening_owner_fail_closed`; `synthetic_sealed_owner`; `synthetic_strict_social_sealed_owner`; `synthetic_visibility_owner` | Fallback owner-bucket and visibility evidence projection. | `SUPPORTING` |
| `answer_prepared_projection`; `action_outcome_prepared_projection`; `rejected_prepared_projection`; `answer_prepared_absent_projection`; `action_outcome_prepared_absent_projection`; `malformed_prepared_projection` | Upstream-prepared emission projection and rejection/missing evidence handling. | `SUPPORTING` |
| `sanitizer_empty_projection`; `strict_social_sanitizer_split`; `sanitizer_clean_lineage`; `sanitizer_debug_lineage`; `sanitizer_legacy_lineage` | Sanitizer ownership and lineage projection. | `SUPPORTING` |

## Advisory Replay Scenarios

| Scenario / Lane | Path | Purpose | Status | Notes |
|---|---|---|---|---|
| Game-level long-session scenario-spine execution | `data/validation/scenario_spines/frontier_gate_long_session.json`; `tools/run_scenario_spine_validation.py` | Long-session branch health, convergence, divergence, and artifact review. | `ADVISORY` | The full 25-turn `branch_social_inquiry` source material now has a protected golden replay bridge, but the standalone scenario-spine runner remains advisory and does not hard-fail on evaluated health failures. |
| Opening scenario-spine paths | `data/validation/scenario_spines/c1a_opening_convergence_paths.json`; `tests/test_scenario_spine_opening_convergence.py` | Opening-convergence evidence. | `ADVISORY` | Evaluator/fixture evidence adjacent to protected replay, not a declared golden scenario. |
| N1 longitudinal scenario-spine lane | `tests/helpers/n1_scenarios.py`; `tools/run_n1_scenario_spine_validation.py` | Synthetic continuity, revisit, progression, and branching artifacts. | `ADVISORY` | Intentionally separate lane; not silently merged into golden replay acceptance. |
| Transcript/gauntlet replay-adjacent regressions | `tests/test_transcript_regression.py`; `tests/test_transcript_gauntlet_actor_addressing.py`; `tests/test_transcript_gauntlet_campaign_cleanliness.py`; `tests/test_narration_transcript_regressions.py` | Broader multi-turn behavior evidence. | `ADVISORY` | Valuable regression evidence, but not declared protected golden scenarios here. |

## Deprecated Replay Scenarios

No existing golden replay scenario is classified `DEPRECATED` in this declaration.
