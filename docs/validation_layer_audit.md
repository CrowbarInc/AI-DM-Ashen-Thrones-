# Validation layer audit (Objective #11, Block C)

## Purpose

`tools/validation_layer_audit.py` is a **maintainer-facing** drift watch for the five canonical validation layers (see `docs/validation_layer_separation.md`). It does **not** prove semantics and does **not** replace code review. It encodes **low-noise** heuristics (especially import seams) so obvious ownership mistakes are caught early.

Canonical ownership is defined by:

- **Prose:** `docs/validation_layer_separation.md` (includes Block D closeout and fenced residue summary)
- **Executable registry:** `game/validation_layer_contracts.py`
- **Block B residue (tolerated compatibility inventory):** `docs/validation_layer_separation_block_b_residue.md` — **non-authoritative** except as a labeled checklist; must not contradict the registry or main contract doc.

Runtime seam clarifications from Block B (NA shadow read, gate file split, offline evaluator naming) are **governed**; the audit treats them as **residue-aligned**, not bugs.

## How to run

From the repo root:

```powershell
py -3 tools/validation_layer_audit.py
```

Optional:

- `--json` — machine-readable report on stdout (includes findings, scan list, summary counts).
- `--scan-root PATH` — repeat to scan extra directories (defaults to `./game`). Paths outside the repo are allowed (for fixtures or local experiments).
- `--strict` — exit with status **2** if any **likely_drift** finding is present (default exit **0** so benign within-layer splits do not fail CI unless you opt in).

## Interpreting results

### Benign within-layer splits vs ownership drift

- **Multiple Python modules implementing one canonical layer** (for example `final_emission_gate.py`, `final_emission_repairs.py`, `final_emission_validators.py`) is **expected** and matches Block B residue: one **gate** layer, several files.
- **likely_drift** usually means a **high-signal** pattern fired (for example an offline evaluator module importing live gate/repair surfaces, or a planner module importing gate orchestration). Treat it as “confirm in review,” not automatic proof of a bug.
- **review** items are **wording or ambiguity** hints (for example subjective quality phrasing in a gate file). They flag text worth reading; they are not a blanket failure.

### Block B residue

The audit **loads** `docs/validation_layer_separation_block_b_residue.md` and surfaces its themes in the report. Those items are **monitored**: when code or comments evolve, reviewers should check that the residue description still matches behavior (shadow read stays non-owning, NA diagnostics stay non-scoring, evaluator stays offline).

## Tests

Lightweight smoke coverage lives in `tests/test_validation_layer_audit_smoke.py` (repo scan, JSON shape, synthetic drift via a temporary scan root). Additional seam locks live in `tests/test_validation_layer_closeout.py` and `tests/test_validation_layer_separation_runtime.py`.
