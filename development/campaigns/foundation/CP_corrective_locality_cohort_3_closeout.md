# CP — Corrective Locality Cohort #3 Closeout

Date: 2026-06-28  
Planning authority: `CP_corrective_locality_cohort_3_discovery.md`, CP1–CP7 slice reports  
Scope: measurement and assessment only — **no additional fixes implemented**

---

## Executive Summary

Corrective Locality Cohort #3 executed **7 slices** (CP1–CP7) against the discovery candidate set. The cohort produced **4 qualifying corrective fixes** and **3 validation-only probes** with **zero governance code churn** and **zero golden/manifest rewrites**.

### Overall verdict: **Moderate improvement**

**Supporting evidence:**

| Signal | CP Cohort #3 | CA Baseline (frozen v1, N=10) | Direction |
|---|---:|---:|---|
| Median production files per fix | **1.0** | 2.5 | ↓ 60% |
| Median total code files per fix | **2.0** | 7.0 (effective) | ↓ 71% |
| Maximum production files per fix | **1** | 9 | ↓ |
| Maximum total code files per fix | **3** | 538 (raw max; polluted) | ↓ |
| Governance code files touched | **0** | not isolated in baseline | improved |
| Golden/manifest edits | **0** | present in historical cohort | improved |
| Repair-family concentration | 4 subsystems, no opening_fallback dominance | 60% opening_fallback | improved diversity |

Locality per fix is **materially better** than the frozen CA baseline on every observed median/max production metric. However:

- Sample size is **N=4** qualifying fixes (below CA12 comparison-ready threshold of 5).
- **43% validation-only rate** (3/7 slices) indicates many probed surfaces are already stable.
- **Persistence across multiple cohort cycles is not yet proven** — this is a single deliberate cohort, not a time-series replication.
- One qualifying fix (CP5) was **read-side only** (0 production files).

**Corrective Locality Trend:** Descriptively meaningful and directionally improved, but **not yet statistically definitive** at conventional confidence levels given N=4 and the high validation-only share.

**Persistence:** **Plausibly improved** for the cohort execution model (bounded slices, stop-on-no-defect), but **not proven** beyond this single cycle.

---

## 1. Completed Cohort Classification

### Summary counts

| Classification | Slices | Share |
|---|---:|---:|
| Qualifying corrective fix | 4 | 57.1% |
| Validation-only | 3 | 42.9% |
| Excluded (not executed as slice) | 2+ | — |

Discovery candidates **not executed** as dedicated slices: CP8 (long-session scenario spine — deferred/high risk), CP7-opening-authorship (superseded by opportunistic CP7 terminal-repair slice), CP9 (absorbed into CP1 combined probe).

---

### Complete cohort table

| Slice | Classification | Subsystem | Root cause (summary) | Prod files | Test files | Helper/replay | Governance code | Recurrence evidence |
|---|---|---|---|---:|---:|---:|---:|---|
| **CP1** | Validation-only | Preflight/config + sanitizer | No defect reproduced; existing safeguards hold for CP9 preflight clamp/skip paths and CP1 scaffold-leak blocking | 0 | 0 | 0 | 0 | Historical `scaffold_leakage` key; protected node passes; no new failure |
| **CP2** | **Qualifying fix** | Routing / directed social entry | `_GENERIC_ADDRESS_PATTERNS` missed `what does the {role} see\|know\|…` — dialogue lane without bound target | 1 | 1 | 0 | 0 | New unit prevention test; protected `directed_npc_question` unchanged pass |
| **CP3** | **Qualifying fix** | Vocative / speaker targeting | Discourse vocative regex required comma; dash and bare-question vocatives failed to override continuity | 1 | 1 | 0 | 0 | Historical speaker-drift keys; 2 new regression tests; protected vocative golden pass |
| **CP4** | Validation-only | BX guard speaker identity parity | No parity drift reproduced; BX Cases A–D and lifecycle probes aligned | 0 | 0 | 0 | 0 | BX marker gate green; historical corpus rows not live failures |
| **CP5** | **Qualifying fix** | Replay projection / fallback taxonomy | Bridge `final_emitted_source` overwritten by generic `realization_fallback_family` in read-side precedence | 0 | 2 | 1 | 0 | Long-session fallback escalation misclassification prevented; CO102 sentinel unchanged |
| **CP6** | Validation-only | Dialogue lock / lead follow-up continuity | No lock break reproduced; narration interrupt and multi-NPC switch behave as designed | 0 | 0 | 0 | 0 | Protected `lead_followup_with_dialogue_lock` pass; no new failure |
| **CP7** | **Qualifying fix** | Terminal retry / minimal repair | Scene anchor required non-empty `visible_facts`; tavern has empty list despite location/summary | 1 | 0 | 0 | 0 | 3/7 Block 14 regression tests failed before fix; no protected recurrence key |

