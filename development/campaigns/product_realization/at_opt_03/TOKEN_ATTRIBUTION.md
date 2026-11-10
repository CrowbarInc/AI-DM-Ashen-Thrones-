# Input Size Attribution

## Measurement classes

| Class | Value |
| --- | --- |
| Recorded F3 provider input | 22,777 tokens. Output 600. Total 23,377. Latency 5,339.716 ms. Attempt `12e9b94b02cb49cf984cf975b5e58d5e`. Ledger `artifacts/pr_play_79df3/http_data/provider_usage.jsonl` |
| Reconstructed blob | 83,040 bytes. System 9,558. User JSON 68,675. Two messages. Full system prompt, not narration-only |
| Admission estimate | 27,744 tokens. Formula `(blob_bytes // 3) + 64` |
| Unattributed remainder | 4,967 tokens, the whole gap between the estimate and the recorded input. No section was tokenized by the provider |
| Prior reconstruction | AT-OPT-01 recorded 83,902 blob bytes and estimate 28,031 on resolution-none. This rebuild is 862 bytes smaller. System bytes match that earlier rebuild (9,558) |

Scene files are not inside the snapshot. They were read from `artifacts/pr_play_79df3/http_data/scenes`. World, character, combat, session, and the two log entries came from snapshot `2026-11-08T16-50-45_8caf7aff`. Resolution was none. Profile was `manual_play_auto`.

Section token figures below are `bytes // 3` on the reconstruction. They are estimates. Summing them does not recover 22,777.

## User JSON by section

| Section | Bytes | Share of user JSON | bytes // 3 |
| --- | ---: | ---: | ---: |
| response_policy | 21,638 | 31.5% | 7,212 |
| instructions | 12,596 | 18.3% | 4,198 |
| turn_packet | 10,642 | 15.5% | 3,547 |
| narrative_plan | 5,031 | 7.3% | 1,677 |
| referent_tracking | 2,650 | 3.9% | 883 |
| dialogue_social_plan | 2,245 | 3.3% | 748 |
| lead_context | 2,145 | 3.1% | 715 |
| speaker_selection | 1,169 | 1.7% | 389 |
| scene | 1,098 | 1.6% | 366 |
| character | 1,059 | 1.5% | 353 |
| scene_state_anchor_contract | 1,005 | 1.5% | 335 |
| mechanical_resolution | 646 | 0.9% | 215 |
| narration_visibility | 615 | 0.9% | 205 |
| selected_conversational_memory | 585 | 0.9% | 195 |
| transition | 535 | 0.8% | 178 |
| narration_obligations | 402 | 0.6% | 134 |
| recent_log | 306 | 0.4% | 102 |
| campaign | 381 | 0.6% | 127 |

Largest policy children: context separation 3,675; answer completeness 2,054; interaction continuity 1,805; response delta 1,739; narrative authenticity 1,674; tone escalation 1,628; anti-railroading 1,551; narrative authority 1,421; fallback behavior 1,315.

Turn packet children: nested response policy 6,016; contracts 3,755; debug 287. Narrative plan’s largest child is `narrative_roles` at 1,321.

Source constants are 9,568 bytes for `SYSTEM_PROMPT` and 4,170 bytes for `NARRATION_ONLY_SYSTEM_PROMPT`. The rebuilt system message is 9,558 bytes because `build_messages` replaces one hidden-fact sentence. Swapping the narration-only system text onto this user payload changes the blob by −5,661 bytes. The user payload would still be the structured-claim payload. That swap is a size bound only.

## Same state, other utterances

Resolution none. Blob bytes and delta versus the step-back rebuild:

| Utterance | Blob bytes | Delta |
| --- | ---: | ---: |
| I step back from the notice board. | 83,040 | 0 |
| I push the nearest crate. | 83,027 | −13 |
| I look closely at the notice board. | 83,046 | +6 |
| I wait and listen. | 83,347 | +307 |
| Hello, Gate Guard. | 84,288 | +1,248 |
| What did we already learn about the patrol? | 85,527 | +2,487 |
| What do I see? | 87,471 | +4,431 |
| Something feels wrong here. What should I do? | 87,668 | +4,628 |

The two questions add an uncertainty hint and a larger payload. Every row still uses the full system prompt. Every row is blocked from the compact instruction list by `must_advance_scene`.

## Requests over 20,000 recorded input tokens

All eleven are `gm.call_gpt`, model `gpt-4.1-mini-2025-04-14`, refusal null. Cycles are different revisions. Equal input counts are not proof of identical bytes.

| Cycle | Purpose | Player text from the session log | Input | Output | Latency ms | Publication observed in the log |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 79 | primary_turn | empty; resolution kind `scene_opening` | 25,294 | 1,382 | 9,758.784 | Opening prose |
| 79 | primary_turn | The log row for the following retry stores 28,425, not this primary. Player text on that row: “I want to follow the tracks farther.” | 22,961 | 600 | 4,312.177 | Visible sentence is a look-around at the milestone |
| 79 | retry_escalation | I want to follow the tracks farther. | 28,425 | 314 | 3,254.451 | Same log row as the retry token count |
| 79 | primary_turn | Paired with the next retry. Player text: “I search for a route along the road.” | 23,178 | 600 | 4,344.5 | Visible sentence: nothing further is established |
| 79 | retry_escalation | I search for a route along the road. | 28,650 | 307 | 2,681.839 | Same row |
| 79A | primary_turn | empty; `scene_opening` | 25,294 | 1,924 | 13,107.816 | Opening prose |
| 79A | primary_turn | Second sent request with the same input count. The log attributes 25,294 only to the opening row | 25,294 | 1,944 | 11,579.405 | Player text for this second request was not on a log row |
| 79A | retry_escalation | I look around the milestone. Kind `already_searched` | 23,669 | 600 | 4,151.64 | “The examination adds nothing new to what you already know.” Tag `provider_retry_disabled` is also on that output |
| 79B | primary_turn | empty; `scene_opening` | 25,294 | 1,662 | 11,334.169 | Opening prose |
| 79C | primary_turn | empty; `scene_opening` | 25,294 | 1,363 | 11,866.995 | Opening prose |
| 79D-F3 | primary_turn | I step back from the notice board. | 22,777 | 600 | 5,339.716 | Replaced fallback. Retreat not narrated |

Shared traits, from the ledgers and these log rows:

- The over-20,000 class is primary narration and its retry. Expression and interpretation in the same cycles stay well below it, as AT-OPT-01 already totaled.
- Openings and later primaries are the same order of magnitude. The F3 recent log is 306 reconstructed bytes at turn 5. Conversation length does not explain the class.
- A failed or replaced call carries the same primary payload. F3 sent one call and published a fallback. Two 79 primaries finished at the 600-token output cap and were followed by retries of 28,425 and 28,650 input tokens.
- The retry surplus over the immediately preceding primary is 5,464 and 5,472 tokens. Current `build_retry_prompt_for_failure` samples are 3,620–3,911 bytes. `regeneration_feedback` without a resolution is 460 bytes. Those samples do not explain a 5,470-token increase. The historical retry text was not stored.

Machine tables: `artifacts/at_opt_03/measurements.json`. Log join: `artifacts/at_opt_03/_correlate_logs.py` and `_correlate_detail.py`.
