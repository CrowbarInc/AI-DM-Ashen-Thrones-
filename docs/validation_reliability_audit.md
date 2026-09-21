# Ashen Thrones Validation Reliability Audit

Date: 2026-09-17

## Executive summary

Ashen Thrones does not have one meaning of `PASS`. Its validation lanes produce materially different kinds of evidence:

- The large pytest suite is primarily structural, component, contract, and deterministic integration evidence. A green test proves its explicit assertions held under its fixtures and patches. It does not generally prove player-facing semantic quality.
- The CI `golden_replay` gate is structural gameplay-path evidence under stubbed GM responses. In the audited checkout it selects seven tests: six run and pass with deterministic GM text; one nominally live pipeline test is skipped unless `ASHEN_RUN_CO102_LIVE_VALIDATION=1` is set. It does not exercise a real external model in ordinary CI.
- The CLI playability runner is the strongest automated short-session gameplay-path evidence: it sends fixed natural-language prompts through real `/api/chat`, uses canonical persisted state, and can use the configured model. Its `PASS` is not a semantic hard gate. It is an aggregate score from the final turn, and demonstrated unacceptable replies pass.
- Scenario-spine validation is useful long-session, scripted gameplay-path evidence. Its scoring is deterministic heuristic analysis of the recorded text and metadata. `warning` still means `overall_passed=true`; it does not evaluate fun, general answer relevance, or unrestricted player behavior.
- Manual gauntlets are the strongest available semantic gameplay evidence because a person owns the verdict and can inspect the full transcript. They are not CI gates, are not automatically enforced, and the CLI accepts an operator-supplied verdict without validating it against the rubric.
- Behavioral gauntlets, N1, synthetic sessions, content lint, coverage registries, and architecture/governance tools are narrower evidence. They should not be cited as proof that the product is playable.

Therefore, current green results support claims such as structural correctness, selected component correctness, controlled integration behavior, and basic runtime survivability. They do not, by themselves, justify a claim of reliable semantic gameplay quality or actual player-facing playability.

The demonstrated answer failures establish that an obviously broken AI-GM interaction can be green. Before substantially more autonomous feature development, the recommended next campaign is evaluator reliability: non-compensatory semantic gates for malformed output and unaddressed intent, calibrated against a human-reviewed transcript corpus, followed by reactive/adversarial multi-turn players and state/narration consistency checks. This report does not implement those changes.

## Scope and method

This audit traced executable code rather than accepting names or historical closeout claims. It inspected test collection, CI workflows, runner and evaluator implementations, mocks, persisted artifacts, and the prior simulated-playtest evidence. No thresholds, prompts, gameplay behavior, scoring rules, or PASS definitions were changed.

Repository-wide collection found 6,381 pytest cases in 456 modules. Text search found 3,294 mock/stub/patch references across 202 test files. Those counts are orientation, not quality measures: parametrization makes collected cases exceed the 5,725 statically declared `test_*` functions, and a mock reference does not make a test invalid.

## Validation architecture inventory

### 1. Unit and component contract tests

- Implementation: `tests/test_*.py` with domain code under `game/`.
- Invocation: `python -m pytest -q`, or focused modules.
- Inputs: fixtures, temporary state, constructed payloads, deterministic examples.
- Dependencies: many tests monkeypatch storage, parsers, model calls, clocks, or adjacent layers.
- PASS: every selected pytest assertion passes, excluding skipped/deselected cases.
- Evidence: console failure details; usually no durable artifact on success.
- Proves: the asserted local contract or deterministic integration behavior.
- Does not prove: live-model quality, broad player behavior, prose quality, or campaign playability unless the individual test explicitly covers it.

Major areas with extensive test coverage include final-emission contracts and metadata, prompt context, routing, fallback behavior, replay projection/governance, failure classification/reporting, lead state, and world/state boundaries. Semantic player-facing tests are a small minority of the 6,381 collected cases.

### 2. API and pipeline integration tests

