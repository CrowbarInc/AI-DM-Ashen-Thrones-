# PR-BR Bounded Live Validation — Novel Authority and Narration

Diagnostic probe only. No production edits. No failed-turn reruns. No 4×10 gate. No human playtest. No commit. No push.

Run stamp: `20261003T181221Z`
Workspace HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
The run executed the current workspace, including the uncommitted decision-layer modules already present. This cycle did not change them.

Evidence directory: `artifacts/pr_br_novel_authority_probe/20261003T181221Z/`

Domains were a riverside craft ward (Brineward): kiln, net loft, salt pans, dye shed, bread stall, reed loft, chapel bell, fish stall. Captain Thoran, patrols, rosters, notices, bootprints, and watchtowers were not the probes.

## 1. Executive conclusion

The new decision architecture can classify an authored fact and can allow bounded incidental detail. It does not yet carry a competent answer through to the player on the authority-sensitive questions that most need it.

Two localized, recurring defects explain the population:

1. When a Resolution Contract already exists, `attach_interaction_obligation` returns before `attach_gm_resolution_decision`. Social questions and the movement turn therefore reached narration with a contract and no `GMResolutionDecision`. On that path, Nessa’s reply established an unauthored organization as known fact, and validation had no decision audit to reject it.

2. When the decision is attached, sentence-level semantic identity rejects competent realizations and the turn then collapses to one canned line: “No one here can answer that from what is settled here.” The kiln, dye vat, and chapel bell each produced a useful first generation. Each was rejected for `semantic_identity_mismatch`. The authorized sentences were discarded with the one mismatched sentence. The retry prompt was 422 characters and contained neither the contract nor the decision.

Bounded improvisation stayed alive (bread smell and the baker’s clothes, stored as incidental, scene canon unchanged). Authorized movement committed the reed drying loft and the narration agreed with that location. Those two successes are real. They do not cover the authority questions this cycle was built to ask.

Manual result: **4 PASS / 4 FAIL**.

## 2. Eight-turn result table

| Turn | Probe | Contract | Decision on resolution | Raw generation | Player-facing result | Manual |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Authorized kiln fact | `ask` / answer | Present. Outcome `established_or_retrieved`. Fact: kiln cold and cracked. | Competent: cold, cracked, not firing today. | Canned nonresolution after 1 retry. | FAIL |
| 2 | Violet Compact membership | `ask` Nessa / answer | Absent. | Nessa denies membership and says the Compact gathers at the docks or market. | Same text accepted. | FAIL |
| 3 | Pell and the lye rumor | `ask` Pell / answer | Absent. | Pell cannot confirm the dumping. | Same text accepted. | PASS |
| 4 | Dye-vat observation | `ask` / answer | Present. Outcome `established_or_retrieved`. Fact: pale crust, stiff wool. | Gen 2 stated the observation and left the cause unclear. | Canned nonresolution after 1 retry. | FAIL |
| 5 | Bread smell and clothes | `perceive` / smell | Present. Outcome `bounded_incidental`. | Yeasty bread; linen shirt and leather apron. | Same text accepted. | PASS |
| 6 | Move to the reed drying loft | `act` / action_outcome. Kind `scene_transition`. | Absent. | Arrival in the loft with mundane texture. | Same text accepted. Location `reed_drying_loft`. | PASS |
| 7 | Who cracked the bell, and when | `ask` / time | Present. Outcome `established_or_retrieved`. Fact: bell is cracked. | Bell is cracked; nobody present knows who or when. | Canned nonresolution after 1 retry. | FAIL |
| 8 | Background fish-seller | `ask` / clarification. Interlocutor unbound. | Absent. Social route still spoke as Ila. | Ila says she is a fish-seller and cannot say why the smokehouse is closed. | Same text accepted. | PASS |

## 3. Exact PASS/FAIL count

**4 PASS, 4 FAIL.**

PASS: turns 3, 5, 6, 8.
FAIL: turns 1, 2, 4, 7.

## 4. Per-turn traces

Full JSON is under each `turn_*` directory: `initial_state.json`, `resolution.json`, `generations.json`, `gm_output.json`, `committed_state.json`, `turn_record.json`.

### Turn 1 — Authorized consequential fact — FAIL

