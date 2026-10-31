PR-PLAY-05 · 2026-10-27 (America/New_York) · evidence_scope: structural_only. Synthetic provider controls; no live generation or gameplay-quality claim.

# 02 — Placeholder Test Closure

The two tests protect journal-source selection and campaign-opening integration, not invalid-output rejection. Their old `[Narration]` fixture cannot establish a scene and must not be accepted. Changing their expected status to 422 would erase their intended coverage.

Added `_structured_opening_fixture`, which invokes the actual `_safe_json` production parser with a declared_claims/narration JSON envelope. Where a consequential journal proposition is narrated, the fixture declares it with its actual source_claim_id from the supplied gm_resolution_decision. No declaration requirement is bypassed. The second test uses one natural scene-setting journal proposition instead of the opaque uppercase marker; a distinct visible-fact sentinel still must not appear.

Both tests still execute New Campaign and successful HTTP Start, read persisted GM output, and assert nonempty/journal-source curated facts. The second asserts the exact selected/curated journal fact, exclusion of visible facts, and final selector mirrors. A valid immutable response does not select a fallback, so the former unconditional fallback-only metadata assertion was obsolete too. The test now exercises the real `opening_context_from_gm_output` and `build_opening_fallback_result_meta` owners and asserts their exact basis/equality. It does not manufacture fallback metadata in production.

Final individual results: both pass (`fixed_4.txt`, `fixed_5.txt`). HTTP regression: these remain green. No production acceptance, schema or parser validation rule was relaxed.

Separate negative controls retain invalid `[Narration]`: real call_gpt with synthetic SDK output produces 422, no gm_output and gameplay_committed false. `placeholder_http.json` records the actual HTTP failure body, state before/after and diagnostics. The diagnostic matrix's placeholder case additionally compares all persisted gameplay values, world/factions/time/turn/latch and log. One admission is consumed, no retry occurs. Full-payload equality accounts explicitly for preexisting save timestamps, empty-log creation and scene-addressability trace bookkeeping; no progression changes are ignored. See report 06.
