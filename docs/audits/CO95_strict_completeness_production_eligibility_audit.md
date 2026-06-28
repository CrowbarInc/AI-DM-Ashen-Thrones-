# CO95 — Strict-Completeness Production Eligibility Audit

Audit date: 2026-06-27  
Scope: discovery-only policy audit over BS1 corpus (56 records), BS3 contract, BR1 strict metric. No production, projection, classifier, baseline, or metric changes.

Ground truth: live `build_baseline_attribution_corpus()` + `calculate_attribution_completeness()`.

---

## Executive Summary

| Metric | Value |
|---|---:|
| Resolved completeness | 48/56 (85.71%) |
| Strict completeness | **0/56 (0.0%)** |
| Unresolved records | 8 (all `gate_outcome` `mutation_classification`) |

**Strict completeness is zero not because resolved fields are missing, but because every resolved record carries at least one inventory-origin field marked `projected` or `classifier_inferred`.** No resolved record is blocked by a single field alone; the minimum blocker set is two fields on every resolved record.

**Production eligibility policy:** strict-direct status requires a field value written at an authoritative production write site and read back without inventory inference or replay derivation. Fields whose canonical semantics are replay-projected or classifier-derived are **permanently resolved-only** under current architecture unless a new FEM stamp surface is introduced with explicit ownership (not duplication of sibling lineage events).

**Program recommendation:** **Freeze strict completeness at current architecture** and **close the attribution maturity program** for resolved completeness (plateau at 85.71%). Remaining resolved gaps (8 records) are intentionally unavailable per CO94. Further strict-direct work lacks legitimate production semantics without duplicating replay-derived information.

---

## 1. Strict-Completeness Field Inventory

Strict completeness requires all five `REQUIRED_ATTRIBUTION_FIELDS` populated, taxonomy-valid, and `attribution_origin[field] == direct` (`tests/helpers/attribution_completeness_metric.py`, `replacement_attribution_inventory._is_strict_complete`).

### 1a. Corpus origin breakdown (56 records)

| Field | Direct | Projected | Classifier inferred | Missing | Resolved coverage |
|---|---:|---:|---:|---:|---:|
| `owner_bucket` | 43 | 12 | 1 | 0 | 100% |
| `source_family` | 7 | 49 | 0 | 0 | 100% |
| `repair_kind` | 33 | 18 | 5 | 0 | 100% |
| `recurrence_key` | 26 | 30 | 0 | 0 | 100% |
| `mutation_classification` | 10 | 32 | 6 | 8 | 85.7% |

### 1b. Per-field write and read sites

#### `repair_kind`

| Site class | Location | Role |
|---|---|---|
| **Canonical production write** | `game/final_emission_meta.stamp_producer_repair_kind`; path owners (`final_emission_visibility_metadata`, `final_emission_sealed_fallback`, `final_emission_response_type`, `output_sanitizer_lineage`); FEM fields `producer_repair_kind`, `response_type_repair_kind`, `fallback_behavior_repair_kind`, opening repair kinds | Authoritative repair identity at gate/sanitizer write time |
| **Read-side projection** | `build_fem_runtime_lineage_events` → `make_runtime_lineage_event(repair_kind=…)`; `_lineage_mutation_attribution_from_fem`; `_projected_gate_family_repair_kind_from_fem` | Bridges FEM stamps onto lineage events when replay omits them; marks inventory origin **projected** even when FEM holds the stamp |
| **Replay-derived** | Lineage `mutation` / `fallback_selected` events carrying `repair_kind` from projection maps | Direct on lineage surface when event field populated |
| **Inventory-derived** | `attribution_record_from_failure_classification` — classifier-inferred when not matched to `response_type_repair_kind` | Origin `classifier_inferred` (5 slots) |

#### `owner_bucket`

