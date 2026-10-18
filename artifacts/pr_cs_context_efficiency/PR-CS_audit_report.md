# PR-CS Audit Report

## Phase 0 Worktree Safety

- git HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- git status: preserved dirty worktree; see `changed_files.txt` for the full pre/post relevant status.
- model configuration: `.env.example` declares `DEFAULT_MODEL_NAME=gpt-4o-mini`, `HIGH_PRECISION_MODEL_NAME=gpt-4.1-mini`, `RETRY_ESCALATION_MODEL_NAME=gpt-4.1-mini`, `ENABLE_MODEL_ROUTING=true`.
- captured provider model for audited gameplay generation: `gpt-4.1-mini`; historical completions report `gpt-4.1-mini-2025-04-14`.
- provider configuration: OpenAI Responses API via repo code; no live provider calls in PR-CS.
- tokenizer: exact GPT-4.1 tokenizer is not vendored in the repo and `tiktoken` is not declared in `requirements.txt`. Historical request totals use exact provider usage. Category attribution uses clearly labeled local `ceil(chars/4)` estimates, not invented exact tokenization.

## Phase 1 Payload Evidence

| Request | Exact API input tokens | Est. system tokens | Est. user payload tokens | Largest top-level payload keys by estimate |
|---|---:|---:|---:|---|
| A_PR_CQ_harmless_NPC_preference | 30877 | 1042 | 29751 | response_policy~5471, instructions~3763, turn_packet~2567, scene~2522, gm_resolution_decision~2096, mechanical_resolution~1710, decision_facing_answer_recipe~1693, narrative_plan~1275 |
| B_PR_CQ_authored_patrol_question_initial | 34561 | 1042 | 33087 | response_policy~5538, instructions~3727, scene~2682, turn_packet~2621, gm_resolution_decision~2327, mechanical_resolution~1741, decision_facing_answer_recipe~1687, narrative_plan~1319 |
| B2_PR_CQ_authored_patrol_question_regeneration | 42960 | 1042 | 40845 | __retry_feedback__~8496, response_policy~5538, instructions~3727, scene~2682, turn_packet~2621, gm_resolution_decision~2327, mechanical_resolution~1741, decision_facing_answer_recipe~1687 |
| C_PR_CO_notice_board_examination | 30970 | 1042 | 29835 | response_policy~5478, instructions~3763, turn_packet~2574, scene~2529, gm_resolution_decision~2096, mechanical_resolution~1740, decision_facing_answer_recipe~1699, narrative_plan~1275 |
| D_PR_CO_ordinary_observation | 29914 | 1042 | 28714 | response_policy~5465, instructions~3701, turn_packet~2656, scene~2546, gm_resolution_decision~2095, decision_facing_answer_recipe~1715, narrative_plan~1150, referent_tracking~1063 |
| E_PR_CO_natural_language_exploration | 35302 | 1042 | 33826 | response_policy~5497, instructions~3791, turn_packet~2630, scene~2625, gm_resolution_decision~2224, mechanical_resolution~1737, decision_facing_answer_recipe~1687, narrative_plan~1319 |

The five required representative requests are exact captured payloads, not reconstructions. The PR-CQ retry payload is included as separate evidence because PR-CR eliminates it under equivalent eligible conditions; it is not counted as required initial prompt size.

## Core Finding

Ordinary gameplay reaches roughly 31k-35k input tokens because every generation request receives a broad all-purpose narration payload. The largest contributors are not conversation history; they are duplicated policy/instruction text, full mechanical/authority projections, repeated authored scene facts across multiple projections, and broad world/lead/NPC scaffolding that is often irrelevant to the current resolver.

## Decision

PR-CS decision: **A - CLEAR LOW-RISK OPTIMIZATION PATH**.

Substantial unnecessary context is supported by exact captured payloads. The lowest-risk first move is deduplication and resolver-specific projection, while retaining deterministic state, validators, CTIR, finalization, and persistence outside the provider prompt.
