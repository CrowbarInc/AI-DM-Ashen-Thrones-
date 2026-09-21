# PR-AR — Perception Narration Authority and Audible Non-Invention

Date: 2026-09-20
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-AR repaired the highest-leverage ordinary-play failure after PR-AQ: a correctly typed listen/observe turn still narrated unsupported whispers, complaints, and overheard topics.

The engine-side perception decision after PR-AQ was already correct (`kind=observe`, local movement ≠ travel, listen ≠ sound creation). The remaining defect was a State ↔ Narration authority failure at the perception boundary.

Earliest causal defect: human-adjacent focus treated a visual crowd/presence fact as `speaking_group` / authored audible content, then told the live model to prefer voices. Downstream, `classify_perception_invention` did not treat unsupported speech or audible events as authority-bearing, so the invented prose survived.

PR-AR did not add a sound system, perception owner, world-authority owner, or canonical Frontier Gate sound/speech. Authorized audible facts and authored current speech can still be realized. Empty listening remains a valid complete result.

Invariant now enforced on perception turns:

```text
PERCEPTION MAY REALIZE THE AUTHORITATIVE WORLD.
PERCEPTION MAY NOT AUTHOR THE WORLD.

THE PLAYER CHOOSING TO LISTEN
    DOES NOT CREATE
SOMETHING WORTH HEARING.
```

## 2. Starting Failure

PR-AQ extended replay T16 (`20260920T211426Z_R2-MT01-AQ`):

> Player: I walk a few steps along the muddy gate line and listen
> GM: You pace alongside the muddy line… murmurs and muted complaints… soft, anxious whispers drift—talk of the missing patrol, concerns about tightened caravan delays to the east, and murmurings of the harsh new curfew rules…

Kind was `observe`. Structured state did not mint those sounds. The player-facing world still acquired speakers, speech, beliefs, and events.

## 3. Exact T16 Reproduction

| Field | Before PR-AR (PR-AQ replay) |
| --- | --- |
| Raw input | `I walk a few steps along the muddy gate line and listen` |
| Action kind | `observe` |
| Parser lane | `human_adjacent_observe` |
| HA family | `approach_listen` |
| Target | none |
| Unsupported audible | murmurs, muted complaints, anxious whispers |
| Unsupported speakers | crowd / unnamed watchers and refugees as speakers |
| Unsupported speech content | missing patrol; eastern caravan delays; harsh new curfew rules |
| Unsupported events | rain/woodsmoke texture plus overheard intelligence |
| Structured mutation | none (leads remained `notice_patrol_route`, `milestone_mud_prints`) |
| Clue/lead mint | none |

Reproduction used the exact natural input. It was not rewritten into engine-shaped commands.

## 4. Perception-to-Narration Trace

```text
raw player input
  → PR-AQ typing: observe / human_adjacent_observe / approach_listen
  → observe owner (existing)
  → HA focus: visual crowd fact scored as speaking_group
  → ENGINE FOCUS hint: "prefer voices" / "speaking cluster"
  → visible-fact listen alignment treated crowd/location overlap as audible
  → live model invented whispers / complaints / topics
  → classify_perception_invention: unsupported=False
  → final emission treated the prose as atmospheric
  → player-facing narration kept the invented speech
  → structured-state reconciliation did not mint clues/leads
```

Authoritative perception result before narration, on the live `data/scenes/frontier_gate.json` surface:

- Visible people/cluster and notice-board facts exist.
- No authored current whisper, complaint, or overheard-topic fact exists in `visible_facts`.
- Present NPCs exist. Presence is not speech authority.
- Discoverable patrol clue exists but is not an audible event at the gate line.

## 5. Failure Classification

**CLASS I**, with earliest causal defect **CLASS A**.

| Class | Finding |
| --- | --- |
| A | HA focus promoted a visual crowd/presence fact to `speaking_group` and licensed voices. First incorrect authority decision. |
| B | The HA hint explicitly said to prefer voices and treated overheard content as the desired listen prize. Narrow prompt-contract defect, not a general rewrite. |
| C | The model invented after that license. Not the first defect. |
| D | Perception grounding covered confrontation and selected physical evidence, not unsupported speech/audible events. Downstream missed defense. |
| E | Final emission did not independently reject the speech as state-bearing. Secondary. |
| F | After repair, replacement uses existing diegetic quiet / authorized audible facts. No reinvention. |
| G | Listen alignment treated crowd/cluster/`missing patrol` topic overlap as authored audible. Same early authority leak. |
| H | Rejected. Whispers/complaints implied speakers, speech, beliefs, and actionable topics. |

