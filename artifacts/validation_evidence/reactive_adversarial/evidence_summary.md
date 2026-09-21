# Validation Evidence: reactive_adversarial_20260918_evidence

> **No important player-facing PASS without inspectable behavioral evidence.**

What was tested: Bounded reactive and adversarial player behavior across watch-command, notice-observation, and patrol-knowledge objectives.
Runtime path: In-process FastAPI TestClient through POST /api/chat with campaign reset before each run.
GM boundary: Configured live AI-GM runtime; outputs are preserved runtime responses, not test-authored GM fixtures.
Player inputs: Authored opening actions followed by deterministic reactive/adversarial policy choices; stress probes are labeled separately.
Runs / turns: 7 / 18
Automated conclusion: The source campaigns completed valid runtime turns and produced PASS/FAIL semantic results. Human review recorded known failures, one evaluator miss, one probable false positive, and one ambiguous response.
Result counts: `{"FAIL": 12, "PASS": 6}`

## Selected Evidence

### Representative Success

Selection: first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS

Example: `reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_0`
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/notice_observation_adversarial_seed1701/run.json`
Run / turn: `notice_observation_adversarial_seed1701` / `0`
Input classification: `representative_player_behavior, runtime_discovered`
Selection rationale: initial_objective:Read the concrete information posted on the gate notice.

Player input (exact):

> I inspect the notice closely and read what is posted.

GM output (exact):

> The notice board displays three sections in faded ink, barely holding against the rain. The first lists new taxes imposed on various goods—grain, cloth, and salt—with strict collection deadlines. Next are curfew hours tightening for travelers and merchants, cited as necessary due to recent unrest. The final section warns of a missing patrol, last seen heading northwest along the muddy track past the stacked crates near the eastern approach. Your eyes catch the gate serjeant glancing at this list while keeping watch on the crowd.

Automated result: `PASS`
Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 87, "text_preview": "The notice board displays three sections in faded ink, barely holding against the rain. The first lists new taxes imposed on various goods—grain, cloth, and sal"}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 23, "gm_terms": ["against", "along", "approach", "barely", "board", "catch", "cited", "cloth", "collection", "crates", "crowd", "curfew", "deadlines", "displays", "due", "eastern", "eyes", "faded", "final", "first"], "player_intent_score": 18, "player_terms": ["closely", "inspect", "notice", "posted", "read", "what"], "request_kind": "observation"}, "passed": true, "reason_codes": [], "status": "PASS"}}`
Diagnostic result: `{"axis_scores": {"direct_answer": 23, "immersion": 24, "logical_escalation": 19, "player_intent": 18}, "passed": true, "rating": "strong", "score": 84}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"diagnostic_quality_rating": "strong", "passed": true, "rating": "strong", "score": 84, "semantic_result": "PASS"}, "run_valid": true}`
Continuation: `{"continued": true, "next_player_action": "You described the notice as both weathered and legible. Which parts can I actually read?", "next_selection_reason": "adversarial_probe:contradiction:prior_semantic_pass"}`
Human review: `UNREVIEWED` - No human judgment recorded for this exact interaction.
Evaluator disagreement: `{"calibration_reference": null, "human_status": "UNREVIEWED", "later_evaluator_result": null, "original_semantic_result": "PASS", "policy_changed": false, "present": false}`

### Boundary Success

Selection: first automated PASS or HUMAN_ACCEPTED example labeled boundary_case

