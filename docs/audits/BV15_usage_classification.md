# BV15 — Usage Classification

**Date:** 2026-06-21

---

## Consumer groups (BV15 taxonomy)

| Usage class | Tag assignments | Share | Typical symbols |
| --- | --- | --- | --- |
| **gate orchestration** | 31 | 43% | `apply_final_emission_gate`, module introspection for layer-order tests |
| **tests** | 30 | 41% | gate legality matrices, selector snapshots, block equivalence harnesses |
| **fallback** | 6 | 8% | fallback-behavior gate tests (indirect — gate invokes stacks, not fallback symbols) |
| **terminal pipeline** | 2 | 2% | `final_emission_runtime` re-export seam to API turn path |
| **governance** | 1 | 1% | ownership registry BN locks, gate_thin_boundary_locks, delegator regression |
| **diagnostics** | 1 | 1% | architecture audit + validation layer audit fixture strings |
| **validators** | 1 | 1% | — (no direct validator imports from gate) |

> **Note:** Importers may appear in multiple classes. Totals sum to **72** tag assignments across **31** files.

## Gate orchestration cluster

Primary production path: `api_turn_support` → `final_emission_runtime.finalize_player_facing_emission` → `apply_final_emission_gate`. Only **one** production module imports the gate directly.

Test cluster (15+ files) imports `apply_final_emission_gate` for end-to-end gate legality, orchestration order, N4 acceptance-quality floor, opening fallback, and block equivalence (S/T/U).

## Terminal pipeline cluster

`game/final_emission_runtime.py` is the **runtime adapter** — sole production importer. Terminal enforcement (`final_emission_terminal_pipeline`) is invoked from stack exit owners, not from gate imports.

## Module introspection cluster

**18** test modules use `import game.final_emission_gate as feg` for:

- Governance identity checks (re-export identity === origin owner)
- Source-text negative assertions (`feg._*` must not appear in stack owners)
- Monkeypatch equivalence harnesses

This FI is **governance overhead**, not accidental production utility sprawl.

## Governance cluster

`tests/test_ownership_registry.py`, `tests/helpers/gate_thin_boundary_locks.py`, `tests/test_final_emission_gate_delegator_regression.py` — BN1–BN11 boundary locks, BJ-129 thin-boundary enforcement.

## Replay cluster

Replay-sensitive tests import `apply_final_emission_gate` directly (not gate module introspection): `test_narration_transcript_regressions` exercises terminal path via stacks; gate FI here is **orchestration-order** not phrase-catalog.

## Ownership bucket cross-cut

| Bucket | Importers |
| --- | --- |
| module-introspection | 17 |
| gate-orchestration | 13 |
| ownership-governance | 1 |
