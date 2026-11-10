# Scenario results

Both live scenarios used `POST /api/chat` on a temporary copy of `frontier_gate`. Live interpretation was disabled, so the existing exploration resolver decided the outcome. The player-facing provider stayed disabled. Only the quarantine hook called the adapter.

Create calls observed by the capture wrapper: 2. That matches the usage ledger.

## Scenario A — successful investigation

Action: `I examine the notice board.`

Mechanical result, identical in the baseline and the live run: `discover_clue`, success, interactable `notice_board`, clue `notice_patrol_route`.

Player-facing text, identical:

> You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.

Authorized context supplied to the provider:

- Player action: `I examine the notice board.`
- Status: `discovered`, success true.
- Newly discovered: the patrol-route sentence above.
- Previously known: none.
- Public observations: the five visible facts already on the frontier-gate scene, including the posted warning that a patrol is missing. The warning does not state the route.
- Constraints: prelude only; the engine appends the discovery; no new rewards, destinations, culprits, or mechanics.

Provider prelude, captured verbatim:

> The notice board stands weathered and splattered with rain, its faded papers fluttering in the damp breeze. Crowds gather nearby, their murmurs blending with the clatter of boots and the occasional bark of the gate serjeant. The board’s messages draw wary glances from those waiting in line.

Diagnostic: `heuristic_pass_pending_review`. Fallback: false. The assembled quarantine text appends the route sentence once. That assembled text is not the player response.

Context leak scan of the hook input and the provider message: none.

## Scenario B — limited investigation

Action: `I examine the rain barrel.`

Mechanical result, identical in the baseline and the live run: `investigate`, success true, no clue id, no clue text, `discovered_clues` empty.

Player-facing text, identical:

> Provider calls are disabled for this run, so no live narration was generated.

This is the existing disabled-provider sentence. The rain-barrel turn does not take the clue-discovery skip, so a live player-facing call would have replaced it. The disable flag kept that from happening. The hook then made its own quarantined call.

Authorized context:

- Player action: `I examine the rain barrel.`
- Status: `observed`, success true.
- Newly discovered: none.
- Previously known: none.
- The patrol-route sentence was not in the provider message (`route_in_limited_context`: false).

Provider prelude, captured verbatim:

> The rain barrel stands near the gate, its surface slick with recent drizzle. The murmur of the tavern runner nearby blends with the distant clatter of boots and the low hum of gathered watchers. Shadows shift as the day wanes, inviting a closer look at this unassuming container.

Diagnostic: `heuristic_pass_pending_review`. Fallback: false. The assembled quarantine text then appends the engine line "No new clue is established by this examination." and the public observations. The route sentence is not among them.

## Scenario C — provider failure

The existing fault `ASHEN_QUARANTINE_NARRATION_FAULT=timeout` was used. The live flag was off, so no seventh or third provider call was made. Create calls remained 2.

Mechanical result and player-facing text matched the notice-board baseline. Diagnostic: `simulated_timeout`. Fallback: true. The fallback prose stayed in the quarantine record.

## Stop conditions

No authentication, connection, or repeated provider error occurred. Token use after two requests was 954, under 10,000. The plan stopped there. A third live sample was not required to see both a discovery and a non-discovery.
