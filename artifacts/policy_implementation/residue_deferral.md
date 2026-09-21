# RC-21 Residue Inspection

Campaign: `rc10_rc21_policy_implementation_20260919`

Inspected against settled policy B+C. Historical artifacts were not rewritten.

## Cleaned

| Surface | Why the treatment follows from B+C |
|---|---|
| `game/clues.py` named-crier comment | The comment claimed current `frontier_gate` still authors Lirael. That is false under current canon and would re-open Policy A. |
| `game/defaults.py` `default_scene("frontier_gate")` Lirael discoverable | The live scene file does not author Lirael. The bootstrap fallback must not re-author her as discoverable evidence. |

## Deferred

| Surface | Why this is not a direct B+C repair |
|---|---|
| `compat_pending_lead_needed` | The flag still reports scene-target pending only. Social extraction already writes rumor/NPC pending through `_lead_has_pending_target`. Changing the engine-signal flag would be a lead-system API decision. |
| Intent parsing over `pending_leads` | Pursuit still consumes the compatibility projection. Migrating that reader to the registry is the deferred lead/clue cleanup, not this campaign. |
| Broader lead/clue overlap | Already deferred in `docs/current_focus.md`. RC-21 C ratifies the store model; it does not authorize that cleanup batch. |

## Not in scope

- Restoring Lirael as authored `frontier_gate` content
- Changing destination extraction
- Rewriting historical replay or campaign artifacts
