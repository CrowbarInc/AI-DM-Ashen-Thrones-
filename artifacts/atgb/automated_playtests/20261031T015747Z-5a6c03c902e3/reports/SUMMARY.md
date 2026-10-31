# ASHEN THRONES — AUTOMATED PLAYTEST

Scenario: FiveTurnGameplay
Mode: Live
Repository revision: b012c3d7e5887fdfb09d10bb9cc0f0220de09df9; dirty=True
Overall: **FAIL**
Provider attempts: 1
Usage (input/output/total): 26593/1352/27945
Opening: False
Structural validation: True
Provider completion: {'provider_status': 'completed', 'provider_finish_reason': None, 'provider_output_limit_exhausted': None, 'classification': 'accepted_structured_response'}
Semantic validation: safe_nonresolution
State integrity: True
UI: NOT_TESTED
Primary observed failure: {'category': 'semantic_validation_failure', 'stage': 'semantic', 'evidence_record': 'diagnostics/provider_usage.jsonl', 'record_index': 9, 'field': 'semantic_reasons', 'observed_value': ['unauthorized_resolution_decision_fact'], 'source': 'game.immutable_valid_response.run_preserve_if_valid._finish', 'root_cause': 'Not established', 'inferred': False}
Root cause: Not established.

Evidence: diagnostics/provider_usage.jsonl; baseline/; after/; reports/result.json.
Remaining uncertainty: Rendered UI, live adequacy, and gameplay quality not established by deterministic API execution
Recommended investigation: inspect the first evidenced failing stage; external review before any live invocation.
Evidence ZIP: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\atgb\automated_playtests\20261031T015747Z-5a6c03c902e3\evidence\evidence.zip
