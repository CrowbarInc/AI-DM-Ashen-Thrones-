# CH8 BV16C Terminal Monkeypatch Guard Extraction

## Objective

Reduce governance concentration in `tests/test_ownership_registry.py` by extracting the BV16C terminal monkeypatch guard family into a focused helper while preserving the central test file as the enforcement aggregator. Move implementation—not policy.

## Files Modified

| File | Change |
| --- | --- |
| `tests/ownership_guard_bv16c_terminal_monkeypatch.py` | **Added** — BV16C constants, scan allowlist, path iterator, and pure validation helpers |
| `tests/test_ownership_registry.py` | **Updated** — imports BV16C helpers; retains 1 enforcement test as aggregator |
| `tests/helpers/gate_thin_boundary_locks.py` | **Updated** — BV16C constants removed; thin re-exports from focused helper for backward compatibility |

`tools/test_audit.py` was **not** modified (no import changes required).

## Implementation Moved

Into `tests/ownership_guard_bv16c_terminal_monkeypatch.py`:

**Constants / monkeypatch policy surface**

- Owner module paths (`BV16C_TERMINAL_PIPELINE_MODULE`, `BV16C_VISIBILITY_OWNER`, `BV16C_N4_OWNER`, `BV16C_IC_OWNER`, `BV16C_OPENING_OWNER`, `BV16C_REPAIRS_OWNER`)
- `BV16C_TERMINAL_ORCHESTRATION_SYMBOLS`
- `BV16C_FORBIDDEN_TERMINAL_DELEGATE_MONKEYPATCH_MARKERS`
- `BV16C_TERMINAL_MONKEYPATCH_SCAN_ALLOWLIST` (constant-holder path updated from `gate_thin_boundary_locks.py` to this helper; same 4-entry allowlist semantics)
- `BV16C_TERMINAL_MONKEYPATCH_SCAN_ROOTS`

**Pure validation (2 public + 1 private helper)**

- `collect_bv16c_terminal_delegate_monkeypatch_violations`
- `iter_bv16c_terminal_monkeypatch_scan_paths`
- `_normalize_test_rel_path` (private path normalizer)

## Remaining Central Enforcement

In `tests/test_ownership_registry.py` only:

- **1 enforcement test** — `test_bv16c_ownership_registry_terminal_pipeline_delegate_monkeypatch_governance` (scan → collect → assert + registry docstring lock)
- Module docstring BV16C references elsewhere unchanged

All other guard families remain in central file or prior helpers (BN, BV compat, BD-6, BA-7, BI-8, inventory governance, BJ closeout locks, etc.).

## Compatibility Verification

Confirm:

- **Enforcement unchanged** — BV16C test passes; identical forbidden marker tuple and violation message strings.
- **Monkeypatch policy unchanged** — same 10 forbidden delegate monkeypatch markers; same owner-module guidance in diagnostics.
- **Scan coverage unchanged for governed tests** — 575 `tests/**/*.py` paths scanned; allowlist still excludes governance module, constant-holder helper, and BV16C migration/audit tools. `gate_thin_boundary_locks.py` is now scanned but contains no forbidden markers (clean pass).
- **Allowlist semantics unchanged** — 4 paths; only constant-holder entry relocated to the new helper module.
- **Central ownership test still invokes the guard** — enforcement test imports and calls moved helpers.
- **No pytest dependency in pure helper logic** — imports only `pathlib` and typing.
- **Runtime unchanged** — test-only relocation; no production module edits.
- **CI unchanged** — no workflow or tooling edits.

### Validation run

```text
py -3 -c "import tests.ownership_guard_bv16c_terminal_monkeypatch; import tests.helpers.gate_thin_boundary_locks; import tests.test_ownership_registry"  # OK
py -3 -m pytest tests/test_ownership_registry.py -q -k "bv16c"                                                    # 1 passed
py -3 -m pytest tests/test_ownership_registry.py -q -k "bv16c or bv12c or bv13c or bv14c or bv7c or ba7"          # 20 passed
py -3 -m pytest tests/test_test_audit_tool.py -q                                                                  # 45 passed
```

Pre-existing repository failures (unrelated to CH8):

- `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports` — compressed gate/replay-projection imports in helpers and golden-replay suites (documented since CH3/CH6).

## Metrics

| Metric | Value |
| --- | --- |
| Lines removed from `tests/test_ownership_registry.py` | **56** (4853 → 4797) |
| Lines added to `tests/ownership_guard_bv16c_terminal_monkeypatch.py` | **100** |
| Helper functions extracted | **2** public (+ 1 private path normalizer) |
| Enforcement tests remaining in central file | **1** BV16C test |
| Tests run (this block) | **66** (1 BV16C + 20 adjacent BV/BA-7 + 45 audit tool) |

## Remaining Ownership Concentration

**Next safest extraction candidate: BI-8 golden replay ownership boundary.**

Rationale:

- Small cohesive surface: BI-8 constants plus `test_bi8_golden_replay_ownership_boundary_is_locked` documentation-lock test (~lines 392+, 2365+).
- No AST scan iterator; mostly committed documentation phrase checks against registry/governance corpus.
- Natural helper name: `tests/ownership_guard_bi8_golden_replay_boundary.py` (or similar).

**Largest remaining implementation family still embedded: inventory governance orchestration** (`collect_ownership_governance_errors`, `_allowed_governance_committed_paths`, registry index integration, and the duplicated `RESPONSIBILITY_REGISTRY` block still in the central file ~lines 533–830). This remains the broadest concentration and should follow smaller guard extractions (BI-8).

Other candidates: **BJ70–BJ129 delegate-collapse closeout locks** (large test concentration, not reusable guard logic), **registry contract deduplication** (wire central file to import `ownership_registry_contract` instead of duplicating registry data).
