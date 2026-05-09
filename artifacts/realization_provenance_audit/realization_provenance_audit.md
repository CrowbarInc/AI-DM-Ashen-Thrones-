# Realization Provenance Coverage Audit

Advisory only: this report is not CI-enforced and findings are not failures.

## Summary by Severity
- INFO: 738
- REVIEW: 1280
- HIGH: 958

## Summary by Matched Term
- `emergency`: 86
- `fallback`: 1184
- `final_emitted_source`: 92
- `gm_output`: 427
- `player_facing_text`: 219
- `prepared_action_fallback_text`: 4
- `prepared_answer_fallback_text`: 3
- `repair`: 657
- `terminal`: 260
- `upstream_prepared_emission`: 44

## HIGH Findings
- `game/api.py:116` fallback: apply_deterministic_retry_fallback,
- `game/api.py:117` fallback: force_terminal_retry_fallback,
- `game/api.py:117` terminal: force_terminal_retry_fallback,
- `game/api.py:235` emergency: record_emergency_nonplan_output,
- `game/api.py:312` fallback: "fallback_repair",
- `game/api.py:1979` terminal: def _gm_planner_convergence_seam_terminal(
- `game/api.py:1996` fallback: out = force_terminal_retry_fallback(
- `game/api.py:1996` terminal: out = force_terminal_retry_fallback(
- `game/api.py:2008` emergency: record_emergency_nonplan_output(
- `game/api.py:2015` fallback: "emergency_fallback_label": "deterministic_terminal_repair",
- `game/api.py:2015` emergency: "emergency_fallback_label": "deterministic_terminal_repair",
- `game/api.py:2015` terminal: "emergency_fallback_label": "deterministic_terminal_repair",
- `game/api.py:2028` emergency: planner_convergence_emergency_exit: bool,
- `game/api.py:2030` fallback: fast_fallback_mode: bool,
- `game/api.py:2031` fallback: used_force_terminal_fallback: bool,
- `game/api.py:2031` terminal: used_force_terminal_fallback: bool,
- `game/api.py:2056` emergency: "emergency_nonplan_output": True,
- `game/api.py:2076` emergency: if planner_convergence_emergency_exit:
- `game/api.py:2101` emergency: "plan_driven": (not _emergency_exit) and _bundle_seam_ok,
- `game/api.py:2102` emergency: "emergency_nonplan_output": _emergency_exit or (not _bundle_seam_ok),
- `game/api.py:2112` emergency: planner_convergence_emergency_exit: bool,
- `game/api.py:2114` fallback: fast_fallback_mode: bool,
- `game/api.py:2115` fallback: used_force_terminal_fallback: bool,
- `game/api.py:2115` terminal: used_force_terminal_fallback: bool,
- `game/api.py:2123` emergency: planner_convergence_emergency_exit=planner_convergence_emergency_exit,
- `game/api.py:2125` fallback: fast_fallback_mode=fast_fallback_mode,
- `game/api.py:2126` fallback: used_force_terminal_fallback=used_force_terminal_fallback,
- `game/api.py:2126` terminal: used_force_terminal_fallback=used_force_terminal_fallback,
- `game/api.py:2136` emergency: planner_convergence_emergency_exit: bool,
- `game/api.py:2138` fallback: fast_fallback_mode: bool,

## REVIEW Findings
- `game/api.py:121` player_facing_text: _gm_has_usable_player_facing_text,
- `game/api.py:169` gm_output: apply_conservative_emergent_enrollment_from_gm_output,
- `game/api.py:240` repair: from game.upstream_response_repairs import apply_spoken_state_refinement_cash_out
- `game/api.py:312` repair: "fallback_repair",
- `game/api.py:616` gm_output: "apply_conservative_emergent_enrollment_from_gm_output": {
- `game/api.py:646` player_facing_text: "player_facing_text",
- `game/api.py:1357` player_facing_text: player_text_present=isinstance(gm.get('player_facing_text'), str) and bool(gm.get('player_facing_text')),
- `game/api.py:1375` player_facing_text: if isinstance(gm.get('player_facing_text'), str):
- `game/api.py:1377` player_facing_text: for clue_text in detect_surfaced_clues(gm['player_facing_text'], scene):
- `game/api.py:1393` player_facing_text: ptext = gm.get('player_facing_text') if isinstance(gm, dict) else None
- `game/api.py:1466` gm_output: gm_output=gm if isinstance(gm, dict) else None,
- `game/api.py:1478` gm_output: gm_output_present=isinstance(gm, dict),
- `game/api.py:1497` gm_output: gm_output_present=True,
- `game/api.py:1506` player_facing_text: narr = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else gm.get("player_facing_text")
- `game/api.py:1513` gm_output: operation="apply_conservative_emergent_enrollment_from_gm_output",
- `game/api.py:1522` gm_output: branch_label="apply_conservative_emergent_enrollment_from_gm_output",
- `game/api.py:1523` gm_output: classification=_post_gm_adoption_classification("apply_conservative_emergent_enrollment_from_gm_output"),
- `game/api.py:1532` gm_output: emergent_debug = apply_conservative_emergent_enrollment_from_gm_output(
- `game/api.py:1545` gm_output: operation="apply_conservative_emergent_enrollment_from_gm_output",
- `game/api.py:1791` player_facing_text: "player_facing_text": "The game master is temporarily unavailable. Please try again.",
- `game/api.py:1812` gm_output: def _attach_resolution_contract_metadata_to_gm_output(gm: dict | None, resolution: dict | None) -> None:
- `game/api.py:2015` repair: "emergency_fallback_label": "deterministic_terminal_repair",
- `game/api.py:2021` gm_output: _attach_resolution_contract_metadata_to_gm_output(out, resolution)
- `game/api.py:2172` repair: repair_terminal_player_facing_if_needed: Callable[..., dict],
- `game/api.py:2193` repair: return repair_terminal_player_facing_if_needed(
- `game/api.py:2513` repair: def _repair_terminal_player_facing_if_needed(
- `game/api.py:2519` repair: repair_started = _now_perf()
- `game/api.py:2521` player_facing_text: if _gm_has_usable_player_facing_text(gm_dict):
- `game/api.py:2522` repair: _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(repair_started))
- `game/api.py:2525` repair: repaired = ensure_minimal_social_resolution(

## Scanned Files
- `game/api.py`
- `game/gm.py`
- `game/gm_retry.py`
- `game/final_emission_gate.py`
- `game/final_emission_repairs.py`
- `game/social_exchange_emission.py`
- `game/upstream_response_repairs.py`
- `game/diegetic_fallback_narration.py`

## Notes
- HIGH means likely player-facing fallback/emergency prose lacks nearby provenance metadata.
- REVIEW means fallback or repair status is ambiguous and should be inspected.
- INFO means the context is already labeled or appears to be comment/doc-only.
