# PR-CQ Turn Transcripts

Isolated disposable session on the authored default frontier gate. Player lines are the exact inputs. Final lines are the exact `player_facing_text`. Provider candidates that were generated and then rejected are quoted in full.

No gameplay turn was rerun. The runner stopped after turn 2. The fourth provider request was turn 2's retry, which completed inside the request cap.

## Startup

Preflight returned `OK` from `gpt-4.1-mini-2025-04-14` with usage attached (24 input, 2 output). Gameplay started only after that.

## Turn 1 — harmless preference

Player: Guard Captain, do you prefer standing watch in the rain, or somewhere dry?

Resolver: social question to `guard_captain`. `incidental_subjective_allowed` was true. No topic was revealed.

Validation: `initial_hard_valid`. Provenance `initial_generation`. No retry.

Final narration:

> The guard captain shrugs, rain pattering off their soaked cloak. "Honestly, I'd prefer somewhere dry, but duty calls, rain or shine. These eastern gates don't watch themselves, no matter the weather." Their gaze flicks toward the muddy crowd pushing through, expression firm yet weary.

The final line is the provider's only candidate. It was not replaced by gate-banner narration.

## Turn 2 — authored patrol fact

Player: Captain, what do you know about the missing patrol?

Resolver: social question to `guard_captain`. Selected topic `patrol`: "A patrol went missing near the old milestone."

Both provider generations were hard-invalid (`unauthorized_resolution_decision_fact`). The sealed line is the canonical projection, not either provider draft.

Rejected attempt 1:

> The guard captain's eyes harden beneath the sodden hood as they reply, "We've had no word from a patrol assigned near the old milestone. They were tasked with scouting the old trading crossroads, a crucial route. They simply didn't return, and a warning was posted on the notice board here. It's troubling—no sign of them, no messages. The town's on edge, and rumors spread fast, though few facts yet." Their gaze flicks over the muddied crowd, expression a mix of concern and the weary resolve of duty.

Rejected attempt 2 (`retry_reason=hard_invalid`):

> The guard captain's eyes flick to the notice board, their expression guarded. "There's talk of a patrol missing near the old milestone. I don't know the details myself — just that the warning is posted there. Seems the runner's whispers around the square are picking up on it, too." Their gaze shifts back to the pressing crowd, firm yet weary amidst the cold rain.

Final narration:

> Guard Captain mutters, "Word is, a patrol went missing near the old milestone."

Acceptance why: `authored_answer_projection`. The "Word is" / "mutters" wrapper is the existing social realization template applied to the authored sentence. The session stored the same sentence as the discovered clue.
