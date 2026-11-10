# AT-OPT-01 Executive Summary

Verdict: **B/PARTIAL**.

The F3 cost incident is attributable. The 3,000-token verification budget never became a runtime ceiling, and the step-back utterance was dispatched as primary narration. Exact token shares inside that 22,777-token prompt were not captured. A working-tree reconstruction gives byte sizes for the same assembler and is labeled reconstructed.

## What happened

HTTP acceptance for PR-PLAY-79D-F3 sent one live request. Player text: “I step back from the notice board.” Purpose `primary_turn`, owner `gm.call_gpt`, model `gpt-4.1-mini-2025-04-14`, attempt `12e9b94b02cb49cf984cf975b5e58d5e`. Recorded use: 22,777 input tokens, 600 output tokens, 23,377 total, provider latency 5,339.716 ms. Ledger: `artifacts/pr_play_79df3/http_data/provider_usage.jsonl`.

The same sentence on the PR-PLAY-79D-F browser host, with physical adjudication and expression enabled, was one expression request: attempt `aed6b30c010a448681b307a0fe012397`, 60 input, 12 output, 72 total, provider latency 1,936.353 ms. That sentence was accepted and published. No primary narration.

## Why this audit is partial

The provider ledger stores no prompt text. Section attribution of the 22,777 tokens is reconstructed from `build_messages` against the pre-continuation snapshot. The admission estimate for that reconstruction is 28,031 tokens. That is the same order of magnitude as the recorded call and is not the captured request.

Route totals, the decision chain, and the budget miss are recorded or read from the current source. Those are sufficient to rank the next experiment. They are not a complete token map of the captured prompt.

## Largest demonstrated cost drivers

Across the retained PR-PLAY-79 through 79C live ledgers, every request over 20,000 input tokens is `gm.call_gpt` (`primary_turn` or `retry_escalation`). Expression requests in those same ledgers stay near 100–350 tokens. On PR-PLAY-79, five primary or retry calls account for 131,711 of 144,968 tokens. The cycle report records 0 accepted narrations and 0 accepted dialogue lines.

The F3 prompt is large because primary narration sends the standing system prompt plus a user payload dominated by `response_policy`, `instructions`, and `turn_packet`. The reconstructed recent log is 402 bytes. Conversation growth does not explain this call.

## Next experiment

One experiment, not started here: stop an unresolved fast-path retreat from entering `gm.call_gpt`, and prove that a 3,000-token admission ceiling refuses a primary prompt before dispatch.

Do not start AT-OPT-02. Do not open PR-PLAY-80. Do not commit or push.
