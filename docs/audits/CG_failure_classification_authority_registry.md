# CG-1 — Failure Classification Authority Registry

**Date:** 2026-06-27 (CO98 governance handoff)  
**Scope:** Documentation and reviewer orientation only. No taxonomy rename, classifier behavior change, recurrence-key change, or generated-artifact refresh.

**Governing authority:** `tests/failure_classification_contract.py` — replay-contract-owned classifier vocabulary, row schema, dashboard evidence manifest, and repair-kind **runtime/producer subsets**. Classification **behavior** is owned by `tests/helpers/failure_classifier.py`.

**Program status:** **CG failure-classification governance program — closed** (CG-7, 2026-06-25). Taxonomy authority is documented and independently governed. **Recurrence operational graduation** is a separate track — **not graduated** per [`BQC4_final_graduation_decision.md`](BQC4_final_graduation_decision.md). **Attribution maturity program — closed** per [`CO96_attribution_program_closeout.md`](CO96_attribution_program_closeout.md); see [`CG_attribution_contract_registry.md`](CG_attribution_contract_registry.md) (CO97 sync).

**Related:**

- [`CG_failure_classification_cost_closeout.md`](CG_failure_classification_cost_closeout.md) (CG-7 program closeout — **CG governance authority narrative**)
- [`BQC4_final_graduation_decision.md`](BQC4_final_graduation_decision.md) (recurrence operational graduation verdict — **not** taxonomy graduation)
- [`BQ16_recurrence_graduation_audit.md`](BQ16_recurrence_graduation_audit.md) (recurrence graduation audit inputs)
- [`CO96_attribution_program_closeout.md`](CO96_attribution_program_closeout.md) (closed attribution program — separate from CG-1)
- [`CG_attribution_contract_registry.md`](CG_attribution_contract_registry.md) (CG-5 attribution boundary; CO97 synchronized with CO96)
- [`CG_recurrence_taxonomy_registry.md`](CG_recurrence_taxonomy_registry.md) (CG-4 recurrence taxonomy)
- [`CG_failure_classification_synchronization_discovery.md`](CG_failure_classification_synchronization_discovery.md) (CG discovery baseline)

## Purpose

Failure classification is intentionally partitioned across multiple authorities. This registry records **which file owns each concept**, which files **derive or consume** it, and what **change cost** to expect (fixtures, generated artifacts, recurrence identity).

Use this document before editing any failure-classification vocabulary, recurrence analytics class, or cross-layer contract.

**Do not conflate programs:** CG-1 governs classifier taxonomy and replay-contract vocabulary. CO96 governs attribution completeness (closed). BQC4 governs recurrence **operational** graduation readiness (open constraints documented below).

## Failure-classification governance (CO98)

| Item | Value | Authority |
|---|---|---|
| CG governance program status | **Closed** (CG-7) | [`CG_failure_classification_cost_closeout.md`](CG_failure_classification_cost_closeout.md) |
| Classifier vocabulary authority | `tests/failure_classification_contract.py` | This registry §Field-level |
| Classifier behavior authority | `tests/helpers/failure_classifier.py` | Rule tables, row builder, investigation overrides |
| Producer repair-kind subset authority | `tests/failure_classification_contract.py` (`ALLOWED_PRODUCER_REPAIR_KINDS`, 10 kinds) | Runtime FEM stamps; union validation in `attribution_contract` |
| Runtime repair-kind / response-type subsets | `tests/failure_classification_contract.py` | `ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS`, `LEGACY_RESPONSE_TYPE_REPAIR_KINDS` |
| Repair-kind full union + aliases | `tests/helpers/attribution_contract.py` | Attribution program closed (CO96); edit both layers for new producer kinds |
| Source-family tag authority | `tests/failure_classification_contract.py` (`ALLOWED_SOURCE_FAMILY_TAGS`, 21 tags) | Classifier routing; attribution validates imported set |
| Emission sublayer authority | `tests/failure_classification_contract.py` (`ALLOWED_EMISSION_SUBLAYERS`) | Classifier `mutation_source` / `emission_sublayer` evidence |
| Recurrence operational graduation | **Not graduated** (`program_graduated: false`) | BQC4 / BQ16; builder in `replay_bug_recurrence_serialization.py` |
| Attribution maturity program | **Closed** (separate) | CO96 — does not block CG-1 independence |

