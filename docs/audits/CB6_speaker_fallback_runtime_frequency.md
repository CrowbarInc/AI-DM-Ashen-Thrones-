# CB6 Speaker / Fallback Runtime Frequency

**Block:** CB6 — Speaker/Fallback Runtime Frequency Probe  
**Type:** Read-only measurement (no runtime behavior changes)  
**Probe tool:** [`tools/cb6_speaker_fallback_frequency_probe.py`](../../tools/cb6_speaker_fallback_frequency_probe.py)  
**Machine output:** [`artifacts/cb6_speaker_fallback_frequency.json`](../../artifacts/cb6_speaker_fallback_frequency.json)  
**Generated:** 2026-06-23

---

## Executive summary

This block closes the BV1 evidence gap by **separating protected replay recurrence from representative runtime artifact incidence**. Key findings:

| Signal | Speaker | Fallback |
|---|---|---|
| **BV3D runtime artifact rate** | **0.00%** speaker_repair (0 / 95 FEM turns) | **1.05%** trigger rate (1 / 95 turns) |
| **BV1 legacy artifact rate** | Not instrumented in BV1 snapshot | **69.16%** (74 / 107 turns) |
| **Protected replay recurrence** | **8 raw rows → 1 unique defect** (BV8A dedupe) | Fallback-drift keys present but low volume |
| **Confidence** | **Low** for runtime incidence | **Medium** (scope-sensitive) | **High** for recurrence vs runtime separation |

**Readiness verdict:** Measured frequency **does not justify** reclassifying `speaker_identity_adoption` or `fallback_sanitizer_repairs` from **prohibited → caution**. Coupling, acceptance authority, and protected-field exposure remain the governing risks—not turn-level artifact rates on the current BV3D corpus.

---

## Measurement source inventory

| Source | Path / tool | Coverage | Limitations |
|---|---|---|---|
| BV1 fallback incidence snapshot | `artifacts/bv1_fallback_summary.json`, `artifacts/golden_replay/bv1_fallback_incidence_report.json` | 107 canonical FEM instances (legacy wide scan) | Pre-BV3D scope; 69.16% rate not comparable to BV3D without scope note |
| BV1B / BV3D fallback incidence | `artifacts/bv1b_fallback_summary.json`, `tools/bv1b_fallback_incidence_validation.py` | 95 FEM instances (BV3D roots) | Excludes refresh archives; not live user traffic |
| Fallback incidence report builder | `tools/fallback_incidence_report.py` | Turn-scoped `fallback_selected` lineage from finalized FEM | Read-only; requires artifact JSON with FEM |
| Fallback recurrence / trends | `artifacts/golden_replay/fallback_recurrence_report.md`, `tools/fallback_recurrence.py` | Snapshot history (2 snapshots) | Short history; advisory only |
| Protected replay recurrence | `artifacts/golden_replay/bug_recurrence_history.json` | 6 governed keys; speaker_drift dominant | **Protected-replay-only** population; backfill inflation (BV8A) |
| BV8A speaker recurrence audit | `docs/audits/BV8A_recurrence_audit.md` | Speaker projection key dedupe | 8 rows = 1 defect |
| Runtime lineage vocabulary | `game/runtime_lineage_telemetry.py` | `speaker_repair`, `fallback_selected` event kinds | Diagnostic read-side; zero speaker repairs in BV3D rescan |
| Golden replay outputs | `tests/test_golden_replay_structural_invariants.py`, manifest | 6+ protected speaker/route scenarios | Acceptance failures ≠ runtime turn rate |
| Attribution reports | `artifacts/bv1_attribution_completeness_report.md`, `tools/fallback_maintenance_economics.py` | Owner bucket / repair_kind completeness | Not turn-frequency |
| Owner drift hotspots | `artifacts/golden_replay/owner_drift_hotspots.md` | 1 `selected_speaker_source` classification | Test-run scoped |
| CB6 probe (this block) | `tools/cb6_speaker_fallback_frequency_probe.py` | Aggregates above + live BV3D rescan | Advisory JSON only |

