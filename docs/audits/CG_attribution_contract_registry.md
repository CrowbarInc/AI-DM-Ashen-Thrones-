# CG-5 — Attribution Contract Registry

**Date:** 2026-06-25  
**Scope:** Documentation and comment-clarity only. No runtime attribution behavior, taxonomy rename, replacement logic, mutation semantics, repair-kind semantics, emitted lineage, validation weakening, or artifact regeneration.

**Related:**

- [`CG_failure_classification_authority_registry.md`](CG_failure_classification_authority_registry.md) (CG-1 failure vs runtime boundaries)
- [`CG_recurrence_taxonomy_registry.md`](CG_recurrence_taxonomy_registry.md) (CG-4 recurrence identity)
- [`metrics/BS3_canonical_attribution_contract.md`](metrics/BS3_canonical_attribution_contract.md) (BS3 contract definition)

## Purpose

Attribution vocabulary intentionally spans failure classification, runtime lineage emission, and replay governance. This registry records **which module owns each attribution concept**, what **imports vs validates vs derives**, and where **intentional overlaps** remain.

Use this document before editing repair kinds, mutation classifications, replacement paths, owner-bucket validation, or attribution inventory logic.

## Contract boundary summary

| Domain | Owns | Does not own |
|---|---|---|
| **Failure classification** (`tests/failure_classification_contract.py`) | Failure categories, primary/secondary owners, investigation routing, dashboard evidence manifest, source-family tags, emission sublayers, repair-kind **runtime/producer subsets** | Replacement paths, repair/mutation unions, alias normalization, attribution record shape |
| **Attribution contract** (`tests/helpers/attribution_contract.py`) | Replacement paths, repair-kind **union** + aliases, mutation-classification **core union** + aliases, fallback-kind normalization, attribution record validation, attribution origins | Failure categories, drift buckets, recurrence key formula, runtime bucket string authority |
| **Runtime** (`game/final_emission_ownership_schema.py`, `game/final_emission_meta.py`, `game/final_emission_replay_projection.py`) | Owner-bucket strings, split-owner tokens, FEM producer stamps, **emitted** lineage events (`repair_kind`, `mutation_kind`, `fallback_kind`, `recurrence_key`) | Replay-contract allowed sets, attribution completeness scoring |
| **Attribution inventory** (`tests/helpers/replacement_attribution_inventory.py`) | Read-side record construction from FEM, lineage, replay projection, classifier rows | Taxonomy authority (imports contract) |
| **Attribution read facade** (`game/attribution_read_views.py`) | Re-export only | Any new vocabulary |

## Authority kinds (attribution-specific)

| Kind | Meaning |
|---|---|
| **attribution-contract-owned** | BS3 union, path, alias, normalization, and record validation |
| **replay-contract-owned (imported)** | Subsets consumed by attribution for validation only |
| **runtime-owned (emitted)** | Production stamps and lineage event fields |
| **replay-contract-owned (derived projection)** | Read-side maps in `final_emission_replay_projection` that **derive** mutation/source labels from FEM |
| **compatibility-only** | Legacy aliases, lineage-only tokens, identity alias maps — accepted but not authoritative for new values |

---

## Vocabulary registry

Columns: **Owner** · **Imported authorities** · **Consumers** · **Runtime?** · **Replay-contract?** · **Attribution?** · **Compatibility?**

### 1. Replacement paths

| Field | Value |
|---|---|
| **Allowed values** | `visibility replacement`, `first mention replacement`, `referential replacement`, `sealed replacement`, `response type replacement`, `sanitizer replacement`, `repair mutation`, `opening fallback`, `strict social replacement` (`REPLACEMENT_PATHS`, count locked at 9) |
| **Owning module** | `tests/helpers/attribution_contract.py` |
| **Imported authorities** | none |
| **Downstream consumers** | `replacement_attribution_inventory` (path detection + record shape), `test_attribution_contract`, `test_replacement_attribution_inventory`, BS3 compliance report |
| **Runtime-owned** | no (runtime FEM flags are inputs; path labels are attribution-only) |
| **Replay-contract-owned** | no |
| **Attribution-owned** | **yes** |
| **Compatibility-only** | no |