Example: `reactive:20260918T021838Z:patrol_knowledge_reactive_seed1701:turn_1`
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/patrol_knowledge_reactive_seed1701/run.json`
Run / turn: `patrol_knowledge_reactive_seed1701` / `1`
Input classification: `boundary_case, runtime_discovered`
Selection rationale: repeat_after_malformed_output

Player input (exact):

> One bounded answer: last reliable location, source, and uncertainty.

GM output (exact):

> "From what I heard," the tavern runner lowers their voice, glancing around nervously, "the missing patrol was last seen near some muddy footprints northwest of the crates, just outside the gate. But no one knows exactly what happened after that."

Automated result: `PASS`
Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 40, "text_preview": "\"From what I heard,\" the tavern runner lowers their voice, glancing around nervously, \"the missing patrol was last seen near some muddy footprints northwest of "}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 23, "gm_terms": ["after", "around", "crates", "exactly", "footprints", "gate", "glancing", "happened", "heard", "knows", "last", "lowers", "missing", "muddy", "near", "nervously", "northwest", "one", "outside", "patrol"], "player_intent_score": 18, "player_terms": ["answer", "bounded", "last", "location", "reliable", "source", "uncertainty"], "request_kind": "action_or_statement"}, "passed": true, "reason_codes": [], "status": "PASS"}}`
Diagnostic result: `{"axis_scores": {"direct_answer": 23, "immersion": 23, "logical_escalation": 23, "player_intent": 18}, "passed": true, "rating": "strong", "score": 87}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"diagnostic_quality_rating": "strong", "passed": true, "rating": "strong", "score": 87, "semantic_result": "PASS"}, "run_valid": true}`
Continuation: `{"continued": false, "termination_reason": "legitimate_boundary"}`
Human review: `UNREVIEWED` - No human judgment recorded for this exact interaction.
Evaluator disagreement: `{"calibration_reference": null, "human_status": "UNREVIEWED", "later_evaluator_result": null, "original_semantic_result": "PASS", "policy_changed": false, "present": false}`

### Representative Failure

Selection: first failure labeled representative_player_behavior

Example: `reactive:20260918T021838Z:patrol_knowledge_adversarial_seed1701:turn_0`
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/patrol_knowledge_adversarial_seed1701/run.json`
Run / turn: `patrol_knowledge_adversarial_seed1701` / `0`
Input classification: `representative_player_behavior, runtime_discovered`
Selection rationale: initial_objective:Determine where the missing patrol was last seen without granting an NPC impossible knowledge.

Player input (exact):

> Runner, where exactly was the missing patrol last seen?

GM output (exact):

> Tavern Runner says, "No. I cannot answer that from what."

Automated result: `FAIL`
Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 10, "text_preview": "Tavern Runner says, \"No. I cannot answer that from what.\""}, "passed": false, "reason_codes": ["malformed_output:broken_refusal_fragment"], "status": "FAIL"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 17, "gm_terms": ["answer", "cannot", "runner", "says", "tavern", "what"], "player_intent_score": 23, "player_terms": ["exactly", "last", "missing", "patrol", "runner", "seen", "where"], "request_kind": "question"}, "passed": false, "reason_codes": ["intent_addressed:response_malformed_before_intent_can_be_satisfied"], "status": "FAIL"}}`
Diagnostic result: `{"axis_scores": {"direct_answer": 17, "immersion": 23, "logical_escalation": 19, "player_intent": 23}, "passed": true, "rating": "strong", "score": 82}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"diagnostic_quality_rating": "strong", "passed": false, "rating": "strong", "score": 82, "semantic_result": "FAIL"}, "run_valid": true}`
Continuation: `{"continued": true, "next_player_action": "One bounded answer: last reliable location, source, and uncertainty.", "next_selection_reason": "repeat_after_malformed_output"}`
Human review: `HUMAN_REJECTED` - Pressure reproduces both the broken-refusal fragment and a truncated speech construction; mandatory gates detect them.
Evaluator disagreement: `{"calibration_reference": null, "human_status": "HUMAN_REJECTED", "later_evaluator_result": null, "original_semantic_result": "FAIL", "policy_changed": false, "present": false}`

### Severe / Worst Failure

Selection: maximum INVALID_RUN, mandatory-gate failure count, then lowest diagnostic score; source order breaks ties