## 6. First Incorrect Authority Decision

`resolve_implicit_human_adjacent_focus` scored a visual people-presence fact (refugees/guards/crowd/cluster, plus player location overlap such as `muddy` / `along`) as `speaking_group`.

`_hint_for_focus_bundle` then told the model to anchor on “a nearby speaking cluster or audible crowd detail” and to “prefer voices.”

That is the first point where unsupported perceptible detail was authorized.

## 7. Existing Perception Authority Contract

Recovered from PR-AH, PR-AO, `game/perception_grounding.py`, and `docs/state_authority_model.md`:

- Observation may reveal the authoritative world; it may not author it.
- Perception kinds already fail closed through `apply_perception_non_invention_to_gm`.
- Evidence is the current visible/interactable/NPC/discovered-clue surface.
- Hidden facts and undiscovered clues must not be spoken.
- Category detectors, not banned-word lists, decide whether a world-significant claim is authorized.
- GPT output must not mutate the five state domains.

## 8. Existing Narration Authority Contract

Recovered from PR-AJ and state-authority doctrine:

- Authority may produce narration. Paraphrase is allowed.
- Narration alone must not produce authority.
- Contextual extraction may remain a non-authoritative continuity hint.
- Player-facing text is still a world-truthfulness surface even when structured state does not mutate.

## 9. Authoritative Perception Inputs

For a listen/observe turn the narrator may realize:

- authored visible facts that are actually perceptible now;
- authored audible/speech tokens in those facts;
- present NPCs as presence, not as spontaneous dialogue;
- discovered clues only if already revealed;
- existing diegetic quiet when no authorized audible fact exists.

The narrator may not realize:

- hidden facts;
- undiscovered clues;
- player hypotheses;
- recent non-authoritative prose;
- NPC topic knowledge as ambient overheard speech;
- visual presence as current speech.

## 10. Narration Context / Prompt Audit

Exact HA hint before repair, T16 / default-or-data crowd fact:

```text
Human-adjacent intent (approach_listen): anchor narration on a nearby
speaking cluster or audible crowd detail. Primary visible cue: <crowd fact>
Prefer voices, groups, patrons, refugees, or guards already implied there...
```

The none-tier hint also said not to invent environmental clues “as a substitute for overheard content,” which treated overheard content as the expected reward.

After repair:

- `speaking_group` requires an authored speech/sound token in the fact.
- `crowd_cluster` may note presence and forbids invented speech.
- empty listen states that absence is valid.
- No general prompt rewrite was performed.

## 11. Raw Live-Model Invention

PR-AQ T16 raw player-facing invention included:

- murmurs and muted complaints;
- soft, anxious whispers;
- talk of the missing patrol;
- concerns about tightened eastern caravan delays;
- murmurings of harsh new curfew rules;
- woodsmoke.

Rain/curfew/patrol topics exist as written or environmental facts. Converting them into overheard speech was invention.

## 12. Post-Generation Grounding Audit

Before PR-AR, `classify_perception_invention` on the exact T16 narration returned:

```text
{"unsupported": false, "flags": [], "checked": true}
```

After PR-AR it returns unsupported flags for smoke (if asserted), whisper, complaint, and spoken content when those categories are absent from the authorized blob.

Authorized paraphrase such as “You hear water somewhere beyond the wall.” survives when the scene authors that audible fact.

## 13. Final-Emission Validation / Repair Audit

PR-AP refusal grammar was not reopened. Final emission did not independently catch T16 speech. Perception grounding remains the fail-closed perception seam and still runs before finalize. Replacement text is existing diegetic quiet or authorized fact realization, not a new rewriter.

## 14. Atmosphere vs World-Assertion Boundary

| Example | Classification |
| --- | --- |
| “The gate yard feels still.” | Texture, if it does not mint events |
| Existing diegetic quiet: “overlapping voices never resolve into distinct speech” | Grounded absence / limitation |
| “Boots scrape behind the wall.” | Authority-bearing audible event |
| “Two guards whisper behind the wall.” | Authority-bearing people + speech |
| “Two guards whisper that the missing patrol left before dawn.” | Stronger: speech + knowledge + event |

