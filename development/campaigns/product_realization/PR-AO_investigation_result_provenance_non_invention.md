# PR-AO — Gameplay / State Authority: Investigation Result Provenance and Non-Invention

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/prao_investigation_provenance/`

---

## 1. Executive Summary

PR-AO repaired the highest-leverage ordinary-play failure after PR-AN: after a grounded last-checker no-answer, thanking the runner and looking toward the gate line routed as `investigate` and minted an unsourced lead-registry rumor titled “Details on the exact timing and personnel of the missing patrol assignment.”

The recovered contract is:

```text
INVESTIGATION MAY DISCOVER THE AUTHORITATIVE WORLD.
INVESTIGATION MAY NOT AUTHOR THE WORLD.

PLAYER SEEKS EVIDENCE X
    + AUTHORIZED DISCOVERABLE X EXISTS
    → X MAY BE DISCOVERED

PLAYER SEEKS EVIDENCE X
    + NO AUTHORIZED DISCOVERABLE X EXISTS
    → GROUNDED ABSENCE

never:
PLAYER SEEKS X → X BECOMES A CLUE
```

T15 world truth is **Class D** for exact patrol personnel/timing at the gate line, with **Class C** related evidence already landed (`notice_patrol_route`). No timing or personnel facts were added.

No new clue system, evidence registry, investigation engine, or provenance owner was introduced. Existing scene facts, interactables, discoverable clues, referenced-surface classification, RC-21 lead landing, and perception grounding were sufficient once untargeted/overlay discovery stopped being treated as evidence authority.

---

## 2. Starting Failure

PR-AN extended replay T15:

> Player: I thank the runner and look toward the gate line again.
> GM: Details on the exact timing and personnel of the missing patrol assignment.
> `resolution.kind`: `investigate`
> Social after: activity / investigate (runner rebound-cleared)
> New lead: `details_on_the_exact_timing_and_personnel_of_the_missing_patrol_assignment`
> `discovery_source`: `clue_explicit`

The social frame was no longer the problem. The world-action continuation invented the evidence the recent conversation had asked for.

---

## 3. T15 End-to-End Trace

Traced against live `frontier_gate` / PR-AN T14 state before production changes.

| Stage | Before repair |
| --- | --- |
| Social before input | `tavern_runner`, social, engaged |
| After `"I thank the runner"` | PR-AM world-action override → activity |
| Parsed action | `investigate` |
| Why `look toward` became investigate | `look toward` was not in directed-look patterns; fallback `(look\|search\|…) → investigate` with no target |
| Extracted target | empty / untargeted |
| Target authority | `AUTHORITY_UNTARGETED` |
| Visible facts | notice board, serjeant/roster mention, runner/stew, muddy gate line, census choke |
| Hidden facts | watcher/agent/spotter rows; no personnel/timing |
| Authored clues | `notice_patrol_route` only |
| Public clues already landed | `notice_patrol_route`, `milestone_mud_prints` |
| Recent contextual / overlay | GPT `visible_facts_add` / `discoverable_clues_add` could inject extra rows into the effective scene |
| Candidate investigation result | scene-level next-clue conveyor (`process_investigation_discovery`) plus GPT title |
| Selected result | unsourced title about exact timing and personnel |
| Function/path creating the slug | title → existing `slugify` → lead-registry id |
| Provenance attached | `clue_explicit` (treated as discovered clue) |
| Did any source contain timing/personnel? | **no** |
| Entered authoritative state? | **yes** — session lead registry |
| Became a clue? | not an authored `discoverable_clues` id; registry rumor only |
| Became a lead? | **yes** |
| Narration only? | **no** |
| Consequences | new active rumor; no travel |

After repair, the same input extracts `gate line` as an authored visible feature, skips the conveyor, and force-grounds narration to that fact.

---

## 4. T15 Result Classification

The suspicious T15 result was **not** an authored clue.

| Question | Answer |
| --- | --- |
| What it actually was | Canonical lead-registry rumor (`type: rumor`, `lifecycle: discovered`) |
| Classes | **E** (lead-registry entry) minted from **H/J/K** (investigation fallback / player-intent / LLM text), not A–D |
| Storage | `session[lead_registry]` |
| Owner | RC-21 lead registry via `clue_explicit` landing |
| ID | `details_on_the_exact_timing_and_personnel_of_the_missing_patrol_assignment` |
| Title | `Details on the exact timing and personnel of the missing patrol assignment.` |
| Source | unsourced investigation result text, not `frontier_gate` `discoverable_clues` |
| Provenance | `discovery_source: clue_explicit` (false authority) |
| Lifecycle | discovered / active |
| Downstream authority | later pursuit, journal, and prompt context would treat it as a real lead |

It was not a contextual hint, not `narration_ctx_…`, and not pure narration.

---

## 5. Authoritative World Truth

At T15:

- The world does **not** know exact patrol personnel as authored evidence.
- The world does **not** know exact patrol timing as authored evidence.
- The gate line visible fact is crowd/watchers/refugees, not a roster of names or times.
- The only authored discoverable clue at the gate is `notice_patrol_route` (last-seen route). That clue was already landed.
- Related evidence exists (missing-patrol warning, last-seen track). It does not establish who or when.
- The recent questions created an information need, not a discoverable fact.

Classification: **Class D** for the requested timing/personnel evidence here; **Class C** for related already-landed route evidence.

---

## 6. First Incorrect Authority Decision

The first incorrect authority decision was:

```text
untargeted investigate
    + skip_unrelated_clue_discovery = false
    → scene clue conveyor / overlay-injected discoverable rows
      treated as authorized evidence
