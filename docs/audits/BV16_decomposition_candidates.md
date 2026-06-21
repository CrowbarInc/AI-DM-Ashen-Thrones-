# BV16 — Decomposition Candidates

**Date:** 2026-06-21

---

## Executive framing

Unlike pre-BN gate monoliths, terminal pipeline is **already a thin sequencer** over extracted owners. BV16 decomposition targets are **monkeypatch seam retirement** and optional **helper relocation**, not tail extraction.

## Candidate modules

| Candidate | Extract / action | Est. FI absorbed | Consumers | Migration cost | Replay risk |
| --- | --- | --- | --- | --- | --- |
| **`terminal_visibility_policy`** | Extract visibility ordering wrapper | **0 BU** — owner exists | 0 production | **High** — splits sequencer | **High** |
| **`terminal_opening_projection`** | Extract generic_accept opening reassert slice | **0 BU** | 0 production | **Medium** | **Medium** — opening accept debug |
| **`terminal_ic_projection`** | Extract IC step/attach ordering | **0 BU** | 0 production | **High** | **High** — strict_accept IC path |
| **`finalize_realization_adapter`** | Move `apply_strict_social_emergency_fallback_patch` to `sealed_fallback` | **−1 AST** | 1 test | **Low** | **Low-medium** — fallback stamping |
| **Monkeypatch migration to owners** | Point tests at `visibility_fallback`, `acceptance_quality`, `interaction_continuity` | **−~20 AST module FI** | 20+ test files | **Medium** — wide test diff | **Low** — noop hooks preserved |
| **Keep centralized sequencer** | No body split; document canonical entry only | **0** | 2 production | **None** | **None** |

## Not recommended

| Candidate | Reason |
| --- | --- |
| Split `run_gate_terminal_enforcement_pipeline` into profile-specific modules | Fragments **single enforcement order** — high replay risk |
| Merge terminal into gate | Inverts BV15 boundary — gate must not own finalize tail |
| Merge terminal into visibility/opening/IC owners | Each owner would need cross-concern ordering knowledge |
| Full module elimination | Legitimate finalize sequencer — 2 production exit paths depend on it |

## Projected FI reduction (module-level)

| Stage | `final_emission_terminal_pipeline` BU FI | Notes |
| --- | --- | --- |
| Current | **26** | 2 production + 23 test + 1 helper |
| After monkeypatch target migration | **~4–6** | BU may remain 26 until CSV refresh; AST drops sharply |
| After emergency patch relocation | **~4–6** | −1 direct symbol import |
| After BV16C governance cap | **≤6** | Production + ownership tests only |
| After full tail extraction | **~2** | **Not recommended** — sequencer authority lost |

**Primary win is governance clarity**, not massive BU FI drop — **16** visibility monkeypatches dominate AST FI but not BU caller CSV.
