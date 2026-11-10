# PR-PLAY-49 — Offline Anchored Investigation Narration Prototype

## Executive summary and final verdict

**A — PASS / GO for a tightly controlled, quarantined real-provider experiment against saved outcomes.** This is a feasibility verdict, not approval of generated prose for gameplay. PR-PLAY-50 has not started. Real provider requests and tokens in this pass: **0 / 0**. No gameplay session, provider adapter, automatic retry, GitHub push, model change or budget change was performed.

The prototype combines the existing authoritative investigation projection, immutable engine-owned anchor records, one offline-stub free-form prelude, and engine assembly into a distinct review artifact. It is explicitly opt-in and has no gameplay caller. All outputs have `review_required=true`. Narration has no path to apply consequences, discover clues, promote incidental details, remember leads, or persist scene/world changes.

Two canonical investigations and six unfamiliar boundary fixtures preserve their authorized information. Ten illustrative notice-board preludes form **seven conservatively grouped rhetorical families**, versus three controlled-renderer block-order families. On an unblinded editorial comparison using identical notice-board outcomes, provisional mean quality scores are host **10.0/16**, controlled **10.2/16**, anchored **13.9/16**. These demonstrate expressive capacity of the interface, not model creativity or player preference.

**Semantic safety is incomplete.** The 40-case authored corpus has 30 unsafe and 10 safe examples: 13 true rejections, **17 unsafe heuristic passes**, 9 true accepts and 1 false rejection. Passing checks does not approve prose. Raw unsafe artifacts and diagnostics are retained, and the review labels reject those 17 candidates. A provider trial must quarantine raw outputs for human assessment; no heuristic pass may trigger player display or any adoption path. Under that restriction, semantic mistakes are measurable trial results rather than gameplay changes. Without quarantine and review, the recommendation is NO-GO.

## PR-PLAY-48 baseline and source integration map

PR48 selected hybrid authority-bounded narration: exact engine disclosures, free descriptive realization, no prose-to-state adoption, ephemeral incidental texture, and explicit separation between mechanical isolation and semantic truth. Its architectural report and source map are retained under `supporting/artifacts/pr_play_48/`. Its recommendation to stop expanding phrase recognizers is preserved. This pass implements only the offline investigation slice, including requested failure/repeat/mundane boundary fixtures; it does not implement the other authority profiles.

Existing integration points inspected, with repository line numbers at review time:

| Responsibility | Existing source |
|---|---|
| Investigation resolution and knowledge ownership | `game/exploration.py:191 resolve_exploration_action`; `:1101 process_investigation_discovery`; `game/models.py ExplorationEngineResult` |
| Authorized discovery selection | `game/authorized_information.py revealed_information` selects successful resolver disclosures and excludes repeat/failure stale text |
| Mechanical outcome projection and heuristic audit | `game/mechanical_claims.py mechanical_outcome`, `audit_mechanical_claims`, `mechanical_fallback` |
| Hidden-information projection | `game/narration_authorization.py:18 project_narration_payload`; public/known/revealed information, private extensions excluded |
| Narration context and final provider payload | `game/prompt_context.py:1527 build_narration_context`; `game/gm.py:4590 build_messages` |
| Deterministic host result and authorized speech | `game/api.py:1057 deterministic_provider_skip_line`; `game/api_turn_support.py:259 _authoritative_resolution_fact_text`; `game/dialogue_authority.py:787 select_host_speech` |
| Semantic checks and final sealing | `game/immutable_valid_response.py:623 validate_generated_response`; `:1301 seal_accepted_response`; `:1624 run_preserve_if_valid`; `:2265 commit_text` |
| Dangerous adoption/extraction paths, deliberately bypassed | `game/api.py:1988 _apply_post_gm_updates`, scene/world legacy validators, world-update application, contextual-lead extraction, bounded-improvisation promotion |
| Controlled comparator | `game/controlled_investigation_renderer.py` enum plan validation, deterministic composition, explicit offline preview |
| Existing diagnostics | API narration accounting/`narration_provider_calls`, provider-skip metadata, immutable-response audit and narration-seam diagnostics; prototype adds safe diagnostic codes plus retained validator audit |

No API integration point was wired. Existing gameplay continues through its original paths. Source snapshots and raw regression results support this limited statement; the 23 baseline failures remain unresolved.

## Exact source changes

