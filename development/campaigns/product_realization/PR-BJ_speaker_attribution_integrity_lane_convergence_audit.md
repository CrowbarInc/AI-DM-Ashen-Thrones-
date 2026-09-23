# PR-BJ — AI Experience: Speaker Attribution Integrity and Lane Convergence Audit

Date: 2026-09-22
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Probe artifacts: `artifacts/prbj_speaker_attribution/probe/`

---

## 1. Executive Summary

`"The guard says"` does not reproduce as a player-facing semantic defect.

The historical line is real. PR-AH extended-replay turn 11, at `old_milestone` with no NPC present, answered an investigate turn as:

```text
The guard says, "I do not know enough to answer that."
```

On the current engine that same player line resolves as `investigate` with no speaker and realizes visible milestone stock. When the stubbed model itself emits the guard line, perception grounding replaces it with the same stock.

The string still exists as a compatibility default inside `speaker_label` when a resolution carries neither `npc_name` nor `npc_id`. Live chat on the recovered turn and on the identity matrix does not let that default reach the player. Authorized speakers keep their authored display names. Turns with no authorized speaker use the existing neutral bridge or scene stock.

No production code was changed.

The PR-AS through PR-BJ sibling-defect sequence is closed. Product Realization should return to playtesting or to a gameplay capability, and should not open another ordinary-play authority micro-cycle from leftover wording.

---

## 2. Recovered Case

### Historical occurrence

Artifact: `artifacts/prah_grounded_observation/extended_replay/runs/20260920T020729Z_R2-MT01-AH/transcript.md`, Turn 11.

| Field | Value |
| --- | --- |
| Player input | `I look for signs of the patrol.` |
| Scene | `old_milestone` |
| Present NPCs | None. `gate_guard`, `gate_serjeant`, and `tavern_runner` were located at `frontier_gate`. |
| Explicit addressee | None |
| Resolved NPC ID | None (`interlocutor` unset; interaction kind `investigate`) |
| Authorized speaker | None |
| Role / name / alias | No in-scene NPC row |
| Social action | None. `resolution.kind` = `investigate` |
| Pre-realization speaker | Not recorded. `final_emission` was `{}` |
| Final speaker label | `The guard` |
| Final narration | `The guard says, "I do not know enough to answer that."` |

A second historical hit is the same probe family's freeform turn 2, `What's nearby from here?` at `frontier_gate`, kind `question`, interlocutor unset, same sentence. That file is `artifacts/prah_grounded_observation/freeform_probe/20260920T020909Z_probe.md`.

PR-AI already classified the helper as a distinct owner from topic selection and deferred broader cleanup. Later handoffs kept the phrase as residue. This cycle re-ran the turn instead of trusting that summary.

### Current reproduction

Probe: `artifacts/prbj_speaker_attribution/probe/20260922T235900Z_probe.json`.

| Model | Kind | `npc_id` | Final narration |
| --- | --- | --- | --- |
| `You study the ground and find no fresh sign worth naming.` | `investigate` | none | `Nothing here matches that. What you can actually see is a weathered stone milestone leans beside the northwest mud track.` |
| `The guard says, "I do not know enough to answer that."` | `investigate` | none | The same milestone stock. Tags include `referenced_surface_realization`. |

No social speaker was authoritative at the moment of realization. The final text does not attribute speech.

---

## 3. End-to-End Speaker Trace

### Recovered investigate turn, current engine

```text
"I look for signs of the patrol."
    -> no explicit addressee
    -> resolution.kind = investigate
    -> social.npc_id / npc_name absent
    -> no authorized speaker
    -> referenced-surface / perception realization
    -> visible milestone sentence
```

Specificity does not change, because no speaker identity was in state. A model sentence that invents a guard is replaced before the player sees it.

### Authorized explicit speaker

```text
I turn to the Gate Serjeant. "Did the census choke change the route?"
    -> explicit_target
    -> npc_id = gate_serjeant
    -> npc_name = Gate Serjeant
    -> authored topic route_change
    -> format_structured_fact_social_line
    -> Gate Serjeant mutters, "Word is, the patrol route changed after the Ash Compact census choke worsened."
```

The display name at the end is the authored name already on the social resolution. The same holds for `Guard Captain`, sole `Gate Guard`, and `Ward Sentry`.

### Empty-identity helper, not reached by those chats

```text
resolution.social without npc_name and npc_id
    -> speaker_label()
    -> "The guard"
    -> catalog line: The guard says, "I do not know enough to answer that."
