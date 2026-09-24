# Cross-turn causal graph

Edges are only those the log and final session support. Raw prompts were not kept, so model-prompt contamination is not claimed. Deterministic reuse is claimed only where a later field cites the earlier text.

```
Turn 1  untargeted inspect
    → player sees visible_facts[0] (notice board)
    → model banner paragraph stored on topic:banner_eastern_enter.last_answer
    → not read by a later turn (separate key)

Turn 2  same untargeted template
    → player sees the same notice-board sentence
    → topic key topic:despite_look_make minted from this wording

Turn 3  no action kind (label downtime); notice_board not bound
    → model curfew statute shown and written onto topic:despite_look_make.last_answer
    → narrative_authority_failed stays false
    → player’s turn 5 question adopts "the curfew" and "bandits"

Turn 4  open solicitation, npc_id null
    → retry escape hatch emits speaker_label default "The guard says"
    → no interlocutor stored
    → a different quantity paragraph is stored on topic:anyone_board_dusk
    → that paragraph is not the shown line and is not cited later

Turn 5  bare "you"  +  route_reason no_addressable_target
    → dialogue lock sets question_tavern_runner
    → model captain paragraph shown inside Word is
    → that paragraph is social_answer_retry_anchor_text on turn 6
    → source recorded as topic_pressure:last_answer
    → recent_contextual_leads keeps "ask the guard captain"
    → lead_registry stays empty

Turn 6  active_interlocutor_followup (continuity is consistent with the lock)
    → prior_same_dimension_answer_exists because that last_answer exists
    → escalation force_partial_answer
    → new model paragraph stored as last_answer
    → shown sentence is the tail of that paragraph ("handles official talk")
    → player’s turn 7 keeps asking about "he"

Turn 7  same interlocutor, new topic key
    → final_emitted_source structured_fact_candidate_emission
    → shown clause is the tail of this turn’s last_answer ("easy ear" / introduction)
    → completeness check skipped because the source was treated as structured
```

This is not one mistake echoing unchanged. Three chains overlap:

1. Turns 1–2 share the untargeted stock line and stop there.
2. Turn 3’s invented curfew is what the player argues about next. The system does not retrieve that `last_answer` as turn 5’s fact.
3. Turn 4’s guard label and turn 5’s lock start the runner. Turn 5’s model paragraph is then an input to turn 6’s structured-fact candidate and escalation. Turns 6 and 7 each also store a new paragraph and show a sentence from it.

No chain changes scene, date, clues, or revealed topics.