**Production file note:** CP2 and CP3 both modified `game/interaction_context.py` in separate, independent fixes (different root causes, same authoritative binding module).

---

## 2. Locality Statistics (Qualifying Fixes Only)

Qualifying fixes: **CP2, CP3, CP5, CP7** (N=4)

### Core metrics

| Metric | Value |
|---|---:|
| Total qualifying fixes | 4 |
| Average production files touched | 0.75 |
| **Median production files touched** | **1.0** |
| Average total code files touched | 2.0 |
| **Median total code files touched** | **2.0** |
| Maximum production files touched | 1 |
| Maximum total code files touched | 3 |

*Total code files = production + test + helper/replay helper files. Slice report markdown excluded.*

### Per-fix breakdown

| Fix | Production | Tests | Helpers | Total code |
|---|---:|---:|---:|---:|
| CP2 | 1 | 1 | 0 | 2 |
| CP3 | 1 | 1 | 0 | 2 |
| CP5 | 0 | 2 | 1 | 3 |
| CP7 | 1 | 0 | 0 | 1 |

### Cohort rates

| Rate | Value | Notes |
|---|---:|---|
| Validation-only rate (all 7 slices) | 42.9% (3/7) | CP1, CP4, CP6 |
| Corrective-fix rate (all 7 slices) | 57.1% (4/7) | CP2, CP3, CP5, CP7 |
| Production : test file ratio (qualifying) | 1 : 1 | 3 production, 3 test |
| Production : (test + helper) ratio | 3 : 4 | CP5 helper counts as replay surface |
| Governance code involvement rate | 0% (0/7) | Reports only; no matrix/manifest/registry edits |
| Replay/helper involvement rate (qualifying) | 25% (1/4) | CP5 only |

---

## 3. Diversity Analysis

### Subsystems represented by qualifying fixes

| Subsystem | Fix(es) | Independent? |
|---|---|---|
| Routing / canonical social entry | CP2 | Yes |
| Vocative / speaker override | CP3 | Yes (same prod module as CP2, different defect class) |
| Replay projection / fallback observation | CP5 | Yes |
| Terminal retry / minimal resolution repair | CP7 | Yes |

**Independent subsystem count: 4** (from 4 qualifying fixes)

### Validation-only coverage (stability probes)

| Subsystem probed | Slice |
|---|---|
| Preflight / config / sanitizer | CP1 |
| BX guard speaker identity matrix | CP4 |
| Dialogue lock / multi-turn continuity | CP6 |

### Diversity assessment

| Criterion | Assessment |
|---|---|
| Sufficient for trend conclusions? | **Partially** — 4 distinct subsystems beats CA baseline opening_fallback concentration (60%), but N=4 is small |
| Over-concentration risk | **Low–moderate** — two fixes in `interaction_context.py`; otherwise spread across routing, projection, retry |
| Discovery coverage | **Good** — 5 of 7 planned low/medium candidates probed; CP8 deferred; opening-authorship not reproduced |
| Validation-only diversity | **Good** — sanitizer, speaker parity, continuity probed independently |

