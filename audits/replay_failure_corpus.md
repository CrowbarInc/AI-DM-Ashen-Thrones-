# Replay Failure Corpus

Controlled discovery only. No production code was modified. Baseline command:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_golden_replay.py -q --tb=short --basetemp=codex_pytest_tmp_failure_dash
```

Result: `12 passed`.

Classifier probes were run through `tests.helpers.golden_replay.classify_golden_drift` using controlled observed/expected rows. This exercises the current failure-locality surface without editing fixtures.

| Scenario | Resulting Failure | Current Observability Quality | Manual Locate Time | Actual Subsystem Cause | Replay Output Misleading? | Ideal Future Classification |
|---|---|---|---:|---|---:|---|
| `wrong_speaker` | `selected_speaker_id` expected `runner`, actual `merchant`; final text contains forbidden `Merchant`. Drift summary: structural=1, semantic=1. | Good: structural speaker id and semantic text fragment both visible. | <2 min | speaker | No | `category=speaker`, `owner=speaker`, `severity=high`, secondary `emission` if candidate authored wrong label. |
| `forced_fallback` | `final_emitted_source` equals forbidden `global_scene_fallback`. Drift summary: structural=1. | Good: final source directly identifies fallback substitution. | <2 min | fallback | Slightly, if text itself looks plausible. | `category=fallback`, `owner=fallback`, include `fallback_family` and gate stage. |
| `removed_route_metadata` | `route_kind` and `trace.social_contract_trace.route_selected` unavailable/absent. Drift summary: structural=4. | Fair: absence visible, but owner ambiguous between route emission and replay projection. | 2-5 min | projection or route | Yes, because final text may pass while route evidence is absent. | `category=projection` when raw payload has data but projection missed it; otherwise `route.missing_metadata`. |
| `emission_mutation` | `response_type_repair_used=True` when expected false; selected speaker unavailable. Drift summary: structural=2. | Fair: response-type repair flag visible; exact sublayer cause requires FEM details. | 2-5 min | emission / validator | Yes, if repaired final text looks acceptable. | `category=emission`, `source_family=response_type`, secondary `validator`, include `repair_kind`. |
| `sanitizer_leakage` | Final text contains `Planner`, `router`, `Validator`, `scaffold`; scaffold predicate true. Drift summary: semantic=5. | Good for leakage; root owner requires sanitizer/gate context. | <2 min for leakage, 2-5 min for root. | sanitizer | No, text visibly leaks internals. | `category=sanitizer`, `owner=sanitizer`, severity `critical`, include `leak_terms`. |
| `continuity_break` | Selected speaker and canonical target expected `runner`, actual `guard`. Drift summary: structural=2. | Good if canonical entry present; if absent becomes projection ambiguity. | <2 min | continuity | Possibly, if player actually used a vocative; expectation must distinguish intended override vs break. | `category=continuity`, owner `continuity`, secondary `route`; include `target_source`. |
| Existing `directed_npc_question` golden replay | Would fail if route leaves social/dialogue or selected speaker not `runner`. | Good: route, speaker, canonical entry, final source expected together. | <2 min | route/speaker depending field | No | Route mismatch -> `route`; speaker mismatch -> `speaker`. |
| Existing `sanitizer_scaffold_leakage` golden replay | Would fail on scaffold/internal terms in final text. | Good: final text predicate and optional final source. | <2 min | sanitizer | No | `sanitizer.leakage` with secondary `emission` only if sanitizer did not run. |
| Existing `opening_fallback_path` direct seam | Would fail on wrong `final_emitted_source`, fallback family, authorship source, temporal frame. | Very good: FEM fields are explicit. | <2 min | fallback | No | `fallback.opening`, owner `fallback`, secondary `emission` for selection timing. |
| Existing `thin_answer_action_outcome_final_emission` golden replay | Would fail if action outcome not repaired or generic text survives. | Good, but sublayer root requires `response_type_repair_kind`. | 2-5 min | validator/emission | Slightly, because final text may be plausible after repair. | `validator.response_type` when candidate illegal; `emission.semantic_mutation` if repair degraded meaning. |

## Observations From Corpus

- Wrong-speaker and fallback-substitution cases are already classifiable in under two minutes from current replay rows.
- Missing route metadata is the clearest projection/locality ambiguity: absence is visible, but owner is not deterministic unless the dashboard also inspects raw payload/debug trace.
- Sanitizer leakage is easy to detect semantically but needs a field for "sanitizer ran / mode / repaired count" to avoid guessing whether the sanitizer failed or was bypassed.
- Emission repairs expose source and repair flags, but precise sublayer attribution depends on FEM layer-specific metadata being present and consumed.

