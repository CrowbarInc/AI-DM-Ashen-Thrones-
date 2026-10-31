# 08 — Final Verdict and Handoff

**A — Implementation target established.** Evidence supports one bounded repair with credible player-facing benefit: correct speech-participant handling at the existing shared addressee-grounding boundary for established NPC follow-ups.

This is a prioritization verdict, not implementation acceptance or proof of improved gameplay. The model already proposes the runner in S03.3 and S05.3; the host rejects that proposal as an unresolved person while retaining active runner context. Current-source reconstruction and unmodified syntax probes isolate a concrete grammatical boundary. A safe repair still has to preserve explicit targets, true ambiguity, scene locality, topic uncertainty, disclosure and resolver authority.

Weighted eligible ranking: F1 4.30, F2 4.00, F3 3.80, F4 3.50. The close F1/F2 comparison is broken by repair specificity and diagnostic confidence, not a numerical claim that F1 affects more turns. F5 3.95 is comparison-only and excluded from new implementation. No recovery percentage is predicted.

Recommended **ATGB-R2-02 — Bounded speech-role grounding for established NPC follow-ups** is specified in report 07. Correct the shared host owner/nominal boundary; do not introduce prompt, schema or memory architecture changes. Expected immediate benefit: remove unnecessary wrong-person clarification and let existing authorized dialogue handling proceed. Answer adequacy downstream is a separate acceptance question, especially after S05's topic switch and GM refusal.

## Behavioral Evidence

Historical ATGB baseline: 10 scenarios, 37 authoritative captured turns, original live-enabled production API path; individual replies can be host-owned. Imported assessment is AI-assisted and unattested. This pass extracts 19 selected original turns across six scenarios, not a new benchmark run. Standard packet: `artifacts/validation_evidence/atgb_r2_01/`. `representative_traces.json` retains canonical result/log references and hashes, exact raw interpretations/decisions/exchanges. Selected historical success S03.1 demonstrates explicitly addressed runner dialogue; failures S03.3 and S02.2 demonstrate wrong-slot clarification and non-answer. S05.3's topic is ambiguous; S07's opening delivery is deficient. No authenticated human adjudication or new evaluator score was created. Historical disagreements/uncertainties remain separate and are not overwritten.

Final PR-EG-R6-R5 raw counts were recomputed (59/164, correction tag 0/25); intervention gains remain intervention results. R4-R1 experimental integration is still forbidden. R1 mechanical routing is repaired/validated within scope; R1-07 conversational contract is implemented/deterministically validated; live conversational acceptance remains pending after R1-08/09 connectivity failures. S08.2 is not the next implementation target.

## Review package and safeguards

Eight reports, architectural failure matrix, scores in JSON/CSV, representative trace references/excerpts, candidate comparison, exact next scope, repository identity/status, protected entry hashes, integrity result and standard evidence packet are included through explicit allowlists. Review exports use the existing handoff generator, with a timestamped `CURRENT_REVIEW(YYYYMMDD-HHMMSS).zip` using America/New_York time. No local configuration or credential source is packaged; selected payloads are scanned for secret-value patterns and ZIP CRC/hash verification is recorded.

Confirmed for this pass, subject to the packaged integrity verification:

* No production changes.
* No prompt or schema changes.
* No provider calls, paid probes, retries or network diagnostics.
* No experimental PR-EG candidates merged or modified.
* Frozen ATGB baseline, original transcripts and historical judgments unchanged.
* No unauthorized gameplay-state mutations; no gameplay execution.
* No secrets included in the checked explicit review payload.
* No commits or pushes; all existing repository changes preserved.

Only new reports/evidence/local review scripts, a concise canonical orientation update and generated handoff exports were written. Offline count/provenance checks and isolated pure syntax probes are not tests of repaired behavior; no product test suite or fresh live acceptance is claimed. Remaining uncertainty includes exact original provider messages, grammar-level implementation details, downstream dialogue adequacy, real provider/token/latency effect and authenticated human review.

**Stop after generating and verifying the review ZIP. Await external review before ATGB-R2-02.** No implementation or live authority carries forward from this recommendation.