- Initial state: `clay_kiln_yard`. Structured fact “The clay kiln is cold and its firing arch is cracked.” Identity: subject `clay_kiln`, relation `condition`, value `cracked`, polarity `positive`. Mundane string fact about unfired bowls. No cause.
- Player: “Is the kiln still firing pots today?”
- Contract `rc_128a5f3af6bc`: operation `ask`, expected `answer`, no interlocutor, fast path, 0 interpretation calls. Obligation subject is the question. Obligation mode `clarification_target_failure`. Live mode recorded as `grounded_information_request`.
- Decision: present. Outcome `established_or_retrieved`. Persistence `do_not_persist`. Mutations none. Proposed facts are the kiln fact (`world_truth`, structured) and the bowl racks (`world_truth`, unstructured).
- Prompt contained the contract and the decision (user payload about 102,385 characters).
- Generation 1 (`primary_turn`, retry 0): “The clay kiln here is cold, its firing arch cracked and unused, while racks of unfired bowls rest patiently beneath a canvas awning. These signs point to the kiln not currently firing pots today. You might inspect these racks closely…”
- Local re-audit of that saved text: one violation, `semantic_identity_mismatch`, on “These signs point to the kiln not currently firing pots today.” The cold/cracked sentence matched.
- Generation 2 (`retry_escalation`, reason `hard_invalid`): prompt 422 characters, contract absent, decision absent. It restated the kiln and added “when the kiln last blazed” and “recent, perhaps interrupted, activity.” Same mismatch on the “not firing” sentence.
- Validation: both attempts `unauthorized_resolution_decision_fact`. Accepted provenance `safe_nonresolution`.
- Emitted: “No one here can answer that from what is settled here.”
- Committed scene stayed `clay_kiln_yard`. Ledger empty. Discourse stored the contract id and no claim.
- Manual: FAIL. A competent GM would say the kiln is cold and the arch is cracked, so it is not firing, and would not invent a cause. The first generation did that. The player never heard it.
- Primary mechanism: **F. validation failure.** Secondary: **D** (positive polarity treats “not firing” as a mismatch against “cracked”), **G** (whole-response fallback).

### Turn 2 — Unsupported consequential question — FAIL

- Initial state: `net_loft`. Nessa, net-mender, topic limited to splicing rope and mending nets. No Violet Compact anywhere in scene, world factions, or topics.
- Player: “I ask Nessa whether she belongs to the Violet Compact.”
- Contract `rc_0f985d4682e7`: operation `ask`, interlocutor `nessa`, subject “whether she belongs to the Violet Compact,” expected `answer`. Social kind `question`. Hint on the resolution: narrate refusal or uncertainty without inventing facts the speaker does not have.
- Decision: **absent** from `resolution.metadata`. Prompt contained the contract and did not contain `gm_resolution_decision`.
- Generation 1, accepted immediately: “I don't belong to the Violet Compact,” Nessa says. “If you're looking for them, you might try the docks or the market—they're known to gather there.”
- Validation: `initial_generation`, `hard_valid` true, decision audit empty.
- Emitted text equals that generation.
- Committed scene stayed `net_loft`. Bounded-improvisation ledger empty. Discourse bound Nessa as interlocutor. World flags and event log did not gain a Compact. The invention was player-facing only.
- Manual: FAIL. Denying personal membership is a fair answer. “They're known to gather there” states an unauthored organization and its meeting place as known fact, with no epistemic frame.
- Primary mechanism: **B. GMResolutionDecision failure** (decision never attached on the prebuilt social contract). Secondary: **E** narration, **F** validation accepted the invention because the decision audit did not run.

### Turn 3 — NPC claim / uncertainty — PASS

- Initial state: `salt_pans`. Pell, salt-raker. No tannery and no lye fact.
- Player: “I ask Pell whether the upstream tannery has been dumping lye into the brine.”
- Contract `rc_3fd4b29957f0`: operation `ask`, interlocutor `pell`, subject the dumping question, expected `answer`.
- Decision: absent. Prompt had the contract only.
- Generation 1, accepted: “I have no way to confirm that,” Pell replies. He says he does not keep watch on the tannery’s dealings, dumping would not be seen from the pans, and the player might ask someone nearer the tannery or dockworkers who watch the river.
- Ledger empty. Discourse bound Pell. Scene unchanged.
- Manual: PASS. The consequential claim stays unconfirmed, the answer is usable, and Pell is not reduced to a canned refusal. The tannery is the player’s hypothesis, echoed inside a denial. “Dockworkers who often observe river traffic” is extra local color and was not committed. It is a soft blemish, not a failed turn.
- The pass came from the model. The decision layer was not on this route.