```

`look toward` failing to extract a target made T15 untargeted. That routing gap was a contributing cause, not the root authority bug. Any untargeted `investigate` could mint the next scene clue or overlay text.

Repair the conveyor/provenance gate, not merely remap the verb.

---

## 7. Look-Toward Routing Audit

| Phrase | Intended family | Before | After |
| --- | --- | --- | --- |
| look / look around | observe or untargeted investigate | fallback investigate | unchanged fallback; untargeted now skips evidence mint |
| look at / glance at | targeted inspect/investigate | targeted | targeted |
| look toward / look towards | targeted inspect of a named surface | **untargeted investigate** | targeted investigate |
| inspect / examine / search / investigate | targeted investigate | targeted | targeted |

`look toward X` is defensible as targeted investigate/inspect once X is extracted. After the extract fix, T15 is `investigate` of authored visible feature `gate line`. That routing is **correct and incidental** to the remaining authority rule: even deliberate investigate must not mint unsupported evidence.

No `"gate line"` special case.

---

## 8. Existing Investigation Authority Contract

Recovered, not replaced:

```text
PLAYER INVESTIGATES TARGET
    → TARGET IS AUTHORITATIVELY GROUNDED
    → AUTHORIZED DISCOVERABLE EVIDENCE EXISTS
    → EVIDENCE MAY BE REVEALED
    → LEGITIMATE STRUCTURED CONSEQUENCES MAY FOLLOW

PLAYER INVESTIGATES TARGET
    → NO AUTHORIZED DISCOVERABLE EVIDENCE
    → GROUNDED ABSENCE / NEUTRAL SURFACE
    → NO NEW EVIDENCE AUTHORITY CREATED
