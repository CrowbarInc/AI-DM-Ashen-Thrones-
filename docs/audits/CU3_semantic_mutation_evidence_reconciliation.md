# CU3 Semantic Mutation Evidence Reconciliation

## Objective

Prefer recorded first-writer evidence over projection-derived semantic mutation inference wherever diagnostics, replay projection, and classifier rows already have enough evidence to do so.

No player-facing behavior changed. No protected replay schema was promoted.

## Precedence Model

`game.semantic_mutation_attribution.reconcile_semantic_mutation_owner` is the single reconciliation helper. It selects attribution in this order:

1. `semantic_mutation_write_sites`
2. runtime lineage mutation events
3. fallback provenance
4. sanitizer lineage
5. FEM mutation lineage
6. stage-diff telemetry
7. projection-derived inference

Explicit write-site attribution is never overwritten by inferred projection ownership.

## Helper

The helper returns:

- `authoritative_mutation_owner`
- `authoritative_mutation_family`
- `authoritative_write_site`
- `authoritative_evidence_source`
- `authoritative_mutation_confidence`
- `used_projection_inference`

The helper is diagnostic-only and read-side. It does not add instrumentation, mutate emitted text, or change runtime selection.

## Files Changed

- `game/semantic_mutation_attribution.py`
- `game/runtime_lineage_telemetry.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/runtime_lineage_reporting.py`
- `tests/failure_classification_contract.py`
- `tests/test_golden_replay_projection_semantic.py`
- `tests/test_failure_classifier.py`
- `tests/test_runtime_lineage_telemetry.py`

## Compatibility Guarantees

Legacy projection fields such as `first_semantic_mutation_bucket` and `first_semantic_mutation_source` are still projected when BY semantic mutation traces exist.

New authoritative fields are optional diagnostics. They are not protected replay fields.

Classifier taxonomy is unchanged. Rows keep existing categories, owners, severities, and investigation-target defaults while adding evidence fields that explain attribution choice.

## Before / After Examples

Before:

```json
{
  "first_semantic_mutation_bucket": "sanitizer",
  "first_semantic_mutation_owner": "game.output_sanitizer"
}
```

After, when write-site evidence exists:

```json
{
  "first_semantic_mutation_bucket": "sanitizer",
  "first_semantic_mutation_owner": "game.output_sanitizer",
  "first_write_family": "fallback",
  "first_write_owner": "game.fallback_provenance_debug",
  "authoritative_mutation_family": "fallback",
  "authoritative_mutation_owner": "game.fallback_provenance_debug",
  "authoritative_evidence_source": "write_site",
  "used_projection_inference": false
}
```

After, when no stronger evidence exists:

```json
{
  "authoritative_mutation_family": "sanitizer",
  "authoritative_mutation_owner": null,
  "authoritative_evidence_source": "projection_inference",
  "used_projection_inference": true
}
```

## Tests Run

Focused validation:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests/test_golden_replay_projection_semantic.py tests/test_failure_classifier.py tests/test_runtime_lineage_telemetry.py tests/test_output_sanitizer.py -q --tb=short
```

## Remaining Inference-Only Cases

Projection inference remains the final fallback for old replay rows that have semantic mutation traces but no write-site, runtime lineage, fallback provenance, sanitizer lineage, FEM mutation lineage, or stage-diff transition evidence.

Stage-diff fallback intentionally requires transition evidence so ordinary stage snapshots do not imply mutation ownership.

## Remaining Work Before Prompt / Policy Attribution

Prompt and policy write-site attribution remains out of scope for CU3. Future work should add explicit policy write-site evidence at the producer surface before teaching this helper to prefer it over runtime lineage.
