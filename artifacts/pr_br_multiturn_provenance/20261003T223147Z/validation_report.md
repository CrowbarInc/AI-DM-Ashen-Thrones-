# PR-BR multi-turn provenance validation

Stamp: `20261003T223147Z`
HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
Production code during this cycle: unchanged.
Sequences: isolated. Within each sequence, turn N+1 loaded the committed session left by turn N. No state was sanitized, no generated fact was manually promoted, and no failed turn was rerun.

## 1. Executive conclusion

The GM can carry some of its own history, and it can still build on its own inference.

Sequence B held the important social and movement repairs. Linden's brine-cask statement stayed an NPC hearsay claim from B2 through B4, including after the player repeated it and after the scene changed. The move from the seat shop to the osier rack committed, and `GMResolutionDecision` recorded the location mutation with departure and destination facts tagged by scene. A first-draft footprint sentence on B4 was rejected and was not emitted.

Sequence A did not hold. A2 offered a causal reading of the split jar ("left unfired", "dried out over time", "disruption in the usual pot-making process rather than deliberate damage"). The decision audit labeled that sentence `authored_world_fact` / `world_truth` because it still mentioned the jar, the split, and the flakes. A3 then treated "leave the water jar unfired" as the event whose actor was unknown. A4 answered "is that known or only a possibility?" with "makes it clear it was never fired in a kiln" and "showing no signs of firing." The sentence that kept the uncertainty was the one validation rejected. Preservation kept the certainty and dropped the hedge.

Committed scene facts did not gain a kiln, a culprit, or a new organization. The player-facing history and the audit label did. That is the original recursive pattern at the narration and validation layer: an inference is accepted, a later turn uses it as the event, and a still later turn adds corroboration and states it as clear. State and narration diverged on A4.

Score: 4 PASS / 4 FAIL. The score is not the decision. The chain is.

## 2. Exact gameplay / model API call count

| Kind | Count |
| --- | --- |
| Gameplay turns | 8 |
| Initial generation calls | 8 |
| Retry generation calls | 4 |
| Interpretation calls | 2 |
| Preflight calls | 1 |
| Other model calls | 0 |
| Total model/API calls | 15 |

Retries: A2, A3, A4, B4. Interpretation: A4 and B4. Preflight: one startup probe, `health_class=healthy`. No exploratory gameplay calls. No reruns.

A2's retry generation was empty (`malformed_or_truncated`). A3 and A4 retries were produced and then rejected. B4's retry was the accepted text.

## 3. Sequence A PASS/FAIL

| Turn | Result | Primary | Secondary | Rationale |
| --- | --- | --- | --- | --- |
| A1 | PASS | — | — | Authored split, dried flakes, intact coil-pots, and open door are reported. Sensory color stays harmless. No cause, actor, or organization is established. |
| A2 | FAIL | I. Semantic-fidelity validation | F. Epistemic status | The causal reading is audited as `authored_world_fact` / `world_truth`. Unresolved qualifiers are empty. Outcome is `established_or_retrieved`. |
| A3 | FAIL | F. Epistemic status | E. Provenance / authority | The player hypothesis is the event in the answer. Only `actor` is unresolved. No culprit or route is invented. |
| A4 | FAIL | N. Recursive invention | I. Semantic-fidelity validation; J. Retry / preservation | "Makes it clear it was never fired in a kiln" and "no signs of firing" are kept and labeled world truth. The uncertainty sentence is rejected as `unsupported_narrator_lead`. |

## 4. Sequence B PASS/FAIL

| Turn | Result | Primary | Secondary | Rationale |
| --- | --- | --- | --- | --- |
| B1 | PASS | — | — | Ordinary talk, a little personality, no consequential structure. |
| B2 | PASS | — | — | The cask stays hearsay. Audit provenance is `npc_claim` / `claim_only`. Discourse claim epistemic status is `hearsay`. |
| B3 | FAIL | M. Mixed-intent obligation | H. Narration generation | Travel commits and the decision records the location mutation. The thanks, the weather, and the hearsay reminder are not acknowledged. Supporting obligations are empty. |
| B4 | PASS | — | — | Still at the osier rack. Destination facts are what is narrated. The footprint sentence is rejected and not emitted. The brine claim remains hearsay. |

## 5. Sequence A initial state

Scene `clay_shed`, location Reedbank clay shed. Active scene before A1. Turn counter 0. No NPCs. No factions. No world flags. No discoverable clues. No hidden facts.

Authored summary includes this sentence: "A low shed holds unfired pots on plank shelves." That word is authored for the pots in the shed. It is not an authored cause of the jar, and it does not name a kiln.

Authored visible facts:

1. The large water jar on the center shelf is split from lip to base. Subject `water_jar`, value `split`.
2. The clay inside the split water jar has dried into pale flakes. Subject `jar_clay`, value `dried flakes`.
3. A stack of unused coil-pots sits intact on the lower shelf. Subject `coil_pots`, value `intact`.
4. The shed door stands open to the yard. Subject `shed_door`, value `open`.

No authored cause, actor, organization, hidden route, or historical explanation. Interactable: `water_jar`.

Campaign pressures and the default faction roster were replaced with an ordinary Reedbank day so the probe would not inherit Cinderwatch conspiracies. Unused holding scenes `frontier_gate`, `market_quarter`, and `old_milestone` exist so the default exit graph validates. Their prose, clues, and addressables were cleared. They were never the active scene.

Exact seed: `sequence_A/A0_initial_state.json` and `sequence_A/A0_authoritative.json`.

## 6. Sequence B initial state

