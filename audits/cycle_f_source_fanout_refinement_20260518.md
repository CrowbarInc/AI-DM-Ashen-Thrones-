# Cycle F.A Source Fanout Refinement - 2026-05-18

## Purpose

Refine the Cycle F maintenance-drag metric by separating true source fanout from tracked runtime/session snapshot churn.

Cycle F recon found these tracked snapshot files in 15 of the last 30 commits:

- `data/combat.json`
- `data/session.json`
- `data/session_log.jsonl`

Those files are useful repo evidence, but they inflate broad-fanout counts when the actual source/test change is small.

## Counting Rules

### True source fanout

Counted paths:

- `game/**`
- `tests/**`
- `tools/**`
- `scripts/**`
- runtime/config code files such as `run.py`, `pytest.ini`, `Makefile`, and `.github/workflows/**`

Excluded paths:

- `data/session*`
- `data/combat*`
- `docs/**`
- `audits/**`
- `*.md`
- `artifacts/**`
- generated pytest temp trees

### Snapshot churn fanout

Counted separately:

- `data/session*`
- `data/combat*`

No git history or tracking changes were made.

## Last-30 Commit Results

| SHA | True source files | Snapshot churn files | Title |
| --- | ---: | ---: | --- |
| 8ddb183 | 13 | 0 | E: Test Signal Ownership Thinning |
| 6c00e6e | 15 | 0 | D: Final Emission Gate Pressure Reduction |
| a5c9146 | 14 | 0 | Cycle C: contract fallback ownership and mutation lineage |
| 98bc059 | 10 | 0 | Failure Classification Dashboard |
| ac1ba90 | 3 | 0 | Add Golden Replay Scenario-Spine Baseline Suite |
| f04ef66 | 2 | 0 | Converge evaluator boundaries, telemetry, and governance |
| 792de85 | 15 | 0 | Freeze Evaluator Convergence and Boundary Governance |
| c89f2f4 | 22 | 0 | Complete Gate Convergence, Semantic Fencing, and Relocation Readiness Hardening |
| 0f03dd6 | 14 | 0 | Gate Boundary Convergence and Compatibility Fencing |
| 177099a | 0 | 0 | Close Out Realization Failure-Locality |
| 0f80564 | 24 | 0 | Realization Layer Failure-Locality Hardening |
| 673118e | 34 | 3 | PLANNER: Stabilize Failure Locality Seam |
| 29da646 | 4 | 0 | Adoption Gateway (Finalized) |
| 6dcccd8 | 4 | 0 | Post-GM adoption gateway fenced |
| 9808d01 | 0 | 0 | Remove generated pytest artifacts from tracking |
| 5cb8444 | 4 | 0 | Recover mixed investigation question routing |
| 53165bb | 5 | 3 | UI & Freeform Investigation (I) |
| f3fa4b1 | 3 | 3 | Preserve player chat in replayed logs |
| 773cbe0 | 3 | 3 | Promote accepted scene opening candidates |
| f6a4c6f | 2 | 3 | Promote upstream prepared scene openings before final gate |
| f487f4d | 3 | 3 | Guard rich scene openings from post-gate shortening |
| 43bdb8b | 2 | 3 | Collapse start_campaign onto canonical gm_output |
| c6e63b0 | 4 | 3 | Refresh session snapshot and opening scene details |
| 1b3b3ee | 2 | 3 | Preserve valid scene openings before deterministic fallback |
| b0cfd07 | 2 | 3 | Refine opening scene narration contract |
| 20b1420 | 0 | 3 | Opening Clean-Up |
| 9e83820 | 4 | 3 | Preserve journal openings through selector fallback |
| ee3af57 | 0 | 3 | Add perceptual filtering for journal opening facts |
| 2b293b2 | 0 | 3 | Restore journal seed facts as opening source |
| 2013258 | 4 | 3 | Restrict journal seed facts to perceptual opening content |

## Updated Metrics

- Median true source fanout: 4 files.
- Commits touching 8+ true source files: 9 of 30.
- Commits where snapshot churn exceeded true source fanout: 7 of 30.

For comparison, Cycle F recon counted median non-artifact fanout as 6 files and 11 of 30 commits with 8+ non-artifact files. Separating snapshots lowers both values.

## Top Production/Test Hotspots

| Count | File |
| ---: | --- |
| 10 | `game/final_emission_gate.py` |
| 9 | `tests/test_start_campaign_api.py` |
| 8 | `game/api.py` |
| 8 | `tests/test_final_emission_gate.py` |
| 6 | `game/gm.py` |
| 5 | `game/final_emission_meta.py` |
| 5 | `game/final_emission_validators.py` |
| 5 | `tests/test_golden_replay.py` |
| 4 | `tests/helpers/golden_replay.py` |
| 4 | `tests/test_failure_classification_contract.py` |

Close next cluster, also at 4 touches:

- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`

## Top Snapshot Churn Files

| Count | File |
| ---: | --- |
| 15 | `data/combat.json` |
| 15 | `data/session.json` |
| 15 | `data/session_log.jsonl` |

## Commits Where Snapshot Churn Exceeded Source Churn

| SHA | True source | Snapshot churn | Title |
| --- | ---: | ---: | --- |
| f6a4c6f | 2 | 3 | Promote upstream prepared scene openings before final gate |
| 43bdb8b | 2 | 3 | Collapse start_campaign onto canonical gm_output |
| 1b3b3ee | 2 | 3 | Preserve valid scene openings before deterministic fallback |
| b0cfd07 | 2 | 3 | Refine opening scene narration contract |
| 20b1420 | 0 | 3 | Opening Clean-Up |
| ee3af57 | 0 | 3 | Add perceptual filtering for journal opening facts |
| 2b293b2 | 0 | 3 | Restore journal seed facts as opening source |

## Interpretation

### Are fixes actually getting smaller?

Yes, partially. The refined metric shows the median true source fanout is 4 files, not 6. Several older opening-scene commits were small source changes paired with three tracked snapshot files.

### Are snapshots obscuring the trend?

Yes. Snapshot churn obscures the trend most strongly in the older opening/fallback cluster, where `data/combat.json`, `data/session.json`, and `data/session_log.jsonl` often add three files to otherwise narrow commits. Snapshot churn does not explain the broadest source commits, though: `673118e`, `0f80564`, `c89f2f4`, `792de85`, `6c00e6e`, `a5c9146`, and `8ddb183` remain broad even after snapshot separation.

### Strongest remaining architectural gravity center

`game/final_emission_gate.py` remains the strongest architectural gravity center. It is the top true-source hotspot at 10 of 30 commits, and its companion test file `tests/test_final_emission_gate.py` is also in the top hotspot list at 8 of 30 commits. The next gravity cluster is API/start-campaign behavior (`tests/test_start_campaign_api.py`, `game/api.py`), followed by replay/classifier/dashboard projection surfaces.

## Maintenance Guidance

- Use true source fanout as the primary drag metric for future Cycle F comparisons.
- Track snapshot churn separately so small fixes are not misclassified as broad source edits.
- Continue treating `game/final_emission_gate.py` as the highest-risk hotspot: comments-only ownership clarification is safe, but runtime refactor or assertion thinning should remain out of scope until a dedicated human-reviewed block.
- Replay/classifier/dashboard projection duplication should be preserved unless a later thinning block proves the same diagnostic locality remains.
