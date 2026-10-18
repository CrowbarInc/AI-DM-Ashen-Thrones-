# 12 — Bounded Improvisation Audit

PR-EG-R5 · 2026-10-17 · investigation only

The current system already distinguishes authored factual speech, incidental characterization, paraphrase, simple explanation, uncertainty and nonbinding refusal. The problem is not absence of a bounded-expression layer. [game/expressive_dialogue.py:319](../../game/expressive_dialogue.py#L319) selects its operation from question patterns, proposition and posture; [game/expressive_dialogue.py:754](../../game/expressive_dialogue.py#L754) uses scope-specific lexical, number, entity and relationship checks. A rejected candidate falls back to host wording. R4-R1 primary6 proves that fallback can itself be inconsistent with prior speech.

| Category | Required authority | Suitable semantic freedom |
|---|---|---|
| Consequential facts, access, security, rewards | exact host source and disclosure permission | faithful expression only; no added implications |
| Incidental taste/characterization | host scope and prior speech consistency | first-person preference/reaction without new actionable world relations |
| Acknowledgment | host non-executing conversational plan | acknowledge misunderstanding or humor without asserting facts/consent |
| Questions/clarifications | grounded unresolved slot | ask only the missing information; preserve resolved speaker/subject |
| Uncertainty/nonbinding refusal | accurate lack-of-authority/knowledge posture | explain limits about the actual question; no invented secrecy or hostility |

Current operation-shaped ASK, SOCIAL_SIGNAL and MIXED adaptation can route harmless speech through action sequencing and consequential validation. Narrow lexical closure also constrains ordinary expression, but widening it alone risks consequential implications disguised as taste (“I like evenings because the sentries sleep”). Recommendation: broaden semantic planning for acknowledgment and correction recovery while retaining exact source constraints for facts. Do not relax the existing gate globally or claim arbitrary incidental text can be soundly validated by a few keywords.
