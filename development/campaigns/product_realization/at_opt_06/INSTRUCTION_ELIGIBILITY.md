# Instruction eligibility

## Original coupling

`_should_use_manual_play_compact_prompt` returns false for `manual_play_auto` when `must_advance_scene` is true. That obligation is copied from `transition.transition_required`. On the attached F3 rebuild the false location-change flag was the only compact blocker. The full 78-line list stayed for that reason. Forcing compact drops the visibility, first-mention, and speaker hard rules. AT-OPT-05 did not accept that loss.

## Corrected predicate

After the explicit `manual_play_compact` short-circuit, and after the non-auto rejection, `manual_play_auto` returns false when `stamp_matched_narrative_plan` is true.

The flag is `bundle_stamp_ok` and a non-empty narrative plan dict. The renderer only assigns that plan when the narration-plan bundle stamp equals the CTIR stamp. The predicate does not read player text.

Detached narration has no stamp-matched plan, so the previous blockers still decide compact eligibility. Profile `full` never selects compact. Explicit `manual_play_compact` still selects compact even when a plan is present.

## Plan-backed preservation

On the rederived F3 auto request, before and after instruction lists are identical: 78 lines. These remain present:

- `You MUST NOT reveal hidden or undiscovered facts.`
- `FIRST-MENTION CONTRACT (MANDATORY)`
- `SPEAKER SELECTION CONTRACT (HARD RULE)`
- `SCENE STATE ANCHOR (MANDATORY)`
- the policy-bridge sentence that forbids treating policy prose as authority to create facts
- `first_mention_contract`

The same full list is selected when the transition is required and when it is false. A genuine resolved transition still carries the `new_scene_draft` permission line. Repeated assembly of the same plan-backed request returns the same instruction list.

## Existing compact paths

- Explicit `manual_play_compact` on the same plan-backed fixture selects compact, omits the visibility MUST NOT line, and omits `first_mention_contract`.
- Detached `manual_play_auto` for “I wait and listen.” stays compact: 9 instructions, 50,793 bytes, identical before and after.
- The same sentence with a stamp-matched plan stays on the full list. The utterance text is not the signal.

## Authority

The compact hold is limited to stamp-matched plans. It does not force every provider request onto the full list. Publication classification was not edited. An operational refusal still does not become a completed gameplay publication, and it does not move `last_publication` or the scene.
