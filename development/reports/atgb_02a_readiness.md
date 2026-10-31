# ATGB-02A — Baseline readiness and reproducibility

Date: 2026-10-18. Scope: benchmark initialization and preflight only.
No live baseline, provider evaluation, production gameplay change or performance score.

The machine-verifiable starting prerequisites for all ten scenarios are available
from the frozen `frontier-gate-v1` baseline. Readiness for a controlled baseline is
conditional on review. Narrative response behavior remains unverified.

## Baseline findings

ATGB-02 copied `data/campaign.json`, `character.json`, `conditions.json`, `world.json`
and every scene template from the working campaign, then invoked the existing hard
reset. This isolates writes but does not reconstruct authored content changed by
play. Reset preserves authored NPC topics and scenes by design. Fixture metadata
never established these facts in the world.

An isolated copy/reset probe of the legacy working source found `frontier_gate`,
zero transcript entries and all three required NPC topics at this point in time
(`artifacts/atgb/atgb_02a/legacy_reset_findings.json`). This is a snapshot observation,
not a stable source contract. Production defaults alone are also insufficient:
their guard/runner topics differ and they omit the serjeant and notice-board clue.

The existing versioned `tests/helpers/golden_replay_fixtures.py` function
`seed_frontier_gate_world` authors precisely the catalog's scene and three topic
owners. A benchmark-only JSON snapshot freezes its output. Campaign, character,
conditions and the two exit scenes come from the existing `game/defaults.py`
factories. No new facts, runtime initialization owner or gameplay subsystem was
introduced. The replay fixture's session assignment is omitted: the existing hard
reset already owns the same starting location and fresh runtime.

Baseline: `data/validation/atgb/baselines/frontier-gate-v1/manifest.json`.
The manifest records the source revision and exact source-file hashes because the
worktree is dirty; HEAD alone does not describe those bytes. The loader pins its
SHA-256, schema, version and seven-file inventory. Files are checked before copying,
after copying, and before importing storage. Missing or incompatible data is refused;
there is no fallback to defaults, canonical data or an alternate campaign.
Frozen baseline files are reviewable repository inputs and must be retained/versioned
with the harness. Runtime does not regenerate them from changing test helpers.

## Scenario readiness matrix

All rows share verified initialized prerequisites: isolated directory bound before
game import/reset; `frontier_gate`; authored visible/hidden facts and exits; no
selected interlocutor; no discovered clues; empty transcript/chat history, fresh
combat and no prior scene/social runtime. The actual reset state is inspected.
No scenario is initialized with another scenario's conversation or with a revealed clue.

| Scenario | Verified in initialized state | Established through its own dialogue | Unverified or unsupported | Starting readiness |
| --- | --- | --- | --- | --- |
| S01 | Public scene facts, runner offer, distinct `guard_captain` addressable and `gate_guard` world owner of `watch_command` | Observation, watch question, stew remark, disengagement | Correct speaker/clarification and relevance; price/quality are unauthored | Verified machine prerequisites |
| S02 | Unread `notice_board` interactable → `notice_patrol_route`, exact track clue; no curfew hours | Board investigation, time question, correction, recall | Whether investigation actually reveals the clue and recall occurs | Verified machine prerequisites |
| S03 | Runner at gate, only footprint-hearsay topic; notice clue separately owned | Runner selection, rumor, source question, repeat commitment; player introduces notice wording in S03.4 | A delivered promise/source distinction; source name, price and second secret unauthored | Verified machine prerequisites |
| S04 | Serjeant location/aliases and `route_change`; visible census choke; Thoran topic belongs to guard | Selection/correction, wagon question, follow-up | Correct relevance and causal restraint; issuer and private awareness unauthored | Verified machine prerequisites |
| S05 | Separate runner rumor and board clue, neither already delivered | Runner account, reading board, ambiguous reference, addressee correction | Both accounts must actually be delivered before comparing; failed delivery must remain visible | Verified machine prerequisites |
| S06 | Runner/offer/topic, fresh inventory and scene; no price | Explicit OOC/IC switches and runner address | Mode-specific answer quality and non-purchase behavior; purchase system not required | Verified machine prerequisites |
| S07 | Rain/banners in opening seeds, queue and runner offer; no prior patrol question | Small talk, initiative and offer question | Opening delivery is not exercised by silent reset; naturalness and initiative unverified; no mood/time system required | Partially verified (opening context delivery) |
| S08 | Same visible scene and serjeant topic, fresh independent store | Question-shaped observation, correction to people, crowd-handler address, conditional route attribution | If S08.3 never says route, S08.4 must not manufacture that history; issuer unauthored | Verified machine prerequisites |
| S09 | `refugee` and `threadbare_watcher` scene addressables; no world topics; posture cues in opening/journal seeds | Two-way ambiguity then selected watcher and pending identity question | Delivery of posture context not exercised; clarification/identity response unverified; no crowd engine required | Partially verified (opening context delivery) |
| S10 | Barrel/offer in visible facts, runner hearsay; barrel has no clue interactable | Thing/offer clarification and reference to non-food half | Pending referent continuity unverified; no barrel knowledge or travel required | Verified machine prerequisites |

