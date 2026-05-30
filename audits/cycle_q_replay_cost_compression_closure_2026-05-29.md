# Cycle Q Closure Report: Replay Cost Compression

Date: 2026-05-29

## Recommendation

Close Cycle Q.

The cycle met its goal: replay authority stayed in the protected golden replay lane while repeated expectation fragments, fixture readers, metadata projection, report ergonomics, and validation docs were compressed into clearer owners. No runtime code, replay fixture JSON, or protected assertion semantics were intentionally changed.

## Blocks Completed

| Block | Status | Summary |
|---|---|---|
| Q1 - Golden Expectation Fragment Helpers | Complete | Added protected expectation fragments for no-scaffold terms, route shape, unavailable fields, and source/fallback checks; reused them in protected golden replay assertions. |
| Q2 - Golden Fixture Reader Extraction | Complete | Centralized Frontier Gate long-session fixture loading plus branch prompt/turn-id extraction in `tests/helpers/golden_replay.py`. |
| Q3 - Replay Identity Metadata Projection | Complete | Added optional `source_path`, `branch_id`, and `turn_id` projection into observed rows, debug context, and protected failure report rows. |
| Q4 - Protected Failure Report Ergonomics | Complete | Added a compact failure locator table and copy-ready reproduction commands while preserving existing classifier/category/owner/severity output. |
| Q5 - Scenario-Spine Metadata Ownership Notes | Complete | Documented ownership of `scenario_id`, `spine_id`, `branch_id`, `turn_id`, `scenario_spine_id`, and text projections. |
| Q6 - Replay Validation Command Docs | Complete | Added concise replay validation commands for golden replay, diagnostics, scenario-spine-adjacent, and broader replay-adjacent safety lanes. |

## Files Changed Across Q1-Q6

| Path | Role |
|---|---|
| `tests/helpers/golden_replay.py` | Helper owner for protected expectation fragments, Frontier Gate fixture readers, and optional replay identity projection/debug context. |
| `tests/test_golden_replay.py` | Protected acceptance owner; now reuses helper fragments/readers and asserts identity/report metadata visibility without weakening replay checks. |
| `tests/helpers/failure_dashboard_report.py` | Protected replay report renderer; now includes fixture identity fields when available, a failure locator, and compact reproduction commands. |
| `docs/testing/protected_replay_manifest.md` | Protected replay governance manifest; now documents metadata ownership and Frontier Gate scenario-spine backing. |
| `tests/README_TESTS.md` | Test-running guide; now documents replay metadata ownership and exact replay validation commands. |

## Maintenance Drag Reduced

- Repeated protected expectation boilerplate was consolidated into named helper fragments instead of repeating dictionary literals across golden replay scenarios.
- Frontier Gate branch prompt and turn-id extraction now has one helper owner, reducing direct JSON path/read duplication in the protected test file.
- Protected failure report rows now carry replay identity metadata when available, so failures can be traced to scenario-spine source material without manual cross-referencing.
- Report reproduction commands are copy-ready and split between focused failing nodes and the protected marker lane.
- Metadata ownership notes reduce future confusion between golden replay, scenario-spine fixtures, and the N1 synthetic lane.
- Validation command docs give maintainers a small menu of replay-only and replay-adjacent checks instead of rediscovering commands per fix.

## Replay Authority Preserved

- Protected golden replay assertions remain in `tests/test_golden_replay.py`.
- Helper extraction did not remove protected invariants; it replaced repeated fragments with equivalent helper-returned values.
- Frontier Gate still reads the same committed scenario-spine fixture and still asserts the same 20 prompts, 20 turn IDs, turn count, drift bounds, continuity classification, fallback limits, and scaffold-leakage locks.
- Optional identity metadata is additive; rows without fixture identity still run and render.
- Report formatting changes do not affect assertion pass/fail logic.
- Q5 and Q6 are documentation-only.

## Validation Results

All requested block-level validation commands passed during Cycle Q. Commands were run with the Codex bundled Python runtime in this workspace, with `PYTHONPATH` pointed at `.\.venv\Lib\site-packages`; command semantics match the documented `python -m pytest ...` forms.

| Validation Lane | Representative Command | Result |
|---|---|---|
| Q1 golden replay file | `python -m pytest tests/test_golden_replay.py -q --tb=short` | Passed |
| Q1 marker lane | `python -m pytest -m golden_replay -q --tb=short` | Passed |
| Q2 Frontier Gate focused replay | `python -m pytest tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_20_turn_structural_stability -q --tb=short` | Passed |
| Q2 golden replay file | `python -m pytest tests/test_golden_replay.py -q --tb=short` | Passed |
| Q2 marker lane | `python -m pytest -m golden_replay -q --tb=short` | Passed |
| Q3 golden replay file | `python -m pytest tests/test_golden_replay.py -q --tb=short` | Passed |
| Q3 failure dashboard/classifier contracts | `python -m pytest tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q --tb=short` | Passed |
| Q3 marker lane | `python -m pytest -m golden_replay -q --tb=short` | Passed |
| Q4 protected report focused test | `python -m pytest tests/test_golden_replay.py::test_protected_golden_assertion_failure_records_canonical_report -q --tb=short` | Passed |
| Q4 failure dashboard/classifier contracts | `python -m pytest tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q --tb=short` | Passed |
| Q4 golden replay file | `python -m pytest tests/test_golden_replay.py -q --tb=short` | Passed |
| Q4 marker lane | `python -m pytest -m golden_replay -q --tb=short` | Passed |
| Q5 docs-adjacent golden replay file | `python -m pytest tests/test_golden_replay.py -q --tb=short` | Passed |
| Q5 docs-adjacent marker lane | `python -m pytest -m golden_replay -q --tb=short` | Passed |
| Q6 docs-adjacent golden replay file | `python -m pytest tests/test_golden_replay.py -q --tb=short` | Passed |
| Q6 docs-adjacent marker lane | `python -m pytest -m golden_replay -q --tb=short` | Passed |

## Remaining Risks And Follow-Up Candidates

- The scenario-spine runner and N1 lane remain advisory and intentionally separate. That is correct for Cycle Q, but future work should keep the distinction visible when adding replay-adjacent validation.
- The broader replay-adjacent safety slice is documented but was not run as part of Q5/Q6 optional docs validation. Run it before merging if transcript or scenario-spine behavior changes are bundled with Cycle Q.
- Protected failure reports now render identity fields as `none` when optional fixture identity is absent. This is readable and stable, but a future report-polish block could introduce a more compact empty-state convention if desired.
- The current report ergonomics are Markdown-focused. No dashboard UX or artifact storage policy was changed.
- Existing unrelated untracked report files remain outside Cycle Q scope and should be handled separately.

## Closure Decision

Cycle Q should be closed.

The high-value replay maintenance drag sources identified in recon were addressed with small, reviewable helper extraction, metadata projection, report formatting, and documentation blocks. Replay validation remains authoritative, and no broad rewrite or coverage deletion occurred. Future work should be opened as a new cycle rather than extending Cycle Q.
