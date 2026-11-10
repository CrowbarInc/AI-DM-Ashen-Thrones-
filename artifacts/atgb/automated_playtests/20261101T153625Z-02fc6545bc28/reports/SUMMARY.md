# ASHEN THRONES — AUTOMATED PLAYTEST

Scenario: FiveTurnGameplay
Mode: Live
Repository revision: d40f1ed198236c604085f1c842ead267a8104ce2; dirty=True
Overall: **FAIL**
Provider attempts: 1
Usage (input/output/total): 26986/2050/29036
Opening: False
Structural validation: False
Provider completion: {'provider_status': 'completed', 'provider_finish_reason': None, 'provider_output_limit_exhausted': None, 'classification': 'missing_structured_envelope'}
Semantic validation: safe_nonresolution
State integrity: True
UI: NOT_TESTED
Primary observed failure: {'category': 'structured_envelope_failure', 'stage': 'structure', 'evidence_record': 'diagnostics/provider_usage.jsonl', 'record_index': 4, 'field': 'classification', 'observed_value': 'missing_structured_envelope', 'source': 'game/provider_budget.py', 'root_cause': 'Not established', 'inferred': False}
Root cause: Not established.

Evidence: diagnostics/provider_usage.jsonl; baseline/; after/; reports/result.json.
Remaining uncertainty: Rendered UI, live adequacy, and gameplay quality not established by deterministic API execution
Recommended investigation: inspect the first evidenced failing stage; external review before any live invocation.
Evidence ZIP: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\atgb\automated_playtests\20261101T153625Z-02fc6545bc28\evidence\evidence.zip
