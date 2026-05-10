# Realization Layer Audit

Advisory only: this report is not CI-enforced and findings are not failures yet.
Interpret classifications alongside `game.realization_authority`.

## Summary by Severity
- INFO: 8947
- REVIEW: 696
- HIGH: 1300

## Summary by Category
- fallback_authorship: 1858
- prompt_gpt_realization_risk: 1533
- raw_state_semantic_risk: 6335
- semantic_reconstruction: 1217

## Top HIGH Findings
- `game/prompt_context.py:132` fallback_authorship / fallback: from game.fallback_behavior import build_fallback_behavior_contract
- `game/prompt_context.py:681` semantic_reconstruction / invent: "turn—without inventing facts beyond visibility and narrative authority.",
- `game/prompt_context.py:1755` fallback_authorship / fallback: else "backbone_fallback",
- `game/prompt_context.py:1786` semantic_reconstruction / reconstruct: "prompt_context_reconstructed_continuation": False,
- `game/prompt_context.py:1930` semantic_reconstruction / invent: "obey CTIR + shipped response_policy for facts; do not invent an alternate structural plan from raw scene text.",
- `game/prompt_context.py:1938` semantic_reconstruction / invent: "Use narration_seam_audit.dialogue_social_plan_failure_codes for machine-readable trace; do not invent speaker/intent/tone/pressure or generic conversational glue to compensate.",
- `game/prompt_context.py:1985` semantic_reconstruction / invent: 'Follow authoritative engine state for who is present, player positioning, scene transitions, and check outcomes; narrate outcomes without inventing structured results.',
- `game/prompt_context.py:2110` semantic_reconstruction / invent: "LEAD REGISTRY (authoritative slice): Use top-level lead_context only as supplied—do not invent leads, facts, or journal summaries. "
- `game/prompt_context.py:2128` semantic_reconstruction / invent: "Use lead_context.urgent_or_stale_leads to surface unattended time pressure or stale threads as diegetic tension or reminders—only as implied by those rows; do not invent urgency.",
- `game/prompt_context.py:2132` semantic_reconstruction / invent: "If follow_up_pressure.from_leads.has_stale is true, you may surface reminder, pressure, or unattended-thread beats that fit the scene—without inventing facts beyond lead_context.",
- `game/prompt_context.py:2133` semantic_reconstruction / invent: "If follow_up_pressure.from_leads.npc_has_relevant is true, you may let the active NPC exchange reflect relevance to those threads—within knowledge_scope and without inventing registry facts.",
- `game/prompt_context.py:2134` semantic_reconstruction / invent: "If follow_up_pressure.from_leads.has_escalated_threat is true, bias tension beats toward unattended threat rows in lead_context (escalation fields)—without inventing facts beyond those rows.",
- `game/prompt_context.py:2516` fallback_authorship / fallback: fallback_behavior_contract = build_fallback_behavior_contract(
- `game/prompt_context.py:2678` semantic_reconstruction / invent: "On follow-up pressure turns, change stance, detail, uncertainty boundary, reaction, or next step—without inventing facts. "
- `game/prompt_context.py:2679` fallback_authorship / fallback: "Avoid generic non-answers when a substantive or bounded-partial reply is available; when fallback_behavior.uncertainty_active is true, brevity and honest limits override polish. "
- `game/prompt_context.py:2685` fallback_authorship / fallback: + _fallback_behavior_instr
- `game/prompt_context.py:2942` fallback_authorship / fallback: 'fallback_behavior': fallback_behavior_contract,
- `game/prompt_context.py:3032` fallback_authorship / fallback: 'fallback_behavior',
- `game/gm.py:31` fallback_authorship / fallback: from game.diegetic_fallback_narration import render_scene_momentum_diegetic_append
- `game/gm.py:34` fallback_authorship / fallback: attach_realization_fallback_family,

## Scanned Files
- `game/prompt_context.py`
- `game/gm.py`
- `game/gm_retry.py`
- `game/final_emission_gate.py`
- `game/final_emission_repairs.py`
- `game/social_exchange_emission.py`
- `game/diegetic_fallback_narration.py`
- `game/upstream_response_repairs.py`
- `game/narrative_authenticity.py`
- `game/fallback_behavior.py`
- `game/api.py`
- `game/opening_scene_realization.py`

## Notes
- The scanner is heuristic and intentionally advisory.
- HIGH means read the hunk first; it does not prove a runtime behavior bug.
- REVIEW means semantic ownership language appears in a sensitive layer.
- INFO usually covers comments, docs, constants, or benign references.
