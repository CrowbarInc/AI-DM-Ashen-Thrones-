# Cycle AU Golden Replay Ownership Compression Recon

## Executive summary

`tests/test_golden_replay.py` is not the highest-churn test file overall, but it is the highest-churn replay gauntlet file in the current late-cycle window: 27 commits total, 11 commits since 2026-05-30, compared with 8 recent touches for `tests/test_final_emission_gate.py` and 6-7 for nearby governance/owner files. The reason is visible in the file itself: it is simultaneously acting as golden replay orchestrator, replay projection contract suite, manifest parity lock, failure dashboard reporter test, rerun drift scorecard test, long-session stability metric test, owner-bucket projection test, runtime lineage diagnostic test, and broad end-to-end scenario suite.

The safe Cycle AU direction is to keep golden replay's hard-fail scenarios and protected observed-turn coverage intact while moving API-level/synthetic assertion families to clearer owner surfaces. The lowest-risk moves are projection/schema locks into projection-specific tests or helpers, failure/report rendering locks into failure dashboard contract tests, owner-bucket projection helpers into owner proof modules, and route/speaker expectation construction into helper-level contracts. Do not move the full protected scenarios or byte-sensitive diagnostics without a separate closeout block.

## Files inspected

- `tests/test_golden_replay.py` lines 1-3100: primary hotspot.
- `tests/helpers/golden_replay.py` lines 55-1692: expectation helpers, replay runner, drift comparison, summaries, scorecards.
- `tests/helpers/golden_replay_projection.py` lines 70-1118: protected observation registry, extraction registry, projection adapter, fallback-family read-side rule.
- `tests/helpers/golden_replay_fixtures.py` lines 95-424: chat stubs, seed worlds, payload factories, synthetic projection helpers.
- `tests/helpers/failure_dashboard_report.py` lines 59-1409: dashboard/report artifact ownership, protected replay failure report, scorecard writers.
- `tests/helpers/replay_drift_taxonomy.py` lines 82-1015 and related `replay_drift_*` helpers: owner drift taxonomy, stability/history/hotspot/risk projection.
- `tests/helpers/opening_fallback_evidence.py` lines 34-194: opening fallback evidence constants and observed-field factories.
- `game/final_emission_replay_projection.py` lines 71-211+: runtime lineage read-side projection.
- `tests/test_failure_classification_contract.py` lines 55-382: classifier/evidence/owner-bucket contract ownership.
- `tests/test_opening_fallback_owner_bucket.py` lines 1-148: canonical owner-bucket mapping.
- `tests/test_final_emission_meta.py`, `tests/test_final_emission_gate.py`, `tests/test_ownership_registry.py`, `tests/test_stability_reporting_contract.py`, `tests/test_replay_drift_taxonomy.py`, `tests/test_replay_drift_risk.py`: nearby owner/contract surfaces.
- Existing recon/closeout notes in `audits/cycle_ag_*`, `audits/cycle_ak_*`, `cycle_aq_*`.

## Golden replay ownership map

`tests/test_golden_replay.py` declares the intended boundary at lines 122-128: golden replay owns replay observation/projection contracts, projection is centralized in `tests.helpers.golden_replay_projection`, and repeated route/speaker/fallback/final-emission fields are diagnostic locks rather than runtime subsystem ownership.

Major sections:

- Projection adapter and protected registry locks, lines 131-498.
- Assertion helper and protected failure reporting locks, lines 498-653.
- Drift classification and runtime-lineage diagnostic handling, lines 656-737.
- Rerun comparison, response-delta, scorecard, markdown, writer behavior, lines 742-1134.
- Long-session summaries and stability scorecards, roughly lines 1134-1491.
- Opening/fallback/lineage/owner-bucket projection locks, lines 1513-2032.
- End-to-end protected and supporting replay scenarios, lines 2056-3100.

## Assertion family inventory

