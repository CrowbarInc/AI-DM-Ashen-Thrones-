# Cycle U - Sustained Session Validation Recon

## Executive Summary

Cycle U does not need a new replay runner as its first move. The repo already has a protected 20-turn golden replay lane, a committed 50-turn long-session scenario-spine source across two 25-turn branches, runtime-lineage projection, fallback escalation summaries, and scenario-spine continuity/degradation evaluation.

Safest first implementation block: extend the existing golden replay long-session surface with a second sustained-session validation layer that remains deterministic, mocked-GPT only, and metrics-first. Start by adding a 25-turn full-branch variant or a 20-turn-plus-resume/checkpoint variant near `tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_20_turn_structural_stability`, then promote only stable aggregate assertions.

Main gap for Cycle U: the repo proves one protected 20-turn social-inquiry path. It does not yet prove 50-turn aggregate behavior, resume/checkpoint persistence, route/fallback behavior across multiple long branches as a protected gate, or mutation accumulation beyond the current bounded lineage summaries.

## Relevant Files

| Path | Purpose | Current Coverage | Suitable For Cycle U? |
|---|---|---|---|
| `tests/test_golden_replay.py` | Protected/supporting replay scenarios and long-session assertions. | 35 collected tests; includes protected `frontier_gate_social_inquiry_20_turn`. Covers route/speaker/fallback/continuity/lineage metrics with mocked GPT. | Yes. Best first home for Cycle U protected or supporting assertions. |
| `tests/helpers/golden_replay.py` | Replay runner wrapper, observed-turn projection, drift classification, long-session summaries, continuity bridge, fallback escalation summaries. | Projects `route_kind`, `selected_speaker_id`, FEM fields, sanitizer fields, runtime lineage, continuity validation, and long-session metrics. | Yes. Primary helper seam. |
| `docs/testing/protected_replay_manifest.md` | Governance declaration for protected/supporting/advisory replay lanes. | Declares `frontier_gate_social_inquiry_20_turn` protected and scenario-spine CLI advisory. | Yes, if Cycle U adds protected entries. |
| `data/validation/scenario_spines/frontier_gate_long_session.json` | Canonical long-session fixture. | `branch_social_inquiry` 25 turns, `branch_direct_intrusion` 25 turns, `branch_cautious_observe` 10 turns; long branches total 50. | Yes. Best fixture source for 20-50 turn suites. |
| `game/scenario_spine.py` | Scenario-spine schema/model/validation. | Enforces long-session minimums for non-smoke definitions. | Yes, likely unchanged unless new fixture schema is needed. |
| `game/scenario_spine_eval.py` | Offline whole-session evaluator. | State continuity, referent persistence, progression, branch coherence, metadata completeness, degradation over time. | Yes. Use through existing bridge; avoid changing scoring first. |
| `tools/run_scenario_spine_validation.py` | API-backed scenario-spine runner and artifact writer. | Per-branch transcript/health/debug/operator artifacts; aggregate branch divergence/runtime lineage for `--all-branches`. | Yes for advisory/manual or later nightly; not safest first protected gate. |
| `tests/test_scenario_spine_eval.py` | Evaluator contracts. | 24 collected tests; includes clean 25-turn branch, late amnesia, filler growth, referent loss, branch divergence. | Yes as supporting validation. |
| `tests/test_run_scenario_spine_validation.py` | Runner/artifact contracts. | 21 collected tests; artifact shape, branch aliases, all-branches aggregate, runtime lineage summary. | Yes as artifact and command reference. |
| `game/runtime_lineage_telemetry.py` | Runtime lineage event normalization/summarization. | Frequencies by event kind, fallback kind, owner bucket, gate path, repair kind, mutation kind, recurrence. | Yes. Stable read-side aggregation seam. |
| `game/final_emission_replay_projection.py` | FEM-to-runtime-lineage projection. | Projects fallback selection, gate outcome, speaker repair, continuity repair, response-type repair, sanitizer/final-emission mutation events. | Yes for observability; avoid behavior changes. |
| `game/final_emission_meta.py` | FEM normalization/read helpers and stable observability bundle. | Emits/normalizes final source, fallback family, owner buckets, mutation lineage, `fem_runtime_lineage_events`. | Yes as read source. High fanout, change carefully. |
| `tests/helpers/failure_dashboard_report.py` | Protected replay failure report and dashboard rows. | Writes `artifacts/golden_replay/replay_failure_report.md` on protected failures. | Yes for failure artifact presence. |
| `tests/helpers/failure_classifier.py` and `tests/failure_classification_contract.py` | Replay failure taxonomy and owner hints. | Classifies speaker/route/fallback/continuity/projection/sanitizer failures. | Yes if new failure categories/tags are needed. |
| `tests/helpers/transcript_runner.py` | Storage patching, clean campaign, transcript snapshots. | Used by golden replay; no TestClient needed. | Yes. Reuse, do not fork. |
| `tests/helpers/transcript_snapshots.py` | Snapshot projection from chat payload/session state. | Exposes current interlocutor and active target for transcript lanes. | Yes as secondary speaker/continuity evidence. |
| `tests/test_transcript_regression.py` | Slow transcript-style multi-turn regressions. | Several 2-5-ish turn continuity/retry/transition cases. | Supporting only; too broad for first Cycle U block. |
| `tests/test_transcript_gauntlet_actor_addressing.py` | Transcript actor binding and address continuity. | Multi-turn speaker/target persistence around guard/runner. | Supporting only. |
| `tests/test_transcript_gauntlet_campaign_cleanliness.py` | Campaign reset/social persistence and lead/travel sequencing. | Multi-turn reset and state cleanliness. | Supporting only. |
| `docs/scenario_spine_validation.md` | Scenario-spine lane documentation. | Documents `--all-branches`, 50-turn long-branch coverage band, artifacts, commands. | Yes for block plan and commands. |
| `docs/cycles/cycle_n_long_session_stability_closure_2026-05-27.md` | Prior closure for 20-turn long-session stability. | States what Cycle N proves and what remains unproven: 50-turn, live model, semantic quality, hard-fail CLI health. | Yes; key prior-art handoff. |

