# PR-BT Policy / Instruction Deduplication Implementation

## A. Executive Result

Implemented a bounded provider-representation deduplication. Large prose restatements of shipped policy and narrative-plan fields were compacted into short operational bridges while preserving machine-readable policy/context objects.

Result across reconstructed P1/P2/P3 provider requests:

| Probe | Before total | After total | Removed | Percent |
|---|---:|---:|---:|---:|
| P1 | 110,450 | 96,178 | 14,272 | 12.92% |
| P2 | 121,438 | 109,095 | 12,343 | 10.16% |
| P3 | 110,665 | 98,118 | 12,547 | 11.34% |

Fixed reduction common to all three: 12,343 provider-facing characters.

## B. Ownership Preservation

No canonical authority moved into prompt-only structures. `GMResolutionDecision`, `ResolutionContract`, `RealizationClaim`, provenance, declaration validation, narration validation, bounded improvisation handling, accepted-response sealing, and C18 remain runtime/validator-owned.

## C. Semantic Overlap Before

Major duplication families:

| Family | Duplicate Surfaces |
|---|---|
| Policy tail | Long instruction paragraphs restated `response_policy` children. |
| Answer/uncertainty | Generic direct-answer prose duplicated `answer_completeness`, `response_delta`, `uncertainty`, `fallback_behavior`, and the PR-BS recipe. |
| Narrative plan | Instructions described fields already present in `narrative_plan` and compact mode-delta lines. |
| System/instructions | System prompt and instructions both repeated action declaration, direct answer, authority, no-validator voice, NPC specificity, and hidden-info boundaries. |

## D. Implementation

Changed:

- `game/gm.py`: compacted duplicated static system prose while preserving the JSON realization envelope and claim/improvisation contract.
- `game/prompt_context.py`: compacted base answer/uncertainty/NPC instruction families, narrative-plan guidance, narrative-role guidance, and repeated policy-tail prose.
- `tools/measure_pr_bt_policy_instruction_payloads.py`: added deterministic P1/P2/P3 provider reconstruction and measurement.
- `tests/test_pr_bt_policy_instruction_deduplication.py`: added provider-construction rule-presence and savings tests.

## E. Instruction Changes

Removed/compacted:

- Long `ANSWER COMPLETENESS CONTRACT` explanation.
- Separate expected-voice and response-delta prose.
- Repeated question-resolution and uncertainty-shaping paragraphs.
- Repeated opening/NPC-reply/narration-obligation lines.
- Long narrative-plan structural guidance.
- Long per-policy tail paragraphs for narrative authority, fallback, tone, anti-railroading, context separation, narration purity, anchoring, and authenticity.

Remaining:

- Short operational bridges.
- The turn-specific PR-BS answer recipe.
- Structured policy objects and contracts.
- Output envelope/schema and declaration lane.

## F. System-Prompt Changes

The system prompt was compacted from 12,975 to 8,851 chars. It still states authority ownership, answer-first behavior, player-hypothesis preservation, no internal/scaffold leakage, NPC/incidental boundaries, app-resolved mechanics, player agency, and the full JSON realization envelope.

## G. Response-Policy Status

No response-policy compact projection was implemented. The provider still receives the full top-level `response_policy` object.

## H. Answer-Recipe Status

The PR-BS Decision-Facing Answer Recipe remains intact and provider-visible:

| Probe | Recipe chars |
|---|---:|
| P1 | 2,356 |
| P2 | 1,876 |
| P3 | 1,691 |

## I. Rule-Presence Evidence

`tools/measure_pr_bt_policy_instruction_payloads.py` records `rule_presence.json` for each probe. All checks passed for P1/P2/P3:

- generated prose is not automatically authoritative;
- canonical decision/claims constrain realization;
- recipe cannot grant new authority;
- inference/uncertainty remains visible;
- player hypotheses remain hypothetical unless authorized;
- NPC incidental realization remains bounded;
- declaration lane remains explicit;
- ordinary narration need not be declared merely because it was generated;
- unknown/fallback behavior remains visible;
- invalid output cannot intentionally escape the JSON envelope;
- raw internal JSON must not leak to player narration.