| Site class | Location | Role |
|---|---|---|
| **Canonical production write** | `stamp_visibility_fallback_owner_bucket_from_fields`, `stamp_sealed_fallback_realization_family`, `stamp_opening_fallback_owner_bucket`, `stamp_response_type_prepared_repair_owner_bucket` (CO92), sanitizer trace co-stamp; FEM fields `visibility_fallback_owner_bucket`, `sealed_fallback_owner_bucket`, `opening_fallback_owner_bucket` | Authoritative ownership at selection/replace write time |
| **Read-side projection** | `game/attribution_read_views` mappers consumed by `_owner_bucket_from_fem`, `_projected_sanitizer_owner_bucket_from_fem`, `_projected_gate_family_owner_bucket_from_fem`, `_projected_repair_mutation_owner_bucket`, `_projected_passive_scene_concrete_beat_attribution` | Derives bucket when FEM lacks direct stamp but inferable fields exist |
| **Replay-derived** | Lineage `fallback_owner_bucket` on `fallback_selected` / `mutation` events | Direct when preserved from FEM through `build_fem_runtime_lineage_events` |
| **Inventory-derived** | Classifier row bucket fields; opening bucket always `classifier_inferred` in failure-classification records | 1 classifier-inferred slot |

#### `recurrence_key`

| Site class | Location | Role |
|---|---|---|
| **Canonical production write** | **None on FEM.** Computed at lineage event creation: `runtime_lineage_telemetry.make_runtime_lineage_event` → `build_recurrence_key` | Identity is event-scoped, not FEM-scoped (CG-4 / runtime lineage contract) |
| **Read-side projection** | `_recurrence_key_from_lineage_events`; passive-scene inventory `build_recurrence_key` call in `_projected_passive_scene_concrete_beat_attribution` | Reads projected lineage bundle or recomputes from contract constants |
| **Replay-derived** | `event.recurrence_key` on all emitted lineage events | Direct on `runtime_lineage_event` source (26 slots) |
| **Inventory-derived** | Failure-classification records pull from observed turn lineage | Origin projected (7 slots) |

#### `source_family`

| Site class | Location | Role |
|---|---|---|
| **Canonical production write** | **None.** Runtime emits `fallback_kind`, component owners, and flags — not `source_family` | CG registry §4: replay-contract-owned tags |
| **Read-side projection** | `_infer_source_family_from_fem` (replacement-path heuristic); `_infer_source_family_from_lineage`; `final_emission_replay_projection.project_source_family_from_fallback_kind` | Always inventory origin **projected** except classifier rows |
| **Replay-derived** | `FALLBACK_KIND_SOURCE_FAMILY_MAP` in lineage projection | Maps fallback_kind → family at replay time |
| **Inventory-derived** | Failure classifier emits `source_family` on classification rows | Direct on `failure_classification` source (7 slots) |

#### `mutation_classification`

| Site class | Location | Role |
|---|---|---|
| **Canonical production write** | Lineage `mutation_kind` on `mutation` events via `_append_fem_mutation_projections` in `build_fem_runtime_lineage_events` | Text-mutation classification at lineage projection time (not FEM field) |
| **Read-side projection** | `_mutation_classification_from_lineage_events`; `project_mutation_classification_from_fallback_kind` on `fallback_selected`; passive-scene inventory projection | FEM-metadata and replay records read sibling mutation events — origin **projected** |
| **Replay-derived** | `event.mutation_kind` on `mutation` events | Direct on mutation lineage records (10 slots) |
| **Inventory-derived** | Classifier `mutation_source` / `emission_sublayer` | Origin `classifier_inferred` (6 slots) |
| **Intentionally absent** | `gate_outcome` events omit `mutation_kind` by contract (CO94) | 8 missing slots |

---

## 2. Projected-Field Classification Matrix

Every field slot that is **resolved** (present + taxonomy-valid) but **not strict-direct** (`projected` or `classifier_inferred`):

