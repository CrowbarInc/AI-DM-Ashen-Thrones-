# BS2 — Attribution Gap Map

Analysis date: 2026-06-20

Scope: read-side gap mapping only. No runtime fields, FEM schemas, lineage events, replacement logic, or failure classification behavior were changed.

Inputs:

- `artifacts/bs_attribution_baseline_report.md` (BS1 baseline)
- `tests/helpers/replacement_attribution_inventory.py` (canonical inventory + scoring)
- `docs/BS_semantic_replacement_attribution_discovery.md` (BS discovery)

Validation: `pytest tests/test_replacement_attribution_inventory.py -q` → **12 passed**

---

## 1. Executive Summary

BS1 measured **116 missing field slots** across **52 baseline records** (260 total slots; **144 populated**).

| Metric | Value |
|---|---|
| Strict completeness | 0.0% (0/52) |
| Resolved completeness | 5.77% (3/52) |
| Top missing field | `repair_kind` (44 slots) |
| Second | `owner_bucket` (43 slots) |
| Third | `mutation_classification` (16 slots) |

**Key finding:** Every missing field has a nearest authoritative source today — but that source is rarely the same layer that BS1 evaluates. Most gaps are **cross-layer availability** problems (field exists downstream or upstream of the evaluated record), not total absence of evidence.

Population mix among the **144 populated slots**:

| Origin class | Count | Share of populated |
|---|---:|---:|
| DIRECT | 58 | 40.3% |
| PROJECTED | 80 | 55.6% |
| INFERRED / CLASSIFIER_DERIVED | 6 | 4.2% |

**Inference rate** (non-direct among populated): **59.7%**. Completeness today is overwhelmingly projection-driven, not write-time producer-owned.

---

## 2. Methodology

For each missing-field occurrence in the BS1 baseline corpus:

1. Identify **replacement path** and **inventory source kind** (`fem_metadata`, `runtime_lineage_event`, `replay_projection`, `failure_classification`).
2. Ask whether equivalent evidence **already exists elsewhere** in the pipeline (FEM, sanitizer trace, lineage projection, golden replay observation, classifier row).
3. Ask whether the field can be filled **deterministically** without new runtime data.
4. Classify whether a **future producer stamp** is required for strict completeness, or whether projection/inference is sufficient.

Denominator: applied replacement/mutation records only (BS1 baseline corpus). Prepared-but-unused candidates excluded.

---

## 3. Missing-Field Occurrence Analysis (by Replacement Family)

Baseline missing counts per path (from BS1 report + inventory drill-down):

| Replacement path | Records | Missing owner | Missing source | Missing repair | Missing recurrence | Missing mutation |
|---|---:|---:|---:|---:|---:|---:|
| visibility replacement | 5 | 3 | 1 | 5 | 0 | 2 |
| first mention replacement | 5 | 5 | 1 | 5 | 0 | 2 |
| referential replacement | 5 | 5 | 1 | 5 | 0 | 2 |
| sealed replacement | 5 | 3 | 1 | 5 | 0 | 2 |
| response type replacement | 7 | 7 | 1 | 4 | 1 | 2 |
| sanitizer replacement | 7 | 7 | 1 | 7 | 1 | 2 |
| repair mutation | 4 | 4 | 0 | 4 | 1 | 0 |
| opening fallback | 7 | 2 | 1 | 3 | 1 | 2 |
| strict social replacement | 7 | 7 | 1 | 6 | 1 | 2 |

### 3.1 Visibility replacement