## Existing Coverage

Current executable replay coverage is strongest in `tests/test_golden_replay.py`:

- Protected short scenarios cover directed NPC questions, vocative overrides, wrong-speaker strict-social repair, thin answer/action outcome repair, sanitizer scaffold leakage, lead follow-up dialogue lock, and opening fallback ownership.
- Protected long scenario `frontier_gate_social_inquiry_20_turn` runs the first 20 prompts from `branch_social_inquiry` with mocked GPT.
- That long scenario asserts completion, bounded route/speaker changes, bounded missing speaker observations, bounded fallback recurrence, no fallback owner oscillation, no fallback spiral, no scaffold leakage, no progressive degradation, no late referent/continuity loss, and bounded mutation/fallback lineage.

Existing long-session fixtures:

| Path | Turn Count | Validates | Cycle U Gaps |
|---|---:|---|---|
| `data/validation/scenario_spines/frontier_gate_long_session.json::branch_social_inquiry` | 25 | Social inquiry, notice/runner/watch continuity, long-session anchors. First 20 are protected through golden replay. | Turns 21-25 are not protected in golden replay. |
| `data/validation/scenario_spines/frontier_gate_long_session.json::branch_direct_intrusion` | 25 | Direct intrusion/pressure alternate from same start. | Not protected as golden replay; useful for route/fallback stress. |
| `data/validation/scenario_spines/frontier_gate_long_session.json::branch_cautious_observe` | 10 | Short contrast branch for divergence/wiring. | Below Cycle U 20-turn target. |
| `tools/run_scenario_spine_validation.py --all-branches` over canonical fixture | 60 total, 50 long-branch scripted | Aggregate artifacts, branch divergence, coverage band, runtime lineage. | Advisory/manual; not a protected hard-fail gate. |
| `tests/test_scenario_spine_eval.py` synthetic rows from fixture | 25 | Clean branch, progressive degradation, late amnesia, generic filler, referent loss. | Evaluator-only, not full chat pipeline. |
| `tests/test_golden_replay.py::frontier_gate_social_inquiry_20_turn` | 20 | Protected sustained social route, speaker, fallback, continuity, mutation metrics. | One branch only; no resume/checkpoint or 50-turn aggregate. |
| Transcript gauntlet/regression tests | Usually 2-5 | Speaker continuity, retry forward progress, reset cleanliness, lead/travel flow. | Not 20+ and not declared protected replay. |

