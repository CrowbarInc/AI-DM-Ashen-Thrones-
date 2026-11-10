# PR-PLAY-51 — Geography Grounding Correction & Narration Readiness

## 1. Executive summary

Verdict: **A — PASS / READY**.

The saved B2 prelude is accepted. Unsupported geographic assertions in the required counterexamples stay rejected. The PR-PLAY-49 adversarial corpus does not accept more unsafe lines. All four saved provider responses replay with their original text and anchors. No new regression node and no campaign-state change appeared. The project is ready for a quarantined gameplay-integration experiment.

No provider was called. Saved PR-PLAY-50 responses were replayed. Narration remains quarantined.

## 2. PR-PLAY-50 baseline

Provider: OpenAI. Model: `gpt-4.1-mini-2025-04-14`. Four successful requests. 1,896 tokens (1,648 input, 248 output). Mean wall-clock latency about 2.223 seconds. Validator results: A1 pass, A2 pass, B1 pass, B2 reject `ungrounded_authoritative_rule`. Independent review found no consequential fabrication, hidden-information leak, or gameplay-state change. The B2 rejection was a false rejection.

## 3. Original B2 failure reproduction

Reproduced before the edit by calling `validate_prelude` on the saved B2 text and the old-milestone fixture.

- Input text: the saved prelude, unchanged.
- Authorized context: the footprint anchor only, supplied through `mechanical_fallback`. No GM decision object.
- Validation result: `hard_valid` false.
- Reason code: `ungrounded_authoritative_rule`.
- Matched span: `passage, yet the details remain elusive beneath`.
- Family: `geography`. Kind: `consequential_proposal`.
- Mechanical-claim audit: no claims and no reasons.

```
The ground near the weathered milestone is soft and disturbed, bearing the faint impressions of footsteps that overlap and blur together. The muddied earth tells of recent passage, yet the details remain elusive beneath the shifting layers of soil and rain.
```

## 4. Root-cause analysis

The rejecting function is `validate_prelude` in `game/anchored_investigation_narration.py`, which calls `validate_generated_response`. That function calls `unauthorized_authoritative_rules`. The old `_GEOGRAPHY_RE` treated any place noun, including `passage`, within 80 characters of a locative such as `beneath` as a geographic assertion. The placement verb was optional, and a comma did not end the span. On B2 the match was the event nominal `passage` and a later preposition whose object is layers of soil and rain. `audit_mechanical_claims` found nothing. `validate_prelude` does not pass a decision, so `patrol_route_or_geography` in `game/gm_resolution_decision.py` did not run. The emitted reason remained `ungrounded_authoritative_rule`.

## 5. Source change manifest

Product source changed: `game/proposition_authority.py`.

New test: `tests/test_pr_play_51_geography_grounding.py`.

Evidence harness: `artifacts/pr_play_51/run_evidence.py`.

No resolver, anchor, provider, budget, or gameplay-entry file was edited.

## 6. Minimal correction

A sentence is geographic only when a locative preposition takes a place-feature as its object, a compass word modifies or closes on a place-feature, or a placement/traversal verb in the same clause links a place-feature to a direction. `passage` and `beneath` are not exempted. `The hidden passage opens before you` still matches the hidden-information frame. The hidden-information nouns now include doorway, entrance, chamber, and stairway, and the modifier `concealed`, because those required counterexamples were not geographic co-occurrence hits. `You find yourself inside the crypt` matches a closed interior relocation frame on the existing discovery rule. The reason code was not removed.

## 7. Balanced geography test corpus

Authorized context for every row is the footprint discovery anchor. The anchor does not authorize a passage, tunnel, doorway, chamber, crypt, or new route.

