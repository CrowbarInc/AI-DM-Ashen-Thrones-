# PR-BZ — Narration-only retry micro-live validation

Date: 2026-10-08.

MODE: CONTROLLED MICRO-LIVE VALIDATION.

Live execution was limited to P2. P1 and P3 were not run live. Phase 0 still verified the inherited selector controls for P1/P2/P3 before the live call.

## Decision

**A — P2 LIVE VALIDATION PASSED.**

PR-BY live retry path not exercised.

P2 selected `narration_only`, the provider obeyed the one-field narration-only contract, and the first response was accepted. The final accepted, sealed, and emitted narration are identical. No declaration metadata leaked to the player, no model-authored declarations were accepted, and no unauthorized state/provenance mutation was observed.

## Reconstruction

- Source: `artifacts/pr_bx_narration_only_micro_live`.
- Player input: `Baker, which loaf do you usually keep for yourself?`.
- Scene: Bread stall. Visible fact: a baker stands beside loaves. No authored loaf preference.
- Response operation: `incidental_dialogue`.
- Declaration expectation: `reply_not_required`.
- Consequential realization required: `False`.

## Pre-live Verification

Focused PR-BY regression: PASS, 22 passed.

Selector/control verification: PASS. P2 selected `narration_only`; P1/P3 controls remained `structured_realization`; narration-only contract stayed `NARRATION-ONLY RESPONSE CONTRACT: Return valid JSON only in this exact shape: {"narration": "player-facing response"}. Do not include other fields. The application will normalize this internally.`; `declared_claims` was absent from the narration-only system prompt; smuggled declarations were rejected.

## Live P2 Evidence

- Selected envelope: `narration_only`.
- Provider response contract: `narration_only`.
- Provider attempts: `1`.
- Attempt 1 input tokens: `23413`.
- Attempt 1 output tokens: `85`.
- Attempt 1 response shape: `{"json_object": true, "keys": ["narration"]}`.
- Declaration validation: hard valid, accepted claims empty.
- Narration validation: hard valid, no rejection reasons.
- Regeneration triggered: `False`.

Attempt 1 narration:

> The baker glances at the neatly arranged loaves, then shrugs with a faint, noncommittal smile. "I don't have a particular favorite to keep for myself," they say carefully. "Every loaf here is made with care, but I try not to show any preference." Their tone carries a hint of guarded discretion, as if some details are best left unshared.

Final emitted narration:

> The baker glances at the neatly arranged loaves, then shrugs with a faint, noncommittal smile. "I don't have a particular favorite to keep for myself," they say carefully. "Every loaf here is made with care, but I try not to show any preference." Their tone carries a hint of guarded discretion, as if some details are best left unshared.

## Retry Contract

No retry occurred. This demonstrates successful first-attempt narration-only operation, but does not independently prove the PR-BY live retry repair under live regeneration. Deterministic PR-BY retry evidence is preserved in `PR-BZ_retry_contract_evidence.json` and the focused test output.

## Narration Validation

No narration rejection occurred in PR-BZ P2. The PR-BX rejection pattern involving `unowned_stateful_world_assertion` and `unauthorized_evidential_relation` did not recur in this sample. No sentence-boundary parsing issue was observed.

## Final Response Integrity

Accepted narration equals sealed narration equals emitted narration. `declared_claims` remained application-created and empty. Player-facing leakage list is empty. `authority_problems` is empty. The only accepted incidental temporal record is bounded incidental texture for the baker's glance/shrug; the NPC spoken answer is claim-only/hearsay in validation and is not promoted to durable world truth.

## Cost

PR-BX P2: 48,294 input tokens, 209 output tokens, 48,503 total tokens, 2 provider attempts.

PR-BZ P2: 23413 input tokens, 85 output tokens, 23498 total tokens, 1 provider attempt.

This is a single sample and did not exercise retry, so no generalized cost-improvement claim is made.
