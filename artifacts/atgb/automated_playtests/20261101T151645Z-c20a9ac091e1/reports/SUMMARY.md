# ASHEN THRONES — AUTOMATED PLAYTEST

Scenario: CampaignOpening
Mode: Deterministic
Repository revision: d40f1ed198236c604085f1c842ead267a8104ce2; dirty=True
Overall: **FAIL**
Provider attempts: 0
Usage (input/output/total): 0/0/0
Opening: False
Structural validation: None
Provider completion: None
Semantic validation: initial_generation
State integrity: True
UI: NOT_TESTED
Primary observed failure: {'category': 'provider_admission_rejection', 'stage': 'admission', 'evidence_record': 'diagnostics/provider_usage.jsonl', 'record_index': 1, 'field': 'refusal', 'observed_value': 'input-token ceiling', 'source': 'game/provider_budget.py', 'root_cause': 'Not established', 'inferred': False}
Root cause: Not established.

Evidence: diagnostics/provider_usage.jsonl; baseline/; after/; reports/result.json.
Remaining uncertainty: Bounded provider response unavailable (disabled, capture failed, or response unparsed); Required provider/acceptance diagnostic artifact unavailable; Rendered UI, live adequacy, and gameplay quality not established by deterministic API execution
Recommended investigation: inspect the first evidenced failing stage; external review before any live invocation.
Evidence ZIP: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\atgb\automated_playtests\20261101T151645Z-c20a9ac091e1\evidence\evidence.zip
