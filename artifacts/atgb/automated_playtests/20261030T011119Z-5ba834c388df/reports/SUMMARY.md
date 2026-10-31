# ASHEN THRONES — AUTOMATED PLAYTEST

Scenario: CampaignOpening
Mode: Deterministic
Repository revision: b012c3d7e5887fdfb09d10bb9cc0f0220de09df9; dirty=True
Overall: **FAIL**
Provider attempts: 1
Usage (input/output/total): None/None/None
Opening: False
Structural validation: None
Semantic validation: initial_generation
State integrity: False
UI: NOT_TESTED
Primary observed failure: {'category': 'state_integrity_violation', 'stage': 'state', 'evidence_record': 'reports/result.json', 'record_index': None, 'field': 'state_comparison.integrity', 'observed_value': False, 'source': 'docs/state_authority_model.md', 'root_cause': 'Not established', 'inferred': False}
Root cause: Not established.

Evidence: diagnostics/provider_usage.jsonl; baseline/; after/; reports/result.json.
Remaining uncertainty: Bounded provider response unavailable (disabled, capture failed, or response unparsed); Rendered UI, live adequacy, and gameplay quality not established by deterministic API execution
Recommended investigation: inspect the first evidenced failing stage; external review before any live invocation.
Evidence ZIP: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\artifacts\atgb\automated_playtests\20261030T011119Z-5ba834c388df\evidence\evidence.zip