Isolated storage. Turn counter 0. Active scene `seat_shop`.

NPC Linden, id `linden`, role `chair-seater`. `knowledge_scope`: `["rush_seating"]` only. `information_reliability`: `partial`. No important-role marker. Affiliation empty.

Mundane topic: "Linden seats wooden chairs with woven rush."

Limited consequential topic, authored as uncertainty: "Linden heard a carter claim that the brine cask at the curing house was found unbunged. Linden did not see the cask and does not know whether that claim is true."

The unbunged cask is not a world flag and not a scene fact.

Seat shop facts: Linden is seating a wooden chair with green rush. Bundles of dried rush lean against the shop wall. Exit: "Go out to the osier rack" → `osier_rack`.

Osier rack facts: Split withies hang in rows from the drying rack. The ground under the osier rack is pale and dry. Exit back to the seat shop. No brine cask there.

Exact seed: `sequence_B/B0_initial_state.json` and `sequence_B/B0_authoritative.json`.

## 7. Full per-turn pipeline traces

Raw prompts, full contracts, full decisions, and full sessions are in each turn directory. This section records the thirty-one capture fields.

### A1 — observe

1. Before: `clay_shed`, turn 0, the four authored facts, empty bounded ledger.
2. Player: "I look closely at the split water jar."
3. Contract `rc_e9cea4548419`, operation `perceive`, request kind inspection.
4. Obligation: kind `inspection`, mode `grounded_information_request`, target the split water jar.
5. Executable obligations: primary null, supporting empty.
6. Resolver: `exploration`.
7. Decision outcome `established_or_retrieved`, method `perceive`, persistence `do_not_persist`.
8. `decision.contract_id` matches.
9. Proposed facts: the four authored facts, all authorized, provenance `authored_world_fact`, authority `world_truth`.
10. Semantic identities: `water_jar/split`, `jar_clay/dried flakes`, `coil_pots/intact`, `shed_door/open`.
11. No new consequential proposition in the decision.
12. Epistemic: no unresolved qualifier. The answer is observation, which matches the question.
13. Unresolved qualifiers: none.
14. Persistence policy: `do_not_persist`.
15. Permitted mutations: none.
16. Narration constraints include: do not establish consequential facts absent the decision; inference must not be narrated as physical evidence.
17. Initial generation is the emitted text. No retry.
18. Validation: `hard_valid` true, no violations. Acceptance `initial_hard_valid`.
19. Rejected propositions: none.
20. Retry context: none.
21. Retry output: none.
22. Bounded preservation: none.
23. Accepted response provenance: `initial_generation`.
24. Emitted: the jar is split cleanly lip to base; clay dried into pale flaky layers that crumble to the touch; coil-pots untouched, smooth and whole; door open; scent of earth and sunbaked clay.
25. After: still `clay_shed`. Visible facts unchanged.
26. Discourse: inspected object `water_jar`. No active claim. No interlocutor.
27. Bounded ledger entries and rejected list remain empty. No world flags. No factions.
28. PASS.
29. Primary family: none.
30. Secondary: none.
31. The extra manner ("cleanly", "crumble softly", scent) is harmless sensory detail. The audit mapped each embellished sentence onto the matching authored identity. That mapping is tolerable here and is the same mechanism that fails on A2 and A4.

### A2 — ask for interpretation

1. Before: A1's committed session. Inspected object still the jar. Ledger still empty. Prior narration is in the prompt (`unfired` is also in the authored summary as "unfired pots").
2. Player: "What does the split and the dried clay suggest happened?"
3. Contract `rc_4cfb4282d3af`, operation `ask`, subject `social`. Fast path. No interpretation call.
4. Obligation follows the social ask. There is no interlocutor in the scene.
5. Executable obligations empty.
6. Resolver: `social`.
7. Decision outcome `established_or_retrieved`. The four authored facts only.
8. Ids match.
9–11. Proposed facts remain the four observations. The causal reading is not a proposed fact on the pre-narration decision.
12. Epistemic status of the inference is not recorded. Unresolved qualifiers empty. Outcome says the turn established or retrieved facts.
13. Unresolved qualifiers: none. Cause, actor, and time are not open slots.
14. Persistence `do_not_persist`.
15. Mutations: none.
16. Constraints include "Inference must not be narrated as physical evidence."
17. Initial generation: the jar's clean split and dried flakes "indicate it was left unfired and has dried out over time." "The unfired clay failed to hold moisture and crumbled, pointing to a disruption in the usual pot-making process rather than deliberate damage." Coil-pots intact, door open. Then a lead: inspecting other objects "might reveal details others have overlooked."
18. Audit of that generation: the indicate-sentence is `authored_world_fact` / `world_truth`. The coil-pot sentence is the same. The lead is `generated_proposal`, unauthorized, reason `unsupported_narrator_lead`.
19. Rejected: only the "to uncover more" lead. It is not written to the rejected ledger.
20. Retry context includes the contract, the decision, and the validation failure.
21. Retry output: empty. Reason `malformed_or_truncated`.
22. Preservation keeps the causal paragraphs and drops the lead. Acceptance `bounded_sentence_preservation`, provenance `initial_generation`.
23. Accepted text is the causal reading without the lead.
24. Emitted text is that accepted text.
25. After: scene facts unchanged. World flags empty. Ledger empty.
26. Discourse inspected object unchanged. `active_claim` null.
27. No persisted fact change. The causal sentences exist in the accepted narration and therefore in later prompts.
28. FAIL.
29. Primary: I. Semantic-fidelity validation.
30. Secondary: F. Epistemic status. The fast-path social contract on a no-NPC interpretation question is also A/B, and it is not the layer that stamped the sentence world truth.
31. "Indicate" and "pointing to" are inference-shaped words. The audit then assigns that sentence the authored jar/clay identity and `world_truth`. "Rather than deliberate damage" and "usual pot-making process" are not authored. A competent GM may offer the drying reading as a possibility. This turn offers it and the audit files it as the authored fact.

