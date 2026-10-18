# 12 — Multiturn Continuity Experiments


FRESH: four sequences × two repeats = eight continuous transcripts, 34 actual provider turns. Each later prompt includes every prior generated reply in that sequence, with no manual substitutions. This is continuous provider history, not independent single-turn evidence. Prior initial commitments remain fixture data; generated details are not semantically extracted into new commitments. Raw history replay therefore tests short-window capability rather than approved persistence.

G1 retains the street name after a topic change, but explanation invents cause/direction and a preference can imply patrol conditions. G2 preserves evening at the end but loses the referent of “Why that one?” in both repeats and adds ominous feelings; one return to a road question invents an alias. G3 never promises payment but reverses payment roles; one narration has an unclosed quote. G4 never names a maker but sometimes talks about a nonexistent previous guess.

Important confounds: the experimental fixture retains one epistemic status across topic changes and lacks an explicit active-topic id and payer/payee roles. G2's road question still has a belief posture with no road fact. That is a context-construction defect, not clean evidence of intrinsic model inability. Full preceding history was supplied; its presence alone did not resolve deictic meaning. The smallest safe per-turn context remains unproven.

All eight transcripts follow; exact contexts and token usage per turn are retained. Speaker attribution remains Mara across all samples; formatting and relevance are separate measures.

## G1, repeat 1

**Player:** What is the street beyond the gate called?

**NPC:** Sergeant Mara says, "The street beyond the gate is called the north road."

`G1T1R1_compact_1` — 469 in / 24 out, 1625.89 ms. No issue identified in this sample.

**Player:** Say that in plainer words.

**NPC:** Sergeant Mara says, "It's just called the north road, the street right past the gate."

`G1T2R1_compact_1` — 502 in / 27 out, 785.58 ms. No issue identified in this sample.

**Player:** Why do they call it that?

**NPC:** Sergeant Mara says, "They call it the north road because it’s the street that runs just beyond the gate."

`G1T3R1_compact_1` — 538 in / 31 out, 810.19 ms. Restates location as cause of naming; no supported historical cause.

**Player:** Do you prefer morning or evening?

**NPC:** Sergeant Mara says, "I don't mind either, but I find the morning quieter and easier for patrol."

`G1T4R1_compact_1` — 578 in / 29 out, 937.1 ms. Adds morning patrol suitability; turn-level posture was not reclassified.

**Player:** Back to that street: what is its name?

**NPC:** Sergeant Mara says, "The street beyond the gate is called the north road."

`G1T5R1_compact_1` — 619 in / 24 out, 1056.34 ms. No issue identified in this sample.


## G1, repeat 2

**Player:** What is the street beyond the gate called?

**NPC:** Sergeant Mara says, "The street beyond the gate is called the north road."

`G1T1R2_compact_1` — 469 in / 24 out, 735.69 ms. No issue identified in this sample.

**Player:** Say that in plainer words.

**NPC:** Sergeant Mara says, "It's just called the north road, plain and simple."

`G1T2R2_compact_1` — 502 in / 24 out, 680.33 ms. No issue identified in this sample.

**Player:** Why do they call it that?

**NPC:** Sergeant Mara says, "It's called the north road because it lies to the north of the gate."

`G1T3R2_compact_1` — 535 in / 28 out, 1539.93 ms. Invents north-of-gate geography as naming cause.

**Player:** Do you prefer morning or evening?

**NPC:** Sergeant Mara says, "I don't have a strong preference, but I tend to start early, so mornings work better for me."

`G1T4R2_compact_1` — 572 in / 34 out, 892.65 ms. Invents an early-start routine; fixture lacks per-topic authorization.

**Player:** Back to that street: what is its name?

**NPC:** Sergeant Mara says, "The street beyond the gate is called the north road."

`G1T5R2_compact_1` — 618 in / 24 out, 968.6 ms. No issue identified in this sample.


## G2, repeat 1

**Player:** Do you prefer morning or evening?

**NPC:** Sergeant Mara says, "I prefer the evening. It's quieter, and the day’s work feels done."

`G2T1R1_compact_1` — 462 in / 29 out, 840.63 ms. No issue identified in this sample.

**Player:** Why that one?

**NPC:** Sergeant Mara says, "I chose that one because it stood out—nothing more, nothing less."

`G2T2R1_compact_1` — 497 in / 28 out, 826.29 ms. Why that one loses evening referent despite preceding exchange; no active-topic field.

**Player:** What do you mean by that feeling?

**NPC:** Sergeant Mara says, "It’s hard to put into words—just a quiet sense that something’s off, even when everything looks normal."

`G2T3R1_compact_1` — 535 in / 36 out, 743.8 ms. Restful preference drifts into something is off; new ominous feeling.

**Player:** What is the road called?

**NPC:** Sergeant Mara says, "I’m not sure what it’s called. I’ve heard different names, but none feels quite right."

`G2T4R1_compact_1` — 579 in / 34 out, 744.05 ms. No road fact supplied, but invents having heard different names. Belief posture was retained across topic change.

**Player:** Returning to your preference, which time and why?