- Representative files: `tests/test_playability_smoke.py`, `tests/test_api_narration_path_selection.py`, `tests/test_turn_pipeline_shared.py`, and other `TestClient(app)` modules.
- Runtime: real in-process FastAPI routes, often `/api/chat`.
- State: generally temporary persisted files via monkeypatching, not the user's canonical campaign.
- GM: ordinarily deterministic. `tests/conftest.py` disables real OpenAI startup calls by default. The playability smoke tests patch `game.api.call_gpt`, intent parsers, retry detection, and uncertainty handling; one test also bypasses `apply_final_emission_gate`.
- PASS: explicit HTTP, metadata, routing, text-fragment, or evaluator assertions.
- Evidence: pytest output only unless a particular helper writes diagnostics.
- Proves: wiring and selected runtime behavior under controlled upstream output.
- Does not prove: external-model behavior or unpatched end-to-end semantics.

### 3. Protected golden replay CI gate

- Implementation: `tests/test_golden_replay_structural_invariants.py`, `tests/test_co102_live_protected_replay_pipeline.py`, `tests/helpers/golden_replay.py`, and replay fixtures.
- Invocation: `python -m pytest -m golden_replay -q`; blocking in `.github/workflows/convergence-checks.yml`.
- Inputs: one- and two-turn natural-language scripts with seeded temporary worlds.
- GM: all six ordinary selected tests use `golden_replay_chat_stubs` and fixed `gm_response(...)` text.
- PASS: protected structural observations match expectations: route/speaker, required fields, fallback provenance, scaffold leakage, action/answer survival, and selected text anchors. Exact final prose is opt-in.
- Evidence: on CI failure, `artifacts/golden_replay/replay_failure_report.md` is uploaded. Success is largely reduced to pytest output; report-only drift layers exist separately.
- Important scope fact: the marker currently collects seven tests, not the much larger family of files with “golden replay” in their names. Six pass; the CO102 test is skipped unless an environment flag is set. Even that opt-in test stubs `call_gpt`; “live” means the replay observation pipeline, not a live external model.
- Proves: protected structural invariants survive the real in-process pipeline with controlled GM input.
- Does not prove: generated prose is relevant, coherent, or satisfying.

### 4. Playability evaluator and CLI runner

- Implementation: `game/playability_eval.py`, `tools/run_playability_validation.py`, `tests/test_playability_eval.py`, `tests/test_playability_smoke.py`.
- Invocation: `python tools/run_playability_validation.py --all` or a scenario id.
- Inputs: fixed, non-reactive natural-language prompts.
- Runtime: real `/api/chat` through in-process `TestClient` by default or HTTP with `--base-url`.
- State: hard-reset canonical persisted state by default; the runner now preserves before/after snapshots.
- GM: configured runtime path in the CLI; deterministic stubs in pytest smoke.
- Temporal depth: one or two turns per shipped scenario; summary is taken from the final turn.
- PASS: total of four 0-25 axes is at least 60 and immersion is at least 10. Individual axes pass at 15, but individual-axis passage is not required for overall PASS. Dead-turn/infrastructure invalidation can force failure.
- `acceptable`: total score at least 55; this rating can coexist with an overall failure between 55 and 59, and with a failed axis at higher totals.
- Evidence: `transcript.md`, `transcript.json`, `evaluation.json`, `summary.json`, `run_debug.json`, `metadata.json`, and state snapshots in the instrumented runner.
- Proves: the short fixed script traversed the API and avoided the heuristics strongly enough to reach the aggregate threshold.
- Does not prove: each player request was answered, every axis passed, the player was reactive, or the prose was human-plausible.

### 5. Scenario-spine long-session validation

- Implementation: `game/scenario_spine.py`, `game/scenario_spine_eval.py`, `tools/run_scenario_spine_validation.py`, fixtures under `data/validation/scenario_spines/`, and associated tests.
- Invocation: `python tools/run_scenario_spine_validation.py` with branch options.
- Inputs: predetermined natural-language branches from a fixed reset; `fixed_start_state` is authoring context and is not injected into runtime state.
- Runtime: `/api/chat` through `TestClient` or a configured live server.
- GM: whatever the selected runtime uses; evaluator itself never calls a model.
- State: reset persisted state; transcript metadata and runtime lineage are recorded.
- Temporal depth: short smoke or full scripted branches, including long-session fixtures.
- PASS: failures subtract 24, warnings subtract 7, API-majority failure subtracts 30. Two failed axes or API-majority failure yields `failed`; one failed axis yields `degraded`; failures outside an axis also yield `failed`; warnings alone yield `warning`; otherwise `clean`. `overall_passed` is true for both `clean` and `warning`. Degradation logic may worsen classification.
- Evidence: per-branch transcript JSON, evaluation/session-health output, debug data, Markdown operator summary, and aggregate artifacts. It does not preserve a canonical state-before/state-after pair.
- Proves: fixed branches retained selected lexical anchors, avoided enumerated reset/debug/filler patterns, met metadata/continuation checks, and stayed within classification rules.
- Does not prove: broad answer relevance, fun, rules correctness, reaction to output, or arbitrary conversation coherence.

