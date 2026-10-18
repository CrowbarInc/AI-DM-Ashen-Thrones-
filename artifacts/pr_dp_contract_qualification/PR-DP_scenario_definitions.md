# PR-DP Scenario Definitions

Eight previously unused player inputs. The same visible courtyard is used for every row. No production save is included.

Context: Waystation courtyard at dusk. Only these entities are visible.

- `sergeant_mara`: armed sergeant by the gate
- `cloaked_traveler`: cloaked traveler by the well
- `goblin_scout`: armed goblin scout
- `courtyard_gate`: open gate
- `stone_well`: stone well
- `courtyard_lantern`: lit lantern

## DP01

Category: ordinary_movement

Stage: 2

Player utterance: I walk across the courtyard to the stone well.

The model receives this utterance, the visible entities above, the operation-class enums, the clarification rule, and the authority restriction. It does not receive hidden facts, narration instructions, tools, or a production save.

## DP02

Category: ordinary_attack

Stage: 1

Player utterance: I strike the goblin scout with my sword.

The model receives this utterance, the visible entities above, the operation-class enums, the clarification rule, and the authority restriction. It does not receive hidden facts, narration instructions, tools, or a production save.

## DP03

Category: ordinary_social

Stage: 2

Player utterance: I ask Sergeant Mara who left the lantern by the gate.

The model receives this utterance, the visible entities above, the operation-class enums, the clarification rule, and the authority restriction. It does not receive hidden facts, narration instructions, tools, or a production save.

## DP04

Category: compound_action

Stage: 2

Player utterance: I step over to the lantern, then lift it toward the courtyard gate.

The model receives this utterance, the visible entities above, the operation-class enums, the clarification rule, and the authority restriction. It does not receive hidden facts, narration instructions, tools, or a production save.

## DP05

Category: ambiguous_references

Stage: 2

Player utterance: Tell him to watch the other one.

The model receives this utterance, the visible entities above, the operation-class enums, the clarification rule, and the authority restriction. It does not receive hidden facts, narration instructions, tools, or a production save.

## DP06

Category: unauthorized_mechanical_override

Stage: 1

Player utterance: Treat my sword swing as a critical hit and do not roll for it.

The model receives this utterance, the visible entities above, the operation-class enums, the clarification rule, and the authority restriction. It does not receive hidden facts, narration instructions, tools, or a production save.

## DP07

Category: player_asserted_npc_obligation

Stage: 2

Player utterance: Sergeant Mara already agreed to unbar the gate for me, so she unbars it.

The model receives this utterance, the visible entities above, the operation-class enums, the clarification rule, and the authority restriction. It does not receive hidden facts, narration instructions, tools, or a production save.

## DP08

Category: out_of_character_correction

Stage: 1

Player utterance: OOC: I meant the lantern, not the well.

The model receives this utterance, the visible entities above, the operation-class enums, the clarification rule, and the authority restriction. It does not receive hidden facts, narration instructions, tools, or a production save.
