# PR-PLAY-18 opening context analysis

Observed PR-PLAY-17 usage: **26,986 input / 2,050 output / 29,036 total tokens**. Exact historical request content was not captured, so no exact historical category breakdown can be established.

Deterministic current reconstruction before repair: **113,280 message-content characters**, approximately **28,320 tokens**. Repaired request: **1,967 message-content characters + 1,642 schema-format characters = 3,609**, approximately **902 tokens**. These are character/4 estimates, not tokenizer counts. tiktoken is unavailable locally. Provider framing, tokenization and output usage are not inferred. Fixtures differ from the historical live campaign; similar magnitude is not identity.

Pre-repair disjoint categories (percent of actual content characters; full distribution in context_measurements.json):

| Category | Characters | Estimated tokens | Share |
| --- | ---: | ---: | ---: |
| user.response_policy | 21,665 | 5,416.2 | 19.13% |
| user.instructions | 14,519 | 3,629.8 | 12.82% |
| user.gm_resolution_decision | 10,750 | 2,687.5 | 9.49% |
| user.scene | 10,353 | 2,588.2 | 9.14% |
| system 1: legacy narration | 9,564 | 2,391.0 | 8.44% |
| user.turn_packet | 8,674 | 2,168.5 | 7.66% |
| user.decision_facing_answer_recipe | 7,287 | 1,821.8 | 6.43% |
| user.narrative_plan | 6,697 | 1,674.2 | 5.91% |
| user.opening_scene_realization | 3,582 | 895.5 | 3.16% |
| user.referent_tracking | 2,671 | 667.8 | 2.36% |
| user.dialogue_social_plan | 2,269 | 567.2 | 2.0% |
| user.mechanical_resolution | 1,431 | 357.8 | 1.26% |
| user.speaker_selection | 1,163 | 290.8 | 1.03% |
| user.character | 1,072 | 268.0 | 0.95% |
| user.campaign | 1,069 | 267.2 | 0.94% |
| user.scene_state_anchor_contract | 1,026 | 256.5 | 0.91% |

The pre-repair first system is 9,564 characters, selection system 920, and JSON user payload 102,796. No developer messages, tool definitions or structured-output schema were present. Conversation/history fields are accounted for only where actually present in the measured keys. Campaign and character are roughly one thousand characters each; they are not the principal contributors. The dominant costs are response_policy, instructions, gm_resolution_decision, scene, turn_packet, answer recipe and narrative_plan.

Requiredness: the full narration policies, answer recipe, dialogue/social plans, character mechanics and legacy declaration protocol are not needed by a provider restricted to selecting public IDs/variants; their authority computations remain required locally. For the provider contract, the public catalog, allowed variants, required coverage/order and selection schema are needed. The dedicated request replaces conflicting narration context as part of alignment; no shared payload optimization was implemented.

Confirmed redundancy: opening_curated_facts equals opening_selector_selected_facts (587 value characters each). Public IDs and variant names appear in both the plan index and strict schema after repair; this overlap has distinct instruction/enforcement purposes. Multiple old fields refer to the same claims/facts and narration policy, but no exact duplication size is claimed beyond equality checks. The first legacy system conflicts with the inserted selection instruction; prompt size alone was not the basis for removal.

Up to three future opportunities (diagnostic only; none implemented beyond the required dedicated opening-contract replacement):

1. **Shared payload narration-policy projection**: response_policy (~21.6k chars) and instructions (~14.5k chars). Audit exact overlaps before removing anything from legacy consumers. Risk: priority/authority guidance loss. Validate disabled openings and ordinary/social-turn acceptance matrices; this is outside PR-PLAY-18.
2. **Duplicate curated fact list**: opening_curated_facts / opening_selector_selected_facts, one copy ~587 chars (~147 estimated tokens). One list may suffice in a future shared projection. Risk: downstream source selection relies on these keys. Validate selectors, fallback and curated-fact attachment before removal.
3. **Shared decision/scene projection**: gm_resolution_decision (~10.7k), scene (~10.3k), turn_packet (~8.7k). They overlap conceptually in authority/fact references; no byte-for-byte duplication is asserted. Keep host authority complete and measure candidate public projections. Risk: removing evidence required by legacy narration or validation. Compare accepted/rejected replay cases before any change.

The repaired opening already forwards only public choices. These opportunities concern shared legacy/context construction and must not be treated as authorization for further optimization here.