### Production vs replay vs classifier boundaries

| Layer | Owns | Consumes from replay contract |
|---|---|---|
| **Production (runtime FEM)** | Owner bucket strings, producer repair stamps, split-owner tokens | Contract **mirrors** bucket allowed sets; does not own category/severity taxonomy |
| **Replay projection** | Lineage event emission (`game/final_emission_replay_projection.py`) | Validates against repair subsets and projection parity via sync matrix |
| **Failure classifier** | Row construction from drift observations | **Must** conform to `failure_classification_contract` allowed values |
| **Attribution inventory** | Five-field completeness records (program closed) | Imports source families, repair subsets, emission sublayers from failure contract |

### Architectural constraints (not backlog)

1. **Repair kind split** — failure contract owns runtime/producer **subsets**; attribution contract owns **union** — both must change together for new producer kinds (not attribution maturity work; CO96 closed).
2. **Recurrence operational immaturity** — BQC4 verdict C: insufficient protected-replay volume and trajectory for operational graduation; does not imply classifier taxonomy is incomplete.
3. **`recurrence:v1` path mutability** — investigation target and field_path participate in recurrence identity; documentation-only renames are key migrations.
4. **Dual mutation vocabulary** — classifier `emission_sublayer` vs lineage `mutation_kind`; attribution union accepts both (CO94 `gate_outcome` constraint is attribution/lineage, not classifier vocabulary).
5. **Attribution strict completeness** — frozen at 0% by architecture (CO95–CO96); unrelated to failure-classification taxonomy graduation.

## Authority kinds

| Kind | Meaning |
|---|---|
| **replay-contract-owned** | Test-side replay failure row contract; allowed values and row schema |
| **runtime-owned** | Production runtime vocabulary (FEM ownership, metadata, read views) |
| **attribution-contract-owned** | BS3 semantic replacement attribution unions, paths, aliases, normalization |
| **recurrence-owned** | Recurrence identity, input/summary status, and analytical classifications |
| **dashboard-owned** | Dashboard display manifest and rendering (derived from contract) |
| **generated/derived** | Checked-in artifacts, matrix reports, or values computed from an upstream authority |

## Field-level authority registry

Columns: **Authority file** (single owner) · **Derived/consumer files** · **Kind** · **Fixtures?** · **Generated refresh?** · **Recurrence identity?**

### Core failure row taxonomy

