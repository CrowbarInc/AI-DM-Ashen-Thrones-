# PR-AP — AI Experience / Gameplay: Grounded Refusal Realization and Grammar

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/prap_grounded_refusal/`

---

## 1. Executive Summary

PR-AP repaired the highest-leverage ordinary-play failure after PR-AO: a correct grounded-absence decision was realized as the broken sentence `"I cannot answer that from what."`

The recovered contract is:

```text
STRUCTURED REFUSAL STATE
    +
AVAILABLE AUTHORIZED CONTEXT
    → COMPLETE PLAYER-FACING SENTENCE

A CORRECT GROUNDED REFUSAL MUST REMAIN SEMANTICALLY CORRECT
WHEN REALIZED AS PLAYER-FACING LANGUAGE.

ABSENCE OF AN AUTHORITATIVE ANSWER
MUST NOT PRODUCE ABSENCE OF GRAMMAR.
```

The catalog already had a complete line:

```text
Tavern Runner says, "No. I cannot answer that from what I know."
```

A downstream fabricated-authority strip treated the knowledge-limit hedge `"from what I know"` as a forbidden `"I know"` claim and deleted `"I know"`, leaving `"from what."`

No stew price, last-reader fact, patrol timing, or patrol personnel was added. PR-AI authorization, PR-AL relevance, PR-AN sufficiency, and PR-AO investigation authority were left intact.

---

## 2. Starting Failure

PR-AO extended replay T12 and T14:

> Player: I step over to the tavern runner and ask what the stew costs.
> GM: Tavern Runner says, "No. I cannot answer that from what."
> Evaluator: `malformed_output:broken_refusal_fragment`

> Player: I step back to the tavern runner and ask who last checked that board.
> GM: Tavern Runner says, "No. I cannot answer that from what."
> Evaluator: `malformed_output:broken_refusal_fragment`

The semantic decisions were already correct: no stew price exists; no last-reader fact exists. The failure was realization, not authority.

---

## 3. Exact Failure Reproduction

Reproduced before production changes with `artifacts/prap_grounded_refusal/repro_before.py`.

| Item | Result |
| --- | --- |
| Catalog owner | `strict_social_ownership_terminal_fallback` |
| Seed | `ownership_terminal\|tavern_runner\|Tavern Runner` |
| Deterministic index | `2` of `3` |
| Catalog text | `Tavern Runner says, "No. I cannot answer that from what I know."` |
| Literal malformed catalog? | **no** |
| Fabricated-authority match | `\bi know\b` |
| After `_remove_fabricated_authority` | `Tavern Runner says, "No. I cannot answer that from what."` |
| Evaluator | `malformed_output:broken_refusal_fragment` |

The same composition was observed on the stew-cost path and T14.

---

## 4. End-to-End Refusal Trace

| Stage | Result |
| --- | --- |
| Player input | stew-cost / last-checker questions |
| Bound speaker | `tavern_runner` |
| Dimension | `quantity` / `identity` |
| Subject | stew-cost tokens / board-check tokens |
| Candidate answers | runner `patrol_rumor` rejected; no price; no last-reader |
| Authorization | speaker bound and eligible to speak |
| Relevance | PR-AL: no relevant owned answer |
| Sufficiency | PR-AN: related board/patrol facts do not answer last-checker |
| Structured no-answer | no `topic_revealed`; social ownership terminal fallback |
| Selected catalog | `strict_social_ownership_terminal_fallback` index 2 |
| Template variables | speaker label only; no interpolated source |
| Present values | speaker = `Tavern Runner` |
| Absent/empty values | no world source slot |
| Intermediate before strip | complete `"from what I know"` line |
| Intermediate after interpolation | same complete line |
| Suffix/prefix added | none at catalog time |
| Function creating `"from what."` | `_strip_patterns_from_text` via `_remove_fabricated_authority` |
| Final emitted text (before) | `"No. I cannot answer that from what."` |
| Evaluator reason | `malformed_output:broken_refusal_fragment` |

---

## 5. Root-Cause Classification

**CLASS F — downstream text transformation breaks valid text**, with a **CLASS B-like** secondary effect: the stripped span left its grammar behind.

Not Class A: the catalog line is grammatical.
Not Class D: the selected variant’s required inputs exist (speaker label).
Not Class E: the structured refusal is complete enough for this catalog family.
Not Class C in the “two valid fragments joined badly” sense: one complete sentence was damaged later.

---

## 6. First Incorrect Realization Decision

```text
_contains_fabricated_authority
    + pattern \bi know\b
    → treats "from what I know" as fabricated authority
    → _remove_fabricated_authority / _strip_patterns_from_text
      deletes "I know"
    → "from what."
