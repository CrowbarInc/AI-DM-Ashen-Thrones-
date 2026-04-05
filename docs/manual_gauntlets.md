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

The repo includes a small terminal driver that calls the same `game.api.chat` path as the web UI and writes a timestamped Markdown transcript under `artifacts/manual_gauntlets/` (git branch/commit, gauntlet id, turns, scene and interlocutor snapshots).

```bash
python tools/run_manual_gauntlet.py --list
python tools/run_manual_gauntlet.py --gauntlet g5
python tools/run_manual_gauntlet.py --gauntlet g6 --no-reset
python tools/run_manual_gauntlet.py --gauntlet g3 --freeform
```

Substitute bracketed placeholders from each scenario before sending. This doc remains authoritative for definitions and rubric; the script only carries compact labels and template lines.

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

## Quick reference — repo terms used here

- **Strict-social** — NPC-directed social exchange paths and final sentence ownership filtering (see `game/social_exchange_emission.py`).
- **Offscene target** — Resolution / coercion paths that disable strict-social when `social.offscene_target` is set.
- **Repeat suppression / continuity** — Exported discussion / lead context so the model does not reintroduce the same beat; covered heavily in synthetic pytest, not wording.
- **Qualified pursuit fail-closed** — Explicit “lead to \<target\>” shapes that must resolve to a single actionable row or fail closed (`game/intent_parser.py`).
