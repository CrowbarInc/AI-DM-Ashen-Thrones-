# 02 — Baseline and Environment

Repository revision `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (“PR-BN bounded DM improvisational authority”). The working tree was already dirty: 498 porcelain entries at review time. The qualification baseline is that worktree, not a clean HEAD. Python 3.12.0. Client date October 17, 2026.

Provider configuration observed in the repaired usage log: configured model `gpt-4.1-mini`, returned model `gpt-4.1-mini-2025-04-14`. Expression uses one Responses call, purpose `expression`, temperature 0.2, max output 80 tokens. Narration is not used for these turns. `ASHEN_DISABLE_EXPRESSION_GENERATION=1` remains set for pytest. The live runner sets it to `0`.

Relevant regression before the expression work: 609 tests, {'failed': 25, 'passed': 584}. The predecessor claim of 650 passing tests was not reused. Focused speech-adoption, continuity, and reference-eligibility tests passed before the expression edits. Speech adoption remains `AUTHORIZED_HOST_SPEECH`; generated wording is an optional checked step immediately before that seal.

PR-EG-R2C artifacts and the frozen R3 inputs were left in place. `frozen_holdouts.json` SHA-256 `fd37f3994d32dee5e0af557e16d3eb4f2754a5df022256640ce7a65d8672494d`. `live_plan.json` SHA-256 `14931ecde13cf0380a00e838db343b9e5537cf9cd47011a994dbaf3b6a62faac`.
