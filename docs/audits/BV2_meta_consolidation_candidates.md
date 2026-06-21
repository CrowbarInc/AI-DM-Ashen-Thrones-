# BV2 — `final_emission_meta` Consolidation Candidates

**Date:** 2026-06-21  
**Goal:** Reduce `final_emission_meta` fan-in without changing runtime behavior.  
**Baseline:** FI **61**, FO **6** (BU scan 2026-06-21).

---

## Candidate overview

| ID | Target surface | Est. FI reduction | Est. FO change (meta) | Ownership impact | Risk |
|---|---|---:|---|---|---|
| **C1** | Owner-bucket views | **−14** | 0 | Bucket constants canonical on `ownership_schema`; mappers co-owned with replay | **Low** |
| **C2** | FEM read-access facade | **−16** | 0 | Meta retains write ownership; read facade owned by meta (re-export) | **Low** |
| **C3** | Observability read module | **−8** | +1 (new module) | Diagnostics read-only; telemetry_vocab stays downstream | **Low** |
| **C4** | Replay acceptance adapter | **−3** | −1 (drop lineage re-export from meta) | Strengthens AO5 replay boundary | **Medium** |
| **C5** | Producer-kind constants only | **−2** | 0 | `output_sanitizer` → schema | **Low** |
| **C6** | Smoke facade hardening | **0** (direct FI) | 0 | Prevents future meta fan-in from 34 indirect consumers | **Low** |

**Combined projected FI (if all executed):** 61 → **~18–22** (−39 to −43, **64–70% reduction**).  
**Conservative phased target (C1+C2+C3):** 61 → **~29** (−32, **52% reduction**).

---

## C1 — Owner-bucket read views

**Problem:** 22 importers use P2 owner-bucket pattern via meta re-exports of `ownership_schema` constants + mapper functions.

**Proposal:** Add `game/final_emission_owner_bucket_views.py` (or extend `ownership_schema` with read mappers moved from meta):

- `opening_fallback_owner_bucket_from_meta`
- `opening_fallback_owner_bucket_from_fields`
- `visibility_fallback_owner_bucket_from_fields`
- `sealed_fallback_owner_bucket_from_fields`
- Re-export bucket constant frozensets from schema (no meta hop)

**Migrate importers:**

| Group | Files | Est. count |
|---|---|---:|
| Test bucket suites | `test_opening_fallback_owner_bucket`, `test_*_fallback*`, `test_gm_retry` | 8 |
| Helpers | `golden_replay_projection` (constants only), `opening_fallback_evidence`, `failure_classifier`, `replacement_attribution_inventory` | 4 |
| Production read | `final_emission_replay_projection` (lazy mapper) | 1 |
| Constants-only | Various tests importing `OPENING_FALLBACK_OWNER_*` | 1 |

**Est. FI reduction:** **−14**  
**Est. FO change:** Meta FO unchanged; new module FO ≈ 2 (schema + typing)  
**Ownership impact:** Aligns with BK — schema owns vocabulary, views own read mapping, meta owns write stamps  
**Risk:** **Low** — pure read relocation; parity tests in `test_opening_fallback_owner_bucket.py` lock behavior

---

## C2 — FEM read-access facade

**Problem:** 23 importers use P1 sidecar read (`read_final_emission_meta_dict`, `read_*_from_turn_payload`, `read_debug_notes`).

**Proposal:** Extract to `game/final_emission_meta_read.py`:

```python
# Narrow immutable read API (delegates to meta internals initially)
read_fem_dict(gm_output) -> Mapping
read_fem_from_turn_payload(payload) -> Mapping
read_emission_debug_lane(gm_output) -> Mapping
read_debug_notes_from_turn_payload(payload) -> str
```

Meta **re-exports** for backward compatibility during migration; registry marks direct meta read as deprecated in non-owner tests.

**Migrate importers:**

| Group | Files | Est. count |
|---|---|---:|
| Gate tests | diagnostics, orchestration_order, n4, selector_snapshots, channel_separation | 5 |
| Smoke/helper | `emission_smoke_assertions`, `behavioral_gauntlet_eval` | 2 |
| Production read-only | `post_emission_speaker_adoption`, `stage_diff_telemetry`, `gm_retry` (read half) | 3 |
| Replay/diagnostics tests | golden_replay_direct_seam, dead_turn_*, transcript_gauntlet, tone_escalation, run_scenario_spine | 6 |

