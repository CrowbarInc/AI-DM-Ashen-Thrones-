# BU4 — Ownership Write-Path Registry

Date: 2026-06-20

## Executive summary

BU4 enumerates **94** deduplicated production write-path rows across **29** `game/` modules and **56** functions. Owner buckets, fallback families, authorship sources, split-owner lineage fields, and replay-visible lineage projection are still authored through multiple surfaces, but `game.final_emission_meta` now holds the canonical owner-bucket vocabulary (Cycle BK1) and `game.final_emission_replay_projection` owns read-side lineage projection (Cycle AO5).

No runtime behavior was changed in BU4. This block is discovery + registry only.

## Method

`scripts/bu4_ownership_write_path_discovery.py` parses `game/` and `tests/` with AST plus a field-name assignment regex. Rows are deduplicated per `(file, function, field)`. Writer classification is heuristic (module + function); see CSV for per-row detail.

Machine-readable inventory: `docs/audits/BU4_ownership_write_paths.csv`.

## Production writer counts by class

| Writer class | Rows | Modules |
|---|---:|---:|
| FEM schema writer | 30 | 11 |
| debug-only writer | 25 | 9 |
| fallback selection writer | 25 | 9 |
| replay projection writer | 13 | 3 |
| speaker contract writer | 1 | 1 |

## Production modules with ownership writes

- `game/api.py` — 2 row(s): `realization_fallback_family`
- `game/diegetic_fallback_narration.py` — 1 row(s): `fallback_family_used`
- `game/fallback_provenance_debug.py` — 3 row(s): `fallback_family`, `fallback_provenance_trace`
- `game/final_emission_acceptance_quality.py` — 1 row(s): `fallback_family`
- `game/final_emission_fem_assembly.py` — 5 row(s): `fallback_family_used`, `fallback_temporal_frame`, `realization_fallback_family`, `speaker_contract_enforcement_reason`
- `game/final_emission_generic_exit.py` — 3 row(s): `fallback_family_used`, `fallback_temporal_frame`, `producer_repair_kind`
- `game/final_emission_meta.py` — 8 row(s): `fem_runtime_lineage_events`, `opening_fallback_owner_bucket`, `owner_bucket`, `sealed_fallback_owner_bucket`, `visibility_fallback_owner_bucket`
- `game/final_emission_meta_observability.py` — 1 row(s): `fem_runtime_lineage_events`
- `game/final_emission_narration_constraint_debug.py` — 1 row(s): `speaker_contract_enforcement`
- `game/final_emission_opening_fallback.py` — 6 row(s): `fallback_family_used`, `fallback_temporal_frame`, `opening_fallback_authorship_source`
- `game/final_emission_owner_bucket_views.py` — 3 row(s): `fallback_family`, `fallback_temporal_frame`, `opening_fallback_authorship_source`
- `game/final_emission_replay_projection.py` — 4 row(s): `fallback_authorship_source`, `fallback_content_owner`, `fallback_owner_bucket`, `fallback_selection_owner`
- `game/final_emission_response_type.py` — 5 row(s): `fallback_family_used`, `fallback_temporal_frame`, `opening_fallback_authorship_source`, `opening_fallback_owner_bucket`, `realization_fallback_family`
- `game/final_emission_sealed_fallback.py` — 6 row(s): `fallback_family`, `fallback_family_used`, `fallback_temporal_frame`, `realization_fallback_family`, `sealed_fallback_owner_bucket`
- `game/final_emission_strict_social_stack.py` — 2 row(s): `speaker_contract_enforcement`, `speaker_contract_enforcement_reason`
- `game/final_emission_terminal_pipeline.py` — 2 row(s): `fallback_family`, `speaker_contract_enforcement`
- `game/final_emission_validators.py` — 6 row(s): `fallback_family_used`, `fallback_temporal_frame`, `opening_fallback_authorship_source`, `opening_fallback_owner_bucket`, `realization_fallback_family`, `sealed_fallback_owner_bucket`
- `game/final_emission_visibility_fallback.py` — 1 row(s): `visibility_fallback_owner_bucket`
- `game/final_emission_visibility_metadata.py` — 3 row(s): `fallback_owner_bucket`, `visibility_fallback_owner_bucket`
- `game/gm.py` — 1 row(s): `realization_fallback_family`
- `game/gm_retry.py` — 1 row(s): `realization_fallback_family`
- `game/interaction_continuity.py` — 1 row(s): `speaker_contract_enforcement`
- `game/output_sanitizer.py` — 5 row(s): `fallback_family`, `owner_bucket`, `sanitizer_empty_fallback_owner_trace_short`, `sanitizer_strict_social_prose_owner_trace_short`, `sanitizer_strict_social_selection_owner_trace_short`
- `game/output_sanitizer_lineage.py` — 6 row(s): `owner_bucket`, `sanitizer_empty_fallback_owner`, `sanitizer_strict_social_prose_owner`, `sanitizer_strict_social_selection_owner`, `sealed_fallback_owner_bucket`
- `game/realization_provenance.py` — 1 row(s): `realization_fallback_family`
- `game/runtime_lineage_telemetry.py` — 8 row(s): `fallback_authorship_source`, `fallback_content_owner`, `fallback_owner_bucket`, `fallback_selection_owner`
- `game/social_exchange_emission.py` — 2 row(s): `realization_fallback_family`
- `game/speaker_contract_enforcement.py` — 1 row(s): `speaker_contract_enforcement`
- `game/upstream_response_repairs.py` — 5 row(s): `fallback_family_used`, `fallback_temporal_frame`, `opening_fallback_authorship_source`, `opening_fallback_owner_bucket`, `realization_fallback_family`