**Conclusion:** Cohort diversity is **adequate to support directional locality conclusions** but **insufficient alone** to claim broad corrective-availability or recurrence-trend significance.

---

## 4. Trend Comparison vs CA Baseline

### Primary comparison (CP N=4 vs CA frozen baseline N=10)

| Metric | CA Baseline v1 | CP Cohort #3 | Delta |
|---|---:|---:|---|
| Median production files / fix | 2.5 | 1.0 | −1.5 (−60%) |
| Mean production files / fix | 3.6 | 0.75 | −2.85 |
| Median test files / fix | 2.0 | 0.75 | −1.25 |
| Median total files / fix (effective) | 7.0 | 2.0 | −5.0 (−71%) |
| Median total files / fix (raw) | 12.5 | 2.0 | −10.5 |
| Max production files / fix | 9 | 1 | −8 |
| Generated-artifact pollution | 30% of fixes | 0% | eliminated |
| Largest repair family share | opening_fallback 60% | max 25% (1/4 per family) | de-concentrated |

### Domain-specific trends

| Domain | Trend | Evidence |
|---|---|---|
| **Production locality** | **Improving** | All qualifying production fixes ≤1 file; median 1.0 vs CA 2.5 |
| **Replay locality** | **Improving** | CP5 read-side helper only; no golden rewrites; manifest `--check` exit 0 on all slices |
| **Governance locality** | **Improving** | Zero governance code edits; no split-owner matrix, registry, or manifest refresh |
| **Recurrence outcomes** | **Mixed / stable** | No new protected failures recorded; no recurrence retirements; historical keys remain in advisory history |
| **Validation stability** | **High** | 3 validation-only slices all green; combined thousands of focused tests pass across slices |
| **Corrective availability** | **Constrained** | CA11 pre-CP: 0 post-baseline qualifying fixes from 26 candidates; CP found 4 fixes but required deliberate probing |

### Qualitative comparison to CA program context

- **CA6 / CA11:** Post-baseline automatic candidate intake found **0 qualifying fixes** before CP — suggesting standalone defects are rare or absorbed by structural programs (CA9/CA10).
- **CP cohort methodology:** Explicit failure→fix→validation slices with stop-on-no-defect produced **4 bounded fixes** in one cycle — demonstrating defects still exist but require targeted discovery.
- **CA10 preventive absorption:** Validation-only rate (43%) aligns with absorption hypothesis — many surfaces (sanitizer, BX parity, dialogue lock) no longer yield standalone fixes.
- **Historical vs current:** CA baseline medians were inflated by opening_fallback concentration and generated-artifact pollution; CP cohort avoided both failure modes.

---

## 5. Confidence Assessment

### Statistical confidence

| Factor | Level | Rationale |
|---|---|---|
| Locality metric confidence | **Moderate–high** | Large median deltas vs CA; all fixes tightly bounded |
| Trend significance (formal) | **Low** | N=4 < CA12 threshold (5); no hypothesis test performed |
| Persistence confidence | **Low** | Single cohort cycle; no before/after replication |
| Diversity confidence | **Moderate** | 4 subsystems; 2 share one production module |
| Availability confidence | **Moderate** | 57% fix rate within CP vs 0% CA11 automatic intake |

### Remaining sources of bias

1. **Selection bias** — CP candidates were pre-ranked; opportunistic CP7 found defects tests already encoded but not previously run in slice order.
2. **Same-file concentration** — CP2 and CP3 both touched `interaction_context.py`; inflates "one file per fix" while masking module-level coupling.
3. **Read-side fix classification** — CP5 qualifies as corrective but touches zero production files; production-locality averages are partly driven by test/helper work.
4. **Validation-only survivorship** — Stable surfaces probed once; does not prove they stay stable under future changes.
5. **Small N** — One outlier fix (CP5 at 3 files) moves medians meaningfully at this scale.

### Cohort strengths

