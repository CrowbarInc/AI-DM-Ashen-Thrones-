# PR-BI — AI Experience / Gameplay: Interruption Progression and Catalog-Residue Re-Audit

Date: 2026-09-22
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Probe artifacts: `artifacts/prbi_interruption_progression/`

---

## 1. Executive Summary

The repeated-interruption fixture was a semantic authority defect. It was not a reason to reopen PR-AI, and it was not the same bug as historical opening `Gate Guard mutters` lines.

`test_transcript_runner_repeated_interruption_beat_forces_progression` failed because model interruption prose was stored as `topic_pressure.last_answer` and then realized as NPC speech:

```text
Tavern Runner mutters, "Word is, the runner begins to respond before noise from the crowd pulls their attention away."
```

The runner was explicitly addressed and allowed to speak. The interruption sentence was not an authored answer. Realization overwrote a referential-clarity refusal with that sentence. The owned patrol fact was displaced.

The repair stays on the existing topic-progress and answer-candidate owners:

* an interruption cutoff is not written as `last_answer`;
* an interruption-shaped stored answer is not selected as a structured fact.

The owned fact remains eligible. After the repair the same fixture restates:

```text
Tavern Runner mutters, "Word is, the patrol never came back from the old milestone."
```

`"Word is,"` and `mutters` on that authorized sentence are the structured-fact speech envelope. That wording is aesthetic. Do not open a prose-tuning cycle, and do not reopen PR-AI.

---

## 2. Recovered Failing Fixture

Source: `tests/test_transcript_regression.py::test_transcript_runner_repeated_interruption_beat_forces_progression`.

Seed: `_seed_tavern_patrol_lead_old_milestone`.

| Item | Evidence |
| --- | --- |
| Scene | `tavern`. Exit label `Path to the old milestone` → `old_milestone`. No pre-seeded pending lead. |
| Present NPC | `tavern_runner` / Tavern Runner, location `tavern` |
| Owned topic | `patrol_milestone`: `The patrol never came back from the old milestone.` |
| Turn 1 input | `Tavern Runner, what happened to the patrol?` |
| Turn 2 input | `"Runner," Galinor presses, "what were you about to say about the patrol?"` |
| Turn 3 input | `"Runner," Galinor says, "ignore the noise and tell me about the patrol."` |
| Model texts | three interruption cutoffs (`starts to answer` / `opens their mouth` / `begins to respond`) |
| Addressee | explicit `Tavern Runner` / `Runner` on every turn |
| Speaker selected | `tavern_runner` |
| Intended assertion | turns 2 and 3 must not replay interruption fragments, and the line must still be socially grounded in the runner/patrol thread |

Before repair, turns 1 and 2 already replaced the model cutoff with the owned topic. Turn 3 failed:

```text
unexpected interruption replay fragment: 'begins to respond'
in 'Tavern Runner mutters, "Word is, the runner begins to respond before noise from the crowd pulls their attention away."'
```

The test is not asking for a new clue. It is asking the exchange to stop repeating the cutoff and to stay on the patrol thread.

After repair, all three turns face the owned milestone sentence. The interruption fragment is gone. `last_answer` stays the owned sentence. `forced_interruption_progression` stays false. Trace: `artifacts/prbi_interruption_progression/fixture_after.json`.

---

## 3. Representative Opening Case

Historical replay, not the current final line. PR-AH `R2-MT01-AH` turn 1:

```text
Player: I look around the gate.
GM: Gate Guard mutters, "Word is, captain Thoran commands the gate watch tonight."
request_kind: observation
```

The inner sentence is the authored `gate_guard.watch_command` fact `Captain Thoran commands the gate watch tonight.` The envelope is `format_structured_fact_social_line`.

Current reproduction (`artifacts/prbi_interruption_progression/opening_probe.json`), Frontier Gate, `gate_guard` present with that topic:

| Case | Kind | Final facing |
| --- | --- | --- |
| `I look around the gate.` with a neutral model line | `observe` | authored visible stock (threadbare figure, muddy approach). No Thoran speech. |
| Same look, model emits the Gate Guard mutters line | `observe` | same visible stock. Perception non-invention replaces the speech. |
| `Gate Guard, who commands the watch here?` | `question` | `Gate Guard mutters, "Word is, captain Thoran commands the gate watch tonight."` |
| Undirected `Who commands the watch here?` with only that NPC present | `question` | same authorized Thoran line |

