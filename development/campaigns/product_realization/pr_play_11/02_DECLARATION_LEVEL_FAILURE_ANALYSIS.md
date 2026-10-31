# 02 — Declaration-Level Failure Analysis

PR-PLAY-11 · 2026-10-30 America/New_York · evidence_scope: structural_only.

**No structured declaration is rejected.** All seven exact authored-text matches pass validate_declared_claims_against_decision, despite source_claim_id=null and semantic_identity={}. The requested declaration-level rejection table is artifacts/pr_play_11/declaration_rejection_table.md; original fields and accepted source claims are preserved in declaration_analysis.json.

The sole offending narration is: “The board itself lists grim new taxes, curfew regulations, and a posted warning about a patrol that has gone missing.” Related accepted declaration: rc_a83c5bcfc65e, “The notice board lists taxes, curfew rules, and a warning about a missing patrol.” Subject/predicate/object fields are **absent**, not inferred replacements for the empty semantic_identity. Every actual field and null/empty value remains in the capture.

Path: call_gpt completed output_text → _safe_json / structured envelope → run_preserve_if_valid._check → validate_generated_response → audit_realization_envelope_against_decision → declarations pass → audit_narration_against_decision → audit_narrated_claims / classify_narrated_fact → _classify_narrated_fact_legacy → no _authorized_rows_for_sentence coverage → consequential pattern notice_roster_history → unauthorized narration → unauthorized_resolution_decision_fact → host safe_nonresolution → api._opening_response_rejection → 422 and rollback.

_empty_identity_covers rejects more than one added content token. Relative to the first authored source, the narration adds gone/grim/itself/posted/regulations; the alternative opening-seed wording also fails. No synonym/entailment authority exists. This is correct under the executable conservative coverage contract, even though the sentence reads as an ordinary paraphrase. The notice/patrol pattern conservatively treats posting assertions as potentially consequential; it does not establish that the model made a mechanical decision.

Existing nested audits already report all seven accepted claims and the rejected narration with specific reason codes. No production diagnostics relaxation or raw-response ledger extension is necessary. PR11 exports that existing audit and bounded (32-item) declaration/narration analysis; omitted counts are explicit. Aggregate ledger error alone must not be used to accuse a declaration.
