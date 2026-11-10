# ASHEN THRONES — AUTOMATED PLAYTEST

Scenario: CampaignOpening
Mode: Deterministic
Repository revision: d40f1ed198236c604085f1c842ead267a8104ce2; dirty=True
Overall: **FAIL**
Provider attempts: 1
Usage (input/output/total): 20/10/30
Opening: False
Structural validation: True
Provider completion: {'provider_status': 'incomplete', 'provider_finish_reason': None, 'provider_output_limit_exhausted': None, 'classification': 'provider_not_completed'}
Semantic validation: safe_nonresolution
State integrity: True
UI: NOT_TESTED
Primary observed failure: {'category': 'provider_incomplete_response', 'stage': 'provider', 'evidence_record': 'diagnostics/provider_usage.jsonl', 'record_index': 4, 'field': 'provider_status', 'observed_value': 'incomplete', 'source': 'game/provider_budget.py', 'root_cause': 'Not established', 'inferred': False}
Root cause: Not established.

Evidence: diagnostics/provider_usage.jsonl; baseline/; after/; reports/result.json.
Remaining uncertainty: Rendered UI, live adequacy, and gameplay quality not established by deterministic API execution
Recommended investigation: inspect the first evidenced failing stage; external review before any live invocation.
Evidence ZIP: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\atgb\automated_playtests\20261101T184213Z-3ae4f79c1805\evidence\evidence.zip
