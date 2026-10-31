# PR-BS current review

Date: 2026-10-04.

MODE: discovery only. Model/API calls during PR-BS discovery: ZERO. Live gameplay validation during PR-BS discovery: ZERO. No implementation, commit, or push.

## Major findings

PR-BR remains closed. The four-turn PR-BR closeout evidence shows the authority boundary held: unauthorized consequential claims were rejected, failed structured envelopes were not prose-salvaged, player hypotheses did not become world truth, and accepted/sealed/emitted exactness held.

The Chapter II problem is cooperation and cost. The model receives a very large, overlapping authority/policy payload but lacks a compact operational recipe for how to answer within the current `GMResolutionDecision`. It often uses ordinary GM instincts to add causal/evidential/status/preference material, while the validator requires exact realization of authorized claims or correctly scoped bounded proposals.

The dominant context cost is not scene/world data. Representative A1 measured payload: 12,543 system chars and 90,681 user chars. The largest user components were `instructions` (26,068 chars), `response_policy` (20,609), `turn_packet` (10,668), `narrative_plan` (4,475), `context_separation_contract` (3,492), and `gm_resolution_decision` (2,124). Retry resends the whole base request and appends feedback.

Retry behavior is costly and tends to produce safe nonresolution because retry feedback makes rejection avoidance more salient than the remaining authorized answer. A1/B1 retries passed by dropping consequential declarations; A2/A3 fell through to safe observations/nonresolution after repeated invalid envelopes.

## Recommended PR-BS implementation slice

First slice: decision-facing answer recipe projection.

Build a compact model-facing projection from `GMResolutionDecision` that says what must/may be stated, what may be inferred, which modality/provenance/relation/declaration mode is valid, what must remain unresolved, and which upgrades are forbidden for this turn. For A1, the deterministic stopping condition is that the prompt projection contains a bounded inference recipe and forbids cause/actor/time/history/lead establishment, while validator fixtures accept the bounded answer and still reject the original overreach.

## Architecture decision

A - PR-BR REMAINS CLOSED.

Observed problems are AI Experience / Gameplay / Performance issues. No new systemic integrity failure was found.

## Unresolved uncertainties

- The discovery did not test whether removing duplicate payload fields changes model behavior.
- The discovery did not run micro-live validation for the proposed recipe projection.
- Some repeated contract/policy representations may be necessary for distinct deterministic consumers; payload cleanup should follow ownership verification rather than pure size reduction.

## Files included for external review

- `CURRENT_REVIEW.md`
- `PR-BS_cooperative_realization_discovery.md`
- `artifacts/pr_bs_cooperative_realization_discovery/context_inventory.json`
- `artifacts/pr_bs_cooperative_realization_discovery/call_chain_evidence.md`
- `handoff/payload_breakdown.json`
- `handoff/REVIEW_MANIFEST.json`
- PR-BR closeout summary/evidence excerpts:
  - `artifacts/pr_br_closeout_live_revalidation/REPORT.md`
  - `artifacts/pr_br_closeout_live_revalidation/model_calls.json`
  - `artifacts/pr_br_closeout_live_revalidation/A1_decision_1.json`
  - `artifacts/pr_br_closeout_live_revalidation/A1_digest.json`
  - `artifacts/pr_br_closeout_live_revalidation/A1_raw_envelope_attempt_1.json`
  - `artifacts/pr_br_closeout_live_revalidation/A1_raw_envelope_attempt_2.json`
  - `artifacts/pr_br_closeout_live_revalidation/B1_decision_4.json`
  - `artifacts/pr_br_closeout_live_revalidation/B1_digest.json`
  - `artifacts/pr_br_closeout_live_revalidation/B1_raw_envelope_attempt_1.json`
  - `artifacts/pr_br_closeout_live_revalidation/B1_raw_envelope_attempt_2.json`