### 6. N1 scenario-spine lane

- Implementation: `tests/helpers/n1_scenario_spine_harness.py`, `tests/helpers/n1_scenarios.py`, `tools/run_n1_scenario_spine_validation.py`, and N1 tests.
- Inputs: fixed shared-prefix and branch-suffix player lines.
- Runtime and GM: `run_synthetic_session`; deterministic configuration controls `use_fake_gm`, and the documented/default validation lane is synthetic/fake-GM evidence.
- State: synthetic profile and harness state, not a real campaign history.
- PASS/evidence: deterministic fingerprints, branch summaries, reason codes, state-channel observations, replay consistency, and JSON artifacts.
- Proves: deterministic harness contracts, branch reproducibility/divergence properties, and selected synthetic state invariants.
- Does not prove: real `/api/chat`, real model output, or player-facing semantic quality.

### 7. Synthetic session and transcript regressions

- Implementation: `tools/run_synthetic_session.py`, `tests/test_synthetic_sessions.py`, `tests/test_synthetic_smoke.py`, transcript helpers, and transcript regression modules.
- Inputs: generated or fixed player actions and profiles.
- Runtime: direct harness/domain calls or controlled API-shaped paths; fake GM is a supported and common mode.
- State: temporary/fabricated fixtures.
- PASS: deterministic invariants such as progress, no stall/repetition beyond specified checks, state channel behavior, routing, and expected milestones.
- Evidence: CLI summaries where requested; pytest generally preserves no success transcript.
- Proves: harness and selected deterministic continuity/state contracts.
- Does not prove: unrestricted human conversation or production model quality.

### 8. Behavioral gauntlet

- Implementation: `tests/helpers/behavioral_gauntlet_eval.py`, `tests/test_behavioral_gauntlet_eval.py`, `tests/test_behavioral_gauntlet_smoke.py`.
- Inputs: caller-supplied compact transcript dictionaries; no model calls.
- Axes: neutrality, escalation correctness, re-engagement quality, dialogue coherence.
- PASS: all selected axes pass and gameplay validation does not exclude the run. Most checks are bounded lexicon or adjacent-turn checks. Empty input passes neutrality; fewer than two turns pass re-engagement and dialogue coherence as non-violations.
- Evidence: returned structured axis results with reason codes and up to five evidence indexes; normal pytest success has no durable artifact.
- Proves: supplied rows avoid specific shallow anti-patterns.
- Does not prove: the rows came from real gameplay, that an answer addressed intent, or global narrative coherence.

### 9. Manual gauntlets

- Implementation: `docs/manual_gauntlets.md`, `tools/run_manual_gauntlet.py`, `tools/aggregate_manual_gauntlets.py`.
- Inputs: fixed suggested scripts plus interactive operator play through `game.api.chat`.
- Runtime/GM/state: real local chat pipeline and persisted state; operator controls prompts and review.
- PASS: human operator judgment against the documented target/failure rubric. The CLI's `--verdict` is freeform and is stored, not independently validated.
- Automated behavioral evaluation: advisory only; attachment failure becomes `behavioral_eval_warning` and does not fail the run.
- Evidence: full Markdown transcript, summary, key events, snippets, optional raw trace, and aggregate review reports.
- Proves: only as much as the named human review actually performed and documented.
- Blind spot: no automation ensures required gauntlets ran, that the reviewer followed the rubric, or that PASS was warranted.

### 10. Content validation

