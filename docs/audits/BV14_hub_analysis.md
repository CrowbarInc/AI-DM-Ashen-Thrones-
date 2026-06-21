# BV14 — Hub Analysis

**Date:** 2026-06-21

---

## Executive answer

Concentration is **mixed authority/utility** with a **legitimate composition core** — not a pure accidental hub like BV13 `final_emission_text`, but **larger than a single authority should be** due to fallback FI sprawl and private-helper leaks.

## Classification matrix

| Signal | Evidence | Implication |
| --- | --- | --- |
| Multi-symbol FI | Top symbol FI 10 / module FI 52 (19%) | **Not** a single-symbol choke — heterogeneous concerns |
| Production breadth | 27/52 importers in `game/` (52%) | Production-core maintenance magnet |
| LOC / export surface | 3881 LOC, 47 public + 102 private defs | **Oversized** for stated downstream-consumer role |
| Fan-out | 17 deps including `game.gm` (circular risk) | Outward coupling moderate; **inbound** coupling is the problem |
| Fallback sprawl | `minimal_social_emergency_fallback_line` → 10+ production paths | Accidental **fallback hub** layered on composition authority |
| Private symbol imports | 8+ private helpers imported externally | Encapsulation failure — maintenance drag |
| Governance locks | BJ-115/116, BN8 preflight, gate delegator map | Team treats module as **strict-social authority seam** |
| Test legality owner | `tests/test_social_exchange_emission.py` BD-2 KEEP | Legitimate contract surface — decomposition must preserve |

## Verdict

| Question | Answer |
| --- | --- |
| Legitimate authority module? | **Partially** — composition + fallback content are real authorities |
| Mixed authority/utility? | **Yes** — composition + policy + fallback + telemetry + validator vocabulary |
| Accidental hub? | **Partially** — fallback sprawl and private leaks resemble BV13 utility accretion |
| Should it remain centralized? | **Core composition yes; periphery no** — BV13-style split for fallback/policy/validation |

## Comparison to BV13 `final_emission_text`

| Dimension | BV13 final_emission_text | BV14 social_exchange_emission |
| --- | --- | --- |
| Intent | Unplanned utility accretion | **Planned** strict-social authority (docstring) |
| Single-symbol dominance | 90% `_normalize_text` | 19% top symbol — **multi-concern** |
| LOC | 465 | **3881** |
| Decomposition driver | Symbol category heterogeneity | **Same** + encapsulation repair |
| Replay risk | Low (formatting) | **Medium-high** (fallback phrase catalog) |
| Legitimate core | Formatting primitive only | **Strict-social composition + fallback content** |

## Comparison to post-BV13 formatting hub

`final_emission_text_formatting` FI ~51 is **homogeneous** (one concern). `social_exchange_emission` FI 52 is **heterogeneous** (five concern categories) — decomposition ROI is **higher** despite similar FI number.