**Est. FI reduction:** **−16**  
**Est. FO change:** Meta FO +1 (imports read submodule) → net meta complexity split, FI down  
**Ownership impact:** `test_final_emission_meta.py` remains direct meta owner; facade for downstream  
**Risk:** **Low** — delegate-only extraction; no logic change

---

## C3 — Observability read module

**Problem:** 9 importers share P3 normalize/bundle chain on meta.

**Proposal:** `game/final_emission_observability_read.py`:

- `normalize_final_emission_meta_for_observability`
- `build_fem_observability_events`
- `normalized_observational_telemetry_bundle`
- `assemble_unified_observational_telemetry_bundle`
- `classify_dead_turn`, `read_dead_turn_from_gm_output`, `summarize_gameplay_validation_for_turn`
- `stage_diff_narrative_authenticity_projection`

**Migrate:** `narrative_authenticity_eval`, `playability_eval`, `dead_turn_report_visibility`, `test_observational_telemetry_confidence`, `test_dead_turn_*`, partial `stage_diff_telemetry`.

**Est. FI reduction:** **−8** (overlap with C2 for stage_diff — net counted in combined projection)  
**Est. FO change:** New module FO ≈ 3 (telemetry_vocab, stage_diff, meta read delegate)  
**Ownership impact:** Clear diagnostics read owner; meta keeps write packaging of dead-turn **into** FEM  
**Risk:** **Low** — read-only projection move

---

## C4 — Replay acceptance adapter

**Problem:** `golden_replay_projection` imports 12 meta symbols including normalize + bucket mappers — blurs AO5 acceptance vs runtime lineage boundary.

**Proposal:** Add to `game/final_emission_replay_projection.py`:

- `normalize_fem_for_replay_acceptance(fem)` — wraps observability normalize or thin subset
- `read_owner_buckets_for_replay(meta)` — wraps C1 views
- `read_fem_from_turn_for_replay(payload)` — wraps C2 read facade

Golden replay helper imports **replay_projection + views**, not meta.

**Est. FI reduction:** **−3** (direct); prevents helper fan-in growth  
**Est. FO change:** Meta **−1** (remove `build_fem_runtime_lineage_events` re-export at L1999)  
**Ownership impact:** Reinforces replay projection as read-side owner for acceptance  
**Risk:** **Medium** — golden replay protected paths; requires full `-m golden_replay` pass

---

## C5 — Producer-kind constants migration

**Problem:** `output_sanitizer.py` imports `PRODUCER_REPAIR_KIND_*` from meta for stamp vocabulary.

**Proposal:** Move producer-kind string constants to `ownership_schema` (alongside owner buckets); meta imports from schema.

**Est. FI reduction:** **−1** direct + prevents future constant-only imports  
**Risk:** **Low**

---

## C6 — Smoke facade hardening (preventive)

**Problem:** 34 tests use `final_emission_meta_from_output` — correct pattern — but AS4 notes stragglers still call `read_final_emission_meta_dict` directly.

**Proposal:** Registry rule (ownership_registry): non-owner tests **must** use smoke facade or C2 read module; no new direct meta imports.

**Est. FI reduction:** **0** immediate; blocks FI regression  
**Risk:** **Low**

---

## Candidates explicitly deferred (write owners)

These **must remain** on `final_emission_meta` after consolidation:

| Module cluster | Reason |
|---|---|
| visibility / sealed / opening fallback (production) | Write stamps + projection apply |
| finalize / terminal_pipeline / strict_social_stack / generic_exit | FEM packaging owners |
| fem_assembly / repairs / acceptance_quality / NMO / preflight | Layer merge write owners |
| fallback_provenance_debug | Debug patch write |
| `test_final_emission_meta.py` | Canonical owner suite |

**Remaining meta FI after full plan:** ~18–22 (production write owners + owner test suite + registry).

---

## Combined projection matrix

| Metric | Current | After C1+C2+C3 | After all (C1–C5) |
|---|---:|---:|---:|
| `final_emission_meta` FI | 61 | **~29** | **~18–22** |
| Production FI | 27 | **~22** | **~20** |
| Test/helper FI | 34 | **~7** | **~2–3** |
| Meta FO | 6 | 6–7 | **5** |
| New module count | 0 | +2–3 | +3 |

---

## Evidence

| Source | Path |
|---|---|
| Access patterns | [BV2_meta_access_patterns.md](BV2_meta_access_patterns.md) |
| Consumer groups | [BV2_meta_consumer_classification.md](BV2_meta_consumer_classification.md) |
| BV2 follow-on | [BV_follow_on_candidates.md](BV_follow_on_candidates.md) § BV2 |
