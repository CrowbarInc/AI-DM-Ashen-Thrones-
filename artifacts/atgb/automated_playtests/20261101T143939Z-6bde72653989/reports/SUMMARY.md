# ASHEN THRONES — AUTOMATED PLAYTEST

Scenario: CampaignOpening
Mode: Deterministic
Repository revision: d40f1ed198236c604085f1c842ead267a8104ce2; dirty=True
Overall: **FAIL**
Provider attempts: 1
Usage (input/output/total): 20/10/30
Opening: False
Structural validation: True
Provider completion: {'provider_status': 'completed', 'provider_finish_reason': None, 'provider_output_limit_exhausted': None, 'classification': 'accepted_structured_response'}
Semantic validation: initial_generation
State integrity: True
UI: NOT_TESTED
Primary observed failure: {'category': 'opening_acceptance_failure', 'stage': 'acceptance', 'evidence_record': 'diagnostics/provider_usage.jsonl', 'record_index': 9, 'field': 'rejection_reason', 'observed_value': 'generic_information_request_fallback', 'source': 'game.immutable_valid_response.run_preserve_if_valid._finish', 'root_cause': 'Not established', 'inferred': False}
Root cause: Not established.

Evidence: diagnostics/provider_usage.jsonl; baseline/; after/; reports/result.json.
Remaining uncertainty: Rendered UI, live adequacy, and gameplay quality not established by deterministic API execution
Recommended investigation: inspect the first evidenced failing stage; external review before any live invocation.
Evidence ZIP: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\atgb\automated_playtests\20261101T143939Z-6bde72653989\evidence\evidence.zip
