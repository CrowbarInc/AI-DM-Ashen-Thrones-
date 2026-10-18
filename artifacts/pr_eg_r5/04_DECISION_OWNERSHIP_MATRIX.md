# 04 — Decision Ownership Matrix

PR-EG-R5 · 2026-10-17 · investigation only

Each row separates semantic competence from authoritative enforcement; a host check that an NPC exists does not settle whom a sentence addresses.

| Decision | Current owner | Other influences | Duplicated/conflicting decision | Required semantic/enforcement boundary |
|---|---|---|---|---|
| GM or NPC | orchestration / continuity | live communication, mode, interaction_context | several semantic owners | Interpret meaning; host enforce mode |
| Which NPC | ordinary_semantic_ownership / interaction_context | bridge, continuity, provider ASK, speaker contract | provider target may be rejected; active focus competes | Semantic addressee; deterministic roster/presence |
| Conversational act | orchestration | live schema, parser, dialogue reply kind | ASK and MIXED command framing | Semantic act; host action eligibility |
| Subject | dialogue_authority / social / continuity | communication.subject, contract dimension | token summary versus proposition/reference | Semantic subject; host source binding |
| Information request | orchestration / intent parser | question regex, communication purpose | questions can become movement/compound acts | Semantic modality; host non-execution |
| Action proposal | bridge / ordinary contract | provider operations, deterministic movement | incidental posture or question can gain operation shape | Semantic proposal; deterministic execution permission |
| Correction | continuity / orchestration | pending revision, live CORRECTION | correction may replay rejected answer | Semantic revised meaning; host forbid retcon |
| Historical recall | continuity / communication decision | public evidence and NPC runtime | same-speaker proposition ambiguity rendered as speaker question | Semantic reference; exact historical source |
| Relevant information | social lexical selection | provider evidence refs, continuity overlap | admissible source mistaken for answer | Semantic relevance; host restrict source pool |
| Authorized information | social / dialogue_authority / final validator | proposition_authority, gm_resolution_decision | many enforcement layers; semantic disagreement is not authority | Host mandatory disclosure/canonical enforcement |
| Sufficient answer | social + dialogue_authority | dimension support, partial absence rules | different predicates return inconsistent judgments | Semantic entailment/coverage; host cannot grant missing facts |
| Answer/clarify/decline/uncertain | orchestration + social reply plan + speech choice | continuity, gm_retry, final gate | multiple independently selected response plans | Semantic appropriateness; deterministic allowed outcomes |
| Allowed wording | expressive_dialogue + host speech | bounded_improvisation, narration policies | local lexical constraints; old narration fallback | Provider bounded wording; host claims enforcement |
| Final delivery | immutable_valid_response + api_turn_support | API and history exact restoration | R4 post-gate rewrite repaired by R4-R1 | Deterministic host final adoption and identity |

Source anchors: [game/conversational_orchestration.py:448](../../game/conversational_orchestration.py#L448), [game/ordinary_semantic_ownership.py:643](../../game/ordinary_semantic_ownership.py#L643), [game/social.py:1587](../../game/social.py#L1587), [game/dialogue_authority.py:162](../../game/dialogue_authority.py#L162), [game/immutable_valid_response.py:1491](../../game/immutable_valid_response.py#L1491). Duplicate enforcement of immutable identity is defensible; duplicate uncoordinated selection of intent, source and speaker is the defect.
