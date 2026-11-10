# Next session

## Verdict

PR-PLAY-53 is **B — PARTIAL / FURTHER INVESTIGATION REQUIRED**.

## Do this next

Repair consequential-fabrication validation before any further live narration round and before any player-facing narration.

The misses to cover, without treating a keyword list as semantic proof:

- "You find a silver key beneath the board."
- "You recognize the culprit immediately."
- "The tavern runner confesses that he sold the patrol route."
- "You succeed in uncovering the patrol route." on a failed investigation. `_mechanical_success` does not read `resolution["success"]`.
- "The silver key is now yours."
- A shortened route that was not authorized, such as "the patrol took the northwest mud track past the crates," when the status is `observed`.

Keep a passing prelude out of the player response. A detection improvement must not false-reject the harmless rain and texture lines already in the PR-PLAY-49 corpus, including the footprint sentence that mentions passage and beneath.

## How to repeat the live path

Leave ordinary play unchanged. Both of these must be exactly `1`, and only for the experiment process:

- `ASHEN_QUARANTINE_INVESTIGATION_NARRATION`
- `ASHEN_QUARANTINE_NARRATION_LIVE`

Keep `ASHEN_DISABLE_PROVIDER_CALLS=1` for the chat turn so the player-facing object stays deterministic. The hook lifts that flag only around its own adapter call. Keep SDK retries off. Cap the run at 6 requests, 1,000 output tokens per request, and 10,000 total tokens. Point `ASHEN_PROVIDER_USAGE_PATH` at a new ledger file. Do not reuse `artifacts/pr_play_53/provider_usage.jsonl`; accounting refuses to reset an existing ledger.

The adapter remains `game.expressive_dialogue.request_expression`. Model `gpt-4.1-mini`. Output cap 80. Timeout 45 seconds. This run used 954 tokens across 2 requests.

## Do not

- Enable the live flag for ordinary `/api/chat`.
- Copy quarantine prose into `player_facing_text`.
- Edit canonical scenes to make the narration easier.
- Treat PR-PLAY-52's 6 ms hook time as provider latency.