### 2. Required attribution record fields

| Field | Value |
|---|---|
| **Allowed values** | `owner_bucket`, `source_family`, `repair_kind`, `recurrence_key`, `mutation_classification` (`REQUIRED_ATTRIBUTION_FIELDS`) |
| **Owning module** | `tests/helpers/attribution_contract.py` |
| **Imported authorities** | per-field validation imports (see fields 3–7) |
| **Downstream consumers** | Inventory completeness, maturity scores, BS1/BS3/BS4/BS5 reports |
| **Runtime-owned** | no |
| **Replay-contract-owned** | no |
| **Attribution-owned** | **yes** |
| **Compatibility-only** | no |

### 3. Owner buckets (attribution validation union)

| Field | Value |
|---|---|
| **Allowed values** | Union of opening + sealed + visibility fallback owner buckets (`ALLOWED_OWNER_BUCKETS`) |
| **Owning module (strings)** | `game/final_emission_ownership_schema.py` + `game/final_emission_owner_bucket_views.py` |
| **Owning module (validation union)** | `tests/helpers/attribution_contract.py` (mirrors runtime buckets for record validation) |
| **Imported authorities** | `ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS`, `ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS`, `ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS` from `tests/failure_classification_contract.py` (re-export of runtime) |
| **Downstream consumers** | Attribution validators, inventory `_owner_bucket_from_fem`, classifier optional evidence, split-owner matrix |
| **Runtime-owned** | **yes** (canonical strings) |
| **Replay-contract-owned** | mirrors only (`failure_classification_contract`) |
| **Attribution-owned** | validation union only |
| **Compatibility-only** | no |

### 4. Source-family tags

| Field | Value |
|---|---|
| **Allowed values** | 21 tags in `ALLOWED_SOURCE_FAMILY_TAGS` (e.g. `final_emission_gate`, `opening_fallback`, `output_sanitizer`, …) |
| **Owning module** | `tests/failure_classification_contract.py` |
| **Imported authorities** | none at authority source |
| **Downstream consumers** | `attribution_contract.validate_source_family`, classifier routing, inventory `_infer_source_family_*`, `final_emission_replay_projection.FALLBACK_KIND_SOURCE_FAMILY_MAP` (projection derives tags from `fallback_kind`) |
| **Runtime-owned** | no (runtime emits `fallback_kind`; projection maps to family) |
| **Replay-contract-owned** | **yes** |
| **Attribution-owned** | validates imported set only |
| **Compatibility-only** | no |

### 5. Repair kinds — runtime/producer subsets

| Field | Value |
|---|---|
| **Allowed values** | `ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS` (4), `ALLOWED_PRODUCER_REPAIR_KINDS` (8), `LEGACY_RESPONSE_TYPE_REPAIR_KINDS` (`thin_answer`) |
| **Owning module** | `tests/failure_classification_contract.py` |
| **Imported authorities** | none |
| **Downstream consumers** | `attribution_contract.ALLOWED_REPAIR_KINDS` union, classifier `_repair_kind` evidence, runtime FEM stamps |
| **Runtime-owned** | **yes** (stamped on FEM/lineage as producer facts) |
| **Replay-contract-owned** | **yes** (subset authority) |
| **Attribution-owned** | imports subsets into union |
| **Compatibility-only** | `LEGACY_RESPONSE_TYPE_REPAIR_KINDS` is legacy-compatible |

### 6. Repair kinds — attribution union