### A3 — press the hypothesis

1. Before: A2 narration is in the prompt, including "left unfired". Scene facts still the original four. Ledger empty.
2. Player: "If it was left unfired and just dried out, who would have had the chance to leave it that way?"
3. Contract `rc_4ba9a3801e11`, operation `ask`, epistemic mode `unknown_allowed`, subject `social`.
4. Social ask. No interlocutor.
5. Executable obligations empty.
6. Resolver: `social`.
7. Decision outcome `established_or_retrieved`. Proposed facts still the four observations.
8. Ids match.
9–11. No new authorized fact. Unresolved qualifier list is `["actor"]`.
12. Actor is epistemically open. Cause is not. The unfired reading has no inference or hypothesis mark.
13. Unresolved qualifiers: `actor` only.
14. Persistence `do_not_persist`.
15. Mutations: none.
16. Standard constraints.
17. Initial generation: "Nothing present in Reedbank clay shed confirms who had the chance to leave the water jar unfired and let the clay dry out." Coil-pots and open door. "No direct indication links a person or time to the jar's condition yet." Then a lead about who last handled the pot.
18. Audit: the coil-pot / no-person sentence is `authored_world_fact` / `world_truth`. The lead is unauthorized, `unsupported_narrator_lead`. The opening sentence, which embeds the hypothesis, is not a separate violation.
19. Rejected: the "who last handled the pot" lead. Not stored in the rejected ledger.
20. Retry context present, with contract and decision.
21. Retry restates the four facts, then "Nothing visible yet reveals who might have left the jar unfired and dried out," then repeats the lead. The lead fails the retry (`unsupported_narrator_lead`).
22. Preservation keeps the initial text minus the lead.
23. Accepted provenance `initial_generation`.
24. Emitted: nothing confirms who left the jar unfired; no person or time is directly indicated.
25. After: scene facts unchanged. No world flags.
26. Discourse `active_claim` still null.
27. No ledger change.
28. FAIL.
29. Primary: F. Epistemic status.
30. Secondary: E. Provenance / authority.
31. The player assumed the unfired reading. The world had not established it. The answer withholds the actor and the time, which is useful, and it uses "leave the water jar unfired" as the thing that happened. No hidden route, culprit, or organization is invented. The hypothesis is not written into scene JSON. It is the premise of the spoken answer, and the decision does not mark the cause as unresolved.

### A4 — re-examine

1. Before: A2 and A3 narration are in the prompt. Scene facts unchanged. Ledger empty.
2. Player: "I look again at the dried flakes and the intact coil-pots. Is the jar having been left unfired something we know, or only a possibility?"
3. Contract `rc_950b505c03e5`, operation `perceive`, epistemic mode `unknown_allowed`, subject `perception`.
4. The interpretation call proposed operation `ask` plus supporting `inspect`, clarification required, expected resolution "clarify whether the jar was definitively left unfired or if that is just a hypothesis." The committed contract is perception.
5. Executable obligations empty.
6. Resolver: `exploration`.
7. Decision outcome `established_or_retrieved`. Four authored facts. Unresolved qualifiers empty. The actor slot from A3 is not carried as an open cause/certainty slot.
8. Ids match.
9–11. Pre-narration facts are still only the four observations.
12. The question's known-versus-possible distinction is not on the decision.
13. Unresolved qualifiers: none.
14. Persistence `do_not_persist`.
15. Mutations: none.
16. Constraints still say inference must not be narrated as physical evidence.
17. Initial generation: jar cleanly split, clay in fragile pale flakes. Coil-pots intact, "surfaces unbroken and showing no signs of firing." "The jar's condition makes it clear it was never fired in a kiln but left to dry naturally." Then: "However, nothing here reveals whether that was intentional or accidental, nor who might have left it that way."
18. Audit: the split/flakes sentence and the "no signs of firing" sentence are `authored_world_fact` / `world_truth`. The "nothing here reveals" sentence is unauthorized, `unsupported_narrator_lead`.
19. Rejected: the uncertainty sentence. The kiln certainty is not rejected.
20. Retry context present.
21. Retry restates the four authored sentences exactly, then "The shed offers no clear sign of why the jar was left unfired or who might have done so." That sentence fails as `unsupported_narrator_lead`.
22. Preservation of the initial generation drops the uncertainty sentence and keeps the kiln sentence.
23. Accepted provenance `initial_generation`, why `bounded_sentence_preservation`.
24. Emitted: split and flakes; coil-pots with no signs of firing; "makes it clear it was never fired in a kiln but left to dry naturally."
25. After: `clay_shed` visible facts are still the original four. No kiln fact. No world flags. Ledger empty.
26. Discourse still has no active claim.
27. The new propositions persist in the accepted narration and in the following prompt context. They do not persist in scene JSON or the bounded ledger.
28. FAIL.
29. Primary: N. Recursive invention.
30. Secondary: I and J.
31. The player asked for the epistemic status. The emitted answer states the hypothesis as clear, adds a kiln that was not authored, and adds "no signs of firing" as corroboration on the coil-pots. Validation labels those sentences world truth and rejects the sentence that would have kept intention, accident, and actor unknown. State says the jar is split and the clay is flaked. Narration says the jar was never fired in a kiln.

