# 07 — Deterministic Validation

PR-PLAY-09 · 2026-10-30 America/New_York · evidence_scope: structural_only.

| Lane | Passed | Failed | Errors |
|---|---:|---:|---:|
| conversation | 35 | 0 | 0 |
| diagnostics | 81 | 0 | 0 |
| export_atgb | 55 | 1 | 0 |
| gameplay | 33 | 0 | 0 |
| harness | 35 | 0 | 0 |
| opening | 23 | 3 | 0 |
| provider | 88 | 1 | 0 |
| rules_persistence | 53 | 0 | 0 |
| structured | 60 | 1 | 0 |
| world | 123 | 0 | 0 |


Completed selected scope: **586 passed / 6 failed / zero errors or timeouts**.
G1–G25 and additional safeguards are covered by 33 passing tests.
G1 proves positive evaluator behavior, not an end-to-end successful five-turn run under
the six-request production limit. The real HTTP example completes four turns and stops
for budget. Do not promote fixture controls to live-quality or generalization claims.


| G | Control | Scope |
|---|---|---|
| G1 | Five successful evaluator records; final PASS while quality remains human-review | evaluator positive control only |
| G2 | Failed opening, no Turn 1 | HTTP |
| G3 | Turn 2 provider exception, stop with journal | HTTP + native-record control |
| G4 | Turn 3 malformed interpretation; invalid narration envelope | HTTP + native-record control |
| G5 | Generic semantic nonresolution classified separately | native-record/heuristic control |
| G6 | Legitimate NPC refusal not automatically failed | evaluator |
| G7 | Unsupported world claim rejected by native hard-validation evidence | evaluator of native contract |
| G8 | Forbidden character/new-world mutation | snapshot comparison |
| G9 | Authored movement agrees with native transition | evaluator |
| G10 | Supported blocked movement accepted | evaluator |
| G11 | Next action invalidated by scene divergence | HTTP read-side fault; no persistent injection |
| G12 | Six admissions exhausted; T5 never submitted | HTTP |
| G13 | Turn timeout, worker stopped, interrupted state exported | HTTP controller fault |
| G14 | Missing text/semantic evidence stays uncertain | evaluator |
| G15 | Off-topic text is heuristic concern, not confirmed defect | evaluator |
| G16 | Exact repeated narration is a concern | evaluator |
| G17 | Descriptive response changes no state/turn | evaluator |
| G18 | Canonical engine noncombat result consistent | real resolver-derived fixture; evaluator |
| G19 | Contradictory engine outcome detected | real resolver-derived fixture with negative control |
| G20 | Inapplicable Q6 is N/A, score null | rubric |
| G21 | Narrative Q5 requires human review, no score invented | rubric |
| G22 | Exact ledger accounting, opening versus turns | HTTP |
| G23 | Zero live; external connection refused | worker subprocess + HTTP |
| G24 | Unauthorized Live blocked before worker | controller |
| G25 | Transcript/state/API/diagnostics/hash-complete export | HTTP ZIP verification |


Six failures match the pre-existing PR-PLAY-08 baseline: three rich-opening assertions,
one saved stew-price conversation assertion, and two stale source-attestation readiness
assertions. Exact names/text remain in JUnit/logs. Production sources and failing test
owners are unchanged in this pass; no unrelated repairs or threshold changes. No new
regression demonstrated in completed lanes. Initial restricted-localhost startup was
environment-blocked; deterministic lanes ran with localhost access, external provider
transport denied. Earlier instrument failures (oversized duplicated state export and
pytest's inherited interpretation-disable flags) were tooling defects corrected before
the final runs; they do not imply production defects.

Relevant lanes include prior harness, opening/diagnostics/budgets, structured/semantic,
world progression, conversation/ATGB interpretation, canonical noncombat rules,
state authority/persistence and evidence export. Commands/exits/timing are recorded in
regression_runs.json. This is no full-suite claim. No live benchmark or independent
held-out generalization was run. Entry-to-exit 471 protected hashes match.