```

That chain is what the historical sentence matches. Current live owners in front of it are perception grounding for investigate/observe, and `reply_speaker_grounding_neutral_bridge` for social turns whose speaker was denied.

---

## 4. Speaker-Display Owner

Two functions choose the label. Both live in `game/social_exchange_policy.py`.

`speaker_label(resolution)`:

1. `social.npc_name` when present;
2. otherwise title-cased `social.npc_id`;
3. otherwise the literal `The guard`.

`npc_display_name_for_emission(world, scene_id, npc_id)`:

1. world NPC `name`;
2. scene/default NPC `name`;
3. title-cased id;
4. `The guard` when the id is empty.

`format_structured_fact_social_line` in `game/social.py` uses the same name-then-id-then-`The guard` order and wraps an authorized fact in the `mutters` / `Word is` envelope.

The catalogs in `game/social_exchange_fallback_catalog.py` interpolate that label. They do not look up role, alias, or roster on their own. Callers include the emergency line, the ownership terminal, and `deterministic_social_fallback_line`.

Intended contract of the label helper: identity presentation for a resolution that already has a speaker. The `The guard` branch is compatibility prose for a missing identity, not a role lookup and not a second NPC router.

When grounding denies a speaker, `apply_social_reply_speaker_grounding` clears `npc_id` and `npc_name` and sets `reply_speaker_grounding_neutral_bridge`. `build_final_strict_social_response` then prefers an authored-knowledge sentence and otherwise emits `neutral_reply_speaker_grounding_bridge_line` (`The murmur around you never tightens into a single clear voice on that point.` and its siblings). That bridge is the live no-speaker display. `tests/test_social_speaker_grounding.py::test_build_final_strict_social_emits_neutral_bridge_when_grounding_denied` locks the source.

---

## 5. Identity / Display Matrix

| Case | Authoritative speaker | Player-facing result |
| --- | --- | --- |
| Specific authored title: Gate Serjeant, explicit ask | `gate_serjeant` / `Gate Serjeant` | `Gate Serjeant mutters` plus the route-change fact |
| Specific authored title: Guard Captain, model said `The guard says` | `guard_captain` / `Guard Captain` | `Guard Captain mutters` plus the watch-command fact |
| Role-titled NPC: sole Gate Guard, undirected watch question | `gate_guard` / `Gate Guard`, role `guard` | `Gate Guard mutters`. The role field is not substituted as `the guard` |
| Explicit addressee among several NPCs | The addressed id | That NPC's authored name |
| Undirected sole NPC | That NPC | Authored name on the watch-command ask. On the runner ask, quoted ignorance remains and the beat prefix is dropped (see below) |
| Several NPCs, undirected `Who commands the watch here?` | None (`target_resolved` false) | Unattributed `Word is, captain Thoran commands the gate watch tonight.` Authored-knowledge preference over the neutral bridge. No `The guard says` |
| Several NPCs, `What's nearby from here?` | None | Neutral bridge. Guards are present and do not speak |
| No NPC at `old_milestone`, watch question | None | Milestone observation stock |
| No NPC at `old_milestone`, look for patrol signs | None | Milestone stock, including when the model speaks as a guard |
| Look around the gate with NPCs present | None | Visible gate stock, including the scenery clause `guards hold the choke` |
| Display name differs from id: `secret_warden` named `Ward Sentry` | `secret_warden` | `Ward Sentry mutters`. The id is not shown |
| Empty resolution passed straight to `speaker_label` | None | `The guard says, "I do not know enough to answer that."` This is the helper, not a chat result |

`"Guard, who commands the watch here?"` with both Guard Captain (`address_roles` include `guard`) and Gate Guard (`aliases` include `guard`) binds `guard_captain` and renders `Guard Captain`. The two identities stay distinct. That bind is existing PR-BH role resolution. This cycle did not retune it.

### Sole-runner quote split

Player: `Where did the patrol go?` Sole NPC `tavern_runner`. Model: `The guard says, "I do not know enough to answer that."`

Resolution keeps `npc_id=tavern_runner` and `npc_name=Tavern Runner`. Final text:

```text
"I do not know that part for certain." "You're asking for a line I don't own."
```

Those sentences are catalog ignorance lines whose speaker beat sits in a separate sentence (`glances away.` / `glances toward the street.`). Strict-social ownership keeps quoted speech and can drop the beat sentence. The false guard label is gone. The authored name is also absent from the final line. With one NPC present, the player is not left choosing among speakers. This is dialogue-tag splitting, not a collapse onto `the guard`.

---

## 6. First Incorrect Decision

