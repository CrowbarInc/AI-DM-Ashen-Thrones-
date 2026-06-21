# BV1 — Fallback Incidence Validation

**Date:** 2026-06-21  
**Scope:** Measurement only. Read-side BP1/BP5/BP7 tooling over current repository artifacts.

## Executive summary

BP instrumentation was re-run on the current tree. A **first denominator-bearing incidence snapshot** was produced by scanning **107 canonical finalized-FEM instances** across `artifacts/` and `data/`, projecting lineage with the current `build_fem_runtime_lineage_events()` projector, and aggregating through `tools/fallback_incidence_report.py`.

| Metric | Value |
|---|---:|
| Eligible turns (canonical FEM) | 107 |
| Fallback turns | 74 |
| Fallback events | 74 |
| **Fallback trigger rate** | **69.16%** |
| Snapshots in history (before BV1) | 0 |
| Snapshots after BV1 append | 1 |

There is **no pre-BI or pre-BM incidence snapshot** for longitudinal comparison. BV1 establishes a **baseline**, not proof of decrease. Fallback behavior in the scanned corpus remains **high and concentrated** by route and owner, with explicit selection/content ownership on most events but **13 events missing owner bucket** metadata.

**Verdict:** Fallback incidence **did not decrease** relative to any prior snapshot (none existed). Behavior **did not disappear**; it is **legible and partially relocated** across visibility, sealed, and opening deterministic owners. Longitudinal trend classification: **`insufficient_history`** (one snapshot).

## Method

1. **Corpus construction (read-only):** Reused BP3 artifact-walk logic (`tools/fallback_projection_gap_reality_audit.py` scanners) over `artifacts/` + `data/`.
2. **Turn shaping:** Each canonical finalized FEM became one eligible turn with `meta.final_emission_meta` and projected `meta.runtime_lineage_events`.
3. **Incidence report:** `build_fallback_incidence_report()` → JSON/Markdown artifacts.
4. **History append:** `tools/fallback_incidence_trends.py --incidence-report …` appended snapshot to `artifacts/golden_replay/fallback_incidence_history.json`.
5. **Recurrence/anomaly pass:** `tools/fallback_recurrence.py`, `tools/fallback_incidence_anomalies.py`.

No runtime selectors, projection rules, replay scoring, or FEM write paths were modified.

## Fallback trigger and family distribution

### Top-level rates

| Measure | Count / rate |
|---|---:|
| Fallback trigger rate | 69.16% |
| Unknown-route turns | 1 (0.93%) |
| Turns with FEM | 107 (100%) |
| Turns with projected lineage events | 107 (100%) |

### Fallback kind (projected lineage)

| Kind | Events | Share of fallback events |
|---|---:|---:|
| `referential_clarity_hard_replacement` | 38 | 51.4% |
| `scene_opening` | 31 | 41.9% |
| `response_type_prepared_emission` | 4 | 5.4% |
| `sealed_passive_scene_pressure_fallback` | 1 | 1.4% |

### Owner bucket distribution

| Owner bucket | Events | Share |
|---|---:|---:|
| `sealed-gate` | 30 | 40.5% |
| `upstream-prepared` | 30 | 40.5% |
| *(missing / unbucketed)* | 13 | 17.6% |
| `unknown-ambiguous` | 1 | 1.4% |

### Selection vs content ownership (split dimension)

| Dimension | Top owner | Events |
|---|---|---:|
| Selection owner | `game.final_emission_visibility_fallback` | 38 |
| Selection owner | `game.final_emission_gate` | 32 |
| Content owner | `game.final_emission_sealed_fallback` | 39 |
| Content owner | `game.opening_deterministic_fallback` | 31 |

Event-level `owner` on projected lineage still reports `game.final_emission_gate` for all 74 events — a **projection packaging default**, not proof that gate code executed every selection. Selection/content owner fields show the **BK redistribution** into explicit fallback modules.

### Route-scoped incidence

