# 03 — Dialogue Failure Reconstruction

Reconstructed on the pre-edit tree with the disposable Mara scene, before the dialogue-authority module was added.

## Case A — irrelevant answer

Player: “I ask Sergeant Mara whether the north road is watched.”

Trace:

- Question dimension: `general`.
- The street topic “The street beyond the gate is the north road.” overlapped the subject, so it was treated as relevant and sufficient.
- The resolver could reveal that topic.
- Realization used `format_authored_knowledge_realization_line`, producing “Word is, the street beyond the gate is the north road.”
- A later authored-knowledge matcher could select the same topic again from subject overlap even after the reply plan had refused it.

Root cause: sufficiency treated a general dimension as an answer, and a second matcher repeated that choice. The line is grounded and does not say whether the road is watched.

## Case B — artificial uncertainty

Player: “I ask Mara what troubles her.”

Trace:

- Reply plan: `genuine_uncertainty`. Speech authority: `none`. Incidental subjective: false.
- Narration ran. Validation failed. `safe_nonresolution` emitted “I cannot answer that from what is settled here.”

Root cause: a personal question was handled as a missing world fact, and the fallback named the engine’s information limit.

## Case C — expensive knowledge gap

Player: “I ask Mara who forged the lantern.”

Historical PR-EF-R4 live case: `genuine_uncertainty`, speech authority `none`, three provider calls, 50,784 input tokens, final line “I don’t know.”

Root cause: that plan was not in the narration-skip set, so strict-social narration and a retry ran for a result the resolver had already closed.

## Case D — contradictory reply plan

With a prior revealed topic, `_bounded_social_reply_plan_for_missing_topic` reported `authoritative_answer_available` while `npc_speech_authority` stayed `none` and objective authority stayed `none`.

Root cause: any prior thread was treated as an available authoritative answer. Narration still ran because the skip required the consequential-information plan.

## What the final code does with these cases

- A is gated by `topic_supports_requested_information` in sufficiency, in the present-NPC topic matcher, and in the authored-knowledge candidate filter. A surveillance question is not answered by the road’s name. The determined line is “Sergeant Mara says, ‘I couldn’t tell you.’” with no narration call. The unit chat test asserts that.
- B is `personal_state`, posture `belief`, improvisation permitted, narration not determined. A generated personal remark can be kept. See the live turn in artifact 13.
- C is `maker`, posture `unknown`, narration determined. The live turn used one interpretation call and 1,965 input tokens.
- D is reconciled in `attach_dialogue_authority`: authoritative answer with no topic becomes genuine uncertainty, speech authority none, `reconciled_plan` `authoritative_without_answer`.

The live conversation also shows failures these four traces do not cover. They are scored in artifact 13, not treated as solved because A–D have a code path.