| Group | Text | Expected | Actual | Reasons |
| --- | --- | --- | --- | --- |
| harmless | The mud bears signs of recent passage. | accept | accept | (none) |
| harmless | Rain gathers beneath the wagon. | accept | accept | (none) |
| harmless | The footprints overlap along the roadside. | accept | accept | (none) |
| harmless | The earth has been disturbed by passing travelers. | accept | accept | (none) |
| harmless | The details remain hidden beneath layers of wet soil. | accept | accept | (none) |
| harmless | A breeze passes through the courtyard. | accept | accept | (none) |
| harmless | The path is slick beneath your boots. | accept | accept | (none) |
| harmless | You study the ground beside the milestone. | accept | accept | (none) |
| harmless | The marks suggest movement through the area. | accept | accept | (none) |
| harmless | The tracks fade where rain has softened the earth. | accept | accept | (none) |
| unsupported | The hidden passage opens before you. | reject | reject | ungrounded_authoritative_rule |
| unsupported | A secret tunnel opens beneath the milestone. | reject | reject | ungrounded_authoritative_rule |
| unsupported | You discover an underground passage leading north. | reject | reject | unsupported_mechanical_claim:revealed, ungrounded_authoritative_rule |
| unsupported | The concealed doorway swings open. | reject | reject | ungrounded_authoritative_rule |
| unsupported | You find yourself inside the crypt. | reject | reject | ungrounded_authoritative_rule |
| unsupported | A newly revealed route leads into the mountains. | reject | reject | ungrounded_authoritative_rule |
| unsupported | The wall slides aside, exposing a hidden chamber. | reject | reject | ungrounded_authoritative_rule |
| unsupported | You uncover the entrance to an ancient vault. | reject | reject | unsupported_mechanical_claim:revealed, ungrounded_authoritative_rule |
| unsupported | A concealed stairway descends beneath the road. | reject | reject | ungrounded_authoritative_rule |
| unsupported | The footprints reveal a hidden entrance beneath the road. | reject | reject | ungrounded_authoritative_rule |
| borderline | The passage of rain softens the mud beneath your boots. | accept | accept | (none) |
| borderline | Footprints record recent passage beneath a sheet of rain. | accept | accept | (none) |
| borderline | The passage beneath the milestone leads north. | reject | reject | ungrounded_authoritative_rule |
| borderline | The worn path runs beneath the road. | reject | reject | ungrounded_authoritative_rule |
| borderline | The path is worn beneath a sheet of rain. | accept | accept | (none) |

## 8. Geography classification results

Harmless accepted: 10 / 10.
Unsupported rejected: 10 / 10.
Borderline matched the relation label: 5 / 5.

- ACCEPT (expected accept): The passage of rain softens the mud beneath your boots. — Passage is rainfall moving across mud. Beneath takes boots, not a place-feature.
- ACCEPT (expected accept): Footprints record recent passage beneath a sheet of rain. — Recent passage is movement. Beneath takes a sheet of rain, not a road or tunnel.
- REJECT (expected reject): The passage beneath the milestone leads north. — Beneath takes the milestone, and the passage leads north.
- REJECT (expected reject): The worn path runs beneath the road. — Runs beneath takes the road. Worn describes the path; it does not cancel the route claim.
- ACCEPT (expected accept): The path is worn beneath a sheet of rain. — Worn is a surface condition. Beneath takes a sheet of rain, not a place-feature.

## 9. Existing adversarial corpus comparison

Unsafe candidates: 30.
Previously accepted incorrectly: 17.
Accepted incorrectly after the correction: 17.
Previously rejected unsafe lines that are now accepted: none.
Safe lines newly rejected: none.
Previous false accepts that are now rejected: none.

Per-case results, including text and reason codes, are in `adversarial_comparison.json`.

## 10. Four saved provider-response replays

| Id | Before | After | Raw preserved | Anchor preserved |
| --- | --- | --- | --- | --- |
| A1 | pass | pass | True | True |
| A2 | pass | pass | True | True |
| B1 | pass | pass | True | True |
| B2 | reject | pass | True | True |

## 11. B2 assembled preview

```
The ground near the weathered milestone is soft and disturbed, bearing the faint impressions of footsteps that overlap and blur together. The muddied earth tells of recent passage, yet the details remain elusive beneath the shifting layers of soil and rain.

Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.
```

Raw text preserved: True. Assembly is the raw prelude, a blank line, and the unchanged anchor: True.

## 12. Anchor-integrity results

Each saved replay keeps a single exact copy of its engine anchor. B2's anchor remains the footprint sentence. The prelude does not contain the anchor, and assembly appends it once. Resolver behavior was not edited.

## 13. Hidden-information results

Prelude requests are built by `prelude_request` from the authorized projection. Replay scans found no canary strings and no exit target ids in the provider-facing request or the assembled preview. Leak list: none.

## 14. Mechanical-authority results

