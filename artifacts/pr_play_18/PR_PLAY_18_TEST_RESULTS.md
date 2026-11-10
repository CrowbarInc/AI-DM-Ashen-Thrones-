# PR-PLAY-18 test results

Relevant suite: **105 passed**, failures=0, errors=0. Final contract suite: **8 passed**, failures=0, errors=0. The latter includes SDK serialization and hidden-context/variant-pair tests; **107 unique tests** passed overall. JUnit XML captures are included.

Relevant suite command:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_pr_play_18_contract_alignment.py tests/test_pr_play_13_opening_renderer.py tests/test_pr_play_04_opening_integrity.py tests/test_pr_play_06_opening_budget.py tests/test_pr_play_11_claim_authority.py tests/test_opening_start_seam_regressions.py -q --basetemp=development/tmp/pr18_final --junitxml=artifacts/pr_play_18/focused_tests.xml
```

Final contract suite adds real OpenAI SDK serialization using httpx.MockTransport, a dummy credential and offline.invalid. All HTTP handling is in memory. It passes through actual application initialization, provider admission/dispatch, SDK serialization/deserialization, parser, renderer and publication. The other contract tests replace responses.create at the SDK boundary and inspect the actual kwargs.

| Required coverage | Result |
| --- | --- |
| A enabled instructions/schema | PASS: actual assembled request captured at transport |
| B disabled legacy | PASS: existing SYSTEM_PROMPT/authored-fact instructions and kwargs; accepted legacy opening |
| C ordinary-turn isolation | PASS: input messages unchanged, no text.format |
| D valid plan | PASS: actual New Campaign/Start Campaign path, authorized text published, one turn committed |
| E legacy narration | PASS: 422 arbitrary_narration_field, no publication |
| F unknown ID | PASS: 422 unknown_catalog_id |
| G unauthorized variant | PASS: 422 unknown_variant_id; approved alternate still passes existing renderer tests |
| H atomicity | PASS: gameplay documents equal authoritative pre-provider baseline; zero turn/log progression on rejection |
| I adapter preservation | PASS: strict schema reaches mocked SDK and real SDK in-memory HTTP body |
| J consistency | PASS: catalog index/variants, schema constraints, selected plan and published text agree |

Final eight contract tests perform seven mocked transport dispatches (one each), zero live provider requests. Valid opening and real SDK serialization both publish successfully; each negative attempt dispatches once and rejects before publication/commit. See offline_success.json, negative_*.json, assembled_request.json and sdk_serialized_request.json. The full relevant suite includes concurrency/repeat-start and historical acceptance/rejection regressions.

During test development, an optional jsonschema import was unavailable and removed; schema structure is checked directly and JSON is serialized by the installed SDK. The first stronger atomicity assertion uncovered documented bookkeeping plus authoritative scene-addressability hydration before opening_scope.track; final tests explicitly account for these existing operations and compare all remaining game documents. One overlapping pytest invocation hit a shared basetemp collision; final runs used dedicated paths. No production repair was made for these test setup issues. No remaining test failures. One pre-existing Starlette/httpx deprecation warning appeared in the relevant suite.
