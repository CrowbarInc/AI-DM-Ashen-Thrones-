# PR-PLAY-25 knowledge pipeline

| Question | Repository finding |
| --- | --- |
| What makes a fact authoritative? | Host-loaded canonical/effective scene state, rather than a player premise or provider assertion. |
| What makes it public? | Membership in the current scene's `visible_facts`; hidden facts and discoverable clues are separate fields and are not read by the new selector. |
| Representation? | A list of free-text strings inside the `scene` envelope. There is no entity ID or provenance attached to each visible sentence. |
| Can facts identify a speaker? | Some have a direct grammatical subject that exactly matches a uniquely registered scene NPC name. Many do not; those remain ineligible. |
| Existing provenance? | NPC topics have IDs and disclosure metadata. Dialogue provenance records identify source, speaker, operation, epistemic status and proposition. Opening rendering has source references, but they do not attach NPC ownership to arbitrary visible strings. |
| Own versus another NPC's activity? | The added narrow grammar requires the sentence's entire subject to match the unique addressable record whose ID matches the resolved NPC. No word-overlap or substring attribution. |
| Question matching? | Existing authored-topic relevance and sufficiency run unchanged. The fallback recognizes a small full-question offerings grammar and the original normalized compound phrasing. No second model or exact item keyword is required. |
| Prior dialogue authority? | Authored topics, verified delivered history, bounded personal expression and host operations. Public scene text was not an answer source for the general offerings request. |
| Restricted exclusion? | `authorize_npc_disclosure` rechecks authored policy/knowledge. New public selection cannot override a selected topic, a refusal, ambiguity, a locked semantic plan, any authored offerings topic, or a restricted topic overlapping advertised items. |
| Expression validation? | Deterministic content anchors, closed vocabulary, numbers, epistemic posture, names, length and sentence checks. Scoped offering verb equivalence is added only for the new source relation; negation is explicitly rejected. |
| Multiple sources? | This repair selects one public source only. Multiple matching visible sentences fail closed; authored sources retain precedence. No concatenation or contradictory merge. |
| No match? | Existing uncertainty/refusal and host fallback remain. |
| Public facts in provider input? | Previously absent in this captured expression request. Now only the selected first-person offering proposition is passed; not the full scene or hidden state. |
| Provider schema change? | None. Existing `authorized_propositions`, `permitted_meaning`, source identity and faithful-paraphrase operation suffice. |
| Existing structures reused? | Existing dialogue authority, provenance, expression contracts, validator, immutable host sealing, accepted response and Player projection. |

Source anchors: `game/social.py:1611 _next_topic_to_reveal`, `:1564 authored_topic_relevant_to_question`, `:1587 authored_answer_sufficient_for_question`, `:3895 resolve_social_action`; `game/public_fact_dialogue.py:select_public_offering`; `game/dialogue_authority.py:509 build_dialogue_authority`, `attach_dialogue_authority`, `select_host_speech`; `game/expressive_dialogue.py:build_expression_contract`, `build_expression_prompt`, `validate_expression`, `_attempt`; `game/immutable_valid_response.py:1448` host-speech selection and expression adoption; `game/api.py:5026` and `:5044` public projection.

Authority hierarchy remains host-owned: established world/NPC sources with disclosure rules; verified history under existing restrictions; bounded expression or honest host uncertainty. Locked unified semantic plans retain their own authority and are not overridden. The new visible-source fallback supplies speech only; it grants no discovery, transaction or durable world mutation. The legacy no-topic resolver hint may still describe uncertainty; the reconciled social reply fields and selected dialogue authority own final delivery.