Golden snapshots/drift:

- `classify_golden_drift(...)` supports exact, structural, and semantic drift, but exact prose is opt-in.
- `render_golden_replay_markdown_report(...)` and `render_long_session_replay_summary_markdown(...)` provide compact failure/debug summaries.
- Protected replay failure artifacts are recorded through `tests/helpers/failure_dashboard_report.py`.

## Observability Map

| Field / Signal | Exact Name | Produced By | Tests Can Read From | Stable For Assertions? |
|---|---|---|---|---|
| Route kind | `route_kind` | `tests/helpers/golden_replay.py::_observed_turn` from payload resolution/trace | Golden replay observed turn | Yes, smoke/aggregate. |
| Resolution kind | `resolution_kind` | Chat payload `resolution.kind` projection | Golden replay observed turn | Yes, smoke/aggregate. |
| Social route | `trace.social_contract_trace.route_selected` | `game/api_turn_support.py::build_social_contract_turn_trace` | Observed turn `trace.social_contract_trace` | Yes when available; allow unavailable for non-social turns. |
| Speaker id | `selected_speaker_id` | Golden replay projection from social trace, latest target snapshot, or resolution social NPC | Golden replay observed turn | Yes, aggregate/strict when scenario expects a target. |
| Speaker source | `selected_speaker_source` | Golden replay projection | Golden replay observed turn | Diagnostic/smoke. |
| Reply owner | `final_reply_owner`, `reply_owner_actor_id`, `visible_grounded_speaker` | Social contract trace | Observed turn nested trace | Yes if present; use with availability guard. |
| Continuity status | `continuity_status` | `game/api_turn_support.py::build_social_contract_turn_trace` | `trace.social_contract_trace` | Smoke/diagnostic; availability varies. |
| Fallback anchor source | `fallback_anchor_source` | Post-emission speaker adoption/stale invalidation overlay in API turn support | `trace.social_contract_trace` | Smoke/diagnostic. |
| Current interlocutor | `current_interlocutor` | Session snapshot in `tests/helpers/transcript_snapshots.py` | Transcript snapshots | Yes for transcript-specific tests. |
| Active target | `active_interaction_target_id` | Session `interaction_context` | Transcript snapshots, prompt contracts, social tests | Yes for targeted continuity assertions. |
| Final emitted source | `final_emitted_source` | Final emission metadata | Observed turn / FEM | Yes, structural. |
| Fallback family | `fallback_family`, `fallback_family_used`, `realization_fallback_family` | FEM normalization/projection | Observed turn / runtime lineage | Yes, aggregate. |
| Fallback kind | `fallback_kind` | Runtime lineage events from `game/final_emission_replay_projection.py` | `runtime_lineage_events`, lineage summary | Yes, aggregate. |
| Fallback owner bucket | `fallback_owner_bucket`, plus `opening_fallback_owner_bucket`, `sealed_fallback_owner_bucket`, `visibility_fallback_owner_bucket` | FEM and replay projection | Observed turn / lineage summary | Yes for known families; diagnostic for mixed fallback families. |
| Fallback temporal frame | `fallback_temporal_frame` | FEM | Observed turn | Diagnostic/smoke. |
| Fallback behavior repair | `fallback_behavior_repaired`, `fallback_behavior_repair_kind`, `fallback_behavior_repair_mode` | FEM | Observed turn / escalation summary | Yes, aggregate. |
| Response-type repair | `response_type_repair_used`, `response_type_repair_kind` | FEM | Observed turn / escalation summary | Yes, aggregate. |
| Upstream prepared fallback | `upstream_prepared_emission_used`, `upstream_prepared_emission_valid`, `upstream_prepared_emission_source`, `upstream_prepared_emission_reject_reason` | FEM | Observed turn | Yes for protected source locks. |
| Gate path | `gate_path` | Runtime lineage event `gate_outcome` | `runtime_lineage_events`, `gate_path_frequency` | Yes, aggregate. |
| Event kind | `event_kind` | `make_runtime_lineage_event(...)` | Runtime lineage summary `by_event_kind` | Yes. |
| Mutation kind | `mutation_kind` | `game/final_emission_replay_projection.py` | Runtime lineage summary `mutation_kind_frequency` | Yes, aggregate. |
| Final mutation lineage | `final_emission_mutation_lineage` | FEM mutation lineage helpers | Observed turn | Yes, aggregate; avoid exact per-turn overreach. |
| Continuity repair | `interaction_continuity_repair`, `interaction_continuity_validation`, `interaction_continuity_enforced` | `game/final_emission_gate.py` metadata merge helpers | FEM / observed turn | Smoke/diagnostic; raw validation can be noisy. |
| Speaker repair | `speaker_contract_enforcement_reason`, lineage `repair_kind` | Speaker contract/FEM replay projection | Observed turn / lineage summary `speaker_repair_frequency` | Yes, aggregate. |
| Source family | `final_emitted_source`, `fallback_authorship_source`, `upstream_prepared_emission_source` | FEM/provenance helpers | Observed turn / reports | Yes for known protected seams. |
| Recurrence | `recurrence_key`, `recurring_events` | Runtime lineage telemetry | Lineage summary | Yes, strong signal for spiral detection. |
| Session health | `session_health.classification`, `overall_passed`, `long_session_band` | `game/scenario_spine_eval.py` | Continuity bridge result | Yes, aggregate. |
| Degradation | `degradation_over_time.progressive_degradation_detected`, `reason_codes`, late-window `signals` | Scenario-spine evaluator | Continuity bridge result | Yes, but text/audit-context dependent. |
| Artifact presence | `artifacts/golden_replay/replay_failure_report.md`; scenario-spine artifact paths | Failure dashboard / scenario-spine runner | File system in tests or CI | Yes for renderer contracts; avoid generating artifacts in normal unit tests unless failure-only. |

