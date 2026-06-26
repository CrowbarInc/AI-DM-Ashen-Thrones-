# CJ2 — First Post-CA Corrective Locality Validation

**Date:** 2026-06-26  
**Scope:** Measurement and documentation only.  
**Baseline authority:** `docs/baselines/ca_corrective_locality_baseline.json` (CA4, frozen 2026-06-22)  
**Prior screening:** [CI_corrective_cohort_validation_2_closeout.md](CI_corrective_cohort_validation_2_closeout.md) — null cohort through `85855df` (zero committed qualifying fixes)

---

## Corrective Fix Selected

| Field | Value |
|---|---|
| **Fix ID** | CJ2-01 |
| **Boundary** | CJ1 — Ownership registry failure locality closeout |
| **Commit** | *Uncommitted workspace diff* (post-`1f3899b` / CI closeout); not yet landed as a discrete Git commit |
| **Date** | 2026-06-26 |
| **Summary** | Restore `tests/test_ownership_registry.py` to green after CE/CF/CG/CH architecture churn by fixing root causes in owning modules rather than centralizing logic in the registry hub |
| **Problem type** | Ownership/governance enforcement regression + replay acceptance facade contract gap + production producer-stamp pairing |
| **Recurrence related** | No — post-architecture drift, not a replayed historical defect |
| **Qualifies** | **Yes** |

### Why this fix qualifies

CI screened all commits in `5f0ad53..85855df` and found **zero** qualifying corrective fixes (audit-only, governance redistribution, discovery, and documentation-only work). The first genuine corrective fix after the CA baseline is the **CJ1 ownership-registry failure locality work** captured in the current workspace diff and documented in [CJ1_ownership_registry_failure_locality_closeout.md](CJ1_ownership_registry_failure_locality_closeout.md).

Qualification evidence:

1. **Concrete failing behavior** — `tests/test_ownership_registry.py` had 10 failures and 12 setup errors (216 tests total) before the fix; all 216 pass after.
2. **Production repair** — `game/final_emission_referential_clarity.py` pairs visibility producer stamp with referential-clarity upstream repair (`BU9` contract).
3. **Replay/projection contract repair** — `tests/helpers/golden_replay_projection.py` re-exports `SEALED_REPLACEMENT_SUBKINDS` and related runtime replay-projection symbols removed from the acceptance facade during CE/CF splits, unblocking pytest collection for inventory governance.
4. **Discrete fix boundary** — separable from CH governance redistribution and CE/CF/CG audit programs; does not reopen monolith extraction or broad decomposition.

### Excluded post-CA commits (for context)

| Commit | Subject | Exclusion |
|---|---|---|
| `85855df` | CH: Governance Hub Redistribution | Governance redistribution |
| `5ea6608` | CG: Failure Classification Synchronization Audit | Audit program |
| `c98dfa6` | CF: Replay Projection Responsibility Audit | Audit program |
| `66b8b32` | CE: Golden Replay Concentration Audit | Audit + generated artifact churn |
| `ba8b29a` | Restore evaluator convergence closeout path contract | Documentation only |
| `247e634` | CC: Feature Readiness Closeout Discovery | Discovery/docs reorganization |
| `ce36d0c` | CB: Feature Boundary Readiness Audit | Readiness audit |
| `3709523` / `1bc28f7` / `1f3899b` | CI/CK hotspot measurement | Tooling/measurement |

### Modules touched