| Family | Current location | Protects | Likely owner | Move candidate? | Fixture-shape dependency | Duplication / nearby surface |
|---|---:|---|---|---|---|---|
| Projection adapter equivalence | `test_golden_replay.py:131` | `project_turn_observation` equals `_observed_turn`; protected paths sorted and bucketed | replay projection | Yes, to `tests/test_golden_replay_projection.py` or helper contract | Synthetic payload only | `tests/helpers/golden_replay_projection.py:592-614` |
| Dual fallback-family read-side precedence | `:159-237`, `:460-495` | `fallback_family_used` preferred over `realization_fallback_family`; raw FEM not rewritten | replay projection / final emission projection boundary | Yes, projection owner test | Synthetic payload only | `tests/test_final_emission_meta.py:1474`, `golden_replay_projection.py:899-932` |
| Protected manifest parity | `:268-398` | generated manifest matches protected registry | inventory/report ownership | Yes, into manifest-specific test or projection contract | No replay fixture dependency | `tools/refresh_protected_replay_manifest.py`, `docs/testing/protected_replay_manifest.md` |
| Protected path representation | `:301-460` | every protected path projected or marked unavailable; extraction registry count 41 | replay projection | Yes | Synthetic payloads | `protected_path_representation_errors`, `protected_observation_extraction_registry` |
| Assertion helper behavior | `:498-542` | dotted paths, debug messages, unavailable semantics | replay assertion helper | Yes, helper-local test | Synthetic row only | `tests/helpers/golden_replay.py:230-444` |
| Protected failure report bridge | `:545-653` | failure rows, owner classification, report headings, rerun command text | diagnostics / failure dashboard | Yes, mostly to dashboard/report contract | Synthetic row only | `failure_dashboard_report.py:403-1240`; `test_failure_classification_contract.py` |
| Drift classifier bucket counts | `:656-737` | exact/structural/semantic drift and lineage not classified unless opted-in | diagnostics / classifier | Partial move to classifier/dashboard tests | Synthetic row only | `tests/test_failure_classifier.py`, `test_failure_classification_contract.py` |
| Rerun comparison deltas | `:742-970` | speaker, route, fallback, text hash, optional metadata, response delta | replay projection / drift taxonomy | Partial move | Synthetic row only | `tests/test_replay_drift_taxonomy.py:169-284`; `tests/helpers/replay_drift_taxonomy.py` |
| Rerun scorecard rendering/writers | `:984-1087` | JSON/markdown output and opt-in behavior | diagnostics/report ownership | Yes | Synthetic scorecard only | `failure_dashboard_report.py:839-1032` |
| Golden markdown renderer | `:1101-1134` | deterministic report rendering | replay report helper | Yes | Synthetic rows only | `golden_replay.py:544` |
| Long-session summaries/stability | `:1134-1491`, `:2511-3001` | long-session metrics, continuity, fallback escalation, owner drift | replay metrics / stability reporting | Partial; helper contract tests yes, E2E thresholds stay | Synthetic rows plus real long fixture | `test_stability_reporting_contract.py`, `tests/stability_reporting_contract.py`, `replay_drift_taxonomy.py` |
| Opening fallback owner projection | `:1513-1576`, `:2394-2456` | canonical upstream-prepared bucket, no compatibility-local ownership | fallback ownership / replay projection | Partial | Synthetic and direct gate seam | `test_opening_fallback_owner_bucket.py`, `opening_fallback_evidence.py` |
| Runtime lineage projection | `:1528-1576`, `:1654-1720` | existing events preferred; FEM-derived lineage keys | final emission replay projection | Yes for synthetic projection proofs | Synthetic rows | `game/final_emission_replay_projection.py` |
| Sealed/strict/visibility fallback owner projection | `:1680-1748` | sealed owner buckets and content/selection owner split | fallback/final emission projection | Yes for synthetic projection proofs | Synthetic rows | `test_failure_classification_contract.py:258-270`, `test_final_emission_meta.py` |
| Upstream prepared emission telemetry | `:1749-1898` | used/valid/source/reject reason, malformed classification evidence | gate/final emission/projection | Partial | Synthetic rows | `test_failure_classification_contract.py:283-287` |
| Sanitizer lineage/fallback projection | `:1900-2032` | sanitizer-owned empty fallback, strict-social split, debug-derived lineage | sanitizer / replay projection | Yes for synthetic projection proofs | Synthetic rows | `test_failure_classification_contract.py:301`, output sanitizer tests |
| Protected E2E route/speaker scenarios | `:2056-2292`, `:2459-2510` | route/speaker/final emission locks through real `chat` path | golden replay | No, except helper extraction | Full replay fixture/harness | owner tests can remain narrower |
| Long-session E2E stability | `:2511-3001` | 25-turn stability, resume persistence, diagnostic branch thresholds | golden replay / stability support | Mostly no | Full long-session fixture | helper-level metric proofs can move |
| Scenario spine smoke orchestration | `:3004-3100` | branch identity, smoke replay shape | golden replay orchestration | No | In-file dynamic spine | `game/scenario_spine*`, run-scenario validation tests |