- Implementation: `game/content_lint.py`, `tools/run_content_lint.py`, `tools/ci_content_lint.py`, content-lint tests.
- Inputs: scene/world JSON and graph references.
- PASS: exit 0 when error count is zero; warnings are allowed unless `--fail-on-warnings`, which exits 2. Errors exit 1.
- CI semantics: Phase 1 uses `continue-on-error: true`, so lint findings do not fail the workflow. The warning gate is disabled with `if: false`. The subsequent summarizer and artifact upload are operational gates, not content-cleanliness gates.
- Evidence: JSON report uploaded by CI.
- Proves: author-time schema/reference/graph checks according to the report; a green workflow does not prove the lint itself was clean.
- Does not prove: runtime gameplay or prose quality.

### 11. Architecture, governance, coverage, and readiness audits

- Representative tools: `tools/validation_layer_audit.py`, `tools/validation_coverage_audit.py`, `tools/test_audit.py`, `tools/final_emission_ownership_audit.py`, `tools/planner_convergence_audit.py`, `tools/architecture_audit.py`, manifest and split-owner checks.
- Inputs: source topology, imports, registries, manifests, generated documentation, and committed snapshots.
- PASS: tool-specific parity/allowlist/drift rules. Some are strict CI gates; architecture, realization, narration-seam, and UI-mode audit steps are explicitly informational with `continue-on-error: true`.
- Evidence: console and, for some tools, generated reports.
- Proves: repository governance and declared architecture properties.
- Does not prove: gameplay quality. `validation_coverage_audit` maps declared coverage; it does not run or rescore that coverage.

### 12. Browser/UI validation

No Playwright, Selenium, Cypress, Puppeteer, WebDriver, screenshot-regression, or equivalent browser automation was found. UI-related pytest modules inspect backend UI-mode policy, payloads, source contracts, or regression matrices rather than driving a browser. There is no automated evidence that a human can complete a gameplay workflow through the rendered UI.

## Trust matrix

| Validation lane | Path / GM | Player input | State / depth | Semantic evaluation | Inspectable evidence | What PASS actually proves | Major blind spots |
|---|---|---|---|---|---|---|---|
| Unit/component pytest | Direct functions; usually no GM | Fixtures | Temp/fabricated; isolated | Assertion-specific | Failure output | Local contract held | Live integration and prose |
| API integration pytest | Real in-process API; commonly stub GM | Fixed NL/structured | Temp persisted; 1-few turns | Usually structural; selected fragments/evaluators | Usually no success artifact | Controlled wiring held | External model, spontaneous play |
| CI protected replay | Real pipeline; fixed GM stubs | Fixed NL; 1-2 turns | Seeded temp state | Structural observations; limited anchors | Failure report only | Protected route/emission invariants held | Generated semantic quality |
| Playability CLI | Real `/api/chat`; configured GM | Fixed NL; non-reactive | Canonical reset state; 1-2 turns | Four shallow heuristic axes | Strong: transcript, eval, debug, state | Final-turn aggregate threshold met | Severe single-axis failure can pass |
| Playability smoke | Real API; patched GM/parsers/retry | Fixed NL | Temp; 1-3 turns | Same evaluator plus selected content assertions | Pytest output | Evaluator and pipeline accept crafted positive controls | Production model and unpatched gate |
| Scenario spine | Real `/api/chat`; configured GM | Fixed NL branches; non-reactive | Reset persisted state; multi-turn | Session lexical/metadata heuristics | Strong transcript/eval summaries | Classification is clean/warning | General relevance, fun, arbitrary continuity |
| N1 spine | Synthetic harness; fake/deterministic GM | Fixed branch scripts | Synthetic; multi-turn | Fingerprints/invariants | Structured JSON | Harness determinism and selected state properties | Real API/model/player semantics |
| Synthetic sessions | Harness/direct or controlled path | Generated/fixed | Temp; multi-turn | Milestones and bounded anti-patterns | Variable | Deterministic simulation contracts | Production narration quality |
| Behavioral gauntlet | Offline rows; no GM call | Supplied transcript rows | None/adjacent turns | Shallow lexicon and adjacency | Structured result if retained | Enumerated anti-patterns absent | Origin authenticity and answer relevance |
| Manual gauntlet | Real local chat pipeline | Scripted plus human-reactive | Persisted; multi-turn | Human rubric | Strong transcript/report bundle | Reviewer judged that run acceptable | Not enforced; verdict provenance |
| Content lint | Static content only | None | Repository files | Structural/heuristic content lint | Uploaded JSON | Report satisfies selected severity policy | CI ignores Phase-1 failure; no gameplay |
| Governance/static audits | Source/registries | None | Repository snapshot | Topology/parity only | Reports/console | Declared architecture policy held | Runtime and semantics |
| UI/browser | Not present | Not exercised | Not exercised | None | None | No PASS signal exists | Entire rendered workflow |

