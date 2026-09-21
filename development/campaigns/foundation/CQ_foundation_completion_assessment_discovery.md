# CQ - Foundation Completion Assessment Discovery

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

## 1. Executive Summary

Recommendation: **Mixed Foundation + Features**

Confidence: **Medium-High**

The foundation program appears past the point where broad foundation-only work is the best default. Recent cycles explicitly closed or cooled the major pressure families: CK lowered opening fallback pressure from high to low, CL closed replay projection churn, CM reduced ownership registry magnet pressure, CN thinned final-emission gate adjacency, CO identified assertion rationalization targets, and CP showed materially improved corrective locality. However, the repo is not ready for unconstrained feature-first work: visibility fallback, FEM metadata, sanitizer, validators, recurrence/reporting tests, and a small replay registry/fields import-cycle risk remain real foundation pressures.

## 2. Recent Maintenance Context

Most relevant recent cycles from `git log --oneline -n 30`:

- `b01e737 CP: Corrective Locality Cohort #3`
- `79d1b85 CO: Assertion Family Rationalization`
- `ec9c7c8 CN: Final-Emission Adjacency Compression`
- `f05e756 CM: Ownership Registry Magnet Reduction`
- `f2935c9 CL: Replay Projection Churn Reduction`
- `4460543 CK: Fallback Authorship Contraction`
- `9b62d17 CJ: Foundation Readiness Closeout`
- `247e634 CC: Feature Readiness Closeout Discovery`
- `5f0ad53 CA: Corrective Change Locality Cohort`

High-signal files inspected:

- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CK_fallback_authorship_contraction_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CL8_replay_projection_churn_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CM8_ownership_registry_magnet_reduction_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CN_final_emission_adjacency_compression_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CO_assertion_family_rationalization_discovery.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CP_corrective_locality_cohort_3_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\docs\audits\CJ_foundation_readiness_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\docs\audits\CB_CLOSE_feature_boundary_readiness.md`

## 3. Fallback Pressure

Top remaining fallback/default/legacy hotspots are concentrated in `docs`, `tests`, and `game`. Keyword-count snapshot excluding `artifacts/**` and `__pycache__/**`:

| Directory | Fallback-family references |
|---|---:|
| `docs` | 19,880 |
| `tests` | 19,216 |
| `game` | 9,709 |
| `audits` | 3,644 |
| `tools` | 3,462 |

Observed live production hotspots:

- `game\final_emission_visibility_fallback.py`: intentional but still broad; CN labels it a remaining hotspot mixing candidate selection, route dispatch, enforcement chains, first-mention, and referential clarity.
- `game\final_emission_meta.py`: intentional FEM write-side hub; still carries lineage, registry, owner stamp, and compatibility surfaces.
- `game\output_sanitizer.py`: intentional but broad text hygiene/rewrite/fallback surface.
- `game\final_emission_validators.py`: large validator-family concentration unchanged by CN.
- `game\final_emission_sealed_fallback.py`, `game\final_emission_visibility_fallback.py`: CK flags sealed/visibility tuple adapters and breadth as outside CK scope.

Classification: fallback behavior is much more localized than earlier cycles, especially opening fallback authorship. Remaining pressure is mostly intentional/transitional, not suspicious, but visibility/sealed/sanitizer/FEM surfaces are still feature-regression risks.

## 4. Replay Pressure

Major replay/projection files:

- `tests\helpers\golden_replay_projection.py`
- `tests\helpers\golden_replay_projection_fields.py`
- `tests\helpers\golden_replay_projection_registry.py`
- `tests\helpers\golden_replay_projection_engine.py`
- `tests\helpers\golden_replay_projection_presence.py`
- `tests\helpers\golden_replay_projection_semantic.py`
- `tests\helpers\golden_replay_projection_fallbacks.py`
- `tests\helpers\golden_replay_projection_speaker.py`
- `game\final_emission_replay_projection.py`
- `tools\replay_maintenance_metrics.py`
- `tools\projection_drift_watch.py`

Keyword-count snapshot:

| Directory | Replay/projection references |
|---|---:|
| `docs` | 16,820 |
| `tests` | 7,529 |
| `audits` | 2,482 |
| `tools` | 1,955 |
| `game` | 1,318 |

CL8 says replay projection churn is no longer high enough to continue the CL cycle. Expectations are now mostly centralized by focused helpers. Remaining fragility is in compatibility imports and recurrence/reporting assertions, especially `tests\test_replay_bug_class_recurrence.py`, `tests\helpers\replay_bug_recurrence_statistics.py`, and dashboard/report tests. CN also reported a small `golden_replay_projection_registry` <-> `golden_replay_projection_fields` import-cycle risk; targeted validation passed in this discovery pass, but the coupling is still worth a hygiene follow-up.

## 5. Governance Pressure

Largest/highest-traffic governance or governance-adjacent files by line count:

| Lines | File |
|---:|---|
| 9,796 | `tests\helpers\replay_bug_recurrence_monolith.py.bak` |
| 4,298 | `tests\helpers\replay_bug_recurrence_statistics.py` |
| 3,561 | `docs\cycles\cycle_as_gate_consumer_inventory.json` |
| 2,848 | `tests\helpers\replay_bug_recurrence_history.py` |
| 2,511 | `tests\test_replay_bug_class_recurrence.py` |
| 2,038 | `tests\helpers\replay_bug_recurrence_serialization.py` |
| 1,863 | `tests\helpers\golden_replay.py` |
| 1,063 | `tests\ownership_closeout_delegate_locks.py` |
| 997 | `tests\helpers\failure_classification_dashboard_expectations.py` |
| 976 | `docs\ownership_cleanup_delta.md` |

CM8 is strong evidence that `tests\test_ownership_registry.py` is no longer a governance magnet: it shrank from 2,357 lines and 217 entrypoints to 257 lines and 9 entrypoints, with domain policy moved into focused files. Recent related cycles touched many governance/docs files, but CP reports zero governance code churn and zero golden/manifest edits for the latest corrective cohort, which is a strong locality signal.

Governance still needs frequent edits for governance-program work, but current evidence does not show ordinary local production fixes requiring registry or manifest churn.

## 6. Corrective Locality

Healthy locality examples:

- CP2 and CP3 fixed routing/vocative defects in `game\interaction_context.py` with one production file each.
- CP5 fixed replay projection/fallback taxonomy read-side behavior in test/helper surfaces with zero production files and no golden rewrites.
- CP7 fixed terminal retry/minimal repair behavior with one production file and no governance churn.
- CM moved governance policy checks out of `tests\test_ownership_registry.py` into focused owner modules.

Remaining locality risks:

- `game\final_emission_validators.py`: CN identifies it as the largest untouched adjacency hotspot.
- `game\final_emission_meta.py`: still a large write-side FEM and compatibility hub.
- `game\final_emission_visibility_fallback.py`: selection and enforcement remain coupled.
- `game\output_sanitizer.py`: broad text transform and fallback responsibilities.
- `tests\test_replay_bug_class_recurrence.py` and recurrence helpers: large assertion/reporting concentration.

Overall corrective work appears bounded now. CP reports median production files per qualifying fix of 1.0 versus CA baseline 2.5, median total code files 2.0 versus 7.0, zero governance code edits, and zero generated-artifact pollution. The caveat is sample size: CP had only four qualifying fixes and a 43% validation-only rate.

## 7. Feature Readiness

Ready for cautious feature work:

- Local, narrow gameplay/content features that exercise stable ownership lanes without changing protected replay fields.
- Features around social routing, interaction context, leads, scene validation, or non-FEM gameplay logic, provided they add focused regression tests.
- Feature-readiness pilots using existing guardrails from `docs\audits\CB_CLOSE_feature_boundary_readiness.md` and `docs\audits\CJ_foundation_readiness_closeout.md`.

Not ready for feature-first unrestricted work:

- New features that require FEM schema changes, protected replay field changes, golden replay manifest rewrites, or broad validator policy changes.
- Visibility fallback/first-mention/referential replacement changes without a dedicated cycle.
- Sanitizer rewrite-mode changes without careful snapshot/projection validation.
- Recurrence/reporting governance expansions that add more assertion duplication.

Safest first feature categories:

- Small user-visible gameplay improvements with local state ownership.
- Feature-readiness pilot slices with explicit no-governance-churn budgets.
- Non-schema UI/API affordance improvements backed by existing test lanes.

Avoid until more foundation work:

- Broad final-emission validator family changes.
- Protected replay schema expansion.
- Visibility fallback selection/enforcement redesign.
- Large diagnostic/reporting framework additions.

## 8. Quantitative Snapshot

Git/worktree:

- `git status --short`: clean before report creation.
- Recent related cycles inspected from last 8 commits.
- Files touched in `HEAD~8..HEAD`: 242 unique paths.
- Production files touched: 21.
- Test files touched: 91.
- Governance/doc files touched: 104.
- Other files touched: 26.

Targeted test status:

- Command run with bundled Python: `python.exe -m pytest tests\test_ownership_registry.py tests\test_golden_replay_projection_modules.py -q --tb=short --basetemp=codex_pytest_tmp_cq`
- Result: passed.
- Full suite was not run because this was a discovery pass and the repository has a large test surface.

Recent validation evidence from closeouts:

- CK closeout: 185 focused fallback/projection/classifier tests passed.
- CL8 closeout: 32 replay projection tests, 167 module/routing/FEM/trace tests, and 155 classifier/dashboard bridge tests passed.
- CM8 closeout: ownership/governance slices passed, including `python tools/test_audit.py --check`.
- CP closeout: all post-fix/post-probe validation stable across seven slices.

## 9. Risk Register

| Risk | Area | Evidence | Severity | Suggested Next Action |
|---|---|---|---|---|
| Visibility fallback remains broad | fallback pressure | CN lists `game\final_emission_visibility_fallback.py` as ~1655 LOC with selection, route dispatch, enforcement chains, and clarity concerns | Medium | Dedicated visibility selection-vs-enforcement discovery before changing behavior |
| FEM metadata hub remains large | governance/fallback/replay | CN lists `game\final_emission_meta.py` as ~1496 LOC with write-side FEM, registries, owner stamps, and compatibility surfaces | Medium | Monitor; only split in a metadata-specific foundation cycle |
| Validator concentration | corrective locality | CN identifies `game\final_emission_validators.py` as ~2231 LOC / 89 funcs and unchanged by CN | Medium-High | Validator-family discovery if feature work touches validation policy |
| Replay registry/fields coupling | replay pressure | CN reports `golden_replay_projection_registry` <-> `golden_replay_projection_fields` import-cycle friction; code search confirms cross-importing parity/defaults | Low-Medium | Small hygiene block if import-graph guard fails or projection churn resumes |
| Recurrence/reporting assertion burden | replay/governance pressure | CO ranks `tests\test_replay_bug_class_recurrence.py`, `tests\test_failure_dashboard_report.py`, and helpers as top duplication hotspots | Medium | Assertion rationalization pilot, starting with diagnostic report string helpers |
| Feature changes may trigger schema churn | feature readiness | Protected replay/FEM fields are heavily guarded; CK/CL/CN all avoid field renames and manifest rewrites | Medium | Start with no-schema feature pilot and explicit rollback criteria |

## 10. Recommendation

Recommendation: **Mixed Foundation + Features**

Rationale:

- Major foundation tracks are closing successfully rather than producing endless broad refactors.
- Corrective locality has improved materially: latest qualifying fixes are small, local, and avoid governance/golden churn.
- Replay projection and ownership registry expectations are now more centralized and focused.
- Remaining risks are real but bounded and named; they do not justify another blanket foundation-only phase.
- Feature-first development would be premature because FEM, visibility fallback, sanitizer, validators, and recurrence/reporting still have meaningful pressure.
- A cautious feature pilot will produce better signal than another broad discovery-only maintenance cohort unless new failures emerge.

Suggested next cycle type: **feature-readiness pilot**, with small companion foundation hygiene only where the pilot hits known risks.

Recommended cycle shape:

- Primary: first feature-readiness pilot or first small feature tranche.
- Guardrails: no protected replay schema changes, no golden manifest rewrites, no ownership registry expansion unless directly justified.
- Companion optional: small replay import-cycle hygiene or diagnostic assertion rationalization if it unblocks the feature pilot.

## 11. Files to Pass Back

Pass back:

- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CQ_foundation_completion_assessment_discovery.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CK_fallback_authorship_contraction_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CL8_replay_projection_churn_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CM8_ownership_registry_magnet_reduction_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CN_final_emission_adjacency_compression_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CO_assertion_family_rationalization_discovery.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\CP_corrective_locality_cohort_3_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\docs\audits\CJ_foundation_readiness_closeout.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\docs\audits\CB_CLOSE_feature_boundary_readiness.md`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\game\final_emission_visibility_fallback.py`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\game\final_emission_meta.py`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\game\final_emission_validators.py`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\tests\helpers\golden_replay_projection_registry.py`
- `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\tests\helpers\golden_replay_projection_fields.py`
- Targeted test output: `tests\test_ownership_registry.py tests\test_golden_replay_projection_modules.py` passed in this discovery pass.

