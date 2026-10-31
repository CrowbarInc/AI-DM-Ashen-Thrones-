# 05 — Host Clarification Analysis

## Acceptance pathway

1. `live_chat_interpretation.py:430–433`: communication structure/enums and evidence membership validated. No semantic clarification-necessity check.
2. PR-DO adapter validates references, statuses, correction shape; `eligibility.py:109–121` returns NEEDS_CLARIFICATION if legacy mode is CLARIFICATION **or** status requires clarification **or** references/IDs are unresolved. Empty unresolved references do not negate the other conditions. This is an execution-safety gate, not a conversational-adequacy evaluator.
3. `live_chat_interpretation.py:499–506`: blocked clarification retains record and model question. “Blocked” does not mean the conversational route ends.
4. `api.py:6523–6564`: a retained record is sent to `decision_from_interpretation_record`; `conversational_orchestration.py:2217–2219` prioritizes communication. Grounding, action-control guards and selected evidence can affect the result. All three traces reach the revision guard and get null.
5. `conversational_orchestration.py:573–581`: CLARIFICATION plus no public_evidence chooses model question; `616–623` builds answer_only CLARIFY with no missing_information. This is the actual observed response plan.
6. `api.py:788–815` copies decision text into a nonmutating response with resolver/parser/narration flags false. Accepted-response receipts preserve it verbatim. `immutable_valid_response.py:1564–1588` authorizes/seals host speech and reports hard validity/contract satisfaction. Those flags protect authority/adoption, not the usefulness of the question.

## What the host knows and cannot establish

The host can reject malformed records or invalid evidence IDs, detect unresolved addressees, preserve missing action parameters, and decline unsafe operations. It can reconsider a blocked record and answer if selected public evidence supports the communication branch. Thus it is inaccurate to say no deterministic alternative exists at all.

However no current generic structured reason identifies what additional information a model-selected clarification needs. There is a free-text question, summary, statuses and references, but no required clarification reason, missing semantic slot, competing interpretations or relation to a corrected antecedent. ConversationalDecision has `missing_information` and `ambiguity` fields, yet these trials populate neither. The host has no established deterministic contract that proves the free-text question redundant for arbitrary input. No automatic reinterpretation/retry runs on this path. Adding one would violate this pass's authority and the proposed no-extra-call boundary.

Rejecting CLARIFICATION whenever unresolved_references is empty would discard legitimate missing-parameter, conflicting-intent and other clarification cases. Asking a generic question, emitting ignorance, or falling through to a gameplay parser would respectively preserve redundancy, discard known facts, or risk state mutation. None is an adequate fallback repair. A host question can be authorized speech and still be the wrong conversational decision.

## Offline counterexamples (provenance and evidence level explicit)

| Existing example | Structure / expected distinction | Comparison with L1/L2/L3 |
|---|---|---|
| PR-DO `fixtures.py` DN04: “OOC: I meant the left guard, not the captain.” | Hand-authored contract fixture; mode OUT_OF_CHARACTER_CORRECTION, status CLARIFICATION_REQUIRED, unresolved left guard, correction REFERENT, targeted question | Genuine unavailable referent explicitly represented; not a stored model outcome |
| PR-EF-R4 `ambiguous_one_of_them_two_npcs`, `ambiguous_either_guard` | Existing fixture inputs, expected clarify_no_mutation; provider stubs may even guess a target. Grounding must reject unsupported interlocutor choice | Several plausible people are a problem when selecting an interlocutor, not when describing people as a group |
| R1-05 L4 setup: “I ask one of them what happened.” | Production-created ambiguous pending ASK, followed by live “Instead, make that a question about the lamp.” revision | Pending intention is real; preserving it differs from inventing one for S08.2. Setup interpretation was stubbed, measured revision live |
| PR-EA `test_pr_ea_deterministic_incomplete_movement_clarifies_without_context`: “I leave.” | Existing deterministic test expects CLARIFY, missing_information=[destination], “Where are you trying to go?” | Legitimate clarification need not appear in unresolved entity references; test source inspected, not rerun |
| PR-EB `test_pr_eb_ambiguous_pronoun_inspection_resumes_after_clarification`: “I examine it.” | Existing stubbed API test offers lantern/shield, pending INSPECT, later “the lantern” resumes | Competing referents and pending operation represented; no live outcome asserted |
| R1-02 AMBIGUOUS: “No, the other one.” / “That's not what I meant.” | Existing routing stubs do not establish what a live model would ask; original excluded subject may be insufficient | Keep as ambiguous-correction guards; absence of action-control routing is not answer adequacy |
| PR-EB active-NPC follow-up: “Which captain?” | Existing test expects ASK to established Mara; PR-EF fixture npc_followup asks “What did you mean by the north road?” | A player's clarification request can be answerable; CLARIFICATION is not necessarily the GM requesting clarification |
| PR-EB conversation close: “That's enough for now.” | Existing deterministic API test expects conversational_answer, clears active interlocutor, no world change | Closest inspected no-fact acknowledgment/close; no evidence requirement. A standalone “Thanks” live trace was not established |
| PR-EG baseline c04t10: “Maud or Lior, what is the chapel relic called?” | **Preserved live baseline**: answer_status clarification_required, ambiguity_type addressee, reason addressee_not_grounded, “Which person do you mean?”, selected_source_ids=[] | Public evidence can exist while a legitimate choice is missing. Model proposal guessed Maud with clarification_needed=false; host corrected that |

Counterexamples show structured distinctions for **some** cases, not a reliable universal necessary/redundant discriminator on the legacy communication record. PR-EG's richer ambiguity_type belongs to its semantic-plan pathway; importing it wholesale is not justified here. Hypothetical conflicting instructions (“describe everyone, but describe nobody”) require a targeted resolution, not an empty-unresolved-reference veto. That illustration is proposed validation, not observed behavior.

Authority implication: preserve execution gating, target grounding, pending-intention owner, disclosure projection and immutable emission. Clarification usefulness is not permission to mutate or disclose. No authority defect is demonstrated by these three redundant but nonmutating questions.
