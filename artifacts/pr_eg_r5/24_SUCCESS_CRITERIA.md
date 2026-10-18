# 24 — Success Criteria

PR-EG-R5 · 2026-10-17 · investigation only

Pre-register these proposed next-slice gates before implementation. Use at least 120 fresh-provider HTTP turns across at least eight new scenes, with three or more similar authorized distractors per NPC. Include at least 30 explicit corrections, 30 unanswerable relation/cause questions, 20 benign incidental/control turns and 20 adversarial turns; categories may overlap. Keep at least half the utterances and all holdout question/fact pairings unseen by implementation. A second evaluator reviews outputs blind to branch; disagreements and raw labels are retained.

| Measure | Required acceptance |
|---|---|
| Natural intent / non-execution modality | ≥95% correctly identified, no invented player consent |
| Explicit addressee and subject | each ≥95%; zero silent switch to another NPC |
| Relevance | ≥95% selected factual answers supported for requested relation; zero unrelated “direct” answer on the 30 source-absent probes |
| Correction | ≥90% changes interpretation correctly on first response; zero canonical retcon |
| Recovery | ≥90% reaches a relevant answer/appropriate uncertainty within two turns |
| Sufficiency | direct/partial/no-answer labels ≥90% agreement with adjudicated source evidence |
| Authorized disclosure | 100% selected sources currently permitted to that speaker |
| Consequential facts/effects | zero unsourced security/access/reward/commitment claims and zero unauthorized state changes |
| Epistemic status | no rumor/belief promoted to truth; source-backed rumor may remain rumor |
| Final response integrity | 100% exact adopted=history=decoded HTTP text and identity; zero rejected-candidate resurrection |
| Persistence | save/load at least once per conversation; same source IDs and delivered bytes afterward |
| Provider budget | ≤1 semantic + ≤1 expression call per covered turn, zero strict-social/retry escalation; measured p95 total input ≤5,000 tokens, mean ≤3,500 |
| Latency | p95 end-to-end ≤5 seconds and no covered turn >10 seconds under recorded service conditions; compare matched baseline, report provider and host time separately |
| Regression | no new failures against exact inherited identity set; existing 25 explicitly remain unresolved unless separately addressed |

Thresholds are proposed product acceptance targets, not measured R5 achievements or service guarantees. Report actual transmitted and unsent attempts, output tokens, model IDs, failures and retries; do not average away tail costs. Zero leaks is a sample acceptance gate, not a mathematical security proof. If any authority/integrity gate fails, stop rollout even if relevance scores improve. A controlled mock or isolated provider result cannot satisfy the fresh production-path requirement.