| Concept | Authority file | Derived / consumer files | Kind | Fixtures | Generated | Recurrence identity |
|---|---|---|---|:---:|:---:|:---:|
| **failure category** | `tests/failure_classification_contract.py` (`ALLOWED_FAILURE_CATEGORIES`) | `tests/helpers/failure_classifier.py` (`CATEGORY_RULES`, row builder), `tests/helpers/failure_classification_sync.py` (alignment asserts), `tests/helpers/failure_dashboard_report.py` (display), `tests/helpers/replay_drift_taxonomy.py` (drift bucket mapping), `tests/helpers/replay_bug_recurrence_events.py` (key component) | replay-contract-owned | yes | no | **yes** — `category` in `recurrence:v1` |
| **primary owner** | `tests/failure_classification_contract.py` (`ALLOWED_PRIMARY_OWNERS`) | `tests/helpers/failure_classifier.py` (`PRIMARY_OWNER_RULES`, validation), sync helpers, dashboard columns, `tests/helpers/replay_bug_recurrence_events.py` (`recurrence_owner` fallback) | replay-contract-owned | yes | no | indirect — not in v1 key; review if primary→drift mapping changes |
| **secondary owner** | `tests/failure_classification_contract.py` (`ALLOWED_SECONDARY_OWNERS`) | `tests/helpers/failure_classifier.py` (`SECONDARY_OWNER_RULES`), dashboard columns, optional row evidence | replay-contract-owned | yes | no | no |
| **owner drift bucket** | `tests/helpers/replay_drift_taxonomy.py` (`ALLOWED_OWNER_DRIFT_BUCKETS`, `classify_owner_drift_bucket`) | `tests/failure_classification_contract.py` (re-export for contract consumers), `tests/helpers/failure_classifier.py` (row field + validation), sync/matrix fixtures, all recurrence modules (key prefix), drift report helpers | replay-contract-owned (allowed set mirrored in contract) / drift taxonomy authority | yes | drift reports if bucket labels exposed | **yes** — first component of `recurrence:v1` |
| **source family** | `tests/failure_classification_contract.py` (`ALLOWED_SOURCE_FAMILY_TAGS`) | `tests/helpers/failure_classifier.py` (rule routing), `tests/helpers/attribution_contract.py` (union validation), attribution inventory/tests | replay-contract-owned | yes | no | no |
| **repair kind** | Split: runtime kinds in `tests/failure_classification_contract.py` (`ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS`, `ALLOWED_PRODUCER_REPAIR_KINDS` [10 kinds incl. `passive_scene_pressure_fallback`], `LEGACY_RESPONSE_TYPE_REPAIR_KINDS`); full union + aliases in `tests/helpers/attribution_contract.py` (`ALLOWED_REPAIR_KINDS`, `REPAIR_KIND_ALIASES`) | Classifier optional evidence, `game/final_emission_replay_projection.py` (lineage emission), sync split-owner matrix, attribution inventory (CO96 closed) | replay-contract-owned (runtime/producer subsets); attribution-contract-owned (union) | yes | no | no |
| **mutation classification** | `tests/helpers/attribution_contract.py` (`ALLOWED_MUTATION_CLASSIFICATION_CORE`, `ALLOWED_MUTATION_CLASSIFICATIONS`, `MUTATION_CLASSIFICATION_ALIASES`); emission sublayers imported from `tests/failure_classification_contract.py` (`ALLOWED_EMISSION_SUBLAYERS`) | Classifier `mutation_source`/sublayer evidence, `game/final_emission_replay_projection.py`, replacement attribution inventory | attribution-contract-owned | yes | no | no |
| **investigation target** | Split: default map in `tests/failure_classification_contract.py` (`MAJOR_OWNER_INVESTIGATION_TARGETS`); per-category overrides in `tests/helpers/failure_classifier.py` (`INVESTIGATION_TARGETS`, builder logic); drift fixtures in `tests/helpers/replay_drift_taxonomy.py` (`*_INVESTIGATION_TARGET`) | Dashboard **Investigate First** column, sync exact-string tests, `tests/helpers/replay_bug_recurrence_events.py` (key component) | replay-contract-owned defaults; classifier-owned behavioral overrides | yes | no | **yes** — `investigate_first` in `recurrence:v1`; path changes are key migrations |
| **dashboard evidence field** | `tests/failure_classification_contract.py` (`FAILURE_DASHBOARD_EVIDENCE_MANIFEST`, labels/row keys) | `tests/helpers/failure_classification_sync.py` (delegating accessors), `tests/helpers/failure_dashboard_report.py` (re-export + render), contract/dashboard tests | dashboard-owned (manifest authority in contract) | yes (evidence cell strings) | dashboard markdown if checked in | no |
| **protected evidence path** | `tests/helpers/golden_replay_projection.py` (`protected_observation_field_paths`, registry in `golden_replay_projection_fields.py`) | `tests/failure_classification_contract.py` (`PROTECTED_CLASSIFIER_EVIDENCE_FIELDS` derived overlap), classifier direct/computed partition, sync assertions | generated/derived (acceptance observation schema) | yes | golden replay artifacts if paths change | no |

### Runtime ownership vocabulary (consumed by replay contract)

| Concept | Authority file | Derived / consumer files | Kind | Fixtures | Generated | Recurrence identity |
|---|---|---|---|:---:|:---:|:---:|
| **fallback owner buckets** (opening/sealed/visibility) | `game/final_emission_ownership_schema.py` (bucket string values) + `game/final_emission_owner_bucket_views.py` (mappers) | `game/attribution_read_views.py` (read facade re-export), `game/final_emission_meta.py` (FEM packaging registries), `tests/failure_classification_contract.py` (allowed-set aliases), classifier validation, sync split-owner matrix | runtime-owned | yes (matrix rows) | BU15 matrix doc if regenerated | indirect via `owner_drift_bucket` only |
| **split selection/content owners** | `game/final_emission_ownership_schema.py` | `game/attribution_read_views.py`, `game/final_emission_replay_projection.py`, sync matrix, classifier optional fields | runtime-owned | yes | matrix doc | no |

