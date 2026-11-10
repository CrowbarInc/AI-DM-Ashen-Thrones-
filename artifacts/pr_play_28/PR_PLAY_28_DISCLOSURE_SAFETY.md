# PR-PLAY-28 disclosure safety

`game/dialogue_authority.py::authorize_npc_disclosure` rematches exact authored speaker-owned text/id and clue_text. Known statuses are known/npc_knowledge/belief/rumor; known=false and unknown statuses deny. Public/allowed/authorized disclosure policies may permit speech; hidden/secret and other disclosure policies deny. Epistemic rumor/belief remains attributed NPC knowledge, never canonical world truth. Legacy absence of disclosure metadata means public knowledge; absence of discovery metadata does not mean category-discoverable.

Both the new category predicate and existing selector call npc_source_permitted. The social resolution owner rechecks authorization before constructing topic_revealed; `game/clues.py::apply_socially_revealed_leads` independently rematches the world source and validates clue id and clue strings before persistence. The evaluator also rechecks the pre-turn authored source. Discovery metadata is not a disclosure grant.

There is no current generic quest-state/relationship threshold predicate on these topic rows. Topics marked with a conditional/restricted disclosure value remain denied; the tests explicitly exercise requires_quest and requires_relationship with unmet permission. This pass preserves fail-closed handling rather than inventing a new quest/relationship implementation. Other safety controls remain unchanged.

Negative coverage: unrelated merchant-only topic, empty knowledge, rumor-like id/text without metadata, malformed category metadata, hidden/secret, unknown/unknowable sources, conditional disclosure policies, multiple candidates including hidden, and distinct general news/specific merchant asks. HTTP restricted-topic integration uses the same campaign, opening renderer, offerings turn and broad follow-up; expects uncertainty and no clue-overlay changes. Exact test outcomes are in focused.xml and PR_PLAY_28_TEST_RESULTS.md.

No new partial-disclosure stages or hidden-topic introductions. Only a currently permitted source may be selected through the new category path. No provider inference over hidden topics is used.