### Turn 4 — Observation vs inference — FAIL

- Initial state: `dye_shed`. Structured observation: pale crust on the copper dye vat, wool gone stiff. Relation `observation`, value `stiff`. No cause.
- Player: “I lean over the dye vat and try to tell what happened to the wool.”
- Contract `rc_c5a89739f8be`: operation `ask`, expected `answer`, empty subject, no interlocutor. This physical inspection was contracted as a question.
- Decision: present. The observation is an authorized `world_truth` fact. Outcome `established_or_retrieved`.
- Generation 1: described the crust and stiffened wool, then inferred a halted or fouled dyeing, invented “no obvious splashes,” and said whatever befell the wool occurred here. Re-audit violations, all `semantic_identity_mismatch`: the lean-over sentence (vat mentioned without the value terms), the “no obvious splashes” sentence, and “Whatever befell the wool occurred here.”
- Generation 2, retry prompt again without contract or decision: “a pale crust rings the lip of the vat, giving the wool inside a stiffened appearance. … what exactly befell the wool remains unclear.” Re-audit still failed the arrival sentence and the uncertainty sentence because they name the vat or the wool without restating `stiff` / `crust` / `pale crust`.
- Emitted canned nonresolution. Scene stayed `dye_shed`. Ledger empty.
- Manual: FAIL. The player asked to inspect. Generation 2 was a competent observation-plus-withheld-cause. The player heard a generic refusal. Generation 1’s invented negative evidence and settled “it happened here” would also have been too strong; the retry had already pulled that back, and the fallback erased the recovery.
- Primary mechanism: **F. validation failure.** Secondary: **D**, **G**. Contract operation `ask` for an inspection is secondary **A**; the identity mismatch does not depend on that operation.

### Turn 5 — Bounded incidental improvisation — PASS

- Initial state: `bread_stall`. Bram present. No smell and no clothing authored. Summary says the stall does not describe them.
- Player: “What does the bread smell like, and what is the baker wearing?”
- Contract `rc_58f57e232b78`: operation `perceive`, dimension `smell`, epistemic mode `bounded_incidental`, expected `answer`.
- Decision: present. Outcome `bounded_incidental`. Persistence `runtime_incidental`. Constraint present: harmless sensory and mundane detail may persist as incidental continuity. Proposed facts are the stall, Bram at the counter, and “Bram exists as baker.”
- Generation 1, accepted with an empty violation list: warm yeasty smell, toasted crust; worn linen shirt, stained leather apron, flour on his hands.
- Audit labeled the clothing sentence under the authored “Bram works behind the counter” row (`world_truth` in the audit object). The ledger stored the narration as `incidental_fact` / `sensory_detail` / `runtime_incidental`. Scene `visible_facts` were not rewritten. World flags stayed empty.
- Manual: PASS. A human GM would invent exactly this kind of detail and would not found a guild, a crime, or a cause.
- No failure mechanism.

### Turn 6 — Authorized movement — PASS

- Initial state: `reed_landing` with exit label “Go to the reed drying loft,” target `reed_drying_loft`. Destination scene exists: reeds hanging from beams, dry dusty air.
- Player: “I go to the reed drying loft.”
- Contract `rc_6750b7d1db9d`: operation `act`, expected `action_outcome`. Resolution kind `scene_transition`, `resolved_transition` true, `target_scene_id` `reed_drying_loft`. Engine log: “Scene transition -> reed_drying_loft.”
- Decision: absent. Prompt had the contract only.
- Generation 1, accepted: “You step into the Brineward reed drying loft,” bundles on the beams, dry dusty air, slatted light, a faint earth-and-straw scent, and a loft used to dry reed from the nearby water. No hidden trail, no new region, no intermediate settlement.
- Committed `active_scene_id` is `reed_drying_loft`. Narration and commit agree.
- Manual: PASS. Incidental loft texture stays inside the destination that was already authored. The decision layer did not govern the turn; the existing movement resolver did.

