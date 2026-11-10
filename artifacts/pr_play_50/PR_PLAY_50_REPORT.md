# PR-PLAY-50 — Quarantined Real-Provider Narration Experiment

## 1. Executive summary

**B — PARTIAL / CONDITIONAL.** The configured model can write short investigation preludes that are more atmospheric than the deterministic host line, without changing campaign state and without revealing the withheld gate secrets. That is not approval to show the prose to a player.

Four real provider requests completed. All four returned finished text from `gpt-4.1-mini-2025-04-14`. None was written into a campaign, inventory, quest, scene, or player-facing response. An earlier local harness mistake never reached the provider and is preserved separately.

Independent review found no consequential fabrication and no hidden-information leak. The notice-board samples are the strongest. The footprint samples paraphrase the engine's discovery and add little structure beyond it. The existing validator accepted three preludes and false-rejected the fourth: it read "passage" plus "beneath" as an ungrounded route. Because a pass still must not authorize display, and because that false rejection would throw away usable prose, the next step is one offline grounding correction. It is not a live narration hook.

## 2. PR-PLAY-49 baseline

PR-PLAY-49 built an offline anchored investigation preview. Eight fixtures kept their authorized discoveries. Ten authored preludes, not model output, scored a provisional mean of 13.9/16 against host 10.0 and controlled renderer 10.2. The existing validator accepted 17 of 30 unsafe candidates. This experiment therefore judged the model text by reading it, and treated the validator as a measurement rather than a permit.

No game module was edited in this pass. The provider path reused `game.expressive_dialogue.request_expression`, which already performs one plain-text completion, accounts the call, and does not apply the text to dialogue unless a separate adopt function is called. That adopt function was instrumented and was not called.

## 3. Experiment configuration

| Setting | Value |
|---|---|
| Provider | OpenAI, through the existing expression adapter |
| Configured model | `gpt-4.1-mini` |
| Returned model | `gpt-4.1-mini-2025-04-14` |
| Temperature | 0.2, the adapter constant, same for every request |
| Output cap | 80 tokens, the adapter constant |
| Timeout | 45 seconds |
| SDK retries | 0 |
| Host retries | disabled |
| Requests planned | 4 |
| Provider HTTP requests | 4 |
| Successful text responses | 4 |
| Campaign session | none |

Token ceilings were the existing code defaults once a four-request process cap was set: 8,000 input, 2,000 output, 10,000 total. Those ceilings were not raised. Estimated input was about 493 tokens per request, so four requests fit before any call was sent.

A first dispatch failed inside the evidence wrapper: it called `Responses.responses.create` instead of `Responses.create`. The exception was `AttributeError`, the ledger latency was 0.065 ms, and the request id was null. No provider response existed. Accounting then refused the other three local attempts. Those files are in `local_harness_failure/`. The wrapper was corrected and the four planned requests were sent once. That was not a retry of a provider error.

## 4. Isolation preflight

Before the successful dispatch, the saved resolutions were projected with `authorize_anchored_investigation` and `prelude_request`. The rebuilt requests matched the PR-PLAY-49 prelude requests exactly. Hostile canaries and the scene's withheld strings were absent from the provider message. Fourteen notice-board strings and nine footprint strings were checked.

Twenty-six state-changing functions were wrapped so a call would raise. None fired. The projection step invoked no exploration resolver. One hundred fifty files under the live data directory, and the `.env` file hash, were unchanged. Provider-call disable was not set, so the configured service was available. Isolation passed. No provider call was made during preflight.

## 5. Authorized provider context

The model received only:

- The player's public action.
- The prelude length target, about 20–60 words.
- The PR-PLAY-49 allowlist: target, status, success, newly discovered text, previously known text, public visible-fact observations, descriptive constraints, and the 1,600-byte output bound.

It did not receive the scene file, exits, hidden facts, GM notes, clue identifiers, resolver hints, world state, or credentials.

Notice board action: "I examine the notice board."

Authorized discovery: "The missing patrol was last seen taking the northwest mud track past the crates."

Footprints action: "I examine the footprints."

Authorized discovery: "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear."

## 6. Prompt contract

The same system prompt was used for all four requests:

