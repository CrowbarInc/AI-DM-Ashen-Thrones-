# BS3 Contract Compliance Report

> Canonical attribution contract lock — validation and taxonomy audit only.

## Attribution Maturity Scores

| Cycle | Coverage | Contract compliance | Taxonomy consistency | Resolved complete |
|---|---:|---:|---:|---:|
| BS1 | 5.36% | 40.3% | 72.0% | 3/56 |
| BS5 | 85.71% | 100.0% | 100.0% | 48/56 |
| BS4 | 50.0% | 100.0% | 100.0% | 28/56 |
| BS3 (live) | 85.71% | 100.0% | 100.0% | 48/56 |

## Layer Compliance Summary

### inventory_corpus

- `owner_bucket`: 56 compliant, 0 non-compliant
- `source_family`: 56 compliant, 0 non-compliant
- `repair_kind`: 56 compliant, 0 non-compliant
- `recurrence_key`: 56 compliant, 0 non-compliant
- `mutation_classification`: 48 compliant, 0 non-compliant

### lineage_projection

- Deprecated fallback kind aliases: `['visibility_or_scene_replacement']`
- Observed normalized fallback kinds: `['first_mention_hard_replacement', 'referential_clarity_hard_replacement', 'response_type_prepared_emission', 'sanitizer_empty_output', 'scene_opening', 'sealed_passive_scene_pressure_fallback', 'strict_social_fallback', 'visibility_hard_replacement']`

- `repair_kind`: 8 compliant, 0 non-compliant
- `recurrence_key`: 26 compliant, 0 non-compliant
- `mutation_classification`: 10 compliant, 0 non-compliant
- `owner_bucket`: 5 compliant, 0 non-compliant

### failure_classifier

- `source_family`: 7 compliant, 0 non-compliant
- `repair_kind`: 7 compliant, 0 non-compliant
- `owner_bucket`: 4 compliant, 0 non-compliant
- `mutation_classification`: 6 compliant, 0 non-compliant

## Deprecated Values

- Repair kinds (legacy): `['thin_answer']`
- Fallback kind aliases: `{'visibility_or_scene_replacement': 'visibility_hard_replacement'}`
- Lineage-only repair kinds (not in repair_kind contract): `['canonical_rewrite', 'dialogue_enforcement_skipped_due_to_social_suppression', 'local_rebind']`

## Normalization Rules

- Repair kind aliases: `{'response_type_contract_repair': 'answer_upstream_prepared_repair'}`
- Recurrence key: must contain `:` and length >= 5

## Taxonomy Source of Truth

- `owner_bucket`: game.final_emission_meta, tests.helpers.attribution_contract
- `source_family`: tests.failure_classification_contract, tests.helpers.attribution_contract
- `repair_kind`: tests.failure_classification_contract, tests.helpers.attribution_contract
- `mutation_classification`: tests.helpers.attribution_contract, tests.failure_classification_contract
- `replacement_path`: tests.helpers.attribution_contract
