# CF6 — Generated Projection Artifact Governance

## Executive Summary

Replay projection produces **two distinct artifact layers**: (1) **acceptance-critical** contracts verified in CI without committed golden files, and (2) **generated advisory/diagnostic snapshots** under `artifacts/golden_replay/` and related paths.

**Primary finding:** Semantic projection changes today create **predictable, minimal required review** when scoped correctly:

| Change type | Required review surface |
|---|---|
| Protected field registry / drift bucket | `docs/testing/protected_replay_manifest.md` generated section (CI `--check`) + focused pytest suites |
| Projection behavior (no registry change) | Pytest assertions only — **no** mandatory artifact refresh |
| Corpus / FEM storage changes | Optional advisory reports (`projection_gap_reality`, `projection_drift_watch`) via BV3F refresh |
| Protected replay failures (opt-in) | Failure dashboard cascade (6 families) — diagnostic, not acceptance |

**Projection Artifact Churn (primary metric):** CE6 established retention classes; CF6 adds **importance classification**, **per-generator ownership**, and **explicit regeneration boundaries**. The former monolithic `projection_governance_reports` family was split into three generator-owned families so BV3F corpus refresh no longer implies coverage-report refresh.

**Runtime behavior unchanged.** Registry and documentation only.

---

## Artifact Inventory

| Artifact | Classification | Generator | Consumer | Required For CI |
|---|---|---|---|---|
| `docs/testing/protected_replay_manifest.md` (generated field-path section) | acceptance-critical | `tools/refresh_protected_replay_manifest.py` | CI convergence-checks; manifest reviewers | **Yes** (`--check`) |
| Pytest golden replay assertions (`pytest -m golden_replay`) | acceptance-critical | `tests/helpers/golden_replay.py` + projection assembler | CI golden replay gate | **Yes** (no committed artifact) |
| `artifacts/golden_replay/trend_window/` (BW lane) | governance | `tools/run_protected_replay_trend.py` | BW closeout tests | **Yes** (frozen baseline) |
| `artifacts/golden_replay/trend_window_2/` (BZ lane) | governance | `tools/run_protected_replay_trend.py` | BZ movement tests | **Yes** (movement outputs) |
| `artifacts/golden_replay/replay_failure_corpus_observations.md` | governance | `tools/expand_protected_replay_observations.py` | observation expansion governance | No |
| `artifacts/golden_replay/bug_recurrence_event_log.legacy.json` | governance | (frozen) | historical comparison | No |
| `artifacts/golden_replay/bv1*b_fallback_incidence_report*` | governance | BV closeout tools | incidence baseline comparison | No |
| `artifacts/golden_replay/projection_coverage_report.json` | advisory | `tools/fallback_projection_coverage_audit.py` | BP2 coverage closeout | No |
| `artifacts/golden_replay/projection_gap_reality_report.json` | advisory | `tools/fallback_projection_gap_reality_audit.py` | BP3 gap audit; BV3F refresh | No |
| `artifacts/golden_replay/projection_drift_watch_report.{json,md}` | advisory | `tools/projection_drift_watch.py` | BP3 drift watch; BV3F refresh | No |
| `artifacts/golden_replay/fallback_*` portfolio reports | advisory | `tools/fallback_*.py` | fallback governance closeouts | No |
| `artifacts/golden_replay/replay_failure_report.md` | diagnostic | `failure_dashboard_report` cascade | failure closeout reviewers | No |
| `artifacts/golden_replay/bug_recurrence_*` | diagnostic | `failure_dashboard_recurrence` cascade | recurrence triage | No |
| `artifacts/golden_replay/owner_drift_*` | diagnostic | drift/hotspot/trend/risk writers | drift triage | No |
| `audits/failure_dashboard_latest.md` | diagnostic | `write_failure_dashboard_artifact` | local dashboard triage | No |
| `artifacts/golden_replay/replay_maintenance_metrics.*` | developer convenience | `tools/replay_maintenance_metrics.py` | CE1 metrics | No (gitignored) |
| `artifacts/golden_replay/rerun_drift_scorecard.*` | developer convenience | opt-in pytest writer | local rerun compare | No (gitignored) |
| `artifacts/golden_replay/long_session_stability_scorecard.*` | developer convenience | opt-in pytest writer | local stability review | No (gitignored) |
| CI `protected-replay-failure-report` upload | ephemeral | GitHub Actions on failure | CI artifact browser | No |

