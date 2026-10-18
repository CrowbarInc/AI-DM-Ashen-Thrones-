# 14 — Provider Prompt and Payload Audit

PR-EG-R5 · 2026-10-17 · investigation only

Production interpretation imports its prompt/schema/adaptation from experiments.pr_do, pr_dp and pr_dr through [game/live_chat_interpretation.py:140](../../game/live_chat_interpretation.py#L140); these are live runtime dependencies despite their directory name. The base prompt says “Describe the attempt,” enumerates executable/ineligible operations and defaults unclear IC/table talk to clarification. The added system instructions tell it to choose communication.recipient and purpose first and permit meaningful zero-operation speech. This is a real tension between legacy command framing and newer discourse semantics, not proof that every provider response is wrong.

| Input | Present? | Limitation |
|---|---|---|
| Current utterance | yes | full text can compete with compact output cap |
| Prior dialogue | last two visible turns, player and GM clipped to 240 characters each | older correction, source identity and contrast may disappear |
| Speaker and scene | visible catalog, scene summary, active NPC | derived focus may already be wrong |
| Pending clarification | kind, scene, up to four steps and choices | not complete discourse history |
| Known facts | public_conversation_evidence from visible scene/log | no general hidden NPC knowledge retrieval; candidate eligibility is separate |
| Prior corrections | only through recent visible text/pending summary | no stable correction relation to rejected proposition |
| Output semantics | strict descriptive schema + communication + references | legacy mode/components and new recipient can disagree; cap 320 output tokens |

Three R5 captures preserve complete messages, production schema and stubbed outputs in [payload_captures.json](payload_captures.json). They execute prompt construction, not a provider; estimated inputs 3,245 / 3,235 / 3,244 tokens include schema and estimator overhead. Actual input/output tokens and provider cost are zero. The captured scene is the historical primary scene; the independent orchard correction deliberately has no matching source.

Historical measured input ranges: R4 interpretation 1,724–2,206 (median 2,033), expression 175–230 (median 187); strict-social 25,817 plus retry inputs 28,430 and 26,831. R4-R1 final has nine expression calls (159–212), strict-social 28,675 and escalation 29,671, total input 59,915 / output 1,327. There are **zero interpretation calls in that final R4-R1 ledger**; several retained metadata records explicitly say live_interpretation_disabled. This limits conclusions about semantic model performance. Do not attribute these costs to every ordinary turn. No currency calculation is needed to compare measured tokens.

Sources: [game/semantic_interpreter.py:127](../../game/semantic_interpreter.py#L127), [game/live_chat_interpretation.py:297](../../game/live_chat_interpretation.py#L297), [game/gm.py:4567](../../game/gm.py#L4567), [game/gm.py:4403](../../game/gm.py#L4403), [game/prompt_context.py:1](../../game/prompt_context.py#L1), [experiments/pr_dr/prompt.py:58](../../experiments/pr_dr/prompt.py#L58). Large strict-social prompts coexist with compact projection helpers; qualification must show why a path reaches the larger payload rather than merely tightening the interpreter prompt.