### Attribution contract

| Concept | Authority file | Derived / consumer files | Kind | Fixtures | Generated | Recurrence identity |
|---|---|---|---|:---:|:---:|:---:|
| **attribution replacement path** | `tests/helpers/attribution_contract.py` (`REPLACEMENT_PATHS`, individual `REPLACEMENT_PATH_*`) | Replacement attribution inventory, lineage projection labels, inventory tests | attribution-contract-owned | yes | inventory reports | no |
| **attribution alias / normalization value** | `tests/helpers/attribution_contract.py` (`REPAIR_KIND_ALIASES`, `MUTATION_CLASSIFICATION_ALIASES`, `DEPRECATED_FALLBACK_KIND_ALIASES`, `normalize_*` helpers) | Attribution validator, inventory compliance checks | attribution-contract-owned | yes | no | no |

### Recurrence

| Concept | Authority file | Derived / consumer files | Kind | Fixtures | Generated | Recurrence identity |
|---|---|---|---|:---:|:---:|:---:|
| **recurrence identity key** | `tests/helpers/replay_bug_recurrence_events.py` (`build_recurrence_key`, schema version constant) | `tests/helpers/attribution_contract.py` (shape validation), event/history artifacts, recurrence tests, `tests/helpers/replay_bug_recurrence.py` facade re-export | recurrence-owned | yes (exact-key tests) | `artifacts/golden_replay/bug_recurrence_*.json\|md` | **defines identity** |
| **recurrence input status** | `tests/helpers/replay_bug_recurrence_events.py` (`ALLOWED_RECURRENCE_STATUSES`: `active`, `retired`) | Event log writers, row projection, history aggregation | recurrence-owned | yes | event log artifacts | no (status not in v1 key) |
| **recurrence summary status** | `tests/helpers/replay_bug_recurrence_events.py` (`SUMMARY_RECURRENCE_STATUSES`, `classify_recurrence_status`) | History summaries, dashboard recurrence renderer, JSON/MD artifacts | recurrence-owned | yes | history artifacts | no |
| **recurrence trend class** | `tests/helpers/replay_bug_recurrence_history.py` (`RECURRENCE_TREND_CLASSIFICATIONS`, `classify_recurrence_trend_entry`) | `tests/helpers/replay_bug_recurrence_statistics.py` (cross-maps), serialization renderer, trajectory artifacts | recurrence-owned | yes | history/report artifacts | no |
| **recurrence forecast class** | `tests/helpers/replay_bug_recurrence_history.py` (`RECURRENCE_FORECAST_CLASSIFICATIONS`, classifier functions) | Statistics alignment maps, serialization, recurrence tests | recurrence-owned | yes | artifacts | no |
| **recurrence remediation-cost class** | `tests/helpers/replay_bug_recurrence_history.py` (`RECURRENCE_REMEDIATION_COST_CLASSIFICATIONS`, `classify_remediation_cost`) | Statistics ROI/remediation summaries, serialization | recurrence-owned | yes | artifacts | no |
| **recurrence governance status** | `tests/helpers/replay_bug_recurrence_history.py` (`RECURRENCE_GOVERNANCE_STATUSES`, `classify_recurrence_governance_status`) | Watchlist rendering, statistics funnel metrics, serialization | recurrence-owned | yes | artifacts | no |
| **recurrence lifecycle stage** | `tests/helpers/replay_bug_recurrence_history.py` (`RECURRENCE_LIFECYCLE_STAGES`, `classify_recurrence_lifecycle_stage`) | Statistics effectiveness/graduation maps, serialization | recurrence-owned | yes | artifacts | no |

### Governance / sync hub (not taxonomy authority)