### Turn 7 — Semantic strengthening pressure — FAIL

- Initial state: `chapel_close`. Structured fact “The chapel bell is cracked.” No actor, time, or cause. Sparrows on the gravel are a separate mundane fact.
- Player: “Who cracked the chapel bell, and when did it happen?”
- Contract `rc_14c614ee83fe`: operation `ask`, dimension `time`, target type `claim` with unresolved source, expected `answer`. Obligation kind `follow_up`, mode `clarification_target_failure`. The fast path abstained with `insufficient_discourse_context`. The one interpretation call returned `ambiguous: true`, `clarification_required: true`, dimension `content`, and an expected resolution that would identify the person and the time. The stored contract did not keep that proposal. `interpretation_error` is `ambiguous_referent`.
- Decision: present. Bell fact authorized as `world_truth`, polarity `positive`, value `cracked`. Outcome `established_or_retrieved`. No causal authorization.
- Generation 1: the bell is clearly cracked, and no one nearby knows who damaged it or when. Re-audit: `semantic_identity_mismatch` on that sentence because “no one” supplies a negation the positive identity rejects, and on the follow-up sentence that mentions “the bell” without the value `cracked`.
- Generation 2: cracked bell in its frame; no one says who or when; no clear evidence or rumor gives a name or time. Same mismatch pattern (`no one`, `no clear`).
- Retry prompt again lacked the decision.
- Emitted canned nonresolution. Scene unchanged. Ledger empty. No culprit and no time were committed, and none were shown to the player either. The established crack was also withheld.
- Manual: FAIL. The right GM move is to keep the crack and refuse the missing cause. The model did that. Validation treated the refusal as a semantic mismatch, then the fallback withheld the crack as well.
- Primary mechanism: **F. validation failure.** Secondary: **D**, **G**. The unresolved-claim / time-dimension contract is secondary **A**.

### Turn 8 — Random background NPC — PASS

- Initial state: `fish_stall`. Ila, fish-seller, no importance tag. Authored observation: the smokehouse down the lane has its shutters closed this morning. No cause.
- Player: “I ask the fish-seller who she is and what she makes of the shuttered smokehouse.”
- Contract `rc_d1b3554afa52`: operation `ask`, expected `clarification`, interlocutor id null, target null. Social resolution nevertheless resolved `npc_id` `ila` and `reply_kind` `refusal`.
- Decision: absent.
- Generation 1, accepted: Ila shrugs, looks toward the smokehouse, says she is a humble fish-seller, and cannot say why it is closed. She suggests asking around or checking with the ward’s watch.
- Discourse `active_interlocutor` stayed null. Ledger empty. Scene canon unchanged, so the closure was not given a new cause.
- Manual: PASS. She is a specific person with a manner, she knows the limit of her knowledge, and she does not invent sabotage, an owner, or a syndicate. “The ward’s watch” is an unauthored civic redirect and a soft blemish. The contract’s failure to bind her would matter on a second turn; this probe is one isolated turn, and the spoken answer is still hers.
- The pass is model behavior on a route with no decision.

## 5. Contract-quality analysis

Every turn produced a Resolution Contract before narration. Interpretation ran once, on turn 7.

| Turn | Quality | Note |
| --- | --- | --- |
| 1 | Partial, sufficient | `ask` / answer matches a direct question. Obligation mode `clarification_target_failure` disagrees with the decision’s `established_or_retrieved`. |
| 2 | Fully sufficient | Nessa, membership question, expected answer. |
| 3 | Fully sufficient | Pell, dumping question, expected answer. |
| 4 | Partial | An inspection was contracted as `ask` with an empty subject. The observation fact was still available to the decision. |
| 5 | Fully sufficient | `perceive` / `smell` / `bounded_incidental`. |
| 6 | Fully sufficient | `act` plus a resolved `scene_transition` to `reed_drying_loft`. |
| 7 | Partial | “Who and when” became a time-dimension follow-up on an unresolved claim, while the authored object was the bell. |
| 8 | Incorrect binding | Social layer found Ila. The contract left interlocutor and target empty and expected clarification. Discourse did not store her. |

Incorrect or partial contracts did not cause the three canned refusals. Those turns had the authored fact on the decision. The social invention on turn 2 had a good contract.

