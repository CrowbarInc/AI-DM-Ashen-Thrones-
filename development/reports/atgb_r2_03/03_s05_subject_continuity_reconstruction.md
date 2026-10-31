# 03 — S05 Subject-Continuity Reconstruction

## Historical sequence

1. S05.1 player: “Runner, what did you hear about the patrol?” Final: `Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."` The runner's hearsay is disclosed; the runner becomes active.
2. S05.2 player: “And the board, what does it say about the same patrol?” Final: “I cannot provide a validated response to that request.” This establishes a request about a second account, but no board detail. The runner remains active. This turn is context only; its failure is not independently diagnosed here.
3. S05.3 actual player text: **“Tell me more about that.”** The request's “Can you tell me more about that?” is representative wording, not the historical line. Final: “Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.”

## Four roles

**Addressee:** tavern_runner, supported by established interaction. The old wrong-person question was repaired in R2-02 and is not reopened.

**Subject:** broadly the missing patrol. The requested account/detail is not unique: the immediately preceding request concerned the board, the most recent actual informative answer was runner hearsay, and the immediately preceding delivered line was a validation failure. Neither “more” nor “that” selects uniquely among those relationships. The failure line itself can motivate a request for explanation, but contains no new world subject. Do not infer future S05.4 (“The runner's version, not the notice.”) as context that existed at S05.3.

**Evidence:** the runner's disclosed rumor is valid public evidence for a restatement, not proof of additional details or of the notice's wording. The board's last-seen clue remains gated. The current builder also labels the S05.2 failure `npc_latest_reply` because its resolution still has a target; that label does not convert the failure into informative NPC testimony.

**Authority:** communication.subject describes intent and cannot establish a fact. NPC evidence must still pass the resolver's speaker, topic, relevance, sufficiency and disclosure checks.

## Model and host

**Observed historical interpretation:** NPC/CLARIFICATION, subject “More information about the patrol rumor from the Tavern Runner,” one ASK tavern_runner, unresolved_references [], evidence npc:tavern_runner:patrol_rumor. Its summary and requested outcome commit to runner detail; this is a plausible reading, not proven unique. The old host discards that route at unresolved_addressee and asks the wrong clarification slot. That historical cause is settled by R2-02.

**Observed current replay:** unchanged captured record yields EXECUTE / single_authoritative_component / ASK tavern_runner, with no immediate response text. proposed_record retains subject and evidence. Changing communication.subject alone to the board account gives the same routing; subject is not an executable semantic plan. The bridge copies communication and selected public evidence into metadata, so there is no wholesale loss of those fields.

The synthetic in-memory social control, with prior patrol_rumor revealed, resolves the correct runner but yields topic_revealed null, requested_subject `more`, reply_plan_kind genuine_uncertainty. The fallback requires authored_topic_relevant_to_question and authored_answer_sufficient_for_question against **raw player text**, not communication.subject. The former does not resolve a bare follow-up to a unique topic. The host's downstream lexical assessment therefore does not adopt the model's proposed rumor binding. This is a demonstrated current boundary, not evidence that the rumor had to be disclosed or that the model interpretation was correct. Full historical preturn continuity state is unavailable.

## Ambiguity verdict

**Partially resolved:** recipient and broad patrol subject are known; runner-versus-board account and requested new detail remain materially ambiguous. The account choice is genuinely ambiguous in the available record. A targeted question is justified. A guaranteed runner-rumor continuation is not justified. Safe proposed clarification: “Do you mean the runner's rumor, or what you wanted to learn from the notice board?” This names only established accounts and claims no board fact. The existing GM/CLARIFICATION contract emits it in the offline adapter/decision control without a new schema or state store.

Original full provider context is **Unknown**. Current captured assembly includes both prior exchanges (the rumor and failure) and public rumor evidence. Thus context enlargement is not demonstrated necessary. The new replay does not establish that a live model will choose the better clarification or that every “that” requires clarification.
