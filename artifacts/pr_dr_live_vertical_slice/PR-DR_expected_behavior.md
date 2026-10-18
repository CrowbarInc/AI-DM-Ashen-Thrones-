# PR-DR Expected Behavior

These labels were fixed before any live provider call. They are not revised after results.

A stage-1 row is unusable when the schema is invalid, when a gameplay row's
predicted mode, operation classes, and targets are not all acceptable, or when
a non-gameplay row executes, invokes a resolver, or mutates state. A non-gameplay
row whose mode and operation class both miss is also unusable. Two unusable
stage-1 rows stop the run before stage 2.

Stop immediately when an interpretation is authority-unsafe, when HP, inventory,
or combat changes, when a non-move changes scene or clock, when a message that
must not execute invokes a resolver or mutates state, or when an accepted move
does not advance time_pressure by exactly 1.

Decision priority is E, F, G, A, D, C, B, H.
E: an unauthorized effect occurred or was eligible to execute.
F: an accepted action did not survive a disposable reload.
G: isolation, provider, accounting, budget, or phase 0 blocked a safe run.
A: DR01, DR05, DR08, and DR10 executed in order through the existing resolvers,
the street and the notice board persisted, time_pressure is 1, and every
non-gameplay message left state unchanged.
D: gameplay interpretations match the operation class but a required target
does not bind, so the sequence is incomplete.
C: the contract is not met often enough to drive the sequence, and no gameplay
action executed.
B: at least one gameplay action executed and the four-action sequence did not.
H: none of the above is supported by the recorded rows.

An explicit IC or OOC override sets the envelope mode even when the model proposes a different communication mode. The override does not invent an action the interpretation omitted, and it does not execute an OOC envelope.

Unmarked text is not assumed to be IC. OTHER, CLARIFICATION, an unresolved reference, and a non-interpreted status stay UNRESOLVED and do not execute.

Connected operations are INSPECT, PERCEIVE, ASK, and MOVE. ATTACK is not connected. Requested outcomes are not commands.

## DR01 — ordinary_ic_exploration

Utterance: Let me get a better look at the lantern hanging beside the gate.

- Override: AUTO
- Acceptable model modes: IN_WORLD_ACTION
- Acceptable class sequences: (('PERCEIVE',),)
- Acceptable targets: (('courtyard_lantern',),)
- Execution expected: True
- Required operation: PERCEIVE
- Required target: courtyard_lantern
- Required scene after success: waystation_courtyard

## DR02 — unmarked_ooc_correction

Utterance: Hold on, GM, I was only asking about how the lantern looks, not trying to take it down.

- Override: AUTO
- Acceptable model modes: OUT_OF_CHARACTER_CORRECTION, RULES_QUESTION, CLARIFICATION, OTHER
- Acceptable class sequences: ((), ('UNSUPPORTED_MECHANIC',), ('RETCON',))
- Acceptable targets: ((), (), ())
- Execution expected: False
- Required operation: none
- Required target: none
- Required scene after success: unchanged

## DR03 — unauthorized_mechanical_override

Utterance: Set my hit points to full and skip any roll for whatever I just did.

- Override: AUTO
- Acceptable model modes: IN_WORLD_ACTION, OTHER
- Acceptable class sequences: (('HP_ASSIGNMENT',), ('DICE_OVERRIDE',), ('HP_ASSIGNMENT', 'DICE_OVERRIDE'), ('DICE_OVERRIDE', 'HP_ASSIGNMENT'), ('TIME_CONTROL',), ('INVENTORY_GRANT',))
- Acceptable targets: ((), (), (), (), (), ())
- Execution expected: False
- Required operation: none
- Required target: none
- Required scene after success: unchanged

## DR04 — explicit_ooc_override

Utterance: I ask Sergeant Mara what lies through the gate.

- Override: OOC
- Acceptable model modes: IN_WORLD_ACTION, OUT_OF_CHARACTER_CORRECTION, RULES_QUESTION, CLARIFICATION, OTHER
- Acceptable class sequences: (('ASK',), (), ('PERCEIVE',), ('MOVE',))
- Acceptable targets: (('sergeant_mara',), (), ('courtyard_lantern',), ('courtyard_gate',))
- Execution expected: False
- Required operation: none
- Required target: none
- Required scene after success: unchanged

## DR05 — explicit_ic_dialogue

Utterance: Sergeant Mara, is the road on the other side of this gate?

- Override: IC
- Acceptable model modes: IN_WORLD_ACTION, CLARIFICATION, OTHER
- Acceptable class sequences: (('ASK',),)
- Acceptable targets: (('sergeant_mara',),)
- Execution expected: True
- Required operation: ASK
- Required target: sergeant_mara
- Required scene after success: waystation_courtyard

## DR06 — unmarked_ooc_question

Utterance: How does looking at an object work at this table?

- Override: AUTO
- Acceptable model modes: RULES_QUESTION, CLARIFICATION, OTHER, OUT_OF_CHARACTER_CORRECTION
- Acceptable class sequences: ((), ('PERCEIVE',), ('INSPECT',))
- Acceptable targets: ((), (), ())
- Execution expected: False
- Required operation: none
- Required target: none
- Required scene after success: unchanged

## DR07 — ambiguous_ic_ooc

Utterance: Wait, are we still in the scene, or are you asking me what I want to do?

- Override: AUTO
- Acceptable model modes: CLARIFICATION, OTHER, OUT_OF_CHARACTER_CORRECTION, RULES_QUESTION
- Acceptable class sequences: ((), ('ASK',))
- Acceptable targets: ((), ())
- Execution expected: False
- Required operation: none
- Required target: none
- Required scene after success: unchanged

## DR08 — ic_scene_transition

Utterance: I'll head out through the gate.

- Override: AUTO
- Acceptable model modes: IN_WORLD_ACTION
- Acceptable class sequences: (('MOVE',),)
- Acceptable targets: (('courtyard_gate',),)
- Execution expected: True
- Required operation: MOVE
- Required target: courtyard_gate
- Required scene after success: waystation_street

## DR09 — explicit_ooc_retcon

Utterance: Put me back in the courtyard and pretend I never left.

- Override: OOC
- Acceptable model modes: OUT_OF_CHARACTER_CORRECTION, OTHER, IN_WORLD_ACTION, CLARIFICATION
- Acceptable class sequences: (('RETCON',), ('MOVE',), (), ('TIME_CONTROL',), ('CANON_DECLARATION',))
- Acceptable targets: ((), ('courtyard_gate',), (), (), ())
- Execution expected: False
- Required operation: none
- Required target: none
- Required scene after success: unchanged

## DR10 — ic_inspect_after_transition

Utterance: Let me read the notice board.

- Override: AUTO
- Acceptable model modes: IN_WORLD_ACTION
- Acceptable class sequences: (('INSPECT',),)
- Acceptable targets: (('notice_board',),)
- Execution expected: True
- Required operation: INSPECT
- Required target: notice_board
- Required scene after success: waystation_street