Full machine inventory: `tests/helpers/golden_replay_artifact_manifest.py::projection_generated_artifact_inventory()` (19 golden-replay families + manifest row).

### Per-artifact ownership (canonical)

| Artifact family | Canonical owner | Generation entry point | Review owner | First-line test | Governance owner |
|---|---|---|---|---|---|
| Manifest field paths | `golden_replay_projection_manifest` | `refresh_protected_replay_manifest.py --write` | same | `test_golden_replay_projection_manifest.py` | `golden_replay_artifact_manifest` |
| Projection coverage | `golden_replay_projection` | `fallback_projection_coverage_audit.py` | same | `test_fallback_projection_coverage_audit.py` | same |
| Projection gap reality | `golden_replay_projection` | `fallback_projection_gap_reality_audit.py` | same | `test_fallback_projection_gap_reality_audit.py` | same |
| Projection drift watch | `golden_replay_projection` | `projection_drift_watch.py` | same | `test_projection_drift_watch.py` | same |
| Trend windows | `protected_replay_trend_movement` | `run_protected_replay_trend.py` | same | `test_bz_protected_replay_trend_window_2.py` | same |
| Failure dashboard cascade | `failure_dashboard_report` | `write_protected_replay_failure_report_if_present` | per-family helpers | `test_failure_dashboard_*` | `golden_replay_artifact_manifest` |
| Fallback portfolio | `runtime_lineage_reporting` | per-tool `tools/fallback_*.py` | same | fallback governance tests | same |

**Duplicate ownership risk:** None identified for projection-specific artifacts after CF6 split. Failure dashboard cascade intentionally shares one pytest opt-in trigger across six families (documented coupling).

---

## Regeneration Matrix

| Artifact | Trigger | Expected Regeneration | Notes |
|---|---|---|---|
| Protected manifest generated section | `PROTECTED_OBSERVATION_FIELDS` / drift bucket edit | **Yes** — `--write` + commit | Only acceptance-critical **committed** artifact for ordinary projection schema work |
| Golden replay pytest assertions | Any semantic projection behavior change | **Yes** — update tests | No file artifact; CI gate |
| `projection_coverage_report.json` | Shape catalog or projector coverage change | Manual / closeout | **Not** in BV3F bundle |
| `projection_gap_reality_report.json` | `artifacts/` or `data/` corpus change | BV3F `refresh_projection_artifacts()` | Full-repo scan; advisory |
| `projection_drift_watch_report.*` | Same as gap reality | BV3F bundle | Paired JSON+MD advisory |
| Trend window BW | Explicit BW closeout only | Rare | Frozen — semantic projection edits should **not** touch |
| Trend window BZ | Explicit BZ refresh | Governance closeout only | Not ordinary field edits |
| Bug recurrence + owner drift families | `ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest` | Opt-in only | Coupled cascade — 6 families |
| Fallback portfolio reports | Manual tool runs | Closeout only | Unrelated to projection manifest |
| Local scorecards / maintenance metrics | Opt-in env / manual tool | Local only | Gitignored |

### Unnecessary coupling (highlighted)

| Coupling | Severity | CF6 action |
|---|---|---|
| Failure dashboard writes failure report + recurrence + 4 owner-drift families together | Medium | Documented in manifest; not split (writer orchestration unchanged) |
| Former single `projection_governance_reports` family implied coverage refreshes with BV3F | Medium | **Resolved** — split into 3 generator-owned families |
| BV3F refresh runs gap + drift but not coverage | Low (positive) | Documented via `PROJECTION_CORPUS_REFRESH_ARTIFACT_PATHS` |
| Paired JSON/Markdown diagnostic outputs | Low | Structural auditability tradeoff (CE6) |

---

## Ownership Findings

| Artifact | Canonical Owner | Duplicate Ownership | Risk |
|---|---|---|---|
| Manifest generated section | `golden_replay_projection_manifest` | None | Low — single `--check` CI entry |
| Projection coverage/gap/drift | `golden_replay_projection` (governance); tools own execution | None after split | Low |
| Trend windows | `protected_replay_trend_movement` | None | Low — BW/BZ lanes explicit |
| Failure dashboard cascade | `failure_dashboard_report` orchestrates; sub-writers own formats | Overlapping trigger, not duplicate generators | Medium churn if opt-in pytest run committed drive-by |
| Fallback portfolio | `runtime_lineage_reporting` + per-tool scripts | Tool fan-out, single governance owner | Low |
| Golden replay observation (non-artifact) | `golden_replay_projection::project_turn_observation` | Runtime FEM projection separate (by design) | Low — AO5 guarded |

