# RC-10 / RC-21 Policy Implementation

Campaign: RC-10 / RC-21 Policy Implementation  
Identifier: `rc10_rc21_policy_implementation_20260919`  
Date: 2026-09-19  
Type: policy implementation  
Prior analysis: `docs/rc10_rc21_policy_resolution_dossier.md`

# Decisions Implemented

```text
RC-10 = A
RC-21 = B + C
```

These are settled. They are no longer pending.

# RC-10 = A

The retired raw token `compatibility_local_opening_deterministic` remains exclusively in
`tests/helpers/opening_fallback_evidence.py`.

`tests/test_fallback_incidence_report.py` now injects the historical authorship stamp through
`legacy_compatibility_local_opening_authorship_source()`. The RC-10 fence was not widened. Live
opening paths were not restored. Player-facing opening behavior did not change.

# RC-21 = B + C

Social redirects create official follow-up from authored or realized scene evidence. Narration or
NPC speech alone does not instantiate an NPC as authoritative world state.

Current `frontier_gate` canon does not author Lirael. The spoken Lirael reference therefore must
not instantiate `emergent_town_crier`. The authored notice-board landmark remains the valid
follow-up. The lead registry is the canonical store; `pending_leads` and clue surfaces are
projections.

The three former RC-21 failures were updated to lock that contract:

- authored notice-board follow-up plus registry ownership
- repeat-redirect merge / no duplicate authoritative rows
- distinction from an unrelated existing milestone pending row

The flavor-text negative remains: directional color without authored-scene evidence still creates
no destination lead.

# Residue

Cleaned because the policy now makes the treatment obvious:

- stale `game/clues.py` comment that claimed `frontier_gate` still authors Lirael
- leftover Lirael discoverable rumor in `default_scene("frontier_gate")`

Deferred because they raise a later lead-system design question, not a direct B+C consequence:

- `compat_pending_lead_needed` still keys off a scene target only
- intent parsing still reads `pending_leads` as the pursuit surface
- broader lead/clue overlap reduction remains deferred in `docs/current_focus.md`

Historical campaign records and old replay copies were left historical.

# Product Behavior

No player-facing opening change. No live destination-extractor change. Official Lirael follow-up
still requires restoring her as authored content, which this campaign did not do.

# Validation Baseline

Before: 6,450 collected, 6,347 passed, 4 failed, 99 skipped.  
After: 6,450 collected, 6,351 passed, 0 failed, 99 skipped.

Focused:

- RC-10 / opening fallback / incidence / classifier helper locks: 216 passed
- RC-21 social redirects / lead registry / pending-clue projections / pursuit / state authority: 118 passed
- Opening replay projection / ownership / scene-canon hygiene / opening-start seams: 30 passed

# Recommended Next Action

Review this clean post-policy baseline. Do not begin Calibration Round #2, State ↔ Narration
Consistency, simulated-player work, or new Product Realization features until that review.
