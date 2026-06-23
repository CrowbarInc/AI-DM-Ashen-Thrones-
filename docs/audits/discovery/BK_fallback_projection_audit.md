# BK — Fallback Projection Audit

**Cycle:** BK — Discovery / Audit  
**Date:** 2026-06-16  

---

## Projection modules inventory

| Module | Layer | ~LOC | Owns fallback decisions? | Owns fallback content? |
|--------|-------|------|--------------------------|------------------------|
| `game/final_emission_meta.py` | Write/read FEM packaging | 1776 | **Partial** — owner-bucket mapping, projection field registry | No |
| `game/final_emission_replay_projection.py` | Runtime lineage (read-side) | 595 | **Partial** — lineage kind/sub-kind refinement | No |
| `tests/helpers/golden_replay_projection.py` | Acceptance observation (test-only) | 1377 | **Partial** — diegetic-first `fallback_family` precedence | No |
| `game/fallback_provenance_debug.py` | Provenance trace packaging | 293 | No — fingerprints and attaches trace | No |
| `game/realization_provenance.py` | Governed family stamp | — | No — normalizes family enum | No |
| `game/final_emission_opening_fallback.py` | Opening result meta factory | 372 | **Partial** — fail-closed meta defaults | No prose |
| `game/final_emission_visibility_fallback.py` | Visibility route metadata | 1627 | **Yes** — routing metadata payloads | No (claims routing-only) |
| `game/final_emission_sealed_fallback.py` | Sealed route meta | 412 | **Partial** — sealed owner bucket stamp | No |
| `game/response_policy_enforcement.py` | Policy debug projection | — | No | No |
| `game/final_emission_repairs.py` | Repair meta merge | 1123 | No — records repair outcomes | No |
| `game/stage_diff_telemetry.py` | Stage snapshots | — | No | No |
| `tests/helpers/opening_fallback_evidence.py` | Test FEM slices | 207 | No — fixture builders | Test literals only |
| `tests/helpers/failure_classification_sync.py` | Classifier bridge | — | No | No |

---

## Classification: decision vs render

### A. Projections that contain fallback **business decisions**

| Location | Decision type | Evidence |
|----------|---------------|----------|
| `final_emission_meta.opening_fallback_owner_bucket_from_fields` | Maps authorship/source → owner bucket | Read-side bucket assignment rules |
| `final_emission_meta.opening_fallback_owner_bucket_from_meta` | Bucket from FEM meta | Used by replay + classifier |
| `final_emission_visibility_fallback.classify_visibility_fallback_owner_bucket` | Visibility bucket classification | Parallel to opening/sealed mappers |
| `final_emission_sealed_fallback` (bucket stamp helpers) | Sealed bucket assignment | `SEALED_FALLBACK_OWNER_*` constants |
| `golden_replay_projection.project_replay_fallback_family_from_fem` | Diegetic-first family precedence | Documented read-side compatibility rule |
| `final_emission_replay_projection` sealed sub-kind mapping | Refines `sealed_or_global_replacement` → sub-kinds | `SEALED_REPLACEMENT_SUBKIND_*` |
| `final_emission_replay_projection` split-owner constants | Selection vs content owner on lineage events | `OPENING_FALLBACK_*_OWNER`, sanitizer/upstream constants |

**Finding:** Owner-bucket and family-precedence **decisions are split across three projection domains** (meta, visibility, replay) rather than centralized.

---

### B. Projections that **merely render** stamped data

| Location | Behavior |
|----------|----------|
| `final_emission_meta.apply_opening_fallback_projection_fields` | Copies `OPENING_FALLBACK_PROJECTION_FIELDS` keys only |
| `final_emission_meta.opening_fallback_projection_fields` | Field list filter |
| `final_emission_replay_projection.build_fem_runtime_lineage_events` | Derives events from finalized FEM (no text selection) |
| `golden_replay_projection.project_turn_observation` | Flattens payload → observed dict via registered extractors |
| `golden_replay_projection._FlatObservedFieldExtractor` | 1:1 key projection |
| `fallback_provenance_debug.record_final_emission_gate_exit` | Packages existing trace onto FEM |
| `realization_provenance.attach_realization_fallback_family` | Stamps provided family constant |