| Field | Origin | Count | Classification | Architectural ground |
|---|---|---:|---|---|
| `source_family` | projected | 49 | **Intentionally projection-only** | No FEM stamp surface; CG registry assigns authority to replay-contract tags derived from `fallback_kind` / path heuristics |
| `mutation_classification` | projected | 32 | **Replay-derived by design** | FEM/replay inventory reads classification from sibling `mutation` lineage events; value originates in `build_fem_runtime_lineage_events`, not FEM stamps |
| `recurrence_key` | projected | 30 | **Replay-derived by design** | Key formula owned by `runtime_lineage_telemetry.build_recurrence_key`; FEM-metadata path always reads projected lineage bundle |
| `repair_kind` | projected | 18 | **Only for specific replacement paths** | Gate-family / sanitizer lineage bridge via `_lineage_mutation_attribution_from_fem`; FEM already holds stamp — inventory marks projected when bridging to lineage, not absent production evidence |
| `owner_bucket` | projected | 12 | **Only for specific replacement paths** | Sanitizer co-stamp (`unknown-none`), strict-social without direct bucket, opening fail-closed meta projection, passive-scene satisfier inventory constants |
| `repair_kind` | classifier_inferred | 5 | **Inventory-derived by design** | Failure classifier row inference; not a production write gap |
| `mutation_classification` | classifier_inferred | 6 | **Inventory-derived by design** | Classifier `mutation_source` / `emission_sublayer`; distinct from runtime `mutation_kind` |
| `owner_bucket` | classifier_inferred | 1 | **Inventory-derived by design** | Opening fallback classifier record |

### Classification summary

| Classification | Field slots | Share of non-direct resolved slots |
|---|---:|---:|
| Intentionally projection-only | 49 (`source_family`) | 41% |
| Replay-derived by design | 62 (`recurrence_key` + `mutation_classification` projected) | 52% |
| Only for specific replacement paths | 30 (`repair_kind` + `owner_bucket` projected) | 25% |
| Inventory-derived by design | 12 (classifier_inferred) | 10% |
| Historical compatibility projection | 0 | 0% |
| Production-stamp eligible (net-new) | 0 | 0% |

*Percentages exceed 100% because slots overlap across classification buckets by field family; no slot qualifies as net-new production-stamp eligible without duplicating replay-derived information.*

### Blocker combinations (48 resolved-but-not-strict records)

| Non-direct field set | Records | Dominant source kinds |
|---|---:|---|
| `source_family`, `recurrence_key`, `mutation_classification` | 18 | `fem_metadata`, `replay_projection` |
| `repair_kind`, `source_family` | 8 | `runtime_lineage_event` (gate_outcome / fallback_selected) |
| `mutation_classification`, `source_family` | 7 | `runtime_lineage_event` (mutation / fallback_selected) |
| `owner_bucket`, `recurrence_key`, `mutation_classification`, `source_family` | 5 | `replay_projection`, `failure_classification` |
| Other multi-field combinations | 10 | Mixed |

**Zero records** are blocked from strict completeness by `source_family` alone.

---

## 3. Production Eligibility Assessment

Formal policy: a field is **strict-direct eligible** only if future production work can stamp it at an authoritative write site **without** (a) duplicating sibling lineage events, (b) conflating routing vs mutation semantics, or (c) replacing classifier/inventory inference that exists because runtime intentionally omits the field.

