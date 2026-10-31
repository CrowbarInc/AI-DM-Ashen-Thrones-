# ASHEN THRONES — AUTOMATED PLAYTEST

Scenario: FiveTurnGameplay
Mode: Live
Repository revision: b012c3d7e5887fdfb09d10bb9cc0f0220de09df9; dirty=True
Overall: **INCONCLUSIVE**
Provider attempts: 1
Usage (input/output/total): 26593/1655/28248
Opening: True
Structural validation: True
Provider completion: {'provider_status': 'completed', 'provider_finish_reason': None, 'provider_output_limit_exhausted': None, 'classification': 'accepted_structured_response'}
Semantic validation: initial_generation
State integrity: False
UI: NOT_TESTED
Primary observed failure: {'category': 'state_integrity_violation', 'stage': 'state', 'evidence_record': 'reports/result.json', 'record_index': None, 'field': 'state_comparison.integrity', 'observed_value': False, 'source': 'docs/state_authority_model.md', 'root_cause': 'Not established', 'inferred': False}
Root cause: Not established.

Evidence: diagnostics/provider_usage.jsonl; baseline/; after/; reports/result.json.
Remaining uncertainty: Rendered UI, live adequacy, and gameplay quality not established by deterministic API execution
Recommended investigation: inspect the first evidenced failing stage; external review before any live invocation.
Evidence ZIP: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\atgb\automated_playtests\20261030T191257Z-ecc1b6062bdc\evidence\evidence.zip
