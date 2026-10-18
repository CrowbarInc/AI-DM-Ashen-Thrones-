# 07 — Cross-Cycle Failure Analysis

| Cycle | What failed | What was changed | What remained |
|---|---|---|---|
| PR-EE | Ordinary GM talk had no purpose. Any unsupported singleton became a compound confirmation. "Why not?" was sent to an NPC who had not been asked. | Nothing. Investigation recommended a routing rework that kept the resolvers. | The recommendation became PR-EF. |
| PR-EF | Added recipient and purpose, GM answers from public passages, continuation, and proposal checks. Fresh holdouts were 5/12. A question about an NPC's expression could still be an NPC action. | Communication fields on the existing interpretation call. | Semantic handoff into resolvers was still wrong. |
| PR-EF-R1 | Repaired same-call guidance, pending continuation, and movement handoff. A fresh ten-turn conversation passed. A resolved NPC could still be narrated as unidentified, and a gesture could block a supported ask. | Normalization and carry into the existing contract. | Identity still fell out between bridge, resolver, and emission. |
| PR-EF-R2 | Carried the validated ASK id into emission and separated unknown knowledge from unknown target. Original holdouts 24/24. Additional holdouts 5/9. The ambiguous ask executed and ticked. | The bridge id became strong enough to replace a missing lexical person. | That strength now also replaces an explicit unresolved person. Recipient can still discard an ask. |

## Pattern classification

| Pattern | Class | Evidence |
|---|---|---|
| Meaning inferred from whether an operation exists | C, shared contract. The original EE compound bug is fixed. The habit remains: EXECUTE plus ASK is forced to purpose ACTION. | `ConversationalDecision.__post_init__`. EE report 10. |
| GM question converted into an NPC action | B, same cause, one instance largely contained. The prompt and the MIXED guard now block some of these. Fresh probe "What is the sergeant worried about?" stayed GM and did not execute, even though the model also emitted ASK Mara. | Fresh probe `gm_about_npc`. EF executive summary. |
| NPC address converted into a GM answer | C. New surface of the same owner split. | Case B. Fresh "one of them" sample. |
| Correct lexical result discarded downstream | C. R1/R2 taught the contract to trust the bridge id. That repair is what deletes "one of them." | `establish_ordinary_gameplay_contract` override. Two-NPC replay. |
| Ambiguous target executed | C, not a one-off default NPC. The social resolver did not invent Mara. It confirmed an authorized id. | Case A trace, `explicit_target`. |
| Correction becomes an ordinary question or a description | C, plus one missing object. There is no pending intention for a normal ask. The label is also unstable across provider samples. | Case D historical versus fresh probe. |
| Incidental gesture blocking an ask | A, historical, addressed in R2 by `normalize_social_scope` for a narrow posture pattern. | R2 report 03. Not reopened by these four failures. |
| Unsupported work offered for confirmation | A, historical. EE's unsupported-as-compound path was separated in EF. | EE report. Not the mechanism of these four failures. |
| Successful operation replaced by a generic refusal | D for the wording, C for why the model is called at all. Validation correctly rejects invented canon. The fallback then speaks as whoever was bound, and the 23k-token call was unnecessary once authority was `none`. | Conversation turns 3, 5, and 10. `safe_nonresolution`. |

## Are these symptoms of one fragmented contract?

Yes, for the failures that are still open. The evidence is not "several bugs happened." The evidence is that each cycle moved authority to a different field, and the next semantic variation failed on the field that was not consulted.

EE had no owner field, so operations stood in for conversation. EF added an owner field, and it could disagree with the operation. R1 and R2 made the operation's target id stronger than the lexical addressee, which fixed "who is Mara" and broke "one of them." None of those cycles created a record that says, at once, "this addressee is unresolved, this owner is NPC, this turn must not tick." Later stages still answer those questions again from whichever field they were given.

Independent mistakes exist and should not be folded into the contract story. The cause-template suffix is a local string in the explanation branch. Referent tracking's single-person label did not select Mara. The twenty inherited regression failures classified in R2 were not re-diagnosed here and are not claimed as this contract's symptoms.

Option C is not supported. Social resolution, authored-topic recall, inspection, and movement still complete without a new orchestrator. Turn 7 of the eleven-turn conversation answered the north-road topic from the resolver with one interpretation call and no narration call. Turn 11 moved through the gate with zero provider calls. The machinery that should remain authoritative is already authoritative when the authorization record it receives is coherent.
