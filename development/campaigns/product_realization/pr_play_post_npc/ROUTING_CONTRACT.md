# Routing contract

An earlier NPC response remains available as context. It does not own the next utterance when the current text names an established scene object or is an unbound physical attempt.

## NPC continuation

A follow-up that does not name a scene object and does not leave the scene still addresses the active speaker. "Ask the captain about the notice." stays with the captain. The focused test keeps the scene at `frontier_gate`.

## Explicit repetition

"Could you repeat that?", "What did the captain just say?", and "Tell me the warning again." still return the captain's delivered sentence. A GM-owned row with an empty speaker id is recovered when the player names that person. Naming the notice does not take those requests.

## Scene-object interaction

Movement toward one established current-scene interactable is local contact. The decline does not set a travel focus, does not change scene, and does not reveal a clue. Two matches ask which object was meant. An unknown place such as the glass observatory still returns `destination_not_established`.

## Inspection

"Read the notice" and "What did that notice say" inspect the established object. A conjunction that names an established object and an unknown object asks for clarification and discloses nothing.

## Grounded recall

A second inspect of a disclosed clue uses the existing already-searched publication. It does not require an NPC addressee. It does not add hidden facts.

## Travel

An authored exit still moves. T11 reaches `old_milestone`. T12 stays there and remains the unsupported retreat while physical adjudication is off.

## Ambiguous targets

"Handle it." does not pick a person. In the corrected replay it falls through to the disabled-narration sentence. "What do the notice board and the glass dial say?" does not disclose the clue.

## Authority restrictions

Local contact does not invent a touch result. The sleeve copy does not create a writing system or change inventory. Hidden watcher, cloak, and signal facts stay hidden. A failed or declined turn does not count as completed gameplay.