| Path | Role |
|---|---|
| `tests/helpers/failure_classification_sync.py` | Compatibility re-export facade (CG-2); orchestrates focused sync modules below |
| `tests/helpers/failure_classification_alignment.py` | Contract/classifier parity, schema validation, manifest locks — **validates** authorities |
| `tests/helpers/failure_classification_builders.py` | Synthetic observed rows and drift-row builders — **derives** test data only |
| `tests/helpers/failure_classification_split_owner.py` | Split-owner acceptance matrix rows, FEM projection, matrix assertions — **owns** matrix generation |
| `tests/helpers/failure_classification_dashboard_expectations.py` | Expected dashboard rows, case-id parity, row-shape checks — **owns** presentation expectations |
| `tests/helpers/failure_dashboard_report.py` | Renders classified rows; **displays** contract-owned evidence manifest via sync delegators |
| `tests/helpers/replay_bug_recurrence.py` | Compatibility facade; **mirrors** focused recurrence modules |
| `tests/helpers/replay_bug_recurrence_statistics.py` | Analytics consumer; owns program-effectiveness policy constants, **derives** trend/forecast/lifecycle classifications |
| `tests/helpers/replay_bug_recurrence_serialization.py` | Report serialization; owns confidence/graduation/blind-spot statuses; **derives** history/statistics taxonomies |

## Recurrence v1 identity (key-sensitive fields)

**Authoritative builder:** `tests/helpers/replay_bug_recurrence_events.py` → `build_recurrence_key`

**Format:**

```text
recurrence:v1:<owner_bucket>|<category>|<field_path>|<investigate_first>
```

**Identity components (all four are key-sensitive today):**

| Component | Source field | Upstream authority |
|---|---|---|
| `owner_bucket` | `owner_drift_bucket` on classification row | `tests/helpers/replay_drift_taxonomy.py` |
| `category` | `category` | `tests/failure_classification_contract.py` |
| `field_path` | `field_path` | Classifier row builder (drift observation path) |
| `investigate_first` | `investigate_first` | Contract defaults + classifier overrides |

**Migration rule:** Any change to these four values for an existing bug class creates a **new recurrence key** unless a dedicated backfill/migration tool is run. Treat `investigate_first` path renames as key migrations even when they look documentation-only.

**Not in v1 identity:** `primary_owner`, `recurrence_status` / summary status, trend/forecast/governance/lifecycle classes, dashboard evidence fields.

**Future note:** A hypothetical `recurrence:v2` could remove mutable paths from identity; that is **out of scope** for CG-1.

## Derived imports and re-exports

| Import edge | Receiving file role | Relationship |
|---|---|---|
| `game.attribution_read_views` → `tests/failure_classification_contract.py` | **Validates** + **mirrors** runtime fallback bucket/owner registries into replay allowed sets | Contract does not own bucket strings; re-exports for classifier consumers |
| `tests.helpers.replay_drift_taxonomy.ALLOWED_OWNER_DRIFT_BUCKETS` → `tests/failure_classification_contract.py` → `tests/helpers/failure_classifier.py` | Contract **mirrors for compatibility**; classifier **validates** row values | Drift taxonomy remains authority |
| `tests.helpers.golden_replay_projection.protected_classifier_evidence_field_paths` → `tests/failure_classification_contract.py` | Contract **derives** `PROTECTED_CLASSIFIER_EVIDENCE_FIELDS` | Projection registry is authority |
| `tests.failure_classification_contract` repair-kind subsets → `tests/helpers/attribution_contract.py` | Attribution **owns union**; failure contract **owns runtime/producer subsets** | Edit both layers when adding repair kinds |
| `tests.failure_classification_contract.ALLOWED_EMISSION_SUBLAYERS` → `tests/helpers/attribution_contract.py` | Attribution **extends** mutation union | Emission sublayers authority stays in failure contract |
| `tests.failure_classification_contract.ALLOWED_SOURCE_FAMILY_TAGS` → `tests/helpers/attribution_contract.py` | Attribution **validates** against imported set | Source-family authority in failure contract |
| `tests.helpers.failure_classification_sync.failure_dashboard_evidence_*` → `tests/helpers/failure_dashboard_report.py` | Report **displays**; sync **delegates** to contract manifest | Manifest authority in failure contract |
| `tests.failure_classification_contract.FAILURE_DASHBOARD_EVIDENCE_*` re-import in dashboard report | Report module-level constants **mirror for compatibility only** | Do not edit manifest here |
| `tests.helpers.replay_drift_taxonomy.ALLOWED_OWNER_DRIFT_BUCKETS` → recurrence modules | Recurrence **validates** owner bucket component of key | Drift taxonomy authority |
| `tests.helpers.replay_bug_recurrence_events` → `history` / `statistics` / `serialization` / facade | Downstream modules **consume** and **re-export** via `import *` for compatibility | Event module owns identity/status vocabulary |
| `game.final_emission_replay_projection` lineage constants → `tests/helpers/failure_classification_sync.py` | Sync matrix **validates** projection parity with split-owner rows | Runtime projection emits; sync tests alignment |

