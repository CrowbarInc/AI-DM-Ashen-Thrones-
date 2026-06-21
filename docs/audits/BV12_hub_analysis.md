# BV12 — Smoke Bridge Hub Analysis

**Date:** 2026-06-21  

---

## Executive answer

Concentration is **intentional aggregation** (BV7A/BV7C design) with **secondary accidental coupling** from BV10C FEM routing and dual-bridge fallback suites. The bridges are not monolith regrowth — they are **thin, governed choke points** that accumulated consumer migrations.

## Intentional aggregation (by design)

| Mechanism | Evidence |
|---|---|
| BV7 retired smoke monolith (FI 73→15) | `test_bv7c_emission_smoke_assertions_concentration_locked` |
| Named bridge facades for FEM read + gate integration | Module docstrings; ownership registry AL4/BV7A |
| Downstream must not import `game.final_emission_gate` directly | AS2 registry routing |
| BV10C FEM reads route through replay bridge | +10 FI on replay_smoke; observability facades for production |

## Accidental / secondary coupling

| Pattern | Impact |
|---|---|
| 25 suites import **both** bridges | Cross-domain edit churn when either bridge changes |
| `gate_integration_smoke` → `replay_smoke_assertions` import edge | Gate module FI partially depends on replay module |
| Alias imports (`as read_final_emission_meta_dict`) | Obscures symbol FI in static scans (12 alias sites) |
| Post-BV10 traffic into FEM read bridge | Shifted authority-cluster cost to replay smoke (+10 FI) |

## Verdict

| Question | Answer |
|---|---|
| Is this monolith regrowth? | **No** — 4 exports total, 84 LOC combined |
| Is concentration intentional? | **Yes** — BV7/BV10 governance pattern |
| Is further decomposition warranted? | **Yes** — consumer graph is domain-heterogeneous (6 usage classes) |
| Replay risk if decomposed carefully? | **Low-medium** — symbols are pure delegates; no assertion logic in bridges |

## Fan-out (dependency tail)

| Module | Production fan-out |
| --- | --- |
| replay_smoke_assertions | `game.final_emission_meta_read` |
| gate_integration_smoke | `game.final_emission_runtime` |

