# Input Size Attribution (review copy)

The handoff filename safeguard treats a path whose file name begins with `TOKEN_` as sensitive and omits it from the zip. This file is the same attribution report as `TOKEN_ATTRIBUTION.md`, kept under a name the bundler can package. If the two files diverge, `TOKEN_ATTRIBUTION.md` is the campaign report.

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

The reconstruction used the full system prompt (9,558 bytes). The narration-only system prompt is smaller. Swapping it onto this user payload changes the blob by −5,661 bytes and would drop the structured-claim schema while the payload still expects that envelope. That swap is a size bound only.

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

## Requests over 20,000 recorded input tokens

All eleven are `gm.call_gpt`, model `gpt-4.1-mini-2025-04-14`, refusal null. Equal input counts across cycles are not proof of identical bytes.

| Cycle | Purpose | Player text from the session log | Input | Output | Latency ms |
| --- | --- | --- | ---: | ---: | ---: |
| 79 | primary_turn | empty; `scene_opening` | 25,294 | 1,382 | 9,758.784 |
| 79 | primary_turn | Paired with “I want to follow the tracks farther.” The log stores the retry’s token count on that row | 22,961 | 600 | 4,312.177 |
| 79 | retry_escalation | I want to follow the tracks farther. | 28,425 | 314 | 3,254.451 |
| 79 | primary_turn | Paired with “I search for a route along the road.” | 23,178 | 600 | 4,344.5 |
| 79 | retry_escalation | I search for a route along the road. | 28,650 | 307 | 2,681.839 |
| 79A | primary_turn | empty; `scene_opening` | 25,294 | 1,924 | 13,107.816 |
| 79A | primary_turn | Second sent request. The log attributes 25,294 only to the opening | 25,294 | 1,944 | 11,579.405 |
| 79A | retry_escalation | I look around the milestone. | 23,669 | 600 | 4,151.64 |
| 79B | primary_turn | empty; `scene_opening` | 25,294 | 1,662 | 11,334.169 |
| 79C | primary_turn | empty; `scene_opening` | 25,294 | 1,363 | 11,866.995 |
| 79D-F3 | primary_turn | I step back from the notice board. | 22,777 | 600 | 5,339.716 |

Openings published opening prose. The track and road rows published a look-around sentence and “Nothing further is established about that.” The milestone row published the examination sentence. F3’s call was replaced and does not narrate the retreat.

Each 79 retry is about 5,470 input tokens above the preceding primary. Current retry-instruction samples are 3.6–3.9 KB. They do not account for that surplus. The historical retry text was not stored.

Machine tables: `artifacts/at_opt_03/measurements.json`.
