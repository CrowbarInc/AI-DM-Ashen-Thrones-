# BV15 — Projection

**Date:** 2026-06-21
**Baseline:** Post-BV14 — `final_emission_gate` FI **30**, `final_emission_terminal_pipeline` FI **26**

---

## FI projection

| Stage | `final_emission_gate` FI | `final_emission_terminal_pipeline` FI | Top production hotspot |
| --- | --- | --- | --- |
| BV15 baseline | **30** | **26** | gate orchestration owner |
| After namespace re-export retirement | ~28–30 | 26 | unchanged BU (0 external re-export consumers) |
| After governance `feg` migration | **~14–17** | 26 | terminal_pipeline |
| After BV15C cap | **≤12** | 26 | terminal_pipeline **26** |
| After BV16 terminal decomposition | ≤12 | **~8–12** | formatting hub / fallback catalog |

## BV15 executive recommendation

| Question | Answer |
| --- | --- |
| Remain centralized orchestration? | **Yes** — `apply_final_emission_gate` stays canonical |
| Decompose gate body further? | **No** — BN series already extracted stacks/preflight |
| Decompose gate namespace? | **Yes** — retire 13 re-exports; cap governance FI |
| Pair with terminal pipeline? | **Yes** — BV16 should target `final_emission_terminal_pipeline` |

## Should terminal pipeline become BV16?

**Yes.** Evidence:

- Terminal FI **26** with **14 fan-out** and **23 test importers** — behavior-heavy finalize coupling
- Gate→terminal direction is acyclic; terminal owns replay-sensitive enforcement patches
- Gate BV15 work is primarily **governance + namespace**; terminal BV16 is **authority split** (visibility, N4, opening, IC tail)

## Success criteria (BV15 analysis)

| Criterion | Status |
| --- | --- |
| Determine legitimate vs accidental hub | **Legitimate orchestration** + accidental namespace/governance FI |
| Measure fan-in concentration | **57%** on `apply_final_emission_gate`; module FI governance-inflated |
| Gate/terminal boundary documented | Acyclic; stacks mediate; 12 dual-import test files |
| Decomposition recommendation | **Keep orchestration centralized**; retire re-exports; **defer behavior split to BV16** |

## Replay risk assessment

| Factor | Risk | Mitigation |
| --- | --- | --- |
| Orchestration order changes | **Medium** | `test_final_emission_gate_orchestration_order` + block equivalence suites |
| Re-export namespace retirement | **Low** | Identity-preserving; update governance imports only |
| Terminal pipeline split (BV16) | **High** | Golden replay + visibility/N4 suites before migration |
