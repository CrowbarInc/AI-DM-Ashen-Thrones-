# BV1A — Maintenance Hotspots (Post-BI Window + BR Bug-Fix History)

**Date:** 2026-06-21
**Scope:** Rank files by bug-fix frequency, post-BI change frequency, and ownership reference concentration.

## Executive summary

Post-BI maintenance magnets are **program-work hubs**, not demonstrated defect-repair hotspots. `tests/test_ownership_registry.py` leads post-BI change frequency (5/10 commits). Pre-BI bug-fix concentration remains in **session/combat fixtures** and **gate/opening seams** — surfaces BI–BM partially decomposed but did not eliminate from historical corrective paths.

## Ranked hotspots

| rank | file | owner / responsibility | bug-fix touches | post-BI change touches | ownership refs | legitimate owner vs accidental hub |
|---:|---|---|---:|---:|---:|---|
| 1 | `tests/test_ownership_registry.py` | ownership enforcement / governance meta-router | 0 | 5 | 338 | Legitimate owner — cross-cutting registry assertions; high touch is intentional |
| 2 | `game/final_emission_visibility_fallback.py` | fallback selection/projection | 0 | 4 | 48 | Legitimate owner — router/schema hub; fan-in redistribution after BI–BM |
| 3 | `game/final_emission_terminal_pipeline.py` | — | 0 | 4 | 0 | Post-BI redistribution hub — touched by planned extraction/governance, not defect repair |
| 4 | `tests/test_final_emission_gate.py` | gate orchestration/preflight | 2 | 3 | 2 | Legitimate owner — thin facade after BJ; historical bug-fix cost remains |
| 5 | `game/final_emission_meta.py` | final-emission policy/metadata | 1 | 3 | 114 | Legitimate owner — router/schema hub; fan-in redistribution after BI–BM |
| 6 | `tests/test_final_emission_meta.py` | supporting contract/test | 0 | 3 | 338 | Legitimate owner — router/schema hub; fan-in redistribution after BI–BM |
| 7 | `game/final_emission_replay_projection.py` | replay projection/governance | 0 | 3 | 150 | Legitimate owner — cross-surface projection responsibility |
| 8 | `tests/test_final_emission_visibility_fallback.py` | fallback selection/projection | 0 | 3 | 84 | Legitimate owner — router/schema hub; fan-in redistribution after BI–BM |
| 9 | `tests/test_final_emission_sealed_fallback.py` | fallback selection/projection | 0 | 3 | 44 | Post-BI redistribution hub — touched by planned extraction/governance, not defect repair |
| 10 | `game/final_emission_sealed_fallback.py` | fallback selection/projection | 0 | 3 | 26 | Post-BI redistribution hub — touched by planned extraction/governance, not defect repair |
| 11 | `game/output_sanitizer.py` | sanitizer boundary | 0 | 3 | 23 | Post-BI redistribution hub — touched by planned extraction/governance, not defect repair |
| 12 | `game/final_emission_response_type.py` | final-emission policy/metadata | 0 | 3 | 8 | Post-BI redistribution hub — touched by planned extraction/governance, not defect repair |
| 13 | `game/final_emission_opening_fallback.py` | fallback selection/projection | 0 | 3 | 6 | Post-BI redistribution hub — touched by planned extraction/governance, not defect repair |
| 14 | `game/final_emission_non_strict_stack.py` | — | 0 | 3 | 0 | Post-BI redistribution hub — touched by planned extraction/governance, not defect repair |
| 15 | `game/final_emission_strict_social_stack.py` | — | 0 | 3 | 0 | Post-BI redistribution hub — touched by planned extraction/governance, not defect repair |

## Hotspot detail

### 1. `tests/test_ownership_registry.py`

- **Owner:** ownership enforcement / governance meta-router
- **Bug-fix touch count:** 0 (all-time BR cohort)
- **Post-BI change count:** 5 (of 10 post-BI commits)
- **Ownership reference count:** 338
- **Concentration assessment:** Legitimate owner — cross-cutting registry assertions; high touch is intentional

### 2. `game/final_emission_visibility_fallback.py`

- **Owner:** fallback selection/projection
- **Bug-fix touch count:** 0 (all-time BR cohort)
- **Post-BI change count:** 4 (of 10 post-BI commits)
- **Ownership reference count:** 48
- **Concentration assessment:** Legitimate owner — router/schema hub; fan-in redistribution after BI–BM

### 3. `game/final_emission_terminal_pipeline.py`

- **Owner:** —
- **Bug-fix touch count:** 0 (all-time BR cohort)
- **Post-BI change count:** 4 (of 10 post-BI commits)
- **Ownership reference count:** 0
- **Concentration assessment:** Post-BI redistribution hub — touched by planned extraction/governance, not defect repair

### 4. `tests/test_final_emission_gate.py`

- **Owner:** gate orchestration/preflight
- **Bug-fix touch count:** 2 (all-time BR cohort)
- **Post-BI change count:** 3 (of 10 post-BI commits)
- **Ownership reference count:** 2
- **Concentration assessment:** Legitimate owner — thin facade after BJ; historical bug-fix cost remains

### 5. `game/final_emission_meta.py`

- **Owner:** final-emission policy/metadata
- **Bug-fix touch count:** 1 (all-time BR cohort)
- **Post-BI change count:** 3 (of 10 post-BI commits)
- **Ownership reference count:** 114
- **Concentration assessment:** Legitimate owner — router/schema hub; fan-in redistribution after BI–BM

### 6. `tests/test_final_emission_meta.py`

- **Owner:** supporting contract/test
- **Bug-fix touch count:** 0 (all-time BR cohort)
- **Post-BI change count:** 3 (of 10 post-BI commits)
- **Ownership reference count:** 338
- **Concentration assessment:** Legitimate owner — router/schema hub; fan-in redistribution after BI–BM

### 7. `game/final_emission_replay_projection.py`

- **Owner:** replay projection/governance
- **Bug-fix touch count:** 0 (all-time BR cohort)
- **Post-BI change count:** 3 (of 10 post-BI commits)
- **Ownership reference count:** 150
- **Concentration assessment:** Legitimate owner — cross-surface projection responsibility

### 8. `tests/test_final_emission_visibility_fallback.py`

- **Owner:** fallback selection/projection
- **Bug-fix touch count:** 0 (all-time BR cohort)
- **Post-BI change count:** 3 (of 10 post-BI commits)
- **Ownership reference count:** 84
- **Concentration assessment:** Legitimate owner — router/schema hub; fan-in redistribution after BI–BM

## Remaining maintenance magnets (actionable)

1. **`tests/test_ownership_registry.py`** — governance meta-router; 311 ownership refs; touched in 5/10 post-BI commits. Legitimate but high fan-out.
2. **`game/final_emission_meta.py`** — schema/read-side hub (175 refs); BK + BU touches. Legitimate owner; growing read-side coupling.
3. **`game/final_emission_visibility_fallback.py`** — fallback selection router (43 refs); 4 post-BI touches. Legitimate router; 17/17 fan-in.
4. **`game/final_emission_replay_projection.py`** — replay projection owner (122 refs). Legitimate cross-surface responsibility.
5. **`data/session.json` / `data/combat.json`** — pre-BI bug-fix magnets (9 and 7 touches). Accidental fixture co-change pattern; not production modules.

## Evidence

| Source | Role |
|---|---|
| `docs/audits/BU_ownership_dependency_map.csv` | Ownership reference counts |
| `docs/audits/BV1_maintenance_cost_matrix.md` | Fan-in redistribution after BI–BM |
| `artifacts/bv1a_analysis.json` | Ranked hotspot machine data |
