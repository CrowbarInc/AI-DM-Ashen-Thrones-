# 06 — Repair Candidate Evaluation

Proposals only. No production, prompt or schema changes were made. At least the top three are evaluated here; all future execution requires external review/new scope.

## Candidate 1: F1 — Speech-participant grounding

Observed defect: S03.3/S05.3 raw model selects an active, present runner; shared host addressee decision rejects it using unmatched grammatical speech nominals. Earliest demonstrated failure is host grounding, before resolver; extraction detail is supported by unmodified syntax probes.

Owner: `game/ordinary_semantic_ownership.py::assess_addressee_grounding`; speech-recipient extraction helper `game/interaction_completion.py::addressed_person_nominal`. All existing callers in orchestration, interpretation bridge, ordinary contract and pre-tick gate must consume the same result. Do not repair an individual caller by bypassing the owner.

Shape: distinguish speech addressee from grammatical recipient/complement, then apply existing explicit-wording and bounded active-interlocutor precedence. Second-person “you” can use a uniquely established, present social interlocutor in an NPC exchange; first-person “me” in a tell construction denotes the player, not an unknown NPC. Preserve ambiguous topic handling separately. Explicit names/roles and genuine nonunique nominals remain authoritative inputs; arbitrary model target IDs never settle ambiguity. No phrase-specific ATGB cases or indiscriminate first-word trimming.

Required context: current scene-visible roster, existing active social target, player text and proposed ASK target, existing delivered exchange/ownership when needed to distinguish GM from NPC. No new persisted state or expanded memory window. Treat S05's recent GM refusal as a topic/ownership boundary, not permission to resume an old rumor automatically.

Authority: grounding identifies an addressee only. Existing bridge, knowledge/disclosure, pending intention, resolver and tick rules still govern ASK and effects. A corrected rejection can newly reach a legitimate social resolution, which may have existing time consequences; require the same effects as an equivalent explicit address. Never assert that every NPC ASK is non-mutating.

Performance: no new provider classification, retry or automatic follow-up call. Pure host computation has unmeasured small expected CPU impact. Prompt/context size should not grow. A turn previously stopped at clarification may now incur existing downstream resolver/expression calls; total call/token/latency effect is unknown and must be measured under the standing budget, not described as free or zero. Stop rather than add admissions when that budget is insufficient.

Offline validation: recorded-interpretation reproductions plus unrelated-name role fixtures; all grounding consumers agree; explicit conflict/nonunique/offscene/GM controls; response plan and state-effect equivalence to explicit-address control. Live acceptance: separately authorized production entry, exact raw requests/results, speaker/topic/answer adequacy independently reviewed. Regression surface medium: shared addressee owner, ASK bridge, social resolution, pre-tick eligibility. No whole-engine refactor.

## Candidate 2: F2 — Question-conditioned evidence sufficiency

Observed defect: recognized curfew time question selects category-only passage; earlier non-answer can be recycled as evidence. Earliest supported failure is interpretation evidence selection; host only checks public membership and emits joined text. S02.4 also involves gated clue access, not merely missing selection.

Owner: existing legacy interpretation contract and `_communication_decision` answer assembly/public evidence projection. R5's semantic planner already has a distinct proposition coverage owner; do not transplant it or establish a parallel classifier without evidence.

Smallest plausible scope: require selected evidence to support the requested detail; empty evidence produces specific grounded uncertainty rather than repeating nearby facts. Couple underlying question to selection in the existing call. However a deterministic general semantic sufficiency test is not identified here; bounded instruction refinement might help but R1-07 already addresses a correction subset. If chosen, first discriminate supplied non-answer, genuinely absent fact and gated clue on saved records/actual payloads before implementation. Do not promise a relevance validator from keywords.

State/context: current question, available public passages, prior delivered answer for elliptical question; source disclosure eligibility. No new world facts or state. Preserve knowledge ownership: empty GM evidence does not license loading hidden board clue or private NPC topic. Passing a public membership test is necessary but insufficient.

Benefit: more useful specific uncertainty and fewer stuck loops; larger potential exposure than F1. Complexity medium/high because question propositions and source propositions interact. Risk medium/high: rejecting valid paraphrases, inventing clock hours, promoting related nonanswers, exposing gated details. Tokens may increase for a clearer existing contract; no extra calls allowed; exact latency and model effect unknown. Offline tests can prove flow and absence/disclosure handling, not actual semantic selection improvement. Live trials must include answerable, absent, related-nonanswer and hidden-source controls with independent human judgments; original/related/held-out claims separate. Preserve PR-EG R2 as diagnostic comparison, not integration authority.

## Candidate 3: F3 — Ordinary remark acknowledgment

Observed defect: raw model expresses acknowledgment intent but labels SESSION/OBSERVATION; host returns ruling language. S01.4 has no operation, S07.2 proposes SOCIAL_SIGNAL. Earliest wrong decision is ownership; acknowledgment support is the next missing contract.

Owner: production interpretation guidance in `live_chat_interpretation.py`, existing orchestration answer branch in `conversational_orchestration.py`. R1-07 already allows empty evidence for factual-free acknowledgment, so first inspect/reuse that obligation rather than duplicating it.

Shape: bounded contract for an ordinary noncommitting remark with existing representation and a short acknowledgment carrying no new world proposition. Do not replace every SESSION response, invent facts, introduce a catch-all semantic classifier, add ACK schema automatically or turn apparent acknowledgment into withdrawal that clears pending work.

Required context: speech ownership, pending intentions, current delivered response and authorized visible content only if actually used. No persistence. Benefit: avoids mechanical interruptions in everyday remarks. Complexity moderate: both model ownership and host realization must align; changing only the fallback string is insufficient. Authority risks lower than F1 but real: remarks must not trigger actions/ticks, erase proposals or launder player premises into canon. No extra provider call; narrow prompt guidance may change tokens and live interpretation, unmeasured. Deterministic tests can prove no-op state and supported route under controlled labels; live ordinary remarks, explicit rules questions, genuine actions and mixed/pending controls needed. Regression surface is existing SESSION/GM communication and fallback behavior.

## Why F4 is not a shortcut

Only propose expression changes after a correct authorized answer plan exists. R5 c06t07 supports a small ignorance-line preservation repair; it does not justify rewriting ATGB's mistaken content. Cosmetic naturalness must not hide unanswered questions or wrong speaker selection. F5 remains the pending R1 acceptance lane, not a new repair candidate.