- Every qualifying fix has **reproducible failure evidence** and **focused validation**.
- **Zero governance churn** and **zero golden rewrites** — low downstream cost.
- **Stop-on-no-defect discipline** prevented architectural expansion (CP4, CP6 correctly stopped).
- **Subsystem diversity** exceeds CA baseline family concentration.
- Median production locality **1.0 file** meets cohort budget (≤5) with wide margin.

### Cohort weaknesses

- **43% validation-only** — diminishing easy corrective targets on pre-selected surfaces.
- **N=4** — below CA12 comparison-ready threshold.
- **No recurrence retirements** — fixes add prevention tests but did not close documented protected failure→fix keys.
- **CP8 / opening-authorship / long-session** not stress-tested as fixes.
- **Single time window** — all slices 2026-06-28; no temporal spread.

### Will additional corrective cohorts materially change the conclusion?

**Unlikely in the near term without new failure signals.**

- Three of seven probed surfaces were stable (validation-only).
- CA11 showed 0 emergent fixes from 26 post-baseline candidates before CP.
- CP7 required opportunistic discovery (failing tests not caught by earlier slices).
- Another cohort of similar scope would likely yield **more validation-only slices** unless new recurrence failures, CI regressions, or unprobed high-risk candidates (CP8 long-session) are prioritized.

---

## 6. Conclusions

### Is Corrective Locality Trend statistically meaningful?

**Directionally yes; formally inconclusive.**

Observed medians (production 1.0, total 2.0) are substantially below CA baseline (2.5, 7.0 effective) with zero artifact pollution. At N=4, this supports a **moderate confidence** locality improvement claim, not a statistically locked trend. CA12 formal post-baseline comparison remains **not ready** (needs ≥5 qualifying fixes; CP contributes 4).

### Does corrective locality appear persistent?

**Not yet proven; plausibly improved for the slice methodology.**

Evidence for improvement:
- Bounded fixes held across all 4 qualifying entries.
- Validation-only slices confirm fixes did not destabilize adjacent surfaces.
- No governance/manifest escalation required.

Evidence against proven persistence:
- Single cohort cycle.
- CA10/CA11 suggest long-run corrective absorption.
- No multi-month replication.

### Recommended next initiative after CP

1. **Lock CP cohort #3 as post-baseline cohort v1 candidate** — append 4 qualifying fixes to CA12 intake when one additional qualifying fix emerges, OR formally accept N=4 descriptive comparison with documented confidence limits.
2. **Shift primary investment to preventive/structural programs** (CA9/CA10 absorption paths) rather than immediate CP cohort #4 — unless new protected replay failures or CI regressions appear.
3. **Maintain watch surfaces** — recurrence advisory keys (`speaker_drift`, `response_type_candidate_ok`, `fallback_drift`) without launching another full cohort until a failing protected node is recorded.
4. **Defer CP8 long-session** unless a reproducible 25-turn degradation appears — high blast radius, zero reproduction in CP7 candidate ranking.

### Additional corrective cohorts: recommended or diminishing returns?

**Diminishing returns for discovery-style cohort #4 at current signal levels**, unless:

- A new protected replay failure is recorded (`replay_failure_report.md` failure row).
- CA11 emergence rate rises above 0 from organic commits.
- CP8 long-session or opening-authorship surfaces show reproducible failure.

The CP3 cohort methodology itself remains valuable; the **availability of standalone corrective work** appears to be the limiting factor, not the measurement framework.

---

## Appendix: Slice Validation Stability Summary

| Slice | Key validation command outcome | Failed tests |
|---|---|---|
| CP1 | 19 + 55 + 47 + manifest check | 0 |
| CP2 | 48 routing/lock/golden | 0 |
| CP3 | 54 + 2 new regressions | 0 |
| CP4 | 49 + 6 marker + manifest | 0 |
| CP5 | ~112 projection/classifier | 0 |
| CP6 | 169 continuity + 1 protected | 0 |
| CP7 | 7 Block 14 regressions + 6 golden structural | 0 (3 failed pre-fix) |

All post-fix/post-probe validation across the completed cohort: **stable**.
