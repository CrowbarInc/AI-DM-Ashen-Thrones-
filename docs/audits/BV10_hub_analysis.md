# BV10 — Read-Side Attribution Cluster Hub Analysis

**Date:** 2026-06-21
**Question:** Which concentration points are legitimate ownership authority vs accidental read hubs?

## Module-level classification

| Module | FI | Hub type | Verdict |
|---|---:|---|---|
| `game.final_emission_ownership_schema` | 19 | **authority** | Canonical bucket strings + selection/content owner tokens. Keep as vocabulary owner. |
| `game.final_emission_owner_bucket_views` | 22 | **projection** | Read-only bucket mappers + schema re-exports. Legitimate facade; FI inflated by attribution/test duplication. |
| `game.final_emission_meta_read` | 29 | **facade** | BV2 read delegate to meta write owner. Legitimate; FI inflated by deferred observability + gate test reads. |
| `game.final_emission_replay_projection` | 15 (adjacent) | **accidental hub** | Imports all three cluster modules — should absorb reads internally. |

---

## File-level concentration (multi-import)

**16 files** import two or three cluster modules:

| File | Modules imported | Hub type | Action |
|---|---|---|---|
| `game/final_emission_meta.py` | `owner_bucket_views`, `ownership_schema` | authority | Keep — write owner re-exports |
| `game/final_emission_replay_projection.py` | `final_emission_meta_read`, `owner_bucket_views`, `ownership_schema` | accidental hub | C3 — internalize via replay adapter |
| `game/final_emission_sealed_fallback.py` | `owner_bucket_views`, `ownership_schema` | accidental hub | Consolidate to domain facade |
| `game/final_emission_visibility_fallback.py` | `owner_bucket_views`, `ownership_schema` | accidental hub | Consolidate to domain facade |
| `tests/failure_classification_contract.py` | `owner_bucket_views`, `ownership_schema` | accidental hub | Consolidate to domain facade |
| `tests/helpers/failure_classification_sync.py` | `owner_bucket_views`, `ownership_schema` | accidental hub | C1 — attribution_read_views |
| `tests/helpers/failure_dashboard_fixtures.py` | `owner_bucket_views`, `ownership_schema` | accidental hub | Consolidate to domain facade |
| `tests/test_failure_classification_contract.py` | `owner_bucket_views`, `ownership_schema` | accidental hub | Consolidate to domain facade |
| `tests/test_failure_classifier.py` | `owner_bucket_views`, `ownership_schema` | accidental hub | Consolidate to domain facade |
| `tests/test_final_emission_gate_selector_snapshots.py` | `final_emission_meta_read`, `owner_bucket_views` | accidental hub | Consolidate to domain facade |
| `tests/test_final_emission_meta.py` | `owner_bucket_views`, `ownership_schema` | authority | Owner suite exception |
| `tests/test_final_emission_opening_fallback.py` | `final_emission_meta_read`, `owner_bucket_views` | accidental hub | Consolidate to domain facade |
| `tests/test_final_emission_visibility.py` | `final_emission_meta_read`, `owner_bucket_views` | accidental hub | Consolidate to domain facade |
| `tests/test_golden_replay_fallback_projection.py` | `owner_bucket_views`, `ownership_schema` | accidental hub | Consolidate to domain facade |
| `tests/test_opening_fallback_owner_bucket.py` | `final_emission_meta_read`, `owner_bucket_views` | facade | C1 partial — bucket owner suite may stay direct |
| `tests/test_runtime_lineage_telemetry.py` | `owner_bucket_views`, `ownership_schema` | accidental hub | Consolidate to domain facade |

---

## Legitimate ownership authority (do not migrate away)

| Authority | Owner module | Consumers that must stay direct |
|---|---|---|
| Bucket string definitions | `ownership_schema` | meta write owner, owner suites |
| Bucket mapper implementations | `owner_bucket_views` | fallback write modules (read bucket for stamp validation) |
| FEM read delegate | `meta_read` | meta write owner (internal) |
| Replay lineage packaging | `final_emission_replay_projection` | golden replay helper (already via replay_projection) |

## Accidental read concentration (migrate)

| Hub | FI contribution | Root cause |
|---|---|---|
| Attribution sync/classifier chain | 12+ edges | Parallel schema + views imports for same vocabulary |
| Gate test cluster | 8 meta_read edges | Bypass smoke facade after BV2 migration |
| Observability eval chain | 7 meta_read edges | BV2 C3 observability module never extracted |
| Replay projection internals | 3 cluster imports | Lazy imports not hidden behind adapter |

## Evidence

| Source | Path |
|---|---|
| Multi-import map | `artifacts/bv10_dependency_inventory.json` |
| BV9 maintenance matrix | `docs/audits/BV9_maintenance_matrix.md` |
