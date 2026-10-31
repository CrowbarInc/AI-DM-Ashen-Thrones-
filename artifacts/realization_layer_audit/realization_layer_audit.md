# Realization Layer Audit

Advisory only: this report is not CI-enforced and findings are not failures yet.
Interpret classifications alongside `game.realization_authority`.

## Summary by Severity
- INFO: 6752
- REVIEW: 435
- HIGH: 739

## Summary by Category
- fallback_authorship: 1106
- prompt_gpt_realization_risk: 1202
- raw_state_semantic_risk: 4733
- semantic_reconstruction: 885

## Top HIGH Findings
- `game/prompt_context.py:132` fallback_authorship / fallback: from game.fallback_behavior import build_fallback_behavior_contract
- `game/prompt_context.py:1741` fallback_authorship / fallback: else "backbone_fallback",
- `game/prompt_context.py:1772` semantic_reconstruction / reconstruct: "prompt_context_reconstructed_continuation": False,
- `game/prompt_context.py:1918` semantic_reconstruction / invent: "obey CTIR + shipped response_policy for facts; do not invent an alternate structural plan from raw scene text.",
- `game/prompt_context.py:1926` semantic_reconstruction / invent: "Use narration_seam_audit.dialogue_social_plan_failure_codes for machine-readable trace; do not invent speaker/intent/tone/pressure or generic conversational glue to compensate.",
- `game/prompt_context.py:1938` semantic_reconstruction / invent: "It does not establish objective world truth, inventory, a durable trait, relationship state, quest evidence, or declared_claims. "
- `game/prompt_context.py:1939` semantic_reconstruction / invent: "If reply_plan_kind is consequential_information_request, genuine_refusal, or genuine_uncertainty, preserve that limit and do not convert it into helpful invention. "
- `game/prompt_context.py:1944` semantic_reconstruction / invent: "Do not invent patrols, allegiances, rewards, quests, keys, or hidden facts. "
- `game/prompt_context.py:1976` semantic_reconstruction / invent: 'Follow authoritative engine state for who is present, player positioning, scene transitions, and check outcomes; narrate outcomes without inventing structured results.',
- `game/prompt_context.py:2095` semantic_reconstruction / invent: "LEAD REGISTRY (authoritative slice): Use top-level lead_context only as supplied—do not invent leads, facts, or journal summaries. "
- `game/prompt_context.py:2113` semantic_reconstruction / invent: "Use lead_context.urgent_or_stale_leads to surface unattended time pressure or stale threads as diegetic tension or reminders—only as implied by those rows; do not invent urgency.",
- `game/prompt_context.py:2117` semantic_reconstruction / invent: "If follow_up_pressure.from_leads.has_stale is true, you may surface reminder, pressure, or unattended-thread beats that fit the scene—without inventing facts beyond lead_context.",
- `game/prompt_context.py:2118` semantic_reconstruction / invent: "If follow_up_pressure.from_leads.npc_has_relevant is true, you may let the active NPC exchange reflect relevance to those threads—within knowledge_scope and without inventing registry facts.",
- `game/prompt_context.py:2119` semantic_reconstruction / invent: "If follow_up_pressure.from_leads.has_escalated_threat is true, bias tension beats toward unattended threat rows in lead_context (escalation fields)—without inventing facts beyond those rows.",
- `game/prompt_context.py:2501` fallback_authorship / fallback: fallback_behavior_contract = build_fallback_behavior_contract(
- `game/prompt_context.py:2602` fallback_authorship / fallback: "(narrative_authority, fallback_behavior, tone_escalation, anti_railroading, context_separation, "
- `game/prompt_context.py:2867` fallback_authorship / fallback: 'fallback_behavior': fallback_behavior_contract,
- `game/prompt_context.py:2957` fallback_authorship / fallback: 'fallback_behavior',
- `game/gm.py:35` fallback_authorship / fallback: from game.diegetic_fallback_narration import render_scene_momentum_diegetic_append
- `game/gm.py:38` fallback_authorship / fallback: attach_realization_fallback_family,

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