## Proposed Assertions

| Assertion | Data Needed | Already Exposed? | Recommended Strength |
|---|---|---|---|
| Bounded replay drift over 20-25 turns | `route_change_count`, `speaker_change_count`, `fallback_total_count`, `mutation_kind_frequency`, `scaffold_leakage` | Yes | Strict for existing protected branch. |
| 50-turn aggregate drift stays bounded | Scenario-spine `--all-branches` transcripts, `aggregate_session_health_summary.json`, runtime lineage summary | Yes, but advisory | Diagnostic first, then nightly/manual. |
| Stable speaker persistence | `selected_speaker_id`, `trace.social_contract_trace.final_reply_owner`, `active_interaction_target_id`, `current_interlocutor` | Yes | Strict only for turns with explicit/direct target expectation; aggregate otherwise. |
| Continuity persists across 20-50 turns | Scenario-spine continuity bridge, `session_health`, `degradation_over_time`, `interaction_continuity_validation` | Yes | Strict on evaluator/degradation; diagnostic on raw interaction-continuity counts. |
| No fallback escalation spiral | `fallback_escalation_summary`, lineage `fallback_frequency`, `fallback_owner_bucket_frequency`, `recurring_events`, repair counts | Yes | Strict for protected 20-turn; smoke/diagnostic for new branches until baseline known. |
| Route stability over time | `route_sequence`, `route_frequency`, `gate_path_frequency`, `trace.social_contract_trace.route_selected` | Yes | Aggregate threshold; avoid exact route sequence unless fixture route is deterministic. |
| Mutation accumulation explainable | `mutation_turn_count`, `final_emission_mutation_lineage`, `mutation_kind_frequency`, `recurring_events` | Yes | Smoke first: no unknown/exploding recurrence; strict once per-family baseline exists. |
| Fallback owner does not oscillate | `fallback_owner_change_count`, `fallback_lineage_owner_change_count`, `fallback_owner_bucket_frequency` | Yes | Strict for current protected branch; smoke for direct-intrusion branch. |
| No late fallback spike | fallback early/middle/late window counts, `late_window_fallback_count`, `max_fallback_streak` | Yes | Strict for protected branch. |
| Artifact/report present on failure | protected replay failure report renderer, long-session markdown debug context | Yes | Strict renderer unit contract; failure-only integration behavior. |
| Resume/checkpoint persistence | snapshot/resume hooks and persisted session fields | Partially; scenario runner has `--mark-snapshot-resume-pending`, storage supports snapshots | Diagnostic first; needs fixture design. |