Style does not grant fact authority. The key distinction is non-authoritative texture versus assertions about the world.

## 15. Audible Fact Authorization

PR-AQ’s visible-fact listen alignment now requires actual audible/speech tokens (`hear`, `sound`, `drip`, `shout`, `call`, `whisper`, and the same class of tokens). Crowd, cluster, guard, and `missing patrol` no longer count as authored sound.

- Authorized: “Water can be heard behind the kiln wall.” may be narrated.
- Unauthorized: empty listen uses existing diegetic quiet.
- No canonical Frontier Gate sound was added.

## 16. Speech Authorization

Present NPC ≠ authorized overheard speech. NPC topic ≠ ambient dialogue. Authored current speech such as “A dock clerk calls the next berth number.” or “A huddled group … murmurs about …” may survive through the existing visible-fact / HA `speaking_group` path.

No ambient-conversation simulation was added.

## 17. Player-Hypothesis Non-Authority

“I listen for whispers.” / “I listen for footsteps.” do not create those events. Fixtures and the freeform probe show the hypothesis is not echoed as evidence.

## 18. Recent-Prose Non-Authority

Rejected observe/listen prose is resynced through the existing PR-AH contextual-lead rebuild. A later “I listen for those whispers.” does not promote the rejected text into authority, clues, or leads.

## 19. State Non-Mutation vs Player-Facing Truthfulness

PR-AQ T16 already left structured state clean. That was not enough. Unsupported narration is a world-authority failure for the player even without clue/lead mutation. PR-AR repairs player-facing truthfulness and keeps the non-mutation contract.

## 20. Implementation

Generic production only:

- `game/human_adjacent_focus.py` — speech/sound vs people-presence; `speaking_group` requires authored speech/sound; listen without speech sets `human_adjacent_diegetic_null`; hints no longer license invented voices.
- `game/diegetic_fallback_narration.py` — listen alignment uses audible tokens only; silent crowd/location overlap is not an audible fact.
- `game/perception_grounding.py` — generalize existing category grounding to perceptible events (speech-act categories and cross-modal events) checked against the authorized blob.

No new owner. No `data/world.json` or `data/scenes/frontier_gate.json` content added to make T16 interesting.

## 21. Empty Listening

PASS. Scene with no authorized audible fact + “I listen.” yields complete diegetic quiet, not invented sound or speech.

## 22. Authorized Listening

PASS. Water/drip or authored shout/call facts may be realized. Extra speakers/events are not added by fallback.

## 23. NPC Present but Silent

PASS. Quay clerk presence does not become `speaking_group` and does not authorize “the clerk whispers…”.

## 24. Authorized Speech

PASS. “A dock clerk calls the next berth number.” survives classify and HTTP when that fact is authored.

## 25. Repeated Empty Perception

PASS. Listen / keep listening / listen again do not escalate into whispers, new voices, or approaching figures.

## 26. Targeted Perception

PASS. “I listen at the door.” does not invent sound. Valid target ≠ authorized discovery.

## 27. Grounded Paraphrase

PASS. “You hear water somewhere beyond the wall.” survives for an authored water-sound fact.

## 28. Unsupported Semantic Expansion

PASS. “A hidden stream rushes through a tunnel beneath the wall.” is rejected by existing hidden-fact span grounding while the simple audible fact remains usable.

## 29. Cross-Modal Generalization

PASS. Unsupported blood, smoke, tracks, and moving-figure claims fail by the same category-vs-authorized-blob rule. The repair is not an auditory vocabulary filter.

## 30. Fallback Non-Reinvention

PASS. Rejected whisper/complaint text is replaced with existing quiet or authorized scene realization, not a different invented event.

## 31. State-Mutation / Lead / Clue Audit

After invented-speech attempts and after repaired T16:

- no new clue;
- no `narration_ctx_…` lead;
- no new NPC;
- no interlocutor bind;
- lead registry on the Frontier Gate chain remains the two authored discoveries.

## 32. Frontier Gate T16 Before / After