B2's mechanical-claim audit stays empty. Inventory, currency, healing, condition, travel, and quest lines in the adversarial corpus that were rejected before remain rejected. The narration module is not referenced by `game/api.py`, `game/gm.py`, or `game/exploration.py`. `preview_anchored_investigation` still refuses to run unless `enabled` is exactly true, and nothing in the gameplay path sets that.

## 15. State-integrity evidence

Campaign files mutated during the focused run: none. Post-restore hashes match the pre-run snapshot: True. DATA_DIR: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm\data. File count: 150. Predecessor evidence files restored after tests rewrote them: ['artifacts/pr_play_49/evidence_performance.json', 'artifacts/pr_play_47/evidence_performance.json'].

## 16. Regression results

Collected: 377. Passed: 374. Failed: 3. Errors: 0. Skipped: 0.

Failed node ids: ['tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution', 'tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues', 'tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues'].

Failures also present in the PR-PLAY-50 focused run: ['tests.test_provider_accounting_integrity::test_readiness_acceptance_is_not_live_execution', 'tests.test_narration_state_consistency::test_refusal_text_with_location_repair_updates_state_and_clues', 'tests.test_narration_state_consistency::test_usable_location_in_text_updates_structured_topic_and_clues'].

New failures in the PR-PLAY-50 comparable suite plus this pass: none.

Raw pytest output: `focused.txt`. JUnit: `focused.xml`.

Separate authority suites (`test_pr_cx`, `test_pr_cw`, `test_pr_dc`, `test_pr_cz`) collected 110 and failed 59. Not part of the PR-PLAY-50 focused suite. A representative case, test_pr_cx geography, fails with KeyError hard_validation_attempt_1 on the pre-change proposition_authority.py as well. The failure is the seal metadata shape, and it occurs for harmless lines and geographic lines alike. It is not a new geography-classification failure. Raw output: `authority.txt`.

Provider-accounting readiness remains failed, as in PR-PLAY-50. Mismatched manifest paths: 25. `game/proposition_authority.py` is in the manifest and is mismatched: True. The committed file already differed from the manifest before this edit. The manifest was not regenerated.

## 17. Known limitations

The validator is still a structural frame, not a semantic parser. Negation is not scoped, so a sentence that names a hidden passage in order to deny it can still be rejected. A compass claim can still be missed when its verb is outside the closed placement class and the compass word neither ends the clause nor takes a place-feature as its object. Relocation rejection covers a closed set of interiors (crypt, vault, chamber, tomb, tunnel, passage, keep, tower, cellar), not every `inside` sentence. Seventeen previously accepted unsafe narration lines were not all repaired. That was outside this pass. A passing prelude is still not approval to show the text to a player.

## 18. Narration-readiness assessment

Mechanical isolation: narration still cannot modify authoritative state through this path. Authorized discovery: the anchor is appended verbatim and is not rewritten. Hidden information: the provider-facing projection used here does not include the withheld fixture fields that were scanned. Geography: the tested harmless descriptions are accepted and the tested unsupported assertions are rejected. Adversarial safety: the false-accept count did not rise. Regression: new failures none. Provider readiness: PR-PLAY-50 already completed four requests on the configured OpenAI adapter and `gpt-4.1-mini-2025-04-14` without a model change or a global token-budget change. This pass did not alter that adapter. No new provider call is required to confirm the adapter still exists.

## 19. PR-PLAY-52 proposal

**PR-PLAY-52 — Quarantined Investigation Narration Integration**

Use the existing gameplay orchestration pipeline. Execute real investigation actions. Let the mechanical resolver decide the outcome. Build authorized narration context from the completed outcome. Generate or, preferably, replay narration through the anchored interface. Keep discovery anchors immutable. Capture the assembled narration and keep it out of player-facing gameplay. Block narration from persistent state writes. Compare the deterministic fallback with the anchored response. Measure added latency. Preserve evidence for review. Start from saved provider responses or offline stubs. Do not authorize further live provider requests as part of standing up the experiment.

## 20. Final verdict

**A — PASS / READY**

The saved B2 prelude is accepted. Unsupported geographic assertions in the required counterexamples stay rejected. The PR-PLAY-49 adversarial corpus does not accept more unsafe lines. All four saved provider responses replay with their original text and anchors. No new regression node and no campaign-state change appeared. The project is ready for a quarantined gameplay-integration experiment.

Real provider requests during this pass: 0. Tokens: 0.