**Not available:** live production traffic logs, session-wide representative sampling, or turn-level speaker-mismatch counters outside artifact/FEM corpora.

---

## Event definitions

### Speaker events

| Event | Definition | Detection signal | BV3D corpus |
|---|---|---|---|
| **Speaker adoption** | Emitted speaker accepted without repair | Turn has FEM + no `speaker_repair` lineage event | Inferred ≥95/95 turns (no repair events) |
| **Speaker mismatch** | Expected vs emitted speaker diverges | Protected replay `selected_speaker_id` drift; scenario `wrong_speaker_strict_social_emission` | Recurrence-only (not turn counter) |
| **Speaker relocation** | Route/target change moves speaker context | `route_kind`, `trace.canonical_entry.target_actor_id` protected fields | Not counted separately in artifact scan |
| **Speaker correction** | Runtime repair applied to speaker attribution | Lineage `event_kind=speaker_repair`; `repair_kind` token | **0 events** in BV3D; 2 events in broader legacy scan (`canonical_rewrite`, `narrator_neutral`) |
| **Speaker override** | Explicit vocative/direct-address override | Protected scenario `vocative_override_after_prior_continuity` | Recurrence key (1 unique historical defect) |
| **Speaker finalize divergence** | Finalize stack vs dialogue-plan speaker mismatch | BX/BT parity probes; `dialogue_plan_subtractive_strip` taxonomy | Not separately instrumented in incidence tools |

### Fallback events

| Event | Definition | Detection signal | BV1 legacy (107 FEM) | BV3D (95 FEM) |
|---|---|---|---:|---:|
| **Opening fallback** | Scene-opening template cash-out | `fallback_kind=scene_opening` | 31 events (42%) | 0 |
| **Visibility fallback** | Referential clarity / visibility replacement | `referential_clarity_hard_replacement`; selection owner visibility module | 38 events (51%) | 1 event (100%) |
| **Sealed fallback** | Sealed passive pressure / sealed-gate bucket | `sealed_passive_scene_pressure_fallback`; `sealed-gate` bucket | 1 event | 0 |
| **Deterministic fallback** | Opening deterministic content owner | `game.opening_deterministic_fallback` content owner | 31 (via scene_opening content) | 0 |
| **Sanitizer-triggered fallback** | Sanitizer empty/strict-social fallback fields | `sanitizer_*` protected paths; sanitizer stage lineage | Sparse in corpus | 0 |
| **Repair-triggered fallback** | Gate terminal repair / prepared emission | `response_type_prepared_emission`; `realization_family=gate_terminal_repair` | 4 + 60 realization | 1 realization |

---

## Speaker Frequency

### Counts

| Population | Metric | Count |
|---|---|---:|
| BV3D artifact FEM turns | Eligible turns | 95 |
| BV3D artifact FEM turns | `speaker_repair` lineage events | **0** |
| Protected replay recurrence | Raw projection-key occurrence_count | **8** |
| Protected replay recurrence | Unique historical speaker defects (BV8A) | **1** |
| Protected replay recurrence | Speaker-family recurrence keys | **3** |
| Owner drift hotspot report | `selected_speaker_source` classifications | **1** |

### Percentages

| Rate | Value | Denominator |
|---|---:|---|
| Speaker repair rate (BV3D runtime artifacts) | **0.00%** | 95 FEM turns |
| Protected replay regression recurrence rate | **50.00%** | 6 recurrence keys (3/6 with count ≥2) |
| Speaker projection key share (forecast) | **47.06%** observation share | Recurrence forecast window |

### Data source

- Runtime artifact: `tools/cb6_speaker_fallback_frequency_probe.py` BV3D rescan via `scan_measurement_fem_turns()` + `summarize_runtime_lineage_events()`
- Recurrence: `artifacts/golden_replay/bug_recurrence_history.json` → `recurrence_forecast.key_forecasts`
- Dedupe authority: [`BV8A_recurrence_audit.md`](BV8A_recurrence_audit.md)

---

## Fallback Frequency

### Counts

