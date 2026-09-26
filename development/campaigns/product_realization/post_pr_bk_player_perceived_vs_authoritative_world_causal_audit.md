# Post-PR-BK Causal Audit — Player-Perceived World vs Authoritative World

Session `735ebd1cfb4567c4f97df6dc`. Bundle `artifacts/human_playtests/20260926_post_pr_bk_latest_human_playtest/`. Checkpoint at audit start: `5555a66`. No production code change. The playtest bundle was not modified.

Evidence notes: `artifacts/human_playtests/post_pr_bk_state_narration_audit/`.

## Answer

The hypothesis holds, in a narrower form than "the whole session was one narration drift."

The player was told, on the first human turn, that the notice board contained a curfew-hour schedule and the patrol's northwest route. State had not discovered that route, and no hours exist. On the next turn the route became a real discovery, so later travel was aimed at an authoritative clue.

The break that made the rest of the play incoherent is log entry 06. The player proceeded northwest. The parser returned no action. Scene id stayed `frontier_gate`. The model narrated a journey past crates, sheds, lanterns, and broken banners, and its `scene_update` was stored as overlay facts. Turns 07–09 are the player using that narrated place. The simulation did not contain it.

PR-BK did not fail. PR-BF did not regress. A sibling path never entered the travel kind PR-BF guards.

## What the simulation actually did

| Log | Player tried | Owner result | Heard result |
| --- | --- | --- | --- |
| 00 | campaign start | opening of `frontier_gate` | opening seeds, including taxes, curfews, missing patrol |
| 01 | approach the notice board | failed `social_probe`, no target, no discovery | a curfew-hour schedule and the undiscovered route |
| 02 | examine the curfew section for times and districts | `notice_board` discovered `notice_patrol_route` | crowd stock plus the patrol route |
| 03 | ask the tavern runner how to get around | runner bound; `reply_kind` refusal; no topic revealed | runner states the patrol route |
| 04 | how many soldiers disappeared | runner kept; quantity question | runner cannot answer. Correct |
| 05 | reward, or turn information over to the watch | `gate_guard` replaces the runner | Gate Guard shrugs |
| 06 | proceed northwest as the runner directed | parse `None`; no transition | a northwest journey with crates, sheds, lanterns, broken banners |
| 07 | are the crates opened or rummaged | adjudication, no crate | the patrol route sentence |
| 08 | study a broken banner; how was it destroyed | `custom`; no banner | `The guard says, "I do not know enough to answer that."` |
| 09 | continue following the path | parse `None`; no transition | the same guard line |

Ending state: scene `frontier_gate` only, Day 1, not in combat, one real clue, overlay claiming the player has reached the mud track and that broken banners exist.

## Earliest divergence

Turn 01. Failed social probe. `generated_candidate` stated a schedule of curfew hours and the northwest route past the crates. The route clue was not discovered. Hours are not authored. The player asked for those hours on turn 02.

That is an information divergence. It is not the journey.

## Spatial divergence

Turn 06.

Player attempt: proceed northwest, as the runner directed.

First incorrect decision: `parse_freeform_to_action` returned `None`. `proceed` is not in the travel-verb set. The follow/pursue exit matcher requires `follow` or `pursue`. Nothing set `kind` to `travel`, so `apply_stay_leave_narration_agreement_to_gm` did not run. Its false-arrival rewrite applies only when kind is `travel` or `scene_transition`.

Authoritative result: `resolved_transition` null. `visited_scene_ids` remains `frontier_gate`. `old_milestone` was not activated.

Narrated result: the player turns northwest, passes crates, walks a mud track between sheds and lanterns, sees broken patrol banners, and steps into the stretch where the soldiers were last seen.

Why they differ: unparsed input falls through to generative narration, and `_validate_gm_scene_update_for_legacy_adoption` accepts any small string list under `visible_facts_add`, `discoverable_clues_add`, `hidden_facts_add`, and `mode`. The validator's own comment says it does not make a gameplay-policy decision. This turn's approved update says the player has reached the track, adds a banner clue, adds a hidden watcher, and sets mode to `exploration`.

Later dependent turns: 07, 08, 09.

