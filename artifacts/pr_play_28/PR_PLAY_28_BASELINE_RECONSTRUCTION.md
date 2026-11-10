# PR-PLAY-28 baseline reconstruction

Revision: d40f1ed198236c604085f1c842ead267a8104ce2. Existing working tree contains prior tracked modifications and untracked evidence/source; see git_status_before.txt. No changes reverted or committed. No AGENTS.md was found in the repository scope.

Historical PR-PLAY-27 reports and final archive were located. archive_path.txt points to handoff/CURRENT_REVIEW(20261101-163648).zip. Original mocked transcripts and baseline replay are retained here with pr27_ prefixes; fresh current-code reproductions use baseline_ prefixes. No missing evidence was synthesized.

Fresh real HTTP two-turn reproduction: four cases pass the historical observed-behavior assertions (two expression outcomes × broad/explicit follow-up); reproduction.xml/reproduction.txt. Broad question: “What sort of rumors have you heard?” selects no authored topic and publishes uncertainty. Explicit question: “What have you heard about the patrol?” selects patrol_rumor. Baseline topic selector results are in baseline_topic_selection.json.

Authored source: artifacts/pr_play_26/live/baseline/persistent/world.json, NPC tavern_runner, topic patrol_rumor, text “The runner heard the patrol vanished near muddy footprints northwest of the crates.”, clue_id muddy_footprints_northwest. No discovery categories, tags, or human-readable title are present. Authored text and clue are unchanged by this pass.

Explicit successful disclosure appends social_lead_revealed(muddy_footprints_northwest) and social_extracted_lead(lead_frontier_gate_old_trading_crossroads). The latter is an independent authored scene discoverable selected by the existing minimum-actionable-lead rule, not a fact in the patrol topic. Evaluation reports unauthorized_overlay_mutation and opening_not_accepted_or_ordinary_turn_authority_unavailable. It is a real ordinary turn after campaign_started=true; this is not an omitted opening initialization.

The historical replay excluded session log and reports invalid_progression as a replay limitation. This pass's new positive authority evaluation requires full log and authored scene evidence. Historical replay alone is insufficient. Fresh integration captures both.

Pre-repair regression scope is the identical 73-file / 1,603-test list from PR-PLAY-27 (test_files.json); exact failures and final comparison are reported in TEST_RESULTS. Pytest's autouse transport guard blocks live model calls. An initial baseline run was interrupted before production edits; baseline_complete uses fresh isolated temp storage and is the authoritative baseline. Zero live-provider requests.

Additional complete pre-repair reproduction: full_reproduction.xml/txt and two_turn_accepted.json/two_turn_accepted_explicit.json capture the actual initialized fixture scene and log context. The scene is the established mocked campaign fixture (not assumed identical to the historical live scene): its discoverable clue supports old_trading_crossroads. A partial projection against the historical live scene instead fails, as preserved in projection_development.json; projection_complete_source.json uses the actual captured fixture scene and exactly matches the observed events/overlay. This evidence distinction is intentional.