| Corpus | Eligible turns | Fallback turns | Fallback events |
|---|---:|---:|---:|
| **BV1 legacy** (wide artifact scan) | 107 | 74 | 74 |
| **BV1B / BV3D** (scoped) | 95 | 1 | 1 |
| **CB6 live rescan** (BV3D) | 95 | 1 | 1 |

### Percentages

| Corpus | Trigger rate | Dominant route (when falling back) |
|---|---:|---|
| BV1 legacy | **69.16%** | `observe` 95.45% (42/44 eligible observe turns) |
| BV3D / BV1B | **1.05%** | `observe` 100% (1/1) |
| BV3D lineage (all turns) | gate_outcome 67.2%, mutation 45.4% of 119 lineage events | Fallback selected: 0.84% of lineage events |

### Fallback family breakdown (BV1 legacy)

| Family | Events | Share of fallback events |
|---|---:|---:|
| Visibility fallback | 38 | 51.4% |
| Opening fallback | 31 | 41.9% |
| Repair-triggered fallback | 4 | 5.4% |
| Sealed fallback | 1 | 1.4% |

### Data source

- `artifacts/bv1_fallback_summary.json`, `artifacts/bv1b_fallback_summary.json`
- `tools/fallback_incidence_report.py` / `build_fallback_incidence_report()`
- CB6 probe rescan: `artifacts/cb6_speaker_fallback_frequency.json`

---

## Replay vs Runtime Comparison

| Dimension | Protected replay recurrence | Observed runtime (BV3D artifacts) |
|---|---|---|
| **Speaker** | 8 inflated recurrence rows; **1** unique `selected_speaker_id` projection defect; speaker_drift highest governance load | **0%** speaker_repair rate; no turn-level mismatch counter |
| **Fallback** | Low-volume fallback_drift / sanitizer keys in recurrence forecast | **1.05%** fallback trigger on scoped corpus |
| **What each measures** | Acceptance failures, drift keys, governance portfolio | Finalized FEM lineage on stored artifact turns |
| **Rate relationship** | Recurrence **≠** incidence — recurrence tracks keyed re-observation of defects | Incidence **scope-dominated** — 69% legacy vs 1% BV3D |

### Protected Replay Rate vs Observed Runtime Rate

| Pathway | Protected replay signal | Runtime artifact signal |
|---|---|---|
| Speaker identity | Recurrence + structural scenarios (`wrong_speaker_*`, `vocative_override_*`) | ~0% repair events on BV3D corpus |
| Fallback | Protected fields (`fallback_family`, sanitizer fields, owner buckets) + recurrence | 1.05% BV3D / 69.16% legacy snapshot |

**Interpretation:** High protected replay attention on speaker drift reflects **acceptance sensitivity and historical defect recurrence**, not proof that speaker mismatch fires on 47% of runtime turns. Fallback incidence is **not stable** across corpora—classification must stay scope-aware.

---

## Confidence Assessment

| Topic | Level | Rationale |
|---|---|---|
| Speaker runtime incidence | **Low** | Zero `speaker_repair` events in 95-turn BV3D corpus; no live traffic sample |
| Fallback runtime incidence | **Medium** | BV1B and CB6 rescan agree on BV3D; legacy 69% shows scope dominates |
| Replay vs runtime separation | **High** | Distinct populations documented; BV8A dedupe clarifies recurrence inflation |
| Owner bucket completeness | **Medium** | 82.4% on legacy fallback events; 100% on BV3D single event |
| Longitudinal fallback trend | **Low** | Two recurrence snapshots; BV5 notes first denominator-bearing longitudinal gap |

---

## Gap analysis

### Unmeasured branches

- Live GM session traffic (non-artifact turns)
- Speaker mismatch branches that **pass** protected replay (silent success path)
- Post-emission adoption mutations without `speaker_repair` lineage stamp
- Sanitizer-triggered fallback on turns without finalized FEM in artifact roots
- Social strict-stack paths outside protected scenario coverage

### Telemetry blind spots

