# PR-CM secondary metadata finding

PR-CM does not repair this. It is outside the passive-pressure test contract.

## Observation

Fallback narration:

`As you watch the scene, a guard leans near the checkpoint, watching the road.`

can be stored as a contextual lead:

- kind: `visible_suspicious_figure`
- subject: `as you`
- position: `near the checkpoint, watching the road`
- stored key: `visible_suspicious_figure_as_you_near_the_checkpoint_watching_the_road`

The candidate helper's own key uses kind `visible_figure` before `extract_contextual_leads_from_text` re-keys it with the suspicious-figure kind.

## Extractor

`game.gm._extract_visible_figure_candidate`, called from `game.gm.extract_contextual_leads_from_text`.

The sentence contains `guard`, so it is a visible-figure candidate, and `watching`, so the kind is `visible_suspicious_figure`.

`_LEAD_SUBJECT_VERB_MARKERS` includes `" watch "`. That marker matches `As you watch the scene` before the later clause `a guard leans`. The subject slice is `As you`. `_clean_lead_subject` only strips a leading `a` / `an` / `the`, so the stored subject stays `as you`.

`game.gm.remember_recent_contextual_leads` writes that record onto `session.scene_runtime[scene].recent_contextual_leads`. Perception grounding can also resync leads from a grounded replacement through the same extractor.

## Durable

Yes. The diagnostic turn stores the record, a later wait leaves it in place, and `storage.load_session()` still returns it.

## Subsequent turns

A following hard-valid wait does not speak an approach built from the bad subject. In the diagnostic, the third line stays `Rain continues to bead on the stone.`

The record is still consumed as context:

- The next provider payload includes the stored lead key. `game.prompt_context` projects recent contextual leads as `contextual_thread` text `{subject} [{key}]`.
- `game.response_policy_enforcement._pick_passive_pressure_source` prefers that lead and returns `source=lead_figure`, `subject=as you`.
- `_render_passive_pressure_beat` ignores the source and still renders a grounded line that names the guard. It does not emit `Shadow as you`.

## NPC and scene authority

The record does not create an NPC, change `guard_captain` or `tavern_runner`, or rewrite the scene's visible facts.

`game.narration_state_consistency` already treats this extraction as non-authoritative continuity. It must not mint gameplay authority when no structured lead exists.

The practical effect is model context and pressure-source selection. A live provider can see `as you` as a contextual thread. The current beat renderer does not turn that thread into an approach.

## Recommended separate repair

Bound a later cycle to `_extract_visible_figure_candidate` only.

Do not treat the established observe opener `As you watch the scene` as the figure subject. The figure in this sentence is the guard. Keep the grounded fallback sentence. Do not restore interruption templates, and do not change world-tick rules.

Fixture: `tests/test_pr_cm_passive_pressure_contract.py::test_diagnostic_scene_stall_fallback_stores_as_you_lead_subject`.

That test locks the current defect so the repair cycle can see it change. It is not a requirement that passive waits invent a confrontation.
