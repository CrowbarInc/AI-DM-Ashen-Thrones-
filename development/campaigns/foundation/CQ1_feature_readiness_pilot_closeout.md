# CQ1 — Feature Readiness Pilot Closeout

**Date:** 2026-06-28  
**Scope:** First intentionally small production feature after CK–CQ foundation program.  
**Primary metric:** Feature Integration Cost  
**Authority:** [CQ_foundation_completion_assessment_discovery.md](CQ_foundation_completion_assessment_discovery.md), [CB_feature_boundary_registry.json](docs/audits/CB_feature_boundary_registry.json), [CJ4_feature_guardrail_pilot.md](docs/audits/CJ4_feature_guardrail_pilot.md)

---

## Executive Summary

CQ1 implemented **one narrowly scoped safe-domain feature** — content lint **`scene_finding_counts`** report metric plus CLI summary — and measured integration cost against foundation guardrails.

**Outcome:** **PASS.** The feature landed in **5 files** (1 production, 1 tooling, 3 tests), touched **zero** replay, fallback, validator, sanitizer, or ownership-registry surfaces, and required **no golden artifact regeneration**. Domain tests: **96 passed**. Ownership, replay-boundary, and gate-boundary governance: **22 passed**.

**Recommendation:** **Continue Feature Pilots** in safe registry domains using the CB2/CJ4 additive-report pattern. Do not infer equal locality for caution or prohibited domains.

---

## 1. Candidate Features (Ranked)

Candidates evaluated against CQ1 constraints: narrow production area, no replay schema expansion, no ownership registry expansion, no final-emission / validator / sanitizer redesign.

| Rank | Feature | Impl risk | User value | Arch impact | Notes |
|---:|---|---|---|---|---|
| 1 | **Content lint `scene_finding_counts` + CLI `scene_findings=` metric** | **Low** | **Medium** (author diagnostics) | **Minimal** | Extends proven CB2/CJ4 pattern; `content_lint_validation` safe domain |
| 2 | Content lint `top_warning_codes` in report JSON | Low | Medium | Minimal | Same domain; slightly more presenter logic if surfaced beyond JSON |
| 3 | UI debug tab: active UI mode badge | Low–Medium | Low–Medium | Low | `ui_mode_frontend` safe domain; touches `static/` + API contract |
| 4 | UI mode: expose `allowed_state_channels` in debug API | Low | Low (operator) | Low | Safe domain; small API payload extension |
| 5 | Playability eval: one new offline scoring axis | Low | Medium (validation reports) | Low | `behavioral_playability_evaluators` safe; advisory only |
| 6 | Combat: named condition template (e.g. Shaken) | Low | High (gameplay) | Medium | Safe mechanics domain but player-visible; wider test fanout |
| 7 | Journal: export last N events as copyable text | Medium | High | Medium | `world_scenes_affordances` caution-adjacent; replay-smoke decision risk |

### Recommendation

**Implement rank #1 — `scene_finding_counts`.**

Rationale: CB2/CJ4 already validated the additive `ContentLintReport.as_dict()` + CLI summary pattern in the same domain. Per-scene finding counts complement existing `code_family_counts` without new lint rules, emit-path coupling, or schema redesign. Lowest integration risk with immediate author-time value (identify which scenes concentrate warnings/errors).

---

## 2. Extension Boundary Verification

**Feature:** CQ1-01 — `scene_finding_counts` report field + CLI `scene_findings=` metric  
**Registry domain:** `content_lint_validation` (**safe**)

### Existing ownership

| Owner | Role |
|---|---|
| `game/content_lint.py` | Canonical author-time lint engine and report serialization |
| `game/validation.py` | Strict scene validation issues collected into lint messages |
| `tools/run_content_lint.py` | CLI disk loader and report presenter |
| `tests/test_content_lint.py` | Engine rule and report shape tests |
| `tests/test_content_lint_tool.py` | CLI contract and exit-code tests |

### Extension point used

- `ContentLintReport.as_dict()` — additive diagnostic field (same seam as CB2 `code_family_counts`)
- `tools/run_content_lint.py` `_render_cli_report()` — optional one-line summary metric

New helpers (localized):

- `GLOBAL_SCENE_FINDING_KEY` (`"_global"`) — bucket for messages without `scene_id`
- `summarize_scene_finding_counts()` — count messages by scene id, sorted keys

### Nearby surfaces (not touched)

| Surface | Proximity | Touched? |
|---|---|---|
| Replay helpers (`golden_replay*`, projection facades) | None — author-time only | **No** |
| Fallback helpers (`final_emission_*_fallback`, diegetic fallback) | None | **No** |
| Validators (`final_emission_validators.py`) | None | **No** |
| Sanitizer (`output_sanitizer.py`) | None | **No** |
| Ownership registry (`tests/test_ownership_registry.py`) | None | **No** |
| Protected replay manifest / golden artifacts | None | **No** |

### Isolation answer

**Yes.** The feature remains isolated within the `content_lint_validation` safe domain. No imports from `final_emission*`, `fallback*`, `response_policy*`, or `golden_replay*` were added. Lint rule passes, exit codes, and message collection semantics are unchanged.

---

## 3. Feature Implemented

### Description

Author-time per-scene finding summary:

- **`scene_finding_counts`** — new field on `ContentLintReport.as_dict()` counting messages by `scene_id`; unscoped messages use `"_global"` (aligned with CLI `[global]` section).
- **CLI quiet summary** — optional `scene_findings=hub:2,island:1` metric when findings exist (sorted scene keys).

Deterministic: sorted dict keys; no gameplay or emit-path behavior change.

