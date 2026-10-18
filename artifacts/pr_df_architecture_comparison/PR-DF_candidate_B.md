# PR-DF Candidate B — AI Planner + Deterministic Executor

Hypothetical. No planner is implemented in this cycle.

Candidate B inserts one non-authoritative plan in front of the resolvers Candidate A already uses. The plan does not write state. The executor does not invent a second rules engine.

The existing `interpret_for_contract` proposal is the nearest live seam: one structured object, closed operations, rejected on malformed output. B widens that object from one operation to an ordered step list, and it adds an executor. It does not reuse the interpretation call as a hidden planner during A's baseline.

## Plan contract

The planner returns JSON. `authority` is required and must be the string `non_authoritative_proposal`. Any other value is a failed plan. The executor does not ask the model to repair authority wording more than once.

```json
{
  "authority": "non_authoritative_proposal",
  "plan_id": "string",
  "player_utterance": "string",
  "intent_summary": "string",
  "referenced_entities": [
    {"raw": "string", "proposed_id": "string or null", "role": "target|addressee|destination|speaker"}
  ],
  "uncertainty": {
    "ambiguous": false,
    "clarification_question": null,
    "unresolved_spans": []
  },
  "world_queries": [
    {"query_id": "string", "kind": "visible_scene|known_entity|npc_context|clock|scheduled_event", "args": {}}
  ],
  "actions": [
    {
      "step_id": "s1",
      "depends_on": [],
      "operation": "perceive|inspect|ask|repeat|confirm|follow|act|advance_time",
      "proposed_resolver": "social|exploration|combat|travel|adjudication|none",
      "target_id": null,
      "target_raw": null,
      "adjudication": null,
      "expects_mutation": "none|scene|world|combat|clock|interaction"
    }
  ]
}
```

`adjudication` on a step, when present, is `{ "skill_id": null, "dc_hint": null, "reason": "string" }`. `dc_hint` is ignored. The skill resolver owns the DC.

Fields the planner must not send, and which the executor drops if sent: rolled totals, hit points, clue ids, hidden facts, world-flag assignments, narration prose that is to be stored as canon, and `authority` values other than the required literal.

## What the executor does

The executor is harness code plus the existing functions. It is not a new authority owner.

1. **Validate the object.** Reject a missing `authority` literal, unknown operations, cycles in `depends_on`, more than four steps, or a step whose `proposed_resolver` is outside the enum. Four is an experiment cap, not a rules change.

2. **Validate references.** Resolve `proposed_id` only through the canonical referent catalog (`build_canonical_referent_catalog`, already used by `attach_interaction_obligation`). An id that is not in the catalog is cleared. If more than one catalog row matches `target_raw` and the plan did not set `uncertainty.ambiguous`, the executor sets ambiguous and stops.

3. **Answer world queries from the same projections A uses.** Visible scene facts, known entities, narration visibility, clocks, and tick events already on the session. Queries never return `gm_only_hidden_facts` or hidden motives. At most one query round, then one replan. A second replan is a failed turn.

4. **Reject impossible steps before any mutation.** Examples: combat resolver while `in_combat` is false; travel to an unknown scene id; downtime or rest (current classification is `downtime_engine_not_wired`); a social step whose addressee is off the scene; a step that depends on a rejected step.

5. **Ask for clarification instead of executing** when `uncertainty.ambiguous` is true or a reference was cleared and the step cannot be retargeted from discourse focus. The player-facing clarification is the engine line already used for ambiguous contracts, or the plan's question after it is checked for hidden-fact terms. No step runs.

6. **Execute permitted steps in dependency order.** For each step the executor builds the same normalized action or combat arguments the current resolvers accept, calls `select_ordinary_resolver` on a contract built from that step (not from the raw plan), and calls `resolve_social_action`, `resolve_exploration_action`, `resolve_noncombat_action`, or `resolve_attack` / `resolve_skill`. If the contract selector disagrees with `proposed_resolver`, the contract wins and the disagreement is logged. The plan does not override the selector.

7. **Resource accounting.** Combat HP and conditions change only inside `resolve_attack` and the condition helpers. Clocks change only inside `advance_clock`. There is no inventory API to call. A step that asks to spend an item is rejected as unsupported.

8. **Time.** The harness calls `advance_world_tick` and `advance_clock(..., "time_pressure", 1)` once, at the same point `chat` does, for every candidate including A. A plan step `advance_time` is accepted only as an acknowledgement of that single tick. A second call is a failed step. Downtime still does not resolve.

9. **Mutation boundary.** The harness deep-copies session, world, scene, and combat before each step. It then calls the existing mutator on the copy. A rejected or exception-raising step leaves the copy at the last successful step. Earlier successful steps stay committed on the copy. There is no engine undo. The production files are never the copy.

10. **Narration.** After the last successful step, the harness calls the existing `build_messages` path on the resulting resolution, with the same envelopes A uses. The planner's `intent_summary` is not player-facing text and is not written into the world.

## Interfaces that already fit

| Need | Existing surface |
|---|---|
| Non-authoritative structured proposal | `InterpretationProposal` / `parse_interpretation_output` |
| Closed operations | `_ALLOWED_OPERATIONS` in `semantic_interpreter.py` |
| Reference list | `build_canonical_referent_catalog` |
| Selector | `select_ordinary_resolver`, `select_resolver_family` |
| Social / exploration / combat execution | current resolvers |
| Contradiction guard | `reject_contradicting_action` |
| One-step mutation | `_apply_authoritative_resolution_state_mutation` |
| Ambiguous stop | contract `ambiguous` and `obligation_preserving_fallback_line` |
| Visibility | `build_narration_visibility_contract` |

## Interfaces that do not exist

- A plan schema and a validator for `depends_on`.
- A loop that feeds step N's resolution into step N+1 without going through `chat`.
- A harness snapshot. Tests already copy session documents (`create_fresh_session_document`, PR-DB). That pattern is the snapshot. It is not a transaction object inside `api.py`.
- A rule that the post-narration gateway must not run on experiment turns. The harness omits `_apply_post_gm_updates` unless a scenario explicitly scores that seam.

## What this design refuses

The planner does not roll dice, set flags, reveal secrets, or promote an incidental sentence into a clue. Those outcomes appear only when an existing resolver returns them.