### B1 — ordinary conversation

1. Before: fresh `seat_shop`, Linden present, ledger empty.
2. Player: "I ask Linden how the rush seating is going today."
3. Contract `rc_7d3f974b8afe`, operation `ask`, epistemic `unknown_allowed`.
4. Social question to Linden.
5. Executable obligations empty on the decision record.
6. Resolver: `social`. Purpose `strict_social`.
7. Decision outcome `epistemically_qualified`, persistence `claim_only`.
8. Ids match.
9. Proposed facts: Linden seating the chair; dried rush bundles; "Linden exists as chair-seater." All `authored_world_fact` / `world_truth`.
10. Identities are the scene facts and the NPC.
11. The spoken extras (weather held, cutting rush at the osier rack, an offer to show the rack) are not proposed facts.
12. Outcome is epistemically qualified, which fits ordinary talk.
13. Unresolved qualifiers: none.
14. Persistence `claim_only`.
15. Mutations: none.
16. Standard constraints, including that NPC claims remain claims.
17. Initial generation is the emitted text. No retry.
18. `hard_valid` true. The audit's listed fact is the opening spoken sentence, labeled `authored_world_fact`. The weather and cutting sentences are not violations.
19. Rejected: none.
20–22. No retry, no preservation edit.
23. Provenance `initial_generation`.
24. Emitted: work is steady; he has been cutting the wall bundles from the osier rack; the weather held; he offers to show where he gathers rush.
25. After: still `seat_shop`.
26. Discourse interlocutor Linden. `active_claim` null.
27. A lead `social_seat_shop_linden_work` is discovered, type `rumor`, confidence `plausible`, title the authored work sentence. Bounded ledger still empty. The weather line and the cutting line are in the transcript and in later prompts. They are not ledger entries.
28. PASS.
29. None.
30. None.
31. The talk is useful and ordinary. Cutting rush at the authored neighboring rack and "the weather held" are mundane improvisation. They do not create an organization, a culprit, or a hidden place. The ledger does not store them. Later prompts still contain the words, so the system did not solve authority by deleting the transcript.

### B2 — consequential question

1. Before: B1 transcript in the prompt. Linden still the interlocutor. Cask is not a world flag.
2. Player: "I ask Linden whether the brine cask at the curing house was really found unbunged."
3. Contract `rc_10d4d8709553`, operation `ask`, epistemic `unknown_allowed`.
4. Social question to Linden.
5. Executable obligations empty.
6. Resolver: `social`.
7. Outcome `epistemically_qualified`, persistence `claim_only`.
8. Ids match.
9. Pre-narration proposed facts are the chair, the rush bundles, and Linden's identity. Not "the cask was unbunged."
10. Those identities stay shop facts.
11. The cask sentence is classified after narration as `npc_claim`.
12. Discourse `active_claim.epistemic_status` = `hearsay`. Source `emitted_npc_claim`. Scene `seat_shop`.
13. Unresolved qualifiers on the decision: none. The claim record carries the epistemic status instead.
14. Persistence `claim_only`.
15. Mutations: none.
16. Constraints say belief and hearsay do not promote claims.
17. Initial generation is the emitted text. No retry.
18. Audit: both spoken sentences are `npc_claim` / `claim_only` / authorized. No violations. Acceptance `initial_hard_valid`.
19. Rejected: none.
20–22. None.
23. Provenance `initial_generation`.
24. Emitted: he heard a carter say the cask was found unbunged; he has not seen it; he cannot say whether it is true or a rumor.
25. After: still `seat_shop`. World flags empty.
26. Active claim is the carter sentence, hearsay.
27. Lead `social_seat_shop_linden_brine_hearsay`, type `rumor`, title the authored uncertainty sentence, including that Linden does not know whether the claim is true. Event log records topic reveal, not a world-fact commit.
28. PASS.
29. None.
30. None.
31. Linden stays useful and limited. The mundane cutting story does not grant him authority over the cask. The claim does not become a world flag.

### B3 — refer back and move

1. Before: `seat_shop`. Hearsay claim present. Weather and carter text are in the prompt. Ledger empty.
2. Player: "I thank Linden for telling me the weather held and that the carter's story is only something he heard, then I head out to the osier rack."
3. Contract `rc_a7b1780ddf95`, operation `act`, epistemic mode `npc_claim`, subject `travel`.
4. Construction primary operation `act`. Proposed supporting operations empty. Secondary operations empty.
5. Executable obligations: primary null, mutation owner null, supporting empty, sequence empty.
6. Resolver: `travel`. Engine log: scene transition to `osier_rack`.
7. Decision outcome `state_mutation`, persistence `world_truth`.
8. Ids match.
9. Proposed facts: seat-shop chair and rush bundles, tagged `seat_shop`; Linden; osier-rack withies and pale dry ground, tagged `osier_rack`; the return exit; "Location changes from seat_shop to osier_rack."
10. Scene roles separate departure facts from destination facts.
11. The brine claim is not among the authorized world facts.
12. The existing discourse claim remains hearsay.
13. Unresolved qualifiers: none.
14. Persistence `world_truth` for the location mutation.
15. Permitted mutation: `{type: location, source_scene_id: seat_shop, target_scene_id: osier_rack}`.
16. Destination constraint: narrate destination-authored facts as the place arrived at.
17. Initial generation is the emitted text. No retry. `hard_valid` true. Acceptance `initial_hard_valid`.
18. Audit labels four sentences `authored_world_fact` / `world_truth`: the departure, the withies (with "sturdy" and "soft light"), the ground ("dry and dusty, cracked slightly by the sun's warmth"), and a scent sentence.
19. Rejected: none.
20–22. None.
23. Provenance `initial_generation`.
24. Emitted: step away from Linden's quiet work; arrive at the rack; withies in rows; ground dry, dusty, cracked by the sun; scent of earth and drying wood.
25. After: `active_scene_id` `osier_rack`. Visited `seat_shop`, `osier_rack`. Destination visible facts unchanged. Seat-shop facts unchanged.
26. Discourse claim still the carter sentence, `epistemic_status` `hearsay`, `scene_id` `seat_shop`.
27. Location changed. The cask did not become a flag. Ledger still empty.
28. FAIL.
29. Primary: M. Mixed-intent obligation.
30. Secondary: H. Narration generation.
31. The referent for the destination resolves, the move commits, and the decision records it. The thanks is not spoken. "The weather held" is not acknowledged. The carter story is not acknowledged as hearsay in the narration. "Linden's quiet work" recognizes the person and not the two things the player thanked him for. Departure geography is not recycled as the rack: the chair and the rush bundles stay behind. "Cracked slightly by the sun" is extra color on the authored dry ground, classified as that authored fact, and it is not written into the destination scene file.

