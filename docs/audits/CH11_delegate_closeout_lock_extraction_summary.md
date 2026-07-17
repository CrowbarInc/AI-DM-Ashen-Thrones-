# CH11 Delegate-Collapse Closeout Lock Extraction

## Objective

Reduce governance concentration in `tests/test_ownership_registry.py` by extracting the BJ-70–BJ-129 delegate-collapse closeout lock family into a focused helper while preserving the central test file as the enforcement aggregator. Move implementation—not policy.

## Files Modified

| File | Change |
| --- | --- |
| `tests/ownership_closeout_delegate_locks.py` | **Added** — BJ-123–BJ-127 path/fragment registries, scan/collect helpers, registry-doc reader, and 60 `verify_bj*` validation routines |
| `tests/test_ownership_registry.py` | **Updated** — imports closeout helper; retains all BJ-70–BJ-129 enforcement tests as thin wrappers; BJ-123–BJ-127 constants and BJ-128/BJ-129 duplicate import block removed; module docstring BJ-129 corpus anchor added |

`tests/helpers/gate_thin_boundary_locks.py`, `tests/helpers/gate_delegator_governance.py`, `tools/test_audit.py`, and production modules were **not** modified.

## Helper Logic Extracted

Into `tests/ownership_closeout_delegate_locks.py`:

**Constants / path registries (BJ-123–BJ-127)**

- `BJ123_ALLOWED_FEG_PATCH_SYMBOLS`, `BJ123_STALE_FEG_PATCH_FRAGMENTS`, `BJ123_HARNESS_PATCH_SCAN_PATHS`
- `BJ124_DEAD_GATE_REEXPORT_SYMBOLS`, `BJ124_DEAD_GATE_IMPORT_MARKERS`
- `BJ127_GLOBAL_SCAN_EXCLUDE`, `BJ127_FEG_ALIAS_IMPORT_ALLOWLIST`, `BJ127_FEG_ALIAS_IMPORT_MARKERS`

**Scan / collect helpers**

- `collect_stale_feg_patch_fragment_violations`
- `iter_bj127_global_harness_scan_paths`
- `collect_bj127_feg_alias_import_violations`

**Registry corpus I/O**

- `ownership_registry_doc` (reads central enforcement module, not helper `__file__`)
- `repo_root` / `get_repo_root`

**Delegate-collapse validation (60 public `verify_bj*` routines)**

- BJ-70–BJ-129 closeout locks: stack/exit direct-owner calls, harness monkeypatch seams, gate dead re-export removal, global stale-`feg` scan, thin gate boundary (BJ-128/BJ-129 via `gate_thin_boundary_locks`)

BJ-128/BJ-129 assertion builders remain canonical in `tests/helpers/gate_thin_boundary_locks.py`; the closeout helper imports and invokes them.

## Remaining Central Enforcement

In `tests/test_ownership_registry.py` only:

- **60 BJ-70–BJ-129 enforcement tests** — each a thin wrapper calling the matching `verify_bj*` helper
- **Earlier BJ cycle entrypoint locks** (BJ-27–BJ-69, BJ-40–BJ-49, etc.) — unchanged inline enforcement
- Module docstring policy corpus (including new BJ-129 thin-boundary documentation anchor)

## Compatibility Verification

Confirm:

- **Governance unchanged** — identical delegate-collapse assertions, markers, fragment lists, and failure strings (registry-doc checks still target `tests/test_ownership_registry.py` via `ownership_registry_doc()`).
- **Ownership unchanged** — no production or owner-suite edits.
- **Runtime unchanged** — test-only relocation.
- **CI unchanged** — no workflow or tooling edits.
- **Central ownership test still invokes guards** — every `test_bj70`–`test_bj129` calls extracted helpers.
- **No pytest dependency in pure helper logic** — helper imports `pathlib`, `typing`, `gate_thin_boundary_locks`, and optional lazy `game.*` / `tests.*` inside verify bodies only.

### Validation run

```text
py -3 -c "import tests.ownership_closeout_delegate_locks; import tests.test_ownership_registry"  # OK
py -3 -m pytest tests/test_ownership_registry.py -q -k "bj70 or ... or bj129"   # 59 passed, 1 failed (BJ-127, pre-existing)
py -3 -m pytest tests/test_ownership_registry.py -q -k "bj27 or bj49 or bj69 or bv16c"  # 4 passed
py -3 -m pytest tests/test_test_audit_tool.py -q  # 45 passed
```

Pre-existing repository failure (unrelated to CH11 extraction logic):

- `test_bj127_ownership_registry_global_stale_gate_harness_scan` — substring scan false-positive on `tests/test_final_emission_gate_delegator_regression.py`, which legitimately references stale `feg` patch strings as negative-test fixtures (`stale = 'monkeypatch.setattr(feg, "build_final_strict_social_response"'`). **Same failure on git HEAD before CH11** (verified by running HEAD `test_bj127` without the new helper module).

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` | **866** (5959 → 5093, git HEAD baseline) |
| Lines added to `tests/ownership_closeout_delegate_locks.py` | **1295** |
| Reusable helpers extracted | **6** scan/collect/doc helpers + **60** `verify_bj*` routines |
| Enforcement tests remaining in central file | **60** BJ-70–BJ-129 wrappers (+ earlier BJ entrypoint locks unchanged) |
| Tests run (this block) | **108** (59 BJ-70–129 + 4 adjacent + 45 audit tool; BJ-127 documented pre-existing fail) |

## Remaining Ownership Concentration

**Estimated remaining line count:** ~5090 in `tests/test_ownership_registry.py`.

**Largest remaining families:**

1. **Inline `RESPONSIBILITY_REGISTRY` + governance orchestration** (~900+ lines) — CH10 target (`ownership_inventory_governance` + `ownership_registry_contract` wiring) when re-applied to working tree.
2. **Earlier BJ entrypoint / gate-wrapper locks** (BJ-27–BJ-69, BJ-40–BJ-49) — policy tests with moderate duplication; could follow CH11 pattern into the same closeout helper if desired.
3. **BV compat / BN gate-context guard families** — already partially extracted (BN, BV16C, BI-8, etc.).
4. **BE6/AL4 documentation-lock tests** — intentionally central.

**Further locality extraction before ending CH:** worthwhile for **inventory/registry deduplication (CH10)** and optionally **BJ-27–BJ-69** entrypoint locks using the same `verify_*` pattern; diminishing returns afterward as remaining bulk is policy corpus and heterogeneous guard families.
