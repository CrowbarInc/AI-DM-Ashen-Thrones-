# BS3 — Canonical Attribution Contract

Contract date: 2026-06-20

Scope: contract definition, taxonomy lock, and read-side validation only. No runtime replacement behavior, routing, recurrence generation, or output changes.

Implementation: `tests/helpers/attribution_contract.py`

Compliance artifact: `artifacts/bs3_contract_compliance_report.md`

Validation:

```powershell
pytest tests/test_attribution_contract.py tests/test_replacement_attribution_inventory.py tests/test_failure_classifier.py tests/test_runtime_lineage_telemetry.py tests/test_final_emission_meta.py -q
```

---

## 1. Canonical Attribution Record

Every semantic replacement attribution evaluation uses this record shape:

| Field | Required | Description |
|---|---|---|
| `owner_bucket` | yes | Family-specific ownership bucket (opening / sealed / visibility registries) |
| `source_family` | yes | Module family that authored or selected the replacement |
| `repair_kind` | yes | Deterministic repair intent token |
| `recurrence_key` | yes | Stable lineage identity (`event:stage:owner:detail`) |
| `mutation_classification` | yes | Coarse mutation class (`mutation_kind` or emission sublayer equivalent) |

Additional record metadata:

| Field | Required | Description |
|---|---|---|
| `replacement_path` | yes | One of nine canonical replacement paths (see §2) |
| `attribution_origin` | per-field | How each required field was populated: `direct`, `projected`, or `classifier_inferred` |

Optional inventory metadata (BS1 read-side):

- `source_kind` — evidence layer (`fem_metadata`, `runtime_lineage_event`, `replay_projection`, `failure_classification`)
- `inferred_fields` — fields populated via projection or classifier inference
- `missing_fields` — required fields absent or failing taxonomy validation

### Completeness scoring (unchanged from BS1)

- **Strict complete** — all five required fields present, taxonomy-valid, and `attribution_origin[field] == direct`
- **Resolved complete** — all five required fields present and taxonomy-valid (any origin)

---

## 2. Replacement Paths

Canonical `replacement_path` values:

- `visibility replacement`
- `first mention replacement`
- `referential replacement`
- `sealed replacement`
- `response type replacement`
- `sanitizer replacement`
- `repair mutation`
- `opening fallback`
- `strict social replacement`

### Attribution origins

- `direct` — write-time FEM or lineage stamp
- `projected` — deterministic read-side projection
- `classifier_inferred` — failure classifier backfill

---

## 3. Locked Taxonomies

Single source of truth: `tests/helpers/attribution_contract.py`

Owner bucket registries originate in `game/final_emission_meta.py` and are re-exported through `tests/failure_classification_contract.py`.

### `owner_bucket` (9 values)

- `upstream-prepared`
- `sealed-gate`
- `retry`
- `strict-social`
- `strict-social-sealed`
- `strict-social-visibility`
- `opening-visibility`
- `unknown-none`
- `unknown-ambiguous`

### `source_family` (21 values)

- `api_route`
- `interaction_context`
- `speaker_contract`
- `dialogue_social_plan`
- `interaction_continuity`
- `final_emission_gate`
- `final_emission_meta`
- `response_type`
- `fallback_behavior`
- `strict_social_emission`
- `opening_fallback`
- `upstream_prepared_emission`
- `output_sanitizer`
- `stage_diff`
- `schema_contracts`
- `state_authority`
- `scenario_spine_eval`
- `playability_eval`
- `narrative_authenticity_eval`
- `behavioral_eval`
- `golden_replay_projection`

### `repair_kind` (15 values)

**Response-type runtime:**

- `answer_upstream_prepared_repair`
- `action_outcome_upstream_prepared_repair`
- `strict_social_dialogue_repair`
- `dialogue_minimal_repair`

**Opening:**

- `opening_deterministic_fallback`
- `opening_deterministic_fallback_failed_closed`

**Producer stamps (BS4):**

- `visibility_enforcement`
- `first_mention_enforcement`
- `referential_clarity_enforcement`
- `referential_clarity_local_substitution`
- `sanitizer_empty_output`
- `sanitizer_strip_only`
- `strict_social_repair`
- `fallback_behavior_repair`

**Legacy:**

- `thin_answer`

### `mutation_classification` (37 values)

**Core mutation kinds:**

- `fallback_mutation`
- `speaker_repair_mutation`
- `continuity_repair_mutation`
- `response_type_repair_mutation`
- `sanitizer_mutation`
- `final_emission_mutation`
- `repair_only_mutation`
- `visibility_replacement_mutation`
- `first_mention_replacement_mutation`
- `referential_clarity_replacement_mutation`
- `referential_clarity_local_substitution_mutation`
- `sealed_replacement_mutation`
- `fallback_behavior_repair_mutation`
- `answer_completeness_repair_mutation`
- `response_delta_repair_mutation`
- `social_response_structure_repair_mutation`
- `narrative_authenticity_repair_mutation`
- `tone_escalation_repair_mutation`
- `anti_railroading_repair_mutation`
- `context_separation_repair_mutation`
- `player_facing_narration_purity_repair_mutation`
- `answer_shape_primacy_repair_mutation`
- `narrative_authority_repair_mutation`

