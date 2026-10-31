# 04 — Source Ownership and Data Flow

The companion `source_ownership_map.json` records exact current function locations, caller/consumer boundaries, inputs, outputs and fallbacks. `source_excerpts.txt` preserves those functions with one-based lines and whole-file hashes for review.

## Production path

`api.chat` → current deterministic continuity → `live_chat_interpretation.interpret_production_turn` when needed → production communication validation and PR-DR adaptation → API record reconsideration → `decision_from_interpretation_record` → `_communication_decision` → either nonmutating GM answer or ASK bridge/social resolver → sealed emission.

This describes the actual legacy communication path exercised in original logs. It does not substitute the experimental PR-EG bind/coverage pipeline merely because those names sound relevant.

## Ownership boundaries

| Owner | Input → output / caller and consumer | Authority and fallback |
| --- | --- | --- |
| semantic_interpreter.player_visible_turns | Log → last two player/GM pairs, each side 240 chars; used by production interpretation | Visible history only; metadata excluded. Not persistent topic authority. |
| conversational_orchestration.public_conversation_evidence | Scene + last four log entries → scene, visible:index, reply:index (1200 chars), causal receipts, latest speech and disclosed topic passages | Candidate construction. Excludes undiscovered clues/private NPC knowledge. IDs are request-local, not durable referents. |
| live_chat_interpretation.interpret_production_turn | Current message, catalog, recent pairs, public evidence, active_npc_id, last_subject and pending context → adapted record or blocked outcome carrying record | Existing semantic owner for communication recipient/purpose/subject/evidence refs. Does not adjudicate facts. Subject is free text. last_subject comes from last_gm_exchange and is usually prior player input, not an accepted semantic topic. |
| live_chat_interpretation.valid_communication | Communication object + host evidence map → bool | Exact fields and enum/type/reference membership validation. [] passes. No relevance or sufficiency test. Model cannot supply passage values. |
| player_interpretation_bridge.reconcile_reference_annotations | Proposed action refs + player text + catalog/context → reconciled record/diagnostics | Existing operation/addressee grounding, including bounded authored subject checks. Does not create general conversation topics; explicitly preserves unresolved deictic subjects. |
| ordinary_semantic_ownership.assess_addressee_grounding | Text, scene/world/session, proposed NPC → recipient grounding/authority | Present interlocutor and explicit speech roles. R2-02 repair accepted. Does not resolve what “that” means. |
| conversational_orchestration.decision_from_delivered_exchange | Text + delivered history/session → continuity decision or None | Prior delivered speech may answer/restate or clarify before a model record is used. Synthetic minimal sessions do not stand for complete historical continuity state. |
| conversational_orchestration._communication_decision | Adapted communication + public_evidence/context → ANSWER/CLARIFY or None for resolver | GM: joins selected public passage values. No fact retrieval or general sufficiency check. Empty QUESTION returns unestablished-information fallback; CLARIFICATION without evidence emits clarification_question. |
| conversational_orchestration.decision_from_interpretation_record | Record + bridge metadata/context → decision envelope | Calls continuity, ownership correction, communication branch, then action fallback. A single ASK goes to EXECUTE; unsupported/unclear interpretation clarifies or declines. |
| player_interpretation_bridge.normalized_action_from_interpretation | Record + catalog/grounding → normalized action and metadata or rejection | Validates operation/entity compatibility; copies communication and public evidence, not free-text subject into an authoritative topic key. |
| social.resolve_social_action | Normalized ASK, raw input, scene/world + copied session → social result; may mutate the provided in-memory session | Existing topic selection and disclosure owner. No topic → bounded uncertainty/refusal plan. Not a stateless function; experiments use copies only. |
| social._next_topic_to_reveal / authored_topic_relevant_to_question / authored_answer_sufficient_for_question | NPC authored topics, runtime reveal state, raw question → eligible topic/selection | Speaker ownership, subject relevance and requested detail sufficiency are separate predicates. Selected public refs alone do not override them. |
| dialogue_authority.authorize_npc_disclosure | NPC + candidate topic → permission/provenance | Final NPC disclosure gate; topic ownership/public epistemic policy. No model authorization. |
| api._nonmutating_conversational_decision_response | Decision → GM response, nonmutating resolution, context/log output | Applies host speech expression/audit then seal; original S02 text already equals the decision, zero generation attempts. We inspect source, not invoke the disk-writing API in this pass. |
| immutable_valid_response.seal_host_speech | Host text, resolution and speaker → accepted immutable speech | Preserves accepted text; does not turn a related sentence into an answer. Original hard-valid/contract-satisfying labels are structural, not proof of semantic adequacy. |

## Where the relationship is lost

S02.2/.4: subject-to-answer relationship first fails in communication.evidence_refs selection. S02.3: subject antecedent and evidence relationship both wrong in the raw completion. Host projection faithfully narrows to selected text, then realizes it faithfully. S05.3: original addressee problem is repaired; current record preserves the proposed subject but downstream lexical relevance does not treat it as a uniquely bound topic. Since that binding is not uniquely supported, bypassing the host would be the wrong repair.

The narrowest next owner is the **existing production interpretation contract** at interpret_production_turn's communication.subject/purpose/evidence_refs boundary. No missing architecture or new memory subsystem is established. PR-EG R5's witness/bind and paired proposition interventions are related lessons about separation, not directly exercised causes or integration authority.