```

Owners:

- Interactable + `reveals_clue` → `discover_clue`
- Authored visible feature without inspectable contents → skip conveyor; narrate the fact
- Hidden / unsupported / empty interactable → skip conveyor; do not instantiate
- Untargeted investigate → skip conveyor; skill-check bookkeeping may still run
- HTTP conveyor → canon `load_scene` `discoverable_clues` only

---

## 9. Existing Clue Authority Contract

Authorized origins remain:

- authored scene `discoverable_clues`
- authored interactable `reveals_clue` / inspectable text
- authored hidden facts revealed by existing interactable contracts
- RC-21 `clue_explicit` landing of those discoveries

Not authorized:

- overlay `discoverable_clues_add`
- player investigative goal / hypothesis
- recent unanswered questions
- GPT title/prose
- scene-level “next clue” conveyor on an untargeted or non-inspectable look

`process_investigation_discovery` remains a compatibility conveyor for helper-direct / authorized-depth callers. It is not a license to invent.

---

## 10. Existing Provenance Contract

RC-21 still owns canonical leads. PR-AJ still fails closed on unsourced prose → lead.

PR-AO adds the investigation-side corollary: a generated title/id is not provenance. `clue_explicit` may land only when the discovered text comes from an authored discoverable/interactable source.

---

## 11. Root Cause

Confirmed.

1. `look toward` was not a directed-look extractor, so T15 became untargeted `investigate`.
2. Untargeted investigate did not set `skip_unrelated_clue_discovery`.
3. `process_investigation_discovery` then treated the effective scene’s discoverable list as evidence, including overlay-injected rows.
4. The resulting title was slugged and landed as `clue_explicit`.

The recent personnel/timing questions supplied the language. They did not supply a source.

---

## 12. Recovered Investigation Non-Invention Contract

```text
INVESTIGATIVE INTENT ≠ EVIDENCE EXISTENCE
WORLD TRUTH ≠ LOCAL DISCOVERABILITY
RELATED EVIDENCE ≠ REQUESTED PROPERTY
PLAYER HYPOTHESIS ≠ FACT
RECENT CONVERSATION ≠ PHYSICAL EVIDENCE
UNSOURCED TEXT ≠ AUTHORITATIVE CLUE
```

Failure to find authorized evidence is a valid investigation result.

---

## 13. Implementation

Generic production only:

- `game/intent_parser.py` — `look toward` / `look towards` on investigate, mixed-turn, and world-action seams
- `game/referenced_surface.py` — same extractors; content-question target extract (`what is posted/written on`); untargeted skip; untargeted grounded-absence line
- `game/exploration.py` — keep bound interactable ids when text extract is empty; skip conveyor for untargeted; do-not-invent hint; do not early-return before skill checks
- `game/api.py` — investigation conveyor uses canon `load_scene` clues only
- `game/perception_grounding.py` — force-ground invented investigate prose for untargeted / empty / unsupported surfaces

No canonical scene or world-content edits.

---

## 14. Player Intent vs Evidence Existence

Amber-quay fixtures search for last user, exact time, opener, or “Identity X”. The inspect is valid. Those properties are not created. Authored wax/bootprints remain discoverable when present.

---

## 15. Player Hypothesis Behavior

“Proof that Rowan poisoned the well” and “signs that Rowan was here” do not mint a Rowan/poison clue or adopt guilt. Narration is replaced with grounded absence / visible surface.

---

## 16. Recent-Conversation Leakage Audit

Ask the warden who oiled a hinge (no answer), then inspect the bench. No hinge-oiler clue. Live probe: ask who oiled the hinge, then inspect the rain barrel. Lead registry unchanged.

---

## 17. World Truth vs Local Discoverability

Fixture: `world_state.mara_owns_missing_key = true`, quay has no Mara/key evidence. Search does not leak the key. Live probe: search the square for Mara’s key. No key lead.

---

## 18. Related-but-Insufficient Evidence

Authored wax stain may land. It is not rewritten into “Mira used this” or an identity clue. Same principle as PR-AN sufficiency, for physical evidence.

---

## 19. Authored Visible Evidence

Visible facts may be reported. Invented contents (“silver locket”) are replaced. T15 after: gate-line visible fact only.

---

## 20. Authored Hidden/Discoverable Evidence

Interactable `reveals_clue` still lands `window_prints` / `chit_lead` / `notice_patrol_route`. Helper-direct `process_investigation_discovery` still reveals the next authored clue. Visible/hidden distinctions are not flattened.

---

## 21. Empty Investigation / Grounded Absence

Valid target, no evidence → no clue/lead/fact mint. Repeated empty inspect does not accumulate specificity.

---

## 22. Clue Title / ID Generation Audit

The T15 slug was derived from result title text via existing slugify, not from an authored id.

Before: title came from unsourced investigation/GPT/overlay text, then became the id.

After: that title is not constructed as structured state. Authored clues keep their authored ids (`window_prints`, `notice_patrol_route`).

A generated id is not itself proof of invented authority. Generating a new structured clue from non-authoritative text is.

---

## 23. Clue Provenance Gate

Unsupported text cannot mint an authoritative clue. Overlay-injected discoverable rows are filtered out of the HTTP conveyor. Authorized interactable discoveries still land.

---

## 24. Failed-Investigation State Mutation

Absence does not create a clue, lead, hidden fact, interactable, NPC, timestamp, or personnel row. Action history, social-frame clear, and optional skill-check bookkeeping remain.

---

## 25. Successful-Investigation State Mutation

Authored discoverable clues keep stable ids, `clue_explicit` provenance, and legitimate consequences (`leads_to_scene` still fires). Rediscovery is `already_searched` / same id, not a duplicate mint.

---

## 26. Relationship to PR-AH

PR-AO is the **investigation analogue** of PR-AH:

```text
OBSERVATION MAY REVEAL THE AUTHORITATIVE WORLD.
OBSERVATION MAY NOT AUTHOR THE WORLD.
```

It is not a rewrite of perception grounding’s observe path. Force-surface was extended to empty/untargeted/unsupported **investigate** so invented investigate prose cannot survive as player-facing text.

---

## 27. Relationship to PR-AJ / RC-21

T15 is a **sibling path**, not incomplete PR-AJ enforcement.

| | PR-AJ | PR-AO |
| --- | --- | --- |
| Source | unsourced narration prose | unsourced investigation result / overlay / conveyor |
| Sink | lead registry via `narration_ctx_…` | lead registry via `clue_explicit` |
| Repair | fail-closed prose promotion | skip unauthorized discovery; canon-only conveyor |

RC-21 remains. `remember_recent_contextual_leads` was not deleted.

---

## 28. Frontier Gate T15 Before / After

| | Before (PR-AN replay) | After (`20260920T195555Z_R2-MT01-AO`) |
| --- | --- | --- |
| Social before | `tavern_runner` / social | same |
| Parsed action | `investigate` untargeted | `investigate` of `gate line` |
| Authority | untargeted | `authored_visible_feature` |
| Skip conveyor | false | true |
| Selected result | invented timing/personnel title | visible gate-line fact |
| Suspicious slug | created | **not created** |
| New clue/lead | yes | no |
| Timing/personnel fact | invented | none |
| Narration | the invented title | “On closer inspection, threadbare watchers and refugees cluster along the muddy gate line. Closer looking yields nothing further.” |
| Next turn | n/a | walk/listen continues; registry unchanged |

---

## 29. Scenario-Independent Generalization Fixtures

Amber-quay / cooper-bench / bell-warden / mill-chit vocabulary. Eighteen HTTP/generalization tests plus content-question, overlay-filter, helper-direct, and T15 regression.

| Gate | Result |
| --- | --- |
| 1 Visible evidence | PASS |
| 2 Hidden/discoverable | PASS |
| 3 Valid target, no evidence | PASS |
| 4 Requested identity absent | PASS |
| 5 Requested time absent | PASS |
| 6 Related evidence only | PASS |
| 7 World-true, locally undiscoverable | PASS |
| 8 False hypothesis | PASS |
| 9 Recent conversation leak | PASS |
| 10 Authorized clue consequence | PASS |
| 11 Unsourced text cannot mint | PASS |
| 12 Observe empty | PASS |
| 13 Investigate empty | PASS |
| 14 Player-specified relation | PASS |
| 15 Player-specified timing | PASS |
| 16 Authorized different evidence | PASS |
| 17 Repeated empty | PASS |
| 18 Rediscovery no duplicate | PASS |

Plus: written-surface question still discovers an authored clue (PR-AD notice-question regression).

---

## 30. Anti-Overfitting Audit

Scanned generic engine diffs for calibration identifiers. None newly introduced in `exploration.py`, `intent_parser.py`, `referenced_surface.py`, `perception_grounding.py`, or the `api.py` conveyor filter.

Not used:

- Frontier Gate / gate line / missing patrol / tavern runner / notice board / personnel / exact timing / Captain Thoran / Cinderwatch / Old Milestone / stew special cases
- filtering the exact suspicious slug
- banning the words “timing” or “personnel”
- special-casing T15
- suppressing all investigation clues
- treating every investigate failure as observe
- deleting hidden evidence
- treating every player hypothesis as false rather than non-authoritative

`patrol` already existed in intent-parser pursuit keywords; it was not added here.

---

## 31. Tests Added or Updated

New: `tests/test_investigation_result_provenance_non_invention.py` (26 tests).

No existing expectation files were weakened.

Tools/fixtures: `tools/run_prao_freeform_probe.py`, `data/validation/prao_investigation_result_provenance/scenarios.json`.

---

## 32. Continued Multi-Turn Replay

`artifacts/prao_investigation_provenance/extended_replay/runs/20260920T195555Z_R2-MT01-AO/transcript.md`

Chain through learn / pursue / travel / arrive / observe / investigate / return / grounded observe / captain first-ask / roster inspect / stew / glance-back / last-checker / T15 / one further walk-and-listen.

T15: social cleared; investigate `gate line`; no invented lead.

T16: play continues; lead registry still only `notice_patrol_route` and `milestone_mud_prints`. `resolution.kind` was `None` (walk/listen is not an existing typed action). Evaluator PASS; no structured mint.

---

## 33. Freeform Investigation-Provenance Probe

`artifacts/prao_investigation_provenance/freeform_probe/20260920T195740Z_probe.md`

| Action | Result |
| --- | --- |
| glance toward rain barrel | visible feature; no clue |
| investigate rain barrel | same; no clue |
| look at notice board | `notice_patrol_route` lands |
| search mud for tracks | visible “mud”; no new clue |
| inspect board for last writer | `already_searched`; no identity lead |
| examine board for exact time | `already_searched`; no timing lead |
| Rowan-poison search | no Rowan lead |
| signs Rowan was here | unsupported; no Rowan presence |
| ask hinge-oiler, then inspect barrel | no hinge clue |
| search square for Mara’s key | no key lead |
| reread notice | already searched; no duplicate id |
| investigate barrel again | no accumulation |
| look toward townhouse doorway | unsupported; no invented doorway evidence |

Lead registry never gained an invented slug. Live-model speech after `already_searched` (T6 census/route-change mutter) remains narration residue, not structured authority.

---

## 34. Validation Results

| Suite | Result |
| --- | --- |
| PR-AO investigation-provenance tests | 26 passed |
| Scenario-independent fixtures | passed |
| Exploration / skill-check | passed |
| Observation / PR-AH | passed |
| Intent parser | passed |
| Interaction / world-action | passed |
| Referenced-surface / PR-AK | passed |
| Clue / clue-knowledge / lead-registry | passed |
| RC-21 destination-redirect / upsert | passed |
| Narration-consistency / state-authority | passed |
| Social / PR-AL / PR-AN | passed |
| PR-AD authored-knowledge | passed |
| PR-AE stay/leave | passed |
| PR-AF arrival | passed |
| PR-AG generalized-exit | passed |
| PR-AI bound-speaker | passed |
| PR-AJ provenance | passed |
| PR-AM world-action | passed |
| Playability eval | passed |
| Round #1 calibration | 13/13 |
| Full authoritative suite | not re-run |

Windows `PermissionError` on shared `codex_pytest_tmp` remains environmental; focused runs used `artifacts/prao_pytest_*`.

---

## 35. Remaining Semantic Failures

Dominant next: grounded no-answer catalog grammar. T14 in this replay still emits `"I cannot answer that from what."` and fails the evaluator on that fragment.

Also remaining:

- Live model can still invent speech after `already_searched` or engine absence (probe T6).
- T16 walk/listen is untyped (`kind=None`) and can truncate.
- Prior look-around stock, paraphrase, Gate Serjeant, geography-bleed, and `"What's nearby?"` residue.
- `"The guard says"` default label (probe T5).

---

## 36. Deferred Findings

- Do not add patrol timing or personnel.
- Do not add a last-reader / board-history store.
- Do not gag live-model invention with a new prompt architecture in this slice.
- Do not delete `remember_recent_contextual_leads`.
- Do not flatten observe vs investigate eligibility.
- Do not retarget walk/listen unless later evidence outranks grammar.
- Do not start a general State ↔ Narration program from T16 narration of the crowd.

---

## 37. Recommended Next Product Slice

**Grounded no-answer grammar:** `"I cannot answer that from what."`

Chosen from the same ordinary-play replay: T15 is repaired and T16 continues, but T14 still semantically FAILs on the catalog refusal fragment. That is class C in the PR-AO next-slice list. It is more severe than T16’s untyped walk/listen, which the evaluator passed and which minted no authority.

Do not reopen investigation provenance, PR-AN sufficiency, or RC-21 unless new evidence shows they cause the broken sentence.

---

## 38. Git / Worktree State

The worktree is dirty and was dirty before PR-AO.

PR-AO generic production: `game/exploration.py`, `game/intent_parser.py`, `game/api.py`, plus already-untracked `game/referenced_surface.py` and `game/perception_grounding.py` from PR-AK / PR-AH.

PR-AO tests/docs/tools: `tests/test_investigation_result_provenance_non_invention.py`, `tools/run_prao_freeform_probe.py`, `data/validation/prao_investigation_result_provenance/`, `artifacts/prao_investigation_provenance/`, `PR-AO_investigation_result_provenance_non_invention.md`, `docs/NEXT_SESSION.md`.

No canonical content change. Replay/probe reset `data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`.

Do not treat `git diff --stat` against HEAD as a PR-AO-only footprint.

Not committed.

---

## 39. Confidence

High on T15 classification, first incorrect authority decision, and the non-invention contract.

High that look-toward→investigate is now a targeted inspect of an authored visible feature and is not the remaining authority bug.

High that amber-quay fixtures prove the same predicates without Frontier Gate vocabulary.

Medium on live-model speech after `already_searched`: the engine no longer mints structured clues, but narration can still invent. That is out of scope unless it becomes a structured-state problem.
