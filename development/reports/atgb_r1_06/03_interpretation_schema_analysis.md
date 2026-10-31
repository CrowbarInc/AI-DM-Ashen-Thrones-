# 03 — Interpretation Schema Analysis

All locations below are current working-tree one-based lines. The three central production source hashes match both R1-03 and R1-05 entry manifests. Numbered excerpts are packaged in `source_excerpts.md`; full selected sources are also included.

## Actual provider construction

`game/live_chat_interpretation.py:34` deep-copies `_contract()[5]()`; `_contract` at 130 imports the existing PR-DP provider schema, PR-DR message builder and PR-DO adapter. These experimental-named dependencies are already on the production route; inspection is not candidate integration. `experiments/pr_dp/prompt.py:25` uses PR-DO's schema document and strips its non-provider documentation field.

`production_interpretation_schema` adds required communication recipient/purpose/subject/evidence_refs and moves communication before legacy fields. `request_interpretation` at 214–253 dispatches the actual OpenAI Responses call with that production schema, strict JSON generation, temperature 0 and output cap 320. `interpret_production_turn:313–319` supplies two recent visible turns; 322–357 appends production instructions; 359 appends PUBLIC evidence; 363–376 appends ownership/pending context. All historical request messages contain those additions. Wire schema itself is source-reconstructed, not a separately saved request object in L1/L2/L3.

## Definitions and their gaps

Legacy modes (`experiments/pr_do/schema.py:9` and `experiments/pr_dr/prompt.py:15–20`) are IN_WORLD_ACTION, OUT_OF_CHARACTER_CORRECTION, RULES_QUESTION, CLARIFICATION and OTHER. The request defines:

> OUT_OF_CHARACTER_CORRECTION=the player corrects a referent, an intention, or a committed action

> CLARIFICATION=the utterance is unclear

The user-message instruction at PR-DR:74 requires CLARIFICATION, one question, no guessed id when in-character play versus table talk is ambiguous. Actual S08.2 is an explicit subject correction; these traces do not demonstrate that ambiguity.

Production purposes (`live_chat_interpretation.py:31`) include QUESTION, DESCRIPTION, EXPLANATION, RECALL, RULES, ACTION, OBSERVATION, CORRECTION, WITHDRAWAL, CONFIRMATION, TENTATIVE and CLARIFICATION. The purpose schema at 58–62 says:

> CORRECTION revises unexecuted intent

This **does** imply pending gameplay-intent control. No equivalent definition covers correcting the subject of a previous description while continuing to answer it. Production system instructions reinforce this at 346 and 352–353: revision controls pending intent; revising a proposed attempt is GM/CORRECTION. However legacy OUT_OF_CHARACTER_CORRECTION explicitly includes referent correction. The vocabularies overlap imperfectly.

CLARIFICATION has no distinct purpose-schema description. System instructions at 337–341 also use NPC/CLARIFICATION for a player asking what an NPC just said, with ASK and selected NPC speech evidence. That is a **player request to explain**, whereas legacy CLARIFICATION means **the player's utterance is unclear**. At 342 the request nevertheless says legacy mode describes “the same speech act.” No field explicitly separates the player's clarifying their own meaning from the GM needing additional information before answering.

Status INTERPRETED and mode CLARIFICATION may coexist. The adapter permits this. `clarification_question` is a string, with no requirement to identify what remains unknown. Adapter:127–131 requires a question or unresolved reference only for status CLARIFICATION_REQUIRED; it does not validate semantic necessity. `correction.subject` allows NONE, REFERENT, INTENTION, COMMITTED_ACTION; no structured corrected question or required antecedent binding is carried here.

Each mode and purpose field is a single enum, mutually exclusive **within that field**, not across the envelope. There is no list of “acknowledge and answer” operations. But the existing host can answer with purpose CORRECTION and selected public passages after the action-revision gate abstains (`conversational_orchestration.py:557–586`; existing R1-02 evidence-preservation test). Explicit acknowledgment is not currently added to that answer. Multiple conversational effects are possible in language without making multiple gameplay operations; current realization does not encode them explicitly.

## Suspected defects and causal confidence

| Location/excerpt | Live support | Causal hypothesis | Confidence |
|---|---|---|---|
| production schema:58–62, “CORRECTION revises unexecuted intent”; system:346/353 | L1/L2 choose CLARIFICATION even while correction note says referent; legacy subject INTENTION | Mechanical purpose definition leaves ordinary subject correction poorly represented | High that contract is narrow; **medium** that this wording caused these outputs |
| PR-DR:19 unclear utterance versus production:337 NPC explanation; production:342 same speech act | All three summarize the correction but set mode/purpose CLARIFICATION | One label conflates clarifying meaning with requesting additional information | High ambiguity; **medium** causal attribution |
| production:332–333 “only when … answers the question”; “No evidence means unknown” | All three select [] and describe the requested outcome as understanding the correction | Negative-only selection rule does not connect an elliptical correction to its corrected underlying question | High contract gap; **medium** explanation of omission |
| schema:44 array of strings; validation:74 all refs must exist | [] accepted and projected to {} | No invariant relates answerability to evidence choice | High permissiveness; not proof of model's internal selection sequence |
| semantic_interpreter:127–141 truncates each visible line at 240 chars | Short recent GM field omits people; full reply:0 and visible:1–3 remain | Truncation may bias salience but does not remove necessary evidence | Low causal confidence; do not enlarge context as first repair |

No relevant worked example for answerable GM conversational correction is present in this provider message assembly. Existing code tests are not automatically model-facing examples. No instruction explicitly commands redundant confirmation. Conflicting/underspecified definitions plausibly invite it; attribution to a particular sentence remains unproven without an intervention.
