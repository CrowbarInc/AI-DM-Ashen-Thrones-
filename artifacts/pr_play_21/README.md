# PR-PLAY-21 external review index

Start with `PR_PLAY_21_FINAL_VERDICT.md`, then the baseline reproduction, trust
model, repair report, related endpoints, and test results. The authorization
contract was written before the production change.

`baseline_http.json` and `repaired_http.json` preserve nine HTTP request results
each. Presence flags use original serialized text; restricted non-sentinel strings
in exported read evidence are redacted. `authorization_trace.json` maps selector,
check, response and original/repaired status. `initialization_and_action.json`
contains complete public serialized initialization/state/action and denial text.
Only temporary test campaigns were used. No real player save or .env is included.
Read capture originally observed an empty snapshot directory; the final harness
explicitly isolates snapshots too.

`source_diff.patch` isolates one production helper repair, three test migrations,
and one new test file. The untracked PR-PLAY-20 test's before-image was reconstructed
by reversing this pass's exact six-line replacement; no unrelated PR-PLAY-20
changes are included. `baseline_api_ui_mode.py.txt` is the actual pre-change
tracked resolver, hash-checked against the baseline capture with LF/CRLF handling.
`source/` contains final changed files plus relevant existing policy/projection
and launcher code. `api_boundary_source_excerpt.txt` preserves numbered API
boundary context without packaging the entire large API implementation.

This is an incremental review package against the current PR-PLAY-20 workspace,
not a standalone repository distribution or patch against a pristine HEAD.
The repository already had substantial unrelated edits, deleted historical
handoffs, and untracked files. They were neither cleaned up nor packaged.
The validation fixtures depend on existing repository tests/helpers and current
opening implementation. Run from the repository with its existing .venv:

```
.venv/Scripts/python.exe -m pytest tests/test_pr_play_21_privileged_reads.py --tb=short
.venv/Scripts/python.exe artifacts/pr_play_21/capture_http.py artifacts/pr_play_21/repaired_http.json
```

Use a separate pre-change checkout to recreate the baseline; do not disable the
repair in a running application. There is no production authorization override.
The complete relevant-suite commands and failure classifications are in the test
report. Both broad runs retain 17 known functional failures and a separate
transient Windows file-I/O error; targeted retries pass. This package does not
claim a fully passing suite, deployed-network validation, HTTP author support,
or live-model gameplay validation.

`MANIFEST.json` inventories sizes and SHA256 hashes. `build_review.py` builds and
opens the ZIP, tests CRCs, and verifies every member against its manifest hash.
It writes `archive_verification.json` beside the evidence directory after the
archive has closed. Nothing was committed or pushed. Await external review.
