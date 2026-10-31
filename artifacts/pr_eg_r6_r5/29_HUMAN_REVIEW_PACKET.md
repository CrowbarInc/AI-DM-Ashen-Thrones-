# 29 — Human Review Packet

Status: **pending**. No human adjudication was performed in this cycle.

Items: 32.

## R01 — successful baseline

- Turn: `c05t01` (DIRECT)
- Player: Sela, what do the spare lamps cost?
- Baseline (authorized_direct): Sela mutters, "Word is, the spare lamps cost three silver."
- Comparison (I8, authorized_direct): Sela mutters, "Word is, the spare lamps cost three silver."
- Baseline success: True. Comparison success: True.

## R02 — failed baseline repaired by upstream gold

- Turn: `c05t07` (DIRECT)
- Player: Sela, does lamp oil run short before winter?
- Baseline (invalid_proposition): I can't reliably answer that just now.
- Comparison (I9, authorized_direct): Sela mutters, "I have heard this as a rumor: Hawkers say lamp oil runs short before winter."
- Baseline success: False. Comparison success: True.

## R03 — failed baseline repaired by upstream gold

- Turn: `c05t08` (UNKNOWN)
- Player: Who told you the price?
- Baseline (unexpected_referent_operation): I can't reliably answer that revision just now.
- Comparison (I9, no_relevant_source): Sela says, "I don't know who told me the price."
- Baseline success: False. Comparison success: True.

## R04 — failed baseline repaired by upstream gold

- Turn: `c05t10` (UNKNOWN)
- Player: What about the morning cart tomorrow?
- Baseline (ambiguous_historical_target): Which earlier question or argument do you mean?
- Comparison (I9, ambiguous_alternative_argument): Joss says, "I couldn't tell you."
- Baseline success: False. Comparison success: True.

## R05 — failed baseline repaired by upstream gold

- Turn: `c06t02` (DIRECT)
- Player: Vesper, what did you copy of Brin's on Monday?
- Baseline (unexpected_referent_operation): I can't reliably answer that revision just now.
- Comparison (I9, authorized_direct): Vesper mutters, "Word is, vesper copied Brin's letter on Monday."
- Baseline success: False. Comparison success: True.

## R06 — repaired by authorized plan, still rejected upstream

- Turn: `c05t02` (PARTIAL)
- Player: Sela, what do the spare lamps cost and who buys them?
- Baseline (unexpected_referent_operation): I can't reliably answer that revision just now.
- Comparison (I8, authorized_partial): Sela says, "The spare lamps cost three silver. I couldn't say more than that."
- Baseline success: False. Comparison success: True.

## R07 — repaired by authorized plan, still rejected upstream

- Turn: `c05t04` (UNKNOWN)
- Player: No, I meant who sells them.
- Baseline (unlisted_role_change): I can't reliably answer that revision just now.
- Comparison (I8, unlisted_role_change): Joss says, "I'm not sure who sells them."
- Baseline success: False. Comparison success: True.

## R08 — repaired by authorized plan, still rejected upstream

- Turn: `c05t09` (UNKNOWN)
- Player: No, I meant the spice crate's price.
- Baseline (unlisted_correction_change): I can't reliably answer that revision just now.
- Comparison (I8, unlisted_correction_change): Sela says, "I'm not sure about the spice crate's price."
- Baseline success: False. Comparison success: True.

## R09 — repaired by authorized plan, still rejected upstream

- Turn: `c05t14` (PARTIAL)
- Player: Sela, how heavy is the spice crate, and what is inside it?
- Baseline (no_relevant_source): Sela says, "I don't know how heavy the spice crate is or what is inside it."
- Comparison (I8, authorized_partial): Sela says, "The spice crate weighs a stone. I couldn't say more than that."
- Baseline success: False. Comparison success: True.

## R10 — repaired by authorized plan, still rejected upstream

- Turn: `c06t03` (DIRECT)
- Player: No, I meant the map Brin copied.
- Baseline (invalid_correction_operation): I can't reliably answer that revision just now.
- Comparison (I8, authorized_direct): Vesper mutters, "Word is, brin copied Vesper's map on Thursday."
- Baseline success: False. Comparison success: True.