**Emission sublayers** (shared with classifier `emission_sublayer`):

- `response_type`
- `fallback_behavior`
- `strict_social_replacement`
- `speaker_contract_enforcement`
- `interaction_continuity`
- `sanitizer`
- `sanitizer.empty_fallback`
- `opening_fallback`
- `upstream_prepared_emission`
- `sealed_gate`
- `final_emission.finalize_packaging`
- `final_emission.finalize_route_illegal_strip`
- `terminal_fallback`
- `emission.post_gate_mutation_unknown`

---

## 4. Deprecated Values, Aliases, Normalization

### Deprecated repair kinds

| Value | Status |
|---|---|
| `thin_answer` | Legacy response-type repair; remains valid for backward-compatible ingestion |

### Deprecated fallback kind aliases (lineage projection)

| Legacy token | Normalized token |
|---|---|
| `visibility_or_scene_replacement` | `visibility_hard_replacement` |

### Repair kind aliases

| Alias | Canonical |
|---|---|
| `response_type_contract_repair` | `answer_upstream_prepared_repair` |

### Lineage-only repair kinds (outside `repair_kind` contract)

Observed on speaker/continuity lineage events but **not** valid `repair_kind` values:

- `canonical_rewrite`
- `local_rebind`
- `dialogue_enforcement_skipped_due_to_social_suppression`

### Normalization rules

| Field | Rule |
|---|---|
| All tokens | `str(value).strip()`; empty → invalid |
| `repair_kind` | lower-case; apply `REPAIR_KIND_ALIASES` |
| `mutation_classification` | apply `MUTATION_CLASSIFICATION_ALIASES` (identity map reserved for future use) |
| `fallback_kind` | apply `DEPRECATED_FALLBACK_KIND_ALIASES` when auditing lineage |
| `recurrence_key` | must contain `:` and length ≥ 5 |

---

## 5. Validation Helpers

Central validators in `tests/helpers/attribution_contract.py`:

| Function | Purpose |
|---|---|
| `validate_owner_bucket(value)` | Bucket registry membership |
| `validate_source_family(value)` | Source family tag membership |
| `validate_repair_kind(value)` | Repair kind taxonomy + normalization |
| `validate_mutation_classification(value)` | Mutation class / sublayer membership |
| `validate_recurrence_key(value)` | Recurrence key shape |
| `validate_replacement_path(value)` | Replacement path membership |
| `validate_attribution_origin(value)` | Origin membership |
| `is_taxonomy_valid(field, value)` | Field-dispatch validator used by BS1 inventory |

All validators return `ValidationResult(field, value, valid, normalized, reason)`.

---

## 6. Taxonomy De-duplication

| Before BS3 | After BS3 |
|---|---|
| `ALLOWED_REPAIR_KINDS` defined in inventory | Owned by `attribution_contract`; inventory re-exports |
| `ALLOWED_MUTATION_CLASSIFICATIONS` defined in inventory | Owned by `attribution_contract`; inventory re-exports |
| `REPLACEMENT_PATHS` / origins duplicated | Owned by `attribution_contract` |
| `_is_taxonomy_valid` inline in inventory | Delegates to `is_taxonomy_valid` |
| Owner buckets in `game.final_emission_meta` + `failure_classification_contract` | Unchanged write-side source; contract unions for validation |

---

## 7. Attribution Maturity Scores

| Cycle | Coverage | Contract compliance | Taxonomy consistency | Resolved complete |
|---|---:|---:|---:|---|
| BS1 | 5.77% | 40.3% | 72.0% | 3/52 |
| BS5 | 10.2% | 55.6% | 85.0% | 5/52 |
| BS4 | 32.65% | 68.0% | 90.0% | 16/49 |
| BS3 (live) | 32.65% | **100.0%** | **100.0%** | 16/49 |

**Coverage score** — resolved completeness % on baseline corpus.

**Contract compliance score** — % of populated required-field slots that pass canonical validators.

**Taxonomy consistency score** — structural checks that contract unions match authoritative registries (100% when all checks pass).

Live BS3 metrics: `calculate_attribution_maturity_scores()` / `write_bs3_contract_compliance_report()`.

---

## 8. Layer Audit Scope

BS3 compliance audit covers:

| Layer | Module | Audited fields |
|---|---|---|
| FEM producers | Baseline corpus FEM fixtures | all five required fields |
| Lineage projection | `game/final_emission_replay_projection` | repair_kind, recurrence_key, mutation_kind, owner bucket |
| Runtime lineage | `game/runtime_lineage_telemetry` | recurrence key shape (via projection output) |
| Failure classifier | `tests/helpers/failure_classifier` | source_family, repair_kind, owner bucket, mutation_source |
| Inventory tooling | `tests/helpers/replacement_attribution_inventory` | full record contract |

See `artifacts/bs3_contract_compliance_report.md` for per-layer compliant / non-compliant counts.