Example: `reactive:20260918T021838Z:patrol_knowledge_adversarial_seed1701:turn_2`
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/patrol_knowledge_adversarial_seed1701/run.json`
Run / turn: `patrol_knowledge_adversarial_seed1701` / `2`
Input classification: `stress_probe, runtime_discovered`
Selection rationale: unresolved_intent:rephrase

Player input (exact):

> Separate rumor from fact: where were they last seen, and who knows that?

GM output (exact):

> Tavern Runner mutters, the tavern runner begins cautiously, brushing rainwater from their hood,

Automated result: `FAIL`
Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 13, "text_preview": "Tavern Runner mutters, the tavern runner begins cautiously, brushing rainwater from their hood,"}, "passed": false, "reason_codes": ["malformed_output:trailing_comma_speech_construction"], "status": "FAIL"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 17, "gm_terms": ["begins", "brushing", "cautiously", "hood", "mutters", "rainwater", "runner", "tavern"], "player_intent_score": 9, "player_terms": ["fact", "knows", "last", "rumor", "seen", "separate", "they", "where"], "request_kind": "question"}, "passed": false, "reason_codes": ["intent_addressed:response_malformed_before_intent_can_be_satisfied"], "status": "FAIL"}}`
Diagnostic result: `{"axis_scores": {"direct_answer": 17, "immersion": 23, "logical_escalation": 18, "player_intent": 9}, "passed": true, "rating": "acceptable", "score": 67}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"diagnostic_quality_rating": "acceptable", "passed": false, "rating": "acceptable", "score": 67, "semantic_result": "FAIL"}, "run_valid": true}`
Continuation: `{"continued": true, "next_player_action": "One bounded answer: last reliable location, source, and uncertainty.", "next_selection_reason": "repeat_after_malformed_output"}`
Human review: `HUMAN_REJECTED` - Pressure reproduces both the broken-refusal fragment and a truncated speech construction; mandatory gates detect them.
Evaluator disagreement: `{"calibration_reference": null, "human_status": "HUMAN_REJECTED", "later_evaluator_result": null, "original_semantic_result": "FAIL", "policy_changed": false, "present": false}`

### Evaluator Disagreement

Selection: first example with explicit evaluator_disagreement.present=true

Example: `reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_1`
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/notice_observation_adversarial_seed1701/run.json`
Run / turn: `notice_observation_adversarial_seed1701` / `1`
Input classification: `stress_probe, runtime_discovered`
Selection rationale: adversarial_probe:contradiction:prior_semantic_pass

Player input (exact):

> You described the notice as both weathered and legible. Which parts can I actually read?

GM output (exact):

> The guard says, "I do not know enough to answer that."

Automated result: `PASS`
Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 11, "text_preview": "The guard says, \"I do not know enough to answer that.\""}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 17, "gm_terms": ["answer", "enough", "guard", "know", "says"], "player_intent_score": 4, "player_terms": ["actually", "both", "described", "legible", "notice", "parts", "read", "weathered", "which"], "request_kind": "question"}, "passed": true, "reason_codes": [], "status": "PASS"}}`
Diagnostic result: `{"axis_scores": {"direct_answer": 17, "immersion": 23, "logical_escalation": 18, "player_intent": 4}, "passed": true, "rating": "acceptable", "score": 62}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"diagnostic_quality_rating": "acceptable", "passed": true, "rating": "acceptable", "score": 62, "semantic_result": "PASS"}, "run_valid": true}`
Continuation: `{"continued": false, "termination_reason": "legitimate_boundary"}`
Human review: `HUMAN_REJECTED` - The guard claims ignorance about which visible parts of a nearby notice are readable. The response is lexically coherent and receives PASS, but it does not provide the requested observation and introduces an unnecessary speaker boundary.
Evaluator disagreement: `{"calibration_reference": null, "human_status": "HUMAN_REJECTED", "later_evaluator_result": null, "original_semantic_result": "PASS", "policy_changed": false, "present": true}`

### Unexpected / Unclassified Behavior

Selection: first HUMAN_AMBIGUOUS or unexpected_behavior example

