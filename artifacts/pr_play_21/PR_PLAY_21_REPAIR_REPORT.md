# PR-PLAY-21 repair report

Confirmed root cause: request-selected UI mode was treated as permission to
select restricted state. Policy membership and capability checks accepted any
caller requesting author/debug. The selector communicates desired visibility;
it proves no identity or entitlement.

The pre-implementation contract is preserved in `AUTHORIZATION_CONTRACT.md`.
Ordinary player HTTP requests retain their existing contracts. Explicit
author/debug HTTP requests return 403 with
`{"ok": false, "error": "privileged HTTP ui mode is not authorized"}`.
Unknown modes retain 400. There is no silent downgrade. All denial happens in
the shared `resolve_requested_ui_mode` after canonical validation and before
endpoint data access/projection. The check applies to query and supported body
forms and all resolver callers, including author writes that can return merged
campaign state. Request=None is not a privileged context.

Production change: `game/api_ui_mode.py` only (two executable lines plus
contract documentation). No game rules, opening generation, renderer, provider
schemas/prompts/models, narration, storage implementation, projection
classification, CORS or server binding changed. No new credentials or
authentication framework were introduced. All HTTP privilege is denied because
the repository supplies no trustworthy author identity. Pure internal policies,
projection helpers and storage tools retain their existing contracts.

Tests changed: new `tests/test_pr_play_21_privileged_reads.py`;
`tests/test_ui_mode_backend_integration.py`,
`tests/test_ui_mode_regression_matrix_objective15.py`, and the existing untracked
PR-PLAY-20 `tests/test_pr_play_20_response_confidentiality.py` have narrowly
updated privileged HTTP expectations. Internal lane assertions are preserved as
direct projection tests, alongside new HTTP 403 assertions. Seven formerly
passing tests explicitly required unauthenticated privileged HTTP access;
`contract_transition_tests.*` records their failures before expectation migration.
They are obsolete HTTP expectations under the documented contract, not discarded
gameplay failures. No test for the 17 known gameplay failures was edited.

Evidence additions live under `artifacts/pr_play_21`; review archive is new in
`handoff`. Existing unrelated workspace edits/deletions were left alone. The
review patch isolates this pass, including the incremental change to the
already-untracked PR-PLAY-20 test. Source snapshots and boundary excerpts are
provided for external assessment.

Compatibility: player state/log fields, opening publication, one mocked opening
dispatch, and the deterministic initiative action work through real HTTP. Hidden
facts remain persisted. Denied requests cannot load restricted data. Ordinary
public reads retain their existing composition behavior (including preexisting
derived session/addressability synchronization); this repair changes none of it.

Limitation: browser author/debug interfaces and author HTTP writes now return
403. Only existing local Python/file workflows preserve privileged access.
Restoring browser access is outside this pass. Key-based public projection is
unchanged and is not a general semantic secret detector. No broad API security
claim is made. Verdict B reflects the remaining author HTTP design gap and the
known gameplay baseline; live gameplay readiness is not asserted.
