# Manual gauntlet — results log (template)

Copy the blocks below. Definitions, scenarios, and rubric live in [`manual_gauntlets.md`](manual_gauntlets.md).

---

## Session (once per file — shared by all entries below)

| Field | Value |
|--------|--------|
| Run date | YYYY-MM-DD |
| Branch | |
| Commit | |
| Runtime / model / local notes | e.g. model id, UI vs CLI, env quirks |
| Command used | paste full `python tools/run_manual_gauntlet.py …` or `N/A` |
| Artifact path | path under `artifacts/manual_gauntlets/` or `N/A` |

---

## Gauntlet result — one block per gauntlet

| Field | Value |
|--------|--------|
| Gauntlet id | e.g. `g5` |
| Scenario name | short label (match doc section title if helpful) |
| Result | **PASS** / **FAIL** / **INCONCLUSIVE** |
| Observed behavior | 1–3 sentences — what you saw |
| Likely implicated subsystem | your hypothesis (routing, emission, parser, …) |
| Next action | e.g. file issue, retry after fix, note for PR |

*(Duplicate this table for each gauntlet in the same session.)*

---

## Multi-gauntlet compact log (optional)

Same **Session** table once, then paste several short lines instead of full tables:

```text
g1 | PASS | …
g2 | FAIL | turn 3 reverted to hint-only — …
g8 | INCONCLUSIVE | could not change scene in this build
```

Or a minimal table:

| Gauntlet id | Result | Observed behavior (short) |
|-------------|--------|---------------------------|
| | | |
| | | |

---

## Common failure mapping (quick)

Aligns with terms in [`manual_gauntlets.md`](manual_gauntlets.md). Use for triage only — rubric detail stays there.

| What you saw | Likely area to inspect |
|----------------|-------------------------|
| Off-scene / absent NPC “speaks” or owns the reply | Target / visibility / emission boundary (`offscene_target`, strict-social sentence ownership) |
| Follow-up answer mostly repeats the prior reply (paraphrase, no new substance) | Repeat suppression / continuity in prompts; narration differentiation |
| Wrong entity becomes the pursuit or “follow lead” target | Parser / API routing / qualified pursuit resolution (`intent_parser` fail-closed path) |
| Stale interlocutor after a scene change | Scene ID / social target cleanup on transition |
