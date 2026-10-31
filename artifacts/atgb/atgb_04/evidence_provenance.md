# Evidence provenance — ATGB-04

Authority hierarchy: Development Constitution and Validation Evidence Standard;
adopted ATGB-02 specification; ATGB-01 design/rubric and catalog. ATGB-01's original
29/4/4 partition proposal is superseded only by ATGB-02's S07 partition adoption:
25 development-visible, 4 related variations, 8 held-out. No criteria or benchmark
version were changed here. Rubric: `atgb-rubric-01`; scenario: `ATGB-01`;
partition revision: `ATGB-02-s07-held-out`.

The authoritative 37-turn index is derived directly from each selected scenario's
original `result.json`. Inputs are checked against approved fixture lines; response
text is checked against the combined baseline worksheet. Each row records the
source path and JSON pointer, trial, actual full preceding same-trial conversation,
approved expectations, authority context and bounded before/after state projection.
The human-readable document escapes text for HTML display and preserves the strings
in the index. It does not rewrite replies, trim repetition or supply missing context.

| Source pass | Selected evidence | Trial boundary |
| --- | --- | --- |
| ATGB-03 | S01: 4; S02: 4; S03: 5 | Trial 1; 13 baseline turns |
| ATGB-03C | S04: 4 | Full trial 2; 4 baseline turns |
| ATGB-03C | S05–S08: 4 each; S09–S10: 2 each | Trial 1; 20 baseline turns |
| ATGB-03 | Original S04: 2 | Historical partial trial 1, separate; excluded from 37-turn aggregation |

ATGB-03 and ATGB-03C execution HEAD: `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`.
The dirty worktree means HEAD alone cannot identify running bytes. Original
`configuration_and_provenance.json`, continuation `provenance_before.json`, and
their preserved checks retain source/configuration hashes. ATGB-04's
`preservation_before.json` and `preservation_checks.json` check unchanged inputs,
production sources, canonical campaign data, harness, prior artifacts and authority.
The standard ZIP manifest hashes every included canonical file and states exclusions.
`evidence_sources.json` separately hashes the selected turn/worksheet source files.

Frozen baseline: `frontier-gate-v1`, pinned manifest SHA-256
`4197114379ba9c406d9b2135085eb605d8235fd9a34dcebe852b95451ef41ae9`.
Initialized-state hash in scenario preflights:
`c12cb0dfe6a31980b4ecc00a59cc359a143a76452e517a36ad76753a6145561a`.
Machine readiness is separate from opening delivery and from human judgment.

Execution lane: live-enabled production `POST /api/chat` through TestClient;
individual replies can be host-owned. Configured roles: `gpt-4.1-mini`; recorded
returned model: `gpt-4.1-mini-2025-04-14`; routing enabled, sampling uncontrolled.
No new provider request or gameplay execution occurs in ATGB-04. The original
completion-only ledger (12 observed requests, 21,531 input / 2,190 output tokens)
and continuation admission ledger (23 admitted/dispatched/completed, 37,222 input /
4,137 output tokens) remain separate. Neither is evidence of conversational
success. Missing host telemetry stays unavailable, never inferred as zero.

Packaged evidence includes all selected transcripts and raw results, original
partial S04, original and combined worksheets, readiness and opening-context
evidence, source provenance and provider-accounting summaries. Detailed final
isolated stores remain at the original per-scenario `stores/` paths in the repository;
full world dumps and unrelated artifact trees are deliberately not copied into the
compact handoff. The raw per-turn state evidence is included. Name-only flag
projections cannot establish unchanged values; deeper questions can remain uncertain.

Human judgments are blank in the HTML, Markdown forms and JSON template. Old
`unchecked`/`unscored` worksheet placeholders and diagnostic failure zeros are not
imported as judgments. The aggregator requires explicit human attribution and
attestation for entered values, validates only schema/rubric consistency, and
counts supplied labels; it never interprets or judges response text. Independent
reviewers keep separate exports. Any disagreement requires explicit human
adjudication rather than automated consensus.

The browser tool refused `file:` navigation under its URL protocol policy. No
browser workaround was attempted. HTML structure, exact text, blank controls and
JavaScript behavior are checked offline; rendered browser layout is not verified.
This presentation limitation does not block the Markdown review document or the
standard handoff ZIP. No gameplay-performance baseline is claimed before human review.