## Change checklist (by concept type)

| If you change… | Review / edit… | Refresh artifacts? |
|---|---|---|
| Failure category or owner | Contract, classifier rules/maps, sync alignment, targeted fixtures/tests | Dashboard output only if columns change |
| Owner drift bucket | `replay_drift_taxonomy.py`, contract mirror, classifier, **recurrence key migration plan** | Drift/recurrence artifacts |
| Investigation target path | Contract map, classifier overrides, exact-string tests, **recurrence migration** | Possibly dashboard markdown |
| Dashboard evidence manifest | Contract manifest only (+ sync/report re-exports follow automatically) | Controlled failure evidence strings |
| Protected observation path | `golden_replay_projection` registry, derived contract overlap, classifier partition | Golden replay artifacts |
| Runtime owner bucket | `final_emission_ownership_schema`, projection, contract aliases, split-owner matrix | BU15 matrix doc via refresh tool |
| Repair kind / mutation class | Producer/runtime source, failure contract subset, attribution union/aliases | Attribution inventory |
| Recurrence analytical class | `replay_bug_recurrence_history.py` (+ statistics maps, serialization labels) | `bug_recurrence_history.*` artifacts |
| Recurrence key formula | `replay_bug_recurrence_events.py`, migration tools, all exact-key tests | All recurrence JSON/MD artifacts |

## Authority file index

| File | Owns |
|---|---|
| `tests/failure_classification_contract.py` | Failure categories, owners, severities, tags, source families, row schema, dashboard evidence manifest, investigation defaults, repair-kind subsets |
| `tests/helpers/failure_classifier.py` | Classification **behavior** (rules, routing, row construction); investigation overrides |
| `tests/helpers/replay_drift_taxonomy.py` | Owner drift buckets and drift classification logic |
| `tests/helpers/golden_replay_projection.py` | Protected observation paths and acceptance projection |
| `tests/helpers/attribution_contract.py` | Replacement paths, repair/mutation unions, aliases, normalization |
| `tests/helpers/replay_bug_recurrence_events.py` | Recurrence key, input/summary status vocabulary, event log contract |
| `tests/helpers/replay_bug_recurrence_history.py` | Trend, forecast, remediation-cost, governance, lifecycle classifications |
| `game/final_emission_ownership_schema.py` | Canonical split-owner and bucket string values |
| `game/attribution_read_views.py` | Read-side re-export facade (no new authority) |
| `game/final_emission_meta.py` | FEM shapes and runtime registry consumption |
| `game/final_emission_replay_projection.py` | Runtime lineage read projection (diagnostic vocabulary emission) |

## Remaining cross-contract dependencies (architectural, not open programs)

| Dependency | Direction | Change cost |
|---|---|---|
| Repair subsets → attribution union | failure contract → attribution | Edit both for new producer kinds |
| Emission sublayers → mutation union | failure contract → attribution | Edit both for new sublayer evidence |
| Runtime buckets → owner validation | ownership schema → failure contract mirror → attribution | Edit schema + contract mirror |
| Projection maps → mutation union | replay projection emits; attribution validates | Align maps when adding core mutation tokens |
| Classifier evidence → inventory | classifier rows → inventory `classifier_inferred` origin | Fixture + inventory tests |
| CO96 attribution closeout → CG-1 | Independent programs | Attribution changes do not require reopening CG-1 |
| BQC4 recurrence graduation → CG-1 | Separate operational track | Recurrence maturity gaps are not classifier taxonomy backlog |

## CG-2 synchronization module layout

**Date:** 2026-06-25  
**Change:** `failure_classification_sync.py` split into purpose-focused modules. Existing import sites continue to use `failure_classification_sync` as a compatibility facade.

