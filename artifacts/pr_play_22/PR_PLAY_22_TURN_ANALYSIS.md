# PR-PLAY-22 turn analysis

PROTOCOL DEVIATION: T1 already made the intended NPC sequence unusable. The controller checked HTTP/provider errors but failed to detect this host-generated semantic dead end. It submitted T2–T4 before stopping, and its raw ordinary_completed=4 counter counts HTTP success, not gameplay success. Those raw records are preserved. Review counts: 4 attempted, 4 HTTP responses, 0 successful NPC/gameplay interactions. T2–T4 are post-failure diagnostic observations, not a valid continuation or recovery. No restart, provider retry, replacement initialization, or extra live run occurred.

## T1

Player intent: Approach the visible runner and ask about offerings.

Technical: PASS (HTTP 200, ok=true). Provider: completed structured interpretation; parsed into native decision metadata.

Parser/validator: interpretation status INTERPRETED; bridge status blocked, reason clarification_required; host decision proposal_not_eligible. Gameplay parser, resolver and narration invoked: False, False, False. No ordinary narration candidate was generated, so narration hard-validation is N/A, not PASS. Structured provider output was not rejected as malformed; action eligibility was blocked.

Player received: I cannot carry out Approach the tavern runner, then Ask the tavern runner what they are offering with the available actions and targets. I have not done any of them yet.

Provider understood the actual target and question: MOVE tavern_runner followed by ASK tavern_runner. Host marked MOVE unsupported and ASK supported, then declined the whole sequence. No NPC speech, offer, or conversational foothold resulted. This is the first decisive gameplay failure.

Engine authorized: nonmutating conversational bookkeeping and log publication only. Location, time, inventory/currency, relationships, quest/world facts and combat unchanged. No unsupported consequential outcome was narrated. No NPC answer was emitted, so NPC setting appropriateness, useful information and omniscience are untested. No evidence of refusing an improvised biographical detail solely for lack of a catalog entry.

Latency: 2.625s API. Verdict: FAIL.

Evidence: live/turns/T1/api_response.json; parser_validation_diagnostics.json; normalized_state_diff.json; before/after snapshots.

## T2

Player intent: Ask the runner for elaboration; generated action instead quotes the engine refusal.

Technical: PASS (HTTP 200, ok=true). Provider: completed structured interpretation; parsed into native decision metadata.

Parser/validator: interpretation status INTERPRETED; bridge status blocked, reason clarification_required; host decision communication_before_execution. Gameplay parser, resolver and narration invoked: False, False, False. No ordinary narration candidate was generated, so narration hard-validation is N/A, not PASS. Structured provider output was not rejected as malformed; action eligibility was blocked.

Player received: I cannot carry out Approach the tavern runner, then Ask the tavern runner what they are offering with the available actions and targets. I have not done any of them yet.

Provider classified the quote as a request for GM explanation (OTHER/EXPLANATION). Host emitted the identical T1 refusal, without explaining the restriction. The NPC question was not answered. This is not a valid follow-up to NPC dialogue.

Engine authorized: nonmutating conversational bookkeeping and log publication only. Location, time, inventory/currency, relationships, quest/world facts and combat unchanged. No unsupported consequential outcome was narrated. No NPC answer was emitted, so NPC setting appropriateness, useful information and omniscience are untested. No evidence of refusing an improvised biographical detail solely for lack of a catalog entry.

Latency: 3.359s API. Verdict: FAIL.

Evidence: live/turns/T2/api_response.json; parser_validation_diagnostics.json; normalized_state_diff.json; before/after snapshots.

## T3

Player intent: Ask how the runner knows the quoted refusal; generated action has no sound in-world basis.

Technical: PASS (HTTP 200, ok=true). Provider: completed structured interpretation; parsed into native decision metadata.

Parser/validator: interpretation status INTERPRETED; bridge status blocked, reason clarification_required; host decision communication_before_execution. Gameplay parser, resolver and narration invoked: False, False, False. No ordinary narration candidate was generated, so narration hard-validation is N/A, not PASS. Structured provider output was not rejected as malformed; action eligibility was blocked.

Player received: I cannot carry out Approach the tavern runner, then Ask the tavern runner what they are offering with the available actions and targets. I have not done any of them yet.

Provider again classified the question as GM explanation. Host repeated the identical refusal for a third time. It preserved the refusal text, not an interactive NPC conversation. The harness action itself wrongly attributes host wording to the runner.

Engine authorized: nonmutating conversational bookkeeping and log publication only. Location, time, inventory/currency, relationships, quest/world facts and combat unchanged. No unsupported consequential outcome was narrated. No NPC answer was emitted, so NPC setting appropriateness, useful information and omniscience are untested. No evidence of refusing an improvised biographical detail solely for lack of a catalog entry.

Latency: 3.672s API. Verdict: FAIL.

Evidence: live/turns/T3/api_response.json; parser_validation_diagnostics.json; normalized_state_diff.json; before/after snapshots.

## T4

Player intent: Read the posted notices by walking over to the opening notice board.

Technical: PASS (HTTP 200, ok=true). Provider: not invoked; deterministic fast path.

Parser/validator: interpretation status N/A; bridge status N/A, reason N/A; host decision compound_intention_needs_confirmation. Gameplay parser, resolver and narration invoked: False, False, False. No ordinary narration candidate was generated, so narration hard-validation is N/A, not PASS. Structured provider output was not rejected as malformed; action eligibility was blocked.

Player received: You can decide to read the notice board first. I have not done this yet: walk over to examine the posted notices. Those later steps cannot be resolved as stated. Should I do the first one now?

No provider request. Deterministic compound handling recognized INSPECT as a supported first action, marked the later walking/examination step unsupported, and asked permission to do the first step. It did not inspect or move. This offers a possible narrow continuation but did not rescue the original NPC scenario.

Engine authorized: nonmutating conversational bookkeeping and log publication only. Location, time, inventory/currency, relationships, quest/world facts and combat unchanged. No unsupported consequential outcome was narrated. No NPC answer was emitted, so NPC setting appropriateness, useful information and omniscience are untested. No evidence of refusing an improvised biographical detail solely for lack of a catalog entry.

Latency: 0.250s API. Verdict: PARTIAL standalone; FAIL for connected gameplay.

Evidence: live/turns/T4/api_response.json; parser_validation_diagnostics.json; normalized_state_diff.json; before/after snapshots.

