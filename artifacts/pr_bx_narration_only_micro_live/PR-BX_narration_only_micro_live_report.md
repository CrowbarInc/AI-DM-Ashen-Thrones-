# PR-BX — Narration-only envelope micro-live gate

Date: 2026-10-06.

MODE: CONTROLLED MICRO-LIVE VALIDATION.

Model requested by production routing: `gpt-4.1-mini`. Every gameplay response resolved to `gpt-4.1-mini-2025-04-14`.

LIVE CALLS: 7. One startup preflight is excluded from gameplay totals, matching prior gates. Gameplay generations: 6. Production retries: 3. Infrastructure reruns: 0. Manual reruns: 0. No production code was changed in this cycle.

Harness: `artifacts/pr_bx_narration_only_micro_live/run_probes.py`. Same P1/P2/P3 fixtures and player wording as `artifacts/pr_bv_turn_operation_projection_micro_live/run_probes.py`.

## Decision

**C — P2 NARRATION-ONLY CONTRACT NEEDS BOUNDED REPAIR.**

P2 selected narration-only, and the provider's first response obeyed `{"narration": "..."}`. Declaration validation accepted that response with application-created empty claims. The turn still failed. Narration validation rejected the ordinary dialogue, and the retry feedback for `unauthorized_resolution_decision_fact` told the model to answer again as a structured envelope with `declared_claims`. The second response included `declared_claims` and was rejected by the narration-only parser as `unexpected_declared_claims`. The player received the safe-nonresolution fallback.

The declaration-affordance pathology targeted by PR-BW did not appear on the first generation. The narration-only retry path did not preserve the contract for this rejection reason, so the envelope was unreliable.

## Phase 0

Focused deterministic slice: PASS, 26 tests. Broad deterministic slice matching the PR-BW review: PASS, 158 tests. See `focused_tests.txt`.

Selection on the prior P1/P2/P3 decisions, before any API call:

| Probe | Envelope | Operation | Declaration expectation | Consequential realization required | Declaration channel |
| ----- | -------- | --------- | ----------------------- | ---------------------------------- | ------------------- |
| P1 | structured_realization | bounded_interpretation | optional_bounded_inference | false | exposed |
| P2 | narration_only | incidental_dialogue | reply_not_required | false | not exposed |
| P3 | structured_realization | player_hypothesis_discussion | hypothesis_discussion_not_required | false | exposed |

The narration-only contract is exactly `{"narration": "player-facing response"}`. `declared_claims` is absent from that system prompt. A sample narration-only payload normalizes to `declared_claims: []` with `declaration_authorship: false`. A smuggled `declared_claims` field is rejected.

## Probes

Same scenes and wording as the PR-BV gate.

P1, chapel belfry. Visible facts only: the bell's wooden yoke is split; the bell's leather hanger is torn.

> I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?

P2, bread stall. Visible fact: a baker stands beside loaves. No authored loaf preference.

> Baker, which loaf do you usually keep for yourself?

P3, fresh chapel belfry with the same two visible facts.

> Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?

## P2 critical validation

Selection on the live decision: `narration_only`. Authority owner: `gm_resolution_decision`. Projection only. Response operation: `incidental_dialogue`. Declaration expectation: `reply_not_required`. Consequential realization required: false. Declaration channel exposed by the selector: false.

Provider contract on both generations: narration-only system prompt. No API response schema was sent. `declared_claims` is absent from that system prompt.

Attempt 1 provider shape:

```json
{"narration": "The baker glances around briefly before muttering, “I’m afraid that’s not something I share lightly. Best you choose your own favorites from the loaves here.” Their tone holds a guarded edge, unwilling to reveal personal preference."}
```

Keys: `narration` only. Parser normalization: `declared_claims: []`, `normalized_empty_declarations: true`, `declaration_authorship: false`. Declaration validation: `hard_valid: true`, accepted claims empty, rejected claims empty.

That first response is ordinary NPC dialogue. It does not expose JSON to the player and does not author a declaration. It was not emitted.

Narration validation rejected it with `unauthorized_resolution_decision_fact`:

- "Best you choose your own favorites from the loaves here." — `unowned_stateful_world_assertion`
- "” Their tone holds a guarded edge, unwilling to reveal personal preference." — `unauthorized_evidential_relation`

The second violation text begins with a curly quote, so the sentence split itself is suspect. This cycle does not reclassify that narration reject as a false reject and does not change the validator.

Retry feedback, while the system prompt stayed narration-only, said: "Answer again as the same structured envelope with declared_claims plus narration." The authoritative retry context also attached `structured_envelope_schema` containing `declared_claims`.

Attempt 2 provider shape had keys `declared_claims` and `narration`. The declaration mode string was the schema placeholder `realize|propose`. Parser result: `structured_contract_failure`, reason `unexpected_declared_claims`. No realization envelope was created. `declaration_authorship` was not set.

Emitted narration:

> No one here can answer that from what is settled here.

Provenance: `safe_nonresolution`. That string is a validation fallback. It does not function as ordinary NPC dialogue.

Retry classification, not treated as one cause:

1. The old PR-BW pathology did not occur. Attempt 1 did not emit an unauthorized `realize` / `authored_world_fact` declaration.
2. The first rejection is narration validation of the prose, not a malformed narration-only envelope.
3. The second failure is the narration-only retry interaction. Feedback reintroduced the declaration channel, the model followed that instruction, and the narration-only parser correctly refused the extra field.

Tokens: attempt 1 input 23413, output 55, total 23468. Attempt 2 input 24881, output 154, total 25035. Turn input 48294, output 209, total 48503. Two provider attempts.

