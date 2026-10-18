# PR-DY implementation report

Decision: A — LIVE GAMEPLAY READY, with the qualifications in PR-DY_remaining_risks.md.

HEAD: d31beb7d73dd4fda0f22184a6a69b947b5f470ff

The dirty worktree was preserved. Production saves under data/ were hashed before and after the cycle and were unchanged:

- session.json 0a77beb47a2c30deb0b1977e915f3a5e2f67f5560e15a8bf0a5874015e244023
- world.json 3592e4af8723e631bb14d4f512431e8697987546f7fdf8076b3fbd1b135a42ef
- combat.json ac977a4ab7d9eae556ba30893d9b09ec075efaf70ba67de0a6d60736eaf685b9
- session_log.jsonl e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
- character.json 8f52309e6dff2626793fb609fd6226d8a0f0adad6e957cc1fc890d0402842795
- campaign.json 65d9e3063dcf13bcd9b155cd4e80e3ec23b867fa8ad326463fda831d8dacb8a8

## What was connected

Ordinary chat already reached HTTP, mode detection, and, for explicit IC with providers off, the deterministic parser. It did not call the PR-DO/PR-DR interpreter. `_stored_interpretation_for_player_text` still returns none unless a test injects a record.

`game/live_chat_interpretation.py` is the production connector. It reuses:

- `experiments.pr_dr.prompt.build_messages_for_catalog`
- `experiments.pr_dp.prompt.provider_schema`
- `experiments.pr_do.adapter.adapt_interpretation`
- `game.player_interpretation_bridge.normalized_action_from_interpretation`

No second interpreter was added. The older semantic interpreter is skipped for the rest of the turn after this connector runs, so one player message does not spend two interpretation calls.

## Where it sits in chat()

After the stored-interpretation block and before the turn counter advances, AUTO and explicit IC call `interpret_production_turn` when live interpretation is enabled. Explicit OOC still returns the existing non-mutating acknowledgement and does not call the interpreter.

Blocked results return a non-mutating response and do not advance turn or time. Accepted results are locked as the parsed action so the phrase parser cannot replace them or fall through. Bridge rejection also returns without execution.

When `ASHEN_DISABLE_LIVE_INTERPRETATION` or `ASHEN_DISABLE_PROVIDER_CALLS` is set, the connector is skipped and the previous parser path remains. That keeps the existing tests and the provider-disabled explicit IC path working.

## Provider bound

`game/provider_budget.py` is active only when a request limit or a usage path is set. `call_gpt` refuses a request before send when the estimate would pass the ceiling. Refusals are not counted as sent requests. `ASHEN_DISABLE_PROVIDER_RETRIES=1` skips retry attempts. `ASHEN_PIN_PROVIDER_MODEL` pins the configured model.

## Test adjustment

`tests/test_pr_dp_contract_qualification.py` still forbids `engine_submission` anywhere in `game/`. The production connector is the one file allowed to name `adapt_interpretation`, because that is the existing adapter. It does not read an execution grant.

## Live evidence

Three sent interpretation calls and three narration refusals. Two ordinary gameplay actions and one automatic OOC classification went through the browser. Explicit OOC was non-mutating and made no provider call. Details are in the companion reports. The human playtest has not been performed.