| Field | Missing (baseline) | Exists elsewhere? | Deterministic? | Future producer required? |
|---|---:|---|---|---|
| owner_bucket | 3/5 | Yes — `visibility_fallback_owner_bucket` on FEM (direct for visibility hard replace); absent on collapsed lineage events | Yes — `visibility_fallback_owner_bucket_from_fields()` | **No** for visibility hard replace; **Yes** for lineage-only records |
| source_family | 1/5 | Yes — classifier `source_family`; inventory projects `final_emission_gate` from path | Yes — path→family map | **No** (projection) |
| repair_kind | 5/5 | No write-time repair kind for visibility whole-text replace | No — no authoritative repair-kind vocabulary | **Yes** |
| recurrence_key | 0/5 | Yes — `make_runtime_lineage_event` / lineage projection | Yes — already synthesized | **No** (projection) |
| mutation_classification | 2/5 | Partial — `fallback_mutation` on lineage; FEM `final_emission_mutation_lineage` includes `sealed_fallback_replacement` | Partial — collapsed to coarse `fallback_mutation` | **Medium** — path-specific token preferred |

**Layer pattern:** FEM/replay records are strong on owner + recurrence; lineage events lose owner bucket; no path owns repair kind.

### 3.2 First mention replacement

| Field | Missing | Exists elsewhere? | Deterministic? | Future producer required? |
|---|---:|---|---|---|
| owner_bucket | 5/5 | Partial — inherits visibility/sealed bucket helpers; only `first_mention_replacement_applied` flag on FEM | Yes — via fallback pool/kind/source projection (same as visibility) | **Yes** — first-mention-specific stamp or explicit inherit rule at write time |
| source_family | 1/5 | Yes — infer `final_emission_gate` | Yes | **No** (projection) |
| repair_kind | 5/5 | No | No | **Yes** |
| recurrence_key | 0/5 | Yes — lineage (`visibility_or_scene_replacement`) | Yes | **No** (projection); **Yes** for path-distinct key |
| mutation_classification | 2/5 | Partial — coarse `fallback_mutation` only | Partial | **Medium** |

**Layer pattern:** Weakest owner-bucket path in baseline; flag exists but bucket is never stamped directly.

### 3.3 Referential replacement

| Field | Missing | Exists elsewhere? | Deterministic? | Future producer required? |
|---|---:|---|---|---|
| owner_bucket | 5/5 | Partial — hard fallback uses visibility/sealed helpers; local substitution has token/replacement only | Hard fallback: yes; local sub: no | **Yes** for local substitution; **Medium** for hard fallback |
| source_family | 1/5 | Yes — infer `final_emission_gate` | Yes | **No** (projection) |
| repair_kind | 5/5 | No — local sub has no repair kind | No | **Yes** |
| recurrence_key | 0/5 | Yes — collapsed lineage key | Yes | **No** (projection); **Yes** for local-sub key |
| mutation_classification | 2/5 | Partial — local sub not distinguished from hard replace in lineage | Partial | **Yes** for local pronoun substitution |

**Layer pattern:** Same collapse as first mention; local mutation is invisible to replacement-level attribution.

### 3.4 Sealed replacement

| Field | Missing | Exists elsewhere? | Deterministic? | Future producer required? |
|---|---:|---|---|---|
| owner_bucket | 3/5 | Yes — `sealed_fallback_owner_bucket` on FEM; `sealed_fallback_owner_bucket_from_fields()` | Yes | **No** for FEM records; **Yes** for lineage-only |
| source_family | 1/5 | Yes — infer `final_emission_gate` | Yes | **No** (projection) |
| repair_kind | 5/5 | No generic sealed repair kind | No | **Yes** (or accept sealed subkind as repair proxy) |
| recurrence_key | 0/5 | Yes — sealed subkind lineage events | Yes | **No** (projection) |
| mutation_classification | 2/5 | Partial — `fallback_mutation` + FEM lineage token `sealed_fallback_replacement` | Partial | **Medium** — preserve subkind in mutation class |

**Layer pattern:** FEM is authoritative for owner bucket; repair kind is the universal gap.

### 3.5 Response type replacement