- No turn-level **`speaker_mismatch_detected`** counter in runtime telemetry
- **`speaker_finalize_divergence`** not aggregated in incidence reports
- Broad `artifacts/` scan (394 FEM) vs BV3D filter (95 FEM) produces different rates—filter rationale must accompany any headline number
- Recurrence backfill duplicates (`command` field dedupe gap per BQ36)

### Missing ownership metadata

- 13/74 legacy fallback events lacked owner bucket (BV1)
- `observed_family` populated on **0** events in both corpora
- `diegetic_family` only 1/74 legacy events

### Missing attribution fields

- Response-type fallback family: **0/6** resolved (BV1 attribution matrix)
- Sealed family: **0/5** resolved
- Repair mutation lineage: **0/4** resolved

---

## Readiness impact

### Does measured frequency justify current prohibited classification?

**Yes — prohibited classification remains justified** for:

| Domain | Why evidence supports prohibited (not lower) |
|---|---|
| `speaker_identity_adoption` | Protected `selected_speaker_id` is structural drift; recurrence governance load highest; BX/BT parity work recent; **zero runtime rate does not prove low risk**—acceptance scenarios are sparse vs full route space |
| `fallback_sanitizer_repairs` | Fallback fields are protected observations; legacy 69% shows path can dominate turns when corpus includes observe/opening lanes; coupling FI 103/FO 193 |
| `replay_governance` | Recurrence and incidence are different metrics; replay remains acceptance authority |

### Would any domains move based on evidence?

| Direction | Domain | Verdict |
|---|---|---|
| prohibited → caution | `speaker_identity_adoption` | **No** — recurrence + protected fields + finalize coupling |
| prohibited → caution | `fallback_sanitizer_repairs` | **No** — scope-sensitive incidence + protected observation families |
| prohibited → caution | `final_emission_core` | **No** |
| caution → safe | Any caution domain | **No** — CB6 does not measure caution-domain throughput |

**Nuanced finding:** BV3D **1.05%** fallback rate suggests **representative artifact sessions** may fall back rarely under current scoped corpus—but **cannot** override prohibited status without accepting scope bias (observe-heavy legacy corpus vs filtered BV3D).

---

## Validation

| Check | Result |
|---|---|
| No code-path modifications to emit modules | **PASS** — new read-only probe only |
| No changes to final_emission / fallback / speaker / replay / policy | **PASS** |
| Measurement sources documented | **PASS** |
| Speaker + fallback event definitions explicit | **PASS** |
| Replay vs runtime separated | **PASS** |
| Probe reproducible | **PASS** — `py tools/cb6_speaker_fallback_frequency_probe.py` |

### Commands run

```text
py tools/cb6_speaker_fallback_frequency_probe.py
```

Output: `artifacts/cb6_speaker_fallback_frequency.json`

---

## Recommended CB7 scope

Per CB1 block list: **CB7 — Ownership Drift Watch Refresh**

1. Re-run fan-in/fan-out after BZ/CA changes vs BV1 matrix
2. Align `tests/test_inventory_governance.json` with +19 missing registry files (pre-existing drift noted in CB5)
3. Extend CB6 probe with **longitudinal snapshot delta** when `fallback_incidence_history.json` gains ≥3 scoped snapshots
4. Add optional **speaker mismatch proxy** from protected scenario pass/fail counts (still not runtime traffic)

---

## Cursor Feedback

| Item | Finding |
|---|---|
| **Speaker incidence rate** | **0.00%** speaker_repair on BV3D (95 FEM turns); protected recurrence **8 raw / 1 unique defect** |
| **Fallback incidence rate** | **1.05%** BV3D scoped / **69.16%** BV1 legacy wide corpus |
| **Confidence level** | Speaker runtime **Low**; fallback runtime **Medium**; recurrence separation **High** |
| **Major blind spots** | No live traffic; speaker mismatch success path unmeasured; corpus scope dominates fallback rate; recurrence backfill inflation |
| **Recommended CB7 scope** | Ownership drift watch refresh + governance inventory alignment + longitudinal fallback snapshots |