## Travel and the authored exit

`frontier_gate` already has `Follow the missing patrol rumor` → `old_milestone`. The milestone scene is the northwest mud track: a stone marker and fading prints. It does not contain crates, sheds, lanterns, or banners.

The discovered lead does not point at `old_milestone`. `related_scene_ids` is `frontier_gate` only. The connection is the exit label plus clue overlap inside `_match_follow_pursuit_exit`, and that function does not run unless the line follows or pursues.

Probes, not a replay:

- `I follow the missing patrol rumor` → `scene_transition` `old_milestone`
- `I follow the northwest mud track` → `scene_transition` `old_milestone` (`legacy_follow_exit_match`)
- `I pursue the missing patrol rumor northwest` → `scene_transition` `old_milestone`
- `I'll head toward the old milestone` and `I go to the old milestone` → `old_milestone`
- `I enter Cinderwatch` → `market_quarter`
- `I'll head northwest` → `travel`, destination `northwest`, no exit
- `I proceed northwest` and the session sentence → `None`
- `I walk a few steps closer to the crates` → `custom` local movement

So existing travel should already have handled a follow-the-rumor or follow-the-mud-track utterance. It should not have treated bare `northwest` as arrival. The session utterance failed one step earlier: it was not travel at all. Class G in the phase-4 list: parsing miss, then no exit bind, then realization and scene-update integrity. The first of those is the parser.

Recognizing `proceed` as a travel verb would put this sentence on the same path as `I'll head northwest`: unresolved travel. PR-BF would then replace success narration with the unresolved terminal. It would not, by itself, select `old_milestone`, and it would not clear a `scene_update` if the model still attached one. A verb addition without the adoption guard is not the whole repair. A new router is not required.

PR-BF classification: C. The parser never established travel ownership, and another path invented movement. It is also a sibling of PR-BF's invariant, not a regression of the guarded kind. Do not reopen PR-BF.

## Generated objects the player then used

Only in prose, then partly copied into overlay: crates being passed now, sheds, lanterns, broken patrol banners, arrival on the track.

The word "crates" inside the clue is authored. "As I pass the crates" is the turn 06 journey.

If turn 06 had fail-closed, turns 07–09 would not have had those referents. That is three later failures. Turn 02's curfew mismatch and turn 03's irrelevant runner answer and turn 05's speaker switch would remain.

## Notice board

Authored advertisement: taxes, curfew rules, a missing-patrol warning.

Inspectable payload: one clue, the northwest route. Alias `curfew notice` is why "curfew section" binds `notice_board`.

Not authored: hours, districts, penalties, reasons.

Turn 02 did not miss the owner. `referenced_surface_interactable_id` is `notice_board`. `skip_unrelated_clue_discovery` is false. The game revealed the unrelated clue (outcome b) after turn 01 had already generated a schedule (outcome c). It did not say the hours were unavailable (outcome a).

This is both missing content and an owner that presents its only payload as the answer to a different subject. Ordinary play needs the second behavior: do not masquerade. It does not need a document-reading subsystem. Do not author curfew rules to make this transcript tidy.

`What do the notices say about the curfew?` still parses as `None`. That older residue is not what this session hit.

## Tavern runner

Address was correct (`tavern_runner`, substring on the declared approach).

Authored topic: the patrol vanished near muddy footprints northwest of the crates. Not spoken.

The heard line is the board clue, wrapped as `Word is`, after a refusal and an ignorance line were both computed. `authored_answer_sufficient_for_question` returns true for dimension `general`. Concealment markers include "not something I can say here," and authored-knowledge realization replaces those with an available fact.

First incorrect decision: relevance / sufficiency, then fallback selection that prefers a known fact over the refusal. Not target selection. Not missing city content. A refusal would have been the better answer.

## Interlocutor

Before turn 05 the runner was active. The player did not say Gate Guard, serjeant, or captain. `to the watch` bound `gate_guard` because alias `watch` sits in a `to the` phrase. Vocative and declared-switch flags are false. Topic salience was ignored because the explicit target won.

Contrasts: `to the watch` binds `gate_guard`. `to the city watch` does not. A reward question with no `to the watch` binds nobody. `to the tavern runner` binds the runner.