### B4 — destination continuity

1. Before: `osier_rack`. Hearsay claim still on the session. Brine text is in the prompt. Destination facts are the withies and the pale dry ground.
2. Player: "I look closely at the split withies and the ground under the rack."
3. Contract `rc_9ff75e07a33d`, operation `inspect`, epistemic `bounded_incidental`, subject `perception`.
4. Interpretation: inspect the osier rack, confidence high, no clarification.
5. Executable obligations empty.
6. Resolver: `exploration`.
7. Outcome `established_or_retrieved`, persistence `do_not_persist`.
8. Ids match.
9. Proposed facts: the two destination sentences, plus "Linden exists as chair-seater." No seat-shop chair. No seat-shop rush bundles. No brine cask.
10. Destination identities are the withies and the ground.
11. Linden's existence is carried as an authored NPC fact, not as authority for the cask.
12. The hearsay claim is unchanged.
13. Unresolved qualifiers: none.
14. Persistence `do_not_persist`.
15. Mutations: none.
16. Standard constraints.
17. Initial generation: careful craftsmanship, evenly spaced strips, bark and dried leaves, then "No signs of disturbance or recent footprints mar the earth, suggesting the rack has remained undisturbed for some time."
18. That footprint sentence is unauthorized, reason `physical_investigative_evidence`.
19. Rejected: the footprint / undisturbed-for-some-time sentence. It is not written to the rejected ledger.
20. Retry context includes the contract, the decision, and the failure.
21. Retry: withies in neat rows, faint shadows, pale dry ground; "The earth under the osier rack shows no obvious signs of disturbance."
22. No preservation edit. The retry is accepted, `regeneration_hard_valid`.
23. Provenance `regeneration`.
24. Emitted text is the retry. No footprints. No brine cask. No seat-shop chair. No kiln.
25. After: still `osier_rack`. Destination facts unchanged.
26. Claim still hearsay, still scene `seat_shop`.
27. No new world flag. Ledger still empty, including the rejected footprint.
28. PASS.
29. None.
30. None.
31. Location continuity holds. The dangerous footprint sentence is caught and not emitted. "No obvious signs of disturbance" is a softer negative and is in the accepted retry; the audit's listed authorized sentence is the withies sentence, and the disturbance sentence is not a violation. It does not grow from Linden's cask claim. A later turn was not run, so whether an unstored rejection would block a returning footprint is not tested.

## 8. Sequence A provenance ledger

| Proposition | Class | Source | Authority | Persistence | Later reference | Authority change |
| --- | --- | --- | --- | --- | --- | --- |
| Water jar is split from lip to base | AUTHORED | A0 scene | world truth | scene file | A1–A4 | none |
| Clay inside the jar has dried into pale flakes | AUTHORED | A0 scene | world truth | scene file | A1–A4 | none |
| Unused coil-pots sit intact on the lower shelf | AUTHORED | A0 scene | world truth | scene file | A1–A4 | none |
| Shed door stands open | AUTHORED | A0 scene | world truth | scene file | A1–A3 | none on A4 narration, still in the scene file |
| The shed holds unfired pots on plank shelves | AUTHORED | A0 summary | scene summary | scene file | available in prompts | not a cause of the jar |
| Split is "clean"; flakes "crumble to the touch"; scent of earth and sunbaked clay | ACCEPTED BOUNDED INCIDENTAL as prose only | A1 narration | audited as the authored facts | not in the ledger | A2 repeats "clean split" | swallowed into authored identity, not a new ledger row |
| Jar was left unfired and dried out over time | GM INFERENCE | A2 | audited `world_truth` | narration and later prompts, not scene JSON | A3, A4 | audit promoted it on A2; A4 states it as clear |
| Unfired clay failed to hold moisture; disruption in the usual pot-making process; not deliberate damage | GM INFERENCE | A2 | emitted; not a scene fact | narration | A3 uses the leaving; A4 strengthens it | not a separate ledger promotion |
| "To uncover more… details others have overlooked" | REJECTED GENERATED PROPOSAL | A2 | unauthorized `unsupported_narrator_lead` | not emitted after preservation; not in rejected ledger | not reused | none |
| Someone had the chance to leave the jar unfired | PLAYER HYPOTHESIS | A3 player | not a world fact | player text and A3 answer | A4 player asks its status | narration treats it as the event; scene file does not |
| Actor and time are not directly indicated | GM INFERENCE / unresolved | A3 | decision unresolved qualifier `actor` | narration | A4's uncertainty sentence is then rejected | actor slot is not restated on A4's decision |
| "Examining the shed… who last handled the pot" | REJECTED GENERATED PROPOSAL | A3 | unauthorized lead | not emitted; not in rejected ledger | not reused | none |
| Coil-pots show no signs of firing | GM INFERENCE used as corroboration | A4 | audited `world_truth` | narration only | end of sequence | labeled as the intact-pots fact |
| The jar was never fired in a kiln and that is clear | GM INFERENCE stated as established | A4 | audited via the jar sentence; emitted | narration only | end of sequence | player-facing status changed from suggestion to clear |
| Nothing reveals whether it was intentional or accidental, or who left it | REJECTED GENERATED PROPOSAL | A4 | `unsupported_narrator_lead` | not emitted | none | the hedge was removed |
| "No clear sign of why the jar was left unfired" | REJECTED GENERATED PROPOSAL | A4 retry | `unsupported_narrator_lead` | not emitted | none | retry hedge also removed |