## Risk Areas

- `tests/test_golden_replay.py` is already protected and CI-selected by `-m golden_replay`; adding expensive or flaky Cycle U cases there immediately affects the hard-fail lane.
- Scenario-spine CLI health is documented as advisory. Promoting `tools/run_scenario_spine_validation.py --all-branches` to hard-fail needs separate exit-policy work.
- Scenario-spine continuity/degradation is partly text heuristic based. Cycle N added deterministic audit context for the protected replay bridge; new branches may need similar context to avoid false late-anchor loss.
- Raw `interaction_continuity_validation` was previously considered noisy for hard failure; prefer scenario-spine degradation assertions for continuity.
- `model_routing_escalation_observable` is explicitly not observable from the current protected golden replay turn observations. Do not assert model-routing escalation frequency without adding a real field.
- `branch_direct_intrusion` likely has different fallback/route behavior from social inquiry; apply diagnostic baselining before strict thresholds.
- Runtime lineage is intentionally observational. It is safe for aggregate assertions, but should not become a live routing policy source.
- Existing transcript regressions are marked slow and broad. They are good supporting evidence but risky as the first Cycle U implementation surface.
- Current git status already has unrelated untracked Cycle N/O report files. Do not overwrite or clean those as part of Cycle U.
- Some committed JSON/text contains mojibake display for em dashes/curly apostrophes in PowerShell output; avoid exact text assertions against those fixture strings.

## Recommended Implementation Blocks

