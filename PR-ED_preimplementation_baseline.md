# PR-ED preimplementation baseline

Captured before PR-ED production edits. The working tree was already dirty from earlier product-realization work. This baseline is the behavior of that tree, not a clean `HEAD` checkout.

## Repository revision

- Branch: `feature/product-realization`
- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- HEAD subject: PR-BN bounded DM improvisational authority
- Tracking: `origin/feature/product-realization` (ahead 1)
- Working tree: dirty. `git diff --stat HEAD` reported 68 tracked files changed (about 14478 insertions, 3860 deletions) plus a large set of untracked PR artifacts. Those files were not cleaned.

## Environment

- OS: Windows 10.0.26200
- Python: 3.12.0 (`.\.venv\Scripts\python.exe`)
- pytest: 9.1.1
- Models from environment, names only: `DEFAULT_MODEL_NAME` and `HIGH_PRECISION_MODEL_NAME` are `gpt-4.1-mini`. `ENABLE_MODEL_ROUTING` is true. The API key is present and was not printed.
- Narration timeout at baseline: OpenAI SDK default (recorded as `openai_sdk_default`; commonly about 600 seconds). `api_upstream_preflight` uses 25.0 seconds.
- Retry ceilings: `MAX_TARGETED_RETRY_ATTEMPTS = 2`. Social dialogue is capped at `min(1, MAX)`. `MANUAL_PLAY_MAX_CALL_GPT = 6`.
- Token budgets: provider accounting is inactive unless `ASHEN_PROVIDER_REQUEST_LIMIT` or `ASHEN_PROVIDER_USAGE_PATH` is set. When accounting is active, narration `max_output_tokens` comes from `ASHEN_NARRATION_MAX_OUTPUT_TOKENS` (default 600) and interpretation max output is 320. Defaults when a request limit is set: input 8000, output 2000, total 10000.
- Caching: no application-level prompt cache. Exact duplicate top-level contracts are already omitted. Instruction dedupe is an exact system-prompt substring check.
- Instrumentation at baseline: none inside production. The profiler wraps `call_gpt`, `save_session`, and `save_world` from outside the engine.
- Pytest sets `ASHEN_DISABLE_LIVE_INTERPRETATION=1` and skips upstream API preflight.

## Regression command

The PR-EC comparison family, plus the PR-EC tests that now exist:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_pr_ea_conversational_orchestration.py tests\test_pr_eb_conversational_continuity.py tests\test_turn_pipeline_shared.py tests\test_pr_du_player_pipeline.py tests\test_pr_dq_ic_ooc_messages.py tests\test_social.py tests\test_pr_br_qualifier_movement_mixed_intent.py tests\test_exploration_resolution.py tests\test_exploration_skill_checks.py tests\test_unparsed_movement_state_narration_integrity.py tests\test_save_load.py tests\test_runtime_persistence_regression_suite_obj14.py tests\test_final_emission_gate.py tests\test_final_emission_response_type.py tests\test_pr_ec_movement_partial_intent.py --tb=no -q --basetemp=codex_pytest_tmp_pr_ed_baseline --junitxml=artifacts/pr_ed_provider_efficiency/baseline_junit.xml --override-ini="addopts="
```

## Counts and timing

- Collected: 279
- Passed: 249
- Failed: 30
- Warnings: 1 (Starlette/httpx deprecation)
- pytest time: 20.09s
- Exit code: 1
- JUnit: `artifacts/pr_ed_provider_efficiency/baseline_junit.xml`

The 30 failures are the inherited social, final-emission, retry, and exploration-routing set. `visible_intro_filler` failed on the social filler assertion (`stands nearby`), not WinError 5. No production code was edited before this run.

## Disabled-provider performance sample

Command: `tools/measure_pr_ed_turn_profile.py --out artifacts/pr_ed_provider_efficiency/baseline_profile.json`

Ten disposable courtyard turns, provider disabled. Engine time only. Narration `call_gpt` entries: 12. Sorted elapsed milliseconds: 3, 23, 68, 74, 74, 75, 77, 80, 93, 102. Median of those ten: 74.5 ms. Persistence on the ordinary-movement turn: `save_session` about 17 ms, `save_world` about 2 ms.

Ordinary movement still built one narration prompt of about 22740 estimated input tokens (`len/4`) and then emitted the deterministic arrival sentence. Alternative movement wording made three narration calls (scene stall twice) at about 17083 estimated user tokens each.

## Live samples captured before production edits

Same courtyard seed, model `gpt-4.1-mini` (`gpt-4.1-mini-2025-04-14`), `--max-output 1600 --input-limit 120000`.

- Ordinary movement: 16646 ms, 2 provider calls, hard-invalid retry. Usage: 22138 in / 917 out, then 25207 in / 1117 out. Player text: "You arrive. The waystation street runs north from the courtyard gate. A notice board stands by the road." Both generations were discarded.
- NPC dialogue initiation: 3111 ms, 1 `strict_social` call, 23469 in / 61 out. Player text: Sergeant Mara names the north road. Clue `north_road` discovered.

An earlier 10-turn live run used a 600-token output cap and an 80000 input ceiling. That cap truncated the first movement call and later turns were budget refusals (3 requests, 67495 input, 1497 output). Those numbers are not the production default and are not used as the comparison baseline.
