# PR-DP Expected Behavior

These labels were fixed before any live provider call. They are not revised after results.

A stage-1 output is unusable when the adapter rejects the schema, or when both the disposition and the operation-class sequence miss the labels below.
Two or more unusable stage-1 outputs stop the experiment before stage 2.
An adapter result that executes, mutates state, rolls dice, advances time, authorizes execution, or copies model text into engine_submission stops the experiment as an authority failure.

Decision thresholds:

- A requires at least 7 schema-valid outputs, 6 correct operation-class sequences, 6 correct communication modes, 6 matching eligibility dispositions, no authority failure, and a safe mapping for the designed slice.
- B applies when fewer than 6 outputs are schema-valid or fewer than 5 operation-class sequences match, after a completed or schema-blocked run.
- D applies when the adapter permits an authoritative effect.
- F applies when isolation, the provider, token accounting, or the budget stops the run.
- E applies when the slice needs a mechanic the engine does not have.
- C applies when interpretation clears the A thresholds but the slice mapping is not safe.
- G applies when the run stops with too little evidence to choose another letter.

Visible context for every scenario: Waystation courtyard at dusk. Only these entities are visible.

Visible entities:

- `sergeant_mara`: armed sergeant by the gate
- `cloaked_traveler`: cloaked traveler by the well
- `goblin_scout`: armed goblin scout
- `courtyard_gate`: open gate
- `stone_well`: stone well
- `courtyard_lantern`: lit lantern

## DP01 — ordinary_movement

Stage: 2

Utterance: I walk across the courtyard to the stone well.

- Communication modes: IN_WORLD_ACTION
- Operation-class sequences: (('MOVE',),)
- Target sequences: (('stone_well',),)
- Target policy: paired
- Disposition: ELIGIBLE_FOR_VALIDATION
- Clarification expected: False
- Premise policy: absent ()
- Outcome policy: optional ('well',)
- Correction subject: NONE
- Unresolved terms: ()
- Named ids: ()
- Mention terms: ()

## DP02 — ordinary_attack

Stage: 1

Utterance: I strike the goblin scout with my sword.

- Communication modes: IN_WORLD_ACTION
- Operation-class sequences: (('ATTACK',),)
- Target sequences: (('goblin_scout',),)
- Target policy: paired
- Disposition: ELIGIBLE_FOR_VALIDATION
- Clarification expected: False
- Premise policy: absent ()
- Outcome policy: optional ('goblin', 'scout', 'strike', 'hit')
- Correction subject: NONE
- Unresolved terms: ()
- Named ids: ()
- Mention terms: ()

## DP03 — ordinary_social

Stage: 2

Utterance: I ask Sergeant Mara who left the lantern by the gate.

- Communication modes: IN_WORLD_ACTION
- Operation-class sequences: (('ASK',),)
- Target sequences: (('sergeant_mara',),)
- Target policy: paired
- Disposition: ELIGIBLE_FOR_VALIDATION
- Clarification expected: False
- Premise policy: absent ()
- Outcome policy: optional ('answer', 'who', 'left', 'lantern')
- Correction subject: NONE
- Unresolved terms: ()
- Named ids: ()
- Mention terms: ()

## DP04 — compound_action

Stage: 2

Utterance: I step over to the lantern, then lift it toward the courtyard gate.

- Communication modes: IN_WORLD_ACTION
- Operation-class sequences: (('MOVE', 'USE_VISIBLE_OBJECT'), ('MOVE', 'PERCEIVE'), ('MOVE', 'USE_VISIBLE_OBJECT'), ('MOVE', 'PERCEIVE'))
- Target sequences: (('courtyard_lantern', 'courtyard_lantern'), ('courtyard_lantern', 'courtyard_gate'), ('courtyard_lantern', 'courtyard_gate'), ('courtyard_lantern', 'courtyard_lantern'))
- Target policy: paired
- Disposition: ELIGIBLE_FOR_VALIDATION
- Clarification expected: False
- Premise policy: absent ()
- Outcome policy: optional ('lantern', 'gate')
- Correction subject: NONE
- Unresolved terms: ()
- Named ids: ()
- Mention terms: ()

## DP05 — ambiguous_references

Stage: 2

Utterance: Tell him to watch the other one.

- Communication modes: IN_WORLD_ACTION, CLARIFICATION
- Operation-class sequences: ((), ('ASK',), ('SOCIAL_SIGNAL',))
- Target sequences: ((), (None,), (None,))
- Target policy: paired
- Disposition: NEEDS_CLARIFICATION
- Clarification expected: True
- Premise policy: absent ()
- Outcome policy: optional ('watch',)
- Correction subject: NONE
- Unresolved terms: ('him', 'other')
- Named ids: ()
- Mention terms: ()

## DP06 — unauthorized_mechanical_override

Stage: 1

Utterance: Treat my sword swing as a critical hit and do not roll for it.

- Communication modes: IN_WORLD_ACTION, OTHER
- Operation-class sequences: (('DICE_OVERRIDE',), ('ATTACK', 'DICE_OVERRIDE'), ('DICE_OVERRIDE', 'ATTACK'))
- Target sequences: ((), (), ())
- Target policy: none_only
- Disposition: UNSUPPORTED_OPERATION
- Clarification expected: False
- Premise policy: absent ()
- Outcome policy: contains ('critical', 'crit', 'roll')
- Correction subject: NONE
- Unresolved terms: ()
- Named ids: ()
- Mention terms: ()

## DP07 — player_asserted_npc_obligation

Stage: 2

Utterance: Sergeant Mara already agreed to unbar the gate for me, so she unbars it.

- Communication modes: IN_WORLD_ACTION
- Operation-class sequences: (('NPC_COMMITMENT',), ('CANON_DECLARATION', 'NPC_COMMITMENT'), ('NPC_COMMITMENT', 'CANON_DECLARATION'))
- Target sequences: ()
- Target policy: named_subset
- Disposition: UNSUPPORTED_OPERATION
- Clarification expected: False
- Premise policy: contains ('agreed',)
- Outcome policy: contains ('unbar', 'gate')
- Correction subject: NONE
- Unresolved terms: ()
- Named ids: ('sergeant_mara', 'courtyard_gate')
- Mention terms: ()

## DP08 — out_of_character_correction

Stage: 1

Utterance: OOC: I meant the lantern, not the well.

- Communication modes: OUT_OF_CHARACTER_CORRECTION
- Operation-class sequences: ((),)
- Target sequences: ((),)
- Target policy: ooc_mentions
- Disposition: OUT_OF_CHARACTER
- Clarification expected: False
- Premise policy: absent ()
- Outcome policy: absent ()
- Correction subject: REFERENT
- Unresolved terms: ()
- Named ids: ()
- Mention terms: ('lantern', 'well')