| | Before (PR-AQ `20260920T211426Z`) | After (`20260920T221938Z_R2-MT01-AR`) |
| --- | --- | --- |
| Raw | walk a few steps along the muddy gate line and listen | same |
| Kind | observe | observe |
| HA | approach_listen | approach_listen |
| Focus | speaking_group on visual crowd | crowd_cluster + diegetic null on live scene file |
| Raw invention | whispers / complaints / patrol talk | rejected |
| Final narration | invented overheard intelligence | “You catch tone and urgency, but overlapping voices never resolve into distinct speech.” |
| Leads | two authored | two authored |
| Later turn treats invention as true | n/a | T17 rereads the board; no whisper follow-up |

Evaluator `player_intent_addressed` FAILed on T16 after repair because the grounded-absence line shares few lexical tokens with `walk` / `gate` / `listen`. That is an evaluator lexical miss on a valid quiet result, not remaining invention. Existing semantic calibration labels were not weakened.

## 33. Scenario-Independent Generalization Fixtures

Synthetic kiln / quay scenes in `tests/test_perception_narration_authority_audible_non_invention.py`:

| Test | Result |
| --- | --- |
| 1 empty listen | PASS |
| 2 authorized water | PASS |
| 3 unsupported footsteps | PASS |
| 4 authorized footsteps | PASS |
| 5 unsupported whisper | PASS |
| 6 authorized speech | PASS |
| 7 NPC present, silent | PASS |
| 8 player seeks whisper | PASS |
| 9 player seeks footsteps | PASS |
| 10 unsupported bell | PASS |
| 11 authorized bell | PASS |
| 12 unsupported blood | PASS |
| 13 authorized blood | PASS |
| 14 unsupported smoke | PASS |
| 15 unsupported tracks | PASS |
| 16 unsupported moving figure | PASS |
| 17 grounded paraphrase | PASS |
| 18 paraphrase expansion | PASS |
| 19 repeated empty listen | PASS |
| 20 targeted empty listen | PASS |
| 21 recent prose leak | PASS |
| 22 no false lead | PASS |
| 23 fallback non-reinvention | PASS |
| 24 cross-modal authority | PASS |

## 34. Anti-Overfitting Audit

Changed generic files: `game/perception_grounding.py`, `game/human_adjacent_focus.py`, `game/diegetic_fallback_narration.py`.

| Check | Result |
| --- | --- |
| Calibration identifiers | None newly introduced. Pre-existing `stew` stock remains in older observe options in `diegetic_fallback_narration.py`. |
| Exact T16 string | Absent from generic engine files. |
| `if "whisper" in` / `.replace("whisper"` | Absent. |
| Category detectors | Same PR-AH pattern: category asserted in narration and absent from authorized blob. Not a strip-if-present blacklist. |
| No new Frontier Gate sound/speech | Confirmed. |
| No disabled live model on all perception turns | Confirmed. |
| No exact source-string-only grounding | Paraphrase of authorized water/call facts survives. |

`whisper`, `complaint`, `footstep`, `bell`, `blood`, `smoke`, and `tracks` appear as category/authorization tokens, matching existing `blood` / `tracks` detectors. They are not a T16 noun ban.

## 35. State ↔ Narration Scope Assessment

Invented auditory perception is a **narrow perception-authority defect** (HA focus over-authorization + incomplete perception-category coverage), not proof that PR-AR must become the project-wide State ↔ Narration campaign.

| Sibling | Classification |
| --- | --- |
| Invented time | RELATED BUT DISTINCT — usually social absence realization |
| Invented count | RELATED BUT DISTINCT |
| Invented price | RELATED BUT DISTINCT — not a perception owner |
| Invented redirect | RELATED BUT DISTINCT — social |
| Invented spoken rumor on observe | SAME SEAM if it is unsupported perceptible speech; now covered by category grounding |
| Invented spoken rumor on a bound NPC question | RELATED BUT DISTINCT — speaker-knowledge / sufficiency |

Same symptom class (narration asserts unauthorized world facts). Not the same first owner or first decision. Do not expand PR-AR to repair time/count/price.

## 36. Tests Added or Updated

Added: `tests/test_perception_narration_authority_audible_non_invention.py`.

No existing owner expectations were weakened.

## 37. Continued Multi-Turn Replay

`artifacts/prar_perception_authority/extended_replay/runs/20260920T221938Z_R2-MT01-AR/transcript.md`

Chain through learn / pursue / travel / arrive / observe / investigate / return / captain / roster / stew / glance / last-checker / T15 / T16 / T17.