```

The earliest incorrect decision is the fabricated-authority classifier matching a speaker-knowledge-limit hedge. The strip helper then failed the optional-material grammar contract by leaving `"from"`.

---

## 7. Existing Refusal-State Inventory

Existing architecture already distinguishes several no-answer states. They were recovered, not invented:

| Internal / catalog state | Player-facing role |
| --- | --- |
| Flat ignorance | `"I don't know."` |
| Insufficient knowledge | `"I do not know enough to answer that."` |
| Situational / unauthorized speech | `"Not something I can say here."` |
| Speaker-knowledge-limit / grounded absence | `"I cannot answer that from what I know."` |
| Rumor-insufficient | `"I've heard talk, but not enough to answer that."` |
| Pressure / already said | `"I've told you what I know."` / `"I will not say more."` |
| Integrity refusal | `"I won't answer that about {topic}—not here."` |

These are not all semantically equivalent. PR-AP does not flatten them to one stock line.

---

## 8. Existing Refusal-Catalog Inventory

Canonical owner: `game/social_exchange_fallback_catalog.py`.

Families used on this path:

- `strict_social_ownership_terminal_fallback`
- `lawful_strict_social_dialogue_emergency_fallback_line`
- `minimal_social_emergency_fallback_line`
- `deterministic_social_fallback_line` (ignorance / pressure / interruption)
- integrity-topic variants when `reply_kind` / probe outcome select them

Selection helpers: `_deterministic_index`, `speaker_label`, social-ownership filter, then final-emission fallback-behavior repair.

---

## 9. Existing Template / Composition Contract

The ownership-terminal family interpolates only speaker label. `"from what I know"` is a fixed hedge, not an optional world-source slot.

Final-emission strip is subtractive:

```text
pattern.sub("")
    → leftover connector may remain
    → _normalize_terminal_punctuation
```

That strip is the composition seam that created `"from what."`

---

## 10. Semantic Distinctions Preserved

Preserved as player-facing:

- speaker lacks information
- speaker does not know enough
- speaker will not say it here
- speaker cannot answer from what they know

Not newly exposed as implementation language:

- “no authored answer”
- “dimension unsupported”
- “no eligible topic candidate”

Authorization-based no-answer already has `"Not something I can say here."` and is not collapsed into ignorance.

---

## 11. Recovered Realization Contract

```text
STRUCTURED REFUSAL STATE
    +
AVAILABLE AUTHORIZED CONTEXT
    → COMPLETE PLAYER-FACING SENTENCE