| Field | Missing | Exists elsewhere? | Deterministic? | Future producer required? |
|---|---:|---|---|---|
| owner_bucket | 7/7 | Partial — opening bucket via meta helper when opening branch; no universal response-type bucket | Opening branch: yes; answer/action: no | **Yes** for non-opening response-type repairs |
| source_family | 1/5 | Yes — FEM flags + classifier (`final_emission_gate`, `upstream_prepared_emission`) | Yes | **No** (projection/classifier) |
| repair_kind | 4/7 | Yes — `response_type_repair_kind` on FEM (authoritative write-time source) | Yes where stamped | **No** when FEM present; **Yes** for lineage-only records |
| recurrence_key | 1/7 | Yes — lineage projection | Yes | **No** (projection) |
| mutation_classification | 2/7 | Partial — `response_type_repair_mutation` on lineage | Yes when response-type repair used | **Low** — projection sufficient |

**Layer pattern:** Best repair-kind coverage in corpus; owner bucket is the primary gap.

### 3.6 Sanitizer replacement

| Field | Missing | Exists elsewhere? | Deterministic? | Future producer required? |
|---|---:|---|---|---|
| owner_bucket | 7/7 | Partial — split owners in sanitizer trace (`sanitizer_empty_fallback_owner`, strict-social selection/prose owners); no unified bucket | Partial — could map trace owners to bucket taxonomy | **Yes** |
| source_family | 1/7 | Yes — classifier `output_sanitizer`; inventory projects from path | Yes | **No** (projection) |
| repair_kind | 7/7 | No | No | **Yes** |
| recurrence_key | 1/7 | Yes — lineage (`sanitizer_empty_output`, `sanitizer_strict_social`) | Yes | **No** (projection) |
| mutation_classification | 2/7 | Partial — `sanitizer_mutation` / `sanitizer` sublayer | Yes | **Low** — projection sufficient |

**Layer pattern:** Trace has ownership fragments; no field maps to canonical five-field contract.

### 3.7 Repair mutation

| Field | Missing | Exists elsewhere? | Deterministic? | Future producer required? |
|---|---:|---|---|---|
| owner_bucket | 4/4 | No unified bucket; repair flags on FEM (`fallback_behavior_repaired`, etc.) | No | **Yes** |
| source_family | 0/4 | Yes — infer `fallback_behavior` | Yes | **No** (projection) |
| repair_kind | 4/4 | Partial — flag names imply repair type but no taxonomy-valid `repair_kind` | Partial — could map flag→kind | **Medium** |
| recurrence_key | 1/4 | Yes — `repair_only_mutation` lineage | Yes | **No** (projection) |
| mutation_classification | 0/4 | Yes — `repair_only_mutation` / `fallback_behavior` sublayer | Yes | **No** (projection) |

**Layer pattern:** Best mutation-class coverage; owner bucket and repair kind absent by design.

### 3.8 Opening fallback

| Field | Missing | Exists elsewhere? | Deterministic? | Future producer required? |
|---|---:|---|---|---|
| owner_bucket | 2/7 | Yes — `opening_fallback_owner_bucket_from_meta()`; lineage `fallback_owner_bucket` | Yes | **No** (projection) for resolved; **Low** for direct stamp |
| source_family | 1/7 | Yes — classifier `opening_fallback` | Yes | **No** (projection/classifier) |
| repair_kind | 3/7 | Yes — `response_type_repair_kind` / opening repair kinds on FEM | Yes | **No** when FEM present |
| recurrence_key | 1/7 | Yes — lineage | Yes | **No** (projection) |
| mutation_classification | 2/7 | Partial — `fallback_mutation` | Partial | **Low** |

**Layer pattern:** Best overall path (3/7 resolved complete in BS1); gaps concentrated on lineage-only records.

### 3.9 Strict social replacement

| Field | Missing | Exists elsewhere? | Deterministic? | Future producer required? |
|---|---:|---|---|---|
| owner_bucket | 7/7 | Partial — sealed bucket on some branches; `strict_social_active` + source tokens on FEM | Partial — `sealed_fallback_owner_bucket_from_fields(strict_social_route=…)` | **Yes** |
| source_family | 1/7 | Yes — infer `final_emission_gate` / `strict_social_emission` | Yes | **No** (projection) |
| repair_kind | 6/7 | Partial — `strict_social_dialogue_repair` when response-type repair used | Partial | **Medium** |
| recurrence_key | 1/7 | Yes — lineage | Yes | **No** (projection) |
| mutation_classification | 2/7 | Partial — `strict_social_replacement` sublayer | Yes | **Low** |

