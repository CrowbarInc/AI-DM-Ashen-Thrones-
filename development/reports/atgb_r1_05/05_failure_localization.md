# 05 — Failure Localization

Primary development failure class for observed L1/L2 inadequacy: semantic.

L1 and L2, independently: earliest demonstrably incorrect decision is the live
model's clarification posture and empty evidence selection, observed together in
request_interpretation raw JSON (game/live_chat_interpretation.py:214). The subject
summary correctly distinguishes people from weather, yet communication_mode and
purpose are CLARIFICATION, evidence_refs is empty, unresolved_references is empty,
and clarification_question merely restates the player's already explicit correction.
The same request contains visible:1/2/3 describing people and the full preceding
reply:0. Thus context absence is not supported by this trace.

High confidence: these observed choices prevent a meaningful answer. No ordering
inside the model between posture and evidence selection is inferable. Adapter
NEEDS_CLARIFICATION and interpret_production_turn's clarification_required return
(game/live_chat_interpretation.py:500) follow. API at game/api.py:6526 passes the
record to decision_from_interpretation_record; _pending_revision_decision at
game/conversational_orchestration.py:391 returns null; _communication_decision
at :461 uses the supplied question. Final realization preserves the deficient plan.
No mechanical regression, bind rejection, disclosure rejection, provider failure,
or generic gameplay fallback explains these new outcomes.

R1-03 L3 comparison: same observed semantic mechanism — correct people subject,
redundant clarification question, no selected evidence despite supplied people facts.
Use its preserved trace.json, response.json and report 05. Wording differs and that
single paraphrase is not independent generalization. Current paths add direct evidence
of the repaired gate's abstention; prior report's claim that its gate was not reached
is not silently extended to these traces. No historical report is rewritten.

Strong explanation: a clarification disposition with no selected facts yields the
observed redundant host answer. Unverified hypothesis: schema's pending-intention
description of CORRECTION biases the model; no prompt intervention or alternate
model was tested. No causal claim that all correction failures share this mechanism.

L4 has no failed required control criterion. Its raw ASK target_ref points to the
lamp rather than an unresolved NPC and correction.note says person-to-lamp target
change. That semantic conflation is directly observed (high confidence); whether it
would impair later authorized execution is unverified. Host preserves choices and
does not execute. No additional scenario or continuation was run to test it.

Preparation-only evaluation issue: offline preview's store self-protection failure
arose from the new runner's environment binding, before its callback, not production
semantics. Current readiness.py preflight/assert_safe_benchmark_data_dir enforced the
guard. Scope-limited runner correction and failed/ready artifacts are retained.
No production repair is implemented or proposed as part of this pass.
