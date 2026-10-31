# 01 — Baseline Reconciliation

ATGB-R1-06, 2026-10-19. Read-only causal investigation; documentation and review exports only. No implementation or live-provider authority. Verdict **B — Conditional**. Primary development failure class: **contract**. The observed semantic error is selecting a clarification response to a correction the model has already understood. The specific prompt wording that induced that choice is not experimentally established.

## Repository and authority

Read `docs/DEVELOPMENT_CONSTITUTION.md`, `docs/NEXT_SESSION.md`, `docs/validation_evidence_standard.md`, `docs/product_realization_validation.md`, and `docs/review_handoff_standard.md`. The requested `support/docs/NEXT_SESSION.md` does not exist in this checkout. `support/` is a review-ZIP namespace; the constitution names `docs/NEXT_SESSION.md` as canonical. This is a path discrepancy, not missing orientation.

`artifacts/atgb/atgb_r1_06/repository_identity.json` records HEAD and branch. `repository_status_before.txt` records the extensive pre-existing dirty/untracked state, including production, canonical session data, experiments, governance and previous exports. Working-tree source, not HEAD alone, is the investigated implementation. All 480 paths in R1-05's entry manifest still match their preserved hashes. The relevant API, interpretation and orchestration hashes are identical in R1-03 and R1-05. A 3,870-file entry manifest additionally protects the examined historical traces, PR-EG-R6-R5 evidence and frozen ATGB data. Final integrity comparison accompanies this report. No existing changes were reverted.

## Reconciled campaign history

| Pass | Established evidence | Limit |
|---|---|---|
| R1-01 | Original S08.2 reply came from mechanical revision entry triggered by correction language with no pending action | Original model purpose was not preserved; do not infer it |
| R1-02 | Revision entry now requires explicit action-revision cues or action components with a pending/executed intention | Selected-evidence stub works; empty-evidence stub still gives ignorance, not a useful answer |
| R1-03 | Original-wording L1/L2 failed at provider transport; L3 paraphrase completed and redundantly confirmed the subject | L4 was an invalid live control due to imported environment defaults; not live authority evidence |
| R1-04 | Offline readiness/control recovery; historical 167 deterministic tests passed | Does not demonstrate conversational adequacy |
| R1-05 | Two original-wording trials completed; both recognized people, selected no passages and asked redundant confirmation. Valid L4 pending ASK revision remained pending | Historical three responses, 6,475 tokens across L1/L2/L4; no broad competence claim |
| Final PR-EG-R6-R5 | 59/164 baseline successes; 18/54 validation; correction-tagged 0/25; diagnosis B | Bind/witness/correspondence interventions are a different pathway; no integration acceptance |

## Raw-evidence discrepancies

1. R1-03 `transcripts.md` L3 says the bridge stops before the revision gate; current NEXT_SESSION repeats that the gate was not reached. The raw `L3/trace.json` contains `_pending_revision_decision` returning **null**, followed by `_communication_decision` and `decision_from_interpretation_record` returning CLARIFY. The API revisits a blocked interpretation's record. Therefore the gate was reached and abstained. The raw trace takes precedence. No historical artifact was edited.
2. R1-05 normalized evaluations call interpretation PASS. That is defensible for **subject recognition**, not conversational disposition: purpose and legacy mode both select CLARIFICATION. This report separates those judgments and preserves the original results in the behavioral packet.
3. Recent visible GM text is cut to 240 characters, but full prior GM text is also supplied in `PUBLIC answer evidence.reply:0`. A truncated recent-turn field does not establish absent antecedent evidence.
4. R1-05 L1/L2 legacy `correction.subject` is INTENTION while its note says referent; L3 uses NONE. No pending intention/action components accompany either. These inconsistencies do not change routing and are not evidence of a mechanical action revision.

## Known limitations

No intervention, model rerun, current gameplay test, or broad suite was performed. Three historical completed interpretations support a local diagnosis, not a measured repair effect. Exact request messages and responses are preserved; the full wire-level JSON-schema request is not independently captured in those traces. Schema dispatch is reconstructed from matching source hashes. No authenticated human review is claimed. Global accounting-manifest staleness and historical HTTP coverage limits remain outside this pass. Exposed benchmark and PR-EG cases are not unseen generalization.

Provenance: R1-01 report; R1-02 routing/final reports and tests; R1-03 L3 raw trace/response/before/after; R1-04 final report; R1-05 L1/L2 raw traces/response/before/after and accounting; PR-EG artifacts 03, 07, 11, 16, 25, 27, 32 and 36. The package includes a hashed explicit source inventory.