On the historical turn, the incorrect decision was emitting a speaker label when the resolution had no speaker. `speaker_label` filled that hole with `The guard`, and the ownership/emergency catalog spoke in that voice. No NPC at `old_milestone` had authorized speech. The label was not a lost `gate_guard` id. The world rows for the guards were off-scene.

On the current recovered turn there is no incorrect player-facing decision. Investigate realization uses visible stock. The helper default remains behind that owner and behind the neutral bridge.

The helper does not read `role`. A role-only guard is rendered from `name` (`Gate Guard`) or from the id. `The guard` means "no name and no id," which is a hardcoded absent-identity default rather than grounded role text.

---

## 7. Semantic versus Aesthetic

| Question | Classification |
| --- | --- |
| Genuine current player-facing attribution defect? | No. The recovered turn and the matrix do not emit the line. |
| Rendering fallback that drops an already chosen NPC? | No on the recovered turn: no speaker had been chosen. Authorized chat rows keep `Gate Serjeant`, `Guard Captain`, `Gate Guard`, and `Ward Sentry`. |
| Legitimate generic role rendering? | The live role-titled line is `Gate Guard` / `Guard Captain`, taken from authored `name`. The helper's `The guard` is not that role field. |
| Output when no speaker is authoritative? | Yes for the helper. Live chat uses the neutral bridge or scene stock instead. |
| Aesthetic wording that should stay? | `mutters` and `Word is` on an already authorized fact stay aesthetic, as PR-BI settled. Scenery `guards hold the choke` is scene stock. The sole-runner dropped beat prefix is tag splitting. |
| Speech with no speech authority? | The historical line did that. Current investigate and no-speaker chat rows do not. |

This is not PR-BH. PR-BH decides which NPC an explicit phrase binds. Those binds still hold, and rendering does not fold `gate_serjeant` and `guard_captain` back into one `the guard`.

This is not PR-AR's owner. PR-AR's boundary is the one that now removes a model guard sentence from an investigate/observe turn. Presence of off-scene or on-scene guards does not by itself create the quote.

It is a final-label default that the live grounding and perception owners already supersede on the probed paths.

---

## 8. Production Changes

None.

A repair would be warranted if a player-facing path still attributed speech to `The guard` while state held a more specific display name, or while state held no speaker at all. The chat probe did not show that. Changing the helper's default would touch every empty-resolution emergency line in order to alter a string the probed turns no longer show. That fails the repair threshold.

The latent default stays as compatibility residue behind the grounding gate. Do not replace it with generated names, a role synonym table, or an LLM speaker guess.

---

## 9. Generalization and Non-Invention

The matrix covers the guard sentence, a distinct title (`Gate Serjeant`, `Guard Captain`), a role-titled speaker (`Gate Guard`), a non-guard speaker (`Tavern Runner`), an internal id with a separate display name (`secret_warden` / `Ward Sentry`), several NPCs, and a scene with no authorized speaker.

No chat row leaked `secret_warden`. The helper will title-case an id when `name` is missing (`Secret Warden`). Current content puts the player-facing label in `name`. This cycle does not add a knowledge-of-name store.

No chat row invented a guard speaker from mere presence. The nearby question, with four NPCs present including guards, used the neutral bridge. The milestone watch question, with guards off-scene, used observation stock.

---

## 10. Regressions

Preservation suites run this cycle:

| Suite | Result |
| --- | --- |
| `tests/test_addressed_npc_identity_resolution_role_title.py` | Pass |
| `tests/test_perception_narration_authority_audible_non_invention.py` | Pass |
| `tests/test_grounded_social_absence_live_model_non_invention.py` | Pass |
| `tests/test_interruption_progression_catalog_residue.py` | Pass |
| `tests/test_transcript_regression.py::test_transcript_runner_repeated_interruption_beat_forces_progression` | Pass |
| `tests/test_social_speaker_grounding.py` | 75 passed in the combined run; 2 failed |

Combined pytest: 75 passed, 2 failed.

The two failures are `test_transcript_runner_asks_about_aldric_followup_stays_runner` and `test_transcript_where_is_aldric_repeated_followups_stay_runner`. Both assert `resolution["success"] is True` and receive `None`. The failure payload's hint still says the player spoke with Tavern Runner. They fail before the speaker-grounding assertion. This cycle did not edit production code. They are not absorbed.

Previously recorded reds stay recorded: the PR-AO redirect-source expectation, the passive-pressure suspicious-figure fixture, BY3/BY4/BZ mutation-attribution generators, and the frontier-gate long-session golden replay.

---

## 11. Explicit Assessment

### A. Does `"The guard says"` reproduce as a semantic defect?

No.

### B. What owns final speaker display?