| Field | Value |
|---|---|
| **Allowed values** | Union of runtime + producer + legacy + opening kinds (`ALLOWED_REPAIR_KINDS`); opening-only subset `ALLOWED_OPENING_REPAIR_KINDS` (`opening_deterministic_fallback`, `opening_deterministic_fallback_failed_closed`) |
| **Owning module** | `tests/helpers/attribution_contract.py` |
| **Imported authorities** | All repair-kind subsets from `tests/failure_classification_contract.py` |
| **Downstream consumers** | `validate_repair_kind`, inventory, BS3 audit layers, `replacement_attribution_inventory` re-export |
| **Runtime-owned** | emits individual kinds; does not own union |
| **Replay-contract-owned** | subset authority in failure contract |
| **Attribution-owned** | **yes** (union + opening-only + validation) |
| **Compatibility-only** | no |

### 7. Repair-kind aliases and deprecated tokens

| Field | Value |
|---|---|
| **Allowed values** | `REPAIR_KIND_ALIASES`: `response_type_contract_repair` → `answer_upstream_prepared_repair`; `DEPRECATED_REPAIR_KINDS` = legacy response-type set; `DEPRECATED_FALLBACK_KIND_ALIASES`: `visibility_or_scene_replacement` → `visibility_hard_replacement` |
| **Owning module** | `tests/helpers/attribution_contract.py` |
| **Imported authorities** | `LEGACY_RESPONSE_TYPE_REPAIR_KINDS` for deprecated set |
| **Downstream consumers** | `normalize_repair_kind`, `normalize_fallback_kind`, lineage projection compatibility (`_LEGACY_VISIBILITY_OR_SCENE_REPLACEMENT` in replay projection) |
| **Runtime-owned** | no |
| **Replay-contract-owned** | no |
| **Attribution-owned** | **yes** (normalization) |
| **Compatibility-only** | **yes** |

### 8. Lineage-only repair kinds

| Field | Value |
|---|---|
| **Allowed values** | `canonical_rewrite`, `local_rebind`, `dialogue_enforcement_skipped_due_to_social_suppression` (`LINEAGE_ONLY_REPAIR_KINDS`) |
| **Owning module** | `tests/helpers/attribution_contract.py` (documented exclusion list) |
| **Imported authorities** | none |
| **Downstream consumers** | BS3 compliance report deprecated section; speaker-repair inventory tests |
| **Runtime-owned** | **yes** (emitted on speaker/continuity lineage events) |
| **Replay-contract-owned** | no |
| **Attribution-owned** | documents intentional **non-membership** in union |
| **Compatibility-only** | **yes** |

### 9. Mutation classifications — core union

| Field | Value |
|---|---|
| **Allowed values** | 22 tokens in `ALLOWED_MUTATION_CLASSIFICATION_CORE` (e.g. `fallback_mutation`, `visibility_replacement_mutation`, `fallback_behavior_repair_mutation`, …) |
| **Owning module** | `tests/helpers/attribution_contract.py` |
| **Imported authorities** | none for core tokens |
| **Downstream consumers** | `validate_mutation_classification`, inventory, replay projection emission maps |
| **Runtime-owned** | emits via `mutation_kind` on lineage events |
| **Replay-contract-owned** | no |
| **Attribution-owned** | **yes** (validation union core) |
| **Compatibility-only** | no |

### 10. Mutation classifications — emission sublayers (imported)

| Field | Value |
|---|---|
| **Allowed values** | 15 tokens in `ALLOWED_EMISSION_SUBLAYERS` (e.g. `response_type`, `fallback_behavior`, `sanitizer.empty_fallback`, `final_emission.finalize_packaging`, …) |
| **Owning module** | `tests/failure_classification_contract.py` |
| **Imported authorities** | none at source |
| **Downstream consumers** | Extended into `ALLOWED_MUTATION_CLASSIFICATIONS`; classifier `emission_sublayer` / `mutation_source` evidence; dashboard manifest |
| **Runtime-owned** | no |
| **Replay-contract-owned** | **yes** |
| **Attribution-owned** | imports into mutation union for cross-layer validation |
| **Compatibility-only** | treated as classifier-side aliases for mutation classification |