## J. P1/P2/P3 Measurements

| Component | P1 Before | P1 After | P2 Before | P2 After | P3 Before | P3 After |
|---|---:|---:|---:|---:|---:|---:|
| Total provider chars | 110,450 | 96,178 | 121,438 | 109,095 | 110,665 | 98,118 |
| System prompt | 12,975 | 8,851 | 12,975 | 8,851 | 12,975 | 8,851 |
| User JSON | n/a | 81,635 | n/a | 93,548 | n/a | 83,425 |
| Instructions | 25,788 | 12,699 | 26,675 | 13,681 | 25,856 | 12,767 |
| Response policy | 20,630 | 21,346 | 21,237 | 21,465 | 20,913 | 21,138 |
| Turn packet | 10,676 | 10,676 | 10,640 | 10,640 | 10,910 | 10,910 |
| Decision recipe | 2,356 | 2,356 | 1,876 | 1,876 | 1,691 | 1,691 |
| Schema/output contract, separable | n/a | 5,440 | n/a | 5,440 | n/a | 5,440 |

The response-policy deltas reflect reconstructing current provider requests from saved PR-BS state and resolution; no response-policy compaction was performed.

## K. Savings

| Probe | Total Removed | Percent | Instructions Removed | System Removed |
|---|---:|---:|---:|---:|
| P1 | 14,272 | 12.92% | 13,089 | 4,124 |
| P2 | 12,343 | 10.16% | 12,994 | 4,124 |
| P3 | 12,547 | 11.34% | 13,089 | 4,124 |

Conceptual repeated-character effect using the fixed common reduction of 12,343 chars:

| Successful turns | Approx repeated chars avoided |
|---:|---:|
| 10 | 123,430 |
| 25 | 308,575 |
| 50 | 617,150 |
| 100 | 1,234,300 |

This matters before future gameplay systems are added because every always-on provider surface compounds with new combat, NPC, provenance, world-state, and ruleset context.

## L. Semantic Diff

See `PR-BT_policy_instruction_semantic_diff.md`.

## M. Regression Results

Commands run:

- `python tools\measure_pr_bt_policy_instruction_payloads.py` PASS.
- `python -m pytest tests\test_pr_bt_policy_instruction_deduplication.py -q --tb=short --basetemp=codex_pytest_tmp_prbt` PASS: 3 passed.
- `python -m pytest tests\test_pr_bs_decision_facing_answer_recipe.py tests\test_build_messages_projection.py tests\test_pr_br_structured_realization_envelope.py tests\test_pr_br_decision_owned_realization_claims.py tests\test_pr_br_decision_semantic_fidelity_slice3.py -q --tb=short --basetemp=codex_pytest_tmp_prbt_g1` PASS: 37 passed.
- Broader authority and policy/emission batches were started and showed only passing progress, but did not terminate within bounded waits in this environment and were interrupted:
  - continuation/immutable/hard-authority group reached 15 passing dots before interruption;
  - individual continuation files reached passing progress before interruption;
  - policy/emission batch reached 26 passing dots before interruption.

No deterministic failure was observed. The incomplete long-run attempts are a residual validation gap for external review.

## N. Architecture Status

A — PR-BR REMAINS CLOSED.

## O. Live-Validation Readiness

Ready in substance for a later 3-turn PR-BT micro-live comparison after the interrupted long deterministic suites are allowed to complete or are rerun in an environment where they terminate normally. No live/model/API calls were run in this implementation block.

## P. Residual Canonicalization Candidates

Recorded but not implemented:

- turn-packet provider projection;
- response-policy compact projection;
- history surface canonicalization;
- debug metadata scrub;
- top-level contract mirror reduction, especially `context_separation_contract`.

## Decision Taxonomy

B — BOUNDED REPAIR NEEDED.

Meaningful provider reduction was achieved, critical operational rules remain provider-visible, and architecture is unchanged. The bounded remaining item is validation completion: the large deterministic regression batches made passing progress but did not terminate within bounded waits in this environment.