## Production writer counts by field

| Field | Writers (deduped rows) |
|---|---:|
| `realization_fallback_family` | 12 |
| `fallback_family_used` | 8 |
| `fallback_temporal_frame` | 8 |
| `opening_fallback_authorship_source` | 8 |
| `fallback_family` | 7 |
| `opening_fallback_owner_bucket` | 6 |
| `sealed_fallback_owner_bucket` | 6 |
| `fallback_owner_bucket` | 5 |
| `speaker_contract_enforcement` | 5 |
| `owner_bucket` | 4 |
| `fallback_authorship_source` | 3 |
| `fallback_content_owner` | 3 |
| `fallback_selection_owner` | 3 |
| `speaker_contract_enforcement_reason` | 3 |
| `visibility_fallback_owner_bucket` | 3 |
| `fem_runtime_lineage_events` | 2 |
| `fallback_provenance_trace` | 1 |
| `producer_repair_kind` | 1 |
| `sanitizer_empty_fallback_owner` | 1 |
| `sanitizer_empty_fallback_owner_trace_short` | 1 |
| `sanitizer_strict_social_prose_owner` | 1 |
| `sanitizer_strict_social_prose_owner_trace_short` | 1 |
| `sanitizer_strict_social_selection_owner` | 1 |
| `sanitizer_strict_social_selection_owner_trace_short` | 1 |

## Schema vocabulary surfaces (read/consume, not necessarily write)

| Surface | Role |
|---|---|
| `game.final_emission_meta` | Owner-bucket constants, stamp helpers, opening projection field registry, sanitizer→FEM copy |
| `game.final_emission_replay_projection` | `build_fem_runtime_lineage_events`, split-owner maps, fallback_kind taxonomy |
| `game.runtime_lineage_telemetry` | Lineage event dict schema (`make_runtime_lineage_event`) |
| `game.realization_provenance` | `realization_fallback_family` stamp normalizer |
| `game.realization_authority` | Governed family token constants |
| `game.diegetic_fallback_narration` | Diegetic `fallback_family_used` template taxonomy |
| `tests/helpers/attribution_contract.py` | BS semantic-replacement attribution vocabulary (read-side inventory) |
| `tests/helpers/replacement_attribution_inventory.py` | Cross-source attribution record builder (read-side) |