`speaker_label` and `npc_display_name_for_emission` in `game/social_exchange_policy.py`, consumed by the strict-social fallback catalog and by `format_structured_fact_social_line`. When grounding denies a speaker, `build_final_strict_social_response` emits `neutral_reply_speaker_grounding_bridge_line` unless authored knowledge supplies a fact. Investigate and observe turns use perception / referenced-surface realization.

### C. Was a specific authoritative speaker already available?

Depends on case. On the recovered `old_milestone` investigate turn, no. On explicit and sole-NPC social turns, yes, and the authored name was the label except for the sole-runner beat split.

### D. What was the first incorrect decision?

Historically, `speaker_label` invented `The guard` because the resolution had no speaker id or name, and the catalog then attributed a quote. The current recovered turn does not make that player-facing decision.

### E. Was production code changed?

No.

### F. If changed, what general speaker-attribution invariant was repaired?

Not applicable. No production change. The live invariant already in force is: an authorized speaker is shown by authored `name` (or title-cased id), and a turn with no authorized speaker does not gain a guard quote from presence alone.

### G. Which generic labels remain legitimate?

Authored role-titles such as `Gate Guard` and `Guard Captain`. Neutral no-speaker bridges. Scene stock that mentions guards as scenery. The helper's `The guard` remains only as an empty-identity compatibility default and did not appear in the chat probe.

### H. Is speaker attribution sufficiently converged?

YES.

### I. What evidence-backed semantic integrity defects remain across the AI Experience lane?

None that clear the threshold for another sibling cycle. See the lane audit below.

### J. Lane decision?

EXIT.

---

## 12. Lane Convergence Audit

### Category 1 — Semantic integrity defects

No evidence-backed ordinary-play semantic integrity defect remains that is large enough to open another sibling cycle.

Checked and left settled: the recovered guard sentence, authorized-name preservation, no-speaker chat, PR-BH binds, PR-AR presence versus speech, PR-AU grounded absence, and PR-BI interruption authority.

### Category 2 — Missing gameplay capabilities

Already supported by prior evidence and still feature work:

* intentional wait / in-place time passage;
* richer object history (last reader, last toucher, provenance);
* comprehensive compound / N-action execution;
* richer travel (routes, durations, unknown-destination guidance);
* rest / camp / downtime;
* a diegetic world clock.

### Category 3 — Accepted language and paraphrase residue

* actorless passive observation questions and `Describe my surroundings.`;
* leading-modifier interactable references such as `posted notices`;
* undirected who-last-read inspect questions;
* richer follow-up discourse and predicate synonyms (`Why did that happen?`, `Who did it?`, `shut down` versus `closed`).

### Category 4 — Aesthetic and prose residue

* authorized `Word is` / `mutters` envelopes;
* generic dialogue rhythm;
* the sole-runner case where a beat sentence is dropped and the quote remains;
* the empty-identity helper string `The guard`, which the probed player-facing paths no longer show.

### Category 5 — Validation and tooling residue

* evaluator lexical false negatives on quiet listen and nothing-new lines;
* `test_emission_quality_anyone_else_talk_to_manifests_preserves_redirect_not_fragment` still expects `topic_pressure:last_answer:redirect`;
* `test_final_emission_passive_pressure_restores_recent_suspicious_figure_from_weak_atmosphere`;
* the two `success is True` assertions in `test_social_speaker_grounding.py` noted above;
* BY3/BY4/BZ mutation-attribution generators and the frontier-gate long-session golden replay.

Do not change game behavior to satisfy those evaluators.

### Lane exit question

Is there currently enough evidence of unresolved ordinary-play semantic integrity defects to justify continuing the PR-AS through PR-BJ defect-hunting sequence?

No.

---

## 13. Recommended Next Product Realization Action

This sibling-defect sequence is closed. Do not open PR-BK to clean evaluator wording, dialogue tags, or the latent `The guard` helper.

Return to Product Realization playtesting of the ordinary gate-and-road loop, or to a gameplay capability chosen from Category 2. Those are feature and content slices. They are not another paraphrase or authority micro-cycle.

---

## 14. Git / Worktree State

The worktree was dirty before PR-BJ and remains dirty. PR-AS through PR-BI production, tests, artifacts, reports, and the prior handoff were already uncommitted. This cycle does not commit or push.

PR-BJ adds:

* `artifacts/prbj_speaker_attribution/probe/20260922T235900Z_probe.json`
* `artifacts/prbj_speaker_attribution/probe/20260922T235900Z_probe.md`
* `development/tmp/prbj_speaker_attribution_probe.py` (disposable)
* this report
* `docs/NEXT_SESSION.md`
