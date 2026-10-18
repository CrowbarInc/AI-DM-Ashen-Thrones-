# 37 — Regression Comparison

{
  "baseline_passed": 431,
  "baseline_failed": 5,
  "passed": 485,
  "failed": 19,
  "new_cases": 68,
  "inherited_failures": [
    "tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C01]",
    "tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C02]",
    "tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C03]",
    "tests.test_pr_eg_r3_r1_expression_semantics::test_t19_t23_answer_sufficiency_and_refusal",
    "tests.test_social_question_relevance_answer_selection::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance"
  ],
  "new_failures": [
    "tests.test_pr_eg_r6_r2_grounding::test_forged_authority_or_entity_rejected[change0]",
    "tests.test_pr_eg_r6_r2_grounding::test_forged_authority_or_entity_rejected[change1]",
    "tests.test_pr_eg_r6_r2_grounding::test_forged_authority_or_entity_rejected[change2]",
    "tests.test_pr_eg_r6_r2_grounding::test_bad_prior_target_cannot_launder_history[correction]",
    "tests.test_pr_eg_r6_r2_grounding::test_bad_prior_target_cannot_launder_history[follow_up]",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[forged]",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[cross_conversation]",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[stale]",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[speaker]",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[field]",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[operation]",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[unwitnessed]",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[substitution]",
    "tests.test_pr_eg_r6_r2_r1_referents::test_unqualified_historical_id_cannot_override_focus"
  ],
  "new_failure_attribution": {
    "tests.test_pr_eg_r6_r2_grounding::test_forged_authority_or_entity_rejected[change0]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_grounding::test_forged_authority_or_entity_rejected[change1]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_grounding::test_forged_authority_or_entity_rejected[change2]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_grounding::test_bad_prior_target_cannot_launder_history[correction]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_grounding::test_bad_prior_target_cannot_launder_history[follow_up]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[forged]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[cross_conversation]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[stale]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[speaker]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[field]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[operation]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[unwitnessed]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_r1_referents::test_untrusted_operations_fail_closed_without_losing_focus[substitution]": "Intentional malformed-provider disposition change: safe unknown replaces player clarification. Authorization rejection and noncommit remain intact.",
    "tests.test_pr_eg_r6_r2_r1_referents::test_unqualified_historical_id_cannot_override_focus": "Design choice: reject an unqualified historical-ID proposal rather than silently substitute active focus. This is stricter than required by the no-legacy-topic-override invariant; it can reduce recoverable continuity and requires external review."
  }
}

No existing test was rewritten. The fourteen new failures are explained contract-expectation differences, not reported as passing tests. Full repository suite was not run.