| Module | Role in fix |
|---|---|
| `game.final_emission_referential_clarity` | Production owner — visibility stamp pairing on upstream observe repair |
| `tests.helpers.golden_replay_projection` | Replay acceptance facade — restore BD-4 contract re-exports |
| `tests.test_ownership_registry` | Governance orchestration hub — docstring corpus + missing import |
| `tests.ownership_guard_bd_dependency_compression` | BD-6 compressed-gate import allowlist for CE/CF/CG owner paths |
| `tests.ownership_guard_bv_compatibility` | BV2C write-owner and BV14C compat importer allowlists |
| `tests.ownership_closeout_delegate_locks` | BJ-127 global scan exclusion for delegator regression fixtures |
| `tests.ownership_registry_contract` | Cross-file duplicate allowlist for CE dashboard split |
| `tests.test_final_emission_gate` | Gate redirect stub inventory layer signal |
| `docs.audits.BU4_ownership_write_paths` | Write-path inventory parity after CH owner-bucket view extraction |

### Tests affected

| Test surface | Before | After |
|---|---|---|
| `tests/test_ownership_registry.py` | 10 failed, 12 errors, 194 passed | **216 passed** |
| Root collection blockers | `full_inventory` fixture raised on missing `SEALED_REPLACEMENT_SUBKINDS` | Collection succeeds via facade re-export |
| Guard suites | BD-6, BV2C, BV12C, BV13C, BV14C, BJ-127, BU8, BU9 violations | Resolved via guard-policy and owner-local fixes |

### Ownership domains involved

BV2C (meta import lockdown), BV12C/BV13C/BV14C (compat barrel FI caps), BD-6 (gate dependency compression), BJ-115/116/127 (delegate closeout locks), BU4/BU8 (production write-path parity), BU9 (visibility producer stamp pairing), CE/CF/CG replay and classification owner registration, gate inventory layer (BM decomposition stub).

---

## Files Changed

| file | subsystem | category |
|---|---|---|
| `game/final_emission_referential_clarity.py` | final-emission referential clarity (runtime) | Runtime |
| `tests/helpers/golden_replay_projection.py` | golden replay acceptance facade | Replay |
| `tests/test_final_emission_gate.py` | gate redirect stub / inventory signal | Test |
| `tests/test_ownership_registry.py` | central ownership registry orchestration | Governance |
| `tests/ownership_guard_bd_dependency_compression.py` | BD-6 gate import compression guard | Governance |
| `tests/ownership_guard_bv_compatibility.py` | BV2C / BV14C compatibility guards | Governance |
| `tests/ownership_closeout_delegate_locks.py` | BJ closeout delegate lock scans | Governance |
| `tests/ownership_registry_contract.py` | registry contract / duplicate allowlists | Governance |
| `docs/audits/BU4_ownership_write_paths.csv` | BU4 production write-path inventory | Inventory |

**Diff size:** 9 files, +80 / −7 lines.

---

## Locality Measurements

### Totals

| Category | Count |
|---|---:|
| **Total files changed** | 9 |
| Runtime | 1 |
| Replay | 1 |
| Projection | 0 |
| Classification | 0 |
| Governance | 5 |
| Inventory | 1 |
| Test | 1 |
| Generated artifact | 0 |
| Documentation | 0 |
| Tooling | 0 |

**CA2 path buckets (for baseline comparison):**

| Bucket | Count |
|---|---:|
| Production (`game/`) | 1 |
| Tests (`tests/`) | 7 |
| Docs (`docs/`) | 1 |
| Generated artifacts | 0 |

### Distribution

| Tier | Assessment |
|---|---|
| **Classification** | **Mostly Local** |

Rationale:

- Single repair family: post-CH ownership-registry enforcement drift.
- Production fanout = **1 file** (below CA production median 2.5).
- Total fanout = **9 files** (above CA effective median 7.0, below CA p75 44.0).
- Governance touches dominate (5/9 files) but each change is policy-local to the extracted guard/contract owner introduced by CH — not logic re-centralized into `test_ownership_registry.py`.
- Zero generated-artifact pollution (CA polluted-fix rate in baseline: 30%).

Tier reference used for this report:

| Tier | Heuristic |
|---|---|
| Highly Local | ≤5 files, ≤1 production, single dominant category |
| Mostly Local | ≤12 files, ≤2 production, one repair family, no generated pollution |
| Mixed | Multiple repair families or >2 production modules |
| Broad | >15 files or wide unrelated subsystem fanout |
| Highly Distributed | p90+ territory (>44 files) or generated-artifact dominated |

