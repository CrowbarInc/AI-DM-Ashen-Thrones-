# AT-OPT-03 Summary

**Verdict: A/PASS.** Primary narration context is mapped, the large contributors are measured on a reconstruction, and one safe next experiment is specified. Live provider calls: 0. No production prompt change.

The captured 22,777-token F3 prompt was not stored. A provider-free rebuild of that turn, from the pre-continuation snapshot, is 83,040 bytes and an admission estimate of 27,744 tokens. The admission formula is UTF-8 bytes divided by 3, plus 64. It sits 4,967 tokens above the recorded input. Section shares below are shares of that reconstruction. They are not a provider tokenizer bill.

## What contributes

On the reconstruction, the user JSON is 68,675 bytes and the system prompt is 9,558 bytes.

| Contributor | Bytes | Share of user JSON |
| --- | ---: | ---: |
| `response_policy` | 21,638 | 31.5% |
| `instructions` (78 lines) | 12,596 | 18.3% |
| `turn_packet` | 10,642 | 15.5% |
| `narrative_plan` | 5,031 | 7.3% |
| Scene, character, campaign, recent log, clues, and the player line together | under 4,000 | under 6% |

Standing scaffold in the user JSON is 58,792 bytes. Gameplay-state fields grouped for this count are 6,921 bytes. Recent log is 306 bytes, from the two snapshot log entries. The player line is a few dozen bytes.

Eight different utterances on the same snapshot stay between 83,027 and 87,668 bytes. Questions add a few kilobytes. They do not create the 20,000-token class. That class is the ordinary primary payload.

## Historical requests over 20,000 input tokens

Eleven sent `gm.call_gpt` requests. Five are openings with empty player text and exactly 25,294 input tokens (79, 79A, 79B, 79C, plus a second 79A primary with the same input count and a different output count). The mid-scene cases are “I want to follow the tracks farther.”, “I search for a route along the road.”, the retry of “I look around the milestone.”, and the F3 step-back. Expression calls in the same cycles stay near 100–350 input tokens.

Openings published opening prose. The mid-scene calls were replaced, retried, or published a short deterministic sentence. F3’s 22,777-token call was replaced and does not narrate the retreat. With current code and physical adjudication off, that sentence no longer builds or sends a prompt.

## Safe cut, and what was left alone

`omit_duplicate_turn_packet_policy` drops `turn_packet.response_policy` only when every nested key equals the root policy. Three keys differ (`response_delta`, `answer_completeness`, `planner_seam_trace`), so twelve JSON-equal keys stay. Removing only those equal keys from a copy saves 2,637 bytes. The admission estimate falls by 879. The root policy still holds the same values.

That is the AT-OPT-04 experiment. It is not implemented here.

A larger instruction-list swap saves about 10,011 bytes on the copy, and the existing compact-instruction gate is closed because `transition.transition_required` is true. Forcing that swap is a narrative-quality change. It is not the next edit.

## Remaining uncertainty

The provider did not return section tokens. The 4,967-token gap between the estimate and the recorded F3 input is unattributed. Historical retries are about 5,470 input tokens above the preceding primary. Current retry instructions measure 3.6–3.9 KB, which does not account for that surplus. The snapshot has no scene files, so scene JSON came from the F3 `http_data` copy. This rebuild is 862 bytes under the AT-OPT-01 reconstruction of the same snapshot.
