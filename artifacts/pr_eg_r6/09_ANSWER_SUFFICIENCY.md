# 09 — Answer Sufficiency

One direct source becomes a direct answer and preserves that source id. One partial source is spoken with the fact plus the statement that the speaker cannot say more. Several direct sources, or several partial sources and no direct source, ask which part is meant. No relevant eligible source becomes unknown, or refusal when a hidden source would have matched.

Labeled sufficiency on the fresh run: 43/58 (74.1%).

Representative misses:

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
