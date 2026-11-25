# Next step decision

Recommended milestone: `pr_play_authored_exit_travel_guard`.

Do not start it from this assessment.

## 1. Player-facing problem

The player can take an authored exit only when the sentence is close to the exit label. Nearby passage wording is rejected as if the exit did not exist. Overlapping wording moves the player when the request was to read, or when the request forbade the move.

## 2. Representative requests

- "I go through the gate into Cinderwatch." Stays at `frontier_gate`. Reply: the destination is not established. The exit "Enter Cinderwatch" targets `market_quarter`.
- "I read the missing-patrol notice." Arrives at Old Milestone. The notice clue is not published.
- "I do not enter Cinderwatch." Arrives at the market quarter.
- Preserved contrast: "I examine the notice board" publishes the clue and stays. "I enter Cinderwatch" arrives at the market. "Instead of entering the gate, I wait beside the rain barrel" stays.

## 3. Existing owners

- `game/intent_parser.py` selects travel and already contains stay/negation helpers.
- `game/exploration.py` resolves a selected transition.
- `game/conversational_orchestration.py` publishes "not an established destination" when the phrase does not bind to an exit.
- `game/ordinary_semantic_ownership.py` does not see the two bad moves, because a transition is already chosen.

## 4. Broken contract

An exit may be selected because its label occurs inside the utterance, including after "do not" and inside a read/examine request whose noun overlaps the rumor exit. A passage request that names the gate and Cinderwatch does not select the exit that enters Cinderwatch.

## 5. Smallest viable implementation

In the existing matcher, accept one positive unconditional passage that names the gate and Cinderwatch as the authored Enter Cinderwatch exit. Reject exit selection when the utterance negates that travel, including "do not enter". Reject exit selection when the main verb is read, examine, or inspect and the player is asking about the notice. Do not add a new travel system.

## 6. Prerequisites

The Frontier Gate exits and the notice interactable already exist. No new world content. Provider calls remain disabled in tests. Experimental physical adjudication stays off.

## 7. Deferred

Multi-action ("examine and then enter"), conditionals, plans, "open the gate" as a physical verb, inventory inspection, mundane move/cover/climb, scene-action flags, look-around narration, and NPC elaboration.

## 8. Positive HTTP tests

- "I enter Cinderwatch" still arrives at the market quarter.
- "I follow the missing patrol rumor toward the northwest track" still arrives at Old Milestone.
- "I go through the gate into Cinderwatch" arrives at the market quarter and does not claim a new destination was invented.
- "I read the missing-patrol notice" stays in the gate district and publishes the patrol-route clue.
- "What routes can I take from here?" still lists both exits and does not move.

## 9. Negative controls

- "I do not enter Cinderwatch" stays in the gate district.
- "Instead of entering the gate, I wait beside the rain barrel" stays.
- "I examine the notice board" does not travel.
- The forbidden-password control still withholds the password.
- "I follow the patrol route to the old trading crossroads" before and after the map flag still does not suddenly start working. That flag is deferred.

## 10. Regression preservation

The combined selection must keep the same failure identities. Focused marking, persistence, admission, inventory-possession, and topic-retrieval tests must not gain failures. Exact exit tests in the travel and composition suites must stay green.

## 11. Expected gameplay change

The player can pass the gate in ordinary passage language and can read the notice without being relocated. A negated entry no longer moves them. The forty-probe SUCCESS count is not expected to rise, because those forty sentences are not these sentences. The gain has to be shown on the new HTTP cases.

## 12. BLOCKED conditions

Block the implementation if the only way to accept the passage phrase is a new travel framework, if it requires enabling experimental physical adjudication, if read-versus-travel cannot be separated without dropping the working notice inspection, or if the combined failure set gains an identity that is not one of the inherited twenty.
