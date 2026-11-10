# Scenario

## Source

The sequence continues the established frontier-gate campaign through `tests/pr_play_79df3_harness.py` `seed_gate`. The campaign is already started at turn 4. The prior publication is the harness sentence: Gate Guard says the notice board mentions a missing patrol. Scene files are copies of `data/scenes`. The opening route is not called.

The harness canaries stay in the isolated store. None appeared in player-facing text.

Experimental gates stay at their defaults: physical adjudication, dynamic NPCs, player initiative, and world improvisation are unset. Live interpretation and expression generation are disabled. Provider calls are disabled. This is deterministic engine output. It is not recorded-provider replay, not a simulated model transcript, and not live-model prose.

## Provider and budget

Configured default model name observed after config import: `gpt-4.1-mini`. A provider key was present in the process after configuration import. The OpenAI client constructor was replaced with a blocker. Non-local `socket.create_connection` was replaced with a blocker. Neither blocker fired. `network_blocks` is empty.

Verification profile installed before the turns: 4 requests, 3,000 input, 600 output, 3,000 total, source `default`. A historical total of 200,000 is rejected and leaves that ceiling in place.

The in-sequence admission probe ran while provider calls were disabled, so both the oversized estimate and the small estimate were refused as `provider calls disabled` before any invoke. That probe does not prove the token ceiling. A separate probe, with the disable flag absent and with a local stub in place of a provider, refused an estimate of 28,000 as `input-token ceiling` with zero invoke calls, and admitted an estimate of 100. The stub completed 11/3/14 tokens locally. Those 14 tokens are not a provider bill. Evidence: `artifacts/pr_play_post_opt/budget_probe.json`.

## Turns

| Turn | Category | Player utterance |
|---|---|---|
| T01 | Scene inspection | I stop under the gate and look around. What is actually in front of me? |
| T02 | NPC interaction | Gate Guard, do you have a moment? |
| T03 | Follow-up | You mentioned the patrol. What have you heard? |
| T04 | Physical interaction | I walk over to the notice board and put a hand on the frame. |
| T05 | Investigation | Read me the missing-patrol notice, not the tax lines. |
| T06 | Improvisation | I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording. |
| T07 | Ambiguous request | Handle it. |
| T08 | Player agency | Don't send me anywhere yet. I'll choose after I know what the board actually says. |
| T09 | Recall | What did that notice say about where the patrol was last seen? |
| T10 | Unexpected request | Can I trade my dry cloak for the tavern runner's stew? |
| T11 | Scene progression | I follow the missing patrol rumor toward the northwest track. |
| T12 | Retreat / continuity | I step back from the notice board. |

The expected story was not hard-coded. T11 uses the authored exit label because that is the established way to leave the gate. The other lines are natural-language variations, including the sleeve copy, the cloak trade, and "Handle it."

## Categories scored on every turn

Intent comprehension, gameplay authority, narrative usefulness, continuity, player agency, conversational flexibility, publication integrity, and responsiveness. Each is scored 0, 1, or 2. A technically published sentence can still score 0 for usefulness.

## Limitations

- Provider-disabled narration cannot show live prose quality.
- The FiveTurnGameplay harness requires a campaign opening and stops at five player turns, so it was not used.
- `chat_turn` reseeds the campaign on every call, so the sequence driver posts twelve turns on one seeded client instead.
- Physical adjudication is off, so a successful physical retreat was not available. That is the condition AT-OPT-02 corrects.
- The three known baseline KeyError tests were not rerun.