Observe still runs authored-knowledge realization first (`npc_topic:gate_guard:watch_command`) because `gate` overlaps the topic text. Perception grounding then replaces the player-facing line. The historical opening sentence does not survive.

Directed and sole-NPC questions are authorized speech of the owned fact. The envelope is the same formatter. That is not an interruption defect.

---

## 4. Interruption Semantics

Authoritative interruption state is `session` scene runtime `social_exchange_interruption_tracker` (`game/interaction_context.py`), written by `apply_interruption_repeat_guard` in `game/social_exchange_emission.py`.

| Term | What the code does |
| --- | --- |
| Interruption | Narration matching `_looks_like_interruption_breakoff_text`: explicit cutoff shapes, or a cutoff verb plus a disturbance (`crowd`, `shout`, `square`, and the same family). |
| Repeated interruption | Same signature, same scene, same `npc_id`, `repeat_count >= 2` (`_INTERRUPTION_REPEAT_FORCE_THRESHOLD`). |
| Forced progression | Replace that repeated cutoff with a different strict-social line and set `forced_interruption_progression`. |
| Interruption beat | The cutoff sentence itself (`starts to answer`, `breaks off`, `begins to respond`, and the fixture's forbidden fragments). |
| Social progression | In this guard, "a different legal social line," preferring a structured fact, then compatibility gate/clerk stock, then deterministic fallback. |
| Terminal response | Retry/ownership terminals such as ignorance, or a referential-clarity sealed line. Distinct from the interruption tracker. |

What must change when repeated interruption forces progression:

```text
The emitted text must stop being that interruption signature.
The tracker records the repeat and the replacement.
No new world fact is required.
```

In the failing fixture the guard never reached count 2. Turns 1 and 2 replaced the model cutoff with the owned topic before a signature was stored. Turn 3 was the first text that still looked like a cutoff at commit time, and realization then removed it. Forced progression did not fire, before or after the repair.

The strict-social unit tests still lock a different path: two cutoff signatures inside `build_final_strict_social_response` replace the second cutoff with compatibility lines that mention a ward clerk, the main gate, Old Millstone, or a crossroads. Those lines can assert unauthored scene events. They did not execute in the transcript fixture. They stay deferred compatibility. This cycle does not rewrite them.

---

## 5. `"Word is,"` Provenance

Classification: the envelope is the structured-fact formatter. The failing proposition was ingested model prose.

`format_structured_fact_social_line` (`game/social.py`) takes a fact and, when the fact lacks `word is` / `they say` / `I heard`, prefixes `Word is,` and wraps it as `{speaker} mutters, "..."`.

That is not authored NPC dialogue, not scene text, not the interruption catalog, and not a live-model invention of the words `Word is`. The interruption catalog's own `Word is, it was messy` line was not selected.

On the failing turn the fact passed into that formatter was:

```text
The runner begins to respond before noise from the crowd pulls their attention away.
```

Source tag before repair: `authored_knowledge_realization:topic_pressure:last_answer`.

Eligibility: `select_best_social_answer_candidate` treats `last_answer` as a structured fact when any non-stopword from the question occurs in the stored text. The player said `ignore the noise`. The cutoff contains `noise`. That overlap made the cutoff look like the answer. Dimension `general` accepts any stored line of sufficient length.

The formatter may introduce a speaker label and a speech act. It may restate the fact it was given. It is not allowed to treat interruption narration as that fact.

---

## 6. First Incorrect Decision

`_commit_topic_progress` in `game/response_policy_enforcement.py` wrote the current player-facing reply into `topic_pressure.last_answer` during response-policy enforcement, before final emission and before authored-knowledge realization.

On turn 3 that reply was the model cutoff. It replaced the owned milestone sentence.

Order before repair:

1. Commit stores the cutoff as `last_answer`.
2. Referential clarity rejects `the runner` as an ambiguous reference and substitutes `Tavern Runner grimaces. "Not something I can say here."`
3. `apply_authored_knowledge_realization_to_gm` reads `topic_pressure:last_answer`, does not see the cutoff communicated by the grimace, and replaces the refusal with `format_structured_fact_social_line` of the cutoff.

The resolution hint on that turn said no new information was revealed. The player-facing line then asserted the crowd-noise cutoff as rumor speech.

This is not PR-AI's bound-speaker lookup. Turns 1 and 2 already voiced the owned topic. PR-AI's rule that ignorance must not conceal an owned fact is what turn 3 correctly does after the cutoff is no longer the stored answer.

---

## 7. Speaker Authority

| Case | Addressed | Social action | Speech authority | What was said |
| --- | --- | --- | --- | --- |
| Fixture turns | Yes, Tavern Runner | question / social_probe | Yes | Owned patrol fact. Before repair, turn 3 also voiced the cutoff. |
| Look around | No | observe | No speech in the final line | Visible scene stock. Realization attempts the watch-command topic; perception removes it. |
| `Gate Guard, who commands the watch here?` | Yes | question | Yes | Owned Thoran fact, inside the `Word is` envelope. |
| Undirected watch question, sole present NPC | No explicit name; sole NPC bind | question | Yes, existing sole-NPC question path | Same owned fact. |
| No NPC | Not re-seeded as a separate world. Look-around with the guard removed was not required once observe no longer emitted speech. | | | |

`Gate Guard`, `speaking`, and `muttering` are separate claims. On the legitimate question, Gate Guard is the topic owner and the bound or sole speaker. Speaking is the social reply. Muttering is the formatter's verb, not a scene event that someone muttered.

PR-BH: the fixture's explicit runner identity bound `tavern_runner`. It did not leak to another NPC.

PR-AR: look-around does not keep Gate Guard speech. Presence did not authorize the final observe line.

---

## 8. Compact Matrix

| Case | Result |
| --- | --- |
| First interruption (fixture turn 1) | Model cutoff rejected by the question rule. Owned topic realized. |
| Repeated interruption (fixture turns 2–3) | Same owned topic. Cutoff is not stored and not spoken. |
| No NPC / observe | Final line is visible stock, not NPC speech. |
| NPC present, not addressed, look-around | Same. Speech attempt does not survive perception. |
| Explicitly addressed NPC | Owned fact is spoken. |
| Grounded absence | Existing PR-AU absence tests still fail closed. This repair does not mint a price, time, count, identity, or redirect from a cutoff. |
| Authorized clue/topic under repetition | Milestone fact stays eligible and is restated. |

Non-invention on the repaired fixture turn 3: no new location, rumor, redirect, identity, or crowd event. The sentence is the topic the runner already owned.

---

## 9. Semantic versus Aesthetic

Semantic, repaired:

* a cutoff was stored as the answer;
* that cutoff was spoken as `Word is` rumor speech;
* a grounded refusal was replaced;
* the owned answer was displaced;
* the word `noise` in `ignore the noise` was enough overlap to select the cutoff.

Aesthetic, accepted:

* `mutters` and `Word is,` around `The patrol never came back from the old milestone.`;
* the same envelope around `Captain Thoran commands the gate watch tonight.` on a real question.

Deferred, not this repair:

* strict-social forced-progression stock that can mention a ward clerk, the main gate, or watchmen hauling someone when the repeat guard actually fires;
* `"The guard says"` absent-speaker label;
* evaluator false negatives on quiet listen / nothing-new.

---

## 10. Repair

Production change: yes. Smallest owners already in the pipeline.

1. `game/response_policy_enforcement.py` — `_commit_topic_progress` still updates pressure scores, and does not replace `last_answer` when the reply is an interruption cutoff.
2. `game/social.py` — `select_best_social_answer_candidate` and authored-knowledge usability skip interruption-shaped stored text, so a previously polluted `last_answer` cannot be realized. Clue and owned-topic answers remain eligible.

Not done: deleting `Word is`, blacklisting `mutters`, hardcoding the Gate Guard, rewriting prompts, adding rumor variants, or changing the forced-progression catalog.

Invariant:

```text
interruption/progression pressure does not create semantic authority
```

---

## 11. Validation

| Check | Result |
| --- | --- |
| Exact fixture | Pass |
| New PR-BI tests (`tests/test_interruption_progression_catalog_residue.py`, 5) | Pass |
| Opening look-around probe | Final text has no Gate Guard speech |
| Directed watch-command question | Authorized Thoran line |
| First / repeated interruption emission tests | Pass, including `test_repeated_interruption_reuse_forces_socially_grounded_progression` and `test_noise_pulls_attention_away_counts_as_same_interruption_signature` |
| Ordinary `last_answer` commit | Pass |
| PR-AI `tests/test_bound_speaker_knowledge_resolution.py` | Pass |
| PR-AU `tests/test_grounded_social_absence_live_model_non_invention.py` | Pass |
| PR-AV `tests/test_grounded_refusal_topic_hook_integrity.py` | Pass |
| PR-AR `tests/test_perception_narration_authority_audible_non_invention.py` | Pass |
| PR-BH `tests/test_addressed_npc_identity_resolution_role_title.py` | Pass |
| PR-BG follow-up continuity and question-dimension suites | Pass |
| `test_final_emission_passive_pressure_restores_recent_suspicious_figure_from_weak_atmosphere` | Still fails. Pre-recorded unrelated social-pressure red. Not this owner. |
| `test_emission_quality_anyone_else_talk_to_manifests_preserves_redirect_not_fragment` | Still expects `topic_pressure:last_answer:redirect` and receives `topic_pressure:last_answer`. Documented since PR-AO. |

---

## 12. Explicit Re-Audit Assessment

### A. Does the semantic interruption defect reproduce?

No, after the repair. It did reproduce before the repair, on fixture turn 3.

### B. Do opening `Gate Guard mutters` and repeated `"Word is,"` share one owner?

Partially. Both can pass through `format_structured_fact_social_line` when an owned fact is realized as speech. Opening observe no longer keeps that speech. The fixture failure was `last_answer` ingestion, not the observe path.

### C. What is the authoritative meaning of forced progression?

Same interruption signature, same NPC exchange, repeat count at least 2: stop emitting that cutoff and emit a different strict-social line. The tracker is the authority. A new world fact is not required. This fixture never reached that threshold.

### D. Where does `"Word is,"` come from?

`format_structured_fact_social_line`. The failing inner text was model interruption prose stored as `topic_pressure.last_answer`. The words `Word is` are the formatter, not the interruption catalog and not the model.

### E. Is the selected NPC actually authorized to speak?

In the fixture, yes: the player addressed Tavern Runner. The cutoff content was not authorized. On look-around, Gate Guard is not the final speaker. On a watch-command question, Gate Guard is authorized to speak the owned Thoran fact.

### F. What is the first incorrect decision?

`_commit_topic_progress` stored the interruption cutoff as `last_answer`. Realization then spoke it.

### G. Does current evidence justify reopening PR-AI?

No.

### H. Was production code changed?

Yes.

### I. If changed, what general invariant was repaired?

Interruption pressure does not become answer authority. A cutoff is not stored or selected as the topic's answer. An already authorized fact stays eligible.

### J. Is interruption/progression ownership sufficiently converged afterward?

YES — the reproduced authority defect is repaired. Remaining `Word is` / `mutters` wording on an authorized fact is aesthetic. Invented ward-clerk / main-gate progression stock remains deferred compatibility of the strict-social repeat guard and did not cause this fixture.

---

## 13. Recommended Next Action

Do not open a `"Word is,"` or `mutters` prose cycle. Do not reopen PR-AI. Do not rewrite the forced-progression catalog unless new evidence shows that guard firing without an authorized answer and asserting an unauthored scene event.

If the next slice stays in AI Experience, pick a different sibling:

* evaluator lexical false negatives on quiet listen and nothing-new;
* `"The guard says"` generic absent-speaker label.

---

## 14. Git / Worktree State

The worktree was dirty before PR-BI and remains dirty. PR-AS through PR-BH were already uncommitted. This cycle does not commit or push.

PR-BI production:

* `game/response_policy_enforcement.py`
* `game/social.py`

PR-BI tests / artifacts / report / handoff:

* `tests/test_interruption_progression_catalog_residue.py`
* `artifacts/prbi_interruption_progression/`
* `development/tmp/prbi_interruption_probe.py`
* `development/tmp/prbi_opening_probe.py`
* this report
* `docs/NEXT_SESSION.md`