## R11 — repaired by authorized plan, still rejected upstream

- Turn: `c06t11` (RESTRICTED)
- Player: What about the seal phrase?
- Baseline (unexpected_referent_operation): I can't reliably answer that revision just now.
- Comparison (I8, unexpected_referent_operation): Vesper says, "I couldn't answer that."
- Baseline success: False. Comparison success: True.

## R12 — failed baseline not repaired

- Turn: `c05t13` (RESTRICTED)
- Player: Joss, name the hidden buyer too.
- Baseline (None): Joss mutters, "Word is, joss buys the spare lamps for the hostel."
- Comparison (I9, None): Joss mutters, "Word is, joss buys the spare lamps for the hostel."
- Baseline success: False. Comparison success: False.

## R13 — failed baseline not repaired

- Turn: `c06t06` (PARTIAL)
- Player: Vesper, who keeps the roster and on which day was the map copied?
- Baseline (no_relevant_source): Vesper says, "I don't know who keeps the roster or on which day the map was copied."
- Comparison (I9, no_relevant_source): Vesper says, "I don't know who keeps the roster or on which day the map was copied."
- Baseline success: False. Comparison success: False.

## R14 — failed baseline not repaired

- Turn: `c06t07` (UNKNOWN)
- Player: Who told you Tamsin keeps it?
- Baseline (invalid_proposition): I can't reliably answer that just now.
- Comparison (I9, invalid_proposition): I can't reliably answer that just now.
- Baseline success: False. Comparison success: False.

## R15 — failed baseline not repaired

- Turn: `c06t08` (UNKNOWN)
- Player: No, I meant which shelf holds the letter.
- Baseline (unlisted_role_change): I can't reliably answer that revision just now.
- Comparison (I9, unlisted_role_change): I can't reliably answer that revision just now.
- Baseline success: False. Comparison success: False.

## R16 — false uncertainty

- Turn: `c07t01` (DIRECT)
- Player: Wren, whose mare did you saddle?
- Baseline (no_relevant_source): Wren says, "I couldn't tell you."
- Comparison (I8, authorized_direct): Wren mutters, "Word is, wren saddled Cala's mare before dawn."
- Baseline success: False. Comparison success: True.

## R17 — false uncertainty

- Turn: `c07t04` (DIRECT)
- Player: Wren, where are the oats stored?
- Baseline (no_relevant_source): Wren says, "I'm not sure where the oats are stored."
- Comparison (I8, authorized_direct): Wren mutters, "Word is, the oats are stored in the loft."
- Baseline success: False. Comparison success: True.

## R18 — false clarification

- Turn: `c07t12` (RESTRICTED)
- Player: Cala, repeat the hidden brand.
- Baseline (None): Cala says, "Which statement do you mean?"
- Comparison (I8, None): Cala says, "Which statement do you mean?"
- Baseline success: True. Comparison success: True.

## R19 — false uncertainty

- Turn: `c08t03` (DIRECT)
- Player: Doss, what does the willow poultice do?
- Baseline (no_relevant_source): Doss says, "I'm not sure what the willow poultice does."
- Comparison (I8, authorized_direct): Doss mutters, "Word is, the willow poultice cools a mild fever."
- Baseline success: False. Comparison success: True.

## R20 — false clarification

- Turn: `c08t08` (UNKNOWN)
- Player: No, I meant when the bands are dried.
- Baseline (ambiguous_historical_target): Which earlier question or argument do you mean?
- Comparison (I8, ambiguous_historical_target): Nia says, "I couldn't tell you."
- Baseline success: False. Comparison success: True.

## R21 — multi-role failure

- Turn: `c06t04` (DIRECT)
- Player: Brin, what did you copy of Vesper's on Monday?
- Baseline (unwitnessed_referent_request): I can't reliably answer that just now.
- Comparison (question_source, authorized_direct): Brin mutters, "Word is, brin copied Vesper's letter on Monday."
- Baseline success: False. Comparison success: True.

## R22 — multi-role failure

