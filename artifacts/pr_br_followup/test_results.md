# PR-BR Continuation 3 test results

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

## Deterministic

`tests/test_pr_br_resolution_contract.py`: 48 passed.

Includes the follow-up matrix (source, confidence, location, time, referential action, ambiguity, wear, recent use), retry preservation, rejected-claim non-promotion, and stubbed `/api/chat` claim promotion plus indirect follow-ups.

## Focused band

156 passed, 0 failed:

- tests/test_pr_br_resolution_contract.py
- tests/test_pr_bp_live_resolution_routing.py
- tests/test_playability_eval.py
- tests/test_bounded_improvisation_authority.py
- tests/test_perception_narration_authority_audible_non_invention.py
- tests/test_playability_smoke.py
- tests/test_prompt_context_public_prompt_boundary.py
- tests/test_referenced_surface_grounding_inspection_resolution.py

## Real-path claim proof

`test_real_path_promoted_claim_accepts_indirect_follow_ups`

Raw player text. Emitted traveler assertion. `active_claim` from the ledger. `truth_status = not_world_truth`. Next turns: "Who did he hear that from?" binds source; "Does she trust the story?" binds confidence. The question is not pasted back.

`test_real_path_refusal_does_not_promote_active_claim` leaves `active_claim` empty.

## Live

`artifacts/pr_br_followup/20260928T011636Z`

Completed turns: 1. Model calls: 2. Aborted turns: 1. Smoke: not run. Full gate: not run.

Turn 1 evaluator: PASS. Manual: refusal, no claim. `failure_locus` in the saved JSON says `bad_contract` because that rumor ask has no dimension. Code now labels that `contract_unchecked`. False PASS: 0. False FAIL: 0.

## Evaluator disagreements

None on PASS/FAIL. One diagnostic overclaim, corrected after the probe without another live run.
