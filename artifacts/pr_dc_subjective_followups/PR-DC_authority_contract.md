# PR-DC Authority Contract

A harmless experiential question may use the existing `harmless_subjective_response_permitted` plan when every row below holds. If any row is uncertain, the classifier keeps `genuine_uncertainty` or the stricter plan already chosen.

| # | Requirement | How it is enforced |
|---|---|---|
| 1 | Grounded, authorized NPC speaker | `resolve_social_action` reaches the reply plan only after an addressable NPC resolves. Speaker selection is unchanged. |
| 2 | Current social interaction | Experiential matching runs only for `question` and `social_probe`. |
| 3 | Ordinary experiential question | The line must match a closed comfort, fatigue, bother, stress, enjoyment-of-work, or subjective-difficulty frame. |
| 4 | No restricted knowledge | `_RESTRICTED_SOCIAL_INFO_RE` still wins and yields `genuine_refusal`. The experiential blocker also rejects secret, hidden, schedule, password, and credential wording. |
| 5 | No unresolved authored factual obligation | A prior revealed topic still yields `authoritative_answer_available` before any subjective match. |
| 6 | No consequential adjudication | `_CONSEQUENTIAL_SOCIAL_INFO_RE` still wins. The experiential blocker also rejects murder, assassination, proof, guilt, allegiance, and loyalty wording. |
| 7 | No requested world-state mutation | The plan still sets `durable_state_mutation_allowed` false. Maneuver action types do not take the experiential branch. |
| 8 | No hidden-information request | Secret, hidden, tunnel, password, and confidential wording stay on refusal or uncertainty. |
| 9 | No unsupported objective world assertion required | Accepted frames ask for the addressee's own impression. `objective_world_fact_authority` remains `none`. `npc_speech_authority` is `claim_only`. |
| 10 | Relevant conversation continuity | Continuity is supplied by the existing social target. The classifier does not treat history, a question mark, or a pronoun as authorization. |
| 11 | Existing uncertainty and authority rules remain enforceable | Hostile disposition still refuses. Blocked and third-person lines stay uncertain. Hard validators were not weakened. |

## Permitted subject frames

- discomfort while standing, waiting, working, or sitting
- personal preference already covered by the preference pattern, including "why do you prefer"
- ordinary fatigue addressed to "you"
- subjective difficulty of keeping watch, standing, waiting, working, or staying awake
- getting used to that difficulty "after a while"
- bother from ordinary conditions
- the work being stressful
- enjoying the work, standing, or waiting

## Kept off this plan

- a named other role as the experiencer ("does the baker", "does the innkeeper")
- gate weaknesses, smugglers, abandoned posts, defenses, hidden tracks, factions
- patrol location, missing patrol, secret tunnel, criminal past
- unlock, waive, persuade, promise, safe passage, assassination
- travel parses such as "leave", which never reach this function

Qualifying words such as "seems" or "perhaps" are not authorization. A question mark alone is not authorization.