| Route kind | Eligible turns | Fallback turns | Trigger rate |
|---|---:|---:|---:|
| `observe` | 44 | 42 | **95.45%** |
| `scene_opening` | 62 | 31 | **50.00%** |
| `unknown` | 1 | 1 | 100.00% |

### Final emission outcome (FEM)

| `final_route` | Fallback-associated events |
|---|---:|
| `replaced` | 72 |
| `accept_candidate` | 2 |

## Unresolved and weakly owned paths

| Gap | Count | Notes |
|---|---:|---|
| Fallback events without owner bucket | 13 / 74 | 17.6%; concentrated in referential/response-type shapes |
| `unknown-ambiguous` bucket | 1 | Named catch-all bucket still in use |
| Diegetic family on FEM | 1 / 74 | Realization-family coverage stronger (60/74) |
| Observed family on turn row | 0 / 74 | Scenario-spine-style observed family not present in artifact scan rows |
| BP2 unprojected catalog shapes on canonical FEM | 0 / 107 | BP3 confirmed; retry-terminal packaging does not survive to finalized FEM in corpus |

## Recurrence of fallback paths (BP7, first snapshot)

With only one history snapshot, recurrence classification is **transient by construction**:

| Classification | Entities |
|---|---:|
| Transient | 16 |
| Recurring / persistent / dominant | 0 |

Top snapshot concentrations (not yet longitudinal):

- Fallback kinds: `referential_clarity_hard_replacement`, `scene_opening`
- Owner buckets: `sealed-gate`, `upstream-prepared`
- Routes: `observe`, `scene_opening`

## Did fallback behavior decrease, remain stable, or relocate?

| Question | BV1 answer | Evidence strength |
|---|---|---|
| Decreased vs prior snapshot? | **Not assessable → no prior snapshot** | N/A |
| Stable vs structural expectation? | **High incidence persists** (69% on corpus) | Medium — corpus is stored FEM, not live traffic |
| Merely relocated? | **Yes, partially** | Medium-high — selection/content owners split across visibility/sealed/opening; gate facade thinned in code (BJ/BN) while lineage event owner label remains gate-default |
| Projection coverage improved? | **Yes** (BP2/BP3 unchanged at 78.95% shape catalog; 0 gap shapes on canonical FEM) | High |

**Net:** Fallback **incidence did not demonstrably fall**; ownership and lifecycle representation **improved**; maintenance relevance **shifted** from monolithic gate file to explicit fallback routers and replay/meta readers.

## Artifacts

| Artifact | Role |
|---|---|
| `artifacts/golden_replay/bv1_fallback_incidence_report.json` | BP1 JSON authority for BV1 run |
| `artifacts/golden_replay/bv1_fallback_incidence_report.md` | Operator view |
| `artifacts/golden_replay/fallback_incidence_history.json` | Append-only snapshot (1 row) |
| `artifacts/golden_replay/fallback_incidence_trends.md` | Trend report (`insufficient_history`) |
| `artifacts/golden_replay/fallback_recurrence_report.md` | Recurrence (`ok`, all transient) |
| `artifacts/golden_replay/fallback_incidence_anomalies.md` | Anomalies (`insufficient_history`) |
| `artifacts/bv1_fallback_summary.json` | Compact machine summary |

## Command log

| Command | Result |
|---|---|
| Artifact scan + `build_fallback_incidence_report` (inline, BP3 roots) | 107 turns, 74 fallback events, 69.16% rate |
| `python tools/fallback_incidence_trends.py --incidence-report artifacts/golden_replay/bv1_fallback_incidence_report.json --artifact-source BV1:artifact_scan_107_fem` | Snapshot appended |
| `python tools/fallback_recurrence.py` | `ok`, 1 snapshot |
| `python tools/fallback_incidence_anomalies.py` | `insufficient_history`, severity none |

## Confidence

| Claim | Confidence |
|---|---|
| First denominator-bearing incidence baseline exists | **High** |
| Incidence decreased after BI–BM | **Not supported** (no prior snapshot) |
| Fallback paths relocated to named owners | **Medium-high** |
| 69% rate characterizes production traffic | **Low** — replay/artifact corpus bias |
