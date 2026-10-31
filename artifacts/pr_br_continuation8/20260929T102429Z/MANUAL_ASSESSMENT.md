# Continuation 8 manual human-DM assessment

Standard: would a player reasonably believe the immediate request had been addressed? Evaluator labels were not the success test.

Artifact: `artifacts/pr_br_continuation8/20260929T102429Z`. 10 completed turns. 0 aborted.

## Persona A — social_goal

Objective: get through the gate tonight by finding someone who can say what to do.

| Turn | Intent | Contract | Binding | Generated responsive | Final responsive | Payload kept | Manual | Evaluator | Agree | Layer |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Ask someone on duty how to pass tonight | NO. `inspect` target object `duty` | NO | YES. Serjeant states papers, toll, inspection, curfew | NO. "You find no such thing" plus notice-board contents | NO | FAIL | FAIL | YES | contract construction |
| 2 | Name the snag and who can deal with it | PARTIAL. `ask`, target still `duty` | NO | YES. Missing patrol; guard captain | NO. "I have heard talk, but I cannot verify it." | NO | FAIL | PASS | NO | satisfaction |
| 3 | Take it to the named person, or ask the person in front what they need | PARTIAL. `act`, no target | NO | YES. No one was named; the person in front has papers and will not say | NO. "The reference cannot be identified clearly enough to resolve without clarification." | NO | FAIL | PASS | NO | final emission |
| 4 | Do the concrete thing just described | NO. `ask`, target `duty` | NO | WEAK. Says no contact was named and offers two routes | NO. "No reliable source here can verify the requested information." | NO | FAIL | FAIL | YES | contract construction |
| 5 | What trouble to watch for in the next few minutes | YES. `ask` | N/A | YES | YES. Missing patrol, bandits on the northwest track, delays, tighter scrutiny | YES | PASS | PASS | YES | — |

Manual PASS: 1/5.

## Persona B — explore_action

Objective: learn the yard well enough to move through it.

| Turn | Intent | Contract | Binding | Generated responsive | Final responsive | Payload kept | Manual | Evaluator | Agree | Layer |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Look around and approach the nearest ordinary thing | PARTIAL. `inspect`, no target | NO | YES. Chooses the notice board and describes it | NO. Same clarification line as social turn 3 | NO | FAIL | PASS | NO | final emission |
| 2 | Examine it and learn what people use it for | NO. Target text is the previous player sentence | NO | YES. Board is for taxes, curfew, patrol warnings | NO. "Nothing here matches that" plus a shorter board list | NO | FAIL | FAIL | YES | contract construction |
| 3 | Do the simplest ordinary use | NO. `perceive` / `use`; target is still that sentence | NO | YES. The player reads the board | NO. Retry says there is no utility to engage | NO | FAIL | PASS | NO | retry |
| 4 | Ask what people usually do with it | YES enough. `ask` about the board's function | YES for the board, despite the stored target string | YES. Serjeant: it is for reading | YES. Narrator paraphrase keeps that answer | YES | PASS | PASS | YES | — |
| 5 | Take the next safe step | NO. Labeled `ask`, target still the old sentence | N/A for the step | YES | YES. The player moves up through the queue | YES | PASS | PASS | YES | — |

Manual PASS: 2/5.

## Totals

- Manual PASS: 3/10
- Evaluator PASS: 7/10
- Evaluator false PASS: 4 (social 2, social 3, explore 1, explore 3)
- Evaluator false FAIL: 0
- Valid-answer destruction: 7 (social 1–4, explore 1–3)
- Generic fallback collapse: 6 (social 1–4, explore 1–2)
- Referent loss: 6 (social 1–3, explore 1–3)
- Action collapse: 3 (social 3, social 4, explore 3)
- Claim clipping: 0. `active_claim` stayed null, including after social turn 5's patrol answer. No repeat was requested.
- Player-visible mid-token truncation: 0
- Scene-momentum splice corruption: 0
- Prose only: explore 4 flattens spoken answers into narrator summary; explore 5 is atmospheric. Neither blocked the request. The Continuation 7 "nothing new resolves into evidence" line did not appear.

READY FOR FULL SYNTHETIC GATE: NO.