```

Rules applied:

1. Preserve the refusal reason where the catalog already distinguishes it.
2. Do not imply knowledge the speaker/world lacks.
3. Do not invent a source to finish a sentence.
4. Do not expose an empty template slot.
5. Do not leave a dangling preposition.
6. Do not leave an incomplete subordinate clause.
7. Do not duplicate neighboring clauses.
8. Do not invent content merely to become grammatical.
9. If optional material is absent or stripped, drop its connector.
10. Remain compatible with existing narration contracts.

Shorter complete refusal is preferred to fabricated complement.

---

## 12. Implementation

Generic production only:

1. `game/final_emission_validators.py`  
   Narrow `_FALLBACK_FABRICATED_AUTHORITY_PATTERNS` so `\bi know\b` does not match knowledge-limit hedges (`what I know`, `all I know`, `far as I know`, `little I know`). Knowledge claims such as `"I know the culprit was X"` still match.

2. `game/final_emission_repairs.py`  
   After a subtractive strip, `_drop_dangling_optional_connectors` removes leftover `from/of/to/...` tails, including incomplete `"from what"`.

No catalog rewrite. No new refusal engine. No LLM rewrite. No exact-string replacement of `"I cannot answer that from what."`

Canonical content: unchanged.

---

## 13. Optional-Material Grammar Handling

If a strip removes a complement, its connector is removed with it.

| Optional material | Result |
| --- | --- |
| present (`from what I know`) | complete hedge preserved |
| absent (`I cannot answer that.`) | remains complete; no `from` invented |
| filtered / leftover (`from what.`) | connector dropped → `I cannot answer that.` |
| empty (`from .`) | connector dropped |

---

## 14. Semantic-Absence Preservation

No source was invented (`from the notices`, `from the patrol reports`).
No stew price, last-reader, or patrol timing/personnel was added.
Rejected PR-AL/PR-AN facts were not restored to make grammar easier.

---

## 15. Person / Identity Absence

Cedar-wharf fixture: pier bell was recaulked; no named repairer.

PASS: grammatical refusal; no invented person.

Frontier Gate T14: last-checker remains grounded absence; complete `"from what I know"`.

---

## 16. Time Absence

Cedar-wharf: grain skiff departed; no departure time.

PASS: grammatical refusal; no invented time.

Live-model sibling: freeform probe T2 invented “before dawn.” Engine topic was empty. Recorded, not expanded.

---

## 17. Location Absence

Cedar-wharf: skiff departed; no destination.

PASS: grammatical refusal; no invented location.

---

## 18. Cause / Reason Absence

Cedar-wharf: pier gate is barred; no authored reason.

PASS: grammatical refusal; no invented cause.

---

## 19. Quantity Absence

Cedar-wharf: coils exist; no authoritative count.

PASS: grammatical refusal; no invented quantity. PR-AN still rejects the existence fact as insufficient for “how many.”

---

## 20. Value / Price Absence

Cedar-wharf broth-cost and Frontier Gate stew-cost.

PASS: grammatical refusal; no invented price; no economy added. Live `data/world.json` still has no stew-price topic.

---

## 21. Content Absence

Cedar-wharf sealed crate; no authored contents.

PASS: grammatical refusal; no invented contents.

---

## 22. Authorization-Based Refusal

Existing catalog already has `"Not something I can say here."` and pressure refusals.

Coil-warden asked about lamp-clerk hidden buyer: answer does not leak. Wording may be ignorance or situational refusal; PR-AP does not invent a new disclosure policy.

Freeform probe T1 used the situational line for an unsupported identity ask. Grammatical. No leak.

---

## 23. Relevance / Sufficiency Refusal

PR-AL: unrelated owned topic still rejected.
PR-AN: subject-relevant but dimension-insufficient fact still rejected.
Refusal grammar is repaired without restoring those rejected facts.

---

## 24. Source-Aware Refusal, If Applicable

Source-aware wording already exists (`All I know on {topic}…`, `not from what I know`). It is speaker-knowledge-limit language, not an invented world source.

Valid hedge present → preserved.
Hedge stripped or absent → shorter complete sentence.
No dangling `"from"` / `"according to"` / `"based on"`.

---

## 25. Clause / Fragment Integrity Audit

Audited on the refusal realization / strip path:

| Class | Result |
| --- | --- |
| dangling prepositions | repaired by hedge exclusion + connector drop |
| incomplete `"from what..."` | no longer emitted on catalog path |
| doubled spaces from missing slots | collapsed by existing normalize |
| sentence fragments from strip | word-count gate plus connector drop |
| duplicate refusal clauses | repeated-refusal HTTP test: one clause each turn |
| punctuation-only suffixes | not observed |
| quote boundaries | even quote counts on catalog lines |

Not a universal grammar checker.

---

## 26. Internal-Language Audit

Repaired refusals inspected. No `authored answer`, `not in state`, `dimension is unsupported`, `eligible topic candidate`, or `clue_knowledge` in player-facing text.

---

## 27. Live-Model Non-Invention Observation

Deterministic/structured output: correct refusal → grammatical refusal.

Live-model sibling (not expanded):

- Freeform T2 invented a dawn departure after engine absence.
- Replay T13 invented “search parties are still in the process of forming.”
- Replay T9 Guard Captain first-ask fell to `"I don't know."` despite PR-AI’s authored watch-command fact. Sibling; PR-AI tests remain green. Not reopened inside PR-AP.

PR-AP’s strip repair did not make these worse. The catalog hedge now survives instead of becoming a fragment.

---

## 28. Frontier Gate Before / After

| Turn | Before | After (`20260920T203314Z_R2-MT01-AP`) |
| --- | --- | --- |
| T12 stew-cost | `"No. I cannot answer that from what."` FAIL | `"No. I cannot answer that from what I know."` PASS |
| T13 glance | world-action override | still `already_searched`; live model added search-party stock |
| T14 last-checker | `"from what."` FAIL | `"from what I know."` PASS |
| T15 thank + look toward | PR-AO grounded inspect | still grounded inspect; no minted timing/personnel lead |
| T16 walk/listen | `kind=None`, truncated | still `kind=None`, truncated ellipsis |

Stew-cost semantic reason: grounded absence / no price topic.
T14 semantic reason: Class C insufficiency / no last-reader.
Selected path: ownership terminal fallback index 2.
Optional inputs: speaker only.
Rejected answers did not leak.
No fact invented by the refusal realization itself.

`"I cannot answer that from what."` does not appear in the repaired replay.

---

## 29. Scenario-Independent Generalization Fixtures

Hard gate. Vocabulary is cedar-wharf / coil-warden / lamp-clerk / broth / pier bell. File: `tests/test_grounded_refusal_realization_grammar.py`.

| Test | Result |
| --- | --- |
| 1. Person absence | PASS |
| 2. Time absence | PASS |
| 3. Location absence | PASS |
| 4. Cause absence | PASS |
| 5. Quantity absence | PASS |
| 6. Value absence | PASS; no economy |
| 7. Insufficient related fact | PASS; PR-AN reject |
| 8. Unrelated owned topic | PASS; PR-AL reject |
| 9. Unauthorized exact answer | PASS; no leak |
| 10. Optional context present | PASS |
| 11. Optional context absent | PASS |
| 12. Optional context filtered | PASS |
| 13. Empty value | PASS |
| 14. Repeated refusal | PASS |
| 15. Refusal then answerable | PASS |
| 16. Answerable then refusal | PASS |
| 17. No internal terminology | PASS |
| 18. No semantic filler | PASS |

HTTP tests exercise `/api/chat` with stubbed GPT.

---

## 30. Anti-Overfitting Audit

Inspected generic production diff: `game/final_emission_validators.py`, `game/final_emission_repairs.py`.

| Term | In new generic production? |
| --- | --- |
| stew / tavern_runner / notice_board | no |
| frontier_gate / Cinderwatch / missing_patrol | no |
| Captain Thoran / guard_captain | no |
| old_milestone / roster_board | no |

No disguised overfitting:

- not an exact replacement of `"I cannot answer that from what."`
- no T14/stew-cost string checks in engine code
- `"from what"` is not banned globally
- refusals are not flattened to `"I don't know"`
- rejected facts are not restored
- no invented source
- PR-AI / PR-AL / PR-AN / PR-AO not bypassed
- no post-hoc LLM rewrite
- dangling-connector cleanup is limited to leftover strip tails

---

## 31. Tests Added or Updated

Added:

- `tests/test_grounded_refusal_realization_grammar.py`

Updated:

- `tests/test_fallback_behavior_validator.py` — hedges are not fabricated authority; claims still are
- `tests/test_final_emission_repairs.py` — catalog hedge preserved; dangling connector drop
- `tests/test_investigation_result_provenance_non_invention.py` — GPT stub no longer encodes the broken fragment

---

## 32. Continued Multi-Turn Replay

`artifacts/prap_grounded_refusal/extended_replay/runs/20260920T203314Z_R2-MT01-AP/transcript.md`

Ordinary-play chain through stew-cost, last-checker, PR-AO look-toward, then one further walk/listen.

T12 and T14 now PASS malformed-output and player-intent gates.
T15 remains grounded inspect.
T16 continues play but is untyped (`kind=None`) with truncated narration.

---

## 33. Freeform Refusal-Realization Probe

`artifacts/prap_grounded_refusal/freeform_probe/20260920T203514Z_probe.md`

| Question class | Realization | Malformed? | Notes |
| --- | --- | --- | --- |
| unknown identity | situational `"Not something I can say here."` | no | grammatical |
| unknown time | live model invented “before dawn” | no | sibling invention |
| unknown location | routed as travel / observe | no | untyped follow-on |
| unknown cause | `"The guard says"` + insufficiency | no | deferred label sibling |
| unknown quantity | scene-hold ignorance | no | grammatical |
| unknown value | scene-hold ignorance; later explicit runner ask is complete `"from what I know"` | no | |
| insufficient / last-checker | grammatical absence | no | |
| answerable patrol ask | notice-board fact, not runner rumor | no | |
| refusal then look | PR-AM world action | no | |
| last-checker after board | grammatical absence | no | |

No `"from what."` fragment. No internal terminology leak.

---

## 34. Validation Results

| Suite | Result |
| --- | --- |
| New PR-AP refusal-realization tests | passed (`--basetemp=artifacts/prap_pytest_tmp`) |
| Scenario-independent fixtures | passed |
| Fallback-behavior validator / repairs / gate | passed |
| Final-emission boundary contract | passed |
| Social / social-lead / lock-escape | passed |
| Social emission quality | known pre-existing redirect-source red only |
| Authored-knowledge PR-AD | passed |
| Stay/leave PR-AE | passed |
| Arrival PR-AF | passed |
| Generalized exit PR-AG | passed |
| Observation PR-AH | passed |
| Bound-speaker PR-AI | passed |
| Provenance PR-AJ | passed |
| Referenced surface PR-AK | passed |
| Relevance PR-AL | passed |
| World-action PR-AM | passed |
| Sufficiency PR-AN | passed |
| Investigation PR-AO | passed |
| Narration-consistency / state-authority | passed |
| Playability eval | passed |
| Round #1 calibration | 13/13 |
| Full authoritative suite | not re-run |

Windows `PermissionError` on shared `codex_pytest_tmp` remains environmental.

Known unrelated reds, not weakened:

- `test_emission_quality_anyone_else_talk_to_manifests_preserves_redirect_not_fragment` (documented since PR-AO)
- `test_final_emission_passive_pressure_restores_recent_suspicious_figure_from_weak_atmosphere` (passive-pressure, not refusal grammar)
- two `test_social_speaker_grounding` success-flag assertions on unsupported Aldric asks (`success is None`) — social-resolution residue, not the strip path

---

## 35. Remaining Semantic / AI-Experience Failures

Dominant next: untyped walk/listen. Replay T16 resolves with `kind=None` and truncated narration after the repaired T14/T15 region.

Also remaining:

- Live model can invent time, count, price, redirect, or spoken rumor after engine absence.
- Replay T9 Guard Captain first-ask can still fall to `"I don't know."` despite PR-AI’s authored fact. Sibling flicker; do not reopen PR-AI without new causal evidence.
- Replay T13 glance still invents search-party stock.
- `"The guard says"` default label.
- Some natural paraphrases still miss `notice_board`.
- Follow-up paraphrases without owned-topic overlap can still refuse.
- `"Gate Serjeant"` → `gate_guard`.
- Look-around stock, `"What's nearby?"`, observe-fallback stacking.

---

## 36. Deferred Findings

- Do not add a stew price or economy.
- Do not add a last-reader fact.
- Do not add patrol timing or personnel.
- Do not start a project-wide State ↔ Narration campaign from live-model dawn/search-party inventions.
- Do not flatten all refusals to `"I don't know."`
- Do not build a universal grammar engine.
- Do not reopen PR-AI first-ask from one live flicker while tests remain green.
- Protected-replay baseline refresh remains deferred.

---

## 37. Recommended Next Product Slice

**Untyped walk/listen (`kind=None`) and truncated physical-action narration.**

Chosen from continued ordinary play: after repaired refusal grammar, T16 is the first new ordinary-play failure in the same sequence. The evaluator passed the truncated listen line, but routing is untyped and the sentence is cut off. That is now more severe than residual look-around stock.

Do not start pricing. Do not automatically promote live-model invention to a full State ↔ Narration campaign unless later evidence outranks T16.

---

## 38. Git / Worktree State

The worktree is dirty and was dirty before PR-AP.

PR-AP generic production: `game/final_emission_validators.py`, `game/final_emission_repairs.py`.

PR-AP tests/docs/tools: `tests/test_grounded_refusal_realization_grammar.py`, `tests/test_fallback_behavior_validator.py`, `tests/test_final_emission_repairs.py`, `tests/test_investigation_result_provenance_non_invention.py`, `tools/run_prap_freeform_probe.py`, `data/validation/prap_grounded_refusal_realization/`, `artifacts/prap_grounded_refusal/`, `PR-AP_grounded_refusal_realization_grammar.md`, `docs/NEXT_SESSION.md`.

No canonical content change. Replay/probe reset `data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`.

Do not treat `git diff --stat` against HEAD as a PR-AP-only footprint.

Not committed.

---

## 39. Confidence

High on reproduction, first incorrect realization decision, Class F classification, and the optional-material grammar contract.

High that the malformed sentence was composed by strip, not authored as a catalog fragment.

High that cedar-wharf fixtures prove the same realization contract without Frontier Gate vocabulary.

High that T12/T14 ordinary-play refusals are now complete and evaluator-green.

Medium on live-model invention after absence: the engine refusal is grammatical, but narration can still invent. Out of scope unless it becomes structured-state authority.
