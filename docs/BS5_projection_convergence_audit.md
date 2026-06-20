# BS5 — Projection Convergence Audit

Audit date: 2026-06-20

Scope: read-side projection and classifier convergence only. No runtime producers, FEM schemas, fallback selection, or replacement execution changed.

Validation:

```powershell
pytest tests/test_replacement_attribution_inventory.py tests/test_final_emission_meta.py tests/test_failure_classifier.py tests/test_runtime_lineage_telemetry.py -q
```

Result: **159 passed**

Comparison artifact: `artifacts/bs5_projection_convergence_report.md`

---

## 1. Taxonomy Collapse Inventory (Pre-BS5)

| Source path | Collapsed value | Lost attribution fields |
|---|---|---|
| Visibility hard replace (`visibility_replacement_applied`) | `visibility_or_scene_replacement` | path-specific `fallback_kind`, path-specific mutation class, distinct recurrence identity |
| First-mention hard replace | `visibility_or_scene_replacement` | owner bucket (not propagated to lineage), repair kind, path-specific mutation |
| Referential hard replace | `visibility_or_scene_replacement` | same as first-mention |
| Referential local substitution | _(no fallback event)_ | mutation classification, repair kind, owner bucket |
| Generic repair-layer flags (11 FEM flags) | `repair_only_mutation` | per-layer repair kind, per-layer mutation class |
| FEM lineage token `fallback_behavior_repair` | `repair_only_mutation` | `fallback_behavior_repair_mutation` |
| All fallback selections (mutation sidecar) | `fallback_mutation` | path-specific mutation class for visibility/first-mention/referential/sealed |
| Opening / sealed / visibility lineage | `fallback_owner_bucket=None` on lineage | direct owner bucket despite FEM stamps |
| Response-type / strict-social lineage | `repair_kind` omitted on `fallback_selected` | repair kind despite FEM `response_type_repair_kind` |
| Classifier rows | category heuristics | lineage `source_family`, recurrence key, preserved owner bucket |
| Unknown sealed terminal | `sealed_unknown_replacement` | subkind only; repair kind still absent (producer gap) |

---

## 2. BS5 Convergence Changes

### 2.1 Path-specific fallback kinds (`game/final_emission_replay_projection.py`)

Replaced collapsed bucket with deterministic kinds:

| FEM evidence | New `fallback_kind` | New `gate_path` |
|---|---|---|
| `visibility_replacement_applied` | `visibility_hard_replacement` | `visibility_hard_replaced` |
| `first_mention_replacement_applied` | `first_mention_hard_replacement` | `first_mention_hard_replaced` |
| `referential_clarity_replacement_applied` | `referential_clarity_hard_replacement` | `referential_clarity_hard_replaced` |

Legacy token `visibility_or_scene_replacement` retained in read-side maps for backward-compatible ingestion only.

### 2.2 Owner bucket preservation

`_fem_preserved_fallback_owner_bucket()` copies existing FEM stamps onto lineage `fallback_owner_bucket`:

- `visibility_fallback_owner_bucket`
- `sealed_fallback_owner_bucket`
- opening bucket via existing `opening_fallback_owner_bucket_from_meta()` (pre-existing projection rule)

No new bucket synthesis added.

### 2.3 Repair kind preservation

`_fem_preserved_repair_kind()` passes FEM `response_type_repair_kind` through to lineage `fallback_selected.repair_kind`.

Classifier `_repair_kind()` now prefers lineage repair kind before heuristic backfill.

### 2.4 Mutation classification fidelity

Path-specific mutation kinds on fallback sidecar events:

| Trigger | New `mutation_kind` |
|---|---|
| Visibility hard replace | `visibility_replacement_mutation` |
| First-mention hard replace | `first_mention_replacement_mutation` |
| Referential hard replace | `referential_clarity_replacement_mutation` |
| Referential local substitution | `referential_clarity_local_substitution_mutation` |
| Sealed subkind fallback | `sealed_replacement_mutation` |
| Each repair-layer flag | `{flag}_repair_mutation` (e.g. `fallback_behavior_repair_mutation`) |

Deterministic maps exported:

- `FALLBACK_KIND_SOURCE_FAMILY_MAP`
- `FALLBACK_KIND_MUTATION_CLASSIFICATION_MAP`
- `project_source_family_from_fallback_kind()`
- `project_mutation_classification_from_fallback_kind()`

### 2.5 Classifier convergence (`tests/helpers/failure_classifier.py`)

Read-side helpers consume projected lineage when present:

- `_source_family_from_lineage()` — prefers projected family over category heuristics
- `_preserved_owner_bucket_from_lineage()` — opening bucket from lineage
- `_repair_kind_from_lineage()` — repair kind from fallback/speaker events
- `_mutation_classification_from_lineage()` — mutation kind from mutation events

### 2.6 Inventory convergence (`tests/helpers/replacement_attribution_inventory.py`)

- Extended mutation taxonomy for path-specific kinds
- Lineage records project mutation class from `fallback_kind` when mutation event is separate
- Failure classification records consume `observed_turn.fem_runtime_lineage_events` for recurrence and owner bucket
- BS5 before/after report generator with BS1 snapshot comparison

---

## 3. Completeness Impact

| Metric | Before (BS1) | After (BS5) | Delta |
|---|---:|---:|---:|
| Strict completeness | 0.0% | 0.0% | 0.0 |
| Resolved completeness | 5.77% | 10.2% | **+4.43 pp** |
| Resolved complete records | 3/52 | 5/49 | **+2** |

### Field-level slots recovered

| Field | Missing before | Missing after | Recovered |
|---|---:|---:|---:|
| `owner_bucket` | 43 | 38 | 5 |
| `repair_kind` | 44 | 37 | 7 |
| `recurrence_key` | 5 | 0 | **5** |
| `mutation_classification` | 16 | 8 | **8** |
| `source_family` | 8 | 8 | 0 |

### Path-level resolved complete

| Path | Before | After | Delta |
|---|---:|---:|---:|
| opening fallback | 3 | 5 | +2 |
| all other paths | 0 | 0 | 0 |

Opening fallback improved because lineage + classifier records now inherit repair kind, mutation class, and recurrence from converged projection.

---

## 4. Recurrence Identity Stability

Unchanged for unaffected paths:

- Opening `scene_opening` recurrence key remains `fallback_selected:gate:game.final_emission_gate:scene_opening`

Intentionally changed (path discrimination):

- Visibility recurrence detail token: `visibility_or_scene_replacement` → `visibility_hard_replacement`
- First-mention / referential paths receive distinct detail tokens

Recurrence **algorithm** (`build_recurrence_key` preference order) unchanged in `game/runtime_lineage_telemetry.py`.

---

## 5. Remaining Gaps (Producer-Required)

BS5 closes projection-induced loss only. These fields still require future producer stamps (BS4):

- Universal `repair_kind` for visibility, first-mention, referential, sealed, sanitizer paths
- Owner bucket for first-mention/referential when FEM lacks visibility/sealed stamps
- Sanitizer unified owner bucket

---

## 6. Recommended Next Blocks

| Block | Focus |
|---|---|
| **BS3** | Lock converged taxonomy in contract tests |
| **BS4** | Producer stamps for remaining repair kind / owner bucket gaps |
| **BS6** | Time-to-classify diagnostic (from BS discovery) |
