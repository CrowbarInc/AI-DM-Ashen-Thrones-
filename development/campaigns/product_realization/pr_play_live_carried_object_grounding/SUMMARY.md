# Summary

Milestone: `pr_play_live_carried_object_grounding`

Verdict: **A/PASS** for the deterministic repair. This is not a live-model pass.

LIVE PROVIDER CALLS: 0

LIVE VALIDATION: NOT EXECUTED

The ordinary interpretation catalog now includes the current character's present inventory beside the existing scene catalog. A unique carried Spellbook can be bound from an explicit name, from `volume` as a book-class word, from a follow-up `that same book`, and from a captured model record whose target is null. Two books stay ambiguous. An unknown object stays unresolved. A fabricated id is rejected and is not replaced with the Spellbook. Prepared-spell questions publish Daze, Detect Magic, Magic Missile, and Shield from the sheet, say those are prepared spells rather than pages written in the book, and do not cast or spend a slot. Recorded-content questions say the sheet does not record spells written in the book. Informational replies do not advance the turn. The notice board examination still does.

## Root cause

The live catalog was `visible_catalog` and the character was not passed into interpretation. The probe's permitted ids omitted `spellbook`. A1 returned `USE_VISIBLE_OBJECT` with a null target, and the host stopped at communication-before-execution. `volume` is not a compound head of `Spellbook`, so the older examine owner never answered. A2 and A3 asked which spellbook even though the sheet has one. Those model strings were preserved and replayed. Whether a future model selects the newly listed id is unmeasured.

## Files changed

- `game/carried_object_grounding.py` — catalog, resolver, sheet answers, model-record policy.
- `game/live_chat_interpretation.py` — catalog rows include carried and equipped objects; `interpret_production_turn` takes the character; the prompt says to use a listed id and not to treat a question as a cast.
- `game/conversational_orchestration.py` — deterministic carried answers run after the existing inspection owner; stored interpretation records are grounded before the communication decision.
- `game/api.py` — the loaded character and recent log are passed into interpretation and into the three interpretation-record decisions.
- `tests/test_live_carried_object_grounding.py` — acceptance and captured-record replays.
- `docs/NEXT_SESSION.md` — this handoff.

`I examine the book.` remains on the older inspection owner. An unresolved examine in a stored record, such as the footprints sentence, returns to the existing referent decline.

## Results

Acceptance: 18 grounding tests plus `test_missing_footprints_are_not_created`, 19 passed. Adjacent unique-carried, inventory-binding, and live-interpretation tests: 43 passed.

Combined: 455 passed / 17 failed. Focused: 470 passed / 1 failed (`test_api_roll_initiative_returns_canonical_resolution`). New identities: none. Provider records in regression: 0.

Catalog construction median 0.0122 ms. Reference matching median 0.1132 ms. Model-output validation median 0.2439 ms. Prepared-spell retrieval median 0.0029 ms. Compact catalog token estimate 166 to 263, delta 97, on the bytes/3 estimator. Not a live latency claim.

## Not done

No provider call. No commit. No push. A4 and B1 stay on the coverage gate. `pr_play_social_check_repeat_and_legacy_stance` stays paused. The next action is a separate authorization for four live calls, ceiling $0.06, described in `LIVE_VALIDATION_PLAN.md`. That run has not started.