## Top schema drift risks

- **Dual fallback-family vocabularies** — `fallback_family_used` (diegetic) vs `realization_fallback_family` (governed) are stamped by different modules (`diegetic_fallback_narration`, `realization_provenance`, route owners). Golden replay projects diegetic-first; lineage uses path-specific `fallback_kind`.
- **Split-owner literals outside replay projection** — `output_sanitizer` stamps `sanitizer_strict_social_selection_owner="output_sanitizer"` and `sanitizer_strict_social_prose_owner="strict_social_emission"` as short names; `final_emission_replay_projection` maps these to canonical `game.*` module owners.
- **Owner-bucket assignment is distributed** — Opening buckets via `stamp_opening_fallback_owner_bucket` (read-side mapper), sealed via `stamp_sealed_fallback_realization_family`, visibility via `stamp_visibility_fallback_metadata` — constants live in `final_emission_meta` but write paths remain per-route.
- **Compatibility-local authorship residue** — `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES` in `final_emission_meta` maps retired tokens to `unknown-ambiguous`; never written in production but still in read-side mapper.
- **emission_debug vs FEM lane duplication** — Speaker contract, response-type debug, and layer merges write `metadata.emission_debug` keys that are later copied or projected into FEM / lineage — two packaging surfaces for same semantics.
- **Scattered bucket string literals** — 16 literal bucket hits outside primary registry modules (see drift table below).

## Scattered bucket literals (outside registry modules)

| File | Line | Literal |
|---|---:|---|
| `game/final_emission_finalize.py` | 178 | `retry` |
| `game/final_emission_ownership_schema.py` | 37 | `upstream-prepared` |
| `game/final_emission_ownership_schema.py` | 38 | `sealed-gate` |
| `game/final_emission_ownership_schema.py` | 39 | `retry` |
| `game/final_emission_ownership_schema.py` | 40 | `strict-social` |
| `game/final_emission_ownership_schema.py` | 41 | `unknown-ambiguous` |
| `game/final_emission_ownership_schema.py` | 53 | `sealed-gate` |
| `game/final_emission_ownership_schema.py` | 54 | `strict-social-sealed` |
| `game/final_emission_ownership_schema.py` | 55 | `unknown-none` |
| `game/final_emission_ownership_schema.py` | 56 | `unknown-ambiguous` |
| `game/final_emission_ownership_schema.py` | 67 | `sealed-gate` |
| `game/final_emission_ownership_schema.py` | 68 | `strict-social-visibility` |
| `game/final_emission_ownership_schema.py` | 69 | `opening-visibility` |
| `game/final_emission_ownership_schema.py` | 70 | `unknown-none` |
| `game/final_emission_ownership_schema.py` | 71 | `unknown-ambiguous` |
| `game/runtime_lineage_telemetry.py` | 63 | `retry` |

## Recommended BU5 block

1. **Narrow ownership schema module** — export owner-bucket constants + split-owner module tokens from one import surface (re-home from `final_emission_meta` / `replay_projection` without behavior change).
2. **Unify sanitizer trace owner literals** — replace short names with canonical `game.*` owners at write time (or single normalizer used by sanitizer + replay projection).
3. **Producer stamp convergence** — ensure every fallback selection path calls one of `stamp_opening_fallback_owner_bucket`, `stamp_sealed_fallback_realization_family`, `stamp_visibility_fallback_metadata` / `stamp_visibility_fallback_owner_bucket_from_fields` before FEM finalize (audit shows gaps on retry/API-only `attach_realization_fallback_family` paths).
4. **Governance lock** — extend `tests/test_ownership_registry.py` with BU4 write-path parity test mirroring CSV inventory (similar to BN lazy-import guards).

## Test / governance writers (summary)

Deduplicated test/helper rows: **279** across 42 files. Primary surfaces: `tests/helpers/replacement_attribution_inventory.py`, `tests/helpers/opening_fallback_evidence.py`, `tests/failure_classification_contract.py`, golden replay fixtures.
