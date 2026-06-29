# CU5 Semantic Mutation Attribution Governance

## Scope

CU5 promotes semantic mutation attribution from diagnostic evidence into a governed compatibility contract. This pass is diagnostic and test-only around existing projection/classifier consumers. It does not change emitted text, runtime selection behavior, write-site instrumentation, protected replay schemas, or replay corpus size.

## Contract Definition

Authoritative semantic mutation attribution is governed by `game.semantic_mutation_attribution.SEMANTIC_MUTATION_ATTRIBUTION_CONTRACT`.

Required guarantees:

- Exactly one authoritative mutation owner is selected for an emitted mutation.
- The authoritative owner is selected by the governed evidence precedence order.
- Candidate-only evidence never becomes authoritative.
- Projection inference is used only when no stronger evidence exists.
- Stronger authoritative evidence is never overwritten by weaker evidence.

Governed write-site families:

- `fallback`
- `final_emission`
- `policy`
- `prompt`
- `repair`
- `sanitizer`

Governed evidence precedence:

1. `write_site`
2. `runtime_lineage`
3. `fallback_provenance`
4. `sanitizer_lineage`
5. `fem_mutation_lineage`
6. `stage_diff`
7. `projection_inference`

## Validation Rules

`validate_semantic_mutation_contract` returns structured diagnostics:

- `valid`
- `errors`
- `warnings`
- `contract`
- `evidence_sources`
- `expected_attribution`
- `actual_attribution`

It validates:

- write-site family membership
- evidence-source precedence
- selected active-stream consistency
- candidate-only consistency
- authoritative owner/family/write-site consistency
- authoritative evidence-source consistency
- projection-inference fallback behavior

Malformed metadata is diagnostic, not fatal. Legacy payloads without attribution fields remain valid when no mutation evidence exists.

## Governance Guarantees

The CU5 test suite locks:

- one authoritative owner for emitted mutations
- no authoritative owner when no mutation evidence exists
- candidate-only records ignored by reconciliation
- projection inference blocked from overriding explicit write-site evidence
- unknown write-site families rejected by validation
- invalid precedence ordering rejected by validation
- malformed attribution metadata tolerated without runtime failure

## Compatibility Guarantees

Replay projection fields remain optional diagnostics. CU5 does not add protected observation fields and does not promote `semantic_mutation_write_sites` or authoritative attribution fields into the protected replay schema.

Existing compatibility behavior is preserved:

- explicit write-site evidence outranks projection summaries
- legacy projection inference still fills attribution only when stronger evidence is absent
- candidate-only upstream records remain visible diagnostically but non-authoritative

## Replay Implications

Replay projection now has a reusable validator to prove:

- authoritative owner matches reconciliation
- authoritative family matches reconciliation
- authoritative evidence source matches reconciliation
- projection fields remain optional
- protected schemas remain unchanged

The replay checks use existing synthetic/minimal turn fixtures and do not expand the replay corpus.

## Classifier Implications

Classifier governance verifies attribution is additive evidence only. CU5 preserves:

- failure taxonomy
- severity
- investigation target
- behavioral reclassification rules

Rows may carry better attribution evidence (`authoritative_mutation_owner`, family, write site, evidence source, confidence, projection-inference flag) without changing semantic-mutation routing.

## Reporting Implications

Dashboard/report helpers already render contract-owned evidence manifest fields. CU5 verifies:

- authoritative attribution appears when available
- projection inference is labeled via `authoritative_evidence=projection_inference` and `projection_inference=True`
- candidate-only evidence is not displayed as authoritative

No dashboard redesign was performed.

## Tests Executed

Passed:

- `python -m pytest tests\test_semantic_mutation_attribution_governance.py -q --tb=short --basetemp=codex_pytest_tmp_cu5`
- `python -m pytest tests\test_semantic_mutation_attribution_governance.py tests\test_semantic_mutation_attribution_cu4.py tests\test_golden_replay_projection_semantic.py tests\test_failure_classifier.py -q --tb=short --basetemp=codex_pytest_tmp_cu5_focus`
- `python -m pytest tests\test_runtime_lineage_telemetry.py tests\test_final_emission_meta.py -q --tb=short -k "semantic_mutation or runtime_lineage or mutation" --basetemp=codex_pytest_tmp_cu5_lineage`

The local shell has no `python` on `PATH`; commands were executed with the bundled Codex Python plus `.venv` packages through `PYTHONPATH=.\.venv\Lib\site-packages`.

## Remaining Deferred Work

Deferred by CU5 non-goals:

- no new write-site instrumentation
- no prompt or policy redesign
- no replay schema promotion
- no protected replay corpus expansion
- no dashboard redesign
- no runtime behavior changes