> The investigation is already complete. Its mechanical result is authoritative. Write one descriptive prelude of about 20 to 60 words, and end on a complete sentence. You are writing prose only. Do not decide the outcome. Do not invent rewards, possessions, currency, health, conditions, travel, quests, or any other mechanical change. Do not invent definitive conclusions, culprits, counts, links, or destinations. Preserve uncertainty that the result leaves open. Do not reveal information that is absent from the supplied context. Harmless incidental atmosphere is allowed and creates no new facts or mechanics. Avoid generic filler. Do not repeat the authorized discovery; the engine appends that sentence separately.

No earlier sample was included in a later request. The prompt was not revised after the results.

## 7–10. Requests, raw responses, usage, and latency

| Request | Investigation | HTTP | Input | Output | Total | Wall clock | SDK dispatch | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| A1 | Notice board | yes | 421 | 78 | 499 | 3212.535 ms | 2661.178 ms | completed |
| A2 | Notice board | yes | 421 | 71 | 492 | 1800.050 ms | 1352.944 ms | completed |
| B1 | Footprints | yes | 403 | 51 | 454 | 1735.375 ms | 1243.251 ms | completed |
| B2 | Footprints | yes | 403 | 48 | 451 | 2143.352 ms | 1483.209 ms | completed |

Wall clock is the adapter timer around client construction and the response. SDK dispatch is the accounting timer around the create call. The first call is the slow outlier on both clocks. None was truncated: every response status was `completed`, and A1 used 78 of 80 output tokens.

Totals: **1,648 input, 248 output, 1,896 provider tokens.** Mean tokens per request: 474.

Wall-clock mean **2222.828 ms**, median **1971.701 ms**, minimum **1735.375 ms**, maximum **3212.535 ms**.

SDK-dispatch mean **1685.146 ms**, median **1418.077 ms**, minimum **1243.251 ms**, maximum **2661.178 ms**.

Provider pricing is not present in the configuration or usage records. No monetary cost is estimated.

PR-PLAY-49's character estimate for one bare projection was about 280 input tokens and 31 output tokens. Measured input was 403–421 because the fixed system prompt and player action were added. Measured output was 48–78 because the model wrote full paragraphs, near the 80-token cap. PR-PLAY-43 spent 39,804 measured tokens across five interpretation requests and made no gameplay narration call. These four narration requests are much smaller than that five-turn total. They would be an additional wait of roughly 1.2–3.2 seconds, not a replacement for interpretation. Four samples do not show that every future call will be this fast.

Raw response objects, request ids, and the usage ledger are in `requests.json`, `dispatch_summary.json`, and `provider_ledger.jsonl`.

## 11. Quarantined assembled previews

The engine anchor is appended only after validation. These previews were not sent to a player.

**A1, validator pass.**

> The notice board stands weathered and crowded, its surface plastered with official decrees and hastily scrawled warnings. Nearby, the murmur of the gate serjeant and the clatter of the tavern runner’s calls mingle with the restless shifting of watchers and refugees. The board’s messages draw a wary crowd, each line hinting at unease and unanswered questions.
>
> The missing patrol was last seen taking the northwest mud track past the crates.

**A2, validator pass.**

> The notice board stands weathered and worn, its surface crowded with official decrees and hastily scrawled warnings. Nearby, the murmur of the gate serjeant and the clatter of the tavern runner’s trade blend with the restless shifting of watchers and refugees. The board’s messages seem to pulse with urgency, inviting closer scrutiny.
>
> The missing patrol was last seen taking the northwest mud track past the crates.

**B1, validator pass.**

> The damp earth near the leaning milestone bears the faint impression of footsteps, their edges softened by recent rain. The muddied ground tells a story of passage, yet the details remain elusive, leaving the trail’s origin and direction shrouded in uncertainty.
>
> Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

**B2, validator false rejection, deterministic fallback kept.** The raw prelude is preserved and was not assembled:

> The ground near the weathered milestone is soft and disturbed, bearing the faint impressions of footsteps that overlap and blur together. The muddied earth tells of recent passage, yet the details remain elusive beneath the shifting layers of soil and rain.

The quarantined preview actually retained is the existing fallback, and the anchor is still exact:

> You examine the evidence. Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear. A weathered stone milestone leans beside the northwest mud track. The mud around the marker is churned with faint overlapping prints that fade into the scrub. The track continues a short way past the stone before rainwater and brush make the next step unclear.

Every anchor appears once. No preview was approved for display.

## 12. Independent narrative review

Review was written before the validator ran. Mechanical correctness is separate from the quality score.

**A1.** No item, coin, injury, condition, journey, or quest. The serjeant, runner, watchers, and refugees are public. "Weathered" and "hastily scrawled" are incidental texture. The northwest track is not guessed early. Withheld material does not appear: the noble-house watcher, the Ash Cowl contact, the checkpoint signal, and the paid face list. "Watchers" is the public observation, not that motive. The last sentence is generic unease, so the anchor arrives as a new fact. 56 words.

**A2.** Same safety result. "Trade" matches the public runner more closely than A1's "calls." "Seem to pulse" is hedged. "Inviting closer scrutiny" gives the anchor a place to land. 52 words.

**B1.** No count, owner, or patrol link. Rain and the leaning stone match the public scene. The second sentence already says the origin and direction are uncertain, so the anchor repeats the finding. "Tells a story of passage" only restates that prints mean someone passed. 41 words.

**B2.** Overlap and the weathered stone match authorized facts. "Recent" is slightly sharper than the unstated timing. Uncertainty stays open, but less precisely than the anchor. No patrol identity. 41 words. "Beneath the shifting layers of soil" is mud texture, not a tunnel.

## 13. Narrative-quality scores

Scale: 0 absent or strongly weak, 1 adequate or limited, 2 complete or strong. Expressive range scores this four-sample corpus, not one sentence's uniqueness. These scores are for the provider prelude plus the exact anchor, including B2's raw prelude. They are not a reliability rate.

| Sample | Info | Mech | Natural | Range | Atmosphere | Clarity | Repetition | Cohesion | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1 | 2 | 2 | 2 | 1 | 2 | 2 | 1 | 1 | 13 |
| A2 | 2 | 2 | 2 | 1 | 2 | 2 | 2 | 2 | 15 |
| B1 | 2 | 2 | 1 | 1 | 1 | 2 | 0 | 1 | 10 |
| B2 raw | 2 | 2 | 1 | 1 | 1 | 2 | 1 | 1 | 11 |

Mean **12.25/16**. Mechanical mean **2/2**. Narrative-only mean **10.25/12**.

PR-PLAY-49, same notice-board outcome, different texts: host 10.0, controlled renderer 10.2, authored anchored examples 13.9. The two notice-board model samples sit with the authored examples. The footprint samples sit with the host and controlled band because they spend the paragraph restating the clue. B2's retained engine preview is the deterministic fallback, so its expressive score does not survive the current validator.

No consequential fabrication is being hidden inside the higher notice-board scores.

## 14. Validator results

| Sample | Decision | Reasons | Unsupported mechanical claims | Hidden-information hits | Fallback |
|---|---|---|---|---|---|
| A1 | pass | none | none | none | not used |
| A2 | pass | none | none | none | not used |
| B1 | pass | none | none | none | not used |
| B2 | reject | `ungrounded_authoritative_rule` | none | none | used |

The validator was not modified. No phrase list was added. No request was repeated to change this outcome.

## 15. Validator disagreement

| Class | Count | Samples |
|---|---:|---|
| Correct acceptance | 3 | A1, A2, B1 |
| Correct rejection | 0 | |
| False acceptance | 0 | |
| False rejection | 1 | B2 |

B2's second sentence is "The muddied earth tells of recent passage, yet the details remain elusive beneath the shifting layers of soil and rain." The geography rule matches `passage` and then `beneath`, and treats the sentence as a route lying under something. The tokens are not all in the clue sentence, so the rule is marked ungrounded. B1 also says "passage" but does not say "beneath," so the same rule does not fire. Independent review does not find a route, vault, or destination in B2.

This agrees with PR-PLAY-49's warning in the other direction too: three passes included B1, which paraphrases the discovery heavily. The validator did not notice that paraphrase. A pass remains a heuristic, not permission to display.

## 16. Expressive variety

A1 and A2 share one three-sentence plan and a lot of wording: weathered board, official decrees, hastily scrawled warnings, the serjeant's murmur, and the restless watchers and refugees. Only the closing clause really changes. That is one rhetorical family.

