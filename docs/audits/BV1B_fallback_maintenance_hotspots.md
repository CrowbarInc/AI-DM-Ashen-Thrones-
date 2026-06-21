# BV1B — Fallback Maintenance Hotspots

**Date:** 2026-06-21

## Ranked by ownership concentration and post-BI modification

| Rank | File | Ownership refs | Post-BI touches | Responsibility | Legitimate owner vs accidental hub |
|---:|---|---:|---:|---|---|
| 1 | `tests/test_golden_replay_fallback_projection.py` | 276 | 1 | replay projection/governance | Legitimate replay projection owner |
| 2 | `tests/test_opening_fallback_owner_bucket.py` | 109 | 1 | fallback selection/projection | Legitimate router owner — BK-explicit selection/content responsibility |
| 3 | `tests/test_final_emission_visibility_fallback.py` | 84 | 3 | fallback selection/projection | Legitimate router owner — BK-explicit selection/content responsibility |
| 4 | `tests/test_final_emission_opening_fallback.py` | 51 | 2 | fallback selection/projection | Legitimate router owner — BK-explicit selection/content responsibility |
| 5 | `game/final_emission_visibility_fallback.py` | 48 | 4 | fallback selection/projection | Legitimate router owner — BK-explicit selection/content responsibility |
| 6 | `tests/test_final_emission_sealed_fallback.py` | 44 | 3 | fallback selection/projection | Legitimate router owner — BK-explicit selection/content responsibility |
| 7 | `tests/helpers/opening_fallback_evidence.py` | 42 | 1 | fallback selection/projection | Legitimate router owner — BK-explicit selection/content responsibility |
| 8 | `game/final_emission_sealed_fallback.py` | 26 | 3 | fallback selection/projection | Legitimate router owner — BK-explicit selection/content responsibility |
| 9 | `tests/test_fallback_incidence_report.py` | 18 | 2 | fallback selection/projection | Governance test facade — intentional assertion concentration |
| 10 | `game/fallback_provenance_debug.py` | 8 | 2 | fallback selection/projection | Peripheral fallback touch surface |
| 11 | `tests/test_fallback_incidence_trends.py` | 8 | 1 | fallback selection/projection | Governance test facade — intentional assertion concentration |
| 12 | `tests/test_fallback_recurrence.py` | 8 | 1 | fallback selection/projection | Governance test facade — intentional assertion concentration |

## Routing concentration (incidence-derived)

| Owner (selection) | Events | Share |
|---|---:|---:|
| `game.final_emission_visibility_fallback` | 1 | 100.00% |

| Owner (content) | Events | Share |
|---|---:|---:|
| `game.final_emission_sealed_fallback` | 1 | 100.00% |
