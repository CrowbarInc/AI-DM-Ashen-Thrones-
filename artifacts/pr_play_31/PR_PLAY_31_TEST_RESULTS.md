# PR-PLAY-31 test results
Raw logs and JUnit XML are preserved. Test transports are blocked by tests/conftest.py's live model guard; interpretation/opening/narration are deterministic mocks only.

Baseline primary: 210 passed, 1 setup error / 211 including one historical failure-observation test. Comparable subset: 210 cases (209 passed, one Windows atomic-file setup error). Baseline additional: 75 passed, seven failed / 82. Baseline inventory typo: zero collected, corrected immediately; log retained.

Final focused run: 99 passed / 99, zero failures/errors/skips, 15.45s. This includes 59 new tests plus 40 existing overlay and harness controls.
Final comparable suite: 285 passed, 7 failed / 292, 0 errors, 0 skipped, 41.88s. All seven assertion failures match baseline nodes exactly. New assertion failures: zero. The baseline WinError 5 and a separate intermediate combat.json WinError 5 did not recur in the final run. They are transient Windows filesystem errors, not fixed by this change. Intermediate implementation failures are preserved in smoke/probe logs and resolved in final runs.

Unchanged historical failures:
- tests.test_clue_idempotence::test_apply_socially_revealed_leads_twice_preserves_canonical_state
- tests.test_investigation_result_provenance_non_invention::test_general_written_surface_question_discovers_authored_clue
- tests.test_investigation_result_provenance_non_invention::test_general_visible_evidence_may_be_reported
- tests.test_investigation_result_provenance_non_invention::test_general_valid_target_no_evidence_is_grounded_absence
- tests.test_investigation_result_provenance_non_invention::test_general_requested_identity_absent_does_not_mint_person
- tests.test_investigation_result_provenance_non_invention::test_general_observe_empty_target_does_not_invent
- tests.test_investigation_result_provenance_non_invention::test_frontier_gate_t15_look_toward_does_not_mint_personnel_timing

No unrelated historical failure was repaired. The historical PR-PLAY-30 observation harness is intentionally not rerun as a post-repair acceptance test: it asserts that the exact bug still occurs. Its before-run trace is retained; new integration replaces that assertion with the required clarification/travel/examination contract.

No complete repository-wide suite was run; the comparable affected suite covers movement, decomposition, clue knowledge/discovery/idempotence, investigation provenance, state/narration integrity, expression validation, topic authority, confidentiality and privileged reads.

Performance: destination-only microbenchmark over 10000 iterations: before 14.92 us, after 15.10 us per call. Actual mocked-pipeline latencies are in performance.json. Extra provider calls/retries/planning loops: zero. Route matching is deterministic over current authored exits and known clue text; no embedding or semantic search. Interpretation latency on original request remains zero provider requests; clarification avoids interpretation entirely.

Final source verification after the last parsing/status adjustments: 113 passed, zero failures/errors in 9.32s (new focused module + movement + local interaction). See post_review_verification.xml/txt.