Gate Guard is actually present. The error is the silent switch. The shrug does not invent a reward. No reward is authored.

## Unknown quantity

Turn 04 is correct / awkward. The runner cannot answer a count that nobody authored. The leading `No.` is style. An unshown model paragraph guessing half a dozen is stored with provenance `generative_reply` and was not emitted.

## `The guard says`

Turns 08 and 09. `speaker_label` returns `The guard` when `npc_id` and `npc_name` are empty. `minimal_social_emergency_fallback_line` is what the anti-reset continuation helper uses. Final source `anti_reset_local_continuation_fallback`.

Display-only false attribution. `current_interlocutor` at session end is null. No new guard id was stored. Turn 07 computed the same line and then replaced it with the patrol clue before the player saw it.

It is a downstream amplifier of turns that had no valid target. The prior playtest already showed this helper can reach the player. It is not the cause of the false journey. Do not reopen PR-BJ.

## PR-BK

| Check | Result |
| --- | --- |
| `generative_reply` became a structured fact? | No. The quantity paragraph stayed `generative_reply` and was not emitted. No `structured_fact_candidate` field in the log scan. |
| Unsupported prose given authoritative provenance? | The banner paragraph sits in `last_answer` with provenance `clue_knowledge`, and `last_answer_authoritative_text` is the real patrol sentence. Selection returns the payload when it is present (`structured_fact_text_from_topic_pressure`). Turn 07 emitted that payload, not the banners. |
| Same-turn self-promotion? | Not observed as an emitted structured fact. |
| Cross-turn promotion of generative prose? | Not observed. |
| Authoritative payloads kept valid provenance? | The heard clue on turn 07 matches `last_answer_authoritative_text`. |

PR-BK remains closed. One unshown generative paragraph, and one paraphrase slot that is not a paraphrase, are residue. They are not the invariant failing in player-facing output.

## Repair threshold

Not taken. The first decisions are established, and the owners exist, but the integrity repair touches narration agreement and scene-update adoption together. Doing it inside this audit would hide the audit under a behavior change. No new subsystem is justified.

## Product direction

State ↔ narration gameplay integrity for movement that never became an authoritative transition.

Not a new travel engine. The exit is already there. Not curfew text. Not a document reader. Not city-guide facts. Not another NPC-title cycle.

## PR-BL

Earned.

TITLE: Unparsed movement must not narrate or commit a spatial transition.

PRIMARY LANE: State ↔ narration integrity. Existing travel and scene-update owners.

GOAL: When no transition owner has succeeded, player-facing narration does not assert arrival or progress into new geography, and model `scene_update` does not add that geography to the overlay.

INVARIANT: Generative narration may decorate an authoritative gameplay result. It may not create the result. `resolved_transition` (or an equivalent transition flag) is the success signal. Travel kind is already not that signal. Absence of a resolution kind is not that signal either.

FIRST INCORRECT DECISION: `parse_freeform_to_action` returned `None` for directional `proceed`, so PR-BF never ran, and legacy scene-update adoption stored the model's arrival.

SMALLEST GENERAL REPAIR: On a turn with no successful transition, reject spatial-success narration and reject `scene_update` entries that add arrival, new discoverable clues, hidden facts, or mode. Keep unresolved-travel fail-closed. Keep local `custom` movement. Do not bind bare compass words to exits.

OUT OF SCOPE: route planning, coordinates, travel duration, a geography database, destination embeddings, a second travel router, noun-to-interactable promotion, curfew authoring, social relevance, interlocutor alias policy, compound N-action execution, a world clock.

## Closeout

A. Player turns audited: 9 human turns, plus the opening entry. 10 log entries.

B. Player-facing failures: 8. Turns 01, 02, 03, 05, 06, 07, 08, 09. Turn 04 is not a failure. Turn 00 is not a failure.

C. Independent root causes after dependency reduction: 4. Unparsed-movement integrity; board payload versus advertised subject; social fact-versus-refusal; `to the watch` interlocutor rebind.