| Block | Goal | Files Likely Touched | Expected Tests | Risk | Parallelizable? |
|---|---|---|---|---|---|
| U1 - Full-Branch Golden Baseline | Extend protected/supporting golden replay from first 20 turns to full 25-turn `branch_social_inquiry`, or add a supporting 25-turn variant with current metrics. | `tests/test_golden_replay.py`, maybe `tests/helpers/golden_replay.py`, `docs/testing/protected_replay_manifest.md` if protected. | Single new/updated golden test, `tests/test_golden_replay.py`, `-m golden_replay`. | Medium | Yes, with U4 docs/artifact work. |
| U2 - Direct-Intrusion Diagnostic Branch | Add a diagnostic/supporting 20-25 turn `branch_direct_intrusion` run to baseline route/fallback/mutation behavior before strict gating. | `tests/test_golden_replay.py`, fixture setup helper if needed. | Targeted new test plus `tests/test_scenario_spine_eval.py`. | Medium-high | Yes after U1 helper shape is settled. |
| U3 - 50-Turn Aggregate Advisory/Nightly Plan | Wire or document a non-default `--all-branches` validation command/report review using existing scenario-spine artifacts. | `docs/scenario_spine_validation.md` or new report/docs; maybe automation later. | `tests/test_run_scenario_spine_validation.py`; manual CLI smoke only if requested. | Medium | Yes; docs/reporting only. |
| U4 - Mutation Accumulation Diagnostics | Add summary fields for mutation kind recurrence, unknown mutation kinds, and per-window mutation counts if current summaries are insufficient. | `tests/helpers/golden_replay.py`, `tests/test_golden_replay.py`. | Golden helper renderer test and protected long replay. | Low-medium | Yes, but coordinate helper edits with U1/U2. |
| U5 - Resume/Checkpoint Persistence Probe | Design a deterministic replay segment split around snapshot/resume or persisted session inspection. | `tests/test_golden_replay.py`, storage/snapshot test helpers; possibly scenario runner only if using `--mark-snapshot-resume-pending`. | New supporting test first; targeted storage/session tests. | Medium-high | Mostly independent after U1. |
| U6 - Failure Artifact Contract | Ensure long-session failure context includes route/speaker/fallback/mutation/continuity summary and source branch/turn ids. | `tests/helpers/golden_replay.py`, `tests/helpers/failure_dashboard_report.py`, `tests/test_golden_replay.py`. | Renderer/failure-report unit tests. | Low-medium | Yes. |

## Commands Run

Search/recon commands:

```powershell
rg --files
git status --short
rg -n "replay|golden|snapshot|drift|route stability|fallback|mutation kind|mutation_kind|speaker|continuity|lineage|protected replay|manifest|long-session|long session" .
rg -n "protected_replay|golden_replay|drift|long-session|long session|20-turn|25 turns|fallback escalation|route stability|runtime_lineage|mutation_kind|speaker_repair|continuity_drift|replay" tests tools docs data game -g "*.py" -g "*.md" -g "*.json"
rg -n "skip|xfail|TODO|fragile|flaky|known instability|snapshot|replay|fallback|speaker|continuity|route" tests docs audits game tools -g "*.py" -g "*.md"
rg -n "turns|turn_id|player_prompt|script|transcript|run_transcript|branch_social_inquiry|long_session|frontier_gate_long_session" tests tools data docs -g "*.py" -g "*.json" -g "*.md"
rg -n "def summarize_long_session|def evaluate_golden_replay_continuity|def render_long_session|def render_golden|def _observed_turn|fallback_escalation|lineage_summary|route_change_count|speaker_change_count" tests\helpers\golden_replay.py tests\test_golden_replay.py
rg -n "def make_runtime_lineage_event|def normalize_runtime_lineage_events|def summarize_runtime_lineage_events|event_kind|fallback_frequency|mutation_kind_frequency|recurrence" game\runtime_lineage_telemetry.py tests\test_runtime_lineage_telemetry.py
rg -n "def build_fem_runtime_lineage_events|fallback_kind|fallback_family|owner_bucket|gate_path|mutation_kind|speaker_repair|repair_kind|final_emitted_source|final_emission_mutation_lineage|fem_runtime_lineage_events" game\final_emission_meta.py game\final_emission_replay_projection.py tests\test_final_emission_meta.py tests\test_run_scenario_spine_validation.py
rg -n "long_session|degradation|continuity|referent|metadata|branch_divergence|long_session_band|progressive_degradation|speaker|fallback" game\scenario_spine_eval.py tests\test_scenario_spine_eval.py tests\test_scenario_spine_contracts.py tests\test_scenario_spine_continuation_convergence.py
rg -n "branch_social_inquiry|branch_direct_intrusion|branch_cautious_observe|frontier_gate_long_session|25 turns|10 turns|scenario_spine_validation|runtime_lineage_summary|compact_operator_summary|aggregate_session_health_summary|--spine|--branch|--max-turns|--all-branches" tools\run_scenario_spine_validation.py tests\test_run_scenario_spine_validation.py docs\scenario_spine_validation.md docs\reports\cycle_n_block_n1_canonical_20_turn_replay_2026-05-27.md docs\reports\cycle_n_block_n3_continuity_drift_bridge_2026-05-27.md docs\reports\cycle_n_block_n4_fallback_escalation_guard_2026-05-27.md
rg -n "^def test_" tests\test_golden_replay.py tests\test_scenario_spine_eval.py tests\test_run_scenario_spine_validation.py tests\test_transcript_regression.py tests\test_transcript_gauntlet_actor_addressing.py tests\test_transcript_gauntlet_campaign_cleanliness.py tests\test_runtime_lineage_telemetry.py tests\test_final_emission_meta.py
rg -n "current_interlocutor|active_interaction_target_id|interaction_continuity|continuity_status|fallback_anchor_source|visible_grounded_speaker|route_selected|social_contract_trace|selected_speaker" game tests -g "*.py"
```

