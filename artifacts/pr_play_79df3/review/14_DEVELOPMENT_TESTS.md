# Development Tests

Final-source run: `python -m pytest tests/test_pr_play_79df3_classification.py tests/test_pr_play_79df2_publication.py`.

Result: **63 passed, 0 failed, 0 skipped, 0 errors.** JUnit: `artifacts/pr_play_79df3/development_tests.xml`. Elapsed about 12 seconds. `ASHEN_TEST_EVIDENCE_DIR` pointed at this artifact directory. Storage isolation remained installed.

The classification file contributes 27 tests:

1. Request ceiling before dispatch.
2. Input-token ceiling.
3. Output-token ceiling.
4. Total-token ceiling.
5. Accounting unavailable.
6. Playtest ceiling.
7. Token estimate unavailable.
8. Provider exception after a send.
9. Model mismatch after a send.
10. Malformed provider output stays gameplay.
11. Context leak stays gameplay.
12. Clarification stays gameplay.
13. Unsupported action stays gameplay.
14. The recorder writes nothing for the operational class.
15. HTTP 500 stays an error category.
16. Projection hides the class, and `static/app.js` still renders player-facing text.
17. A duplicate refusal writes no event.
18. Two refusals, then an examination, advance the pointer once.
19. Repeat investigation does not reveal the canary.
20. Save and reload keep the preceding publication.
21. A refusal does not touch another campaign store.
22. Accepted dialogue stays gameplay.
23. Grounded fallback stays gameplay.
24. Physical narration remains one expression.
25. A second expression is not requested.
26. HTTP fallback is not an operational refusal.
27. State stillness is not operational.

The publication file contributes the remaining 36 tests from PR-PLAY-79D-F2, including parametrized cases. Those assertions were not weakened.
