# Manual gauntlets — lead / narration smoke validation

## Purpose

Canonical **manual** smoke pass for conversational feel: continuity, speaker grounding, hint→explicit upgrades, and fail-closed pursuit behavior. Use the **exact prompt sequences** below (substitute bracketed placeholders for your loaded scene). Automated tests lock contracts and shapes; this pass catches regressions that still **feel** wrong in the UI or your usual play harness.

## When to run this pass

- After changes to **leads**, **prompt context export**, **narration**, **routing**, **social resolution**, or **final emission** (including strict-social / sentence ownership).
- After fixes touching **`offscene_target`**, qualified pursuit parsing, or repeat-suppression / discussion continuity.
- Before release or merge when those areas moved, even if `pytest` is green.

## How this differs from automated pytest coverage

| Layer | What it checks |
|--------|----------------|
| **pytest** (unit / integration / synthetic) | Storage, exports, invariants, deterministic transcript regressions, repeat-suppression contract — not whether prose “sounds” right. |
| **This gauntlet** | Named multi-turn **player scripts**, subjective pass/fail on advancement, speaker stickiness, bleed across NPCs, and closed failure on bad pursuit targets. |

Synthetic sessions can pass while wording or grounding still slips; this doc is the deliberate human spot-check.

## How to record results

After saving the transcript artifact (CLI) or when logging a UI-only pass, record conclusions with [`docs/manual_gauntlet_results_template.md`](manual_gauntlet_results_template.md): one result block per gauntlet, or several compact lines in one file for a multi-gauntlet session. Optional: paste an offending reply snippet into **Observed behavior**. Definitions and rubric remain in this doc.

### Operator CLI (local transcript)

The repo includes a small terminal driver that calls the same `game.api.chat` path as the web UI and writes artifacts under `artifacts/manual_gauntlets/`. At end of run the script prints a block titled **`=== Gauntlet artifacts ===`** with the paths it wrote (transcript always; JSON report files when reporting is enabled; optional raw trace when requested).

**Flags (reporting and naming):**

