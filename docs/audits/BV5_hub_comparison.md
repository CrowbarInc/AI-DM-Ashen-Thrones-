# BV5 — Maintenance Hub Comparison

**Date:** 2026-06-21  
**Scope:** Re-measure maintenance hubs after BV2 (meta consolidation), BV3 (fallback observe-route reduction), BV4B (concrete-beat upstream satisfier).  
**Baseline:** BV1C integrated matrix and BU scan at BV1 closeout.  
**Method:** `scripts/bu_final_emission_coupling_discovery.py`, BV1B incidence re-run, BV4B metrics, attribution BS artifacts.

---

## Executive answer

BV2–BV4 ** materially changed hub economics** on fallback and meta read paths. Fallback routing volume **collapsed** on the BV3D corpus; meta **split** into a smaller write core plus explicit read facades. **Unchanged dominant hubs:** `emission_smoke_assertions` (73 FI), `test_ownership_registry` (57 FO), `terminal_pipeline` (26 FI). BV4's planned test-facade decomposition **did not ship**.

---

## Hub comparison table

| Area | BV (BV1C baseline) | Current (BV5) | Delta |
|---|---|---|---|
| **`final_emission_meta`** | FI **61**, FO **6**; #2 ecosystem hub; 134 ownership refs; 20+ write owners | FI **24**, FO **8**; production importers **22**, tests **2** | **−37 FI** on core module; write path consolidated |
| **`final_emission_meta_read`** | Did not exist (reads via meta) | FI **28**, FO **1**; production **20**, tests **8** | **+28 FI** new read delegate (BV2A) |
| **`final_emission_owner_bucket_views`** | Did not exist | FI **22**, FO **1** | **+22 FI** bucket vocabulary surface (BV2A) |
| **Meta ecosystem total** | **61** direct meta imports | **74** (meta + read + views) | **+13** net imports; **redistributed** not eliminated |
| **Replay projection** | `final_emission_replay_projection` **15/4**; `golden_replay_projection` **18/7**; area FI **86** | `final_emission_replay_projection` **15/5**; `golden_replay_projection` **14/6** | Replay owner stable; golden adapter **−4 FI** |
| **Fallback routing** | `visibility_fallback` **17/17**; incidence **69.16%** (107 FEM); observe **95.45%**; RC **38** events | `visibility_fallback` **17/18**; incidence **1.05%** (95 FEM); observe **4.35%**; RC **1** event | **Incidence −68.11 pp** (cross-scope); router FI unchanged |
| **Ownership views** | Registry FO **57**, 320 refs; owner bucket gaps **13** runtime events | Registry FO **57** unchanged; runtime ownerless **0/1** | Governance router **unchanged**; runtime stamping **improved** |
| **Test facades** | `emission_smoke_assertions` **70/5**; registry **57** FO; gate stub **19 LOC** | `emission_smoke_assertions` **73/5**; registry **57** FO; BV4B tests added to smoke consumers | Smoke **+3 FI**; BV4 facade cycle **deferred** |
| **`final_emission_gate`** | **28/7**, prod FI **1**, 308 LOC | **30/9**, prod FI **1** | **+2 FI** from BV3/BV4 satisfier hooks |
| **`final_emission_passive_scene_pressure`** | Not a maintenance hub | New module; BV4B satisfier owner; imports meta + replay projection | **New hub** (bounded, targeted) |
| **`terminal_pipeline`** | **26/13** convergence hub | **26/14** | Unchanged FI; +1 FO |
| **Attribution reads** | Owner bucket **38.78%**; `realization_provenance` **28/1** | Unchanged BS metrics | No BV5 regression; no BV2–BV4 attribution refresh |

---

## Area notes

### Final emission meta (BV2)

BV2C closed at meta FI **22**; current **24** (+2) from BV4 production hooks (`passive_scene_pressure`, visibility skip guards). Read-side coupling moved to:

- `final_emission_meta_read` — stage diff, smoke delegate, replay telemetry reads
- `final_emission_owner_bucket_views` — fallback bucket tests and incidence adapters

**Net:** fewer direct writes touch meta schema; more **named import targets** for readers. Maintenance blast radius on schema edits **likely lower**; import graph **wider but typed**.

### Replay projection

`final_emission_replay_projection` remains the legitimate runtime lineage owner (**15 FI**). BV2B migrated replay adapters off direct meta reads. Speaker-projection recurrence (**8** protected rows) **unchanged** — replay maintenance drag on speaker drift **not reduced** by BV2–BV4.

### Fallback routing (BV3 + BV4B)

| Phase | Events | Incidence | Dominant family | Observe rate |
|---|---:|---:|---|---:|
| BV1B (107 FEM) | 74 | 69.16% | RC hard replace (38) | 95.45% |
| BV3F (95 FEM) | 11 | 11.58% | PSP (10) | 47.83% |
| BV5 (95 FEM) | 1 | 1.05% | RC hard replace (1) | 4.35% |

Fallback **router fan-in unchanged**; **trigger volume** fell — maintenance cost shifted from **high-frequency fallback debugging** to **low-frequency residual RC shape work**.

### Test facades

Largest fan-in node remains **`emission_smoke_assertions` (73)**. BV4 (planned facade decomposition) was **superseded by BV4B concrete-beat work**; test coupling **increased slightly** (+3 importers including BV4B suite).

---

## Residual dominant hubs (post-BV5)

| Rank | Hub | FI / FO | Why still dominant |
|---:|---|---:|---|
| 1 | `tests.helpers.emission_smoke_assertions` | **73 / 5** | Cross-cutting test delegate |
| 2 | `game.final_emission_meta_read` | **28 / 1** | BV2 read-side concentration |
| 3 | `game.final_emission_terminal_pipeline` | **26 / 14** | BJ finalize convergence |
| 4 | `game.final_emission_meta` | **24 / 8** | Schema/write core |
| 5 | `game.final_emission_owner_bucket_views` | **22 / 1** | Bucket vocabulary |
| 6 | `tests.test_ownership_registry` | **0 / 57** | Governance fan-out router |

---

## Evidence

| Source | Role |
|---|---|
| `docs/audits/BU_import_fan_in_fan_out.csv` | Current FI/FO |
| [BV1C_hub_migration_analysis.md](BV1C_hub_migration_analysis.md) | BV baseline hub taxonomy |
| [BV2C_fan_in_closeout.md](BV2C_fan_in_closeout.md) | Meta consolidation timeline |
| [BV3F_reduction_classification.md](BV3F_reduction_classification.md) | BV3 incidence reduction |
| [BV4B_concrete_beat_report.md](BV4B_concrete_beat_report.md) | BV4B PSP elimination |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Current incidence |