### Fanout

| Metric | CJ2-01 | CA4 baseline median |
|---|---:|---:|
| Total files touched | 9 | 7.0 (effective) |
| Production files | 1 | 2.5 |
| Test-path files | 7 | 2.0 |
| Governance-category files | 5 | — |
| Replay-category files | 1 | — |
| Generated artifacts | 0 | — |

**Subsystem spread:** 4 logical areas (runtime, replay facade, governance guards/contracts, inventory CSV) serving one failure surface.

---

## Comparison Against CA Baseline

| Dimension | vs CA4 median | Direction |
|---|---|---|
| Total fanout | 9 vs 7.0 | +2 files (+29%) |
| Production fanout | 1 vs 2.5 | **−1.5 files (improved)** |
| Test fanout | 7 vs 2.0 | +5 files (worse raw count) |
| Generated distortion | 0 vs 44% median pollution | **Improved** |
| Governance involvement | 5 files | Elevated but expected for ownership-routing corrective |
| Replay involvement | 1 file (facade re-export) | Low — root-cause localized |
| Projection involvement | 0 files modified | None — CF owners only referenced in allowlists |
| Classification involvement | 0 files modified | None |
| Ownership involvement | Central — by design | Expected hotspot participation |

### Verdict

**Improved (production locality); Neutral (overall fanout).**

- **Improved:** Production repair stayed in the owning module (`final_emission_referential_clarity`) with a 2-line stamp pairing. No `game/final_emission_meta.py`, `game/final_emission_replay_projection.py`, or classifier modules were edited. Zero generated-artifact churn contrasts sharply with CA-07/CA-08/CA-09 pollution patterns.
- **Neutral:** Total file count slightly exceeds the effective median (9 vs 7), driven by guard-policy updates that register CE/CF/CG/BX owner paths in BD-6 and BV allowlists. These are additive policy rows, not behavioral rewrites across 26 modules.
- **Not regressed:** Fanout is far below CA p75 (44) and p90 (248.2). The fix did not reopen broad golden-replay monolith edits or multi-hundred-file artifact regeneration seen in historical corrective outliers.

---

## Unexpected Hotspots

| Hotspot | Participated? | Expected? | Notes |
|---|---|---|---|
| `tests/test_ownership_registry.py` | Yes | **Yes** | Failure hub under test; received orchestration-only edits (import + docstring), not new enforcement logic |
| `tests/helpers/golden_replay_projection.py` | Yes | **Yes** | Root cause of inventory collection failure — missing facade re-export after CE split |
| Replay helpers (other) | No (referenced only) | — | BD-6 allowlist names 26 CE/CF/CG paths; none modified |
| Projection helpers | No (referenced only) | — | CF3 owner registered in BV2C allowlist; `fem_normalization_contract.py` not edited |
| Classifier helpers | No (referenced only) | — | CG classification owners registered in BD-6 allowlist only |
| Governance inventory (`BU4_ownership_write_paths.csv`) | Yes | **Yes** | Required for `test_bu8_bu4_production_ownership_write_paths_parity_locked` after CH owner-bucket view extraction |
| Hotspot watch infrastructure (`tools/corrective_fix_watch.py`, CK reports) | No | — | Not touched |

**No unexpected hotspot participation.** Every touched file maps directly to a named failing test or collection blocker in the CJ1 inventory. The elevated governance file count reflects CH's intentional extraction of guard modules as the correct repair surface — not accidental re-centralization.

### Necessity and future architecture

