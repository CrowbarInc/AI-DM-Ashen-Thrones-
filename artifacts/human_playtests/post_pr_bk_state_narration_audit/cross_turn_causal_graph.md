# Cross-Turn Causal Graph

Session `735ebd1cfb4567c4f97df6dc`. Only edges with log or probe evidence.

## Chain A — false journey

```text
turn 06 "I proceed North-West, as the runner directed."
        ↓
parse_freeform_to_action → None
        ↓
no travel kind, so PR-BF's travel-kind narration guard does not run
        ↓
generated_candidate narrates crates, sheds, lanterns, broken banners, and arrival
        ↓
shape-valid scene_update is adopted (arrival, banner clue, hidden watcher, mode exploration)
        ↓
player believes they are on that track
        ↓
turn 07 "As I pass the crates..."
        ↓
adjudication, no crate target
        ↓
anti-reset prepares "The guard says..."
        ↓
authored-knowledge realization replaces it with the real patrol clue
        (topic_pressure last_answer authoritative text, not the banner paragraph)
        ↓
turn 08 approaches a broken banner and asks how it was destroyed
        ↓
custom action, no banner, detail question not executed
        ↓
empty speaker_label → "The guard says..."
        ↓
scene_update writes the banner clue again
        ↓
turn 09 "I continue following the path."
        ↓
parse → None again
        ↓
referential-clarity replacement → the same guard line
        ↓
scene_update writes arrival and banner visible facts again
```

Turn 06 is the cause. Turns 07–09 are echoes. The guard line is an amplifier on 08 and 09. Turn 07's heard text is the clue, not the guard line.

## Chain B — board, separate from the journey

```text
turn 00 opening correctly says the board lists curfews and a missing patrol
        ↓
turn 01 approach is a failed social_probe
        ↓
generated_candidate adds a curfew-hour schedule and the undiscovered route
        ↓
turn 02 asks for times and districts
        ↓
notice_board binds (alias "curfew notice") and reveals its only clue, the patrol route
        ↓
player treats the route as the board's answer
```

This chain establishes the route for real on turn 02. It does not move the player. Stopping turn 01's schedule sentence would not remove turn 06, because the discovered clue and the runner both state the direction afterward.

## Chain C — runner relevance, feeds the wording of turn 06

```text
turn 03 runner is correctly addressed
        ↓
resolution reply_kind is refusal
        ↓
ignorance line is computed
        ↓
general-dimension sufficiency accepts the patrol clue
        ↓
player hears that as how to get around the city
        ↓
turn 06 says "as the runner directed"
```

The direction was already in the discovered clue. This chain explains the player's attribution. It does not explain why the move was narrated as success. That is chain A.

## Chain D — interlocutor switch, stops before the journey

```text
turns 03–04 tavern_runner is the active interlocutor
        ↓
turn 05 "to the watch" matches alias watch on gate_guard
        ↓
explicit target beats continuity (topic salience ignored)
        ↓
Gate Guard shrugs
        ↓
no reward fact is invented in the heard line
        ↓
turns 06–09 do not continue a guard conversation in state
```

No edge from this shrug to the banners. The banner paragraph stored as `last_answer` on this turn was not the player-facing travel narration.

## Independent, not echoes

| Turn | Why it is not only an echo |
| --- | --- |
| 01 | Earliest false board reading. Happens before any travel |
| 02 | Inspect owner works and still emits the other subject. Would be reachable from the opening's "curfews" line without turn 01 |
| 03 | Relevance. The NPC bind is correct |
| 04 | Not a failure |
| 05 | Alias rebind. Geography unchanged |
| 06 | Fresh. The route it follows is authoritative; the journey is not |

## What is not linked

- PR-BK did not feed the banner paragraph back out as a structured fact. Turn 07 emitted the clue payload.
- `old_milestone` content was not copied into the travel prose. Sheds, lanterns, and banners are not that scene.
- Faction event-log lines were not spoken.
- No combat and no date change participated.