1. **New `game/anchored_investigation_narration.py`**: small contract, discovery anchors, allowlisted offline prelude request, existing validator invocation, assembly, deterministic fallback, immutable review artifact.
2. **New `game/offline_investigation_projection.py`**: moves PR47's existing `AuthorizedInvestigation`, `_strings`, `authorize_investigation`, and `deterministic_fallback` definitions unchanged into a shared offline helper.
3. **Modified existing workspace `game/controlled_investigation_renderer.py`**: imports/re-exports those same helper symbols; controlled rendering, selector validation, preview behavior and remaining definitions are unchanged. AST comparison confirms all moved and retained definitions match the PR48 source snapshot. Ten historical controlled stress outputs reproduce byte-for-byte.
4. **New `tests/test_pr_play_49_anchored_narration.py`**: 80 offline tests and raw evidence generation.
5. **New evidence tooling**: `artifacts/pr_play_49/run_regression.py`, `evaluate.py`, `package_review.py`.

`source_change_manifest.json` records exact hashes and sizes. Reports, JSON, logs, XML, source/supporting snapshots, and CURRENT_REVIEW archive/pointer are evidence outputs. Existing tests, resolver code, campaign files, provider configuration and token budgets were not edited. The workspace already contained extensive unrelated tracked and untracked changes; this pass does not claim them as PR49 work or revert them.

The initial direct import of PR47's renderer triggered its static no-callers isolation test. Extracting the unchanged read model avoided renderer-to-renderer coupling and retained that test unchanged. Initial failing results are kept in `initial_final.xml/txt`. An early evidence-reader failure used `clue_text` in a historical summary that actually retains `discovered_clues`; `focused.xml` retains that development failure. Neither failure was suppressed or relabelled as pre-existing.

## Contract, outcome projection and offline interface

`authorize_anchored_investigation` is an engine-only adapter over a completed result and existing narration payload. It reuses the established projection and disclosure selection; it neither resolves an action nor persists knowledge. This narrow slice rejects consequences outside discoveries, including inventory, currency, health, conditions, NPC changes and travel. Failed/repeated/mundane fixtures do not fabricate discoveries.

The frozen contract contains the existing frozen outcome view and a tuple of frozen `DiscoveryAnchor(order, source, status, text)` records. Original source sentences retain their uncertainty. Multiple disclosures retain resolver selection order. Previously known information is labelled by an engine status sentence. With no discovery, status and public observations supply the engine statements instead.

The offline generator receives a detached JSON dictionary with exactly four top-level keys: `authorized_investigation`, `public_scene`, `descriptive_constraints`, `max_output_utf8_bytes`. The investigation fields are target, status, success, newly discovered and previously known text. Public scene information is restricted to string observations; planner instructions, world data, raw metadata, hidden catalogs, NPC motivations, quest internals and arbitrary nested convenience fields do not cross this final allowlist. The target is the resolved target identifier, not an undiscovered clue/catalog identifier.

`OfflinePreludeGenerator.generate(request)` returns one string. It accepts/returns no mutation envelope or metadata. Maximum output is 1,600 UTF-8 bytes. Stub code is trusted Python, not an adversarial-code sandbox; only its returned value is untrusted. It receives no engine state references or state-write tools. JSON roundtripping detaches even nested request lists. Mutating the request cannot change the original outcome or anchors.

Validation applies strict shape, size, empty/incomplete/control-character checks; detects an exact duplicate of an anchor; and reuses `validate_generated_response` with an engine-owned reduced resolution. It does not derive grants from prose. The standalone resolver fixtures have no orchestration `resolution_contract`; contract lookup therefore supplies an empty mapping for those checks. These results exercise the existing high-confidence/mechanical validator, not every full-context production semantic branch. Production-path regression tests are reported separately.

Assembly is `[trimmed prelude]`, a blank line, then every exact engine anchor in order. No player-facing role labels or trailing generated postscript are added. Exact-once integrity is checked on accepted assembly. Approximate paraphrase duplication and contradictions remain semantic risks. No repair, sentence salvage, second judging provider or retry occurs.

## Canonical investigation results

Saved PR43 engine summaries are retained in `evidence_canonical_saved_resolvers.json`; fresh offline resolver results independently confirm the same disclosures. No campaign fixture was changed.

**“I examine the notice board.”** Authorized anchor:

> The missing patrol was last seen taking the northwest mud track past the crates.

One complete illustrative response:

> Rain patters around the gate. Against that restless background, the posted notices hold your attention, one line at a time.
>
> The missing patrol was last seen taking the northwest mud track past the crates.

The prelude is newly authored offline prose, not recorded provider output. The anchor is generated from the resolver result, not from that prelude. No extra patrol members, witness, reward, culprit, item or destination are authorized.

**“I examine the footprints.”** Authorized anchor:

> Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