| Module | Responsibility | Approx LOC |
|---|---|---:|
| `tests/helpers/failure_classification_sync.py` | Compatibility `import *` re-exports + high-level orchestration assertions | 30 |
| `tests/helpers/failure_classification_alignment.py` | Contract/classifier parity, TypedDict schema locks, evidence-manifest validation | 423 |
| `tests/helpers/failure_classification_builders.py` | Synthetic observed rows, drift-row helpers, `classify_replay_probe_row` | 737 |
| `tests/helpers/failure_classification_split_owner.py` | `SPLIT_OWNER_ACCEPTANCE_MATRIX`, FEM projection, matrix contract/report | 1,011 |
| `tests/helpers/failure_classification_dashboard_expectations.py` | Dashboard expected dicts, controlled-failure case tuples, case-id parity | 198 |

**Import fan-in:** ~20 external call sites still import from `failure_classification_sync.py` (unchanged). New modules are imported only internally plus the sync facade.

**Largest remaining sync file:** `failure_classification_split_owner.py` (matrix data + projection helpers).

**Generated artifact touched:** `docs/audits/BU15_split_owner_acceptance_matrix.md` footer path updated (`failure_classification_split_owner.py` canonical source).

## CG-3 dashboard fixture decoupling

**Date:** 2026-06-25  
**Change:** Controlled dashboard probes distinguish classifier behavior probes from presentation goldens. Repeated classifier routing literals removed from fixtures; routing expected values derived from ``classify_replay_probe_row``.

### Case groups (36 controlled probes)

| Group | Count | Where | Assertion style |
|---|---:|---|---|
| **A — behavior probes** | 36 | `failure_dashboard_fixtures.py` probe tuples + split-owner matrix probes | Routing fields derived via ``derive_classifier_routing_expected``; split-owner owner literals validated via ``assert_split_owner_matrix_dashboard_expected(row, classified_row)`` against matrix |
| **B — presentation goldens** | 36 evidence cells + 1 report shape test | `tests/test_failure_dashboard_controlled_failures.py` | Explicit ``_CONTROLLED_PROBE_EVIDENCE_CELLS`` strings; markdown report substring locks |
| **C — compatibility probes** | 4 surfaces | Export parity tests, empty ``SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES``, ``record_selected_speaker_protected_failure``, ``expected_failure_classification_row_fields`` re-export | Unchanged import paths and historical guards |

### Explicit goldens preserved

- All 36 ``_CONTROLLED_PROBE_EVIDENCE_CELLS`` evidence strings (unchanged).
- ``test_controlled_failure_probe_dashboard_contains_triage_columns`` report shape/substring locks.
- Protected replay / rerun / recurrence report section tests in ``test_failure_dashboard_report.py``.
- Split-owner matrix owner literals (BU15) via matrix row assertions, not duplicated dashboard dict literals.

### Derived expectations

- ``CLASSIFIER_ROUTING_FIELD_KEYS``: ``category``, ``primary_owner``, ``secondary_owner``, ``severity``, ``investigate_first``.
- ``derive_classifier_routing_expected`` / ``controlled_failure_probe_case``: build 4-tuple cases from classifier output.
- ``split_owner_matrix_dashboard_expected_dict``: compatibility wrapper delegating to derive (replaces ~60 lines of manual literals).
- ``assert_classifier_routing_parity``: dashboard vs classifier path wiring check in probe test.

### Failure Classification Cost reduction

When classifier routing rules change, editors update ``failure_classifier.py`` and ``test_failure_classifier.py`` canonical cases once. Dashboard probe fixtures no longer require synchronized manual edits to 21+ per-case expected dicts; only presentation goldens (evidence cells) need explicit updates when dashboard *rendering* changes.

### Intentionally left duplicated

- ``_CONTROLLED_PROBE_EVIDENCE_CELLS`` — display contract; must stay explicit.
- ``test_failure_classifier.py`` canonical failure tuples — classifier behavior authority.
- Observed-row + drift-row literals in probe tuples — scenario inputs, not classifier outputs.
- ``SPLIT_OWNER_ACCEPTANCE_MATRIX`` rows — split-owner acceptance authority (BU15).

