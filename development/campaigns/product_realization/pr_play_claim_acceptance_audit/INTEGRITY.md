# Integrity

Milestone `pr_play_claim_acceptance_audit`. Branch feature/product-realization; HEAD d40f1ed198236c604085f1c842ead267a8104ce2. Dirty work preserved; entry status retained. No commit/push/reset/clean/stash/revert. No production/test/frozen/config/data edits. “Do not alter worktree” governs investigation inputs; the explicitly requested reports/handoff are authorized outputs.

Before behavior tracing, all 1,294 predecessor manifest hashes matched and aggregate identity verified: 02fb4ccf8ae2d016aef1ba6b2d140279c04285e734cedf56764f8f3a1c8cf151. No baseline regeneration or hypothetical historical checkout. Historical origin stays closed. Relevant source hashes in source_hashes.json. Final seal rechecks all paths and branch/HEAD. Existing large baseline archives are not duplicated.

Executed from repository root:

```powershell
.\.venv\Scripts\python.exe artifacts/pr_play_claim_acceptance_audit/run_audit.py
.\.venv\Scripts\python.exe artifacts/pr_play_claim_acceptance_audit/run_controls.py
.\.venv\Scripts\python.exe artifacts/pr_play_claim_acceptance_audit/analyze_traces.py
```

Exact pytest args/flags and collected ids retained. Disable flags, fail-closed nonloopback network guard and existing storage isolation apply before imports. Runs sequential: 235 tests 219/16; 146 tests 139/7. Total 381 tests 358 passed / 23 failed, zero errors/skips; original 356 baseline plus 25 mechanical passes. Failure-id sets match. Both report 1,292 protected files unchanged, zero additions and zero external network attempts. Final manifest check includes requirements and pytest config. Probe inputs unchanged. Live provider calls: **0**.

Nine reports created in development/campaigns/product_realization/pr_play_claim_acceptance_audit/: SUMMARY, PIPELINE_TRACE, CLAIM_CLASSIFICATION, THREE_CASE_ANALYSIS, AUTHORITY_GAP, NEGATIVE_CONTROLS, IMPLEMENTATION_OPTIONS, NEXT_STEP_DECISION, INTEGRITY (all .md).

Evidence under artifacts/pr_play_claim_acceptance_audit/: baseline verification, entry status/handoff, source hashes, guarded run/probe/report/seal scripts; exact commands, collected nodes, JUnit, failures, output and integrity; raw HTTP/stage captures; compact three-case trace/summary, classification matrix/probes, negative controls, related-publication summary and test_results. evidence_manifest.json binds hashes/sizes and packaging status; files_created.json records final inventory. All new investigative evidence, including full raw captures, is packaged. Existing large predecessor archives are referenced rather than duplicated. Final build/seal records stay external to avoid circularity.

Handoff: prepend docs/NEXT_SESSION.md preserving historical bytes; regenerate stable review Markdown/manifest/ZIP via tools/build_review_handoff.py with explicit config; create a fresh New York timestamped CURRENT_REVIEW(YYYYMMDD-HHMMSS).zip. Do not edit generated review manually.

Verification: reopen stable and dated ZIP; CRC test; internal milestone and nine reports; manifest member SHA-256/canonical bytes; packaged NEXT_SESSION/historical suffix; evidence-manifest identities and omissions; source and prior dated-archive preservation; stable/dated equality. Final cryptographic seal is external to avoid circular self-hashing. Exact archive path/hash and PASS checks are in archive_verification.json, archive_contents.txt and archive_sha256.txt. This describes the protocol; completion is claimed only after final seal PASS.