### 11. Mutation classifications — full validation union

| Field | Value |
|---|---|
| **Allowed values** | `ALLOWED_MUTATION_CLASSIFICATIONS` = core ∪ emission sublayers |
| **Owning module** | `tests/helpers/attribution_contract.py` (union assembly) |
| **Imported authorities** | `ALLOWED_EMISSION_SUBLAYERS` from failure contract |
| **Downstream consumers** | All attribution validation and inventory completeness |
| **Runtime-owned** | partial (emits core kinds) |
| **Replay-contract-owned** | partial (sublayers) |
| **Attribution-owned** | **yes** (assembled union) |
| **Compatibility-only** | no |

### 12. Mutation-classification aliases

| Field | Value |
|---|---|
| **Allowed values** | `MUTATION_CLASSIFICATION_ALIASES`: `strict_social_replacement` → `strict_social_replacement` (identity) |
| **Owning module** | `tests/helpers/attribution_contract.py` |
| **Imported authorities** | none |
| **Downstream consumers** | `normalize_mutation_classification` |
| **Runtime-owned** | no |
| **Replay-contract-owned** | no |
| **Attribution-owned** | **yes** |
| **Compatibility-only** | **yes** (identity map reserved for future alias) |

### 13. Attribution origins

| Field | Value |
|---|---|
| **Allowed values** | `direct`, `projected`, `classifier_inferred` (`ALLOWED_ATTRIBUTION_ORIGINS`) |
| **Owning module** | `tests/helpers/attribution_contract.py` |
| **Imported authorities** | none |
| **Downstream consumers** | Inventory record construction, strict vs resolved completeness scoring |
| **Runtime-owned** | no |
| **Replay-contract-owned** | no |
| **Attribution-owned** | **yes** |
| **Compatibility-only** | no |

### 14. Recurrence key shape (attribution validation)

| Field | Value |
|---|---|
| **Allowed values** | Must contain `:` and length ≥ 5 (`RECURRENCE_KEY_MIN_LENGTH`); formula owned elsewhere |
| **Owning module (formula)** | `tests/helpers/replay_bug_recurrence_events.py` |
| **Owning module (shape check)** | `tests/helpers/attribution_contract.py` |
| **Imported authorities** | none |
| **Downstream consumers** | `validate_recurrence_key`, lineage inventory |
| **Runtime-owned** | emits lineage recurrence keys (distinct from bug-recurrence v1 key) |
| **Replay-contract-owned** | no |
| **Attribution-owned** | shape validation only |
| **Compatibility-only** | no |

### 15. Runtime split-owner registries

| Field | Value |
|---|---|
| **Allowed values** | `ALLOWED_FALLBACK_SELECTION_OWNERS`, `ALLOWED_FALLBACK_CONTENT_OWNERS`, per-path selection/content owner constants, sanitizer trace short fields |
| **Owning module** | `game/final_emission_ownership_schema.py` |
| **Imported authorities** | realization provenance tokens |
| **Downstream consumers** | `attribution_read_views` (re-export), `final_emission_replay_projection`, split-owner matrix, classifier optional evidence |
| **Runtime-owned** | **yes** |
| **Replay-contract-owned** | mirrors via `failure_classification_contract` |
| **Attribution-owned** | no |
| **Compatibility-only** | legacy sanitizer trace short fields |

### 16. Runtime owner-bucket mappers

| Field | Value |
|---|---|
| **Allowed values** | `opening_fallback_owner_bucket_from_meta`, `sealed_fallback_owner_bucket_from_fields`, `visibility_fallback_owner_bucket_from_fields` |
| **Owning module** | `game/final_emission_owner_bucket_views.py` (re-exported via `attribution_read_views`) |
| **Imported authorities** | bucket strings from ownership schema |
| **Downstream consumers** | Inventory projection, replay lineage projection |
| **Runtime-owned** | **yes** (derivation logic) |
| **Replay-contract-owned** | no |
| **Attribution-owned** | consumes for projected `owner_bucket` |
| **Compatibility-only** | no |

