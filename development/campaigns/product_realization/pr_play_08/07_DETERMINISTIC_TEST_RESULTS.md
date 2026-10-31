# Deterministic Test Results

PR-PLAY-08 · 2026-10-29 America/New_York. Offline development tooling only.

Final harness/coverage lane: 35 passed (26 harness checks plus nine registry checks).
H1–H20 are deterministic tooling assertions; negative fixture outcomes deliberately
FAIL while their corresponding harness test PASS confirms correct measurement.

| ID | Case | Observed / asserted | Check |
|---|---|---|---|
| H1 | Successful opening | PASS, one commit | PASS |
| H2 | Output truncation | FAIL; provider_output_limit_exhaustion | PASS |
| H3 | Invalid JSON | FAIL; json_parsing_failure | PASS |
| H4 | Missing envelope | FAIL; structured_envelope_failure | PASS |
| H5 | Semantic rejection | FAIL; semantic_validation_failure | PASS |
| H6 | Genuine safe nonresolution | FAIL; opening_acceptance_failure; zero commit | PASS |
| H7 | Provider exception | FAIL; provider_exception | PASS |
| H8 | Admission budget rejection | FAIL; provider_admission_rejection; zero dispatch | PASS |
| H9 | Rollback | FAIL outcome / PASS state integrity | PASS |
| H10 | Commit once | PASS; turn/log/commit=1 | PASS |
| H11 | Preflight failure | BLOCKED; no owned process or provider request | PASS |
| H12 | Startup timeout | BLOCKED; bounded owned-process shutdown | PASS |
| H13 | Interrupt | INCONCLUSIVE; ZIP/state preserved; process stopped | PASS |
| H14 | Missing journal | INCONCLUSIVE; explicit limitation | PASS |
| H15 | Deterministic boundary | Zero live calls; external connect refused | PASS |
| H16 | Unauthorized Live | BLOCKED before worker/provider dispatch | PASS |
| H17 | Occupied port | BLOCKED; unrelated listener survives | PASS |
| H18 | Evidence archive | Readable ZIP; all manifest hashes match | PASS |
| H19 | State categories | Bookkeeping separated; injected truth mutation rejected | PASS |
| H20 | Unknown category | Explicit unknown; root cause unestablished | PASS |


Additional checks: scripted observation, Live multi-turn refusal, scenario/global
limit enforcement, incomplete/empty categories, classification precedence and log
redaction. Evidence: harness_regression.xml/.txt; H1_H20_results.json; matrix_runs.json.

| Lane | Passed | Failed | Errors | Timeouts |
|---|---:|---:|---:|---|
| diagnostics | 81 | 0 | 0 | None |
| export_atgb | 55 | 1 | 0 | None |
| harness | 35 | 0 | 0 | None |
| opening | 23 | 3 | 0 | None |
| provider | 88 | 1 | 0 | None |
| structured | 60 | 1 | 0 | None |
| world | 123 | 0 | 0 | None |


Completed scope totals: **465 passed / 6 failed / zero errors/timeouts**.
No full-suite claim. All lanes use existing pytest/live-model guards and bounded
120-second owned-process timeouts. The final harness-only rerun updated its exact
command record; broader XML and logs retain measured outcomes, with lane commands
defined in tools/validate_pr_play_08.py.

Failure classification: six preexisting defects, zero demonstrated new production
regressions. Three rich-opening emission/length assertions and the saved stew-price
conversation assertion match documented PR-PLAY-06/07 baseline failures. Two tests
call the same stale provider source-attestation readiness audit (one provider test,
one ATGB accounting test). The production and frozen fixture sources those tests
inspect are hash-identical across this pass, and none of those test files changed.
No unrelated repair, threshold relaxation, source-attestation rewrite or production
change was made to obtain green results. Details remain in each failing lane log.

Initial HTTP runs under the restricted sandbox were environment-blocked at Python
socketpair/event-loop creation; bounded local-only probe reproduced it. With
localhost execution permitted, the same deterministic harness and HTTP regression
paths complete. Early harness-development failures and their corrected reruns
are preserved separately; they are not counted as final product regressions.