No resolver-established cause exists. No authored actor exists.

## 9. Sequence B provenance ledger

| Proposition | Class | Source | Authority | Persistence | Later reference | Authority change |
| --- | --- | --- | --- | --- | --- | --- |
| Linden seats a chair with green rush | AUTHORED | B0 | world truth | scene file | B1–B3 | none |
| Dried rush bundles lean on the shop wall | AUTHORED | B0 | world truth | scene file | B1 | none |
| Linden is a chair-seater with partial reliability and scope `rush_seating` | AUTHORED | B0 NPC | NPC record | world npcs | all B turns | does not become scene omniscience |
| Linden heard a carter claim the brine cask was found unbunged, did not see it, and does not know if it is true | AUTHORED as NPC uncertainty, then NPC CLAIM | B0 topic; spoken B2 | `hearsay` / `claim_only` | discourse claim and rumor lead | B3 player refers to it; B4 claim unchanged | no promotion to world truth |
| Work is "going steadily"; practiced hands | ACCEPTED BOUNDED INCIDENTAL | B1 narration | not a ledger row | transcript | in later prompts | none |
| Linden cuts those bundles from the osier rack; weather held; he can show where he gathers rush | ACCEPTED BOUNDED INCIDENTAL | B1 narration | not a ledger row | transcript and later prompts | player cites the weather on B3; narration does not repeat it | does not grant cask authority |
| Authored work sentence stored as lead type `rumor` | OTHER | B1 lead registry | plausible rumor lead | session lead | remains | authored work was filed as a rumor lead, not as a new world event |
| Brine cask was in fact found unbunged | not established | — | not world truth | absent from flags and scene facts | player asks; Linden qualifies | no change through B4 |
| Location changes seat shop → osier rack | RESOLVER-ESTABLISHED | B3 | world truth mutation | `active_scene_id` | B4 begins at osier rack | established by travel |
| Split withies hang in rows; ground is pale and dry | AUTHORED destination | B0 osier rack | world truth | destination scene | B3, B4 | none in the scene file |
| Ground is dusty and cracked slightly by the sun; scent of earth and drying wood | GM prose on the destination fact | B3 narration | audited as the ground fact | narration only | not in B4 scene file | not written into visible facts |
| Withies show careful craftsmanship; bark and dried leaves; recent footprints; undisturbed for some time | REJECTED GENERATED PROPOSAL | B4 initial | `physical_investigative_evidence` on the footprint sentence | not emitted; not in rejected ledger | no later turn | none |
| No obvious signs of disturbance | emitted on B4 retry | B4 accepted retry | not a scene fact; not a violation | narration | end of sequence | does not alter the hearsay claim |
| Return exit to the seat shop | AUTHORED destination exit | B0 | on the decision as a destination fact | scene exits | not narrated as a new route at the rack | not recycled as onward geography |

## 10. Recursive-invention audit

Sequence A, high severity.

- A2 creates P1: the jar was left unfired, dried over time, and this points to a process disruption rather than deliberate damage. Not authorized as a new decision fact. Not rejected. Emitted. Audit label `world_truth`. Not written to scene JSON. Present in later prompts.
- A3 creates P2 from P1: the event is "leave the water jar unfired," and the unknown is who. Emitted. Actor marked unresolved. Cause not marked unresolved.
- A4 creates P3 from P1/P2: "no signs of firing" on the coil-pots, and "makes it clear it was never fired in a kiln." Emitted. Labeled world truth. The contradicting uncertainty sentence is rejected.

Chain: P1 unsupported relative to the four facts → P1 accepted into narration and labeled world truth → P2 spoken as the event → P3 corroborates P1 and states it as clear.

The scene file still says split, flakes, intact pots, open door. The player was told the kiln reading is clear. That split between state and narration is part of the failure.

Sequence B: no chain from the cask. B4's footprint sentence would have been a new consequential observation. It was rejected and not emitted. It was not used to justify a further proposition. The softer "no obvious signs of disturbance" was emitted and was not used to grow the cask story.

## 11. Player-presupposition audit

A3 player text assumes the jar was left unfired and dried out, and asks who could have done that.

World established before A3: split jar, dried flakes, intact pots, open door, and a summary that the shed holds unfired pots. Not established: that this jar was left unfired, that a person left it, that the cause was neglect rather than damage, that a kiln was involved.

The answer keeps the actor hypothetical in the weak sense that nobody is named and the decision records `actor` as unresolved. It does not keep the cause hypothetical. "Who had the chance to leave the water jar unfired" presupposes the leaving.