## PASS semantics and compensatory behavior

### Confirmed compensatory signals

- Playability: one or more axes may fail while stronger axes lift the total to 60. Only immersion has an additional floor, and that floor is 10, below its own 15-point axis PASS threshold.
- Playability rating: `acceptable` starts at 55 while overall PASS starts at 60, so `acceptable` does not imply PASS.
- Scenario spine: warnings reduce score but classification `warning` is explicitly an overall pass. Axis failures are non-compensatory at the classification layer: one failed axis becomes `degraded`, two become `failed`.
- Manual aggregation: it counts stored operator verdicts; it does not independently derive them. A strong metric does not compensate by formula because there is no automated formula, but a reviewer can still choose a permissive verdict.
- Content lint CI: a failing Phase-1 lint command is compensated operationally by `continue-on-error`; the workflow can remain green.

### Default-success and missing-data behavior

- Behavioral neutrality passes on no turns. Re-engagement and dialogue coherence pass when fewer than two turns are supplied.
- Playability gives non-question directness a lenient starting score and gives a first-turn escalation axis 19/25 because no prior GM text exists.
- Narrative authenticity in the preserved bad playability runs can expose `narrative_authenticity_checked: false` and a skip reason while returning `passed: true` with a verdict of `unchecked`. Consumers must not read that boolean alone as positive semantic evidence.
- Scenario-spine metadata incompleteness is appended to `detected_failures` after the overall classification is calculated in `game/scenario_spine_eval.py`; the metadata block itself is reported, but this late append does not change `overall_passed`. This is an auditability failure signal, not necessarily a gameplay failure.
- Manual-gauntlet report attachment catches evaluator errors and records a warning instead of invalidating the run.

## Known-bad calibration

The four preserved runs are under `artifacts/simulated_playtest_observability/20260917T221002Z_*`. These are demonstrated results from the real playability CLI path, not fabricated examples.

| Case | Existing lane that encountered it | Detection | Overall result | Why the bad interaction remained green |
|---|---|---|---|---|
| A: “Who commands the watch here?” not meaningfully answered | Playability CLI/evaluator | Final run summary flags `player_intent` weak and missing topic anchors | PASS, 67, `acceptable` | Other axis scores compensate; direct-answer heuristics do not establish factual answer fulfillment |
| B: relic-theft question receives “No. I cannot answer that from what.” | Playability CLI/evaluator | `player_intent` fails in the run summary | PASS, 78, `acceptable` | Strong directness/escalation/immersion heuristics offset the failed axis |
| C: notice follow-up receives only “Tavern Runner mutters,” | Playability CLI/evaluator | `player_intent` fails 9/25 | PASS, 67, `acceptable` | `direct_answer` still scores 17/25 because no recognized deflection/procedure/throat-clearing pattern fires; `immersion` scores 23/25 because “Tavern” is a scene anchor; aggregate threshold passes |
| D: notice observation not meaningfully satisfied | Playability CLI/evaluator | `player_intent` fails in the final summary | PASS, 75, `acceptable` | Aggregate scoring is compensatory and does not hard-gate observation fulfillment |

All four runs reported no dead turn, so dead-turn invalidation did not protect against these semantic failures. In Case C, narrative authenticity also returned `passed: true` while its own fields said `narrative_authenticity_checked: false` and `narrative_authenticity_verdict: unchecked`.

Other lanes did not encounter these exact runtime outputs during their normal invocation:

- Playability smoke uses crafted positive-control GM strings, not the observed model replies.
- Protected golden replay uses fixed GM strings and checks structural expectations.
- Scenario-spine fixtures use different fixed prompts; its evaluator could catch empty/API/reset/debug/filler/anchor failures but has no general “answered this question” authority.
- N1 and synthetic lanes use synthetic/fake output and cannot validate the real failures by design.
- Behavioral gauntlet does not automatically consume playability artifacts and lacks a general intent-fulfillment axis.
- Manual gauntlets could detect all four through human review, but no audited manual verdict covered these runs.

## Blind spots

### Demonstrated

- A malformed, incomplete three-word GM response can pass overall playability and the direct-answer axis.
- A clearly unaddressed player intent can fail its axis and still produce overall PASS/`acceptable`.
- A narrative-authenticity result can present `passed: true` while being explicitly unchecked.
- The ordinary CI protected-replay gate can be green while no external-model response was generated.
- The content-lint workflow can be green when the lint command reports errors because the step is non-blocking.
- The full repository test suite is currently not green: 47 tests failed in this audit run. Failures include missing closeout documents, governance/snapshot drift, attribution-completeness drift, replay registry count drift, validation-layer import drift, and several gameplay/state expectations. A narrower green lane cannot be generalized to repository-wide health.

### Structural

- Stubbed-GM tests cannot detect production-model irrelevance, hallucination, voice drift, or malformed prose outside their supplied text.
- Fixed scripts cannot adapt to the GM, probe ambiguity, abandon a path, or test recovery as a human would.
- One- and two-turn lanes cannot establish long-session memory or campaign continuity.
- Offline evaluators cannot prove transcript provenance.
- Structural replay expectations cannot detect semantically nonsensical text when required fields and lexical anchors remain present.
- No browser automation exercises rendering, controls, front-end state synchronization, or a complete UI play flow.
- Governance and coverage registries cannot prove the referenced tests were run or that their assertions are sufficient.

### Plausible but unconfirmed

- Hallucinated NPC/world facts may pass if they do not hit a protected lexical contradiction.
- Narration may disagree with canonical state while both independently remain structurally valid.
- Conversation memory may decay outside fixed anchor windows or after branch patterns not represented in fixtures.
- Inventory, quest, time, and relationship transitions may become semantically impossible while satisfying schema invariants.
- Repeated but lexically varied responses may evade overlap-based repetition checks.
- Arbitrary fallback NPC identity and subtle speaker misattribution may evade checks when metadata appears valid.
- Unexpected, adversarial, contradictory, or confused player input may expose loops or dead ends absent from cooperative scripts.
- Successful isolated turns may compose into incoherent sessions beyond current long-session anchor heuristics.

These are risk hypotheses supported by bypass boundaries, not demonstrated product failures.

## Evidence preservation assessment

Best evidence:

- Instrumented playability runs preserve exact player/GM transcripts, per-turn evaluations, summary, debug data, metadata, and before/after canonical state.
- Manual gauntlets preserve full transcripts, snapshots, key events, snippets, summaries, optional raw traces, and operator notes.
- Scenario-spine runs preserve transcripts and detailed session-health/operator summaries, though not canonical before/after state snapshots.

Partial evidence:

- Golden replay can write rich failure diagnostics and has report-only drift tooling, but ordinary successful CI provides no uploaded transcript and uses stubbed responses.
- Content lint uploads its structured report even though the finding step is non-blocking.
- N1 and some synthetic CLIs preserve structured summaries, but they are synthetic evidence.

Weak evidence:

- Most pytest successes collapse behavior to a green checkmark. Reproduction requires the source fixture and rerunning the test.
- Governance/static audit successes mostly preserve console status or generated summaries, not gameplay evidence.
- There is no screenshot/video/browser trace lane.

## Test-suite architecture assessment

- Collected baseline: 6,381 cases across 456 modules.
- Static declarations: 5,725 `test_*` functions; parametrization accounts for the larger collected count.
- Mock/stub/patch prevalence: 3,294 textual references in 202 test files. This is consistent with a heavily isolated deterministic suite.
- Static skip/xfail call sites: 21. Ten permanent skips are concentrated in retired final-emission repair expectations; others depend on optional artifacts, git presence, or fixture behavior. The `golden_replay` CI selection additionally skips the CO102 live-pipeline test by environment flag.
- Current full run: 47 failures. The complete failure list is available in the audit command output; major clusters were missing BW/BZ closeout docs, architecture/governance snapshot drift, attribution coverage drift, replay registry drift, validation-layer import drift, and selected scene/lead behavior regressions.
- Focused semantic/harness run: all selected playability, behavioral, scenario-spine, N1, synthetic, and manual-report tests passed. This proves their contracts are internally consistent, including the permissive semantics described above.
- Protected replay CI-equivalent run: six passed, one skipped.