| Touch | Why necessary | Can architecture reduce later? |
|---|---|---|
| `golden_replay_projection.py` re-export | CE facade split removed symbols that inventory collection imports transitively | Yes — automated facade export contract test (CE5/BD-4) could catch at extraction time |
| BD-6 / BV allowlist rows | New CE/CF/CG owner paths legitimately import compressed gate dependencies | Yes — codegen allowlist from ownership registry metadata instead of manual rows |
| `BU4_ownership_write_paths.csv` | CH moved `opening_fallback_owner_bucket_from_meta` to owner-bucket views | Yes — derive CSV from static analysis of write owners |
| Referential-clarity stamp pairing | BU9 contract requires visibility bucket pairing on producer repair kind | No — belongs in production owner; already minimal |

---

## Architectural Assessment

**Did recent CE/CF/CG/CH/CI work make this corrective fix more localized?**

**Yes — with evidence.**

1. **CH governance hub redistribution** extracted enforcement into `ownership_guard_*`, `ownership_registry_contract`, and `ownership_closeout_delegate_locks`. The corrective fix updated those focused owners instead of growing `test_ownership_registry.py` with new guard logic. Registry test line changes were limited to a missing `dataclasses.replace` import and BV12C/BV13C/BV14C hub documentation in the policy docstring.

2. **CE golden replay concentration** split the monolithic projection surface into facades and family owners. The failure localized to a **missing re-export** in `golden_replay_projection.py` (19 lines) rather than edits across `test_golden_replay_projection.py`, generated event logs, or CE's 77-file audit footprint.

3. **CF replay projection responsibility** kept projection contract tests in named CF owners. CJ2 registered those owners in BD-6 allowlists but did **not** modify `game/final_emission_replay_projection.py` or CF test modules — contrast with pre-CF era where projection contract drift often required runtime + broad integration edits.

4. **CG failure classification synchronization** similarly contributed only allowlist registrations; zero classifier or dashboard files were edited for this fix.

5. **Production repair locality** — the only runtime change pairs stamps inside `final_emission_referential_clarity.py`, the module that owns referential-clarity upstream repair. No cross-module FEM meta surgery.

**Counter-evidence (bounded):** Guard allowlist updates name many CE/CF/CG modules, inflating perceived fanout in the BD-6 diff (+28 lines). Those are policy declarations, not multi-module code changes. Pre-CH architecture would likely have concentrated similar policy edits inside the 3,000+ line registry test file.

---

## Recommendation

| Rating | **Good** |
|---|---|

**Rationale:**

- Production corrective locality is **excellent** (1 file, 2 lines, correct owner).
- Overall fanout is **acceptable** — slightly above CA effective median but well within normal variance and far below broad-corrective outliers.
- Governance participation is **proportionate** to an ownership-enforcement corrective and aligns with CH extraction intent.
- Zero generated-artifact distortion is a clear improvement over 30% of the CA cohort.
- **Caveat:** Fix is not yet committed; locality should be re-verified at commit time to ensure no scope creep.

**To reach Excellent:** Land as a discrete commit without additional files; add a facade export contract guard so the `SEALED_REPLACEMENT_SUBKINDS` class of collection failures cannot recur silently after future CE-style splits.

---

## Test Results

### Commands

```text
python -m pytest tests/test_ownership_registry.py -q --tb=line
python -m pytest tests/test_final_emission_gate.py -q --tb=line
```

### Results

| Command | Outcome |
|---|---|
| `tests/test_ownership_registry.py` | **216 passed** (~71s) |
| `tests/test_final_emission_gate.py` | **1 passed** |

Pre-fix baseline (from CJ1 closeout): 10 failed, 12 errors, 194 passed on `tests/test_ownership_registry.py`.

---

## Completion Criteria

| Criterion | Status |
|---|---|
| One genuine corrective fix analyzed | ✅ CJ2-01 (CJ1 ownership registry failure locality) |
| Locality measured | ✅ 9 files; Mostly Local |
| Compared against CA baseline | ✅ Improved production; neutral total fanout |
| Hotspot participation evaluated | ✅ No unexpected hotspots |
| Report completed | ✅ This document |