Blocked scenarios in the selected intact baseline: **none**. Any failed machine
prerequisite blocks execution before chat and stops the run; subsequent scenarios
are not attempted. A missing setup condition is never scored as a conversational
failure. The former unpinned source was a reproducibility limitation for every row,
even when its facts happened to match.

Verified readiness means only that the machine prerequisites exist. The two
partially verified rows distinguish authored context availability from delivery.
Every row still has unverified narrative assumptions: interpretation, response
relevance, ambiguity/continuity handling, secrecy and preservation of grounded
uncertainty require a later authorized live transcript and human judgment.

## Preflight and minimal corrections

`tools/atgb/baseline.py` validates the frozen input. Isolation still rejects canonical,
active-player, ancestor, occupied and reused stores. `source_data_dir` can no longer
select working campaign files. Disposable directories now live under
`development/tmp/` because Windows sandbox temporary paths denied atomic rename.
Production reset/storage behavior is unchanged.

`tools/atgb/preflight.py` reads reset state, checks storage binding and baseline marker,
expected location and scene presence, authored scene/bootstrap content and world
projection, individual NPC locations/topics, and the existing fresh-runtime validator.
Load-time dictionary defaults may add keys; authored values/lists must match.
It separately reports unverified conditions. It does not rewrite state or assess
dialogue. The worker refuses failed prerequisites before submitting any turn.
Result JSON and Markdown expose these failures separately from performance scoring.

`--mode provider_disabled_host --preflight-only` resets and inspects all selected
scenarios with providers disabled and zero chat turns. Normal host/live paths
automatically preflight. Simulated mode remains infrastructure-only and does not
claim runtime readiness. Each result identifies the baseline version/digest.

The ATGB-01 design and catalog now have explicit S07 supersession notes. Historical
partition tables and player lines remain intact. ATGB-02 and the machine corpus
remain execution authority: 25 visible / 4 related / 8 held-out turns. Held-out
content was inspected here only for initialization; it remains previously exposed.

## Validation

Results and exact commands are recorded under `artifacts/atgb/atgb_02a/`.
The focused readiness/infrastructure checks cover all 37 fixture turns, two complete
initialization passes, unsafe directories, incompatible/missing source files,
missing NPC/topic/history/location/binding, preflight failure with zero chat turns,
unchanged canonical data, ordered simulated requests and existing host infrastructure.
The preflight artifact records all ten scenario checks and normalized state digests.
Random session/run ids and save timestamps are excluded from equivalent-state comparison.

Final focused result: **24 passed** (`final_focused.xml`), including the existing
four-turn S06 host-chat regression with providers disabled. Adjacent result:
**49 passed** (`adjacent.xml`) across playability evaluator, review-handoff and
validation-evidence-standard tests. Two complete resets of all ten scenarios
produced the same normalized starting-state digest:
`c12cb0dfe6a31980b4ecc00a59cc359a143a76452e517a36ad76753a6145561a`.

Earlier attempts are retained separately: sandbox temporary-path rename failures;
then a sandbox host-chat timeout in Windows asyncio `socketpair` initialization
(diagnostic stack in `host_diagnostic.txt`); then an isolated intermittent atomic
rename denial in one reset of the first authorized host run. The final authorized
provider-disabled rerun passed all 24 checks. No production I/O or event-loop
workaround was added. Those tooling/environment failures are not gameplay scores.
No provider-disabled response is scored as gameplay performance. Full suite and
live-provider evaluation are not run.

## Limits and handoff

This is a benchmark instrument readiness correction, not a gameplay repair or a
claim of related/independent conversational generalization. The primary defect
class is evaluation: an unpinned working save could change the evaluation setup.
The earliest incorrect choice was the bootstrap source, before any conversational
turn. The correction belongs in benchmark data/tooling, not production gameplay.

The frozen world is the existing replay environment, not every working campaign
scene. Baseline changes require review and a version/pin change. Authored context
does not guarantee prompt delivery or model behavior. No unseen held-out environment,
historical adapter, price table, live trial count decision or PR history reconciliation
was added. Structural success does not prove conversational success.

Review `handoff/CURRENT_REVIEW.md` and `handoff/CURRENT_REVIEW.zip`. Stop here.
Await review before ATGB-03 or any controlled live baseline. Do not begin a Product
Realization campaign or change production gameplay to satisfy the benchmark.
