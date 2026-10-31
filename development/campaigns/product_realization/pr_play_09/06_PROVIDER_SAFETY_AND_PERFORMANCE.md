# 06 — Provider Safety and Performance

PR-PLAY-09 · 2026-10-30 America/New_York · evidence_scope: structural_only.

The hard ceiling is six provider requests total: opening plus whatever production
operations each action actually needs. Existing atomic admission and cumulative
ledger reconciliation remain authoritative. The worker disables SDK/host retries,
forbids connectivity probes, preserves normal routing/model selection and per-operation
output limits. No provider escalation/retry path is introduced. All operation records
retain model/purpose/owner, count, input/output/total tokens, latency, status and configured
zero retry count. Missing usage/latency stays null. Application latency is separate.

Aggregate ceilings remain 200000 input / 20000 output / 220000 total; any stricter
inherited ceiling wins. Effective limits print before worker launch. Opening normally
reserves up to 3000 output, ordinary narration 600; no allowance is increased. Existing
interpretation reservations also count. A successful historical opening used 28317
tokens; that is evidence, not a forecast of five additional turns or monetary cost.
No currency estimate is supplied.

Live interpretation calls request_interpretation; resolved actions can separately
call gm.call_gpt. The normal-pipeline synthetic example records opening=1, T1=1,
T2=1, T3=2, T4=1: six requests, 120/60/180 synthetic usage. T5 is skipped before
submission. The T2 fixture was clarified rather than forcing an NPC success. Five
actions each using interpretation+narration would expose eleven calls including
opening; this illustrates feasibility, not a guaranteed upper bound for every optional
production path. A complete five-turn run inside six cannot be guaranteed.

Readiness is conditional for a six-request diagnostic that may stop early. Keep the
hard limit. External reviewers may instead authorize a separately designed budget
scope after reviewing these native operation records. No larger ceiling or bypass
is implemented or authorized here. Do not restart the process to finish the script.