---

## 4. Integration Cost

| Category | Count | Files |
|---|---:|---|
| **Production** | **1** | `game/content_lint.py` |
| **Tests** | **3** | `tests/test_content_lint.py`, `tests/test_content_lint_tool.py`, `tests/test_content_lint_bundle.py` |
| **Tooling** | **1** | `tools/run_content_lint.py` |
| **Governance/docs (feature diff)** | **0** | — |
| **Replay helpers** | **0** | — |
| **Fallback helpers** | **0** | — |
| **Validator helpers** | **0** | — |
| **Total (feature diff)** | **5** | +66 / −3 lines |

**Unexpected architectural expansion:** **None.**

**Incidental test alignment:** `tests/test_content_lint_bundle.py::test_lint_all_content_merges_bundle_passes_without_changing_report_shape` was stale (predated CB2 `code_family_counts`). Updated to assert current canonical report keys including both additive metrics. This is test-contract alignment, not architectural expansion.

---

## 5. Validation Results

### Domain tests (required — SAFE_G1)

```text
py -3 -m pytest tests/test_content_lint.py tests/test_content_lint_tool.py \
  tests/test_content_lint_bundle.py tests/test_content_lint_n2_closure.py -q
```

| Result | Detail |
|---|---|
| **96 passed** | ~7.8 s |

New tests:

- `test_summarize_scene_finding_counts_groups_by_scene_id`
- `test_cli_summary_includes_scene_finding_metric_for_warnings`

### Foundation guardrails (targeted)

```text
py -3 -m pytest tests/test_ownership_registry.py \
  tests/test_replay_boundary_governance.py tests/test_gate_boundary_governance.py -q
```

| Suite | Result |
|---|---|
| Ownership registry | **Passed** |
| Replay boundary governance | **Passed** |
| Gate boundary governance | **Passed** |

### Not run (by design)

| Suite | Reason |
|---|---|
| Golden replay (`-m golden_replay`) | No replay/projection/emit-path changes; golden artifacts not regenerated |
| Full convergence CI | CQ1 scoped to domain + boundary slices |

### Pre-existing failures (unrelated to CQ1)

`tests/test_ownership_write_path_governance.py` — 2 failures (`test_bu8_bu4_production_ownership_write_paths_parity_locked`, `test_bu9_visibility_fallback_producer_stamp_pairing_locked`) on `final_emission_meta.py` / `final_emission_visibility_metadata.py` stamp routing. **Not introduced by this feature** (no files in that subsystem touched).

---

## 6. Architectural Assessment

| Question | Answer | Detail |
|---|---|---|
| Did the feature remain local? | **Yes** | 5 files, 1 production module, single safe domain |
| Require unexpected coordination? | **No** | No cross-team seams, no registry edits, no replay smoke |
| Expose hidden coupling? | **Minor** | Stale bundle test expected pre-CB2 report shape; fixed in same PR slice |
| Create new fallback pressure? | **No** | Zero fallback imports or behavior |
| Increase governance pressure? | **No** | No inventory, registry, or CI matrix changes |

**Corrective locality assessment:** If this feature regressed, a fix would touch **≤1 production file** (`game/content_lint.py`) plus domain tests — consistent with CP cohort median of 1 production file per corrective fix.

**Foundation impact:** **Neutral.** Replay stability, ownership boundaries, projection contracts, and deterministic output on gameplay paths unchanged. Author-time report JSON shape extended additively only.

---

## 7. Comparison to CJ4 (CB2 Pilot)

| Metric | CJ4-01 (`code_family_counts`) | CQ1-01 (`scene_finding_counts`) |
|---|---:|---:|
| Total files | 4 | **5** |
| Production files | 1 | 1 |
| Test files | 2 | **3** (+ bundle shape alignment) |
| Tooling files | 1 | 1 |
| Governance/replay/projection | 0 | 0 |
| Classification | Highly Local | **Highly Local** |

CQ1 confirms the safe-domain additive-report pattern remains cheap after CK–CQ foundation work. Integration cost is within one file of CJ4, with the extra test file being contract alignment rather than architectural fanout.

---

## 8. Recommendation

| Rating | **Continue Feature Pilots** |
|---|---|

**Rationale:**

- Feature integration cost stayed **Highly Local** (5 files, 0 prohibited surfaces).
- Foundation guardrails held: no replay churn, no ownership registry expansion, no fallback or validator pressure.
- Safe-domain throughput validated twice (CB2/CJ4 + CQ1) with consistent patterns.

**Next steps (optional, not in CQ1 scope):**

- Run additional safe-domain pilots in `ui_mode_frontend` or `behavioral_playability_evaluators` to confirm locality outside content lint.
- Keep caution/prohibited domains on stronger gates (replay smoke, registry runs, emit-path review).
- Address pre-existing BU8/BU9 write-path parity drift separately as foundation hygiene — not as a CQ1 blocker.

**Do not yet:** Return to foundation-only mode globally; **do not** infer unconstrained feature-first work on emit-path seams.

---

## Files Modified (Feature Diff)

| File | Change |
|---|---|
| `game/content_lint.py` | `GLOBAL_SCENE_FINDING_KEY`, `summarize_scene_finding_counts()`, `scene_finding_counts` on `as_dict()` |
| `tools/run_content_lint.py` | `_format_scene_finding_counts()`, summary line metric |
| `tests/test_content_lint.py` | Report shape + summarize unit test |
| `tests/test_content_lint_tool.py` | JSON key set + CLI summary test |
| `tests/test_content_lint_bundle.py` | Canonical report key assertion updated |
