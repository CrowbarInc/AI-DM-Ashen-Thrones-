# 04 — Current Contract Audit

# Preimplementation contract audit

This record was generated before changing the three existing production contracts.

* Intent: `unified_semantic_planning.validate_plan_schema` accepts four conversational acts. Schema and missing-argument enums are binary. `is_migrated_information_turn` uses an existing lexical scope gate; this campaign must not expand its phrase tables.
* Binding: `conversational_referents.bind` checks conversation IDs, but silently substitutes active focus when an older target lacks a literal subject/object. This loses provider intent and named-role distinctions.
* Transformations: deltas preserve eight fields, but only predicate/subject/object changes require current evidence. Qualifier changes can escape the witness check. `reject_interpretation` accepts an arbitrary complete field delta. Multi-role replacement has no representation.
* Correspondence: `semantic_correspondence.coverage` checks binary arguments, predicate, negation, qualifiers and epistemics. It cannot preserve speaker, recipient, topic and message independently. Literal indefinite arguments can be overstated as identities. Missing time/space becomes nonanswer even if some information was supplied.
* Failure handling: parse/schema errors and invalid targets all become player clarifications. Genuine ambiguity and model failure are indistinguishable to the player. There is no retry loop.
* Resolution: `authorize_information_turn` invokes one provider proposal, binds before source selection, then checks `dialogue_authority.npc_source_permitted` and returns a locked response. Only original permitted text supplies facts. Legacy fallbacks are fenced by locked planning ownership.
* Delivery: `immutable_valid_response` seals adopted speech; `conversational_continuity.record_delivered_exchange` commits the referent after seal verification. Corrections append revisions; they do not rewrite speech.
* Persistence: version 1 conversational_context question index is stored in the session integrity envelope, bounded to 24 records. Provider context contains six recent referents, no secret source texts. Existing arbitrary session keys survive storage roundtrips.

Exact pre-edit line numbers and source hashes: [source inventory](preimplementation_source_inventory.json). Complete source snapshots: [baseline sources](baseline_sources/game). Raw failures: [failure evidence](preimplementation_failures.json). Those links retain pre-edit semantics even when final source line numbers change.


Final boundaries: [game/unified_semantic_planning.py:778](<C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm/game/unified_semantic_planning.py:778>); [game/conversational_referents.py:108](<C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm/game/conversational_referents.py:108>); [game/semantic_correspondence.py:103](<C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm/game/semantic_correspondence.py:103>)

Caller audit: conversational_orchestration consults planning_decision before legacy delivered-exchange selection; social uses a semantic_lock branch and only runs _next_topic_to_reveal when that lock is absent. dialogue_authority delegates locked plans to authority_record_from_plan. conversational_continuity suppresses legacy selection for migrated turns, verifies adopted speech, then commits the referent index. API delivery records that same sealed line. Exact current import/caller lines and hashes: [artifacts/pr_eg_r6_r2_r2/caller_inventory.json:1](<C:/Users/Master Mandalcio/Documents/Tabletop Gaming/AI Dungeon Master/ashen_thrones_ai_gm/artifacts/pr_eg_r6_r2_r2/caller_inventory.json:1>)
