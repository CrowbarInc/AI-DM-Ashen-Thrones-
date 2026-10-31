# 04 — Deterministic Validation

Evidence scope: structural/runtime under controlled substitutes, not live semantic
playability. Focused suite: 30 passed, zero failed/errors/skipped, 3.428s JUnit.
Source: tests/test_pr_play_02_controls.py. All production wire clients are replaced
or use the installed SDK's entirely local MockTransport. Existing pytest live guard
remains in force. No live provider call is authorized or performed.

| Required check | Effective-boundary evidence |
|---|---|
| A/J ordinary compatibility | Seven owners with flag absent omit max_retries; ordinary gate absent even with stopped budget; established regression tests |
| B SDK suppression | Seven owners with flag enabled receive zero; actual SDK property and single mocked 429 transport verified |
| C/D six/seventh | Seven parameterized production owners each admit six, refuse seventh before SDK, dispatch count six |
| E multiple pathways | Interpretation/narration share six in three pairs; seven-owner coverage includes expression, contract, candidates, planning, preflight |
| F multiple turns | Six actual api.chat submissions invoke production interpretation request under a controlled orchestration substitute; seventh submission stops, counter stays six |
| G failed attempt | Production interpretation timeout consumes one; usage null; existing unknown-usage policy rejects further calls |
| H state integrity | Exhausted chat, pending-confirmation text, OOC and opening cannot reach state loads/saves or interpretation; no action execution |
| I concurrency | Sixteen threads call production interpretation/narration; six dispatch, ten refusals; durable ledger reconciles |
| K diagnostics | Sequence 1–6, purpose, known usage sum 72 mock tokens, rejection not counted as dispatch, unknown usage null, zero SDK retries and host-disabled classification |

Additional isolated-data subprocess imports storage with ASHEN_DATA_DIR, invokes
the real hard-reset owner, and confirms silent reset, empty transcript and separate
Start Campaign requirement. Existing-ledger restart refusal, duplicate dispatch,
accounting I/O failures, interruption/unknown usage and owner lifecycle coverage
also pass in the established accounting regression suite, apart from the already
stale source-attestation test described in report 07.

Raw reproducible offline sample: capture_controls.py, mock_concurrent_ledger.jsonl,
mock_concurrent_snapshot.json and constructor_evidence.json. Six mocked calls and
ten refusals, zero live requests. Its reported tokens are fixture values, not billed
usage. Scheduling determines which callers win; explicit sequential tests establish
shared-path coverage independently. Failed-attempt evidence is in focused.xml and
the test assertions, not relabeled as a live failure.

No independent held-out generalization, gameplay benchmark, human scoring, live
repair-effect result or semantic conversational-improvement claim is made.