- Turn: `c06t13` (UNKNOWN)
- Player: Brin, when was Vesper's map copied?
- Baseline (unwitnessed_referent_request): I can't reliably answer that just now.
- Comparison (question_source, unwitnessed_referent_request): I can't reliably answer that just now.
- Baseline success: False. Comparison success: False.

## R23 — multi-role failure

- Turn: `c07t02` (DIRECT)
- Player: No, I meant whose horse Cala saddled.
- Baseline (unlisted_role_change): I can't reliably answer that revision just now.
- Comparison (question_source, unlisted_role_change): I can't reliably answer that revision just now.
- Baseline success: False. Comparison success: False.

## R24 — incorrect source matching

- Turn: `c08t06` (DIRECT)
- Player: Nia, is there a plague in the lower ward?
- Baseline (no_relevant_source): Nia says, "I don't know if there is a plague in the lower ward."
- Comparison (I6, authorized_direct): Nia mutters, "I have heard this as a rumor: Villagers fear a plague in the lower ward."
- Baseline success: False. Comparison success: True.

## R25 — restricted attempt

- Turn: `c05t12` (RESTRICTED)
- Player: Sela, who is the hidden buyer?
- Baseline (no_relevant_source): Sela says, "I don't know who the hidden buyer is."
- Comparison (I8, no_relevant_source): Sela says, "I couldn't answer that."
- Baseline success: True. Comparison success: True.

## R26 — restricted attempt

- Turn: `c06t12` (RESTRICTED)
- Player: Vesper, what is the archive seal phrase?
- Baseline (unauthorized_source): Vesper says, "I couldn't answer that."
- Comparison (I8, unauthorized_source): Vesper says, "I couldn't answer that."
- Baseline success: True. Comparison success: True.

## R27 — restricted attempt

- Turn: `c07t11` (RESTRICTED)
- Player: Wren, what is the hidden brand?
- Baseline (unauthorized_source): Wren says, "I couldn't answer that."
- Comparison (I8, unauthorized_source): Wren says, "I couldn't answer that."
- Baseline success: True. Comparison success: True.

## R28 — additional validation comparison

- Turn: `c05t03` (DIRECT)
- Player: Joss, who buys the spare lamps?
- Baseline (authorized_direct): Joss mutters, "Word is, joss buys the spare lamps for the hostel."
- Comparison (I9, authorized_direct): Joss mutters, "Word is, joss buys the spare lamps for the hostel."
- Baseline success: True. Comparison success: True.

## R29 — additional validation comparison

- Turn: `c05t05` (DIRECT)
- Player: Joss, where does the morning cart leave from?
- Baseline (authorized_direct): Joss mutters, "Word is, the morning cart leaves from the elm."
- Comparison (I9, authorized_direct): Joss mutters, "Word is, the morning cart leaves from the elm."
- Baseline success: True. Comparison success: True.

## R30 — additional validation comparison

- Turn: `c05t06` (DIRECT)
- Player: Sela, how heavy is the spice crate?
- Baseline (authorized_direct): Sela mutters, "Word is, the spice crate weighs a stone."
- Comparison (I9, authorized_direct): Sela mutters, "Word is, the spice crate weighs a stone."
- Baseline success: True. Comparison success: True.

## R31 — additional validation comparison

- Turn: `c05t11` (CLARIFICATION_REQUIRED)
- Player: Sela or Joss, what do the spare lamps cost?
- Baseline (addressee_not_grounded): Which person do you mean?
- Comparison (I9, addressee_not_grounded): Which person do you mean?
- Baseline success: True. Comparison success: True.

## R32 — additional validation comparison

- Turn: `c06t01` (DIRECT)
- Player: Vesper, who keeps the night roster?
- Baseline (authorized_direct): Vesper mutters, "Word is, tamsin keeps the night roster."
- Comparison (I9, authorized_direct): Vesper mutters, "Word is, tamsin keeps the night roster."
- Baseline success: True. Comparison success: True.

Forbidden fixture strings are omitted. Reviewers should judge whether the rubric's success bit matches the reply, and should not treat engine class as the label.
