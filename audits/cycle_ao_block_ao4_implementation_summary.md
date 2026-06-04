# Cycle AO4 — Unified Synthetic Observed-Row Fixture Builder (Closeout)

**Date:** 2026-06-03  
**Status:** Completed

---

## Objective

Remove duplicate synthetic observed-row ownership by consolidating `observed_failure_row()` and `failure_dashboard_fixtures._observed()` into one shared factory with profile-specific defaults.

---

## Files changed

| File | Change |
|---|---|
| `tests/helpers/replay_observed_row_fixtures.py` | **New** — single authority: `synthetic_observed_replay_row()`, `observed_failure_row()`, `observed_dashboard_probe_row()` |
| `tests/helpers/failure_classification_sync.py` | Removed inline `observed_failure_row()`; imports from shared factory; specialty row helpers unchanged |
| `tests/helpers/failure_dashboard_fixtures.py` | Removed inline `_observed()`; aliases `observed_dashboard_probe_row` as `_observed` |
| `tests/test_failure_classification_contract.py` | Added `test_ao4_synthetic_observed_row_factory_is_single_authority` |

**Not changed:** `failure_classifier.py`, `failure_dashboard_report.py`, projection, golden fixtures, runtime, `CONTROLLED_FAILURE_CASES` tuple content.

---

## Duplicate fixture surfaces removed

| Before | After |
|---|---|
| `failure_classification_sync.observed_failure_row()` — 38-line inline dict | Thin wrapper → `synthetic_observed_replay_row(profile="classifier_probe")` |
| `failure_dashboard_fixtures._observed()` — 38-line near-duplicate dict | Alias → `observed_dashboard_probe_row()` |
| Two independent baseline field lists | One `_base_synthetic_observed_replay_row()` |

**Profile differences preserved:**

| Field / behavior | `classifier_probe` | `dashboard_probe` |
|---|---|---|
| `scenario_id` | `"probe"` | `"controlled_probe"` |
| `final_text_hash` | `"hash123"` | `"probehash"` |
| `raw_signal_presence` | absent unless override | `{}` by default |
| `normalized_signal_presence` | absent unless override | `{}` by default |
| `fallback_behavior_repair_kind` | `None` | `None` (in shared base) |

---

## Authority model

```
replay_observed_row_fixtures.py
  ├── synthetic_observed_replay_row(profile=...)
  ├── observed_failure_row()          → classifier_probe
  └── observed_dashboard_probe_row()  → dashboard_probe

failure_classification_sync.py      → re-exports observed_failure_row + specialty wrappers
failure_dashboard_fixtures.py       → _observed = observed_dashboard_probe_row
```

---

## Tests executed

```powershell
python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py tests/test_failure_dashboard_controlled_failures.py -q
# 152 passed

python -m pytest -m golden_replay -q
# 68 passed
```

---

## Follow-up recommendation

**AO5 — Runtime vs test projection boundary clarity (doc-only)**

- Cross-link `game/final_emission_replay_projection.py` and `tests/helpers/golden_replay_projection.py` module docs
- Extend `tests/test_ownership_registry.py` if needed
- Zero behavior change; can run anytime

**AO6 — Machine-readable protected scenario registry**

- Optional Python registry for manifest PROTECTED scenario IDs ↔ test function names
- Reduces manual manifest ↔ test drift; independent of AO4

**Optional later:** Collapse `OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS` to `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS | CLASSIFIER_EVIDENCE_EXTENSION_FIELDS` (AO2 follow-on).

---

## Risks

- New shared fields must be added once in `_base_synthetic_observed_replay_row()` — profile defaults stay in one place
- Import path for new probes should prefer `replay_observed_row_fixtures` directly; sync/dashboard modules re-export for compatibility