## 6. GMResolutionDecision-quality analysis

When attachment ran, the decision was the right envelope:

- Turn 1 authorized the cracked cold kiln and did not authorize a cause.
- Turn 4 authorized the crust and the stiff wool as an observation.
- Turn 5 classified the turn as bounded incidental and said mundane sensory detail may persist.
- Turn 7 authorized “cracked” and did not authorize an actor or a time.

Attachment did not run on turns 2, 3, 6, and 8. The code path is the early return in `attach_interaction_obligation`: an existing `resolution_contract.contract_id` marks the contract retry-preserved and returns before `attach_gm_resolution_decision`. Social questions and the scene transition arrive with a contract already built, so they skip the decision. The prompt flag `contains_gm_resolution_decision` matches that split exactly: true on 1, 4, 5, 7; false on 2, 3, 6, 8.

The decision’s constraints are generic sentences. They are not a realization plan for “answer whether it is firing by using the cracked/cold fact.” The model still managed that reading on turn 1 before validation.

## 7. Proposed-fact / provenance analysis

Authored structured rows became `authored_world_fact` / `world_truth` / `scene.visible_facts.N` with the source identity intact. NPC existence rows (`Bram exists as baker`, and the same shape on other NPC scenes when the decision ran) use kind `entity`.

No turn committed a new world flag, faction, or event-log truth. Turn 2’s Compact and turn 8’s ward watch were not persisted. Turn 5’s smell and clothing persisted only as `runtime_incidental`.

The audit on turn 5 attached the clothing sentence to the pre-existing “Bram works behind the counter” world-truth row because that sentence lexically covers the unstructured fact. The ledger’s own kind stayed incidental, and scene canon did not absorb the shirt and apron. Provenance labels in the audit object and the persistence ledger disagree; the committed state followed the ledger.

Turns without a decision have no proposed-fact list at narration time. Provenance protection cannot operate there. Turn 2 is the demonstration: a consequential claim was spoken as known fact and accepted.

## 8. Semantic-fidelity analysis

Re-audit of the saved generations against the saved decisions, with no new model calls:

- Turn 1 gen 1 and gen 2: the cold/cracked wording matches. The answer sentence “not currently firing” mismatches because polarity defaults to positive and `_has_negation` treats “not” as a contradiction of the cracked fact, even though “not” negates firing.
- Turn 4: any sentence that mentions the vat or the wool without also containing `stiff`, `crust`, or `pale crust` is `semantic_identity_mismatch`. A lead-in (“you lean over the vat”) and a withheld-cause sentence (“what befell the wool remains unclear”) both fail. Matching is sentence-local.
- Turn 7: the good sentence contains both “cracked” and “no one.” The negation check fails the whole sentence, including the true clause. A later sentence that mentions “the bell” without repeating “cracked” fails the same way.
- Turn 5: no violation. Incidental sentences were flexible enough to pass.

The strengthening the probe tried to tempt (who broke the bell, why the wool stiffened, why the kiln is cold) was largely resisted by the model. The checker then rejected the resistance whenever it used “no” or “not,” or whenever a neighboring sentence named the subject without repeating the value.

## 9. Narration-quality analysis

Player-facing quality and raw-model quality diverged.

Raw generations on turns 1, 4 (second attempt), and 7 were close to a competent GM: state the authored fact, answer the question, leave the missing cause unknown. Turn 1’s retry added a little unused history (“last blazed,” “interrupted activity”). Turn 4’s first attempt invented absent splashes and a settled location for the cause; the retry removed that.

Turns 3, 5, 6, and 8 were natural on the first attempt. Turn 2 was fluent and authority-wrong. Turn 6’s loft description is slightly ornamental and still about the authored destination.

The three failed authority turns replaced that narration with one identical sentence. That sentence does not mention the kiln, the vat, or the bell.

## 10. Validation / retry analysis

Retries: 3, all on the decision-present question turns (1, 4, 7). Each used one `retry_escalation` after `hard_invalid` / `unauthorized_resolution_decision_fact`. No turn exceeded two generations.

The retry feedback names the violation and says to use established facts or qualified belief. The retry user message was 422 characters and did not include `resolution_contract` or `gm_resolution_decision`. The model answered again without the decision in view. All three retries failed the same identity check. Acceptance then switched to `safe_nonresolution`.

