# Ashen Thrones — Conversational continuity C01–C03 repair

Date: November 1, 2026 (America/New_York).

## A. Executive Summary

**PASS — REPAIR VERIFIED**

All three established failures reproduced. The current GM clarification was being filtered out as ineligible historical disclosure before the repeat rule determined which delivery was latest. That caused an older NPC statement to be selected and an absent-NPC sentence to replace the clarification.

Contract determination: **A — Clarification required for C01–C03**. A bare repeat/meaning request refers to the latest current-scene GM clarification when it matches `last_gm_exchange` and contains no explicit speaker or subject. Genuine historical references retain the existing selection and NPC-absence rules.

The correction uses the existing `last_delivered_exchange` helper for conversational recency, retaining the existing filtered history for NPC recall. Frozen expectations and fixtures were not changed. Fifteen parametrized regression controls were added to the existing test module. The targeted selection passed 18 tests; the complete adjacent selection passed 106 tests; a separate focused regression selection passed 153 tests. There are **259 distinct passing tests** across the latter two selections. Implementation and tests are uncommitted; this report is untracked.

### Preflight

| Item | Observed |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `9f6a008837438b6a9b3128b31e2cd178c7f19e90` |
| Existing tracked modification | `game/api.py`, the prior content-lint docstring repair |
| Existing untracked material | Content-lint investigation report plus 22 storage-cleanup reports/manifests |
| Overlap with this task | None: continuity implementation and its tests were initially clean |
| Environment | Existing `.venv/Scripts/python.exe`; Windows, Python 3.12.0, pytest 9.1.1, pluggy 1.6.0, anyio 4.14.2 |

Read the storage-cleanup final closeout (also reviewed in the preceding investigation), `artifacts/storage_cleanup_phase2a_regression_investigation.md`, relevant continuity implementation/tests/fixtures, and the historical continuity contract. No AGENTS.md was found in the repository inventory. Storage cleanup remains closed.

Relevant functions in `game/conversational_continuity.py`: `continuity_directive`, `record_delivered_exchange`, `delivered_exchanges`, `last_delivered_exchange`, `_pending_blocks`, `_present`, `_active_id`, `reference_subject_tokens`, `_best_exchange`, and `_absent_line`. Relevant filter in `game/dialogue_authority.py`: `historical_disclosure_permitted`, with `is_host_operation` and `is_bounded_expression` for legacy rows.

Primary tests: `tests/test_pr_eg_r2c_r2_reference_eligibility.py::test_independent_clarification_holdout`. Fixtures: `artifacts/pr_eg_r2c_r2/clarification_holdouts.json` and `clarification_freeze.json`. Supporting frozen precedence: `tests/fixtures/pr_eg_r1_continuity_holdouts.json`. Existing documentation: continuity module docstring; `artifacts/pr_eg_r2c_r2/09_CONVERSATIONAL_CONTINUITY.md` and `15_FROZEN_HOLDOUTS.md`. Historical evidence files were read only.

## B. Reproduction

The first test execution selected only the three requested cases:

```text
.venv/Scripts/python.exe -m pytest "tests/test_pr_eg_r2c_r2_reference_eligibility.py::test_independent_clarification_holdout[C01]" "tests/test_pr_eg_r2c_r2_reference_eligibility.py::test_independent_clarification_holdout[C02]" "tests/test_pr_eg_r2c_r2_reference_eligibility.py::test_independent_clarification_holdout[C03]" -q -p no:cacheprovider --basetemp <fresh-temporary-root>/pytest
```

A Python wrapper generated a unique temporary parent using `tempfile.mkdtemp`, supplied its unused `pytest` child as basetemp, and saved the exact expanded command and full output externally. This overrides `pytest.ini`'s reusable `development/tmp/pytest` directory. No historical pytest store was reused or removed. All later selections likewise used fresh temporary roots.