Example: `reactive:20260918T021838Z:notice_observation_reactive_seed1701:turn_0`
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/notice_observation_reactive_seed1701/run.json`
Run / turn: `notice_observation_reactive_seed1701` / `0`
Input classification: `representative_player_behavior, runtime_discovered`
Selection rationale: initial_objective:Read the concrete information posted on the gate notice.

Player input (exact):

> I inspect the notice closely and read what is posted.

GM output (exact):

> The notice board lists taxes, curfew rules, and a warning about a missing patrol sharpens when you look again, and ash compact census delays have tightened the eastern caravan choke point still competes for notice.

Automated result: `PASS`
Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 35, "text_preview": "The notice board lists taxes, curfew rules, and a warning about a missing patrol sharpens when you look again, and ash compact census delays have tightened the "}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 23, "gm_terms": ["again", "ash", "board", "caravan", "census", "choke", "compact", "competes", "curfew", "delays", "eastern", "lists", "look", "missing", "notice", "patrol", "point", "rules", "sharpens", "still"], "player_intent_score": 18, "player_terms": ["closely", "inspect", "notice", "posted", "read", "what"], "request_kind": "observation"}, "passed": true, "reason_codes": [], "status": "PASS"}}`
Diagnostic result: `{"axis_scores": {"direct_answer": 23, "immersion": 22, "logical_escalation": 19, "player_intent": 18}, "passed": true, "rating": "strong", "score": 82}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"diagnostic_quality_rating": "strong", "passed": true, "rating": "strong", "score": 82, "semantic_result": "PASS"}, "run_valid": true}`
Continuation: `{"continued": false, "termination_reason": "objective_resolved"}`
Human review: `HUMAN_AMBIGUOUS` - The requested categories are present, but the sentence is grammatically degraded ('a warning ... sharpens') and mixes unrelated pressure. It remains insufficiently clear for an evaluator-policy change.
Evaluator disagreement: `{"calibration_reference": null, "human_status": "HUMAN_AMBIGUOUS", "later_evaluator_result": null, "original_semantic_result": "PASS", "policy_changed": false, "present": false}`

### Stress Probe

Selection: first example labeled stress_probe