### 17. Replay projection maps (derived mutation/source)

| Field | Value |
|---|---|
| **Allowed values** | `FALLBACK_KIND_SOURCE_FAMILY_MAP`, `FALLBACK_KIND_MUTATION_CLASSIFICATION_MAP`, `REPAIR_FLAG_MUTATION_CLASSIFICATION_MAP`, sealed/visibility fallback kind constants |
| **Owning module** | `game/final_emission_replay_projection.py` |
| **Imported authorities** | ownership schema owners; mutation core values must stay aligned with attribution union |
| **Downstream consumers** | `build_fem_runtime_lineage_events`, inventory lineage records, sync split-owner matrix |
| **Runtime-owned** | **yes** (emits derived labels) |
| **Replay-contract-owned** | no |
| **Attribution-owned** | validates emitted values against union |
| **Compatibility-only** | `_LEGACY_VISIBILITY_OR_SCENE_REPLACEMENT` token |

### 18. FEM producer attribution stamps

| Field | Value |
|---|---|
| **Allowed values** | FEM fields: `producer_repair_kind`, `response_type_repair_kind`, `fallback_behavior_repair_kind`, `*_fallback_owner_bucket`, replacement-applied flags |
| **Owning module** | `game/final_emission_meta.py` (packaging/stamps) |
| **Imported authorities** | ownership schema registries |
| **Downstream consumers** | Lineage projection, inventory direct-origin fields, classifier evidence |
| **Runtime-owned** | **yes** |
| **Replay-contract-owned** | no |
| **Attribution-owned** | validates stamped values when present |
| **Compatibility-only** | no |

---

## Mutation classification role matrix

Each value in `ALLOWED_MUTATION_CLASSIFICATIONS` participates in one or more roles. **Do not split or rename** values in CG-5; this table documents current intent only.

| Role | Description | Examples |
|---|---|---|
| **Producer fact** | Stamped or selected during runtime repair/finalization; may appear directly on FEM or first mutation event | `response_type_repair_mutation`, `referential_clarity_local_substitution_mutation` |
| **Replay-derived** | Deterministically projected from FEM flags or `fallback_kind` via `final_emission_replay_projection` maps | `visibility_replacement_mutation`, `fallback_behavior_repair_mutation`, `sealed_replacement_mutation` |
| **Emission sublayer** | Classifier evidence vocabulary (`emission_sublayer` / `mutation_source`); failure-contract-owned, unioned for attribution validation | `response_type`, `sanitizer.empty_fallback`, `final_emission.finalize_packaging` |
| **Compatibility alias** | Normalization map entry; identity or legacy bridge | `strict_social_replacement` (identity alias) |

### Core mutation tokens — authority vs derivation

| Token | Authoritative owner | Normalized? | Derived? | Notes |
|---|---|:---:|:---:|---|
| `fallback_mutation` | attribution core | no | yes | From opening/scene `fallback_kind` |
| `speaker_repair_mutation` | attribution core | no | yes | Speaker lineage projection |
| `continuity_repair_mutation` | attribution core | no | yes | Interaction continuity owner branch |
| `response_type_repair_mutation` | attribution core | no | yes | Response-type repair flags / prepared emission |
| `sanitizer_mutation` | attribution core | no | yes | Sanitizer fallback paths |
| `final_emission_mutation` | attribution core | no | yes | Finalize/route packaging mutations |
| `repair_only_mutation` | attribution core | no | yes | Generic repair-flag fallback |
| `visibility_replacement_mutation` | attribution core | no | yes | Visibility hard replacement |
| `first_mention_replacement_mutation` | attribution core | no | yes | First-mention hard replacement |
| `referential_clarity_replacement_mutation` | attribution core | no | yes | Referential hard replacement |
| `referential_clarity_local_substitution_mutation` | attribution core | no | partial | Producer-stamped local substitution |
| `sealed_replacement_mutation` | attribution core | no | yes | Sealed subkind projection default |
| `*_repair_mutation` (10 behavior repairs) | attribution core | no | yes | `REPAIR_FLAG_MUTATION_CLASSIFICATION_MAP` |
| Emission sublayer tokens (15) | failure contract | no | no | Classifier evidence; not emitted as `mutation_kind` |

