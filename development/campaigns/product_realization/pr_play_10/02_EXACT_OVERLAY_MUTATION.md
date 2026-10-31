# 02 — Exact Overlay Mutation

PR-PLAY-10 · 2026-10-30 America/New_York · evidence_scope: structural_only.

`exact_historical_overlay_diff.json` is the exact structured before/after comparison, including
every added list item and mutation key, prior presence/value, provenance and authorization.
The field existed as an object. Three scene overlays existed before and after. Only frontier_gate
changed: five visible_facts_add strings appended to an empty list; mutations gained empty
discoverable_clues_add / hidden_facts_add lists and mode="social". Nothing was removed.
market_quarter and old_milestone remained byte-value identical. No runtime entity, discovered clue,
or state flag changed. Overlay identifier is the scene key; there is no separate overlay UUID.

All five strings match authored opening_seed_facts after case / terminal full-stop normalization:
rain/banners, noble townhouse, still threadbare figure, congested approach, notice board.
They describe locations, objects and observable scene facts; they create no NPC identity.
Mode equals authored scene.mode. The complete provider parsed_response explicitly contains
these exact scene_update strings and mode. This is not inference from narration: the still
figure detail has no exact corresponding sentence in the delivered narration. Several declared
realization claims cover rain/crowd/board, but no one-to-one declaration ID grants persistence
for every overlay string. Authored public seed content plus structured update plus native
adoption and accepted commit establish this particular mutation's authority.

Chain: captured parsed_response.scene_update → parser GM scene_update → policy cleanup →
typed legacy shape validation → native authoritative_adopted trace → overlay append →
opening acceptance → session save → committed opening_outcome → harness false positive.
Raw wire bytes were not captured: replay reproduces the exact captured parsed JSON value,
not an asserted byte-for-byte original network response. Capture reports truncated=false.
