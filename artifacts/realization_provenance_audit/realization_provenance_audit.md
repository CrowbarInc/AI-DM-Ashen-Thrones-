# Realization Provenance Coverage Audit

Advisory only: this report is not CI-enforced and findings are not failures.

## Summary by Severity
- INFO: 434
- REVIEW: 628
- HIGH: 585

## Summary by Matched Term
- `emergency`: 51
- `fallback`: 660
- `final_emitted_source`: 17
- `gm_output`: 214
- `player_facing_text`: 153
- `prepared_action_fallback_text`: 2
- `prepared_answer_fallback_text`: 2
- `repair`: 316
- `terminal`: 215
- `upstream_prepared_emission`: 17

## HIGH Findings
- `game/api.py:119` fallback: apply_deterministic_retry_fallback,
- `game/api.py:120` fallback: force_terminal_retry_fallback,
- `game/api.py:120` terminal: force_terminal_retry_fallback,
- `game/api.py:260` emergency: record_emergency_nonplan_output,
- `game/api.py:977` fallback: "fallback_repair",
- `game/api.py:2893` terminal: def _gm_planner_convergence_seam_terminal(
- `game/api.py:2910` fallback: out = force_terminal_retry_fallback(
- `game/api.py:2910` terminal: out = force_terminal_retry_fallback(
- `game/api.py:2922` emergency: record_emergency_nonplan_output(
- `game/api.py:2929` fallback: "emergency_fallback_label": "deterministic_terminal_repair",
- `game/api.py:2929` emergency: "emergency_fallback_label": "deterministic_terminal_repair",
- `game/api.py:2929` terminal: "emergency_fallback_label": "deterministic_terminal_repair",
- `game/api.py:2942` emergency: planner_convergence_emergency_exit: bool,
- `game/api.py:2944` fallback: fast_fallback_mode: bool,
- `game/api.py:2945` fallback: used_force_terminal_fallback: bool,
- `game/api.py:2945` terminal: used_force_terminal_fallback: bool,
- `game/api.py:2970` emergency: "emergency_nonplan_output": True,
- `game/api.py:2990` emergency: if planner_convergence_emergency_exit:
- `game/api.py:3015` emergency: "plan_driven": (not _emergency_exit) and _bundle_seam_ok,
- `game/api.py:3016` emergency: "emergency_nonplan_output": _emergency_exit or (not _bundle_seam_ok),
- `game/api.py:3026` emergency: planner_convergence_emergency_exit: bool,
- `game/api.py:3028` fallback: fast_fallback_mode: bool,
- `game/api.py:3029` fallback: used_force_terminal_fallback: bool,
- `game/api.py:3029` terminal: used_force_terminal_fallback: bool,
- `game/api.py:3037` emergency: planner_convergence_emergency_exit=planner_convergence_emergency_exit,
- `game/api.py:3039` fallback: fast_fallback_mode=fast_fallback_mode,
- `game/api.py:3040` fallback: used_force_terminal_fallback=used_force_terminal_fallback,
- `game/api.py:3040` terminal: used_force_terminal_fallback=used_force_terminal_fallback,
- `game/api.py:3050` emergency: planner_convergence_emergency_exit: bool,
- `game/api.py:3052` fallback: fast_fallback_mode: bool,

## REVIEW Findings
- `game/api.py:124` player_facing_text: _gm_has_usable_player_facing_text,
- `game/api.py:180` gm_output: apply_conservative_emergent_enrollment_from_gm_output,
- `game/api.py:265` repair: from game.upstream_response_repairs import apply_spoken_state_refinement_cash_out
- `game/api.py:465` player_facing_text: "player_facing_text": (
- `game/api.py:510` player_facing_text: "player_facing_text": gm["player_facing_text"],
- `game/api.py:513` gm_output: "gm_output": gm,
- `game/api.py:524` gm_output: return {"ok": True, "gm_output": gm, "resolution": resolution}
- `game/api.py:534` player_facing_text: "player_facing_text": (
- `game/api.py:573` player_facing_text: "player_facing_text": gm["player_facing_text"],
- `game/api.py:576` gm_output: "gm_output": gm,
- `game/api.py:587` gm_output: return {"ok": True, "gm_output": gm, "resolution": resolution}
- `game/api.py:594` player_facing_text: "player_facing_text": (
- `game/api.py:632` gm_output: "gm_output": gm,
- `game/api.py:641` gm_output: return {"ok": True, "gm_output": gm, "resolution": resolution}
- `game/api.py:673` player_facing_text: "player_facing_text": str(outcome.get("player_facing_text") or "No gameplay action was taken."),
- `game/api.py:714` player_facing_text: "player_facing_text": gm["player_facing_text"],
- `game/api.py:717` gm_output: "gm_output": gm,
- `game/api.py:728` gm_output: return {"ok": True, "gm_output": gm, "resolution": resolution}
- `game/api.py:773` player_facing_text: "player_facing_text": decision.player_facing_text or "No gameplay action was taken.",
- `game/api.py:829` player_facing_text: gm["player_facing_text"] = rewritten
- `game/api.py:831` player_facing_text: gm, text=gm["player_facing_text"],
- `game/api.py:854` player_facing_text: line=gm["player_facing_text"],
- `game/api.py:863` player_facing_text: delivered_text=gm["player_facing_text"],
- `game/api.py:877` player_facing_text: "response": gm["player_facing_text"][:1200],
- `game/api.py:888` player_facing_text: "player_facing_text": gm["player_facing_text"],
- `game/api.py:891` gm_output: "gm_output": gm,
- `game/api.py:905` gm_output: return {"ok": True, "gm_output": _strip_internal_gm_keys(gm), "resolution": resolution}
- `game/api.py:977` repair: "fallback_repair",
- `game/api.py:1107` player_facing_text: "player_facing_text": text,
- `game/api.py:1444` gm_output: "apply_conservative_emergent_enrollment_from_gm_output": {

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
