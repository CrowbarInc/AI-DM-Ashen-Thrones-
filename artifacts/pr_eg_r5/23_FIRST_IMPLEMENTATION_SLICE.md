# 23 — First Implementation Slice

PR-EG-R5 · 2026-10-17 · investigation only

Proposal only: **ordinary NPC information questions with explicit addressee, including a correction of the prior question's subject**. Keep broad action/combat/movement routes unchanged. This slice tests the main semantic bottleneck without requiring all conversational ownership to move at once.

Use a host-filtered list of currently disclosable authored propositions plus a bounded delivered-history window. One AI semantic call proposes requested relation, subject, correction linkage, relevant candidate IDs and coverage. The host validates all IDs and disclosure, binds exact propositions or a genuine no-answer plan, and uses existing speech adoption and persistence. It must understand that “who manages docking” has no answer in a bell-name fact, and that “I meant the ferry schedule” replaces the rejected bell question. Do not encode these exact words as runtime exceptions.

Replace the covered question family’s independent social relevance/sufficiency selection with the new shared authorized-plan result. Do not append a second relevance verdict after the old selector has already chosen a fact. Downstream speech/expression may format the authorized proposition but cannot reselect it. Failed interpretation cannot fall through to a differently targeted legacy answer.

Review deliverables for that future slice: ownership diff; raw prompt/schema/output; source eligibility and coverage trace; exact adopted/history/API comparison; unauthorized-state diff; matched cost/latency comparison; save/load results; holdout failure inventory. Preference reasoning, GM historical recall and multi-NPC sequencing remain later migration stages, but must not regress while the slice is enabled. This scope can disprove C's relevance/authority premise with a small reversible change. No such change was made in R5.
