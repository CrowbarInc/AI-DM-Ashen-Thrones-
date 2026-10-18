# 32 Acceptance Gates

[
  {
    "gate": "Entity roles",
    "threshold": 0.95,
    "rate": 0.4444444444444444,
    "status": "FAIL",
    "method": "local implementing-agent assessment"
  },
  {
    "gate": "Addressee",
    "threshold": 0.95,
    "rate": 0.7049180327868853,
    "status": "FAIL",
    "method": "local implementing-agent assessment"
  },
  {
    "gate": "Relationship",
    "threshold": 0.95,
    "rate": 0.6293103448275862,
    "status": "FAIL",
    "method": "local implementing-agent assessment"
  },
  {
    "gate": "Relevance",
    "threshold": 0.95,
    "rate": 0.6311475409836066,
    "status": "FAIL",
    "method": "local implementing-agent assessment"
  },
  {
    "gate": "Sufficiency",
    "threshold": 0.9,
    "rate": 0.6229508196721312,
    "status": "FAIL",
    "method": "local implementing-agent assessment"
  },
  {
    "gate": "Corrections",
    "threshold": 0.9,
    "rate": 0.0,
    "status": "FAIL",
    "method": "local implementing-agent assessment"
  },
  {
    "gate": "Follow-ups",
    "threshold": 0.9,
    "rate": 0.0,
    "status": "FAIL",
    "method": "local implementing-agent assessment"
  },
  {
    "gate": "Clarification loops",
    "status": "FAIL",
    "evidence": "Repeated Which information / Which person loops in labeled quill and roles conversations."
  },
  {
    "gate": "Authorization",
    "status": "PASS",
    "limit": "Restricted-value and route sentinel checks plus preserved provenance tests, not proof of every possible leak."
  },
  {
    "gate": "State",
    "status": "PASS",
    "limit": "Selected canonical projection (NPC topics, factions, location, HP, combat). Full arbitrary-state nonmutation not proven."
  },
  {
    "gate": "Discovery",
    "status": "PASS",
    "limit": "Restricted sentinel scan, not exhaustive semantic detection."
  },
  {
    "gate": "Delivery",
    "status": "PASS"
  },
  {
    "gate": "Baseline improvement",
    "status": "PARTIAL",
    "evidence": "Matched raw transcripts show addressee/object/paraphrase improvements and continuity regressions; stochastic variation not causal proof."
  },
  {
    "gate": "Holdouts",
    "status": "FAIL",
    "evidence": "Frozen cases expose predicate/argument and correction limitations. See holdout_results.json."
  },
  {
    "gate": "Regression",
    "status": "PASS",
    "evidence": {
      "baseline_passed": 347,
      "baseline_failed": 5,
      "final_passed": 384,
      "final_failed": 5,
      "new_failures": [],
      "inherited_failures": [
        "tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C01]",
        "tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C02]",
        "tests.test_pr_eg_r2c_r2_reference_eligibility::test_independent_clarification_holdout[C03]",
        "tests.test_pr_eg_r3_r1_expression_semantics::test_t19_t23_answer_sufficiency_and_refusal",
        "tests.test_social_question_relevance_answer_selection::test_immutable_preseal_preserves_selected_authored_answer_over_ignorance"
      ],
      "added_cases": 37
    }
  },
  {
    "gate": "Performance",
    "status": "PASS",
    "evidence": {
      "turns": 122,
      "conversations": 9,
      "calls": 182,
      "calls_per_turn": 1.4918032786885247,
      "input_tokens_per_turn": {
        "mean": 1538.9098360655737,
        "median": 1586.5,
        "p95": 1759,
        "maximum": 1816
      },
      "output_tokens_per_turn": {
        "mean": 257.3524590163934,
        "median": 232.5,
        "p95": 411,
        "maximum": 527
      },
      "latency_ms": {
        "mean": 2913.7559926240383,
        "median": 2952.0244000013918,
        "p95": 4128.386500000488,
        "maximum": 9563.662700005807
      },
      "retry_calls": 0,
      "planning": {
        "calls": 116,
        "input_tokens_per_call": {
          "mean": 1470.0862068965516,
          "median": 1495.0,
          "p95": 1627,
          "maximum": 1646
        },
        "latency_ms_per_call": {
          "mean": 2375.537405172414,
          "median": 2153.2205,
          "p95": 3529.207,
          "maximum": 9519.731
        }
      },
      "nonplanning_input_tokens_per_call": {
        "mean": 260.8636363636364,
        "median": 161.0,
        "p95": 1756,
        "maximum": 1816
      },
      "total_input_tokens": 187747,
      "total_output_tokens": 31397,
      "note": "Engine calls only; development pilots, matched runs and scoring excluded. Currency cost not estimated; actual token consumption is reported. Null usage is not asserted to be measured zero."
    }
  },
  {
    "gate": "Fresh provider",
    "status": "PASS",
    "evidence": {
      "status": "completed",
      "turns": 122,
      "conversations": 9,
      "source_sha256": {
        "game/unified_semantic_planning.py": "37efde83243ee249756dc2a3fa109321085b209888b48fb4370a11fcae1624cb",
        "game/semantic_correspondence.py": "c387a521557ba96a5befd3335d13ad7ce44bfc6406af8e8143f2ccea45847b78"
      },
      "composition": "119 primary turns + 3 supplemental final-code turns; no turn replaced. Separate original files retained."
    }
  }
]
