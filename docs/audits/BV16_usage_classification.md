# BV16 — Usage Classification

**Date:** 2026-06-21

---

## Consumer groups (BV16 taxonomy)

| Usage class | Tag assignments | Share | Typical symbols / attrs |
| --- | --- | --- | --- |
| **finalize path** | 25 | 31% | `run_gate_terminal_enforcement_pipeline` via `strict_social_stack` / `generic_exit` |
| **tests** | 24 | 30% | gate legality, boundary convergence, player-facing purity suites |
| **visibility** | 16 | 20% | `terminal_pipeline.apply_visibility_enforcement` monkeypatch noop in layer tests |
| **IC** | 6 | 7% | `attach_interaction_continuity_validation`, `apply_interaction_continuity_emission_step` hooks |
| **N4** | 3 | 3% | `apply_acceptance_quality_n4_floor_seam` hook in selector snapshots + gate N4 tests |
| **replay** | 2 | 2% | transcript regressions with visibility noop + full gate path |
| **opening** | 1 | 1% | source inspection of `opening_fallback.reassert_*` inside pipeline body |
| **realization** | 1 | 1% | `apply_strict_social_emergency_fallback_patch` direct import in sealed fallback tests |
| **governance** | 1 | 1% | ownership registry BJ-73/74/75/76 direct-call assertions, gate_thin_boundary_locks |

> **Note:** Importers may appear in multiple classes. Totals sum to **79** tag assignments across **26** files.

## Finalize path cluster

**2 production modules** call `run_gate_terminal_enforcement_pipeline` directly:

- `game/final_emission_strict_social_stack.py` — strict accept/replace exit (2 call sites)
- `game/final_emission_generic_exit.py` — generic accept/replace exit (2 call sites)

Gate does **not** import terminal pipeline; stacks mediate. This is the **canonical production finalize tail**.

## Visibility cluster

**16** files monkeypatch `terminal_pipeline.apply_visibility_enforcement` to noop or trace — layer-isolation pattern for anti-railroading, context separation, player-facing purity, prompt context, tone escalation, speaker contract, social exchange emission, narration transcript regressions, gate orchestration order, boundary convergence.

Ownership tests (BJ-73) already assert terminal pipeline **calls visibility owner directly** in source — monkeypatch target is legacy convenience.

## N4 cluster

`test_final_emission_gate_selector_snapshots` and `test_final_emission_gate_n4` hook N4/IC via terminal namespace. BJ-74 ownership registry verifies direct call to `final_emission_acceptance_quality` owner.

## IC cluster

Fallback behavior gate tests hook IC emission step + fallback behavior layer via terminal namespace. `post_speaker_finalize_probe` wraps terminal-bound IC/visibility/N4 symbols for finalize stack divergence characterization.

## Replay cluster

Transcript regressions import terminal module for visibility noop only — replay sensitivity is **enforcement order + text mutations**, not terminal module identity.

## Governance cluster

`tests/test_ownership_registry.py`, `tests/helpers/gate_thin_boundary_locks.py`, `tests/test_final_emission_gate_delegator_regression.py` — BJ-42/69/73/74/75/76 boundary locks; verify terminal pipeline does not lazy-import gate namespace and calls extracted owners directly.

## Ownership bucket cross-cut

| Bucket | Importers |
| --- | --- |
| visibility-monkeypatch | 15 |
| terminal-orchestration | 6 |
| terminal-tail-monkeypatch | 2 |
| finalize-realization | 1 |
| ownership-governance | 1 |
| module-introspection | 1 |
