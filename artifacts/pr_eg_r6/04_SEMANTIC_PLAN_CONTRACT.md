# 04 — Semantic Plan Contract

Plan version `pr-eg-r6.1`.

Fields: `conversational_act`, `addressee_reference`, `addressee_id`, `requested_subject`, `requested_relationship`, `question_text`, `correction_of_prior_question`, `correction_target`, `referenced_prior_proposition`, `candidate_source_ids`, `proposed_coverage`, `ambiguity_type`, `clarification_needed`, `interpretation_confidence`.

Host-added fields after validation: `locked`, `answer_sufficiency`, `response_kind`, `selected_source_ids`, `rejected_source_ids`, `authorized_text`, `host_line`, `reason`, `epistemic_status`, `canonical=false`.

Acts are `information_question`, `correction`, and `follow_up`. Ambiguity is empty, `addressee`, `subject`, `proposition`, or `correction_target`. Coverage is `direct`, `partial`, `unrelated`, or `unknown`.

Forbidden proposal fields (`canonical_fact`, `state_update`, `reward`, `promise`, `world_fact`, `disclosure_granted`, `execute_action`, `mechanical_action`, `time_advance`) reject the plan.

The relationship form is `predicate(argument)`. A bare predicate is combined with `requested_subject`. A name word inside an unparenthesized phrase becomes the predicate. The host stamps `plan_version`; a model-written version string is not authority.

Delivered history stores a compact copy of the locked plan. That is continuation memory, not a second fact ledger.