---

### C. Projections that **own fallback content** (should be none in projection layer)

| Location | Violation? | Notes |
|----------|------------|-------|
| `opening_fallback_evidence.EXPECTED_FRONTIER_GATE_OPENING_FALLBACK` | Test-only | Literal prose for golden scenarios — acceptable test fixture |
| `golden_replay_projection` | No | No prose authoring |
| `final_emission_meta` | No | No prose authoring |
| `final_emission_replay_projection` | No | No prose authoring |

**No runtime projection module authors player-facing fallback prose.** Content stays in `diegetic_fallback_narration`, `opening_deterministic_fallback`, `social_exchange_emission`, `gm_retry`.

---

## Dual projection boundary (AO5)

Documented split — **must not merge**:

| Concern | `final_emission_replay_projection` | `golden_replay_projection` |
|---------|-----------------------------------|---------------------------|
| Authority | Runtime diagnostic lineage | CI acceptance observation |
| Key output | `fem_runtime_lineage_events` | `project_turn_observation` |
| Fallback family | Preserves both FEM fields on lineage | Collapses to observed `fallback_family` |
| Owner semantics | `owner` = selector; split fields for content | Protected paths for buckets/authorship |
| Drift classification | Excluded from protected drift (diagnostic) | Included (41 protected paths) |

Cycle BL simplified `golden_replay_projection` without merging modules — **positive precedent** for BK.

---

## Projection-owned metadata registries

| Registry | Owner module | Field count (fallback-related) |
|----------|--------------|-------------------------------|
| `OPENING_FALLBACK_PROJECTION_FIELDS` | `final_emission_meta` | 14+ keys |
| `OPENING_FALLBACK_RESULT_META_FIELDS` | `final_emission_meta` | 13 keys (subset) |
| `PROTECTED_OBSERVATION_FIELDS` | `golden_replay_projection` | 41 total paths |
| `REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS` | `golden_replay_projection` | 2 keys |
| `RUNTIME_LINEAGE_FALLBACK_ATTRIBUTION_FIELDS` | `runtime_lineage_telemetry` | attribution vocabulary |
| `FEM_FALLBACK_PROVENANCE_TRACE_KEY` | `final_emission_meta` | trace key name |

**Seam:** Adding one opening metadata field touches **meta registry + opening_fallback builder + golden protected manifest + possibly classifier allowlist**.

---

## Business decisions in projection files (highlight)

These files currently own **policy** beyond pure render:

1. **`game/final_emission_meta.py`** — opening owner-bucket mapper; mutation lineage token assembly; opening projection field coercion (bool/int normalization).

2. **`game/final_emission_visibility_fallback.py`** — `classify_visibility_fallback_owner_bucket`; `stamp_visibility_fallback_metadata`; first-mention fallback strategy fields on metadata payloads.

3. **`game/final_emission_replay_projection.py`** — sealed replacement sub-kind refinement; upstream/sanitizer/opening split-owner projection rules.

4. **`tests/helpers/golden_replay_projection.py`** — diegetic-first `fallback_family` precedence; protected field requiredness; drift bucket assignment per path.

---

## Render-only projection helpers (safe compression surface)

These are **low-risk** consolidation targets because they copy or flatten without semantic choice:

- `apply_opening_fallback_projection_fields`
- `_FlatObservedFieldExtractor` family
- `build_fem_runtime_lineage_events` (given finalized FEM)
- `normalize_final_emission_meta_for_observability`
- `fallback_provenance_debug` fingerprint helpers

---

## Recommendations (audit-only)

| Priority | Target | Rationale |
|----------|--------|-----------|
| High | Consolidate owner-bucket mappers into `final_emission_meta` | Three parallel classifiers today |
| Medium | Keep AO5 boundary; continue simplifying `golden_replay_projection` extractors | BL model |
| Low | Move sealed sub-kind constants next to sealed owner | Locality with `final_emission_sealed_fallback` |
