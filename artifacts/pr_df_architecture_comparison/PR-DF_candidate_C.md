# PR-DF Candidate C — Tool-Using AI + Authoritative Engine

Hypothetical. No tools are implemented in this cycle.

Candidate C lets the model ask for projections and request execution. Text the model emits between tool calls is not applied to the world. The only mutators are the tool handlers, and those handlers call the same functions as Candidate B's executor.

The experiment cap is four model rounds that may contain tool calls, plus one narration call that uses the existing payload. A fifth tool round ends the turn as `retry_budget_exceeded` and does not mutate further.

## Shared tool result shape

Every tool returns:

```json
{
  "ok": true,
  "tool": "name",
  "authority": "engine",
  "mutation": "none|committed|refused",
  "code": "ok or a stable failure code",
  "result": {}
}
```

`ok: false` leaves state unchanged for that call. Failure codes used below: `unknown_id`, `ambiguous`, `not_visible`, `unsupported`, `permission`, `conflict`, `already_applied`, `budget`.

The model is not given a tool that accepts a free-form world patch.

## Tools

### 1. `inspect_visible_scene`

| | |
|---|---|
| Input | `{ "scene_id": "string or null" }`. Null means the active scene. |
| Output | Scene id, location, player-visible facts, visible entity ids and labels, exits the engine already exposes to play. |
| Authority | Read-only projection of the active scene envelope and `narration_visibility`. |
| Permission | None beyond the current session. |
| Failure | Unknown scene id → `unknown_id`, no read of another scene's hidden layer. |
| Transaction | None. |

Hidden facts and GM notes are omitted even if they sit on the same scene document.

### 2. `query_known_entities`

| | |
|---|---|
| Input | `{ "raw": "string", "proposed_id": "string or null" }`. |
| Output | Zero, one, or many catalog rows: id, type, label, aliases, presence (`active` / off-scene / unknown). |
| Authority | `build_canonical_referent_catalog` plus presence already on `scene_state`. |
| Permission | Read. |
| Failure | Empty raw and empty id → `permission` (refuse a dump of every entity). More than one match → `ambiguous` and the row list, with no chosen target. |
| Transaction | None. |

### 3. `inspect_permitted_npc_context`

| | |
|---|---|
| Input | `{ "npc_id": "string" }`. |
| Output | Name, presence, relationship already in player-known state, last player-visible lines, discourse focus if this NPC is the interlocutor. Bounded improvisation entries of kind `npc_claim` whose epistemic status is rumor, hearsay, uncertain, speculative, or opinion. |
| Authority | Player-visible NPC projection. |
| Permission | NPC id must be in the visible-entity set or already the committed interlocutor. |
| Failure | Id outside that set → `not_visible`. Hidden motive fields are not a key in the output. |
| Transaction | None. |

### 4. `request_rules_adjudication`

| | |
|---|---|
| Input | `{ "kind": "attack|skill|social_check", "skill_id": null, "target_id": null, "raw": "string" }`. |
| Output | Whether the current resolvers would require a check, the player-facing check prompt if one is already built, and whether combat is active. |
| Authority | Read of resolver preconditions (`player_can_act`, skill-check request shape, social check request). |
| Permission | Must not call `resolve_attack` or `resolve_skill`. Those roll and, for attacks, write HP. |
| Failure | Preview function missing for that kind → `unsupported`. The tool must not guess a DC. |
| Transaction | None. A preview that cannot be done without rolling is a refusal, not a silent roll. |

`make_check_request` and `_is_pending_check_resolution` are the patterns to mirror. If a pure preview cannot be separated from a roll with the current function, the tool returns `unsupported` until a read-only wrapper exists. It does not call the rolling function "just to see."

### 5. `propose_action`

| | |
|---|---|
| Input | One step object from the Candidate B action schema. |
| Output | `{ "accepted_shape": true, "resolver": "string", "blocks": ["code"] }`. |
| Authority | Dry run of contract construction and `select_ordinary_resolver` on a copy. |
| Permission | None. |
| Failure | Shape errors use the same codes as the B validator. |
| Transaction | The dry run discards its copy. `mutation` is `none`. |

### 6. `request_action_execution`

| | |
|---|---|
| Input | The same step object. Optional `confirm: true` after a pending check. |
| Output | Resolver kind, success flag, public hint, ids of state fields that changed (scene id, hp delta, clue ids that became known). |
| Authority | Existing resolver, then `_apply_authoritative_resolution_state_mutation` on the harness copy. |
| Permission | `propose_action` for that step id must have returned no blocks on this turn, or the executor re-validates. The model cannot skip validation by calling execution first. |
| Failure | Any B rejection code. Exception from a resolver → `conflict`, copy restored to the pre-call snapshot. |
| Transaction | One resolver call is atomic on the harness copy. Earlier executed steps in the same turn remain. There is no cross-step undo. |

Dice, when a resolver rolls, use the experiment's injected roller so A, B, and C share the roll stream. The model does not supply the roll.

### 7. `inspect_resulting_state`

| | |
|---|---|
| Input | `{ "fields": ["scene_id", "visible_facts", "known_clues", "combat_public", "clocks"] }`. |
| Output | Those fields after the last committed execution, filtered by visibility. |
| Authority | Read of the harness copy. |
| Permission | `fields` must be a subset of the list above. `hidden_facts` is not a member. |
| Failure | Unknown field → `permission`. |
| Transaction | None. |

### 8. `advance_authorized_time`

| | |
|---|---|
| Input | `{ "clock": "time_pressure", "delta": 1, "world_tick": true }`. |
| Output | New clock value and the tick event list. |
| Authority | `advance_clock` and `advance_world_tick`. |
| Permission | The harness may allow this once per turn, matching `chat`. Delta other than 1, a clock other than `time_pressure`, or a second call → `already_applied`. |
| Failure | Downtime, long rest, and short rest are `unsupported` (`downtime_engine_not_wired`). |
| Transaction | The single tick is committed on the copy. It is the same tick A receives from the harness, not an extra one. |

## Read versus write

| Tool | State change |
|---|---|
| `inspect_visible_scene` | No |
| `query_known_entities` | No |
| `inspect_permitted_npc_context` | No |
| `request_rules_adjudication` | No |
| `propose_action` | No |
| `request_action_execution` | Yes, through current resolvers |
| `inspect_resulting_state` | No |
| `advance_authorized_time` | Yes, one shared tick |

Narration generation is not a tool. It is the same post-resolution `build_messages` call used by A and B. Declared claims in that narration still do not authorize themselves. The current prompt already says declarations do not grant world-truth authority.

## What the model cannot do

It cannot pass a JSON world update, a scene draft, or a sentence to be stored as a fact. Those channels exist on the production GM object (`world_updates`, `scene_update`, `new_scene_draft`). The experiment harness does not expose them and does not call `_apply_post_gm_updates`.