## Touch concentration

History evidence:

- `tests/test_golden_replay.py`: 27 commits total.
- Since 2026-05-30: 11 commits.
- Recent commits touching it:
  - `dcf8d0a` 2026-06-06 `AT: Longitudinal Stability Promotion` (+287 lines)
  - `6210a5d` 2026-06-06 `AR: Replay Drift Classification`
  - `8195287` 2026-06-04 `AS: Downstream Dependency Reduction`
  - `927dae2` 2026-06-03 `AO: Replay Ownership Consolidation`
  - `59c14aa` 2026-06-03 `AP: Fallback Authorship Resolution`
  - `43de427` 2026-06-02 `AK: Replay Schema Maintenance Compression Recon` (+195 lines)
  - `49e4147` 2026-05-31 `Cycle AG: residual complexity burn-down`
  - `2d0ca82` 2026-05-31 `Cycle AC replay surface compression` (large rewrite)
  - `2274f26` 2026-05-31 `Complete Cycle AE: Change Locality Optimization`
  - `b54b311` 2026-05-31 `Close Cycle AB fallback topology collapse`
  - `0ef46f3` 2026-05-30 `T: reduce maintenance locality fanout`

Comparison against nearby files:

| File | All commits | Since 2026-05-30 |
|---|---:|---:|
| `tests/test_golden_replay.py` | 27 | 11 |
| `tests/test_final_emission_gate.py` | 45 | 8 |
| `tests/test_ownership_registry.py` | 9 | 7 |
| `tests/test_final_emission_meta.py` | 21 | 6 |
| `tests/test_failure_classification_contract.py` | 11 | 6 |
| `tests/test_opening_fallback_owner_bucket.py` | 8 | 6 |
| `tests/test_failure_classifier.py` | 12 | 3 |
| `tests/test_fallback_behavior_gate.py` | 10 | 3 |

So the precise conclusion is: it is not the most frequently touched test file over full history, but it is the most touched replay/golden file and the current late-cycle replay/governance hotspot. The recurring reasons are visible in commit names and diffs: baseline creation, failure dashboard, fallback ownership, runtime lineage, replay cost/compression, long-session stability, schema maintenance, ownership consolidation, replay drift classification, and stability promotion.

## Existing owner surfaces

- `tests/helpers/golden_replay_projection.py`: best owner for projection adapter, protected registry, extraction registry, unavailable coverage, dual fallback-family read-side projection.
- `tests/helpers/golden_replay.py`: best owner for reusable expectation builders, replay runner, drift comparison, long-session metric generation. Current helper already owns `protected_route_expectation`, `protected_social_structural_base`, `compare_golden_replay_reruns`, `summarize_long_session_replay_observations`, and `build_long_session_stability_scorecard`.
- `tests/helpers/failure_dashboard_report.py`: best owner for protected replay failure reports, rerun scorecard markdown/JSON writers, artifact opt-in behavior.
- `tests/test_failure_classification_contract.py`: best owner for classifier evidence schema, allowed owner buckets, taxonomy contract, dashboard diagnostic headers.
- `tests/test_replay_drift_taxonomy.py`, `test_replay_drift_hotspots.py`, `test_replay_drift_risk.py`, `test_replay_drift_longitudinal.py`, `test_replay_drift_trends.py`: best owner surfaces for owner drift classification and aggregation.
- `tests/test_opening_fallback_owner_bucket.py` plus `tests/helpers/opening_fallback_evidence.py`: best owner for opening fallback bucket mapping and evidence factories.
- `game/final_emission_replay_projection.py` plus `tests/test_final_emission_meta.py`: best owner for read-side runtime lineage and sealed replacement subkind projection.
- `tests/test_final_emission_gate.py`: runtime gate orchestration owner, not a golden observed-turn owner.
- `tests/test_stability_reporting_contract.py` and `tests/stability_reporting_contract.py`: best owner for stability reporting schema/governance; golden replay remains metric-generation source.
- `tests/test_ownership_registry.py`: best owner for declaring that golden replay is a gauntlet neighbor rather than a live legality direct owner.

