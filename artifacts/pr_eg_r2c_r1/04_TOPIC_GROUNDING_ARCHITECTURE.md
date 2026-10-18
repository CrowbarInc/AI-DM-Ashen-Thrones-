# 04 — Topic-Grounding Architecture

The path remains: player text → interpretation/ordinary communication ownership → grounded interlocutor → social.resolve_social_action → _next_topic_to_reveal → build_dialogue_authority → supplied_clarification/_best_exchange → select_host_speech → existing immutable response adoption → API delivered-exchange recording → continuity GM recall → existing storage.

The existing dialogue_authority now projects topic_grounding: speaker_id, addressee, requested_subject, requested_information, reference, candidate_sources, selected_source, ambiguous and ownership. The social result carries turn-local topic_selection from authored candidates. Stable sources use `npc:<speaker>:<authored-topic-id>`; historical sources use delivered speaker/turn/adoption provenance. Accepted-response authorization_source remains the final adoption identity. These are request diagnostics over existing sources, not another knowledge database.

Only three production modules changed. No new NPC agent, generated-dialogue lane, memory store or world authority was added. History capacity grows from 8 to 32 in the same existing delivered_exchanges list because the former cap demonstrably evicts required conversation turns.