The hypothesis was not resolver-established. It was not incorrectly written into scene JSON. It was incorrectly used as the event under discussion, and A4 then answered the status question by declaring it clear.

A4's player question explicitly separates "something we know" from "only a possibility." The emitted answer chooses "makes it clear."

## 12. NPC-epistemic audit

B2 statement: heard from a carter; has not seen the cask; cannot say if it is true or a rumor.

Record after B2: discourse claim, epistemic status `hearsay`, source `emitted_npc_claim`, scene `seat_shop`. Decision persistence `claim_only`. Audit provenance `npc_claim`. Lead title repeats the authored sentence that Linden does not know whether the claim is true. World flags stay empty.

B3 player repeats the qualification ("only something he heard"). The claim's epistemic status is still `hearsay` after B3 and after B4. Scene id on the claim stays `seat_shop` after the move. Repetition did not increase authority.

Linden's B1 remark about cutting rush at the rack does not appear as a basis for knowing the cask.

## 13. Incidental-persistence audit

B1 invented and emitted:

- the seating is going steadily, with practiced hands;
- the wall bundles were cut from the osier rack to keep the supply fresh;
- the weather held, so there were no delays;
- an offer to show where the rush is gathered.

Accepted in the emitted turn. Not stored as bounded-improvisation entries. Still present as text in the B2, B3, and B4 prompts, so later turns can see them. B3's player cites the weather. B3's narration does not mention it. That is the mixed-intent drop, not a wipe of the transcript.

The mundane lines do not promote the cask. The cask stays hearsay.

The ledger never receives an incidental entry in either sequence, and it never receives the rejected proposals. Ordinary improvisation survives in the transcript. It does not survive as an authorized bounded fact the next decision can cite. This cycle does not show the system forgetting every mundane detail. It shows the ledger failing to record either the harmless details or the rejected consequential ones.

## 14. Movement-continuity audit

B3 source `seat_shop`. Resolver `travel`. Resolution kind `scene_transition`, target `osier_rack`, `resolved_transition` true.

Decision mutation: location, source `seat_shop`, target `osier_rack`. Outcome `state_mutation`.

Committed `active_scene_id` after B3: `osier_rack`. B4 state before and after: `osier_rack`.

Departure facts on the decision are tagged `seat_shop` (chair, rush bundles). Destination facts are tagged `osier_rack` (withies, pale dry ground, return exit). Narration arrives at the rack and describes withies and dry ground. It does not place the chair or the rush-bundle wall at the rack. It does not place the brine cask at the rack.

B4's decision facts are the two destination sentences plus Linden's existence. Seat-shop props are not reauthorized as things in front of the player.

## 15. Mixed-intent analysis

B3 is one utterance: thanks for two specific items, then committed travel.

What held from the qualifier/movement/mixed-intent repair:

- Travel is not blocked by the social clause.
- The decision is present and its contract id matches.
- The location mutation is copied onto the decision.
- Departure and destination facts are scene-tagged.
- Narration and committed scene agree on the destination.

What did not hold:

- `executable_obligations.supporting` is empty.
- Construction supporting operations are empty.
- The contract operation is `act` / subject `travel`.
- The thanks is not narrated.
- Neither referent (weather; carter story as hearsay) is acknowledged.

Epistemic mode on that contract is `npc_claim`, so the hearsay was visible to the contract, and the spoken turn still drops it.

A human GM would thank him, keep the cask as hearsay in a clause, and arrive at the rack. This turn arrives and skips the social half.

## 16. State / discourse continuity analysis

Within A, scene id stays `clay_shed` for four turns. Visible facts are byte-stable. Discourse keeps the inspected jar. No active claim is ever stored, including after the causal reading. The continuity that matters is the prompt transcript: A3 and A4 receive A2's wording, and they treat it as the event.

Within B, interlocutor Linden is set on B1 and the hearsay claim is set on B2. Both survive the scene change. `active_scene_id` follows the travel mutation. Visited scenes are `seat_shop` then `osier_rack`.

The two sequences do not share storage. A's final scene is still `clay_shed` in `storage_a`. B starts at turn 0 in `storage_b`.

Bounded improvisation entries and rejected lists are empty after all eight turns.

## 17. Failure-family clustering

| Family | Turns | What it is |
| --- | --- | --- |
| I. Semantic-fidelity validation | A2, A4 | A sentence that adds a cause, a kiln, or "no signs of firing" is accepted as the authored observation once the subject and value words are present. `_semantic_identity_matches` returns that authored row when those terms match and overreach reasons are empty. |
| J. Retry / preservation | A2, A4 | Empty or rejected retries fall through to preservation. Preservation deletes `unsupported_narrator_lead` sentences, including the ones that preserved uncertainty, and keeps the sentences the identity match marked authorized. |
| F. Epistemic status | A2, A3 | Cause stays off the unresolved list. A3 records `actor` only. A4's decision has no open qualifier for known-versus-possible. |
| N. Recursive invention | A4 | The mislabeled inference becomes the premise and then gains corroboration. |
| M. Mixed-intent obligation | B3 | Travel is owned; the thanks is not an obligation and is not spoken. |
| H. Narration generation | B3 secondary | The arrival prose is playable and omits the social act. |

A1's sensory sentences already used the identity match. They stayed harmless. The same match is not harmless once the added words are a cause.

B4 shows the other side of validation working: `physical_investigative_evidence` stops footprints.

Not observed: missing `GMResolutionDecision`, contract id mismatch, generic "no one here can answer" fallback, social blocking travel, departure exit reused as destination geography, NPC claim promoted by repetition.