Four compatible preludes cover careful examination, mud conditions, a pause before conclusions, and surface texture. They retain the complete uncertainty sentence. Existing checks reject the explicit “definitely prove” example but miss unsupported exact traveler counts, a definitive destination, and the asserted patrol connection. Those outputs are retained as unsafe review cases; unchanged anchor bytes do not cure a contradictory prelude.

## Six additional fixtures

All are unfamiliar offline scenarios, not campaign additions. Full scene, outcome, authorized projection, hidden canaries, request, candidate, response, audit and fallback are retained in each `evidence_fixture_*.json` and `scenario_matrix.json`.

| Target / category | Authorized information and result |
|---|---|
| Merchant ledger / success | Twelve ingots arrived, nine entered stock; exact clue retained |
| Damaged bridge / partial | Fresh scoring on one support; cause cannot be determined; qualifier retained |
| Sealed chamber / failed | No new result; stale concealed-release clue excluded |
| Written testimony / previously known | Ferryman at quay, time unknown; existing knowledge retained, no new discovery claimed |
| Weathered monument / mundane | Public visible observations and no-new-clue status; no fabricated clue |
| Abandoned campsite / multiple | Blue-cloth fragments, then a boot impression with unknown owner; both anchors retained in order |

Ledger/bridge/monument use actual resolver results on synthetic scenes. Failed and repeat matrix cases are explicit outcome fixtures, backed by separate actual failed-check/repeat-resolver tests. The campsite uses an actual single-clue result extended with an explicit second authorized disclosure in the same existing result schema. It is not represented as a production multi-clue resolver run.

## Anchor integrity, mechanical authority and hidden information

All eight fixture outputs preserve authorized anchors exactly once in order. Single/multiple/partial/uncertain/known/no-clue/failed cases, empty and malformed candidates, exact duplicate anchors, conflicting claims, renderer errors and simulated timeouts retain the engine result. Discovery delivery survives rejection and fallback. No re-resolution or effect application takes place.

Fourteen existing sink references were instrumented across API, GM, world, storage and bounded improvisation; **zero calls** occurred. Frozen-record mutation raises, request-list mutation is detached, output serialization has no GM adoption envelope, and source inspection confirms no gameplay import/caller. The review type cannot enter those paths through any implemented adapter. This is an architectural capability restriction, not a claim that arbitrary malicious Python could never access global files.

Campaign data before/after hashes match for every checked file; exact count is in `state_integrity.json`. Broad regression suites ran in a disposable copy so historical test evidence and campaign data were not overwritten. Selected PR49 focused tests generate only this pass's evidence.

Private input tests cover undiscovered clue text/identifiers, GM notes, NPC motivation, hidden destinations, private world state and quest development, including nested unknown metadata. No private canary reaches the stub request or authorized anchors. A candidate cannot cause a lookup or reveal hidden source data by naming an identifier.

**Output secrecy is a different guarantee:** a free string can guess or echo a hidden fact or internal-looking identifier. The current validator rejects marked `GM_ONLY`/“the secret is” prose but accepts natural secret assertions and a synthetic hidden identifier. These are unsafe review artifacts, not approved player narration. There is no universal secret-text matching or paraphrase detector. Public authoring must also correctly classify visibility; allowlisting cannot repair a secret already mislabelled public. Gate 3 below concerns provider-facing input exclusion, not an unsupported proof of output truth/secrecy.

## Semantic boundary, failure handling and incidental detail

`semantic_metrics.json`, `adversarial_corpus.json` and `residual_failures.json` preserve all raw candidates, expected labels, existing-validator audits, final preview/fallback, and confusion labels. **17/30 unsafe cases pass heuristics**: key discovery, indirect wealth/healing/condition removal/arrival/quest completion, culprit, contradictory patrol direction, traveler count, destination, unsupported connection, natural hidden facts, hidden identifier, private NPC motivation, quest twist and world-state claim. **1/10 safe cases falsely rejects**: harmless dust lying in a pack is read as possession. The six requested authority probes are included verbatim; coins and marked passage prose reject, while key/poison/culprit/quest frames expose misses. No phrase dictionary was expanded.

Detected unsupported consequences, marked secret disclosure and explicit certainty assertions reject the complete prelude. Empty, overlong, non-string, malformed JSON-envelope, nested proposal, invalid metadata, incomplete and control-character candidates fall back. Simulated timeout, generator exception and renderer exception return safe diagnostic codes, without reflecting private exception messages. Multiple recognized conflicting assertions reject. Undetected contradiction remains in a **review-required artifact** and must be rejected by a reviewer; the prototype does not claim automatic semantic approval.