**Layer pattern:** Similar to response-type but weaker repair-kind coverage on fallback-only branches.

---

## 4. Source-of-Truth Matrix

Nearest **authoritative** source = the layer that owns the decision, not merely first observer.

| Attribution field | Current source | Earliest available source | Deterministic? | Producer change required? | Notes |
|---|---|---|---|---|---|
| **owner_bucket** | FEM family-specific stamps (`visibility_fallback_owner_bucket`, `sealed_fallback_owner_bucket`); opening via `opening_fallback_owner_bucket_from_meta()`; lineage `fallback_owner_bucket` (opening only) | `game/final_emission_meta` bucket helpers at replacement application (`final_emission_visibility_fallback.py`, `final_emission_sealed_fallback.py`, opening projection) | **Yes** for opening/sealed/visibility hard replace; **Partial** for first-mention, referential local sub, sanitizer, repair layers, strict-social | **Yes** for 6/9 paths at strict completeness | No universal bucket field; taxonomy split across three bucket registries |
| **source_family** | `tests/helpers/failure_classifier.py` → `source_family` via `CATEGORY_RULES` | Classifier at drift time; inventory can project earlier via path→family map | **Yes** (projection) | **No** for resolved completeness; **Yes** for write-time strict | Never written to FEM or lineage today; replay-classifier concept |
| **repair_kind** | FEM `response_type_repair_kind` (response-type/opening branches); lineage `repair_kind` (speaker repairs only) | `game/final_emission_response_type.py` at response-type enforcement | **Yes** for response-type paths only | **Yes** for visibility, first-mention, referential, sealed, sanitizer, repair mutation, strict-social fallback-only | Largest gap (44/116 missing slots) |
| **recurrence_key** | `game/runtime_lineage_telemetry.build_recurrence_key()` via `make_runtime_lineage_event()` | Lineage projection (`game/final_emission_replay_projection.build_fem_runtime_lineage_events`) | **Yes** | **No** for resolved; **Optional** persist-at-write for strict | Not persisted by replacement producers; synthesized read-side |
| **mutation_classification** | Lineage `mutation_kind`; classifier `mutation_source` / `emission_sublayer`; FEM `final_emission_mutation_lineage` tokens | FEM lineage refresh (`build_final_emission_mutation_lineage`) + lineage projection | **Partial** — coarse kinds collapse path-specific evidence | **Medium** — path-specific tokens needed for visibility/first-mention/referential/local-sub | No literal `mutation_classification` runtime field; `mutation_kind` is accepted equivalent |

---

## 5. Path-Level Gap Analysis

