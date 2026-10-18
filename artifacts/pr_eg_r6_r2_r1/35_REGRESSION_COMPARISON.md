# 35 — Regression Comparison

{
  "baseline_passed": 383,
  "baseline_failed": 6,
  "final_passed": 431,
  "final_failed": 5,
  "added_cases": 47,
  "inherited_failures": [
    "tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C01]",
    "tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C02]",
    "tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C03]",
    "tests.test_pr_eg_r3_r1_expression_semantics::test_t19_t23_answer_sufficiency_and_refusal",
    "tests.test_social_question_relevance_answer_selection::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance"
  ],
  "new_failures": [],
  "baseline_failures_now_passing": [
    "tests.test_pr_eg_r2c_r2_reference_eligibility::test_continuity_classes[T19-The street beyond the gate is the north road.]"
  ]
}

The expanded pre-edit baseline has six failures; final five are inherited, none newly failed. One previously failing T19 test passes in the final selection; no targeted repair to that test was made and no broad fix is claimed. Full repository suite was not run; selection follows the requested R2C/R3/R3-R1/R4-R1/R6/R6-R1/provenance/R6-R2 stack plus answer selection.
