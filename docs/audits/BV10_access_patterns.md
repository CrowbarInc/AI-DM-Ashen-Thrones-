# BV10 — Read-Side Attribution Cluster Access Patterns

**Date:** 2026-06-21
**Scope:** Repeated read-side sequences across the 70-FI cluster.

## Pattern summary

| ID | Pattern | Top symbols | Import edges | Consolidation surface |
|---|---|---|---:|---|
| **P1** | FEM sidecar read | `read_final_emission_meta_dict` (17) | 17 | `meta_read` (existing) / gate smoke helper |
| **P2** | Owner-bucket projection | `*_owner_bucket_from_*` (6+5+3) | 10 | `owner_bucket_views` (existing) |
| **P3** | Bucket vocabulary | `SEALED_FALLBACK_OWNER_*`, frozensets | 12 | `ownership_schema` / `attribution_read_views` |
| **P4** | Selection/content owner tokens | `*_SELECTION_OWNER`, `*_CONTENT_OWNER` | 7+ | `ownership_projection_views` |
| **P5** | Observability bundle projection | `normalized_observational_telemetry_bundle`, dead-turn reads | 7 | `observability_attribution_read` |
| **P6** | Replay acceptance normalize | `normalize_final_emission_meta_for_observability`, turn-payload reads | 4 | `replay_attribution_adapter` on replay_projection |
| **P7** | Layer / accept-path projection | `infer_accept_path_final_emitted_source`, `default_response_type_debug` | 4 | meta_read layer surface |
| **P8** | Schema registry parity | `ownership_schema_registry_surface`, lazy imports in owner suite | 3 | owner suite only (no migration) |

---

## P1 — FEM sidecar read

**Sequence:** `read_final_emission_meta_dict(gm_output)` → field assertions or downstream projection.

**Consumers:** gate tests (5), smoke helpers (2), speaker finalize, stage-diff, opening/visibility tests.

**Assessment:** Already on `meta_read`; remaining churn is **fan-in concentration**, not missing facade. Gate tests should route through a single `fem_read_smoke` helper (BV7 pattern).

## P2 — Owner-bucket projection

**Sequence:** read FEM fields → `opening_fallback_owner_bucket_from_meta` / `*_from_fields` → compare to expected bucket token.

**Consumers:** attribution helpers (3), fallback tests (4), replay projection (1), fallback write modules (3).

**Assessment:** Mapper authority correctly on `owner_bucket_views`. Attribution cluster duplicates imports of both views **and** schema bucket constants.

## P3 — Bucket vocabulary (constants-only)

**Sequence:** import `OPENING_*` / `SEALED_*` / `VISIBILITY_*` frozensets or scalar tokens; no mapper call.

**Consumers:** failure classification contract/sync (6 edges), fallback bucket owner suites (5), golden replay fallback projection.

**Assessment:** Lowest-risk consolidation — single `attribution_read_views` re-export removes parallel schema + views imports.

## P4 — Selection/content owner vocabulary

**Sequence:** import allowed `*_SELECTION_OWNER` / `*_CONTENT_OWNER` module-path strings for lineage projection or classifier routing.

**Consumers:** `failure_classification_sync`, `failure_dashboard_fixtures`, `final_emission_replay_projection`, golden replay tests.

**Assessment:** Schema authority is legitimate. Accidental concentration in sync helper (23 schema symbols) warrants **projection facade**, not schema move.

## P5 — Observability bundle projection

**Sequence:** `normalized_observational_telemetry_bundle` / `summarize_gameplay_validation_for_turn` / dead-turn classify reads.

**Consumers:** dead_turn_report_visibility, playability_eval, narrative_authenticity_eval, observational test suite.

**Assessment:** BV2 deferred C3 (`observability_attribution_read`). Still the densest **production read** pattern on meta_read.

## P6 — Replay acceptance normalize

**Sequence:** turn payload → `read_final_emission_meta_from_turn_payload` → normalize → bucket mapper for lineage row.

**Consumers:** `final_emission_replay_projection` (imports all three cluster modules), golden replay tests.

**Assessment:** BV2B adapters exist but replay_projection still triple-imports cluster. Extend adapter surface to absorb internal lazy imports.

## Anti-patterns

| Anti-pattern | Evidence | Remedy |
|---|---|---|
| Triple-import hub | `final_emission_replay_projection` → meta_read + bucket_views + schema | Internal-only imports; export single replay adapter |
| Dual vocabulary import | 6 attribution files import bucket_views constants re-exported from schema | `attribution_read_views` |
| Gate test bypass of smoke facade | 5 gate tests direct-import `read_final_emission_meta_dict` | Consolidate to replay/emission smoke helpers |
| Owner suite sprawl | `test_final_emission_meta.py` imports schema + bucket_views | Permanent — governance exception |

## Evidence

| Source | Path |
|---|---|
| Symbol frequency | `artifacts/bv10_dependency_inventory.json` |
| BV2 access patterns (meta) | `docs/audits/BV2_meta_access_patterns.md` |
| BV2B replay adapters | `docs/audits/BV2B_replay_attribution_migration.md` |
