# CU6 Semantic Mutation Contract Adoption Audit

## Scope

CU6 verifies adoption of the governed semantic mutation attribution contract. This is an adoption and consistency audit only. It does not change emitted text, add write-site instrumentation, redesign governance, promote protected replay schemas, or expand replay corpus coverage.

## Authoritative Model

The single authoritative semantic mutation attribution model is:

- `game.semantic_mutation_attribution.reconcile_semantic_mutation_owner`
- `game.semantic_mutation_attribution.validate_semantic_mutation_contract`
- `game.semantic_mutation_attribution.SEMANTIC_MUTATION_ATTRIBUTION_CONTRACT`

The governed precedence order remains:

1. `write_site`
2. `runtime_lineage`
3. `fallback_provenance`
4. `sanitizer_lineage`
5. `fem_mutation_lineage`
6. `stage_diff`
7. `projection_inference`

## Consumer Inventory

| Consumer | Function / surface | Uses reconciliation helper | Independent inference |
|---|---|---:|---|
| `game.semantic_mutation_attribution` | `reconcile_semantic_mutation_owner` | Canonical owner | No |
| `game.semantic_mutation_attribution` | `validate_semantic_mutation_contract` | Yes | No; validates against canonical reconciliation |
| `game.final_emission_meta` | `append_semantic_mutation_write_site` | Uses contract family vocabulary | No authoritative inference; write-time evidence append only |
| `tests.helpers.golden_replay_projection` | `project_turn_observation` | Yes | Compatibility-only `first_write_*` diagnostics now use contract write-site helpers |
| `tests.helpers.failure_classifier` | `_authoritative_mutation_attribution` | Yes | Existing-row passthrough is a compatibility shim; absent rows reconcile |
| `tests.helpers.failure_classifier` | `_mutation_source` | Yes via `_authoritative_mutation_attribution` | Category/source-family routing remains classifier-owned, not authoritative attribution |
| `game.runtime_lineage_telemetry` | `summarize_runtime_lineage_events` | Yes | Frequency buckets remain local; first mutation attribution is reconciled |
| `tests.helpers.runtime_lineage_reporting` | `runtime_lineage_markdown_lines` | Consumes reconciled summary fields | No |
| `tests.helpers.failure_dashboard_report` | `_evidence_cell` / report rendering | Consumes classifier row fields | No |
| `tests.failure_classification_contract` | dashboard evidence manifest | Schema/label registry only | No |

## Duplicate Logic Review

| Duplicate candidate | Classification | CU6 action |
|---|---|---|
| Write-site family allowlist in `game.final_emission_meta` | Unnecessary duplication | Replaced with import of `SEMANTIC_MUTATION_WRITE_SITE_FAMILIES` from contract module |
| Replay `first_write_site`, `first_prompt_write`, `first_policy_write` filtering | Compatibility shim | Retained fields, but filtering/labeling now delegates to contract helpers |
| Runtime-lineage summary first mutation owner/family extraction | Unnecessary duplication | Replaced with `reconcile_semantic_mutation_owner(runtime_lineage=events)` |
| Failure classifier existing authoritative field passthrough | Acceptable wrapper | Preserved for compatibility with projected rows; fallback path reconciles |
| Classifier `mutation_source` derivation | Intentional classifier taxonomy behavior | Preserved; it consumes authoritative family when available but does not define attribution precedence |
| Fallback/sanitizer/repair owner-bucket fields | Intentional adjacent ownership signals | Preserved; they are source evidence, not semantic mutation authoritative attribution |

## Adoption Changes

CU6 made three compatibility-preserving adoption changes:

- `game.final_emission_meta` now uses the governed write-site family set.
- `tests.helpers.golden_replay_projection.project_turn_observation` now uses `selected_semantic_mutation_write_site` and `semantic_mutation_write_site_label` for compatibility diagnostics.
- `game.runtime_lineage_telemetry.summarize_runtime_lineage_events` now uses reconciliation for first mutation owner/family/evidence fields.

No observable runtime behavior changed.

## Intentional Exceptions

The following remain outside authoritative semantic mutation attribution by design:

- Fallback split-owner fields (`fallback_selection_owner`, `fallback_content_owner`, owner buckets) because they describe fallback provenance and content/selection splits.
- Sanitizer owner fields because they are sanitizer lineage/provenance evidence.
- Repair-kind fields because they classify repair mechanism, not authoritative mutation ownership.
- Classifier taxonomy, severity, primary/secondary owner, and `investigate_first` routing because those are failure-classification behavior, not attribution precedence.
- Dashboard evidence formatting because it renders classifier rows and does not infer owners.

## Compatibility Review

CU6 validates that these payload shapes still function:

- legacy payloads without write-site records
- malformed legacy `semantic_mutation_write_sites` values
- minimal payloads with no mutation evidence
- partial selected metadata with only family/file evidence
- candidate-only write-site records
- projection-inference-only records

Candidate-only evidence remains diagnostic and non-authoritative.

## Reporting Consistency Review

The reporting surfaces agree for identical evidence:

- Golden replay projected rows expose authoritative owner/family/write-site/evidence source from reconciliation.
- Failure classifier rows preserve those same authoritative fields.
- Dashboard markdown renders the same authoritative attribution and labels projection inference explicitly.
- Runtime lineage summaries now reconcile first mutation attribution instead of extracting owner/family independently.

## Remaining Technical Debt

- The classifier still has intentional routing logic for `mutation_source`, taxonomy, severity, and investigation target. This is not duplicate authoritative attribution, but it remains adjacent and should stay covered by classifier governance.
- Fallback/sanitizer split-owner vocabularies remain broad adjacent attribution surfaces. They are intentionally not collapsed into semantic mutation ownership.
- Existing CU2-CU4 worktree changes remain the foundation for CU6; CU6 did not attempt to normalize unrelated pre-existing files.

## Validation Commands / Results

Passed:

- `python -m pytest tests\test_semantic_mutation_contract_adoption.py -q --tb=short --basetemp=codex_pytest_tmp_cu6`
- `python -m pytest tests\test_semantic_mutation_contract_adoption.py tests\test_semantic_mutation_attribution_governance.py tests\test_semantic_mutation_attribution_cu4.py tests\test_golden_replay_projection_semantic.py tests\test_failure_classifier.py tests\test_runtime_lineage_telemetry.py -q --tb=short --basetemp=codex_pytest_tmp_cu6_focus`
- `python -m pytest tests\test_final_emission_meta.py -q --tb=short -k "semantic_mutation or runtime_lineage or mutation" --basetemp=codex_pytest_tmp_cu6_meta`

As in CU5, the local shell has no `python` on `PATH`; these were executed with the bundled Codex Python plus `.venv` packages through `PYTHONPATH=.\.venv\Lib\site-packages`.