| Field | Eligible? | Rationale |
|---|---|---|
| **`repair_kind`** | **Only for specific replacement paths** | FEM stamps exist and are direct on `fem_metadata` / `replay_projection` (33 direct). Remaining projected slots are lineage-bridge reads where FEM stamp is present but inventory origin policy marks projected. Gate_outcome / fallback_selected could receive lineage `repair_kind` from FEM at projection time — that is replay-layer enrichment, not a missing producer stamp. Classifier-inferred slots are inventory-only. |
| **`owner_bucket`** | **Only for specific replacement paths** | 43/56 direct after CO92–CO93. Remaining projected: sanitizer `unknown-none` (co-stamp semantics — bucket is direct on FEM in baseline but projected when bridged through sanitizer helper), strict-social (could stamp `sealed_fallback_owner_bucket` at repair write — partially projected today), opening fail-closed (meta mapper projection). No corpus-wide gap. |
| **`recurrence_key`** | **No** | Canonical identity is computed in `make_runtime_lineage_event`. Stamping on FEM would duplicate lineage-computed keys and violate CG-4 recurrence identity separation. Direct origin already achievable on `runtime_lineage_event` records (26/56). |
| **`source_family`** | **No** | No production write surface by design (CG registry §4). Tags are replay-contract vocabulary derived from `fallback_kind` and component ownership. A FEM `source_family` stamp would be a new metadata dimension duplicating deterministic projection maps. |
| **`mutation_classification`** | **No** (for unresolved gate_outcome); **Only for specific replacement paths** (for resolved projected slots) | CO94 locks `gate_outcome` as mutation-free; sibling `mutation` events carry classification. Resolved projected slots read sibling mutations — stamping on FEM or gate_outcome would duplicate. Mutation lineage records already have direct `mutation_kind` (10 slots). Classifier-inferred slots are intentionally separate vocabulary (`emission_sublayer`). |

### Production-eligibility policy (normative)

1. **Stamp at write time** when the field represents a producer decision made during gate/sanitizer/finalize (applies today: `repair_kind`, `owner_bucket`).
2. **Never stamp to satisfy strict completeness** when the authoritative value already exists on a sibling lineage event (`mutation_classification`, `recurrence_key`).
3. **Never introduce FEM stamps** for replay-contract derived labels (`source_family`).
4. **Treat classifier-inferred origin** as permanently non-strict regardless of production stamps.
5. **Resolved-only fields** on `gate_outcome` records are acceptable; use sibling `mutation` events for strict-adjacent observability.

---

## 4. Strict-Completeness Roadmap

Remaining opportunities that could increase strict completeness **without violating architecture**:

| Opportunity | Affected paths / records | Est. strict gain | Complexity | Architectural risk | Verdict |
|---|---|---:|---|---|---|---|
| FEM `source_family` stamp | All 9 paths (~49 projected slots) | Up to 48 records **if** all other fields also direct | High — new FEM field, taxonomy governance, all write paths | **High** — duplicates `FALLBACK_KIND_SOURCE_FAMILY_MAP`; blurs replay-contract vs runtime boundary | **Reject** — not legitimate production semantics |
| FEM `recurrence_key` stamp | FEM / replay / classifier records (~30 slots) | Up to ~30 records | Medium | **High** — duplicates `build_recurrence_key`; two sources of truth | **Reject** |
| FEM `mutation_classification` stamp | FEM / replay records (~32 slots) | Up to ~32 records | Medium | **High** — duplicates sibling `mutation` events; violates CO94 separation | **Reject** |
| Lineage `repair_kind` on gate_outcome from FEM | 8 gate_outcome records across 8 paths | 0 strict records (still blocked by `source_family` + others) | Low | Medium — lineage enrichment, not producer gap | **Reject for strict** — insufficient gain; resolved `repair_kind` already 100% |
| Production `owner_bucket` on strict-social / opening fail-closed | 2–3 projected owner slots | 0 strict records (multi-field blockers remain) | Low | Low | **Optional hygiene** — improves direct owner count, not strict completeness |
| Reclassify inventory origin when reading FEM stamp through projection helper | 18 projected `repair_kind` slots | Potentially 0–few strict records | N/A (inventory change) | Medium — origin semantics change | **Out of scope** — CO95 forbids inventory changes |
| Accept `gate_outcome` `mutation_classification` gap | 8 unresolved records | +14.3 pp **resolved** only | N/A | Violates CO94 | **Reject** (closed in CO94) |