| Replacement path | Missing fields (baseline) | Existing evidence | Can infer? | Requires producer change? | Recommended future source |
|---|---|---|---|---|---|
| visibility replacement | owner (3), repair (5), mutation (2), source (1) | `visibility_replacement_applied`, pool/kind, owner bucket on FEM, lineage fallback/mutation events | owner: yes; source: yes; recurrence: yes; repair: no; mutation: partial | **Yes** for repair kind; **No** for owner on FEM reads | `response_type_repair_kind`-style visibility repair token at `apply_visibility_enforcement`; keep recurrence on lineage projection |
| first mention replacement | owner (5), repair (5), mutation (2), source (1) | `first_mention_replacement_applied`, visibility fallback fields (inherited) | owner: yes via inherit; source: yes; recurrence: yes; repair: no; mutation: partial | **Yes** — stamp owner inherit + repair kind at `apply_first_mention_enforcement` | Write-time inherit of visibility bucket + `first_mention_repair_kind` |
| referential replacement | owner (5), repair (5), mutation (2), source (1) | hard: `referential_clarity_replacement_applied`; local: token/replacement fields | hard: partial; local: no for owner/repair; source: yes | **Yes** — local sub needs mutation class + repair kind | `final_emission_referential_clarity.py` for local sub; visibility/sealed helpers for hard fallback |
| sealed replacement | owner (3), repair (5), mutation (2), source (1) | `sealed_fallback_owner_bucket`, `final_route`, subkind projection | owner: yes; source: yes; recurrence: yes; repair: no; mutation: partial | **Yes** for repair kind (or adopt subkind as repair proxy) | `prepare_sealed_replacement_route_meta` for repair/subkind token |
| response type replacement | owner (7), repair (4), recurrence (1), mutation (2), source (1) | `response_type_repair_kind`, upstream prepared flags | repair: yes on FEM; owner: partial; others: yes | **Yes** for universal owner bucket on non-opening repairs | `enforce_response_type_contract` stamps owner bucket + existing repair kind |
| sanitizer replacement | owner (7), repair (7), recurrence (1), mutation (2), source (1) | sanitizer trace owners, empty/strict-social fallback flags | source/mutation/recurrence: yes; owner: partial; repair: no | **Yes** | Map trace owners → bucket taxonomy + `sanitizer_repair_kind` in `output_sanitizer.py` |
| repair mutation | owner (4), repair (4), recurrence (1) | repair layer flags, `repair_only_mutation`, `fallback_behavior` sublayer | source/mutation/recurrence: yes; owner: no; repair: partial | **Yes** for owner; **Medium** for repair kind mapping | Central repair-layer registry in `final_emission_repairs.py` |
| opening fallback | owner (2), repair (3), recurrence (1), mutation (2), source (1) | authorship source, repair kind, meta bucket projection | **Yes** for all with projection | **Low** — optional direct bucket stamp | Keep projection; optional `opening_fallback_owner_bucket` on FEM for strict |
| strict social replacement | owner (7), repair (6), recurrence (1), mutation (2), source (1) | `strict_social_active`, source tokens, optional sealed bucket | partial | **Yes** for owner + repair on fallback-only branches | `final_emission_strict_social_stack.py` + sealed bucket helper |

---

## 6. Attribution Origin Totals

Classification of all **populated** field slots in the BS1 baseline corpus (n=144):

| Origin | Count | Share | Typical sources |
|---|---:|---:|---|
| **DIRECT** | 58 | 40.3% | FEM bucket/repair stamps; lineage recurrence_key; classifier `source_family` |
| **PROJECTED** | 80 | 55.6% | `opening_fallback_owner_bucket_from_meta`, path→`source_family`, FEM→lineage mutation_kind, bucket helper projection |
| **INFERRED** | 6 | 4.2% | Classifier-computed `repair_kind`, `mutation_source`, `opening_fallback_owner_bucket` |
| **CLASSIFIER_DERIVED** | 6 | 4.2% | Same 6 slots (inventory `classifier_inferred` origin = classifier-derived) |

**Unpopulated slots:** 116 (missing entirely from evaluated record at that layer).

### Origin by inventory source kind

| Source kind | Records | Dominant origins | Primary gaps |
|---|---:|---|---|
| fem_metadata | 9 | DIRECT (owner, repair on some paths) | repair kind on non-response-type paths |
| runtime_lineage_event | 27 | PROJECTED (recurrence, mutation, source_family) | owner_bucket, repair_kind |
| replay_projection | 9 | DIRECT + PROJECTED | same as FEM layer |
| failure_classification | 7 | DIRECT (source_family) + INFERRED | recurrence_key, owner_bucket |

**Interpretation:** Lineage events are recurrence/mutation-rich but owner/repair-poor. Classifier rows are source-family-rich but recurrence-absent. FEM is the only layer with direct repair kind — and only for response-type/opening branches.

---

## 7. Producer-Readiness Ranking

Ranked by invasiveness of future producer work to achieve **strict** completeness.

### LOW RISK — projection / contract only; no runtime stamping required

