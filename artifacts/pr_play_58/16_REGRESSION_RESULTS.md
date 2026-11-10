# Regression evidence

{
  "suite_results": {
    "focused": {
      "label": "focused",
      "collected": 604,
      "failed": 3,
      "errors": 0,
      "skipped": 0,
      "passed": 601,
      "exit_code": 1,
      "failed_nodeids": [
        "tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution",
        "tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues",
        "tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues"
      ],
      "failure_messages": [
        {
          "nodeid": "tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution",
          "message": "assert False"
        },
        {
          "nodeid": "tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues",
          "message": "assert set()\n +  where set() = get_all_known_clue_ids({})"
        },
        {
          "nodeid": "tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues",
          "message": "assert set()\n +  where set() = get_all_known_clue_ids({})"
        }
      ],
      "command": [
        "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
        "-m",
        "pytest",
        "tests/test_pr_play_57_integrated_narration.py",
        "tests/test_pr_play_58_semantic_coverage.py",
        "tests/test_pr_play_55_discovery_claims.py",
        "tests/test_pr_play_54_consequential_validation.py",
        "tests/test_pr_play_53_quarantined_live.py",
        "tests/test_pr_play_52_quarantined_integration.py",
        "tests/test_pr_play_42_evidence_boundaries.py",
        "tests/test_pr_play_51_geography_grounding.py",
        "tests/test_pr_play_49_anchored_narration.py",
        "tests/test_pr_play_47_controlled_renderer.py",
        "tests/test_pr_play_45_narration_authority.py",
        "tests/test_pr_play_46_mechanical_boundary.py",
        "tests/test_pr_play_44_information_delivery.py",
        "tests/test_pr_bu_lexical_scope.py",
        "tests/test_provider_accounting_integrity.py",
        "tests/test_pr_bw_narration_only_envelope.py",
        "tests/test_diegetic_fallback_narration.py",
        "tests/test_narration_state_consistency.py",
        "--tb=line",
        "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_58\\focused_final.xml",
        "--basetemp",
        "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\pr_play_58_focused_17432"
      ],
      "provider_calls": "disabled",
      "preexisting_failures_seen": [
        "tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution",
        "tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues",
        "tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues"
      ],
      "new_failures": []
    },
    "holdout": {
      "label": "holdout",
      "collected": 1,
      "failed": 0,
      "errors": 0,
      "skipped": 0,
      "passed": 1,
      "exit_code": 0,
      "failed_nodeids": [],
      "failure_messages": [],
      "command": [
        "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
        "-m",
        "pytest",
        "tests/test_pr_play_55_holdout.py",
        "--tb=line",
        "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_58\\holdout_final.xml",
        "--basetemp",
        "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\pr_play_58_holdout_17432"
      ],
      "provider_calls": "disabled"
    },
    "broader_hard_validation": {
      "label": "broader_hard_validation",
      "collected": 9,
      "failed": 9,
      "errors": 0,
      "skipped": 0,
      "passed": 0,
      "exit_code": 1,
      "failed_nodeids": [
        "tests.test_pr_cx_authority_assurance::test_pr_cx_rejects_inherited_objective_authority_violations[biography-The guard captain was born in Blackharbor and served for twenty years.-biography]",
        "tests.test_pr_cx_authority_assurance::test_pr_cx_rejects_inherited_objective_authority_violations[geography-The old milestone lies east beyond the trading crossroads.-geography]",
        "tests.test_pr_cx_authority_assurance::test_pr_cx_rejects_inherited_objective_authority_violations[hidden_information-A secret tunnel runs beneath the gate into the keep.-hidden_information]",
        "tests.test_pr_cx_authority_assurance::test_pr_cx_rejects_inherited_objective_authority_violations[npc_action-The captain unlocks the gate and lets you pass.-npc_action]",
        "tests.test_pr_cx_authority_assurance::test_pr_cx_rejects_inherited_objective_authority_violations[discovery-You discover a hidden map beneath the notice board.-discovery]",
        "tests.test_pr_cx_authority_assurance::test_pr_cx_preserves_harmless_dialogue_and_grounded_observation[preference-The guard captain says, \"I prefer a dry watch.\"]",
        "tests.test_pr_cx_authority_assurance::test_pr_cx_preserves_harmless_dialogue_and_grounded_observation[opinion-The guard captain says, \"I like the square best after rain.\"]",
        "tests.test_pr_cx_authority_assurance::test_pr_cx_preserves_harmless_dialogue_and_grounded_observation[incidental_characterization-The guard captain shrugs and nods.]",
        "tests.test_pr_cx_authority_assurance::test_pr_cx_preserves_harmless_dialogue_and_grounded_observation[grounded_observation-A notice board lists new taxes, curfews, and a posted warning about a missing patrol.]"
      ],
      "failure_messages": [
        {
          "nodeid": "tests.test_pr_cx_authority_assurance::test_pr_cx_rejects_inherited_objective_authority_violations[biography-The guard captain was born in Blackharbor and served for twenty years.-biography]",
          "message": "KeyError: 'hard_validation_attempt_1'"
        },
        {
          "nodeid": "tests.test_pr_cx_authority_assurance::test_pr_cx_rejects_inherited_objective_authority_violations[geography-The old milestone lies east beyond the trading crossroads.-geography]",
          "message": "KeyError: 'hard_validation_attempt_1'"
        },
        {
          "nodeid": "tests.test_pr_cx_authority_assurance::test_pr_cx_rejects_inherited_objective_authority_violations[hidden_information-A secret tunnel runs beneath the gate into the keep.-hidden_information]",
          "message": "KeyError: 'hard_validation_attempt_1'"
        },
        {
          "nodeid": "tests.test_pr_cx_authority_assurance::test_pr_cx_rejects_inherited_objective_authority_violations[npc_action-The captain unlocks the gate and lets you pass.-npc_action]",
          "message": "KeyError: 'hard_validation_attempt_1'"
        },
        {
          "nodeid": "tests.test_pr_cx_authority_assurance::test_pr_cx_rejects_inherited_objective_authority_violations[discovery-You discover a hidden map beneath the notice board.-discovery]",
          "message": "KeyError: 'hard_validation_attempt_1'"
        },
        {
          "nodeid": "tests.test_pr_cx_authority_assurance::test_pr_cx_preserves_harmless_dialogue_and_grounded_observation[preference-The guard captain says, \"I prefer a dry watch.\"]",
          "message": "KeyError: 'hard_validation_attempt_1'"
        },
        {
          "nodeid": "tests.test_pr_cx_authority_assurance::test_pr_cx_preserves_harmless_dialogue_and_grounded_observation[opinion-The guard captain says, \"I like the square best after rain.\"]",
          "message": "KeyError: 'hard_validation_attempt_1'"
        },
        {
          "nodeid": "tests.test_pr_cx_authority_assurance::test_pr_cx_preserves_harmless_dialogue_and_grounded_observation[incidental_characterization-The guard captain shrugs and nods.]",
          "message": "KeyError: 'hard_validation_attempt_1'"
        },
        {
          "nodeid": "tests.test_pr_cx_authority_assurance::test_pr_cx_preserves_harmless_dialogue_and_grounded_observation[grounded_observation-A notice board lists new taxes, curfews, and a posted warning about a missing patrol.]",
          "message": "KeyError: 'hard_validation_attempt_1'"
        }
      ],
      "command": [
        "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
        "-m",
        "pytest",
        "tests/test_pr_cx_authority_assurance.py",
        "--tb=line",
        "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_58\\broader_hard_validation_final.xml",
        "--basetemp",
        "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\pr_play_58_broader_hard_validation_17432"
      ],
      "provider_calls": "disabled"
    },
    "restored": [
      "artifacts/pr_play_49/evidence_performance.json",
      "artifacts/pr_play_47/evidence_performance.json",
      "artifacts/pr_play_52/integration_results.json",
      "artifacts/pr_play_55/evaluation.json"
    ],
    "known_failures_not_modified": [
      "tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues",
      "tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues",
      "tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution"
    ],
    "note": "The holdout test writes artifacts/pr_play_55/evaluation.json. That file is restored after the run. Broader PR-BR continuation files were not all executed in this command."
  },
  "final_frozen_source_checks": {
    "label": "final_frozen_source",
    "collected": 204,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "passed": 204,
    "exit_code": 0,
    "failed_nodeids": [],
    "failure_messages": [],
    "command": [
      "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\.venv\\Scripts\\python.exe",
      "-m",
      "pytest",
      "tests/test_pr_play_58_semantic_coverage.py",
      "tests/test_pr_play_57_integrated_narration.py",
      "tests/test_pr_play_55_discovery_claims.py",
      "tests/test_pr_play_54_consequential_validation.py",
      "tests/test_state_authority.py",
      "--tb=line",
      "--junitxml=C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\pr_play_58\\final_frozen_source_final.xml",
      "--basetemp",
      "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\development\\tmp\\pr_play_58_final_frozen_source_33396"
    ],
    "provider_calls": "disabled"
  }
}

The focused lane reuses PR57's selection plus new PR58 controls, with no provider calls and temporary stores. PR56 has no separate test module: its prelude/quarantine behavior is exercised by PR49/52/53 and PR55 paths. PR55 holdout wrapper ran separately and its historical output artifact was restored. Nine broader authority-assurance cases retain hard_validation_attempt_1 metadata failures. Full repository suite, live runtime and ATGB gameplay benchmark were not executed. No assertions were weakened.

The first broad lane began before the last route/status normalization adjustment. Final frozen-source focused checks rerun the changed coverage and integrated HTTP module; unchanged broader modules retain the first lane's evidence. This timing limit is explicit and is not a full-suite claim. Initial development failures are preserved in development_initial.json.
