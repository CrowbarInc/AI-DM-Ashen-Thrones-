# Unique carried object reference

## Objective

Repair ordinary resolution of an object that is already in authoritative state. "I examine the book." while the player carries one spellbook was answered with "Nothing here matches that reference. Which established object do you mean?" and the turn advanced. The reference had to bind, and an unresolved object action had to stop spending the turn.

## Scope

Object-reference classification, carried inventory, current-scene interactables, aliases, unique versus ambiguous versus unmatched, admission, and turn integrity. Inventory transfer, equipment, encumbrance, identification, and new examination or interaction mechanics were not added. Recognizing the spellbook does not make examination a supported action.

## Verdict

A/PASS.

The original failure was reproduced on the ordinary chat path. The carried spellbook now binds. Ambiguity is named and not executed. An unmatched object keeps the existing sentence and does not spend the turn. The notice board still examines and still spends the turn. Persistence, person grounding, negation, and conditionals still hold. The final regression selections add no new failure identities. The review archive is validated by the packaging script.

## Repair

`reference_compatible` accepts an exact token sequence, a spaced suffix, a closed-compound spacing variant, and one reference token of at least four letters that is the trailing head of a longer name token. Inventory rows and visible current-scene interactables are collected with that check. One carried match resolves to the sheet. More than one match, or a carried match plus a scene match, asks which object. A unique visible interactable stays with the existing scene owner. An examine, inspect, or look-at with no carried row, no visible interactable, and surface authority `unsupported` or `authored_hidden` returns before the turn increment. That return records `last_publication` and copies `referenced_surface_authority` onto the logged resolution.

## Results

Provider mode: deterministic HTTP, provider calls disabled. Live-model object-grounding reliability: NOT MEASURED.

| Measure | After | Before, on the isolated case |
| --- | --- | --- |
| Carried-object grounding | 12/12 | "the book" 0/1; explicit spellbook already 1/1 |
| Scene-object grounding | 2/2 | notice board 1/1 |
| Ambiguity handling | 3/3 | two carried books 0/1 |
| Unmatched handling | 3/3 | astrolabe sentence present; its turn decision 0/1 |
| Admission integrity | 7/7 | |
| Turn integrity | 7/7 | |
| Consequence integrity | 7/7 | |
| Continuity | 5/5 | |

Indeterminate count: 0 in each table. A resolved spellbook with an unsupported examination is counted as grounded, not as a successful examination.

Ordinary sequences: the book, the pronoun, and the reloaded book bind `spellbook` at turn +0. Two books clarify, then each name binds. The astrolabe stays unmatched at turn +0 and a retry does not claim success. The notice board publishes its clue at turn +1. "I look around." still publishes the provider-disabled stub and still advances the turn.

Frozen forty: 1 visible change, `inventory_equipment-05-01`, previously INDETERMINATE, not relabeled. Unchanged successes 12. Unchanged minimum-quality marks 22. Mean actionability 1.675 was not rescored. Supplementary executable stays 5/55. Provider stub count in the forty: 3. No broad-score improvement is claimed.
