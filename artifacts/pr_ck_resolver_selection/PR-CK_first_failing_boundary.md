# PR-CK first failing boundary

Live provider calls: 0. The dirty worktree was preserved. HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`.

## Earliest incorrect assignment

Player text entered `_operation` in `game/resolution_contract.py`. Text that was not already inspect, perceive, or a physical act fell through to `operation=ask`.

`_topical_resolution_subject` then labeled every leftover ask `resolution_subject=social`.

`select_ordinary_resolver` selected `social` for every ask.

`stage_permitted` then refused exploration and passive wait. The exploration parser and the passive-wait stage never saw the turn. That is why `/api/action` could discover the authored desk clue while the equivalent `/api/chat` sentence could not. The exploration resolver itself was not the first break.

## Before

| Text | Operation | Subject | Resolver | Exploration | Passive wait | Interlocutor |
| --- | --- | --- | --- | --- | --- | --- |
| I investigate the desk. | ask | social | social | no | no | none |
| I search the desk. | act | world_action | world_action | no | no | none |
| I wait. | ask | social | social | no | no | none |
| I remain silent and observe. | ask | social | social | no | no | none |
| Describe the gate. | ask | social | social | no | no | none |
| Where are we? | ask | social | social | no | no | none |
| hello there | ask | social | social | no | no | none |
| I ask the baker which loaf he recommends. | ask | social | social | no | no | none |
| Where is the harbor? | ask | place_location | adjudication | no | no | none |
| I open the door. | act | world_action | world_action | no | no | none |

"I examine the desk." and "I look through the papers." were already exploration before this repair.

## After

| Text | Operation | Subject | Resolver | Exploration | Passive wait | Interlocutor |
| --- | --- | --- | --- | --- | --- | --- |
| I investigate the desk. | inspect | perception | exploration | yes | no | none |
| I search the desk. | inspect | perception | exploration | yes | no | none |
| I examine the desk. | inspect | perception | exploration | yes | no | none |
| I look through the papers. | perceive | perception | exploration | yes | no | none |
| I inspect the contents of the drawer. | inspect | perception | exploration | yes | no | none |
| I wait. | unresolved | unspecified | generation | no | yes | none |
| I remain silent and observe. | unresolved | unspecified | generation | no | yes | none |
| Describe the gate. | unresolved | unspecified | generation | no | yes | none |
| Where are we? | unresolved | unspecified | generation | no | yes | none |
| hello there | unresolved | unspecified | generation | no | yes | none |
| I look around. | perceive | perception | exploration | yes | no | none |
| I talk to the tavern runner. | ask | social | social | no | no | none |
| Tell me plainly. | ask | social | social | no | no | none |
| I persuade the gate guard to let me pass. | ask | social | social | no | no | none |
| Who attacked them? with an established interlocutor | ask | social | social | no | no | that interlocutor |
| Where is the harbor? | ask | place_location | adjudication | no | no | none |
| I open the door. | act | world_action | world_action | no | no | none |

A wait made while an interlocutor is already in scene focus stays generation and does not inherit that interlocutor.