---

## Repair-kind ownership and validation direction

### Why both contracts reference repair kinds

1. **Runtime/producer subsets** (`failure_classification_contract`) define which tokens may be **stamped at origin** (FEM fields, classifier evidence paths tied to replay failure taxonomy).
2. **Attribution union** (`attribution_contract`) defines the **complete allowed set** for BS3 five-field record validation across inventory layers.
3. **Lineage emission** (`final_emission_replay_projection`, `runtime_lineage_telemetry`) may emit tokens outside the attribution union (e.g. `canonical_rewrite`) — documented as lineage-only, not contract violations for speaker paths.

### Validation direction

```
Runtime FEM stamp ──► lineage event.repair_kind ──► inventory (direct origin)
                              │
                              ▼
              attribution_contract.validate_repair_kind (union + normalize)
                              ▲
Failure classifier row.repair_kind ──► inventory (classifier_inferred)
                              ▲
              imports subsets from failure_classification_contract
```

- **Adding a producer repair kind:** edit `ALLOWED_PRODUCER_REPAIR_KINDS` (or runtime subset) **and** confirm union inclusion in `ALLOWED_REPAIR_KINDS`.
- **Adding a legacy alias:** edit `REPAIR_KIND_ALIASES` in attribution contract only.
- **Speaker/continuity kinds outside union:** remain lineage-only until explicitly promoted into producer or runtime subsets.

---

## Intentional overlaps

| Overlap | Failure classification | Attribution | Runtime |
|---|---|---|---|
| **repair_kind** | Owns runtime/producer/legacy subsets | Owns union + aliases + validation | Emits on FEM/lineage |
| **mutation_classification** | Owns emission sublayers (classifier evidence) | Owns core union + assembled validation set | Emits `mutation_kind` (core tokens) |
| **source_family** | Owns allowed tag set | Validates imported set | Projection derives from `fallback_kind` |
| **owner_bucket** | Mirrors runtime buckets for classifier | Validates union for records | Owns canonical strings |
| **fallback_kind** | Dashboard/observation evidence | Normalizes deprecated alias only | Emits on lineage; projection input |

---

## Consumer map by layer

| Layer | Module | Role |
|---|---|---|
| **Authority** | `attribution_contract.py` | Unions, paths, aliases, validators |
| **Inventory** | `replacement_attribution_inventory.py` | Constructs records; imports contract symbols |
| **Validation tests** | `test_attribution_contract.py` | Locks taxonomy + normalization |
| **Inventory tests** | `test_replacement_attribution_inventory.py` | End-to-end record construction |
| **Classifier** | `failure_classifier.py` | Emits evidence fields; does not own attribution unions |
| **Failure contract** | `failure_classification_contract.py` | Subsets + source families + sublayers |
| **Lineage emission** | `final_emission_replay_projection.py` | Derives/emits mutation + repair on events |
| **Read facade** | `attribution_read_views.py` | Re-exports runtime bucket vocabulary |
| **FEM packaging** | `final_emission_meta.py` | Producer stamps and registry consumption |
| **Ownership schema** | `final_emission_ownership_schema.py` | Canonical bucket and split-owner strings |
| **Completeness metric** | `attribution_completeness_metric.py` | Consumes contract fields |

---

## Governance metrics (CG-5 snapshot)