## Helper and fixture duplication

- `_synthetic_rerun_turn` and `_synthetic_rerun_scorecard` in `test_golden_replay.py:742` and `:984` are conceptually shared with replay drift taxonomy/risk tests. Candidate: owner-specific synthetic scorecard factories in a helper module, or keep local if only AU splits tests by file.
- Repeated direct projection setup using `project_synthetic_turn`, `fem_payload`, and `minimal_gm_output_payload` is already centralized in `tests/helpers/golden_replay_fixtures.py`; the assertions are what remain concentrated.
- Opening fallback expected observed fields are partly centralized in `opening_fallback_evidence.py:178-194`; golden replay still repeats bucket/source assertions around `:1513`, `:2394`.
- Route/speaker expectation composition is already centralized in `golden_replay.py:65-207`; future AU work should avoid adding more inline expectation dicts where those helpers suffice.
- Report header/string expectations are concentrated in golden replay but owned by `failure_dashboard_report.py`; candidate for report contract tests with only one thin golden bridge left.
- Long-session threshold blocks repeat similar summaries across social-inquiry, resume, and diagnostic branches. Candidate: helper-level assertion functions only if they preserve byte-identical debug context and thresholds.

## Safe compression candidates

1. Projection registry contract extraction
   - Current: `tests/test_golden_replay.py:131-498`
   - Proposed: new `tests/test_golden_replay_projection.py` or existing projection contract file.
   - Why safe: synthetic payloads exercise helper APIs without running replay; coverage can move 1:1.
   - Must pass: `python -m pytest tests/test_golden_replay.py -q --tb=short`, new projection test file, `python tools/refresh_protected_replay_manifest.py --check`.
   - Risk: low.
   - Separate block: yes, AU1/AU2.

2. Failure report and rerun scorecard rendering relocation
   - Current: `tests/test_golden_replay.py:545-653`, `:1006-1087`.
   - Proposed: `tests/test_failure_classification_contract.py` or new `tests/test_failure_dashboard_report.py`.
   - Why safe: these use synthetic rows and report writers; no gameplay replay semantics.
   - Must pass: `tests/test_failure_classification_contract.py`, `tests/test_failure_dashboard_controlled_failures.py`, golden replay lane.
   - Risk: low-medium because markdown text is byte-sensitive.
   - Separate block: yes.

3. Rerun drift taxonomy split
   - Current: `tests/test_golden_replay.py:785-970`, parts of `:1372-1491`.
   - Proposed: `tests/test_replay_drift_taxonomy.py` and `tests/test_replay_drift_risk.py`.
   - Why safe: replay comparison remains in helper; synthetic scorecard proofs can live beside taxonomy/risk consumers.
   - Must pass: replay drift taxonomy/risk/hotspot/trend/longitudinal tests plus golden replay.
   - Risk: low-medium due import/factory reuse.
   - Separate block: yes.

4. Fallback owner projection proof relocation
   - Current: `tests/test_golden_replay.py:1513-2032`.
   - Proposed: projection-owner tests plus owner-specific contract tests for opening, sealed, visibility, sanitizer, upstream-prepared telemetry.
   - Why safe: synthetic `project_synthetic_turn` assertions can move while protected E2E replay keeps end-to-end coverage.
   - Must pass: `tests/test_opening_fallback_owner_bucket.py`, `tests/test_final_emission_meta.py`, `tests/test_failure_classification_contract.py`, golden replay.
   - Risk: medium because owner mapping language is easy to blur.
   - Separate block: yes.

