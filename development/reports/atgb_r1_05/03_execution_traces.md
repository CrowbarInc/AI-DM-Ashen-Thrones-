# 03 — Execution Traces

Each L1/L2/L4 directory contains full response.json, before/after snapshots, preflight,
configuration, durable provider_usage.jsonl, accounting, timing, transcript.md,
observational traces.json and normalized.json. Root normalized_results.json joins
all three without changing raw artifacts. L4 also retains setup_before.json and
setup_response.json establishing production-created pending provenance. Offline
preview directories are explicitly separate and are not included in live totals.

Existing Python profiling records function returns and an allowlisted set of locals:
public_conversation_evidence; request_interpretation (complete production messages,
raw response and usage); interpret_production_turn (parsed/adapted record, disposition,
selected evidence); assess_addressee_grounding; _pending_revision_decision;
_communication_decision; decision_from_interpretation_record. Source lines and
host decision envelope preserve proposed operations, targets, execution policy,
context updates, authorization when available and player-facing response plan.
No production instrumentation or decision override was added. The SDK constructor
wrapper changes only transport retry count. The L4 setup stub is restored before
preflight/measured chat and explicitly recorded in configuration.

L1/L2: public evidence -> live request -> clarification_required /
NEEDS_CLARIFICATION -> API re-evaluates the existing record -> repaired revision
gate returns null -> communication_before_execution -> redundant model question.
Unlike the prior R1-03 report's L3 summary, current traces directly show the gate
is consulted after the blocked live outcome. Do not transfer its path claim blindly.
L4: same blocked-outcome adaptation seam -> pending_intention_revised -> host
acknowledgment and retained ambiguity. No bind call observed. A planning_decision
hook returns null; no experimental semantic plan is substituted.

Gaps: no exhaustive rejected-evidence reasons (no such model rationale supplied),
no hidden chain of thought, no separate comprehensive disclosure-check log, no
provider billing invoice/price table, no transport-level packet trace, no HTTP/browser
capture. No downstream narration input exists: each final answer is host-owned and
recorded in its decision and response metadata. Absence of a field is not a PASS.
