# 06 — Authority and Regression

## Completed checks

- Focused production request, evidence, correction, mechanical revision and participant lane: **198 passed** (focused_verified.xml).
- Broader relevant slice: **332 passed, 39 HTTP cases explicitly deselected** (after_nonhttp.xml and http_after_inventory.json).
- The same broader entry slice before editing: **314 passed, the identical 39 cases deselected** (baseline_nonhttp.xml). The added 18 are the new R2-04 tests. No completed-slice failure was excluded to obtain these counts.

Broader source modules: PR-EF-R4 authorization, PR-EB conversational continuity, PR-BR-C16 interaction completion, PR-EA orchestration, PR-BR-C22 commitment, R1-02 revision boundary, R1-07 correction contract, PR-CK ordinary resolver selection, PR-EF-R2 social authority, directed social routing, vocative direct address recovery, PR-BR-C25 semantic ownership and R2-02 participant grounding; after-run also includes R2-04. Exact node inventories and JUnit results are packaged. Existing Starlette TestClient deprecation warning remains.

## Failure / incomplete-execution classification

New product regression: none demonstrated in completed scope. Preexisting product failure reproduced in completed scope: none. Two R2-02 historical failures (C22 raw_chat_stub and directed_social hailing_runner) are recorded as historical known failures, not newly reproduced: both belong to the currently blocked HTTP inventory.

Environment-blocked: pre-change explicit-local-temp attempts with .venv Python 3.12.0 and bundled Python 3.12.14 stalled after 353-item collection before the first TestClient test completed; both were interrupted. The HTTP transport family was explicitly inventoried/deselected by a temporary AST/call-reference and fixture scanner. All 39 omitted node IDs and the selector source are included. This is a limitation, not a passing HTTP result; OS/network/event-loop root cause is undiagnosed. No provider connectivity diagnostic ran.

Indeterminate: the first default-temp interrupted run printed setup errors/failures but never emitted tracebacks, node names or a final summary. Its partial log is retained as baseline_regression.txt and is not counted as a completed result. No unsupported root-cause classification of those individual events is made.

Harness implementation errors: early new-test logs focused.txt and focused_final.txt show incomplete/misapplied synthetic social session fixtures. Corrected to R2-03's per-scenario sessions; intended assertions remained exact. Also the first capture script used the wrong original-log input key and failed before dispatch; corrected to the trace's player_input. Neither required production changes. Raw early logs remain packaged.

No full-suite execution or complete broader HTTP result. Verdict remains conditional for this coverage gap. TestClient is not repaired and unrelated prior product failures are not repaired. regression_summary.json records all categories and limitations.

## Authority

Evidence membership rejects unavailable clue IDs. Public request captures exclude the undiscovered posted route; controlled output selects no hidden passages. Existing authorization/social/participant/correction/revision tests protect NPC knowledge, off-scene recipients, pending/committed intent and unsupported claims within selected cases. Canonical protected data (including world, session, combat, scene, logs and frozen ATGB) is byte-identical to entry; no unauthorized world, combat, simulation time, event or faction mutation occurred. Test fixtures use isolated temp stores or in-memory copies.

1,301 protected entry hashes were checked; only the authorized production instruction changed. AST equality outside that literal and exact schema equality prove host, parser, provider, combat/event/faction/time owners and safeguard implementation unchanged. This is instruction compatibility plus deterministic authority evidence under tested inputs; it is not live authority preservation or proof that future model selections will be valid.
