# Dead Governance Archive — 2026-05-31 (Cycle AF Blocks AF-1, AF-4)

## Purpose

This folder holds **historical governance artifacts** moved out of active repo paths during Cycle AF. AF-1 files had **zero incoming references** (filename/stem scan) outside self-citation. AF-4 replay baseline/readiness docs were **superseded** by `docs/testing/protected_replay_manifest.md` but still had stale authority references in active docs.

**No active authority** files were moved: CI registries, closeouts, protected replay manifest, ownership ledger, runtime code, and operational snapshots (e.g. `audits/failure_dashboard_latest.md`) remain in place.

## Verification performed before move

For each file below:

- Substring search for filename/stem across `*.py`, `*.yml`, `*.md`, `*.txt`, `*.json` — **no non-self references**
- No `.github/workflows/*` references
- No pytest/tool imports of these paths
- Not listed as canonical authority in `docs/current_focus.md` or `docs/convergence_ci_inventory.md`

Commands used (repo root):

```bash
# Per-candidate grep (example pattern)
rg -l "failure_dashboard_contract_lock_2026-05-11" --glob "*.{py,yml,md,txt,json}" .

# Post-move governance validation
python -m pytest tests/test_ownership_registry.py -q
python -m pytest tests/test_validation_coverage_audit.py -q
python tools/validation_coverage_audit.py --strict
```

## Archived files

| Original path | Reason archived |
| --- | --- |
| `audits/failure_dashboard_contract_lock_2026-05-11.md` | Cycle B failure-dashboard operational memo; superseded by classifier tests + `failure_dashboard_latest.md` |
| `audits/failure_dashboard_cycle_b_closure_2026-05-11.md` | Historical Cycle B closure evidence; zero refs |
| `audits/failure_dashboard_final_integration_audit_2026-05-11.md` | Pre-integration audit memo; superseded by classifier harness |
| `audits/failure_dashboard_operationalization_2026-05-11.md` | Operationalization notes; zero refs |
| `audits/failure_dashboard_probe_harness_2026-05-11.md` | Probe harness design memo; zero refs |
| `audits/failure_dashboard_sample.md` | Sample output doc; zero refs |
| `audits/failure_locality_assessment.md` | Pre-closeout locality assessment; superseded by `docs/realization_failure_locality_closeout.md` |
| `audits/post_gate_sanitizer_rewrite_surface_inventory_2026-05-12.md` | Surface inventory; absorbed by later cycle closeouts |
| `audits/cycle_g_block1_full_suite_validation_20260519.txt` | Raw full-suite validation log; zero refs |
| `audits/cycle_g_block2_full_suite_validation_20260519.txt` | Raw full-suite validation log; zero refs |
| `audits/cycle_g_block3_full_suite_validation_20260519.txt` | Raw full-suite validation log; zero refs |
| `audits/cycle_g_runtime_stability_suite_hygiene_recon_20260518.md` | Cycle G recon; zero refs |
| `audits/cycle_g_tracked_runtime_snapshot_churn_recon_20260519.md` | Cycle G recon; zero refs |
| `audits/cycle_f_opening_projection_fixture_helper_recon_20260518.md` | Superseded by Cycle AC golden replay harness extraction |
| `audits/cycle_f_routing_policy_decision_memo_20260518.md` | Cycle F decision memo; zero refs |
| `audits/cycle_e_test_signal_ownership_thinning_closure_2026-05-17.md` | Superseded by Cycle AD/L test ownership work |
| `audits/golden_replay_baseline_2026-05-11.md` | Pre-promotion human-readable golden baseline; superseded by `docs/testing/protected_replay_manifest.md` (Cycle AF Block AF-4) |
| `audits/golden_replay_readiness_2026-05-11.md` | Pre-promotion readiness assessment; superseded by manifest + pytest golden replay gate (Cycle AF Block AF-4) |

## Not moved (intentionally)

- All paths listed in Cycle AF recon **Do not modify** guard list
- `audits/failure_dashboard_latest.md` — still referenced by failure classifier / dashboard helpers
- `audits/failure_dashboard_probe_sample.md`, `audits/failure_dashboard_precision_pass_2026-05-11.md` — not zero-ref; deferred
- `game/*.md` architecture mirrors — removed in Block AF-2
- `docs/cycles/cycle_r_*.md` — deferred (non-zero-ref or medium risk)
