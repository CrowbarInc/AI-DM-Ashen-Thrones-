# 04 — Instrumentation Audit

No production logging was added. The harness reads instruments that already exist and stores them beside the frozen labels.

## Already recorded

| Need | Existing instrument |
|---|---|
| Raw planner input and output | `ASHEN_SEMANTIC_TRACE_PATH` when the real provider runs |
| Parsed plan, reason, sufficiency, selected ids, authorized text, host line | Locked plan on the API decision / social binding |
| Provider model, request id, token counts, latency, sent, refusal | Provider budget ledger. Request content is not stored there. |
| Expression audit | `gm_output.metadata.expression_generation` |
| Final adopted speech | `accepted_response` plus `verify_delivery_record` |
| History match | Last `delivered_exchanges` row |
| Topic integrity | Canonical topic snapshot before and after the turn |

The harness row in `baseline.jsonl` keeps the plan, the raw proposal (baseline only), provider calls, checks, and the rubric score.

## Not a separate production trace

These values exist only inside `authorize_information_turn` and are visible if the locked plan retains them:

- `source_relevance` (coverage per source that reached the relevance closure)
- `source_propositions` after schema cleaning
- `referent_operation` and `bound_referent_id`
- `validation_failure`

A turn rejected before the source scan has no `source_relevance`. That absence is the observation that retrieval did not run. It is not a missing logger.

## Gaps

- There is no production counter for "coverage() was not called because the source proposition was missing." The harness infers that from an empty `source_relevance` or from relevance stuck at `unknown` with no selected source.
- Expression token cost is a second ledger record with purpose `expression`. Turns whose contract is `None` have no expression call. That is visible as a one-call turn.
- The provider ledger cannot be appended by a second process. A reused path fails closed before dispatch. Diagnostic runs use one ledger file per process. The failed reuse is preserved as `baseline_ledger_collision.jsonl` and is not scored.
- Restricted topic text is not placed in planner candidates (`hidden` rows are omitted). The harness still does not copy snapshot worlds into the review bundle, because those worlds contain the fixture secrets.

## Compact proposal constraint

The live provider payload is accepted only when its keys match the proposal schema exactly (`conversational_act`, `addressee_id`, `referent_operation`, `request_proposition`, `source_propositions`, `ambiguity_type`, `clarification_needed`). `requested_relationship` is projected by the host after that check. Adding `interpretation_confidence` or `proposed_coverage` to that payload returns `invalid_plan_fields` before retrieval.

The first intervention file did that and is preserved as `interventions_schema_rejected.jsonl`. It is not used for causal ranking. The valid file is `interventions.jsonl`. On a compact payload, I6 applies the gold label through the `coverage()` adapter and does not add `proposed_coverage`.

## What the harness adds

Each row records `arm`, `turn_id`, `checks`, `restricted_hits`, `score`, `intervention` notes, and latency. Gold arms add which labeled fields were substituted. The production plan object is not given a diagnostic bypass flag that later turns could honor. `install_authorized_plan` marks `gold_intervention` on the copy used for that request only.
