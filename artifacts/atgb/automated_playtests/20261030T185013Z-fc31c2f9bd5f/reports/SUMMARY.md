# ASHEN THRONES — AUTOMATED PLAYTEST

Scenario: FiveTurnGameplay
Mode: Deterministic
Repository revision: b012c3d7e5887fdfb09d10bb9cc0f0220de09df9; dirty=True
Overall: **INCONCLUSIVE**
Provider attempts: 2
Usage (input/output/total): 40/20/60
Opening: True
Structural validation: False
Provider completion: {'provider_status': 'completed', 'provider_finish_reason': None, 'provider_output_limit_exhausted': None, 'classification': 'json_parse_failure'}
Semantic validation: initial_generation
State integrity: True
UI: NOT_TESTED
Primary observed failure: {'category': 'json_parsing_failure', 'stage': 'parsing', 'evidence_record': 'diagnostics/provider_usage.jsonl', 'record_index': 13, 'field': 'json_parsing_succeeded', 'observed_value': False, 'source': 'game/provider_budget.py', 'root_cause': 'Not established', 'inferred': False}
Root cause: Not established.

Evidence: diagnostics/provider_usage.jsonl; baseline/; after/; reports/result.json.
Remaining uncertainty: Rendered UI, live adequacy, and gameplay quality not established by deterministic API execution; Evidence export failed: ValueError
Recommended investigation: inspect the first evidenced failing stage; external review before any live invocation.
Evidence ZIP: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\atgb\automated_playtests\20261030T185013Z-fc31c2f9bd5f\evidence\evidence.zip