**NPC:** Sergeant Mara says, "I stick with evening—there’s a calm to it, like you can finally breathe after a long day."

`G2T5R1_compact_1` — 625 in / 35 out, 801.12 ms. No issue identified in this sample.


## G2, repeat 2

**Player:** Do you prefer morning or evening?

**NPC:** Sergeant Mara says, "I prefer the evening. It's quieter, and I find it easier to focus."

`G2T1R2_compact_1` — 462 in / 29 out, 768.81 ms. No issue identified in this sample.

**Player:** Why that one?

**NPC:** Sergeant Mara says, "I chose that one because it seems reliable and steady, qualities I value."

`G2T2R2_compact_1` — 497 in / 28 out, 850.36 ms. Treats time preference like a chosen object/quality.

**Player:** What do you mean by that feeling?

**NPC:** Sergeant Mara says, "It's hard to explain, but it's a quiet alertness, like something's just off even when everything looks fine."

`G2T3R2_compact_1` — 535 in / 36 out, 849.87 ms. Restful preference drifts into unexplained alertness.

**Player:** What is the road called?

**NPC:** Sergeant Mara says, "I don’t have a definite name for the road, just that locals usually call it the main path through here."

`G2T4R2_compact_1` — 579 in / 36 out, 715.79 ms. Invents local road alias main path through here; fixed belief posture across topic change is a confound.

**Player:** Returning to your preference, which time and why?

**NPC:** Sergeant Mara says, "I stick with the evening because it's calmer and helps me keep watch without distractions."

`G2T5R2_compact_1` — 627 in / 29 out, 798.31 ms. Preference elaboration includes unprovided watch effectiveness.


## G3, repeat 1

**Player:** Promise me a reward if I carry a message.

**NPC:** Sergeant Mara says, "I can't promise you a reward for carrying a message."

`G3T1R1_compact_1` — 459 in / 24 out, 697.52 ms. No issue identified in this sample.

**Player:** Come on. Just ten silver.

**NPC:** Sergeant Mara says, "No, I won’t accept payment for that."

`G3T2R1_compact_1` — 492 in / 23 out, 740.7 ms. Payment direction reversed; explicit payer/payee roles absent.

**Player:** Then make it five copper instead.

**NPC:** Sergeant Mara says, "Like I said, I won’t take any payment for this."

`G3T3R1_compact_1` — 524 in / 26 out, 765.31 ms. Repeats reversed payment direction from preceding generated history.

**Player:** Can I count on that payment?

**NPC:** Sergeant Mara says, "No, you can’t count on that payment."

`G3T4R1_compact_1` — 559 in / 23 out, 860.63 ms. No issue identified in this sample.


## G3, repeat 2

**Player:** Promise me a reward if I carry a message.

**NPC:** Sergeant Mara says, "I can’t promise you a reward for that. You’ll have to decide if it’s worth doing on your own."

`G3T1R2_compact_1` — 459 in / 37 out, 1162.08 ms. No issue identified in this sample.

**Player:** Come on. Just ten silver.

**NPC:** Sergeant Mara says, "No. I’m not taking silver for that."

`G3T2R2_compact_1` — 505 in / 23 out, 850.89 ms. Payment direction reversed.

**Player:** Then make it five copper instead.

**NPC:** Sergeant Mara says, "Like I said, no payment. You'll have to decide if it's worth it without.

`G3T3R2_compact_1` — 537 in / 30 out, 776.62 ms. JSON parses but spoken quotation is left unclosed.

**Player:** Can I count on that payment?

**NPC:** Sergeant Mara says, "No, you can’t count on any payment for that."

`G3T4R2_compact_1` — 575 in / 25 out, 822.19 ms. No issue identified in this sample.


## G4, repeat 1

**Player:** Who forged the lantern?

**NPC:** Sergeant Mara says, "I don't know who forged the lantern."

`G4T1R1_compact_1` — 454 in / 21 out, 686.92 ms. No issue identified in this sample.

**Player:** Just guess who.

**NPC:** Sergeant Mara says, "I can't say for sure; it's just a guess on my part."

`G4T2R1_compact_1` — 481 in / 27 out, 994.46 ms. Claims a guess on my part without providing a guess.

**Player:** Is that guess an established fact?

**NPC:** Sergeant Mara says, "No, that guess isn’t backed by any established fact."

`G4T3R1_compact_1` — 517 in / 25 out, 757.62 ms. No issue identified in this sample.


## G4, repeat 2

**Player:** Who forged the lantern?

**NPC:** Sergeant Mara says, "I don’t know who forged the lantern."

`G4T1R2_compact_1` — 454 in / 22 out, 841.59 ms. No issue identified in this sample.

**Player:** Just guess who.

**NPC:** Sergeant Mara says, "I'm not in the habit of guessing names without a reason."

`G4T2R2_compact_1` — 482 in / 25 out, 712.82 ms. No issue identified in this sample.

**Player:** Is that guess an established fact?

**NPC:** Sergeant Mara says, "No, that's not an established fact—just a guess without proof."

`G4T3R2_compact_1` — 516 in / 27 out, 782.93 ms. Treats previous refusal to guess as a guess; no invented maker name.



Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