### Remaining dashboard fixture hotspots

- ``tests/test_failure_dashboard_controlled_failures.py`` — presentation golden dict (~150 LOC evidence cells) and report substring test.
- ``tests/helpers/failure_classification_split_owner.py`` — matrix data + FEM projection (~1,011 LOC).
- ``tests/helpers/failure_classification_builders.py`` — synthetic observed/drift builders (~737 LOC).

## CG-4 recurrence taxonomy clarification

**Date:** 2026-06-25  
**Change:** Explicit recurrence taxonomy registry; module authority headers updated; one import narrowed to authority modules.

**Registry:** [`CG_recurrence_taxonomy_registry.md`](CG_recurrence_taxonomy_registry.md)

**Summary:** 20 taxonomy families across 4 authority modules (`events`, `history`, `statistics`, `serialization`). Display consumers (`failure_dashboard_recurrence.py`, `replay_bug_recurrence.py` facade) documented as non-owners. Cross-taxonomy pairs (trend vs lifecycle, input vs summary status, governance vs graduation, confidence vs outcome) explicitly distinguished.

## CG-5 attribution contract boundary tightening

**Date:** 2026-06-25 (updated CO97 / CO98)  
**Change:** Explicit attribution contract registry; module authority headers updated to distinguish **imports**, **validation**, **normalization**, **compatibility**, and **runtime emission**; no behavioral changes.

**Registry:** [`CG_attribution_contract_registry.md`](CG_attribution_contract_registry.md) — **CO97 synchronized** with [`CO96_attribution_program_closeout.md`](CO96_attribution_program_closeout.md) (attribution program **closed**).

**Summary:**

| Boundary | Failure classification owns | Attribution owns | Runtime owns |
|---|---|---|---|
| Repair vocabulary | Runtime/producer/legacy **subsets** | **Union**, aliases, opening kinds, validation | FEM/lineage **stamps** |
| Mutation vocabulary | Emission **sublayers** (classifier evidence) | Core **union**, aliases, assembled validation set | `mutation_kind` **emission** + projection maps |
| Owner buckets | Mirror for classifier validation | Validation union for records | Canonical **strings** + mappers |
| Source family | Allowed **tag set** | Validates imported set | Projection **derives** from `fallback_kind` |
| Replacement semantics | — | **Paths**, record shape, origins (program closed) | FEM flags as inputs only |

**Governance snapshot (attribution — see CG-5 registry for current):** 18 vocabulary families · attribution program **closed** · resolved completeness 85.71% · strict completeness diagnostic-only at 0% · 8 intentional `gate_outcome` gaps (CO94).

**Intentional overlaps preserved:** repair-kind split, dual mutation vocabulary (`mutation_kind` vs `emission_sublayer`), lineage-only repair kinds outside BS3 union.

**Relationship to CG-1:** Failure classification taxonomy authority is **independent** of the closed attribution maturity program. CG-1 remains authoritative for classifier vocabulary; CO96 is authoritative for attribution completeness policy only.

**Files touched (comments/docs only):** `attribution_contract.py`, `replacement_attribution_inventory.py`, `failure_classification_contract.py`, `final_emission_replay_projection.py`, `final_emission_ownership_schema.py`, `attribution_read_views.py`, `final_emission_meta.py`, `CG_attribution_contract_registry.md`, this section.

## CG-7 failure classification cost closeout

**Date:** 2026-06-25  
**Change:** Final maintenance-economics measurement; no code or taxonomy changes.

**Closeout:** [`CG_failure_classification_cost_closeout.md`](CG_failure_classification_cost_closeout.md)

**Verdict:** **IMPROVED_GOVERNANCE** — Failure Classification Cost is now measurable; sync hub largest module −59%; dashboard fixtures −44%; routing edit fanout reduced ~40–50% for classifier-only changes; total governance LOC +7% due to explicit module boundaries and registries.

**Audit status:** CG program **formally closed**. Taxonomy synchronization remains a hotspot but is documented with named owners. No architectural blocker before feature development.

**CO98 handoff:** CG-1 registry updated to cross-reference CO96/CO97 (closed attribution) and BQC4 (recurrence operational graduation not met). Failure-classification governance stands independently.
