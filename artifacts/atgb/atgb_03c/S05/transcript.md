# S05 — ATGB-03C, trial 1

Captured 4/4; stop: none. Human judgments pending.

This uses the live-enabled production API path; individual replies may be host-owned. Technical completion is not gameplay success.

## S05.1

Player: Runner, what did you hear about the patrol?

AI-DM: Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

Capture: captured; resolution: question.

State evidence: `{"before": {"scene_id": "frontier_gate", "discovered_clues": [], "world_flag_names": [], "world_state_flag_names": [], "interlocutor": null, "transcript_entries": 0}, "after": {"scene_id": "frontier_gate", "discovered_clues": ["The runner heard the patrol vanished near muddy footprints northwest of the crates.", "Follow the missing patrol rumor"], "world_flag_names": [], "world_state_flag_names": [], "interlocutor": "tavern_runner", "transcript_entries": 1}}`

Host telemetry: `{"elapsed_ms": {"status": "recorded", "value": 3368}, "provider_call_count": {"status": "recorded", "value": 1}, "input_tokens": {"status": "recorded", "value": 1795}, "output_tokens": {"status": "recorded", "value": 181}, "retry_count": {"status": "recorded", "value": 0}, "estimated_cost": {"status": "unavailable", "value": null, "reason": "no_price_table"}, "provider_call_detail": {"interpretation_requests": "unavailable", "narration_requests": "unavailable", "retries": "unavailable"}}`

Accounting: see result.json → provider_accounting and provider_usage.jsonl.

## S05.2

Player: And the board, what does it say about the same patrol?

AI-DM: I cannot provide a validated response to that request.

Capture: captured; resolution: question.

State evidence: `{"before": {"scene_id": "frontier_gate", "discovered_clues": ["The runner heard the patrol vanished near muddy footprints northwest of the crates.", "Follow the missing patrol rumor"], "world_flag_names": [], "world_state_flag_names": [], "interlocutor": "tavern_runner", "transcript_entries": 1}, "after": {"scene_id": "frontier_gate", "discovered_clues": ["The runner heard the patrol vanished near muddy footprints northwest of the crates.", "Follow the missing patrol rumor"], "world_flag_names": [], "world_state_flag_names": [], "interlocutor": "tavern_runner", "transcript_entries": 2}}`

Host telemetry: `{"elapsed_ms": {"status": "recorded", "value": 1554}, "provider_call_count": {"status": "recorded", "value": 0}, "input_tokens": {"status": "host_reported_null", "value": null}, "output_tokens": {"status": "host_reported_null", "value": null}, "retry_count": {"status": "recorded", "value": 0}, "estimated_cost": {"status": "unavailable", "value": null, "reason": "no_price_table"}, "provider_call_detail": {"interpretation_requests": "unavailable", "narration_requests": "unavailable", "retries": "unavailable"}}`

Accounting: see result.json → provider_accounting and provider_usage.jsonl.

## S05.3

Player: Tell me more about that.

AI-DM: Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.

Capture: captured; resolution: conversational_clarify.

State evidence: `{"before": {"scene_id": "frontier_gate", "discovered_clues": ["The runner heard the patrol vanished near muddy footprints northwest of the crates.", "Follow the missing patrol rumor"], "world_flag_names": [], "world_state_flag_names": [], "interlocutor": "tavern_runner", "transcript_entries": 2}, "after": {"scene_id": "frontier_gate", "discovered_clues": ["The runner heard the patrol vanished near muddy footprints northwest of the crates.", "Follow the missing patrol rumor"], "world_flag_names": [], "world_state_flag_names": [], "interlocutor": "tavern_runner", "transcript_entries": 3}}`

Host telemetry: `{"elapsed_ms": {"status": "recorded", "value": 2166}, "provider_call_count": {"status": "recorded", "value": 1}, "input_tokens": {"status": "recorded", "value": 1948}, "output_tokens": {"status": "recorded", "value": 198}, "retry_count": {"status": "recorded", "value": 0}, "estimated_cost": {"status": "unavailable", "value": null, "reason": "no_price_table"}, "provider_call_detail": {"interpretation_requests": 1, "narration_requests": 0, "retries": 0}}`

Accounting: see result.json → provider_accounting and provider_usage.jsonl.

## S05.4

Player: The runner's version, not the notice.

AI-DM: Tavern Runner says, "I couldn't tell you."

Capture: captured; resolution: question.

State evidence: `{"before": {"scene_id": "frontier_gate", "discovered_clues": ["The runner heard the patrol vanished near muddy footprints northwest of the crates.", "Follow the missing patrol rumor"], "world_flag_names": [], "world_state_flag_names": [], "interlocutor": "tavern_runner", "transcript_entries": 3}, "after": {"scene_id": "frontier_gate", "discovered_clues": ["The runner heard the patrol vanished near muddy footprints northwest of the crates.", "Follow the missing patrol rumor"], "world_flag_names": [], "world_state_flag_names": ["faction_house_verevin_agenda_advanced", "faction_ash_cowl_agenda_advanced", "faction_ordo_pyric_agenda_advanced"], "interlocutor": "tavern_runner", "transcript_entries": 4}}`

Host telemetry: `{"elapsed_ms": {"status": "recorded", "value": 4517}, "provider_call_count": {"status": "recorded", "value": 1}, "input_tokens": {"status": "recorded", "value": 2050}, "output_tokens": {"status": "recorded", "value": 232}, "retry_count": {"status": "recorded", "value": 0}, "estimated_cost": {"status": "unavailable", "value": null, "reason": "no_price_table"}, "provider_call_detail": {"interpretation_requests": "unavailable", "narration_requests": "unavailable", "retries": "unavailable"}}`

Accounting: see result.json → provider_accounting and provider_usage.jsonl.
