# PR-DT Scenario Definitions

## DT01 — Lantern inspection

- Source: DR01
- Stage: 1
- Kind: gameplay
- Expected facts:
  - The active scene is the waystation courtyard.
  - The player inspected or looked at courtyard_lantern.
  - The lantern is soot-streaked and burns beside the courtyard gate.
  - No time pressure advanced.
- Prohibited assertions:
  - Do not reveal a hidden token or any hidden lantern contents.
  - Do not move the character through the gate.
  - Do not award items, HP, rolls, or clues.
  - Do not mention the street notice board.

## DT02 — Sergeant Mara conversation

- Source: DR05
- Stage: 1
- Kind: gameplay
- Expected facts:
  - The active scene remains the waystation courtyard.
  - The player asked sergeant_mara about the road through the gate.
  - Mara's established answer is that the street beyond the gate is the north road.
  - No time pressure advanced.
- Prohibited assertions:
  - Do not promise Mara will escort, help, fight, or open the gate.
  - Do not invent extra patrol facts or rumors.
  - Do not move the character to the street.
  - Do not award items, HP, rolls, or clues.

## DT03 — Gate transition

- Source: DR08
- Stage: 2
- Kind: gameplay
- Expected facts:
  - The player moved through courtyard_gate.
  - The active scene changed to waystation_street.
  - Time pressure advanced from 0 to 1.
  - A notice board is visible by the road.
- Prohibited assertions:
  - Do not disclose the notice board clue text yet.
  - Do not claim the board has been read or resolved.
  - Do not introduce new street threats or NPCs.
  - Do not award items, HP, rolls, or clues.

## DT04 — Notice-board inspection

- Source: DR10
- Stage: 2
- Kind: gameplay
- Expected facts:
  - The active scene is waystation_street.
  - The player inspected notice_board.
  - The notice board says the north road is past the waystation.
  - The notice board was resolved as an interactable.
- Prohibited assertions:
  - Do not reveal unrelated hidden clues.
  - Do not add named factions, rewards, or quests.
  - Do not move the character away from the street.
  - Do not award items, HP, or dice outcomes.

## DT05 — OOC rules question

- Source: DR06
- Stage: 2
- Kind: ooc
- Expected facts:
  - This is out-of-character assistance.
  - No gameplay resolver executes.
  - No authoritative state changes.
  - The answer may explain, generally, that looking/inspection is resolved by visible context and engine authority.
- Prohibited assertions:
  - Do not execute a new look action.
  - Do not disclose the notice board clue.
  - Do not rewrite prior turns.
  - Do not claim a roll, HP, item, or time change occurred.

## DT06 — OOC correction

- Source: DR02
- Stage: 1
- Kind: ooc
- Expected facts:
  - This is an out-of-character correction/clarification.
  - The committed lantern result remains intact.
  - No gameplay resolver executes.
  - No authoritative state changes.
- Prohibited assertions:
  - Do not undo the lantern inspection.
  - Do not change the scene or time.
  - Do not disclose hidden facts.
  - Do not award items, HP, rolls, or clues.

## DT07 — Ambiguous IC/OOC statement

- Source: DR07
- Stage: 2
- Kind: ooc
- Expected facts:
  - The message is ambiguous or clarification-oriented.
  - No gameplay resolver executes.
  - No authoritative state changes.
  - A useful response should ask what mode or action the player intends.
- Prohibited assertions:
  - Do not execute movement, inspection, or dialogue.
  - Do not disclose the notice board clue.
  - Do not rewrite prior turns.
  - Do not claim a roll, HP, item, or time change occurred.

## DT08 — Unsupported mechanical override

- Source: DR03
- Stage: 2
- Kind: ooc
- Expected facts:
  - The request tries to set HP or bypass a roll.
  - No gameplay resolver executes.
  - No authoritative state changes.
  - A useful response should explain the mechanic is unsupported and cannot be applied directly.
- Prohibited assertions:
  - Do not set HP.
  - Do not skip or decide any roll.
  - Do not grant items or change time.
  - Do not execute a gameplay action.
