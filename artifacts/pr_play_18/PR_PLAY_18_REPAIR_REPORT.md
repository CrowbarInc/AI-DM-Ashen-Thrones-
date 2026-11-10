# PR-PLAY-18 repair report

Changed production files:

- game/opening_presentation_renderer.py: prepare_opening_renderer now projects a dedicated public selection request instead of adding instructions to the legacy narration request. Added opening_plan_text_format to encode the existing plan field contract and per-entry allowed ID/variant pairs.
- game/gm.py: only when opening_catalog exists, pass prepared text_format as Responses API text.format.

Tests: added tests/test_pr_play_18_contract_alignment.py; updated the PR-PLAY-13 replay assertion because authority claims are now retained locally rather than sent in the user message. Existing unit replay/variant/authority tests still cover deterministic rendering; the new integration test compares published text to the exact selected public variants.

This is a necessary replacement of contradictory provider contract inputs, not a general prompt optimization. Public facts still come from the unchanged engine catalog. Validator, renderer, accepted publication authority and rollback logic are unchanged. No legacy prose conversion, fallback, unknown-ID allowance or error suppression was added.

Disabled openings retain their existing system prompt, authored-fact instruction, full payload, request kwargs, parser and validation. Ordinary turns retain their messages and parser and never attach the new schema; both branches are tested at the transport boundary. Model, limits, budgets and retries are unchanged. No commit/push was performed. Pre-existing unrelated working-tree changes are preserved; source_changes.diff is relative to snapshots taken at this pass's start, not Git HEAD.

Limitations: no live provider was used, so provider-side schema support and actual model selection behavior await an explicitly authorized experiment. The real SDK serializer was exercised with in-memory HTTP, but a mocked HTTP response cannot prove remote schema acceptance. A first unhydrated campaign synchronizes authored scene addressability before the rollback snapshot; negative tests compare against that exact authorized synchronization plus the established bookkeeping normalization. No attempt was made to redesign this pre-existing boundary.
