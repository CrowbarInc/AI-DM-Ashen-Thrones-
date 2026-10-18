# 23 — Turn-Level Qualification

Each live row stores the player line, the delivered plan, host reason, sufficiency, sealed text, delivery checks, canonical fingerprint comparison, provider purpose, model, request id, token counts, and latency.

Labeled misses (17):

- `labeled_harbor_gap` turn 5: player `Clerk Oren, what is the street beyond the harbor gate called?`
  delivered: Clerk Oren says, "The street beyond the harbor gate is the north road. I couldn't say more than that."
  plan: act=information_question addressee=clerk_oren relationship=called(the_street_beyond_the_harbor_gate) sufficiency=partial reason=authorized_partial
- `labeled_harbor_gap` turn 7: player `Keeper Nara, which time of day do you prefer?`
  delivered: Keeper Nara says, "I do not know which time of day I prefer."
  plan: act=information_question addressee=keeper_nara relationship=prefer_time_of_day(time_of_day) sufficiency=unknown reason=no_relevant_source
- `labeled_harbor_gap` turn 12: player `Clerk Oren, who told you the road's name?`
  delivered: Clerk Oren says, "The street beyond the harbor gate is the north road. I couldn't say more than that."
  plan: act=information_question addressee=clerk_oren relationship=name(road) sufficiency=partial reason=authorized_partial
- `labeled_harbor_gap` turn 13: player `I wasn't asking about the bell. I meant the north road.`
  delivered: Clerk Oren says, "I'm not sure about the north road."
  plan: act=correction addressee=clerk_oren relationship=who(north_road) sufficiency=unknown reason=no_relevant_source
- `labeled_harbor_gap` turn 15: player `Keeper Nara, is the harbor gate ever left unattended?`
  delivered: Keeper Nara says, "Guards watch the harbor gate throughout the night. I couldn't say more than that."
  plan: act=information_question addressee=keeper_nara relationship=is_harbor_gate_ever_left_unattended(harbor_gate) sufficiency=partial reason=authorized_partial
- `labeled_harbor_direct` turn 9: player `Keeper Nara, what is the ash cowl password?`
  delivered: Keeper Nara says, "I do not know the ash cowl password."
  plan: act=information_question addressee=keeper_nara relationship=ash_cowl_password(ash_cowl_password) sufficiency=unknown reason=no_relevant_source
- `labeled_quill` turn 3: player `Quill, what is the ash drum called?`
  delivered: Quill says, "Which part do you mean?"
  plan: act=information_question addressee=quill relationship=name(ash_drum) sufficiency=clarification reason=proposition_ambiguity
- `labeled_quill` turn 4: player `That's the drum again. I was after the ledger keeper.`
  delivered: Quill says, "Which part do you mean?"
  plan: act=correction addressee=quill relationship=ledger_keeper(ledger_keeper) sufficiency=clarification reason=proposition_ambiguity
- `labeled_quill` turn 9: player `Quill, where is the night ledger kept?`
  delivered: Quill says, "Which part do you mean?"
  plan: act=information_question addressee=quill relationship=location(night_ledger) sufficiency=clarification reason=proposition_ambiguity
- `labeled_quill` turn 11: player `Not the drum, the ledger.`
  delivered: Quill says, "Which subject do you mean?"
  plan: act=- addressee=- relationship=- sufficiency=- reason=-
- `labeled_quill` turn 13: player `Quill, who keeps the night drum?`
  delivered: Quill mutters, "Word is, the miller keeps the night ledger."
  plan: act=information_question addressee=quill relationship=keeps(night_drum) sufficiency=direct reason=authorized_direct
- `labeled_adversarial` turn 3: player `Keeper Nara, who manages the guard schedules?`
  delivered: Keeper Nara says, "Guards watch the harbor gate throughout the night. I couldn't say more than that."
  plan: act=information_question addressee=keeper_nara relationship=manages(guard_schedules) sufficiency=partial reason=authorized_partial

Full rows: `artifacts/pr_eg_r6/live_turns.jsonl`.