- `--report` / `--no-report` — JSON report bundle is **on by default**; use `--no-report` for transcript only.
- `--raw-trace` — additionally writes `{base}_raw_trace.json` (sanitized dump). See [Artifact outputs](#artifact-outputs).
- `--artifact-prefix NAME` — use `NAME` as the shared basename instead of the default timestamp-based name. `/` and `\` in `NAME` are replaced with `_`; leading/trailing `.` are stripped.

Substitute bracketed placeholders from each scenario before sending. This doc remains authoritative for definitions and rubric; the script only carries compact labels and template lines. Exact filenames and JSON shapes: [Artifact outputs](#artifact-outputs), [`docs/manual_gauntlet_report_format.md`](manual_gauntlet_report_format.md).

### CLI examples

```bash
# List gauntlets
python tools/run_manual_gauntlet.py --list

# Default: transcript + summary, key_events, snippets (report on by default)
python tools/run_manual_gauntlet.py --gauntlet g5

# Explicit reporting (same as default)
python tools/run_manual_gauntlet.py --gauntlet g5 --report

# Transcript only (no JSON report bundle)
python tools/run_manual_gauntlet.py --gauntlet g5 --no-report

# Deep debug: also write raw_trace.json
python tools/run_manual_gauntlet.py --gauntlet g5 --raw-trace

# Custom shared basename (becomes NAME_transcript.md, NAME_summary.json, …)
python tools/run_manual_gauntlet.py --gauntlet g3 --artifact-prefix my_g3_smoke

# Other useful combinations (unchanged behavior)
python tools/run_manual_gauntlet.py --gauntlet g6 --no-reset
python tools/run_manual_gauntlet.py --gauntlet g3 --freeform
```

## Filename evolution (transcript naming)

Older docs or habits may expect a single file named like `{gauntlet_id}_{YYYYMMDD_HHMMSS}.md`. The current driver uses a **shared basename** so one run produces sibling files:

- **Old pattern (replaced):** `{id}_{YYYYMMDD_HHMMSS}.md`
- **Current pattern:** `{timestamp}_{id}_transcript.md` (and sibling `{timestamp}_{id}_*.json` files), i.e. `{base}_transcript.md` where `{base}` is `{UTC_timestamp}_{gauntlet_id}` or your `--artifact-prefix`.

The default timestamp is UTC in a filesystem-safe form: `YYYY-MM-DDTHH-MM-SSZ` (hyphens in the time portion instead of colons), e.g. `2026-04-09T14-30-00Z_g5_transcript.md`.

## Artifact outputs

All artifacts live in `artifacts/manual_gauntlets/`. For a given run, let `{base}` be:

- `{UTC_timestamp}_{gauntlet_id}` by default (UTC, `T` and `Z` as shown in [Filename evolution](#filename-evolution-transcript-naming)), or
- the sanitized `--artifact-prefix` value.

**Always written**

| File | Role |
|------|------|
| `{base}_transcript.md` | Full Markdown transcript (git branch/commit, gauntlet id, turns, scene and interlocutor snapshots). |

**Written when reporting is on (default)**

| File | Role |
|------|------|
| `{base}_summary.json` | Run header: gauntlet id, git metadata, mode, turn count, path to transcript, report version, key-event count, whether raw trace was requested. May also include optional `axis_tags` (behavioral gauntlets G9–G12), advisory `behavioral_eval` (deterministic shallow checks; **not** a substitute for your verdict), and `behavioral_eval_warning` if that pass could not be attached. |
| `{base}_key_events.json` | Distilled high-signal events from debug/trace metadata (see companion doc). |
| `{base}_snippets.json` | Small capped set of illustrative excerpts (repairs, fallbacks, errors, heuristics). |

**Written only with `--raw-trace`**

| File | Role |
|------|------|
| `{base}_raw_trace.json` | Optional full per-turn record dump (sanitized/truncated for size/safety). For deep debugging, not routine review. |

- **Transcript-only:** `python tools/run_manual_gauntlet.py ... --no-report` — only `{base}_transcript.md`.
- **Forensic / deep debug:** add `--raw-trace` to also emit `{base}_raw_trace.json`.

JSON field-level behavior is summarized in [`docs/manual_gauntlet_report_format.md`](manual_gauntlet_report_format.md).

## Recommended review payload (what to send)

For **normal** feedback (issues, regressions, “this gauntlet failed”), include:

1. **Gauntlet id** (e.g. `g5`)
2. **Brief verdict** (PASS / FAIL / Inconclusive and one line why)
3. The compact artifacts: **`summary.json`**, **`key_events.json`**, **`snippets.json`** (paths or attached files — keep excerpts short if pasting)

**Do not** treat **`raw_trace.json`** as part of the default bundle. It is for **deep debugging** when the compact artifacts are insufficient.

Do **not** paste full JSON blobs into chat unless the compact artifacts are insufficient and you are intentionally sharing a **small** excerpt. If the compact files plus a short excerpt from `_transcript.md` do not capture the issue, attach files or link to a gist/repo path instead of dumping full `raw_trace` or entire transcripts into a message thread.

## Aggregating manual gauntlet runs

After one or more gauntlet runs, you can roll up many `*_summary.json` files into a single **aggregate report** without re-executing anything. Aggregation is a **standalone, read-only** CLI: [`tools/aggregate_manual_gauntlets.py`](../tools/aggregate_manual_gauntlets.py). It scans disk, normalizes each run, applies filters, computes metrics, and writes JSON (and optionally Markdown) under `artifacts/manual_gauntlets/reports/`.

**Anchor artifact.** Discovery is driven by **`{base}_summary.json`**. Optional siblings in the **same directory** are inferred from the same `{base}`: `{base}_key_events.json`, `{base}_snippets.json`, `{base}_transcript.md`. Only the summary is required; absent optional files are omitted quietly. **Malformed** optional files (unreadable JSON, wrong root type, etc.) produce **warnings** and that file’s data is skipped; a **bad summary** skips that run only — the rest of the aggregate still completes.

**Operator fields.** Each summary’s `operator_verdict` and `operator_notes` feed filters, metrics, and Markdown ordering. For **legacy** summaries that only have `notes`, the tool treats `notes` as operator notes when `operator_notes` is absent, so older artifacts still aggregate sensibly.

**What to use when.** Per-run artifacts (`_transcript.md`, `_summary.json`, `_key_events.json`, `_snippets.json`) are for **deep inspection** of a single pass. Aggregate reports are for **trends**, **failure clustering**, and **objective-readiness** review across many runs. If no runs match your filters, you still get a report with **zero runs** and empty rollups — that is expected, not an error.

**Filter order (exact).** Filters apply in this order: `--gauntlet-id` → `--objective` (substring on **label** or **description**, case-insensitive) → `--verdict` (case-insensitive **exact** match on `operator_verdict`). Then runs are sorted **newest first** by `started_utc` when parseable, else by the summary file’s modification time. Finally `--limit` keeps only the first **N** runs after sorting. **Sorting happens before the limit.**

For discovery rules, metrics fields, Markdown layout, event rollup details, and resilience behavior, see [`docs/manual_gauntlet_aggregation.md`](manual_gauntlet_aggregation.md).

### Aggregation CLI examples

```bash
# Full rollup: JSON + Markdown, key-event name/stage counts, snippet samples, console summary
py -3 tools/aggregate_manual_gauntlets.py --include-events --include-snippets --stdout

# Newest 10 FAIL runs for gauntlet g5; JSON only (no .md file)
py -3 tools/aggregate_manual_gauntlets.py --gauntlet-id g5 --limit 10 --verdict FAIL --json-only
```

Other useful flags: `--artifacts-dir` (default: repo `artifacts/manual_gauntlets`), `--output-dir` (default: `artifacts/manual_gauntlets/reports`), `--objective SUBSTRING`.

## Pass / fail rubric (compact)

- **PASS** — Behavior matches **What should happen** for that scenario; no **Failure** trigger.
- **FAIL** — Any **Failure** line matches, or the thread clearly violates **Target behavior** even if wording varies slightly.
- **Inconclusive** — Setup impossible (no second NPC, no scene change affordance). Note it and skip; do not count as pass.

---

## G1 — Same NPC follow-up should advance, not restate

**Target behavior** — Second line assumes the lead is already on the table; reply **advances** (detail, consequence, next beat) — not a full reintroduction.

**Setup** — One NPC `[NPC]` in scene with a followable lead (rumor, task, person, place). You are addressing `[NPC]` directly.

**Exact player prompt sequence**

1. `What do you know about [LEAD_TOPIC]?`
2. `Right — you mentioned that before. What happens if we pursue it?`

**What should happen** — Turn 1 may introduce or hint. Turn 2 acknowledges continuity and adds new information, stakes, or a concrete next step — not the same opening spiel.

**Failure** — Turn 2 restates the lead as if the first exchange did not happen (same premise, “let me tell you for the first time” energy).

**Notes / likely subsystem if it fails** — Discussion / lead storage → prompt context export → repeat suppression; same-NPC continuity in social or GM prompt assembly.

---

## G2 — Hint upgrades to explicit without reset

**Target behavior** — A hinted lead may become explicit across turns; once explicit, later turns **do not** revert to “first hint only.”

**Setup** — Same `[NPC]`; a lead that can start vague and become clear with probing.

**Exact player prompt sequence**

1. `I heard there’s trouble around [VAGUE_HOOK]. Anything you can share?`
2. `You’re holding something back. Spell it out — who’s involved?`
3. `So we’re clear: [SHORT_SUMMARY_OF_WHAT_THEY_SAID]. What’s the risk if we ignore it?`

**What should happen** — Progression from vague → specific; turn 3 treats the summary as established and pushes forward (risk, options), not back to “I don’t know what you mean.”

**Failure** — Turn 3 resets the thread to an earlier hint-only posture, or contradicts what was already made explicit without in-fiction reason.

**Notes / likely subsystem if it fails** — Lead acknowledgment / discussion rows; prompt context for “already disclosed”; GM narration merging strict-social vs exploration.

---

## G3 — Acknowledged lead becomes shared local context

**Target behavior** — After you clearly acknowledge the lead, the NPC moves past re-explaining the premise toward next beats.

**Setup** — `[NPC]` can answer about `[LEAD_TOPIC]` with a concrete lead.

**Exact player prompt sequence**

1. `What’s the real story on [LEAD_TOPIC]?`
2. `Understood — I’ll treat that as our working assumption. What should we do first?`
3. `And if that first step goes wrong, what’s our fallback?`

**What should happen** — After turn 1 establishes the lead, turns 2–3 treat it as **shared**; answers are procedural or conditional, not re-deriving the basic fact.

**Failure** — NPC re-explains the same lead as if turn 2’s acknowledgement never happened.

**Notes / likely subsystem if it fails** — Session-local discussion / lead state; exports into player-visible or GM context; strict-social emission staying with the speaking NPC while still using continuity.

---

## G4 — Same lead across different NPCs must not bleed continuity

**Target behavior** — NPC B may know the same topic, but must **not** inherit NPC A’s private acknowledgement, disclosure depth, or “we already agreed this” state.

**Setup** — Two distinct NPCs `[NPC_A]` and `[NPC_B]` in the same or adjacent fiction; both could plausibly discuss `[LEAD_TOPIC]`.

**Exact player prompt sequence** (to `[NPC_A]`)

1. `What do you know about [LEAD_TOPIC]?`
2. `Thanks — I’m with you. I’ll act on that.`

Then (to `[NPC_B]`, without quoting A’s private lines as if B heard them)

3. `What’s your take on [LEAD_TOPIC]?`

**What should happen** — B answers in character from **B’s** knowledge; no reference to **your** closed-door agreement with A unless B would reasonably know.

**Failure** — B speaks as if they witnessed A’s exact disclosure, or uses phrasing that only makes sense if B shares A’s thread state.

**Notes / likely subsystem if it fails** — Per-NPC vs global prompt context; social target resolution; discussion scoping by `npc_id` or equivalent.

---

## G5 — Off-scene / absent NPC must not steal narration

**Target behavior** — With a **grounded** active speaker `[NPC_PRESENT]`, lines that mention a lead salient to an **absent** NPC `[NPC_ABSENT]` still produce a reply **owned by** the present interlocutor (or clear deflection), not a voice swap to the absent party.

**Setup** — `[NPC_PRESENT]` is the addressed / scene-grounded speaker. `[NPC_ABSENT]` exists in lore or world data but is **not** the active social target.

**Exact player prompt sequence**

1. `Speaking to you directly — what do you make of [TOPIC_TIED_TO_ABSENT_NPC]?`

**What should happen** — Present NPC responds, refuses, redirects, or admits limits — **as** the present NPC. No full reply framed as if the absent NPC is speaking.

**Failure** — Reply reads as the absent NPC’s voice, or strict-social / final emission attributes SOCIAL sentences to the wrong party for this turn.

**Notes / likely subsystem if it fails** — `offscene_target` handling; `reconcile_strict_social_resolution_speaker` / coercion paths; `strict_social_emission_will_apply` and `apply_strict_social_sentence_ownership_filter` behavior in `game/social_exchange_emission.py`.

---

## G6 — Follow-up answer must materially differ from prior reply

**Target behavior** — A genuine follow-up question elicits **new** substance, not a paraphrase of the previous answer.

**Setup** — Same `[NPC]`, same thread as G1 after turn 1 (or any established answer).

**Exact player prompt sequence**

1. `What do you know about [LEAD_TOPIC]?`
2. `Narrow it down: where exactly should we look first, and what are we avoiding?`

**What should happen** — Turn 2 adds location, ordering, danger, or constraint not already given in turn 1.

**Failure** — Turn 2 is substantially the same content reworded, with no new actionable detail.

**Notes / likely subsystem if it fails** — Repeat suppression / continuity hints in prompts; model stochasticity (retry once); emission truncation. If it **always** repeats, treat as pipeline/context bug, not random noise.

---

## G7 — Qualified pursuit to nonexistent or unmatched named target must fail closed

**Target behavior** — Phrases shaped like **qualified pursuit** (“follow the lead to …” with a **named** target) must **not** silently invent a transition when the target cannot be resolved to exactly one valid row (per code: fail-closed guard in qualified pursuit parsing).

**Setup** — You have (or had) an active lead; use a target string that **does not** match any valid pursuit destination in your world (fake name or wrong location).

**Exact player prompt sequence**

1. `I follow the lead to [NONEXISTENT_NPC_OR_PLACE].`

(Optional second line if the engine allows clarification turns)

2. `No — I mean I go after the lead specifically toward [NONEXISTENT_NPC_OR_PLACE].`

**What should happen** — System does **not** treat this as a successful automatic scene hop to a made-up anchor. Expect refusal, clarification request, or explicit “can’t resolve” style outcome — **not** a confident arrival narrative at a fictitious ID.

**Failure** — Seamless transition or strong confirmation that you arrived at / met the nonexistent target as if resolved.

**Notes / likely subsystem if it fails** — `is_qualified_pursuit_shaped`, `_resolve_qualified_pursuit_target_to_row`, `_QUALIFIED_PURSUIT_FAILED` path in `game/intent_parser.py`; API routing around qualified pursuit in `game/api.py`.

---

## G8 — Scene change should prevent stale NPC conversational carryover

**Target behavior** — After you **leave** a scene where you were deep in dialogue with `[NPC_OLD]`, the **new** scene should not continue as if `[NPC_OLD]` is still the implicit interlocutor unless they are actually present / targeted there.

**Setup** — Ability to move to a different scene (travel, exit, or engine affordance). `[NPC_OLD]` stays behind; `[NPC_NEW]` or environment-only is in the new location.

**Exact player prompt sequence** (in original scene, to `[NPC_OLD]`)

1. `I need everything you have on [LEAD_TOPIC] — hold nothing back.`
2. `[Use your build’s normal scene-change affordance — travel, exit, or equivalent — so you are no longer in the same scene as [NPC_OLD].]`
3. `What’s going on here?`  
   (Do **not** name or address `[NPC_OLD]` in this line unless the UI shows them present in the new scene.)

**What should happen** — New scene grounding: narrator or local presence; no automatic reply **as** `[NPC_OLD]` unless the system shows them present.

**Failure** — `[NPC_OLD]` answers as primary speaker in the new scene without an in-fiction reason, or social resolution still locks to the old NPC ID after the transition.

**Notes / likely subsystem if it fails** — `active_scene_id` / scene state; social target clearing on transition; session carryover of `social` resolution into the wrong scene.

---

## G9 — Neutral prompt should not provoke ungrounded hostility

**Target behavior** — Calm, observational, or informational player lines should not be met with **socially hostile** GM prose (accusations, insults, “how dare you”) **unless** the fiction clearly grounds that tone (orders, reports, prior provocation called out in the same reply).

**Setup** — Any grounded speaker `[NPC]` or narrator context where a neutral look-around or read-aloud is natural.

**Exact player prompt sequence**

1. `What do I see at [LOCATION]?`
2. `I read the posted notice calmly — what does it actually say?`

**What should happen** — Replies stay proportionate: description, mild wariness, or grounded pushback tied to visible facts — not a personal attack stack with no diegetic cause.

**Failure** — GM voice piles on insults, “traitor,” “liar,” or similar **without** grounding cues (patrol orders, witnessed acts, faction policy) after neutral input.

**Notes / likely subsystem if it fails** — Prompt tone routing, social strictness, or model drift; compare advisory `behavioral_eval` → `neutrality` in `summary.json` (tests-only evaluator; see `tests/helpers/behavioral_gauntlet_eval.py`).

---

## G10 — Escalation should track player pressure, not jump or flatten

**Target behavior** — When the player stays **neutral**, the GM should **not** snap to combat-grade violence or arrest beats without transition. When the player is clearly **hostile or violent**, the GM should **not** respond with fawning compliance that ignores the threat.

**Setup** — `[NPC]` who can speak in-character under mild and strong pressure.

**Exact player prompt sequence**

1. `I listen quietly — what can you tell me about the mood here?`
2. `I'm done being patient: I curse you and draw steel; this ends now.`

**What should happen** — Turn 1: informative or lightly tense, not blood/combat initiation. Turn 2: meets the threat with plausible resistance, fear, combat framing, or refusal — not “anything you wish, master.”

**Failure** — Neutral line (turn 1) triggers attacks/combat/arrest-with-shackles escalation; or hostile line (turn 2) gets only uncritical subservience with no acknowledgment of danger.

**Notes / likely subsystem if it fails** — Resolution kind routing, intent classification, social vs exploration narration merge; advisory `behavioral_eval` → `escalation_correctness`.

---

## G11 — Re-engagement after uncertainty should progress the exchange

**Target behavior** — If the GM asks for **clarification**, the next GM beat after the player narrows the scope should **advance** (specific detail, direction, stakes) — not another generic “be more specific” stall.

**Setup** — `[NPC]` with local knowledge who may reasonably ask which quarter, time, or topic you mean.

**Exact player prompt sequence**

1. `What rumors matter around [PLACE]?`
2. `The [WARD] quarter, last night — be concrete.`

**What should happen** — Turn 2 receives a **new** concrete hook (place, person, sensory detail, or next step), not a duplicate clarification loop.

**Failure** — Second GM reply is another empty clarification request with no new fiction.

**Notes / likely subsystem if it fails** — Discussion continuity, lead export into GM context; advisory `behavioral_eval` → `reengagement_quality`.

---

## G12 — Multi-turn dialogue should remain locally coherent

**Target behavior** — Across **adjacent** turns in the same scene, the GM should not **contradict** a focal object without cause, inject **tutorial/session-reset** breaks, or **swap speaking NPC identity** without a player handoff cue (addressing another NPC, “I turn to the clerk,” etc.).

**Setup** — Stay in one scene with one primary `[NPC]` for both lines (or explicitly hand off if testing a two-NPC desk).

**Exact player prompt sequence**

1. `What is posted at [GATE_OR_POSTING]?`
2. `I acknowledge that — what happens if we ignore it?`

**What should happen** — Turn 2 treats turn 1’s content as **shared** and pushes consequences or options; same implied speaker unless you clearly pivot.

**Failure** — Adjacent GM lines deny then affirm the same object, reset to “tutorial” voice, or answer as a different NPC mid-thread with no player cue.

**Notes / likely subsystem if it fails** — Speaker binding, continuity repairs, scene/session state; advisory `behavioral_eval` → `dialogue_coherence`.

---

## Quick reference — repo terms used here

- **Strict-social** — NPC-directed social exchange paths and final sentence ownership filtering (see `game/social_exchange_emission.py`).
- **Offscene target** — Resolution / coercion paths that disable strict-social when `social.offscene_target` is set.
- **Repeat suppression / continuity** — Exported discussion / lead context so the model does not reintroduce the same beat; covered heavily in synthetic pytest, not wording.
- **Qualified pursuit fail-closed** — Explicit “lead to \<target\>” shapes that must resolve to a single actionable row or fail closed (`game/intent_parser.py`).