5. Route/speaker expectation helper contract
   - Current: helpers in `tests/helpers/golden_replay.py:65-207`, verified indirectly throughout `test_golden_replay.py`.
   - Proposed: a focused helper contract test for `protected_social_structural_base` / `protected_route_expectation`, leaving scenario assertions thin.
   - Why safe: no runtime behavior; preserves existing helper outputs.
   - Must pass: `tests/test_golden_replay.py -k "directed_npc_question or vocative_override or lead_followup"`.
   - Risk: low.
   - Separate block: optional early block.

6. Long-session threshold helper extraction
   - Current: `tests/test_golden_replay.py:2511-3001`.
   - Proposed: helper assertions in `tests/helpers/golden_replay.py` or a test-local helper module; E2E scenarios call one helper per branch.
   - Why safe: reduces repeated threshold assertions without moving the protected scenario.
   - Must pass: `tests/test_golden_replay.py -k "frontier_gate" -q --tb=short`.
   - Risk: medium; threshold/debug churn risk.
   - Separate block: yes, late.

7. Manifest/inventory command parity test
   - Current: `tests/test_golden_replay.py:268-398`.
   - Proposed: owner-specific manifest test near projection registry or tools tests.
   - Why safe: checks generated docs against registry; no replay execution.
   - Must pass: `python tools/refresh_protected_replay_manifest.py --check`, `python -m pytest tests/test_ownership_registry.py -q`.
   - Risk: low.
   - Separate block: yes.

## Things not to move

- Full hard-fail protected replay scenarios should remain golden replay coverage: `directed_npc_question`, `vocative_override_after_prior_continuity`, `wrong_speaker_strict_social_emission`, `thin_answer_action_outcome_final_emission`, `sanitizer_scaffold_leakage`, `lead_followup_with_dialogue_lock`, and the long-session social-inquiry baseline.
- Do not remove or weaken `pytestmark = [pytest.mark.integration, pytest.mark.golden_replay]` at `test_golden_replay.py:122`.
- Do not alter expected diagnostic strings that users/CI read, including report headings such as `# Protected Replay Failure Report`, `## Failure Locator`, `### Protected replay lane`, and command text `python -m pytest -m golden_replay -q --tb=short` asserted at `:605-622`.
- Do not change protected observation path count/shape (`41`) without a manifest-governed block.
- Do not rewrite fallback-family semantics. The read-side precedence rule is locked at `:159-237`, but raw FEM must remain uncollapsed.
- Do not move long-session fixture data or branch thresholds casually. The 25-turn assertions at `:2511-3001` carry acceptance signal and debug context.
- Avoid moving dynamic in-file scenario-spine smoke construction at `:3004-3100` until replay thin-orchestrator closeout; it proves orchestration shape, not just helper output.

## Recommended AU block sequence

### AU1 - Replay Assertion Family Inventory

Create an inventory-only map of assertion families, probably as generated or static docs data. No tests move. Confirm every assertion family has an owner bucket and a "golden stays/moves" decision.

Validation: `python -m pytest tests/test_golden_replay.py -q --tb=short`; `python tools/test_audit.py --check`.

### AU2 - Owner Mapping Extraction

Extract or document owner mapping for projection/report/taxonomy surfaces. Keep golden replay unchanged except possibly importing constants/helpers from owner modules.

Validation: `python -m pytest tests/test_ownership_registry.py tests/test_failure_classification_contract.py -q --tb=short`; `python tools/test_audit.py --check`.

### AU3 - Route/Speaker Assertion Compression

Add focused helper contract tests for `protected_route_expectation`, `protected_social_structural_base`, and common speaker proof fragments. Thin scenario tests only by replacing inline dict duplication with existing helper fragments.

