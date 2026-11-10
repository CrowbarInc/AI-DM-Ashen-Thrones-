# Negative Controls

Milestone: `pr_play_object_marking_inspection`. Date: 2026-11-09.

72 focused tests cover empty/one/multiple/post-removal reads, repeated detached reads, malformed/missing/duplicate identities, legacy/partial/string records, malformed markings and orphan/corrupt receipts. Missing runtime files do not bootstrap. Persistence and UUID functions are replaced with forbidden callbacks during reads and replay. Request, revision, marking-ID, scope, authorization and every prerequisite failure refuse with unchanged durable bytes. Content-identical marks are selected by identity. New request against removed mark does not become replay. Authority guard denial prevents commit. Concurrent identical requests commit once. Historical resurrection/dropped receipt/tampered add receipt refuse. Save failure controls and opaque extension preservation are explicit. Internal helpers are absent from FastAPI routes; twelve-turn replay verifies no natural-language activation, implicit migration, marking, inspection or removal.

Exact parameterized identities and outcomes: final_inspection_junit.xml; requests/results/timeline and failure artifacts provide machine-readable evidence.