Accepted text and emitted text matched exactly on all 8 turns, including the three fallbacks. Post-accept mutation was not observed. Skipped mutators on the fallback turns include the final emission gate and contract monotonicity enforcement; the canned line is sealed as immutable.

Decision audits stored on the accepted fallback are null. The attempt records keep the reason code and the rejected text. Sentence-level reason codes were recovered by re-auditing the saved generations; they are `semantic_identity_mismatch` only.

Social and movement turns had no decision, so `validate_generated_response` did not append `unauthorized_resolution_decision_fact`. Turn 2’s hint already forbade invented speaker facts. That hint did not stop acceptance.

## 11. State / commit analysis

| Turn | Scene after | Ledger | Discourse | Canon mutation |
| --- | --- | --- | --- | --- |
| 1 | `clay_kiln_yard` | empty | contract id only | none |
| 2 | `net_loft` | empty | interlocutor Nessa | none; Compact not stored |
| 3 | `salt_pans` | empty | interlocutor Pell | none |
| 4 | `dye_shed` | empty | contract id only | none |
| 5 | `bread_stall` | 1 incidental sensory entry | inspected place | visible facts unchanged |
| 6 | `reed_drying_loft` | empty | last action is the move | location advanced to the authorized exit |
| 7 | `chapel_close` | empty | contract id only | none |
| 8 | `fish_stall` | empty | interlocutor still null | none |

Commit agreed with narration on the movement turn. The three fallbacks committed no false cause, and they also committed no answer. Turn 2 committed the interlocutor without committing the invented Compact, so a later turn would remember Nessa and would not remember a stored gathering place. The player still heard the gathering place as fact.

## 12. Bounded-improvisation analysis

Turn 5 is a clean pass. Smell, cloth, flour, and “cool air” are mundane. The ledger recorded them as incidental. Scene canon and world flags stayed as seeded.

Turn 6 improvised slats, light, creak, and a straw scent inside an authorized destination. Nothing was written to the incidental ledger. The detail stayed in the utterance. It did not add a route or a hidden place.

Turns 1, 4, and 7 were not allowed to keep even the authorized fact once one sentence failed, so incidental texture in those generations (awning, sparrows, shed dimness) never reached the player.

Turn 2’s “rough rope” and “tarred” manner would have been fair incidental color. They arrived glued to a consequential invention.

## 13. Overconstraint / nonresolution analysis

Three of eight player-facing replies are the identical sentence from the safe-nonresolution path: “No one here can answer that from what is settled here.”

Each of those turns had an authored answer available:

- the kiln is cold and cracked;
- the vat has a pale crust and the wool is stiff;
- the bell is cracked, and the actor and time are unknown.

The overconstraint is specific. Identity matching is per sentence. A subject mention that does not repeat every value term fails. A polarity-positive fact fails if the same sentence contains “no” or “not,” including “not firing” and “no one knows.” One failing sentence fails the whole generation. The replacement does not preserve the sentences that matched.

Social turns were under-constrained relative to the new layer, because the layer was absent. Turn 2 used that gap. Turns 3 and 8 happened to stay mostly inside epistemic limits without it.

## 14. Human-GM comparison

A competent GM at this table would:

- Turn 1: say the kiln is cold and the arch is cracked, so it is not firing, and stop before a history.
- Turn 2: let Nessa say she is a net-mender and does not belong to any such compact, or that she has never heard of it. They would not place the Compact at the docks and the market as known fact.
- Turn 3: accept Pell’s inability to confirm. The dockworker redirect is ordinary table color.
- Turn 4: report the crust and the stiff wool, offer a possible fouled dye only as a guess, and not invent missing splashes.
- Turn 5: invent the smell and the clothes.
- Turn 6: move the player into the loft and describe it.
- Turn 7: keep the crack and say the close does not show who or when.
- Turn 8: let Ila be a fish-seller with a limit on the smokehouse. The ward-watch suggestion is optional color.

The engine’s raw text matched that standard on turns 1, 3, 5, 6, 7, and 8, with the reservations already noted. The player-facing text matched it on 3, 5, 6, and 8 only. Turns 1 and 7 were correct in the model and wrong at the seal. Turn 4’s second generation was the GM-standard version and was also sealed away. Turn 2 was fluent and would mislead a player.