The suite extensively checks implementation contracts and ownership boundaries. It has less evidence for live, unpatched, model-generated, human-plausible play. High test volume should be interpreted as broad deterministic contract coverage, not as a playability percentage.

## Hard-gate candidates for a future campaign

These are recommendations only.

| Candidate | Why non-compensatory | Current detection | False-positive risk |
|---|---|---|---|
| Empty, truncated, or syntactically incomplete player-facing response | Breaks the conversation regardless of other strengths; Case C supports this | Dead-turn checks do not catch the demonstrated fragment; word/shape checks are insufficient | Medium: intentional fragments or terse dialogue require careful definition |
| Intelligible request not addressed | Core agency failure; all four known-bad cases support this | Playability can flag topic failure but allows compensation | High without calibrated semantic judgment; refusals and uncertainty can be valid |
| API/runtime/infrastructure failure | No valid gameplay evidence exists | Dead-turn and API-majority mechanisms exist | Low if transport/model failures are separated from valid in-world refusal |
| Canonical-state contradiction | Undermines world trust | Some state, anchor, and contradiction checks exist; no general authority | Medium-high due to implicit facts and unreliable extraction |
| Impossible state transition | Corrupts persistent play | Domain invariants cover selected transitions | Medium; rules and narrative exceptions must be modeled |
| Incorrect speaker attribution | Breaks NPC continuity and can leak knowledge | Strong metadata/route contracts; semantic text attribution is partial | Medium when narration is indirect or group-addressed |
| Required output missing for a resolved action | A successful route with no consequence is not playable | Response-type and action-outcome contracts cover selected paths | Medium; observation and uncertainty need distinct obligations |
| Conversation-breaking reset/amnesia | Invalidates multi-turn play | Scenario-spine detects enumerated reset phrases and some anchor loss | Medium-high for legitimate scene/time jumps |

The first implementation prerequisite is a human-labeled calibration corpus. Without it, hard gates for intent and coherence risk replacing false negatives with brittle false positives.

## Recommended remediation sequence

1. Establish a small, versioned, human-reviewed transcript corpus containing the four demonstrated failures plus matched acceptable refusals, terse replies, observations, and follow-ups. Preserve exact output, state, and reviewer rationale.
2. Redesign evaluator result semantics so `passed`, `unchecked`, `not_applicable`, and `invalid_run` cannot be confused. Make the top-level playability conclusion expose failed mandatory axes explicitly.
3. Add carefully calibrated non-compensatory gates for malformed/incomplete output and clearly unaddressed intelligible intent. Keep aggregate scores as diagnostics rather than allowing them to erase severe failures.
4. Add reactive simulated-player scenarios that choose follow-ups from prior GM output, then add adversarial/confused personas and recovery tests.
5. Add state/narration consistency checks over canonical before/after snapshots for NPC identity, inventory, quest/project, time, location, and combat transitions, starting with high-confidence invariants.
6. Expand long-session evidence with human-transcript regressions and branch paths that are not cooperative with known heuristics.
7. Add a real browser/UI playtest lane with inspectable screenshots or traces for a small critical workflow.
8. Clarify CI naming and artifact policy: label stubbed replay as structural, make content-lint gating intent visible, and publish representative success evidence for gameplay lanes.
9. Repair the current 47-test full-suite baseline separately before treating “full suite green” as an available release signal.

Normal feature development should not use aggregate playability PASS as autonomous evidence of player-facing correctness until steps 1-3 are complete. Structural work can continue using the narrower lanes when claims are kept within what those lanes prove.

## Major implementation references

