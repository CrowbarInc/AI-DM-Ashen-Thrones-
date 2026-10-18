# PR-DD Recommended Sequence

Each cycle is independently reversible. None of them run as one combined redesign. No cycle removes a validator.

## Cycle 1 — Exact provider contract dedupe

Do this next.

Omit a top-level provider field only when its JSON is equal to the `response_policy` child. Keep the in-memory policy, the engine decision, and every validator.

Why first: about 10,947 bytes, about 11% of the common harmless request, with an equality check that makes the change reversible. It applies to every measured class, so it cuts the common case. It does not change reply-plan selection, so first-attempt acceptance should be unchanged if the model still sees one full copy.

Evidence before and after: the preference hash `d8d6737d1bfa4f6d0928719c7e1d454b83ba46b1868434c5be71b13053c26e4f` at 98,773 bytes, and the consequential hash `40e5408dc2cac4524faf2cc5a17182d92b67614e4a5d50822ed20591a8260f60` at 108,362 bytes. Re-run the same measurement script. No live call.

Rollback: restore the top-level keys. No migration.

## Cycle 2 — Affordability benchmark harness

Land the permanent benchmark from `PR-DD_affordability_benchmark.md` immediately after cycle 1, still with no live calls. Store the cycle-1 payloads as the first baseline. Later cycles compare against that baseline rather than against a drifting worktree hash.

## Cycle 3 — Pointer-instruction trim

After the baseline exists, remove instruction lines that only name a policy field which remains in `response_policy`. Keep answer-first, visibility, no-hidden-reveal, no-dice-invention, and claim-only reinforcement.

Why here: 84 lines and 13,947 section bytes are the second-largest block, and exact substring dedupe has already done all it can. Semantic edits need the benchmark and the PR-BT style diff. They are a separate rollback from cycle 1.

First-attempt risk: real. PR-BT had to restore an epistemic sentence after a deletion changed behavior. Keep this cycle to pointer lines.

## Cycle 4 — Harmless answer-packet projection

Only for turns that already select `harmless_social_incidental_dialogue_v1`. Project `gm_resolution_decision` and `decision_facing_answer_recipe` to the fields the projector and the narration contract actually read. Generate the projection from the decision. Do not store a parallel authority file.

Why after cycle 3: the decision plus recipe is about 15 KB on the preference request, but the safe remainder is unmeasured. Doing it earlier would mix hash changes with the dedupe.

Rollback: the projector returns the full decision and recipe when a new flag is off.

## Cycle 5 — Opening-scaffold predicate for non-social ordinary turns

A separate predicate, not a change to the harmless social predicate. Drop opening and world-progression keys when `opening_mode` is false and the resolver kind is `observe` or `discover_clue`. Retain the revealed clue and `scene.public`.

Transition, combat, authored facts, and consequential questions stay on the full payload.

## Cycle 6 — Retry body

Only when a retry is about to be sent, build the retry from the failure class, the resolution contract, the decision projection, and the rejected narration. Leave the first-pass builder untouched.

The historical prize is the avoided second request, not the 4,239-byte instruction. This cycle still must not weaken validation. If the retry payload cannot carry the failure class safely, keep resending the cycle-1 body.

## Explicitly later

- Removing `scene.gm_only.hidden_facts` from the provider payload. The byte saving is 372. The authority question is unresolved.
- A combat or skill-check budget. Authored fixtures do not exist.
- Forcing narration-only onto exploration or transitions to shrink the 9,568-byte system prompt.
- A new context-authority system beside `gm_resolution_decision`.

## Stop conditions for every cycle

Stop if the change needs a live provider call to decide correctness, if it edits a production save, or if it would repair the inherited patrol-test failures as a side effect. Those failures stay inherited until their own cycle.