B1 and B2 share a two-sentence plan: describe the mud, then say the details are elusive. B1 names rain-softened edges and origin and direction. B2 names overlap, blur, and soil. The cadence still matches.

With two samples per investigation, this is preliminary. The fixed temperature of 0.2 is a plausible cause. It was not changed between calls, because the experiment forbade tuning for variety. Shared words such as "notice board" and "milestone" are not the problem. The sentence plans are.

## 17. State integrity

After the four provider calls: campaign files unchanged (150 files), `.env` hash unchanged, sink-call list empty. No inventory, currency, condition, travel, quest, scene, world, lead, or incidental-detail write occurred. No player-facing response was emitted. The same campaign snapshot still matched after the offline regression. Two predecessor performance-evidence files were rewritten by tests and restored.

The experiment did not fail the integrity gate.

## 18. Regression

Focused offline pytest, provider calls disabled, no live request:

| Collected | Passed | Failed | Errors | Skipped |
|---:|---:|---:|---:|---:|
| 316 | 313 | 3 | 0 | 0 |

The two narration-state failures are the PR-PLAY-49 pre-existing failures. The accounting readiness failure is older manifest drift across the game package, including modules this pass did not edit. The manifest was not regenerated and the failure was not suppressed. No new failure was introduced by the experiment harness. PR-PLAY-49's anchored tests passed.

## 19. Known limitations

- Four samples cannot support a model reliability rate.
- Temperature 0.2 produced near-duplicate plans. Variety is unproven.
- Footprint preludes paraphrase the anchor even though the prompt says not to repeat it.
- Incidental words such as "weathered," "hastily scrawled," and "recent" are not new mechanical facts, and they are also not authorized canon.
- The validator still misses paraphrase and can false-reject atmosphere. PR-PLAY-49's 17 unsafe passes were not re-litigated here and are not cured.
- The 80-token expression cap is tight. A1 used 78 tokens. A longer prelude would truncate, and this experiment would not have retried it.
- The first harness attempt was a local defect. It did not create a fifth provider call.
- Monetary price is unknown because the repository has no pricing table.
- Public authoring still decides what the projection treats as visible. The allowlist cannot repair a secret that was mislabeled public.

## 20. Decision

**CONDITIONAL — one narrow correction before any integration prototype.**

Why not NO-GO: isolation held, anchors stayed exact, withheld secrets stayed out of the prompt and the prose, and the notice-board narration is visibly better than "You inspect notice board." Latency and token use are small enough for another offline test.

Why not GO: wiring this in now would let `ungrounded_authoritative_rule` replace some of that prose with the deterministic fallback, as it did for B2. The integration would then be scored on the fallback. The validator also still cannot be the authority that releases text.

## 21. Recommended PR-PLAY-51 scope

One offline correction. No player-facing narration, no new provider request, no budget change, no phrase-list expansion, and no campaign edit.

Acceptance:

1. The preserved B2 prelude no longer fails `validate_prelude` with `ungrounded_authoritative_rule`.
2. Its assembled preview keeps the raw prelude and the footprint anchor exactly once.
3. The existing unsafe sentence "The hidden passage opens before you." still fails validation.
4. On the PR-PLAY-49 30-case unsafe corpus, the number of heuristic passes does not rise above 17.
5. `tests/test_pr_play_49_anchored_narration.py` still passes.
6. The correction is covered by a regression fixture that uses the preserved B2 sentence. Do not weaken hidden-route detection in order to clear the word "beneath."

The likely defect is the geography rule treating "passage … beneath" as a place relation, not a missing public fact. Adding the public observations to the corpus alone does not clear B2, because words such as "beneath," "shifting," and "soil" are not in those observations.

Do not start that correction in this pass.

## 22. Final verdict

**B — PARTIAL / CONDITIONAL.**

The quarantined experiment obtained four genuine provider preludes, measured their tokens and latency, kept the anchors, and kept them out of the campaign. The model can narrate the notice board with real atmosphere and without the tested secrets. The footprint narration is weaker, and the current validator both missed a paraphrase and rejected a safe sentence. Fix that bounded grounding misfire offline before any integration prototype. Do not enable live narration.