| Field / scope | Rationale |
|---|---|
| `source_family` (all paths) | Path→family map already deterministic in inventory; promote to shared projection module |
| `recurrence_key` (all paths) | Already synthesized in `runtime_lineage_telemetry`; persist optionally but not required for resolved completeness |
| `mutation_classification` (opening, response-type, sanitizer, repair mutation) | Existing lineage kinds / sublayers sufficient when projection preserved |
| `owner_bucket` (opening fallback) | `opening_fallback_owner_bucket_from_meta()` is stable; direct stamp optional |

### MEDIUM RISK — localized FEM/trace stamps at existing application points

| Field / scope | Rationale |
|---|---|
| `owner_bucket` (visibility, sealed) | Helpers exist; extend lineage projection to carry bucket from FEM (BS5) before new stamps |
| `owner_bucket` (first mention, referential hard) | Inherit visibility/sealed bucket at write time in visibility fallback module |
| `mutation_classification` (visibility, first-mention, referential) | Split `visibility_or_scene_replacement` lineage bucket; add path-specific mutation tokens |
| `repair_kind` (strict social fallback-only) | Extend existing `response_type_repair_kind` pattern |
| `repair_kind` (repair mutation) | Map existing repair flags to taxonomy-valid kinds |
| `owner_bucket` (response-type non-opening) | New bucket vocabulary slice; confined to response-type module |

### HIGH RISK — new producer vocabulary, multi-module coordination, or classifier convergence

| Field / scope | Rationale |
|---|---|
| `repair_kind` (visibility, first-mention, referential, sealed) | No current repair-kind contract for whole-text replacements; touches gate + fallback selectors |
| `owner_bucket` (sanitizer) | Must unify trace split-owners into bucket taxonomy across `output_sanitizer.py` |
| `owner_bucket` (repair mutation) | No bucket concept for repair-only layers today |
| `owner_bucket` (strict social) | Cross-cuts strict-social stack, sealed fallback, response-type |
| `repair_kind` (sanitizer) | New sanitizer repair vocabulary + trace alignment |
| `mutation_classification` (referential local substitution) | New mutation surface; currently not a replacement flag |
| `source_family` at write time | Would duplicate classifier taxonomy in runtime FEM — prefer projection unless product requires write-time |

---

## 8. BS2 Recommendations

### A. Fields that should remain inferred

Keep **classifier-derived** population for failure-investigation workflows only:

- `source_family` on classification rows (already authoritative post-drift)
- `mutation_source` / `emission_sublayer` when classifying replay failures
- `repair_kind` fallback from drift row when FEM repair kind absent (diagnostic backfill)

Do **not** treat classifier inference as write-time completeness.

### B. Fields that should be projected

Promote to shared read-side projection (no runtime change):

| Field | Projection owner | Action |
|---|---|---|
| `source_family` | `game/final_emission_replay_projection.py` or inventory | Path→family map from finalized FEM |
| `recurrence_key` | `runtime_lineage_telemetry` (existing) | Keep synthesized; document as canonical read-side ID |
| `owner_bucket` (opening) | `final_emission_meta.opening_fallback_owner_bucket_from_meta` | Already authoritative for resolved completeness |
| `mutation_classification` | Lineage + FEM lineage tokens | Preserve subkind before collapse |

### C. Fields that should become canonical producer-owned data

For **strict** completeness, stamp at application time:

1. **`repair_kind`** — highest ROI; start at response-type module (extend pattern), then visibility/sealed/sanitizer
2. **`owner_bucket`** — first-mention + referential inherit; sanitizer bucket mapping; strict-social unified bucket
3. **Path-specific `mutation_classification`** — referential local sub; split visibility/first-mention/referential lineage bucket

### D. Smallest possible future implementation sequence

