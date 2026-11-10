# ASHEN THRONES — AUTOMATED PLAYTEST

Scenario: FiveTurnGameplay
Mode: Deterministic
Repository revision: d40f1ed198236c604085f1c842ead267a8104ce2; dirty=True
Overall: **FAIL**
Provider attempts: 1
Usage (input/output/total): 20/10/30
Opening: False
Structural validation: False
Provider completion: {'provider_status': 'completed', 'provider_finish_reason': None, 'provider_output_limit_exhausted': None, 'classification': 'json_parse_failure'}
Semantic validation: safe_nonresolution
State integrity: True
UI: NOT_TESTED
Primary observed failure: {'category': 'json_parsing_failure', 'stage': 'parsing', 'evidence_record': 'diagnostics/provider_usage.jsonl', 'record_index': 4, 'field': 'json_parsing_succeeded', 'observed_value': False, 'source': 'game/provider_budget.py', 'root_cause': 'Not established', 'inferred': False}
Root cause: Not established.

Evidence: diagnostics/provider_usage.jsonl; baseline/; after/; reports/result.json.
Remaining uncertainty: Bounded provider response unavailable (disabled, capture failed, or response unparsed); Rendered UI, live adequacy, and gameplay quality not established by deterministic API execution
Recommended investigation: inspect the first evidenced failing stage; external review before any live invocation.
Evidence ZIP: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\atgb\automated_playtests\20261101T212904Z-fc7b240fab67\evidence\evidence.zip