Result: **3 failed, exit 1**, all at the unchanged assertion on line 157 of the original test module. `action` was correctly `clarify`, but `line` was wrong. Direct traces confirmed GM ownership and reason `absent_npc_reference` for all three.

| Case | Request | Expected exact line | Older NPC selected incorrectly |
| --- | --- | --- | --- |
| C01 | Can you repeat that? | Which sailor do you mean: Fenn or Rook? | Harbormaster Lis |
| C02 | What did you mean by that? | Which library do you mean? | Scholar Om |
| C03 | Say that again in simpler words. | Which tower are you asking about? | Sentry Nao |

Actual C01 output:

```text
Harbormaster Lis is not here, so I will not speak to Harbormaster Lis from this place. When you last spoke, Harbormaster Lis said: "The old quay is open." Nothing new has been established since that conversation. Do you want that recalled as it stands, or are you speaking to someone here?
```

C02 returned the identical template with both occurrences of `Harbormaster Lis` replaced by `Scholar Om`; C03 replaced both with `Sentry Nao`. The full exact strings and sessions are saved in `continuity_decision_traces.json` described below.

The sole reported warning was the existing `StarletteDeprecationWarning`: using `httpx` with `starlette.testclient` is deprecated and the package recommends `httpx2`. No dependency was changed.

## C. Root-Cause Analysis

All three cases share this decision path:

1. The session records an NPC saying `The old quay is open.` in scene `harbor`.
2. It then records the case's exact clarification as a GM-owned delivery in `harbor` with no NPC speaker ID.
3. `last_gm_exchange` has category `CLARIFY`, scene `harbor`, and response exactly equal to that latest GM delivery. Pending state is `kind=ambiguous_addressee`, `status=pending`.
4. The function receives scene `{'id': 'harbor'}` and world `{'npcs': []}`. No NPC is present or active. The earlier NPC really is absent; that fact is not contradictory with the GM asking a current clarification.
5. The legacy-abstention and early-return checks do not consume these requests. `_pending_blocks` does not block a repeat/meaning request; it checks revision wording rather than treating every pending clarification as a global block.
6. `_REPEAT` matches C01 and C03; `_MEANING` matches C02. The requests have no explicit subject tokens or named target. They are understandable as requests to repeat the latest clarification, without resolving the original ambiguous intention.
7. `historical_disclosure_permitted` returns `[True, False]` for the NPC row and GM row respectively. The legacy GM row has no modern provenance seal or speaker ID. Its line does not match the limited `_HOST_OPERATION_LINE` phrases (`which statement`, `which person`, etc.) or the bounded personal-expression rule. `Which sailor`, `Which library`, and `Which tower` are therefore discarded for historical-disclosure selection.
8. Previously, `latest = rows[-1] if rows else {}` used this filtered history. It saw the older NPC row, so the current-GM-clarification short-circuit failed its ownership/matching-response guard.
9. `_best_exchange` selected the remaining NPC statement. With no present speaker, the repeat/meaning branch returned `_absent_line` and reason `absent_npc_reference`.

The defect is using historical-disclosure eligibility to establish conversational position. NPC absence handling itself is correct when an NPC statement is actually requested. Reordering all absence rules or broadly allowing legacy GM history would change more behavior than needed.

After correction, `latest` is the actual last delivered exchange. The existing narrow short-circuit sees the matching GM clarification and returns its exact response with `action=clarify`, `owner=gm`, empty NPC identifiers, and reason `repeat_pending_clarification`. The session remains unchanged, including pending intention. Filtered `rows` still supplies `_best_exchange` and every later historical-recall branch.

The Phase 2A baseline comparison and the newly reproduced failures establish that this was pre-existing development behavior, not a demonstrated consequence of cleanup. No cleanup report or history was rewritten.

## D. Contract

The intended contract is established by mutually supporting evidence:

- The continuity module's precedence contract puts explicit player wording first, then the immediately preceding delivered statement for deictic/meaning follow-ups, before earlier history and scene presence.
- `artifacts/pr_eg_r2c_r2/09_CONVERSATIONAL_CONTINUITY.md` explicitly specifies repeating a current-scene GM clarification only when the latest delivered row matches `last_gm_exchange/category CLARIFY`, with no explicit speaker/subject, preserving pending intent. It explicitly retains the historical selector for explicit recall.
- C01–C03 were frozen before the clarification repair. Their fixture SHA-256 remains `060febf1918370228b1b30f5a398ffad5fe6059a17378c24a45275b575d9fe6b`; the existing tests verify it against the unchanged freeze file.
- Existing `test_T17_actual_http_pending_clarification` covers repeat, meaning, and simpler-word requests through real in-process HTTP handling with stubbed model boundaries, exact clarification repetition, and pending-state preservation.

Historical documents' claims that C01–C03 once passed were treated as contract evidence, not as evidence of the current result. The new executions establish the present defect and repair independently.

No fixture correction or design decision was necessary. The chosen behavior is A for these three cases, with the already documented contextual guards: an explicit speaker/subject, different scene, mismatched response, non-CLARIFY category, or intervening delivery must not trigger this shortcut. A bare repeat preserves the question; it does not answer that question or execute the pending action.

## E. Changes

New changes in this task:

1. `game/conversational_continuity.py`: replace the filtered-row recency expression with `last_delivered_exchange(session) or {}`; add two explanatory comments. This reuses an existing helper. No new abstraction, state field, persisted memory, AI instruction, dependency, or provider call was added. All existing short-circuit guards remain intact; historical disclosure filtering is unchanged.
2. `tests/test_pr_eg_r2c_r2_reference_eligibility.py`: add 15 cases through two parametrized tests in the existing module. Three independent clarification phrasings test a present active NPC; 12 controls cover missing GM context, stale scene, mismatched response/category, intervening NPC/GM deliveries, NPC ownership, explicit subjects, explicit absent/present speakers, explicit ask, and scene requests. Tests assert output selection and session immutability. Original C01–C03 assertions and frozen fixtures remain unchanged.
3. This untracked report.

The prior `game/api.py` docstring change and content-lint report were preserved byte-for-byte. All original untracked cleanup reports/manifests and the frozen clarification files were checked against preflight SHA-256 snapshots and remain unchanged. The final tracked diff has only the prior API change and the two files above. No CI, ATGB, PR-PLAY, provider routing, campaign-state code, or historical evidence was modified.

## F. Verification

