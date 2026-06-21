# BV16 — Projection

**Date:** 2026-06-21
**Baseline:** Post-BV15 — `final_emission_gate` FI **30**, `final_emission_terminal_pipeline` FI **26**

---

## FI projection

| Stage | `final_emission_gate` FI | `final_emission_terminal_pipeline` FI | Top production hotspot |
| --- | --- | --- | --- |
| BV16 baseline | **30** | **26** | terminal finalize tail |
| After BV15 namespace cleanup (parallel) | ≤12 | 26 | terminal_pipeline |
| After monkeypatch migration to owners | ≤12 | **~6–8** (AST); BU ~26 until remeasure | gate orchestration |
| After emergency patch relocation | ≤12 | **~5–7** | formatting / fallback catalog |
| After BV16C governance cap | ≤12 | **≤6** | next BU-ranked module |
| After full tail extraction (not recommended) | ≤12 | ~2 | — |

## BV16 executive recommendation

| Question | Answer |
| --- | --- |
| Remain centralized finalize sequencer? | **Yes** — `run_gate_terminal_enforcement_pipeline` stays canonical |
| Decompose terminal body (visibility/N4/IC/opening splits)? | **No** — owners already extracted; splitting sequencer fragments order |
| Decompose terminal namespace / monkeypatch surface? | **Yes** — migrate **16** visibility (+ IC/N4) test hooks from terminal namespace to owner modules |
| Proceed to extraction phase (BV16A)? | **No** — governance cleanup only; optional helper relocation |

## Should BV16 proceed to extraction?

**No — governance cleanup only.** Evidence:

- Terminal is **legitimate finalize authority** — 2 production exit owners, single ordered entrypoint
- FI **26** is **test-monkeypatch inflated** (16 files patch `apply_visibility_enforcement` via terminal namespace)
- BV15 gate work established acyclic gate→stack→terminal boundary — tail extraction would **invert** that separation incorrectly
- BJ-73/74/75 ownership tests already verify direct owner calls — remaining work is **consumer migration**, not new modules

## Success criteria (BV16 analysis)

| Criterion | Status |
| --- | --- |
| Determine legitimate vs accidental hub | **Legitimate finalize sequencer** + accidental monkeypatch namespace |
| Measure fan-in concentration | **8% BU** on canonical entry; **66% AST** on visibility noop seam |
| Finalize boundary documented | Acyclic; 5 owner modules; 12 dual-import test files |
| Decomposition recommendation | **Keep sequencer centralized**; migrate monkeypatches; **defer tail extraction** |

## Replay risk assessment

| Factor | Risk | Mitigation |
| --- | --- | --- |
| Terminal enforcement order changes | **High** | `test_final_emission_gate_orchestration_order`, selector snapshots, block equivalence |
| Owner policy changes (visibility/N4/opening) | **High** | Owner-module test suites; terminal source-order governance tests |
| Monkeypatch target migration | **Low** | Point hooks at same owner callables — identity-preserving |
| Tail module extraction | **High** | **Avoid** — not in BV16 scope |
