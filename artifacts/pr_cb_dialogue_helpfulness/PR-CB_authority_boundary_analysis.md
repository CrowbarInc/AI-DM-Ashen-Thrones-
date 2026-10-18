# Authority Boundary Analysis

| Category | Existing handling | PR-CA limitation |
| --- | --- | --- |
| Established world fact | Authored decision claims with provenance; objective assertions must respect visibility and decisions | Only baker existence/location and loaves are established; no bread varieties or preference |
| Consequential world invention | Requires authorized decision/state lanes; typed consequential proposals rejected as incidental | Narration-only cannot mutate world state or add declarations |
| Incidental NPC opinion | Quoted speech may be claim_only; typed npc_claim/opinion accepted at low consequence | Recipe warns against durable preference and says no NPC claim authorized without explaining transient claim permission |
| Incidental conversational improvisation | Typed incidental_fact categories include food_composition, mundane_service_detail, mannerism, local_color, ordinary_personal_detail | Narration-only schema exposes no improvisation_proposals field; transient speech still passes |
| NPC claim | Separate npc_claim provenance and claim_only authority; accepted ledger claims stay not_world_truth | General visibility instructions do not explain this distinction locally |
| Durable NPC characterization | Existing bounded ledger supports scene/session scopes and ordinary_personal_detail, with runtime authority; reuse projected for continuity | No new typed ledger entry can be proposed through narration-only; chat memory may preserve speech without durable ledger authority |

Deterministic controls accept 'I usually keep a rye loaf for myself.' as npc_claim/opinion, 'The darker loaf is popular with travelers.' as food_composition, and 'The baker prefers rye bread.' as ordinary_personal_detail. A consequential hidden-vault proposal is rejected. These controls demonstrate available typed lanes, not that narration-only can call them or that every statement in those categories is safe.

The misclassification is operational: absence of authored information becomes refusal even for subjective or mundane role-grounded speech. It is NOT evidence that the validator universally classifies categories 3-6 as consequential invention. Plain quoted preference passes as claim_only; persistent characterization is deliberately governed separately. The no-durable-fact ceiling is sound, but its generation wording overreaches if read as prohibiting the NPC from stating any preference.

References: game/bounded_improvisation.py:27-56 (categories/scopes), :230 (validation), game/gm_resolution_decision.py:1706 (ledger projection), :3123 (narration audit), game/gm.py:3767 (exact narration-only parser). No rules or persistence were changed.