| Metric | Count |
|---|---:|
| Attribution vocabulary families documented | 18 |
| Authority modules (attribution-owned) | 1 (`attribution_contract.py`) |
| Imported authority modules | 2 (`failure_classification_contract.py`, runtime ownership via contract mirror) |
| Compatibility layers | 4 (repair aliases, fallback-kind aliases, mutation identity alias, lineage-only repair kinds) |
| Replacement paths | 9 |
| Core mutation classifications | 22 |
| Imported emission sublayers | 15 |
| Repair-kind union members | runtime (4) + producer (8) + legacy (1) + opening (2) = 15 unique |
| Remaining ambiguous concepts | 5 (see below) |

### Remaining ambiguous concepts

1. **Dual mutation vocabulary** — classifier uses `emission_sublayer` strings while lineage emits `mutation_kind` tokens; attribution union accepts both by design.
2. **Repair kind split** — failure contract subsets vs attribution union; both must change together for new producer kinds.
3. **Lineage-only repair kinds** — runtime-emitted but intentionally excluded from BS3 union (speaker paths).
4. **Source family derivation** — failure contract owns tags; replay projection and inventory **derive** values from `fallback_kind` (not authoritative emission).
5. **Recurrence key namespaces** — lineage `recurrence_key` shape vs bug-recurrence `recurrence:v1:…` formula are distinct authorities.

### Remaining cross-contract dependencies

| Dependency | Direction | Change cost |
|---|---|---|
| Repair subsets → attribution union | failure contract → attribution | Edit both for new producer kinds |
| Emission sublayers → mutation union | failure contract → attribution | Edit both for new sublayer evidence |
| Runtime buckets → owner validation | ownership schema → failure contract mirror → attribution | Edit schema + contract mirror |
| Projection maps → mutation union | replay projection emits; attribution validates | Align maps when adding core mutation tokens |
| Classifier evidence → inventory | classifier rows → inventory `classifier_inferred` origin | Fixture + inventory tests |

---

## Change checklist

| If you change… | Edit… | Behavioral impact |
|---|---|---|
| Replacement path label | `attribution_contract.py` only | Inventory path detection strings must match |
| Producer repair kind | `failure_classification_contract.py` subset + confirm `ALLOWED_REPAIR_KINDS` | Runtime stamp + validation |
| Repair alias | `attribution_contract.py` `REPAIR_KIND_ALIASES` | Normalization only |
| Core mutation token | `attribution_contract.py` + `final_emission_replay_projection.py` maps | Emitted lineage + validation |
| Emission sublayer | `failure_classification_contract.py` + attribution union import | Classifier evidence + validation |
| Owner bucket string | `final_emission_ownership_schema.py` + contract mirror | Runtime + replay + attribution |
| Fallback-kind legacy alias | `attribution_contract.py` + projection legacy token | Normalization + projection compat |
| Lineage-only repair kind | Document in `LINEAGE_ONLY_REPAIR_KINDS`; do not add to union unless promoting | Speaker/continuity paths |

---

## Authority file index (attribution scope)

| File | Owns | Imports / validates |
|---|---|---|
| `tests/helpers/attribution_contract.py` | Paths, unions, aliases, normalization, record validation, maturity audit | Failure contract subsets, bucket mirrors, source families, emission sublayers |
| `tests/helpers/replacement_attribution_inventory.py` | Record construction, baseline corpus, BS1–BS5 reports | Entire attribution contract surface |
| `tests/failure_classification_contract.py` | Source families, repair subsets, emission sublayers, bucket mirrors | Runtime ownership schema via read facade |
| `game/final_emission_ownership_schema.py` | Bucket strings, split-owner tokens | — |
| `game/attribution_read_views.py` | Re-export facade | Ownership schema + bucket views |
| `game/final_emission_meta.py` | FEM shapes, producer stamps | Ownership schema registries |
| `game/final_emission_replay_projection.py` | Lineage derivation maps, event emission | Ownership schema owners; aligns with attribution core |
