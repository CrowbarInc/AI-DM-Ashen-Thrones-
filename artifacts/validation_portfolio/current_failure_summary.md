# Current Failure Classification

Observed command: `python -m pytest -q --tb=short`

Observed result: **36 failures** from **6439 collected cases**.

## By likely cause

| Classification | Count |
|---|---:|
| CURRENT_ARCHITECTURE_REGRESSION | 9 |
| CURRENT_PRODUCT_REGRESSION | 7 |
| REGISTRY_GOVERNANCE_DRIFT | 9 |
| STALE_EXPECTATION | 9 |
| STALE_FIXTURE | 1 |
| UNCERTAIN | 1 |

## By confidence

| Confidence | Count |
|---|---:|
| HIGH | 13 |
| LOW | 2 |
| MEDIUM | 21 |

## By validation family

| Family | Count |
|---|---:|
| `ARCHITECTURE_GOVERNANCE` | 4 |
| `FINAL_EMISSION_CONTRACTS` | 6 |
| `GOLDEN_PROTECTED_REPLAY` | 2 |
| `OWNERSHIP_IMPORT_GOVERNANCE` | 6 |
| `PLAYABILITY_RUNTIME` | 1 |
| `PYTEST_COMPONENT_CONTRACT` | 4 |
| `REPLAY_PROJECTION_DIAGNOSTICS` | 13 |

## Interpretation

After approved high-confidence rationalization, the 13 legacy closeout-document failures are retired from active authority. The remaining baseline mixes current product defects, current architecture violations, stale snapshots/expectations, registry drift, and one unresolved case. The audit still identifies 7 likely current product regressions and 9 likely current architecture regressions, but only 9 of those 16 are high-confidence; the rest require owner confirmation or reproduction before repair. No product defect was fixed by this campaign.

This is an audit classification, not a waiver. No failing test was disabled, repaired, or silently downgraded.
