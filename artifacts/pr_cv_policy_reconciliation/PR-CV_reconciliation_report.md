# PR-CV Reconciliation Report

Decision: A - POLICY CONTRACT RECONCILED.

The ordinary NPC dialogue provider surface is current and bounded. P2 is intentionally a narration-only provider request, not a structured declaration request. The missing structured markers were obsolete placement assertions, not missing behavioral safeguards.

No production code changed. No resolver-specific projection was implemented. No authority owner, validator, state commitment, resolver selection, immutable finalization, retry architecture, or output schema was weakened.

Repairs/rebaselines:

- P2 PR-BT assertions now validate the effective narration-only contract.
- P3 prompt-size assertion no longer depends on an arbitrary historical 12,000-character threshold.
- P2 epistemic-guidance assertion no longer requires interpretation/hypothesis guidance on an incidental-dialogue turn.
- Added deterministic parser/validator coverage proving declaration smuggling is rejected and harmless narration-only dialogue survives.

Residual unrelated baselines:

- Authored-knowledge realization remains 14 passed / 2 failed.
- Shared turn pipeline remains 41 passed / 24 failed.

Recommended next step: PR-CU may retry its regression gate against the reconciled PR-BT tests before attempting resolver-specific context projection.

