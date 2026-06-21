# BV10 — Read-Side Attribution Cluster Consolidation Candidates

**Date:** 2026-06-21
**Goal:** Reduce combined cluster fan-in (70) without changing ownership authority or replay behavior.
**Baseline:** meta_read FI 29 + bucket_views FI 22 + ownership_schema FI 19.

## Candidate overview

| ID | Target surface | Est. combined FI Δ | Migration cost | Replay risk |
|---|---|---:|---|---|
| **C1** | `attribution_read_views` | **−12 to −15** | Low | **Low** |
| **C2** | `ownership_projection_views` | **−6 to −8** | Low | **Low** |
| **C3** | `replay_attribution_adapter` (extend replay_projection) | **−8 to −10** | Medium | **Medium** |
| **C4** | `observability_attribution_read` | **−7 to −9** | Low | **Low** |
| **C5** | Gate/smoke read helper hardening | **−6 to −8** | Low | **Low** |

**Conservative phased combined FI:** 70 → **~34–38** (phase 2) → **~26–30** (phase 3).

---

## C1 — `attribution_read_views`

**Problem:** 11 attribution import edges split across `owner_bucket_views` and `ownership_schema`; 6 files import both.

**Proposal:** Add `game/attribution_read_views.py` (read-only re-exports):

- Bucket mappers: all four `*_owner_bucket_from_*`
- Vocabulary: bucket frozensets + `ALLOWED_*_OWNERS` + selection/content owner tokens used by classifier/sync
- No write stamps, no mapper logic changes

**Migrate:** `failure_classification_contract`, `failure_classification_sync`, `failure_classifier`, `failure_dashboard_fixtures`, `replacement_attribution_inventory`, related tests.

**Est. FI reduction:** bucket_views −6, schema −5, new module +4 → **net −7 to −9** on combined sum; **−12 to −15** import edges removed from cluster modules.

---

## C2 — `ownership_projection_views`

**Problem:** Schema selection/content tokens imported piecemeal by replay lineage and sanitizer trace normalization.

**Proposal:** Thin module wrapping `ownership_schema` tokens needed for **read-side projection** (not write stamps):

- `lineage_owner_vocabulary()` registry surface
- `sanitizer_trace_owner_vocabulary()`
- Delegates only; schema remains authority

**Migrate:** `runtime_lineage_telemetry`, `output_sanitizer` read constants, replay_projection internal reads.

**Est. FI reduction:** schema −4 to −5, new module +2 → **net −6 to −8**.

---

## C3 — `replay_attribution_adapter`

**Problem:** `final_emission_replay_projection` is a triple-import hub; golden replay tests still reach cluster modules directly.

**Proposal:** Extend BV2B adapters on `final_emission_replay_projection`:

- `read_attribution_vocabulary_for_replay()`
- `project_owner_buckets_for_replay(meta)`
- Hide lazy imports of meta_read / bucket_views / schema inside replay owner

**Migrate:** golden replay fallback/projection tests, runtime_lineage test fixtures.

**Est. FI reduction:** −3 per cluster module on replay consumers → **−8 to −10** combined.
**Replay risk:** **Medium** — requires protected replay manifest parity check (BV3F pattern).

---

## C4 — `observability_attribution_read`

**Problem:** Seven meta_read import edges use observability bundle / dead-turn projection (BV2 C3 deferred).

**Proposal:** Add `game/observability_attribution_read.py` delegating to meta_read:

- `normalized_observational_telemetry_bundle`
- `summarize_gameplay_validation_for_turn`
- `classify_dead_turn` / `read_dead_turn_from_gm_output`
- `assemble_unified_observational_telemetry_bundle`

**Migrate:** dead_turn_report_visibility, playability_eval, narrative_authenticity_eval, stage_diff_telemetry (NA projection half), observability tests.

**Est. FI reduction:** meta_read −7, new module +2 → **net −7 to −9**.

---

## C5 — Gate / smoke read helper hardening

**Problem:** 14 meta_read import edges on gate tests and smoke helpers duplicate `read_final_emission_meta_dict`.

**Proposal:** Extend `tests/helpers/emission_smoke_assertions` + `replay_smoke_assertions` with attribution-aware read helpers; gate tests import helpers only.

**Est. FI reduction:** meta_read −6 to −8.

---

## Intentionally excluded

| Surface | Reason |
|---|---|
| `game/final_emission_meta.py` | Write owner — re-imports views for packaging |
| `tests/test_final_emission_meta.py` | FEM owner suite — permanent direct schema/views |
| Fallback write modules (visibility/sealed) | Write-time bucket stamp authority |
| `ownership_schema` constant definitions | Canonical vocabulary authority |
