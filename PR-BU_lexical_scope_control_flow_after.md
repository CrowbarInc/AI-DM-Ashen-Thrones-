# PR-BU lexical-scope control flow after

Deterministic repair. Model and gameplay API calls: zero. The production validator is `audit_realization_envelope_against_decision` in `game/gm_resolution_decision.py`.

## GEOGRAPHY

### Previous trigger

`patrol_route_or_geography`, second alternative.

Left head class included `split` beside `route`, `road`, `path`, `fork`, `marker`, `watchtower`, and `milestone`. The right class was `patrol`, `tracks`, `trail`, `broken twigs`, `bootprints`, or `evidence`, within 90 characters, inside one sentence.

On the preserved P1 retry sentence `The bell's wooden yoke is split, its surface showing clear evidence of damage.` the match was:

- span `[26, 67]`
- text `split, its surface showing clear evidence`
- left token `split`
- right token `evidence`

No patrol, route, road, path, or trail is in that span. `split` is the copula complement of the yoke. `evidence` is evidence of damage. The head class treated `split` as if it were a route noun.

### Physical-state path

`split` is no longer a route head. These stay off the geography recognizer:

- `The beam is split.`
- `The leather is split.`
- `The beam is split, with clear evidence of a crack along the timber.`
- `The bell's wooden yoke is split, its surface showing clear evidence of damage.`

Nearby `evidence` does not supply a route noun. The sentence can still fail for a different authority reason. Geography is not that reason.

### Route / geography path

A route noun has to be in the match. `splits` and `forks` are branch verbs on the right of that noun. `split` remains a right-hand token after a route noun, which is how `the patrol split` and `the trail split north` still match.

Still activated, and still rejected when the decision does not authorize them:

- `The road splits ahead.`
- `The trail split north.`
- `The trail forks toward the river.`
- `The patrol route splits near the gate.`
- `Broken twigs show the patrol took the old route, then split at a fork near the marker and watchtower.`

### Authorization / rejection

Unauthorized route matches still append `patrol_route_or_geography` and fail the narration audit.

Two repository paths that already accept stay accepted:

- Attributed speech. `The driver says, "The patrol took the old route and then split at the fork."` is an NPC claim. The geography pattern still matches the quoted words. The claim path records `npc_claim` and does not emit `patrol_route_or_geography`.
- Permitted movement. `You walk through the gate arch and reach the road beyond.` stays valid when the decision is a scene transition with a location mutation. That sentence does not carry `patrol_route_or_geography`.

An exact copy of an authored patrol-route sentence can still fail `patrol_route_or_geography`. Fact overlap does not clear that consequential code. That behavior was already true before this repair, including for `The missing patrol was last seen taking the northwest mud track past the crates.`

## CAUSALITY

### Previous trigger

`_EVENT_CAUSE_ATTRIBUTION_RE`, alternative `caused` followed by `it`, `this`, `that`, `the`, or `damage`.

On the preserved sentence `These details point to significant deterioration, though without further context it remains uncertain what exactly caused this wear or when it occurred.` the match was:

- span `[115, 126]` inside that sentence
- text `caused this`

The enclosing words are `remains uncertain what exactly caused`. `_UNRESOLVED_STATUS_EQUIVALENT_RE` matches `remains uncertain`, so `_marks_unresolved_status` already recorded `unknown_cause_actor_or_time`. `_UNKNOWN_SLOT_RE` does not match `uncertain`. It matches `remains unclear`. `_ordinary_residual_reasons` returned early only for `_UNKNOWN_SLOT_RE`, then appended `unauthorized_cause_attribution`. The verb's governing construction was not inspected.

### Direct attribution path

A cause match that is not inside an unresolved-cause construction still rejects when the decision does not authorize cause:

- `Neglect caused this damage.` → `unauthorized_cause_attribution`
- `The damage was caused by neglect.` → `unauthorized_causal_relation`
- `This happened because of neglect.` → `unauthorized_causal_relation`
- `Neglect caused this damage, though it remains uncertain what exactly caused this wear.` → `unauthorized_cause_attribution` on the first clause

`possibly from`, `because`, and `caused by` still go through `_CAUSAL_RELATION_RE`. That path was not widened.

### Qualified possible-cause path

`A sudden pull might have caused this.` on the preserved P1 decision stays `authorized_qualified_inference`. The uncertain-frame handling of `might` is unchanged. The new scope check does not treat `might` as an unresolved-cause construction.

### Explicit unresolved-cause path

`_causal_match_is_unresolved_cause` reuses `_UNRESOLVED_STATUS_EQUIVALENT_RE`. The status match and the causal verb have to sit in the same clause. A `what` / `which` / `who` / `why` has to link them. `and` or `but` between them keeps the verb an attribution.

These accept, with `unknown_cause_actor_or_time`, and without `unauthorized_cause_attribution`:

- `It remains uncertain what exactly caused this wear.`
- `What exactly caused this wear remains uncertain.`
- `It remains unclear what caused this.`
- `The cause cannot be determined from the visible evidence.`
- `It cannot be determined what caused this wear.`
- `We cannot determine what caused this wear.`

`cannot` / `can't determine` was added to the shared unresolved-status pattern, next to the passive `cannot be determined` that was already there. That is what lets the same helper see the active form.

### Authorization / rejection

When the decision carries the same sentence as an authorized causal fact, `Neglect caused this damage.` stays accepted. The scope helper does not run a whitelist on `caused this`. It only drops a verb that the unresolved-status marker governs.

## P1 RETRY

Narration, exact preserved text:

> The bell's wooden yoke is split, its surface showing clear evidence of damage. The leather hanger appears torn, frayed at the edges. These details point to significant deterioration, though without further context it remains uncertain what exactly caused this wear or when it occurred.

`declared_claims` is empty. Decision and corpus are the preserved P1 inspect decision and chapel scene.

### Before

Envelope `hard_valid: false`.

| Sentence | Path | Code |
| --- | --- | --- |
| wooden yoke is split … evidence of damage | second geography alternative, `split` then `evidence` | `patrol_route_or_geography` |
| remains uncertain what exactly caused this wear | `caused this` inside the status clause, status not allowed to govern the verb | `unauthorized_cause_attribution` |

The third sentence also recorded `authorized_qualified_inference` and `unknown_cause_actor_or_time`. The unauthorized cause row failed the sentence.

### After

Envelope `hard_valid: true`.

| Sentence | Path | Result |
| --- | --- | --- |
| wooden yoke is split … evidence of damage | physical-state split, no route noun | no `patrol_route_or_geography` |
| leather hanger appears torn | unchanged | no violation |
| point to deterioration … remains uncertain what exactly caused this wear | qualified inference, plus unresolved cause governing `caused this` | `authorized_qualified_inference`, `unknown_cause_actor_or_time` |

`unauthorized_cause_attribution` is absent. `patrol_route_or_geography` is absent.