Compared with PR-BV P2: initial 24671 in / 421 out, retry 26142 in / 295 out, turn input 50813. That earlier retry existed to recover from an unauthorized structured declaration and then accept empty `declared_claims`. This gate did not repeat that recovery. It still spent a second full prompt, and the second prompt did not produce an accepted narration. This sample does not support a generalized cost-savings claim.

State: scene visible facts unchanged. World authoritative slice unchanged aside from the default faction clock, which the harness excludes. Rejected narration sentences were stored as unauthorized and `do_not_persist`. No accepted incidental was promoted to world truth.

## P1 control

Live selection: `structured_realization`, `bounded_interpretation`, `optional_bounded_inference`. Declaration channel remained available.

Attempt 1 declared a `propose` / `gm_inference` / `inferred` claim and narrated prolonged heavy use or a sudden impact. Validator rejected it for `unauthorized_causal_relation`. That is the same class of over-causal narration seen in the PR-BV P1 probe.

Attempt 2 narrated "clearly split" and "significant wear" and was also rejected (`unauthorized_certainty_upgrade`, `unsupported_narrator_lead`). Emitted text is the authorized observation fallback:

> The bell's wooden yoke is split. The bell's leather hanger is torn.

First-attempt input tokens: 22084, the same count as PR-BV P1. Provider contract remained structured. Assessment: **P1-A**. This is the existing narration-quality limitation. It is not a new PR-BW regression. Only P1-C would block acceptance, and P1-C was not observed.

## P3 control

Live selection: `structured_realization`, `player_hypothesis_discussion`, `hypothesis_discussion_not_required`.

The player hypothesis was stored with `epistemic_status: hypothesis`, `provenance: player_hypothesis`, and `authority: observation`. It was not stored as an established world fact. Scene facts did not gain a cutter, motive, tool, or time.

Both generations were rejected for narrator-lead / evidential wording around the hypothesis discussion. Emitted text is the same two visible facts, not a hypothesis discussion. First-attempt input tokens: 22108, the same count as PR-BV P3, which had accepted a cautious discussion on the first pass. The provider payload for P3 was not migrated and was not shrunk. This weaker sample is not a PR-BW regression. It is evidence that P3 can still pay a full structured retry. That is a possible later envelope slice, not a change to make in this cycle.

## Cross-probe integrity

Authority: `gm_resolution_decision` remained the owner. The envelope selector remained `projection_only`.

Selection: P1 and P3 stayed structured. P2 stayed narration-only. Consequential realization was not required on these probes and did not enter narration-only.

State: no unauthorized world mutation on P1, P2, or P3.

Provenance: narration-only normalization on P2 attempt 1 created empty claims with `declaration_authorship: false`. It did not create an authored world fact. Attempt 2's declaration fields were rejected and not accepted.

C18 canonical path:

- P1 and P3: the sealed text is the authorized-observation fallback after both structured generations were rejected. Accepted, sealed, and emitted strings match.
- P2: attempt 1 normalized to a narration-only realization envelope, then narration validation rejected that text before seal. Attempt 2 never became a realization envelope. The sealed object is `safe_nonresolution`. Accepted, sealed, and emitted strings match that fallback. They do not match the provider narration.

Player-facing leakage: none of the three emitted strings contain `declared_claims`, provenance metadata, semantic identities, validator language, response-contract instructions, or JSON.

## Cost / retry comparison

| Probe | Envelope | Input tokens | Output tokens | Attempts | Retry | Retry cause | Accepted as playable narration | Prior relevant behavior | Assessment |
| ----- | -------- | -----------: | ------------: | -------: | ----- | ----------- | ------------------------------ | ----------------------- | ---------- |
| P1 | structured_realization | 45563 | 576 | 2 | Yes | unauthorized causal / certainty narration | No. Observation fallback only. | PR-BV also retried. First input 22084 both times. Prior retry was accepted but sterile. | P1-A. Not a PR-BW regression. |
| P2 | narration_only | 48294 | 209 | 2 | Yes | narration reject, then retry reintroduced declarations | No. Safe-nonresolution fallback. | PR-BV structured retry after an unauthorized `realize` declaration. Retry input about 26142. Final narration was usable. | Targeted declaration pathology absent. Retry contract unreliable. |
| P3 | structured_realization | 45517 | 800 | 2 | Yes | hypothesis discussion treated as narrator lead | No. Observation fallback only. Hypothesis record stayed a hypothesis. | PR-BV first pass accepted. First input 22108 both times. | Not a PR-BW regression. Later P3 slice may still be warranted. |

### P2 before / after

| | Envelope | Attempts | Retry input tokens | What the retry did |
| --- | --- | ---: | ---: | --- |
| PRE-PR-BW P2 | structured realization | 2 | 26142 | First response declared the reply as an unauthorized authored world fact. Retry discovered `declared_claims: []` and was accepted. |
| POST-PR-BW P2 | narration-only | 2 | 24881 | First response had no declaration channel and declaration validation passed. Retry feedback demanded `declared_claims`. Second response was rejected. Turn was not accepted as dialogue. |

The structural pathology targeted by PR-BW — ordinary dialogue forced through an unauthorized structured declaration, then a full retry to discover empty claims — did not appear. A different retry still occurred, and this single sample does not establish a cost saving.

## What a bounded repair would be

Not done in this cycle.

When the selected contract is narration-only, regeneration feedback for every rejection reason, including `unauthorized_resolution_decision_fact`, must keep `{"narration": "player-facing response"}` and must not attach `structured_envelope_schema` or tell the model to emit `declared_claims`.

Do not redesign `gm_resolution_decision`. Do not change the selector. Do not move P1, P3, or consequential realization onto narration-only. Do not weaken structured declaration validation. Do not treat the narration-validator hit on the baker's sentence as license for a general validator rewrite inside this gate.