Files read:

```powershell
Get-Content -Path tests\helpers\golden_replay.py
Get-Content -Path tests\test_golden_replay.py
Get-Content -Path docs\testing\protected_replay_manifest.md
Get-Content -Path docs\reports\cycle_n_long_session_stability_recon_2026-05-27.md
Get-Content -Path data\validation\scenario_spines\frontier_gate_long_session.json
Get-Content -Path tests\helpers\transcript_runner.py
Get-Content -Path docs\reports\cycle_n_block_n1_canonical_20_turn_replay_2026-05-27.md
Get-Content -Path docs\reports\cycle_n_block_n3_continuity_drift_bridge_2026-05-27.md
Get-Content -Path docs\reports\cycle_n_block_n4_fallback_escalation_guard_2026-05-27.md
Get-Content -Path docs\reports\cycle_n_long_session_stability_closure_2026-05-27.md
```

Pytest collection commands:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_golden_replay.py --collect-only -q
# Result: tests/test_golden_replay.py: 35

$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_scenario_spine_eval.py tests/test_run_scenario_spine_validation.py --collect-only -q
# Result: tests/test_run_scenario_spine_validation.py: 21; tests/test_scenario_spine_eval.py: 24

$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -m golden_replay --collect-only -q
# Result: tests/test_golden_replay.py: 35
```

Discovered protected replay commands:

```powershell
python -m pytest tests/test_golden_replay.py -q
python -m pytest -m golden_replay -q
python -m pytest tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_20_turn_structural_stability -q
```

Discovered scenario-spine commands:

```powershell
python tools/run_scenario_spine_validation.py --list
python tools/run_scenario_spine_validation.py --branch branch_social_inquiry --smoke
python tools/run_scenario_spine_validation.py --branch branch_social_inquiry
python tools/run_scenario_spine_validation.py --all-branches
python tools/run_scenario_spine_validation.py --base-url http://127.0.0.1:8000 --branch branch_social_inquiry
py -3 tools/run_scenario_spine_validation.py --list
py -3 tools/run_scenario_spine_validation.py --branch branch_social_inquiry --smoke
```

No targeted runtime tests were run beyond collection in this recon, to avoid creating replay artifacts or updating snapshots.

## Open Questions / Files To Provide To ChatGPT

- Should Cycle U promote a full 25-turn `branch_social_inquiry` replay into protected golden replay, or land first as supporting?
- Should `branch_direct_intrusion` be a protected stress branch or a diagnostic baseline first?
- Is Cycle U expected to include a hard-fail 50-turn aggregate gate, or only a documented/manual/nightly command?
- What persistence mode should count for "continuity persistence": in-memory session across turns, saved session reload, snapshot restore, or scenario-spine resume marker?
- Should model-routing escalation become explicitly observable in golden replay turn observations, or remain outside the sustained-session lane?
- What mutation kinds are expected/allowed over 20-50 turns for each branch family?
- Provide any desired CI runtime budget for `-m golden_replay` before adding 25/50-turn protected coverage.
