# PR-BR deterministic results

Date: 2026-09-27

HEAD: d31beb7d73dd4fda0f22184a6a69b947b5f470ff

No completion commit.

## PR-BR matrix

`tests/test_pr_br_resolution_contract.py`: 21 passed, 0 failed.

Includes raw `/api/chat` paths for referent inheritance and generic-scene rejection.

## Focused regression band

113 passed, 0 failed, across:

- tests/test_pr_br_resolution_contract.py
- tests/test_pr_bp_live_resolution_routing.py
- tests/test_playability_eval.py
- tests/test_bounded_improvisation_authority.py
- tests/test_perception_narration_authority_audible_non_invention.py
- tests/test_playability_smoke.py
- tests/test_prompt_context_public_prompt_boundary.py

After a one-line generation-constraint article fix, the 21 PR-BR tests passed again.

## Live funnel

Focused live turns: 0

Smoke runs: 0

Smoke turns: 0

Full-gate runs: 0

Full-gate turns: 0

Reason: OPENAI_API_KEY is unset and no repo `.env` is present.