D. Semantically acceptable: turn 00 opening; turn 04 quantity refusal (correct / awkward). Turn 05's shrug is an acceptable absence attached to the wrong speaker. The absence is not the defect.

E. Earliest meaningful divergence: turn 01. Narrated curfew-hour schedule and undiscovered northwest route. Authoritative result was a failed social probe with no discovery.

F. Yes. Turn 06 narrated a northwest journey and arrival. Scene id did not change. Overlay then stored the arrival.

G. First incorrect decision: the utterance was not classified as travel (`parse_freeform_to_action` → `None`), so no transition owner ran and the travel-kind narration guard did not apply. Generative text and `scene_update` created the journey.

H. Yes. `Follow the missing patrol rumor` → `old_milestone`. The milestone scene is the northwest mud track.

I. The utterance used `proceed` and a compass direction. `proceed` is not a travel verb. The follow/pursue matcher, which can bind "northwest mud track" to that exit, requires `follow` or `pursue`. Bare `northwest` after a recognized verb (`I'll head northwest`) is unresolved travel and does not select the exit.

J. Prose-only, relative to authored scenes: curfew-hour schedule (turn 01); crates as objects being passed; sheds; lanterns; broken patrol banners; the player's arrival on the track. The route sentence itself is authored and was discovered on turn 02.

K. Turn 02 relied on the schedule. Turn 07 relied on passing the crates. Turn 08 relied on the banners. Turn 09 relied on the path. Sheds and lanterns were not used again.

L. Three later failures, turns 07–09, disappear if turn 06 does not invent the journey. Preventing only turn 01 does not remove them. The route is authoritative after turn 02, and the runner repeats it on turn 03.

M. Yes. The board is described as listing curfews, and turn 01 adds a schedule of hours. Hours, districts, penalties, and reasons are not authored.

N. Yes. Turn 02 bound `notice_board` and returned `notice_patrol_route` instead of an absence.

O. Yes. Tavern Runner was the resolved speaker on turn 03.

P. Dimension `general` treated an available clue as a sufficient answer, and authored-knowledge realization replaced a computed ignorance line with that clue. The runner's own topic sentence was not the line spoken.

Q. Yes. `to the watch` selected `gate_guard` over the active runner. Not a vocative and not a declared switch.

R. Display-only false attribution. Empty `speaker_label`. No guard id stored. `current_interlocutor` ended null.

S. No. Generative prose was not emitted as a structured fact. Turn 07 emitted the authoritative clue payload.

T. Yes. PR-BK remains closed.

U. A different path bypassed it. Kind was null, not unresolved `travel`. PR-BF's guarded path was not shown failing. Do not reopen PR-BF.

V. The heard geographic progression — leaving the gate, the mud track, crates, sheds, lanterns, banners, and still being on that path — was narration. The scene graph did not move. One real clue was discovered. The overlay then stored arrival and banners. Diegetic date did not change.

W. Missing capability, not a defect in an owner that already succeeds: an inspect surface cannot carry several advertised subjects with one reveal and then refuse the unauthored ones. Also still deferred, and not this session's cause: compound N-action execution, a diegetic clock, richer unresolved-travel guidance.

X. Missing authored content: curfew hours, districts, penalties, and reasons; a reward or informant procedure; a soldier count; crate and banner objects. Do not add them to explain this transcript. The runner does not need a city guide for turn 03 to be fixed; a refusal was available.

Y. State ↔ narration integrity when movement is not an authoritative transition.

Z. Yes. PR-BL as specified above. Do not implement it inside this audit.

## Validation

No production repair. Diagnostic probes only, recorded in `diagnostic_probes.md`. Full suite not run.

## Deferred residue

- Board subject versus single payload, and the turn 01 social misread of an approach.
- General-question fact substitution over a grounded refusal.
- `to the <alias>` beating an active interlocutor.
- Empty `The guard` label on ownerless turns.
- Compound execution of the banner question beside the move.
- `What do the notices say...` remaining untargeted.
- Unshown generative `last_answer` text beside a correct authoritative payload.
- Lead row for `notice_patrol_route` not pointing at `old_milestone`. The exit label is the current bridge, and it already works for follow/pursue phrasing.