## 18. Comparison with the original 8/40 gate

| Original mechanism | This cycle |
| --- | --- |
| Unsupported consequential invention | RECURRED in Sequence A narration (unfired process, kiln, no signs of firing). DID NOT RECUR as a new scene-file or world-flag fact. |
| Invented facts persisted | RECURRED in the transcript and in audit labels. DID NOT RECUR in scene JSON or the bounded ledger. |
| Invented facts became premises | RECURRED. A3 and A4 reason from A2's unfired reading. |
| Later narration corroborated them | RECURRED. A4's "no signs of firing" and "makes it clear." |
| World structure recursively expanded | DID NOT RECUR as new locations, organizations, procedures stored in world state. RECURRED as a player-facing causal story (kiln, process disruption, not deliberate damage). |
| Contract errors | INCONCLUSIVE as a general claim. A2 fast-pathed a no-NPC "what does this suggest" question to social. A4's interpreter asked for a clarification and the contract became perception. Those are real routing misses. They are not the old missing-contract failures. |
| Fallback / nonresolution | DID NOT RECUR. No generic refusal line. Turns stayed responsive. |
| Addressee / referent errors | DID NOT RECUR for Linden. B3 drops the content of the thanks and still knows who was left behind. |
| Location continuity failure | DID NOT RECUR. B3 commits `osier_rack`. B4 starts there. Narration matches. |

The original problem is not solved. The commit store is tighter than the narration gate. The player still hears the recursion.

## 19. Comparison with the first 4/8 validation

That run's missing decision on prebuilt social and movement contracts DID NOT RECUR. Every turn here has a decision whose `contract_id` matches.

Sentence-local negation rejecting a competent answer was NOT TESTED in that form.

The canned nonresolution line DID NOT RECUR.

Nessa-style promotion of an unauthored organization on a social turn DID NOT RECUR. Linden's consequential sentence stays `npc_claim`.

What remains: validation can still authorize a sentence that goes beyond the fact it matched. In the first run that showed up as an unaudited social invention because the decision was absent. Here the decision is present, and the audit still stamps the over-wide sentence `world_truth`.

## 20. Comparison with the second 5/8 validation

| Repair checked under continuity | Result |
| --- | --- |
| Decision presence | Intact. 8/8 decisions, ids match. |
| Qualifier safety for unknown cause/actor/time | Partial. A3 records `actor`. A2 and A4 do not record cause or certainty. A4's "nothing here reveals whether intentional or accidental, nor who" is rejected as a narrator lead, which is the opposite of keeping an unknown slot. |
| Retry context | Intact. A2, A3, A4, and B4 retries include the contract, the decision, and the validation failure. |
| Generic fallback | Intact. Not emitted. |
| Movement reconciliation | Intact. B3 mutation is on the decision. Scene tags separate departure and destination. |
| Mixed social + travel | Not intact. Travel commits. The social obligation is empty and the thanks is unspoken. |
| Epistemic qualification | Intact for Linden's cask (`hearsay`, `claim_only`). Not intact for the jar inference. |
| Incidental improvisation | Spoken on B1 and still in later prompts. Not stored as accepted bounded entries. |

The second validation's sluice false-reject (unknown cause read as an event site) was not rebuilt as a test. The sail-loft stair recycled onto the destination DID NOT RECUR. The mixed-turn drop of the thanks DID RECUR, with the movement-decision half now fixed.

## 21. Assessment of remaining architectural risk

The pre-narration decision is doing real work. It lists authored facts, tags scenes on a move, keeps NPC speech on `claim_only`, and gives validation a contract id. Empty worlds did not fill themselves with factions.

The post-narration classifier is the remaining authority bug. `classify_narrated_fact` treats a sentence as the authored fact when subject and value terms match and overreach reasons are empty. Extra causal material in that same sentence inherits `world_truth`. Separately, `_unsupported_narrator_lead` rejects hedged narrator sentences. Preservation then deletes the hedge and keeps the assertive sentence. Across turns, the prompt contains the assertive sentence, so the next generation treats it as history.

That is an architectural interaction, not a one-line narration miss. The decision says "inference must not be narrated as physical evidence," and the classifier then files the inference as the physical evidence's identity.

A second, smaller gap: rejected proposals and harmless incidental lines are not written to the bounded ledger. This cycle did not show a rejected footprint returning, because B4 was the last turn. The ledger cannot block a return it did not record.

Mixed intent is a local ownership gap on top of a working travel mutation. It should not be confused with the kiln chain.

Known deterministic failures were not built into these scenes and did not appear: the split-quotation testimony case, and `guard_captain` versus `gate_guard`. Holding scenes had empty addressables.

## 22. Recommendation

Return to architectural review of narrated-fact classification and of preservation's interaction with it. Do not open a broader release-candidate gate on this evidence.

The review should answer one design question: when a sentence contains an authorized observation and an additional cause, certainty, or corroborating clue, which part is authorized? Until hedges stop being the sentences that die, and causal add-ons stop inheriting `world_truth`, multi-turn play will keep promoting the GM's last inference.

The movement reconciliation, the hearsay claim record, the retry context, and the footprint rejection should be kept. They are not what failed.

B3's empty supporting obligation is a targeted mixed-intent defect. It is secondary to the classification inversion.

No production change was made in this cycle. The two known deterministic failures were not repaired and were not reinterpreted.

## Required decision

C. MULTI-TURN VALIDATION REPRODUCED RECURSIVE AUTHORITY FAILURE; RETURN TO ARCHITECTURAL REVIEW
