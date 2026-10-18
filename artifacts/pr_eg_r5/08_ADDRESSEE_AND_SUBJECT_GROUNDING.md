# 08 — Addressee and Subject Grounding

PR-EG-R5 · 2026-10-17 · investigation only

| Expression | Current mechanism / risk | Proposed single-plan treatment |
|---|---|---|
| Explicit Mara name | vocative, catalog and provider target plus downstream recheck; name mention ≠ address | preserve named addressee separately from referenced person |
| she / what did she mean? | delivered overlap, active NPC and third-person recall cues | bind speaker and proposition independently; retain ambiguity kind |
| one of them | multi-person pool and pending choice; no general choice semantics | distinguish permission to choose one from inability to identify a referent |
| the guard | role/catalog resolution; ambiguous if several eligible guards | host ground candidate IDs; clarify only remaining ambiguity |
| back to the road | _REPEAT and historical token matching | explicit topic return, with prior proposition candidates |
| I meant the ferry schedule | correction regex, pending revision, historical overlap | replacement subject supersedes rejected bell interpretation |

Initial addressee may come from continuity, deterministic orchestration, provider ASK or directed-social entry. Later bridge and ordinary grounding can reject it; social runtime, declared-switch and speaker contract can influence the response. Subject can be recreated by subject_phrase, question dimension, topic overlap and historical selection. There is no immutable semantic plan corresponding to the final immutable speech.

The primary-12 probe reproduces a particularly clear false ambiguity: one named speaker, multiple matching propositions, then a clarification offering two speakers. Preserve ambiguity as a typed result (speaker, subject, source or modality) with candidate IDs; never render all ambiguity as an addressee question. A correction is evidence about player intent, not permission to edit prior NPC speech or canonical facts.

Anchors: [game/interaction_completion.py:627](../../game/interaction_completion.py#L627), [game/player_interpretation_bridge.py:85](../../game/player_interpretation_bridge.py#L85), [game/conversational_continuity.py:318](../../game/conversational_continuity.py#L318), [game/conversational_continuity.py:309](../../game/conversational_continuity.py#L309), [game/conversational_orchestration.py:752](../../game/conversational_orchestration.py#L752).