| Phase | Block | Scope | Expected strict completeness lift |
|---|---|---|---|
| 1 | Projection convergence | source_family + owner bucket on lineage from FEM | Low strict; high resolved |
| 2 | Repair kind pattern extension | response-type → visibility/sealed | Medium strict |
| 3 | Bucket inherit stamps | first-mention, referential hard | Medium strict |
| 4 | Sanitizer + repair-layer vocabulary | sanitizer trace, repair mutation | High strict |
| 5 | Path-specific mutation tokens | split collapsed lineage kinds | Medium strict; better recurrence discrimination |

---

## 9. Recommended Downstream BS Blocks

### Recommended BS3 candidate — **Attribution record contract & taxonomy lock**

**Goal:** Formalize the canonical five-field record, allowed taxonomies, and origin vocabulary as a bounded read-side contract.

**Likely files:**

- `game/runtime_lineage_telemetry.py` (document recurrence as canonical read-side ID)
- `game/final_emission_replay_projection.py` (path-specific mutation kinds)
- `tests/failure_classification_contract.py` (align repair-kind / mutation-class vocabularies)
- `tests/helpers/replacement_attribution_inventory.py` (contract tests)

**Validation:** `pytest tests/test_replacement_attribution_inventory.py tests/test_runtime_lineage_telemetry.py tests/test_failure_classification_contract.py -q`

**Risk:** Medium

---

### Recommended BS4 candidate — **Producer coverage (repair kind + owner bucket stamps)**

**Goal:** Stamp missing direct fields at shared replacement application points without changing selection behavior.

**Priority order (from gap map):**

1. `repair_kind` on visibility / sealed / first-mention / referential hard replace
2. `owner_bucket` inherit for first-mention and referential
3. Sanitizer bucket + repair kind mapping
4. Strict-social unified owner bucket

**Likely files:**

- `game/final_emission_visibility_fallback.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_response_type.py`
- `game/output_sanitizer.py`
- `game/final_emission_strict_social_stack.py`

**Validation:** visibility, sealed, sanitizer, response-type test suites + inventory strict completeness re-baseline

**Risk:** Medium-high

---

### Recommended BS5 candidate — **Projection / classifier convergence**

**Goal:** Stop attribution loss at projection collapse; consume canonical FEM evidence before classifier heuristics.

**Actions:**

- Split `visibility_or_scene_replacement` into path-specific lineage kinds
- Carry FEM owner buckets onto lineage `fallback_owner_bucket` for all families
- Teach classifier to prefer projected canonical record over re-inference
- Preserve distinct recurrence keys per path

**Likely files:**

- `game/final_emission_replay_projection.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/golden_replay_projection.py`

**Validation:** lineage, classifier, golden replay tests + inventory resolved completeness re-baseline

**Risk:** Medium

---

## 10. Gap Closure Summary

Every missing field in the BS1 baseline maps to a nearest authoritative source:

| Missing field (total slots) | Nearest authoritative source | Gap type |
|---|---|---|
| repair_kind (44) | `final_emission_response_type.py` (partial); nowhere else for whole-text replace | **Producer vocabulary absent** |
| owner_bucket (43) | `final_emission_meta` bucket helpers (partial); sanitizer trace fragments | **Partial stamp + projection lag** |
| mutation_classification (16) | Lineage `mutation_kind` + FEM lineage tokens (coarse) | **Projection collapse** |
| source_family (8) | `failure_classifier.CATEGORY_RULES` | **Wrong layer evaluated** |
| recurrence_key (5) | `runtime_lineage_telemetry.build_recurrence_key` | **Not persisted at write; classifier never emits** |

No missing field is irrecoverable. The roadmap is: **project what is deterministic (BS5)** → **stamp what must be direct (BS4)** → **lock the contract (BS3)**.

---

## Validation Performed

```powershell
pytest tests/test_replacement_attribution_inventory.py -q
```

Result: **12 passed**

Baseline metrics reproduced from `build_baseline_attribution_corpus()`:

- 52 records, 116 missing slots, 144 populated slots
- Origin totals: DIRECT 58, PROJECTED 80, INFERRED/CLASSIFIER_DERIVED 6
