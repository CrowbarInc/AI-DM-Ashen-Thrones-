# 06 — PR-EG Comparison and Causal Verdict

## PR-EG comparison

Final PR-EG-R6-R5 is the authority, not a superseded R4-R1 summary. Its raw baseline has 164 rows. Representative inspected rows and original reasons are packaged in `pr_eg_comparison_rows.json`; these are excerpts of preserved executions, not new experiments.

| Topic | Relationship | Evidence and implication |
|---|---|---|
| Correction-purpose ambiguity | **Distinct** demonstrated mechanism | ATGB selects legacy GM/CLARIFICATION; PR-EG c06t03 correctly proposes conversational_act=correction but host rejects invalid_correction_operation. c07t02 is correction with unlisted_role_change. Similar correction failure does not identify same cause |
| Inadequate antecedent binding | **Related** | PR-EG report 07 demonstrates bind/witness rejection against stored propositions; c03t14 has ambiguous_historical_target. ATGB has adequate prior question/full reply in request and no demonstrated bind rejection |
| Question-to-evidence mismatch | **Related** | PR-EG reports 15/17/18 and R2 concern proposition pairing/coverage. ATGB selects no public passages before its host answer projection. No coverage rejection is traced here |
| Evidence-reference omission | **Distinct** operational gate | ATGB communication.evidence_refs directly controls public_evidence. PR-EG source-id retrieval intervention I4 net 0 (report 16); host scans all public NPC topics. An omitted selected_source_ids can be downstream of bind/coverage, not failure to list candidates |
| Excessive clarification | **Related** | PR-EG baseline quality flags 9 false clarifications; F12 appears downstream in 6 failures and first in 0 (report 25). Same symptom, no proof of same legacy speech-act ambiguity |
| Host acceptance of inadequate plans | **Related** | Both can emit structurally accepted but semantically inadequate language. PR-EG c01t14 has an authorized_partial host line but a final clarification question (F15 attribution; its expression field is null); ATGB final text already equals the wrong interpretation/decision, zero generation attempts |

None of those shared high-level descriptions establishes the **same specific causal mechanism**, so no row is labeled Directly supported. PR-EG also contains useful directly observed legitimate clarification controls (c04t10), but that does not equate its failure mechanism with S08.2.

R5 R1 proposes bind/witness changes; inapplicable to this demonstrated legacy interpretation failure. R2 proposes joint question/source proposition alignment; not the boundary exercised here. R3 protects an ignorance line from expression; these ATGB responses have no expression rewrite. The general lesson that downstream wording cannot recover a missing authorized answer applies. The experimental candidates and R4-R1 integration ban remain untouched. No prediction from I8's 44/54 or I10B's 45/54 is transferred to ATGB.

## Stage-by-stage causal trace

| Stage | Classification | Supported finding |
|---|---|---|
| Available context | **Correct** for this request | Prior question, full prior answer and relevant public people passages supplied; truncated recent-turn field is a limitation, not demonstrated missing evidence |
| Interpretation instructions/schema | **Incorrect as a complete product contract**; causal contribution indeterminate | Ordinary conversational correction not clearly separated from action revision and GM clarification need; selection guidance lacks corrected-question obligation |
| Model disposition | **Incorrect** | All three choose a redundant question despite summaries that understand the correction. Earliest demonstrably wrong **runtime decision** |
| Evidence selection | **Incorrect for these turns** | Relevant authorized passages left unselected; co-produced with disposition, internal ordering indeterminate |
| Host validation | **Correct under current structural/authority rules**, semantically insufficient | Accepts allowed enum/empty refs, preserves no-op revision and emits clarification. No necessity proof required |
| Response plan | **Incorrect for intended conversation** | CLARIFY/answer_only with empty missing_information and empty context_references |
| Final response realization | **Correct relative to selected plan**, inadequate to request | Exact model question survives decision and immutable emission; no later distortion |

The requested linear diagram is an analytical decomposition. Disposition and evidence selection are fields in one completion, not separately observed serial model processes.

## Observed failure, hypothesis, consequence

**Observed (high confidence):** understood corrected subject is mapped to requesting confirmation, with no facts selected. There is no demonstrated unresolved entity referent, missing action target or conflicting instruction in these turns. The raw output itself demonstrates the earliest wrong runtime decision. L3 also misstates the prior question as a weather question; it had the correct broad question available. That antecedent paraphrase error is co-produced in the same completion, not proof of an earlier binding-stage defect.

**Root-cause hypothesis (medium confidence):** a narrow CORRECTION purpose plus an overloaded CLARIFICATION label encourages treating the player's act of clarification as the GM's need for clarification. Negative-only evidence selection fails to connect the correction to the prior answerable description request. Model summaries/requested_outcomes support this reading. No controlled prompt ablation proves which clause mattered; pretraining preferences, salience/truncation, or the interaction of instructions could contribute. Output cap is not established as causal: completions are recorded completed, well formed and include a full question, not truncated evidence lists.

**Downstream consequence (high confidence):** [] projects to {}, legacy eligibility flags NEEDS_CLARIFICATION, API reconsideration accepts the same posture, host chooses CLARIFY and seals its question. This is not an observed failure of evidence disclosure, state ownership, final wording generation, or PR-EG bind().

The development class is **contract** because the existing owner can perform the answer but its stated classification/evidence obligations are incomplete. A new architecture or semantic classifier is unnecessary on this evidence. The semantic failure is proven; a successful repair and generality are unproven.