Fallback uses existing deterministic wording with independently preserved anchors. A single engine status avoids repeating two “nothing new” sentences. It neither edits unsafe prose into another claim nor partially commits generated text. Generation is attempted once; no retry. Raw rejected inputs remain only in evidence, not fallback prose.

The chipped-cup case runs in a separate compatible inn fixture. It may appear as incidental prose, but creates no item ID, possession, value, properties, scene object, quest lead, campaign update or memory. A future “I pick up the cup” must go through engine admission and a suitable mundane-interaction/inventory decision using the prior mention as provenance. Mention alone is insufficient authority. No continuity or promotion machinery is implemented.

## Expressive range and provisional quality comparison

Ten newly authored, selected offline candidates vary concise action, atmosphere, tension, observation, method, character gesture, sensory focus, reflection, quick pacing and understatement. They are **not real AI-generated provider results**. Conservative grouping merges atmosphere/sensory, tension/fast fragments and observational/methodical progressions: **seven families** remain. The family grouping, rationale and raw outputs are in `expressive_range.json`. PR47's ten saved plans were rendered against the identical notice-board outcome; they still form three block-order families. Historical footprint outputs also reproduce exactly after helper extraction.

The quality rubric assigns 0 absent/incorrect/strongly weak, 1 adequate/limited, 2 complete/strong to information completeness, mechanical consistency, naturalness, expressive range, atmosphere, investigative clarity, repetition avoidance and cohesion. Range is an approach-corpus property, not a uniqueness score. Per-candidate/category ratings and explanations are in `quality_comparison.json`.

| Identical notice-board outcome | Mean total /16 | Mechanical /2 | Narrative-only /12 |
|---|---:|---:|---:|
| Existing deterministic host emitter | 10.0 | 2.0 | 6.0 |
| Controlled renderer, ten existing plans | 10.2 | 2.0 | 6.2 |
| Anchored, ten authored preludes | 13.9 | 2.0 | 9.9 |

All three contain the authorized clue in this comparison. Mechanical correctness is reported separately and applies to these reviewed comparison samples, not the unsafe corpus. Controlled output repeats attention/pause/whole-to-detail language. Anchored candidates offer more rhetorical freedom but some are mannered, sparse variants lack atmosphere, and the immutable paragraph boundary can feel pasted in. The neutral prelude reused across all eight fixture tests is deliberately formulaic and demonstrates no expressive improvement by itself. Additional baseline weaknesses include the mundane host emitting only a target label and the repeated-clue host omitting prior text; raw responses are retained, without claiming these baselines lost a new discovery in the canonical comparison.

Ratings are unblinded implementing-agent judgments, with hand-selection bias and no independent panel, player study, sampling of a model or proof that an actual provider uses the extra freedom. Do not interpret aggregate scores as solving semantic safety.

## Performance and future token estimate

Final focused-run measurements, 100 warm in-process samples per operation: validation median **0.673 ms**, assembly **0.0008 ms**, fallback **0.0019 ms**, complete preview **0.777 ms**. Measured maxima are retained in `evidence_performance.json`. Timing excludes imports, provider transport and gameplay resolution. Variability between development/final runs is expected.

Authorized outcome JSON is **596 bytes**, final prelude request **1,118 bytes**, illustrative output **123 bytes**, discovery anchor **80 bytes**. Ten previews under tracemalloc showed **9,096 bytes peak traced allocation** (2,728 retained); this is incremental Python tracing, not process RSS or total model memory.

English content estimate at characters/4: about **280 input + 31 output tokens** for this example, before future message/schema/protocol overhead. The 1,600-byte output bound is roughly 400 English tokens, not a tokenizer guarantee. These are estimates, not measured provider tokens, latency or monetary costs. PR43 used **39,804 measured tokens** across five requests (37,326 input/2,478 output), including a 26,714-token opening input; it made zero gameplay narration calls. A narrow prelude request is much smaller than those whole-context interactions, but would add a new request if no eligible post-resolution interaction is reused. Do not claim it replaces PR43's opening/interpretation cost.

A future experiment could reuse an already eligible post-resolution narration interaction, send one selected authorized projection instead of broad planner context, and avoid sending anchors twice. A pre-resolution interpretation call cannot realize an outcome it does not yet know. None of these optimizations or transport changes is implemented; actual tokenizer, request overhead and latency must be measured in PR50.

## Regression results and scope