Example: `reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_1`
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/notice_observation_adversarial_seed1701/run.json`
Run / turn: `notice_observation_adversarial_seed1701` / `1`
Input classification: `stress_probe, runtime_discovered`
Selection rationale: adversarial_probe:contradiction:prior_semantic_pass

Player input (exact):

> You described the notice as both weathered and legible. Which parts can I actually read?

GM output (exact):

> The guard says, "I do not know enough to answer that."

Automated result: `PASS`
Mandatory gates: `{"malformed_output": {"evidence": {"gm_word_count": 11, "text_preview": "The guard says, \"I do not know enough to answer that.\""}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 17, "gm_terms": ["answer", "enough", "guard", "know", "says"], "player_intent_score": 4, "player_terms": ["actually", "both", "described", "legible", "notice", "parts", "read", "weathered", "which"], "request_kind": "question"}, "passed": true, "reason_codes": [], "status": "PASS"}}`
Diagnostic result: `{"axis_scores": {"direct_answer": 17, "immersion": 23, "logical_escalation": 18, "player_intent": 4}, "passed": true, "rating": "acceptable", "score": 62}`
Runtime validity: `{"dead_turn": {"dead_turn_class": "none", "dead_turn_reason_codes": [], "is_dead_turn": false, "manual_test_valid": true, "validation_playable": true}, "dead_turn_count": 0, "excluded_from_scoring": false, "infra_failure_count": 0, "invalidation_reason": null, "raw_overall": {"diagnostic_quality_rating": "acceptable", "passed": true, "rating": "acceptable", "score": 62, "semantic_result": "PASS"}, "run_valid": true}`
Continuation: `{"continued": false, "termination_reason": "legitimate_boundary"}`
Human review: `HUMAN_REJECTED` - The guard claims ignorance about which visible parts of a nearby notice are readable. The response is lexically coherent and receives PASS, but it does not provide the requested observation and introduces an unnecessary speaker boundary.
Evaluator disagreement: `{"calibration_reference": null, "human_status": "HUMAN_REJECTED", "later_evaluator_result": null, "original_semantic_result": "PASS", "policy_changed": false, "present": true}`

## All Evaluator Disagreements

### reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_1

Source: `artifacts/reactive_adversarial_players/20260918T021838Z/notice_observation_adversarial_seed1701/run.json`
Player classification: `stress_probe, runtime_discovered`
Player (exact): You described the notice as both weathered and legible. Which parts can I actually read?
GM (exact): The guard says, "I do not know enough to answer that."
Original automated result: `PASS`
Original gates: `{"malformed_output": {"evidence": {"gm_word_count": 11, "text_preview": "The guard says, \"I do not know enough to answer that.\""}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 17, "gm_terms": ["answer", "enough", "guard", "know", "says"], "player_intent_score": 4, "player_terms": ["actually", "both", "described", "legible", "notice", "parts", "read", "weathered", "which"], "request_kind": "question"}, "passed": true, "reason_codes": [], "status": "PASS"}}`
Human review: `HUMAN_REJECTED` - The guard claims ignorance about which visible parts of a nearby notice are readable. The response is lexically coherent and receives PASS, but it does not provide the requested observation and introduces an unnecessary speaker boundary.
History: `{"calibration_reference": null, "human_status": "HUMAN_REJECTED", "later_evaluator_result": null, "original_semantic_result": "PASS", "policy_changed": false, "present": true}`

### reactive:20260918T022209Z:patrol_knowledge_adversarial_seed1701:turn_0

Source: `artifacts/reactive_adversarial_players/20260918T022209Z/patrol_knowledge_adversarial_seed1701/run.json`
Player classification: `representative_player_behavior, runtime_discovered`
Player (exact): Runner, where exactly was the missing patrol last seen?
GM (exact): Tavern Runner grimaces. "Not something I can say here."
Original automated result: `FAIL`
Original gates: `{"malformed_output": {"evidence": {"gm_word_count": 9, "text_preview": "Tavern Runner grimaces. \"Not something I can say here.\""}, "passed": true, "reason_codes": [], "status": "PASS"}, "player_intent_addressed": {"evidence": {"direct_answer_score": 17, "gm_terms": ["grimaces", "runner", "say", "something", "tavern"], "player_intent_score": 23, "player_terms": ["exactly", "last", "missing", "patrol", "runner", "seen", "where"], "request_kind": "question"}, "passed": false, "reason_codes": ["intent_addressed:unanswered_intelligible_question"], "status": "FAIL"}}`
Human review: `HUMAN_ACCEPTED` - Tavern Runner grimaces and says 'Not something I can say here.' This is a coherent diegetic refusal, but player_intent_addressed reports FAIL.
History: `{"calibration_reference": null, "human_status": "HUMAN_ACCEPTED", "later_evaluator_result": null, "original_semantic_result": "FAIL", "policy_changed": false, "present": true}`

## Missing Concepts / Future Capabilities

- **player_to_gm_vs_character_utterance_authority**: The notice-legibility probe can be read as player-to-GM clarification rather than character dialogue. Status: RECORDED_NOT_IMPLEMENTED.
- **general_ambiguity_clarification_behavior**: Some confusing or mixed utterances may require clarification rather than confident interpretation. Status: RECORDED_NOT_IMPLEMENTED.

## What This Does Not Prove

- These runs do not prove broad gameplay quality, long-session continuity, hidden-fact consistency, or UI usability.
- Player openings and probes are authored; adversarial probes are useful QA evidence, not representative-human-play evidence.
- The deterministic player does not make the configured AI-GM deterministic.
- Human review covers selected interactions, not every PASS in every validation lane.

## Review Notes

Human review is recorded beside automated evaluation and never rewrites the historical result.
The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.