Validation: `python -m pytest tests/test_golden_replay.py -k "directed_npc_question or vocative_override or wrong_speaker or lead_followup" -q --tb=short`; full golden replay lane afterward.

### AU4 - Fallback Proof Ownership Relocation

Move synthetic fallback owner-bucket, dual-family, sealed/visibility/upstream-prepared/sanitizer projection proofs into owner-specific projection/contract files. Keep E2E golden locks that prove those fields survive the replay path.

Validation: `python -m pytest tests/test_opening_fallback_owner_bucket.py tests/test_final_emission_meta.py tests/test_failure_classification_contract.py -q --tb=short`; `python -m pytest tests/test_golden_replay.py -k "opening_fallback or sanitizer or fallback_owner or prepared_projection" -q --tb=short`.

### AU5 - Diagnostics / Report Ownership Relocation

Move protected failure report, rerun scorecard, markdown writer, and opt-in artifact tests to dashboard/report contract tests. Keep a single golden bridge test if needed.

Validation: `python -m pytest tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q --tb=short`; `python -m pytest tests/test_golden_replay.py -k "protected_golden_assertion_failure or rerun_drift or markdown_report" -q --tb=short`.

### AU6 - Replay Projection Contract File

Create a projection-focused test module for `project_turn_observation`, protected path representation, extraction registry parity, raw signal presence, and manifest parity. Remove only synthetic projection contract tests from `test_golden_replay.py` after parity passes.

Validation: new projection test file; `python tools/refresh_protected_replay_manifest.py --check`; `python -m pytest tests/test_golden_replay.py -q --tb=short`.

### AU7 - Golden Replay Thin Orchestrator Closeout

Only after the owner tests exist, make `test_golden_replay.py` read as an orchestrator: protected scenarios, long-session acceptance, scenario-spine smoke, and a minimal bridge to projection/diagnostics. Avoid behavior or snapshot changes.

Validation: `python -m pytest tests/test_golden_replay.py -q --tb=short`; `python -m pytest -m golden_replay -q --tb=short`; `python tools/test_audit.py --check`.

## Validation commands

Existing commands surfaced by repo docs/tests:

```bash
python -m pytest tests/test_golden_replay.py -q --tb=short
python -m pytest -m golden_replay -q --tb=short
python -m pytest tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q --tb=short
python -m pytest tests/test_opening_fallback_owner_bucket.py tests/test_final_emission_meta.py tests/test_ownership_registry.py -q --tb=short
python -m pytest tests/test_replay_drift_taxonomy.py tests/test_replay_drift_hotspots.py tests/test_replay_drift_longitudinal.py tests/test_replay_drift_trends.py tests/test_replay_drift_risk.py -q --tb=short
python -m pytest tests/test_stability_reporting_contract.py -q --tb=short
python tools/refresh_protected_replay_manifest.py --check
python tools/test_audit.py --check
python tools/test_audit.py
```

Optional diagnostics/artifacts:

```bash
python -m pytest -m golden_replay -q --write-failure-dashboard
ASHEN_WRITE_FAILURE_DASHBOARD=1 python -m pytest -m golden_replay -q
python -m pytest -m failure_dashboard_probe -q
python -m pytest -m failure_dashboard_probe -q --write-failure-dashboard
```

## Open questions / files to pass back to ChatGPT if needed

- Should AU create one new `tests/test_golden_replay_projection.py`, or split by owner (`test_replay_projection_contract.py`, `test_replay_reporting_contract.py`, etc.)? I recommend one projection file plus existing owner files to avoid a new mega-test.
- Should `_synthetic_rerun_turn` become a shared helper? If only two or three files need it, a small `tests/helpers/replay_drift_fixtures.py` is cleaner than importing test-local functions.
- Should long-session threshold assertions become helper functions? This reduces duplication but can hide acceptance thresholds; defer until AU7.
- Confirm whether `tests/test_golden_replay.py` should remain the only `golden_replay` marker owner, or whether moved projection/diagnostic tests should also carry the marker. I recommend keeping the marker on hard replay coverage only unless CI explicitly needs projection contracts in the same lane.