Environment `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1` is set before application imports in runners; existing test conftest blocks live provider constructors and generation entry points. Baseline and full final runs use a disposable workspace and the same 29 existing suites, covering investigation checks/discovery, PR44 information delivery, PR45 projection, PR46 claim validation, PR47 rendering, host narration, semantic checks, finalization, state integrity and context isolation.

| Run | Collected | Passed | Failed | Skipped | Errors |
|---|---:|---:|---:|---:|---:|
| Fresh baseline | 698 | 675 | 23 | 0 | 0 |
| Final full selection | 777 | 754 | 23 | 0 | 0 |
| Final focused, including added historical-equivalence comparator | 80 | 80 | 0 | 0 | 0 |
| Combined unique test identities | 778 | 755 | 23 | 0 | 0 |

**80 new tests pass, zero changed existing outcomes, zero new regressions.** The 23 failures are freshly reproduced pre-existing failures, not inferred from historical pass counts. Their exact identities, failures and commands are in baseline/final XML/logs and `regression_comparison.json`. They concern pre-existing finalization, exploration API compatibility, travel/social overrides, state consistency and campaign-start expectations. No suppression or existing expectation edit was used. The whole repository suite was not run, and existing failures are not certified harmless or fixed.

## GO / NO-GO gates and recommended PR-PLAY-50 scope

| Gate | Decision and supporting bound |
|---|---|
| 1 Mechanical authority | **PASS:** no state handles, proposal fields, adoption adapter, gameplay caller or instrumented sink calls; effects remain resolver-owned |
| 2 Authorized information | **PASS:** exact engine anchors preserved across eight fixtures, ten variants and fallback/error cases; no candidate selects or rewrites them |
| 3 Hidden provider inputs | **PASS:** existing projection plus final explicit allowlist excludes tested private fields and identifiers; trusts public/known authoring |
| 4 Expressiveness | **PASS, provisional:** seven conservative authored families vs three controlled families on a fixed outcome; editorial quality advantage, not a model result |
| 5 Bounded semantic risk | **PASS only for quarantined saved-outcome review:** known heuristic misses retained and explicitly rejected by review labels; no live gameplay, persistence, automatic approval or player release is authorized |

**Recommendation: GO for an isolated real-provider measurement experiment, not automated player narration.** All corpus review labels are explicit; there are no unreviewed ambiguous cases being treated as safe. The semantic failure rate remains a trial measurement target, not a production acceptance rate. If PR50 cannot keep all generated outputs quarantined pending review, Gate 5 fails and the recommendation becomes NO-GO; the smallest correction is the trial harness's artifact-only release boundary, not another broad phrase-recognizer expansion.

Recommended PR50: use saved notice-board and footprint outcomes, no live gameplay and no state-write capabilities. Predeclare **four requests total** (two fixed prompts per saved outcome), one attempt each, no retries, unchanged configured model/budgets. Preflight estimated token fit under existing limits; stop before dispatch if that fixed request count or declared token ceiling cannot be honored. Preserve full authorized requests, raw responses, usage and timing. Compare actual preludes with the same deterministic and controlled baselines; review mechanical contradictions, count/destination/culprit certainty, invented rewards, hidden assertions, duplication, atmosphere and cohesion. Measure actual tokens and latency and stop at the declared cap. Every result remains a reviewer artifact even if automated checks pass. No raw or assembled provider text enters a player session, memory or state-adoption path. A later gameplay rollout requires separate authorization and evidence.

No real-provider request was made in this pass. No PR50 harness or experiment was started.

## Evidence package and stop point

`handoff/CURRENT_REVIEW.zip` is the established stable archive; a timestamped sibling is also preserved. The prior stable archive/report were copied to `artifacts/pr_play_49/predecessor/` before replacement. No older archive was removed. This packet includes this report, request, source manifest/snapshots, PR48 baseline, actual canonical resolver evidence, all six extra fixtures, 40-case corpus including every failed semantic case, ten expressive samples, fixed-outcome comparator, ratings, integrity checks, failure diagnostics, performance measurements, provider-use record and raw regression XML/logs. The complete supporting live summary is historical evidence, not a provider run in this pass.

`MANIFEST.json` hashes every packaged file; `archive_verification.json` records CRC, manifest validation and equality of stable/timestamped archives. Verification output is external to the archive to avoid self-referential hashing. Local credential-value matching checks source/log snapshots before packaging without exporting credentials. Full historical campaign stores remain at their existing repository paths; this packet does not modify them.

Final verdict: **A — PASS / GO for the defined quarantined experiment. Semantic safety for automatic player-facing free prose remains unproven and visibly poor on this adversarial corpus.** Stop after evidence packaging. No GitHub push and no PR50 execution.