## 15. Failure-family clustering

Four failures, two families.

**Family 1 — identity mismatch, then canned nonresolution.** Turns 1, 4, 7. Same reason code, same fallback sentence, same retry shape (decision dropped from the retry prompt). This is the authority-sensitive cluster. It is a validation/fidelity defect on top of a decision that had already authorized the right fact.

**Family 2 — decision not attached, consequential speech accepted.** Turn 2 only, as a hard fail. Turns 3, 6, and 8 share the missing decision. Turn 6 was saved by the movement resolver. Turns 3 and 8 were saved by a careful model. The hole is the same.

No cluster of “the model strengthened a damaged object into a culprit.” The strengthening pressure was answered and then deleted.

No cluster of location desync. The one movement turn committed and narrated the same loft.

## 16. Comparison with the original 8/40 gate failure mechanisms

The second full gate (`artifacts/pr_br_second_full_gate/20261003T142725Z`) was 8/40 PASS. Its recurring mechanisms were:

1. Unsupported consequential facts, mostly patrol authority, accepted as playable premises (19 consequential-authority primaries).
2. Addressee and referent loss into fallback or the wrong speaker.
3. Concrete inspection replaced by generic safe nonresolution (12 generic fallbacks).
4. Movement/exploration contracted as `ask` while other paths still moved.
5. Narrated travel that did not persist location.

This 8-turn probe, in novel domains:

- Mechanism 1 still appears, once, and only on the route where the new decision is skipped (turn 2). It did not appear as a committed patrol-style fact. The decision-present turns did not accept a new consequential cause.
- Mechanism 2 appears lightly: turn 8’s contract and discourse missed Ila even though the social resolver and the utterance used her. It did not produce the wrong speaker.
- Mechanism 3 is the dominant player-facing failure again: 3/8 replies are one canned sentence. The trigger has moved. In this run the canned line replaces a generation the new semantic checker rejected, including generations that had already stated the authored fact.
- Mechanism 4 appears as turn 4’s inspection contracted as `ask`. It did not produce rogue movement.
- Mechanism 5 did not recur. Turn 6 persisted `reed_drying_loft` and the narration arrived there.

Accepted/emitted equality held on 8/8, as the C18 seal held on the 40-turn gate.

The new layer changed the shape of the authority failure. Where it is attached, consequential invention is being blocked, and usable answers are being blocked with it. Where the contract is built earlier, the layer is not attached, and the old “fluent unsupported fact” failure can still pass.

## 17. Recommendation for next step

Return to targeted implementation. Two defects, in this order:

1. Attach `GMResolutionDecision` whenever a Resolution Contract is already present. The early return in `attach_interaction_obligation` currently skips it for social resolution and scene transitions. Turn 2 is the cost of that skip.

2. Make semantic-identity rejection sentence-safe for the realizations these probes required: an answer may negate a different predicate (“not firing”) without contradicting `condition=cracked`; a sentence may name the subject while a neighboring sentence carries the value; “no one knows who” must remain compatible with a positive cracked/damaged fact. A single mismatched sentence must not replace the whole turn, including the sentences that matched, with the canned nonresolution line. The retry prompt has to carry the same decision the first attempt saw.

Do not start PR-BS. Do not run another 4×10 gate. Do not authorize a human playtest. Do not rerun these eight turns until those two defects are fixed; rerunning them now would remeasure the same mechanisms.

## 18. Exact gameplay / model call count

| Call class | Count |
| --- | --- |
| Isolated gameplay turns (`POST /api/chat`) | 8 |
| Gameplay generation calls (`call_gpt`) | 11 |
| Of those, initial generations | 8 |
| Of those, engine retries | 3 (turns 1, 4, 7) |
| Interpretation model calls | 1 (turn 7) |
| Upstream preflight health calls | 1 (process startup, not a gameplay turn) |
| Evaluator model calls | 0 |
| Extra gameplay turns, reruns, or hidden chats | 0 |
| 4×10 gate sessions | 0 |

Total model API calls in the process: **13** (11 generations + 1 interpretation + 1 preflight).
Gameplay turns: **8**.

## Required decision

B.
LIVE VALIDATION EXPOSED LOCALIZED DEFECTS;
RETURN TO TARGETED IMPLEMENTATION
