# 14 FAILURE INJECTION

12/12 assessed HTTP publication faults pass: provider unavailable, timeout, empty, malformed, FAIL, REVIEW_REQUIRED, VALIDATION_ERROR, unauthorized discovery, persistent consequence, item acquisition, missing mandatory disclosure and hidden identifier disclosure.

Each uses deterministic fallback, preserves mandatory route text, validates the fallback, matches the feature-disabled resolver/authority control, and accepts a subsequent repeat action. No fault calls the provider.

The original harness's `stable_authority` boolean is false because it incorrectly assumed npc_runtime could not be initialized on the first resolver turn. Exact raw assertions remain in `failure_injection.json`; `failure_injection_assessed.json` explains the correction. Complete bounded authority equals the disabled control in all cases, including the initialized NPC records and normal time-pressure tick. No production change was made to improve this assessment.