- Playability scoring and aggregate PASS: `game/playability_eval.py::_score_direct_answer`, `_score_player_intent`, `_score_logical_escalation`, `_score_immersion`, `_finalize_overall`, `evaluate_playability`.
- Playability runtime and artifacts: `tools/run_playability_validation.py::run_scenario`, `_write_observability_artifacts`, `_transcript_markdown`, `_evaluation_artifact`.
- Stubbed playability smoke: `tests/test_playability_smoke.py::_patch_api_retry_and_uncertainty` and its four tests.
- Scenario-spine PASS: `game/scenario_spine_eval.py::_compute_score`, `_classify`, `_EvalContext.evaluate`; runner aggregation in `tools/run_scenario_spine_validation.py::build_aggregate_session_health_summary`.
- N1 synthetic boundary: `tests/helpers/n1_scenario_spine_harness.py::execute_n1_spine_branch_with_shared_prefix`; `tools/run_n1_scenario_spine_validation.py`.
- Behavioral PASS: `tests/helpers/behavioral_gauntlet_eval.py::evaluate_behavioral_gauntlet` and axis evaluators.
- Manual authority/evidence: `tools/run_manual_gauntlet.py`, especially `try_behavioral_eval_for_run`, `_write_transcript`, report construction, and operator verdict handling; rubric in `docs/manual_gauntlets.md`.
- Golden replay structural authority: `tests/test_golden_replay_structural_invariants.py`, `tests/helpers/golden_replay.py::assert_protected_golden_turn_observation`; marker scope in `.github/workflows/convergence-checks.yml`.
- Default external-call suppression: `tests/conftest.py`.
- Content-lint exits: `tools/run_content_lint.py::_exit_code`; CI non-blocking policy in `.github/workflows/content-lint.yml`.
- Coverage registry boundary: `tests/validation_coverage_registry.py`, `tools/validation_coverage_audit.py`.
- Prior evidence: `docs/simulated_playtest_observability_audit.md` and `artifacts/simulated_playtest_observability/`.

## Commands executed

```text
rg --files ...
rg -n -i <validation and status vocabulary> ...
rg -n <mock/skip/browser/runner criteria searches> ...
python -m pytest --collect-only -q --basetemp=codex_pytest_tmp_validation_audit_collect*
python -m pytest -m golden_replay --collect-only -q --basetemp=codex_pytest_tmp_validation_audit_golden_collect
python -m pytest -m golden_replay -q --tb=short --basetemp=codex_pytest_tmp_validation_audit_golden
python -m pytest tests/test_playability_eval.py tests/test_playability_smoke.py tests/test_behavioral_gauntlet_eval.py tests/test_behavioral_gauntlet_smoke.py tests/test_scenario_spine_eval.py tests/test_run_scenario_spine_validation.py tests/test_n1_scenario_spine_validation.py tests/test_n1_scenario_spine_cli.py tests/test_synthetic_sessions.py tests/test_synthetic_smoke.py tests/test_manual_gauntlet_report.py tests/test_manual_gauntlet_aggregation.py -q --tb=short --basetemp=codex_pytest_tmp_validation_audit_semantic
python -m pytest -q --tb=short --basetemp=codex_pytest_tmp_validation_audit_full
```

The runtime used the bundled Codex Python with `PYTHONPATH=.\.venv\Lib\site-packages` because `python` was not on `PATH` in this shell.

## Test results

- Collection: 6,381 tests from 456 modules.
- Protected replay marker: 6 passed, 1 skipped.
- Focused evaluator/harness slice: passed.
- Full suite: failed with 47 failures. No claim of full-suite health is made.

## Files created or modified by this audit

- Created: `docs/validation_reliability_audit.md`.
- No validator, threshold, prompt, fixture, runtime, gameplay, or PASS behavior was modified.
- Existing dirty files and prior simulated-playtest artifacts were preserved unchanged by this audit.

## Final answer to “When Ashen Thrones says PASS, what does that actually mean?”

It means only that the specific lane's explicit conditions held. For most lanes, that is structural or deterministic component evidence. For playability, it means a final-turn heuristic aggregate reached 60 with immersion at least 10 and the run was not invalidated; it does not mean every player intent was served. For scenario spine, it means the session was classified `clean` or `warning` under bounded continuity heuristics. For manual gauntlets, it means a human entered that judgment. No current automated PASS, alone, proves actual player-facing playability.
