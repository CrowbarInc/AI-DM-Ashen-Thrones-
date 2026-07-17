# CU7 Semantic Mutation Acceptance Audit

Date: 2026-06-29

## Scope

CU7 is an acceptance and evidence audit for semantic mutation attribution. This pass did not modify runtime behavior, add instrumentation, redesign governance, promote protected replay schemas, or expand the replay corpus.

Evidence sources used:

- protected replay semantic mutation corpus via `tests.helpers.protected_semantic_mutation_measurement.execute_protected_replay_corpus_with_semantic_mutation_probe`
- golden replay projection fixtures via `tests.helpers.golden_replay_projection.project_turn_observation`
- BY semantic mutation fixtures in `tests/test_by_first_semantic_mutation_attribution.py`
- sanitizer, fallback, repair, prompt, policy, and final-emission attribution fixtures represented by existing CU4/CU5/CU6 tests
- governance validation via `game.semantic_mutation_attribution.validate_semantic_mutation_contract`
- classifier/reporting compatibility via CU5/CU6 tests

Validation command:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_by2_protected_semantic_mutation_measurement.py tests\\test_by3_strict_social_semantic_mutation.py tests\\test_by4_semantic_mutation_attribution_closeout.py tests\\test_by_first_semantic_mutation_attribution.py tests\\test_golden_replay_projection_semantic.py tests\\test_semantic_mutation_attribution_cu4.py tests\\test_semantic_mutation_attribution_governance.py tests\\test_semantic_mutation_contract_adoption.py -q --tb=short --basetemp=codex_pytest_tmp_cu7
```

Result: 68 passed.

## Corpus Summary

The compact audit corpus covered:

| Corpus / fixture group | Rows examined | Notes |
| --- | ---: | --- |
| protected replay | 8 | Existing protected scenarios; 3 rows had normalized semantic mutation evidence, 5 were packaging/no-mutation lineage observations. |
| golden replay compatibility | 2 | Legacy projection-only and no-mutation payloads. |
| BY semantic mutation fixtures | 2 | Prompt and policy write-site projection locks. |
| sanitizer fixtures | 1 | Sanitizer write-site family fixture. |
| fallback fixtures | 2 | Fallback write-site plus candidate-only projection fallback. |
| repair fixtures | 1 | Repair write-site family fixture. |
| prompt/policy/final-emission fixtures | 1 | Final-emission write-site family fixture. |

Adjusted semantic mutation denominator: 11 emitted semantic mutation rows. This excludes protected replay rows whose only attribution was `finalize_packaging` with `semantic_mutation_changed_count == 0`, and excludes the explicit no-mutation legacy compatibility fixture.

## Quantitative Metrics

| Metric | Count |
| --- | ---: |
| total semantic mutations | 11 |
| explicit write-site attribution | 8 |
| runtime-lineage attribution | 1 |
| projection-inference attribution | 2 |
| candidate-only write-site records | 3 |
| selected active-stream write-site records | 9 |
| malformed metadata records | 1 |
| contract validation failures, positive corpus | 0 |
| contract validation failures, negative malformed fixture | 1 |
| duplicate authoritative owners | 0 |
| missing authoritative owners | 2 |

Interpretation:

- Explicit write-site attribution is stable where present: every selected active-stream write-site row reconciled to `authoritative_evidence_source == "write_site"`.
- The only missing authoritative owners are projection-inference compatibility rows where legacy projection retains family/source but does not project `first_semantic_mutation_owner`.
- Candidate-only records were ignored as owners and did not override active-stream attribution.
- The malformed record is the existing negative compatibility fixture (`semantic_mutation_write_sites` as a non-list). It produced a diagnostic warning plus expected validation errors when an invalid projected attribution was supplied; it did not crash reconciliation.

## Family Coverage

| Family | Count | Percentage | Validation failures | Inference usage |
| --- | ---: | ---: | ---: | ---: |
| prompt | 1 | 9.09% | 0 | 0 |
| policy | 2 | 18.18% | 0 | 0 |
| sanitizer | 3 | 27.27% | 0 | 2 |
| repair | 2 | 18.18% | 0 | 0 |
| fallback | 1 | 9.09% | 0 | 0 |
| final_emission | 1 | 9.09% | 0 | 0 |
| legacy runtime family: `final_emission_mutation` | 1 | 9.09% | 0 | 0 |

Write-site family completeness: complete for the governed family set:

- `prompt`
- `policy`
- `sanitizer`
- `repair`
- `fallback`
- `final_emission`

The one `final_emission_mutation` row came from protected replay runtime lineage, not explicit write-site metadata. It remains compatible with the reconciler because runtime lineage is a stronger source than projection inference and weaker than explicit write-site evidence.

## Governance Verification

| Rule | Result | Evidence |
| --- | --- | --- |
| exactly one authoritative owner | Pass for explicit/runtime rows; legacy projection rows have family/source but owner is absent | 0 duplicate authoritative owners; 2 missing owners, both projection-inference rows. |
| valid precedence | Pass | Positive corpus had 0 contract validation failures. CU5 negative tests reject invalid precedence. |
| valid family | Pass | All explicit write-site rows used governed families. |
| candidate-only ignored | Pass | 3 candidate-only records did not become authoritative. |
| no explicit attribution overridden | Pass | Explicit write-site rows stayed authoritative even with projection metadata present. |
| projection inference only when expected | Pass | Projection inference appeared only for legacy/candidate-only rows with no stronger evidence. |

Answer to the governing questions:

- Does every semantic mutation have exactly one authoritative owner? Explicit and runtime-lineage mutations do. Two legacy projection-inference rows do not expose an owner field, only family/source attribution.
- Are write-site families complete? Yes, all six governed write-site families are represented and validated.
- Does projection inference occur only when expected? Yes.
- Does legacy replay remain compatible? Yes; malformed and partial metadata are diagnostic/compatible rather than runtime-fatal.
- Is the attribution system ready for long-term maintenance? Yes, with a small maintenance caveat for ownerless legacy projection rows.

## Compatibility Review

Legacy payload compatibility: Pass. Missing `semantic_mutation_write_sites` reconciles to no owner when no mutation evidence exists, and projection-only payloads still classify as inferred attribution.

Partial metadata compatibility: Pass. A partial selected write-site row with family/file but no explicit owner reconciles using the write-site file as owner.

Replay compatibility: Pass. `project_turn_observation` projects diagnostic attribution fields without adding them to protected observation paths.

Classifier compatibility: Pass. CU5/CU6 locks show `classify_replay_failure` consumes the governed reconciler and preserves attribution fields in semantic mutation rows.

Reporting compatibility: Pass. CU5/CU6 dashboard tests show inferred attribution is labeled, explicit owner/family/evidence are surfaced, and candidate-only owners are not promoted in reports.

Protected replay schema compatibility: Pass. No protected replay schema promotion is recommended or required by this audit.

## Remaining Projection-Inference Inventory

| Row | Family | Owner | Why explicit attribution is unavailable | Intentional? | Future instrumentation warranted? |
| --- | --- | --- | --- | --- | --- |
| `candidate_only_projection_fallback` | sanitizer | none | The only explicit write-site row is candidate-only and not selected active-stream evidence. Projection metadata is the strongest remaining signal. | Yes | No immediate instrumentation; keep as a compatibility guard for candidate-only exclusion. |
| `legacy_projection_only` | sanitizer | none | Legacy semantic trace lacks write-site metadata and replay summary intentionally does not project `first_semantic_mutation_owner`. | Yes | Minor future maintenance only: if owner precision becomes necessary for inferred rows, consider projecting legacy owner as diagnostic-only metadata without schema promotion. |

No protected replay row in the measured run depended on projection inference. Protected replay semantic mutations resolved through explicit write-site or runtime-lineage evidence.

## Readiness Assessment

Assessment: Yellow.

The attribution system is ready for long-term maintenance and can graduate from Foundation Stabilization with a documented compatibility caveat: ownerless projection-inference rows remain for legacy/candidate-only cases. This is not a runtime blocker and does not require instrumentation, schema promotion, or governance redesign.

Supporting evidence:

- 68/68 targeted replay and governance tests passed.
- 0 positive-corpus contract validation failures.
- 0 duplicate authoritative owners.
- 8 explicit write-site attributions across all six governed families.
- Projection inference was limited to 2 expected compatibility rows.
- Candidate-only records were ignored as authoritative evidence.
- Legacy and partial metadata remained compatible.

## Recommended Future Maintenance

- Keep `game.semantic_mutation_attribution` as the single reconciliation authority.
- Keep `semantic_mutation_write_sites` diagnostic and out of protected replay schemas.
- Preserve the precedence order: `write_site`, `runtime_lineage`, `fallback_provenance`, `sanitizer_lineage`, `fem_mutation_lineage`, `stage_diff`, `projection_inference`.
- Revisit ownerless projection-inference rows only if reporting needs owner-level precision for legacy inferred attribution.
- Continue using CU5/CU6 governance tests as the regression guard for candidate-only exclusion, precedence, classifier compatibility, and reporting compatibility.