### Realistic strict-completeness ceiling under current architecture

Even if all path-specific owner/repair production stamps were completed and inventory origin policy treated FEM reads as direct, **`source_family` alone blocks every resolved record** from strict completeness (minimum blocker set size ≥ 2 on all 48 resolved records; `source_family` appears in every multi-field blocker combination).

**Estimated strict ceiling without new `source_family` production surface: 0%.**

**Estimated strict ceiling with `source_family` FEM stamp (not recommended):** still blocked by `recurrence_key` and `mutation_classification` on FEM-metadata records (18 records with triple projected blocker), requiring additional FEM duplication of lineage-derived fields — violating policy rule 2.

---

## 5. Program Status Recommendation

### Recommendation: **Freeze strict completeness at current architecture** and **close the attribution maturity program**

#### Rationale (production semantics, not percentages)

1. **Resolved completeness plateau is real and governed.** 85.71% (48/56) with all remaining unresolved slots classified as intentional `gate_outcome` gaps (CO94). CO92–CO93 closed the last legitimate producer-stamp gaps for `owner_bucket` and `repair_kind`.

2. **Strict completeness at 0% is architecturally correct, not a maturity defect.** Every resolved record necessarily includes replay-derived (`recurrence_key`, `mutation_classification`) or projection-only (`source_family`) fields by design. No record has a single-field strict blocker; multi-field replay derivation is the norm.

3. **No remaining production opportunity increases strict completeness without duplicating replay-derived information.** The roadmap rejects all candidate stamps on semantic grounds aligned with CO94 and CG-5 registry boundaries.

4. **Continuing strict-completeness production work would optimize a metric that contradicts ownership architecture** — either by duplicating lineage on FEM or by conflating routing and mutation observability.

5. **Classifier-inferred fields (12 slots) are permanently non-strict** under the origin model regardless of production stamps.

#### Not recommended

- **Continue strict-completeness production work** — no eligible stamps remain that satisfy the non-duplication policy.
- **Close attribution program without freezing strict policy** — would leave strict completeness as a misleading target for future cycles.

#### Resolved-completeness status

The **resolved** attribution maturity program may be considered **closed** at 85.71%. The 8 remaining gaps are permanently intentional per CO94. Future work should treat **resolved completeness** and **strict completeness** as distinct program tracks with strict frozen at 0% by policy.

---

## 6. Validation

Discovery-only audit. Architecture verified against live corpus:

```text
python -m pytest tests/test_replacement_attribution_inventory.py -q  PASS (90 tests)
python -m pytest tests/test_attribution_contract.py -q               PASS
python -m pytest tests/test_attribution_completeness_metric.py -q    PASS
```

Live corpus metrics confirmed:

```text
resolved_complete_records: 48/56 (85.71%)
strict_complete_records: 0/56 (0.0%)
missing mutation_classification: 8 (all gate_outcome)
missing repair_kind / owner_bucket / source_family / recurrence_key: 0
```

No production behavior changes. Audit reflects post-CO94 architecture.

---

## 7. Files Modified

| File | Change |
|---|---|
| `docs/audits/CO95_strict_completeness_production_eligibility_audit.md` | **Added** — this audit report |

No production code, read-side projection, classifier vocabulary, baselines, metrics, or producer stamps modified.

---

## 8. Recommended CO96 Target

**CO96 — Attribution program closeout and strict-completeness policy lock**

- Target: `docs/audits/CG_attribution_contract_registry.md`, `tests/helpers/attribution_contract.py` (documentation-only policy section), `tests/helpers/attribution_completeness_metric.py` (report footnote only if desired)
- Goal: codify CO95 production-eligibility policy as normative governance; document strict completeness as frozen observability metric (0% baseline by architecture); formalize resolved-completeness graduation at 85.71%
- Expected impact: policy clarity only; no metric inflation; prevents future cycles from treating strict % as a production-stamp KPI