Environment flags for test processes:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONIOENCODING=utf-8
ASHEN_DISABLE_PROVIDER_CALLS=1
ASHEN_DISABLE_LIVE_INTERPRETATION=1
ASHEN_DISABLE_EXPRESSION_GENERATION=1
ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1
ASHEN_PROVIDER_REQUEST_LIMIT=0
```

Existing `tests/conftest.py` installs the live-model guard. Tests that exercise interpretation wiring use controlled stubs. No external provider or live game was invoked.

All completed selections used `-p no:cacheprovider` and a unique `--basetemp`. Subsequent runs also used `-o addopts=` for explicit command control. The following are pytest argument lists supplied to the existing `.venv/Scripts/python.exe` environment:

### Targeted and added regression controls

```text
-m pytest tests/test_pr_eg_r2c_r2_reference_eligibility.py -k "independent_clarification_holdout or current_gm_clarification_precedes or clarification_repeat_keeps" -q -o addopts= -p no:cacheprovider --basetemp <fresh-temporary-root>/pytest
```

**18 passed, 63 deselected, 1 warning, exit 0.** Includes original C01–C03 unchanged and all 15 added cases.

To verify the new controls against the old implementation, `git show HEAD:game/conversational_continuity.py` was compiled and loaded into the module in memory, without changing disk files or Git state. Running only the two new parametrized tests produced **3 failed, 12 passed, 66 deselected, exit 1**. Thus the added positive cases independently detect the defect, while all 12 selection-boundary expectations already pass before the repair. The corrected implementation passes both sets.

### Adjacent selection

```text
tests/test_pr_eg_r2c_r2_reference_eligibility.py tests/test_pr_eg_r1_continuity.py tests/test_pr_eb_conversational_continuity.py -q -o addopts= -p no:cacheprovider --basetemp <fresh-temporary-root>/pytest
```

**106 passed, 1 warning, exit 0** (4.39 seconds reported by pytest). Covers all tests in the affected reference-eligibility module, including HTTP clarification and resolver controls; frozen R1 NPC presence/absence, explicit addressee, historical recall, uncertainty and save/load cases; and conversational exit/ambiguity resolution state transitions.

Two initial sandboxed attempts at this combined selection were stopped without a completed summary. A diagnostic retry with `-vv -o faulthandler_timeout=30` showed 17 reference-matrix cases passing before the first HTTP test stalled. The traceback placed the blocked worker at `socket.py:accept` inside `socketpair`, called from asyncio `_make_self_pipe`; the main thread waited for AnyIO's blocking portal. The request had not reached application handling. This was local test-environment setup, not an assertion regression.

The same selection was then run with approved execution outside the restricted sandbox, still using the existing project environment, plus a process-local socket guard on `connect`, `connect_ex`, `create_connection`, and `getaddrinfo`. That guard allowed loopback only and rejected external destinations. The run completed successfully and recorded **zero external network attempts**. No source, dependency, test expectation, or OS setting was changed to address the sandbox limitation.

### Focused regression selection

```text
-m pytest tests/test_pr_eg_r2c_speech_adoption.py tests/test_pr_eg_r6_r1_disclosure_boundary.py tests/test_pr_eg_r6_r1_r1_provenance.py -q -o addopts= -p no:cacheprovider --basetemp <fresh-temporary-root>/pytest
```

**153 passed, 1 warning, exit 0** (4.40 seconds). Covers historical GM/absent-NPC ownership, multiple topics and speakers, uncertainty, exact recall, current disclosure restrictions, provenance, unauthorized historical content, and persistence. These are existing deterministic tests with model stubs/guards, not provider qualification or live gameplay.

No new failing adjacent assertion remains. `git diff --check` passed. Preflight preservation hashes matched for all saved existing reports, the prior API change, and the C01–C03 fixture/freeze. No commit, push, deletion of historical evidence, or history rewrite was performed.

### Detailed local evidence

Logs and decision traces were written outside the repository to the authorized workspace:

```text
C:\Users\Master Mandalcio\.codex\visualizations\2026\11\01\01a19720-f79c-7540-9e54-009349e81956\
```

- `continuity_before.txt`: exact initial command and original failures.
- `continuity_new_controls_before.txt`: old implementation in-memory comparison.
- `continuity_targeted_after.txt`: 18 passing targeted/control cases.
- `continuity_adjacent_retry.txt`: sandbox diagnostic progress and socketpair traceback.
- `continuity_adjacent_after.txt`: exact final adjacent arguments, 106 passes, zero external network attempts.
- `continuity_focused_after.txt`: exact focused command and 153 passes.
- `continuity_decision_traces.json`: each original session, history eligibility, request classification, before/after directives.
- `continuity_preservation.json`: preflight preservation hashes.

## G. Remaining Risks

Validation is limited to the selected 259 distinct tests; the full repository suite was deliberately not run. No live/provider behavior or remote CI result is claimed. The existing Starlette/httpx deprecation warning remains; dependency changes are outside this repair.

The correction is intentionally limited to the current matching GM clarification. Other historical-disclosure eligibility decisions, lexical reference recognition, and broader malformed-state handling are unchanged. No unresolved contract decision or additional repair is required by this investigation. Review the uncommitted changes before any separately authorized commit or push. Storage cleanup stays closed. Stop here.