T16 is typed observe and emits grounded quiet. T17 continues with a board reread. T12/T14 remain grammatical refusals. T15 remains grounded investigate.

## 38. Freeform Perception-Authority Probe

`artifacts/prar_perception_authority/freeform_probe/20260920T222131Z_probe.md`

Empty listen, listen-for-whispers, listen-for-footsteps, repeated listen, look around, listen at the door, walk+listen, listen-for-prior-sound, and post-perception actions completed without surviving whisper/complaint/footstep invention or new leads.

Residual siblings observed in the probe, not treated as PR-AR acceptance failures:

- observe-stock pair still appends the same two gate facts;
- opening `Gate Guard mutters, "Word is,"` can still appear on some observe/untyped turns (known PR-AI / opening-stock residue);
- `I watch the road.` can still parse as `kind=None`.

## 39. Validation Results

| Suite | Result |
| --- | --- |
| New PR-AR fixtures | passed (`--basetemp=artifacts/prar_pytest_tmp2`, later verify) |
| PR-AH / HA / PR-AQ | passed |
| PR-AD through PR-AP focused owners | passed (`artifacts/prar_pytest_reg1`) |
| Intent parser, local observe, diegetic fallback, narration-consistency, state-authority, clues, FEM validators/repairs, fallback-behavior, calibration corpus | passed (`artifacts/prar_pytest_reg2`) |
| Social / lead-landing / dialogue-routing | passed (`artifacts/prar_pytest_reg3`) |
| Round #1 semantic calibration | 13/13 |
| Extended R2-MT01-AR | completed; T16 grounded |
| Freeform probe | completed |
| Full authoritative suite | not re-run (same doctrine as PR-AQ) |

Windows `PermissionError` on shared pytest temp remains environmental.

## 40. Remaining Semantic / Playability Failures

- Observe fallback stock can still append the same two-fact gate pair (`As you watch the scene…`).
- T13 `already_searched` can still truncate.
- Live model can still invent a time, count, price, or redirect on social absence turns.
- Replay/opening `Gate Guard mutters` / `"Word is,"` can still appear; do not reopen PR-AI without new causal evidence.
- Untargeted look-around can still repeat gate stock.
- Some paraphrases (`posted notices`, `Gate Serjeant`, `What's nearby?`) remain as previously deferred.
- Evaluator lexical false negatives on short grounded-absence listen lines.

## 41. Deferred Findings

All previously deferred residue remains deferred unless later evidence elevates it. PR-AR does not start a project-wide State ↔ Narration campaign.

## 42. Recommended Next Product Slice

Chosen from continued ordinary play after repaired T16:

**Observe fallback stock repeatedly appending the same two-fact gate pair.**

T16 is now a coherent grounded listen. The next ordinary-play quality failure on the same perception lane is stock repetition, not missing action typing and not a general State ↔ Narration rewrite. T13 truncation and opening-mutter residue remain siblings.

Do not start pricing/economics. Do not reopen PR-AQ typing, PR-AP grammar, PR-AO provenance, PR-AH confrontation grounding, or PR-AI speaker ownership without new causal evidence.

## 43. Git / Worktree State

The worktree remains dirty.

PR-AR generic production: `game/perception_grounding.py`, `game/human_adjacent_focus.py`, `game/diegetic_fallback_narration.py`.

PR-AR tests/docs/tools: `tests/test_perception_narration_authority_audible_non_invention.py`, `tools/run_prar_freeform_probe.py`, `data/validation/prar_perception_narration_authority/`, `artifacts/prar_perception_authority/`, this report, `docs/NEXT_SESSION.md`.

Canonical scene/world content was not modified to add Frontier Gate sounds or speech.

Replay/probe reset local runtime documents (`data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`).

Pre-existing PR-AC through PR-AQ dirt remains. Do not treat the tree as a clean post-PR-AR commit.

## 44. Confidence

**High** that T16 invention was HA visual-as-speech authorization plus a perception-grounding category gap, not a missing action type.

**High** that empty listen and unauthorized speech/sound now fail closed without a noun blacklist.

**High** that authorized audible facts and authored current speech still survive.

**Medium-high** that live listen turns will stay free of whispers/complaints. Opening-mutter stock and observe-stock repetition can still occupy other observe paths.

**Medium** that every live-model sensory flourish is now classified. Category grounding is general, not complete semantic entailment.
