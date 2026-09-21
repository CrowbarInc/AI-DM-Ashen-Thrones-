# Reactive and Adversarial Player Campaign

```json
{
  "artifact_version": 1,
  "total_runs": 6,
  "valid_runs": 6,
  "invalid_runs": 0,
  "total_turns": 19,
  "semantic_result_counts": {
    "FAIL": 13,
    "PASS": 6
  },
  "mandatory_gate_failure_counts": {
    "malformed_output": 4,
    "player_intent_addressed": 13
  },
  "diagnostic_only_warnings": 0,
  "failure_classification_counts": {
    "A_KNOWN_EVALUATOR_DETECTED_FAILURE": 13,
    "E_AMBIGUOUS_HUMAN_REVIEW_REQUIRED": 6
  },
  "failure_clusters": {
    "malformed_output": [
      "patrol_knowledge:adversarial:seed=1701",
      "patrol_knowledge:reactive:seed=1701"
    ],
    "player_intent_addressed": [
      "patrol_knowledge:adversarial:seed=1701",
      "patrol_knowledge:reactive:seed=1701",
      "watch_command:adversarial:seed=1701",
      "watch_command:reactive:seed=1701"
    ]
  },
  "failure_references": [
    {
      "run": "watch_command:reactive:seed=1701",
      "turn_index": 0,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "watch_command:reactive:seed=1701",
      "turn_index": 1,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "watch_command:reactive:seed=1701",
      "turn_index": 2,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "watch_command:reactive:seed=1701",
      "turn_index": 3,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "watch_command:adversarial:seed=1701",
      "turn_index": 0,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "watch_command:adversarial:seed=1701",
      "turn_index": 1,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "watch_command:adversarial:seed=1701",
      "turn_index": 2,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "watch_command:adversarial:seed=1701",
      "turn_index": 3,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "patrol_knowledge:reactive:seed=1701",
      "turn_index": 0,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "patrol_knowledge:adversarial:seed=1701",
      "turn_index": 0,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "patrol_knowledge:adversarial:seed=1701",
      "turn_index": 2,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "patrol_knowledge:adversarial:seed=1701",
      "turn_index": 3,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    },
    {
      "run": "patrol_knowledge:adversarial:seed=1701",
      "turn_index": 4,
      "semantic_result": "FAIL",
      "classification": "A_KNOWN_EVALUATOR_DETECTED_FAILURE"
    }
  ],
  "novel_failures_not_in_calibration_corpus": [],
  "human_review_note": "PASS turns remain review candidates; probable evaluator misses and false positives are not inferred automatically or converted into semantic policy.",
  "campaign_id": "20260918T021417Z",
  "run_artifact_paths": [
    "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\reactive_adversarial_players\\20260918T021417Z\\watch_command_reactive_seed1701\\run.json",
    "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\reactive_adversarial_players\\20260918T021417Z\\watch_command_adversarial_seed1701\\run.json",
    "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\reactive_adversarial_players\\20260918T021417Z\\notice_observation_reactive_seed1701\\run.json",
    "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\reactive_adversarial_players\\20260918T021417Z\\notice_observation_adversarial_seed1701\\run.json",
    "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\reactive_adversarial_players\\20260918T021417Z\\patrol_knowledge_reactive_seed1701\\run.json",
    "C:\\Users\\Master Mandalcio\\Documents\\Tabletop Gaming\\AI Dungeon Master\\ashen_thrones_ai_gm\\artifacts\\reactive_adversarial_players\\20260918T021417Z\\patrol_knowledge_adversarial_seed1701\\run.json"
  ]
}
```
