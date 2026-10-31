# 07 — Deterministic Validation

PR-PLAY-07 · 2026-10-29 America/New_York. Synthetic-provider evidence only.

| Fixture | Structural | Semantic / opening reason | Expected / actual acceptance | Commit | Result |
|---|---|---|---|---|---|
| S1 | accepted_structured_response | valid opening | True / True | True | PASS |
| S2 | accepted_structured_response | generic_information_request_fallback | False / False | False | PASS |
| S3 | structured_validation_failure | malformed_envelope | False / False | False | PASS |
| S4 | missing_structured_envelope | malformed_envelope | False / False | False | PASS |
| S5 | accepted_structured_response | valid opening | True / True | True | PASS |
| S6 | accepted_structured_response | valid opening | True / True | True | PASS |
| S7 | accepted_structured_response | valid opening | True / True | True | PASS |
| S8 | accepted_structured_response | valid opening | True / True | True | PASS |
| S9 | accepted_structured_response | safe_nonresolution | False / False | False | PASS |
| S10 | accepted_structured_response | valid opening | True / True | True | PASS |
| S11 | accepted_structured_response | valid opening | True / True | True | PASS |
| S12 | accepted_structured_response | safe_nonresolution | False / False | False | PASS |

S1–S12 use existing schema and real endpoint/pipeline with synthetic SDK responses.
Exact fixture, before/after, expected/actual, structural/semantic/outcome events are in
matrix/S*.json. S5 lacks optional proposals; S6 ignores unknown provider fallback metadata,
while actual host safe-provenance separately rejects. S7 confirms type derivation despite
question-shaped input, followed by normal endpoint start; not an intentionally broken router.
S8 reuses authored guards/runner introduction, creates no NPC record. S9 appends unauthorized
key/gold acquisition and rejects. S10 repeats Start, one dispatch/commit. S11 first fails
without progression then succeeds once, two attempts total. S12 existing rich fixture gives
structural success then safe provenance with unauthorized_resolution_decision_fact.
These are related synthetic controls, not exact historical or held-out reproduction.

Focused 86 pass/0 failure: matrix, optional capture/default/
oversize/count/control/write failures, ledger failure, PR04 integrity, PR05 diagnostics,
PR06 budgets and frontend source checks. Broader: provider 88
pass/1 failure; structured 60 pass; ordinary/NPC direct
37 pass; world/factions/opening planning/ATGB interpretation
123 pass; review/export 11 pass.
Total completed nonduplicate current-source checks: 405 pass / 1 failure, plus 9 Node
UI cases. Entry-source comparator separately reproduces the same one failure. Full suite,
live behavior, ATGB performance and independent generalization not run/claimed.

State regressions: invalid/nonresolution no commit; valid once; repeated/concurrent Start;
failure->success; persistence exception rollback; world/faction consistency and ordinary
fallback intact. PR05 compares full persisted JSON values/inventory allowing documented
save/debug/empty-log bookkeeping. Diagnostics live outside gameplay state. Provider controls
verify atomic admission, no extra request/retry, unchanged 3000 opening/600 ordinary limits,
aggregate accounting and explicit incomplete-status rejection. New stages reconcile without
double counting diagnostic usage copies. See XML, command/duration manifests, UI JSON and
test_summary.json; integrity.json verifies protected normal/frozen/experiment hashes.

Failure classes:
- Preexisting: test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution
  asserts current frozen source attestation, which is stale. Reproduced using saved dirty
  entry GM/API/immutable/budget source via pr_play_07_entry_source. Not repaired.
- Environment-blocked/unresolved transport coverage: bounded 90-second HTTP-bearing focused,
  structured raw_chat_stub, ordinary, opening and scene-canon attempts timed out. Partial dots
  are not counted. Completed direct slices exclude blocking HTTP cases. Prior PR06 rich
  emission/conversation assertion failures are documented history, not newly reproduced here.
- Tool setup: initial missing --basetemp parent caused FileNotFoundError; driver now creates
  parent. Initial logs retained, not counted as product failures.
- Development-only regression: new diagnostic stages initially rejected by accounting reader;
  fixed and PR05 reconciliation/final focused checks pass. No relevant new completed-scope failure.

Rendered UI, full HTTP transport and live provider semantic adequacy remain unproven.