---

## Review Burden Findings

| Artifact | Review Required | Reason | Recommendation |
|---|---|---|---|
| Manifest generated section | **Yes** on registry edits | CI gate | Run `--check` locally before push |
| Pytest golden replay | **Yes** on semantic changes | Acceptance authority | Use CF1–CF5 focused suites for locality |
| `projection_coverage_report.json` | Only on shape-catalog closeout | Advisory | Do not refresh for ordinary projection edits |
| Gap/drift watch reports | Only on corpus refresh closeout | Advisory | Use BV3F bundle; skip if corpus unchanged |
| Bug recurrence / owner drift | Only intentional governance refresh | High-churn diagnostic | Avoid committing local dashboard output |
| Trend window BW | Rare explicit closeout | Frozen baseline | Never drive-by regenerate |
| Trend window BZ | BZ governance events | Movement evidence | Separate commit from projection code |
| Fallback portfolio JSON/MD | Fallback governance only | Unrelated to projection | Do not bundle with projection PRs |
| Local scorecards / maintenance metrics | Never | Gitignored | Regenerate freely locally |
| Failure dashboard latest | Optional | High-churn | Treat as scratch unless closeout |

**Review noise reduction:** Semantic projection PRs should touch manifest (if registry changed) + pytest only. Advisory scans and diagnostic snapshots are **out of scope** unless the PR explicitly changes corpus or governance evidence.

---

## Changes Made

| Item | Change |
|---|---|
| `tests/helpers/golden_replay_artifact_manifest.py` | Added CF6 `importance`, `generator`, `consumer`, `ci_required`, ownership fields; split projection reports into 3 families; added `projection_generated_artifact_inventory()`, corpus refresh path constant, cascade documentation |
| `tests/test_cf6_generated_projection_artifact_governance.py` | **Added** — 9 governance contract tests |
| `artifacts/golden_replay/artifact_manifest.md` | Added CF6 importance table, regeneration boundaries, split projection families |
| `artifacts/golden_replay/README.md` | Linked acceptance-critical manifest contract |
| `docs/audits/CF6_generated_projection_artifact_governance.md` | **Added** — this report |

No replay semantics, writer orchestration, or tool execution behavior changed.

---

## Behavior Changes

**Expected default: none.**

No runtime projection, FEM normalization, or pytest assertion behavior was modified. Registry classification and documentation only.

---

## Remaining Risks

1. **Failure dashboard cascade** still regenerates six committed families from one opt-in pytest flag — local runs can dirty working tree (CE6 known issue; documented, not fixed).
2. **Tracked diagnostic snapshots** (`bug_recurrence_*`, `owner_drift_*`) remain high-churn if committed accidentally.
3. **`audits/failure_dashboard_latest.md`** is tracked but diagnostic — future closeout could untrack or gitignore.
4. **Trend window `_storage/` bulk** — low frequency but large diffs when BZ lane refreshes.
5. **Acceptance is test-based, not artifact-based** — reviewers must distinguish pytest failures (required) from advisory JSON drift (optional).

---

## Recommended Next Block

**Proceed with CF7** focused on **synthetic row / classifier evidence bridge** (per CF discovery backlog), with shifted priority:

1. **Optional CF7-pre:** Untrack or gitignore operational diagnostic snapshots (`bug_recurrence_*`, `owner_drift_*`) with explicit refresh commit workflow — reduces churn without changing acceptance.
2. **CF7 core:** Table-driven tests distinguishing `observed_projection_schema_defaults` synthetic rows from genuinely projected unavailable fields (CF discovery drift source).
3. **Defer:** Further failure-dashboard writer decomposition unless churn metric worsens.

CF6 acceptance criteria met:

- [x] Every generated projection artifact has a documented owner
- [x] Acceptance-critical artifacts distinguished from advisory outputs
- [x] Regeneration boundaries explicit (manifest CI, BV3F bundle, dashboard cascade)
- [x] Review burden documented with recommendations
- [x] Runtime behavior unchanged
- [x] CF7 can proceed without guessing artifact scope
