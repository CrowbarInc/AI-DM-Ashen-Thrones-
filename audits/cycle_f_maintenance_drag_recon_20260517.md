# Cycle F Maintenance Drag Recon - 2026-05-17

## Scope

Question: Are fixes becoming smaller and better-owned, or are we still paying high maintenance drag through broad file fanout and repeated hotspot edits?

Constraints followed: reporting only; no runtime logic changes; no test thinning; no assertion deletion; no edits to `game/final_emission_gate.py`.

## Part 1 - Git history maintenance-drag metrics

Source window: last 30 commits on the current branch (`git log --oneline -30`).

Artifact/report/doc classification used here: `audits/**`, `docs/**`, `*.md`, `artifacts/**`, generated pytest temp trees, files with `results`, `baseline`, `report`, or `analysis` in the path. Runtime data snapshots under `data/**` are counted as non-artifact because they are tracked runtime fixtures/state in this repo.

### Per-commit fanout

| SHA | Title | Total files | Non-artifact | Tests | Production | Artifact/doc | Gate touched | Visibility/referential touched | Likely hotspot |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 8ddb183 | E: Test Signal Ownership Thinning | 23 | 13 | 13 | 0 | 10 | No | 1 | fallback; replay / classifier / dashboard |
| 6c00e6e | D: Final Emission Gate Pressure Reduction | 17 | 14 | 9 | 5 | 3 | Yes | 3 | final_emission_gate; visibility / referential clarity |
| a5c9146 | Cycle C: contract fallback ownership and mutation lineage | 18 | 13 | 10 | 3 | 5 | Yes | 0 | fallback; final_emission_gate |
| 98bc059 | Failure Classification Dashboard | 28 | 9 | 8 | 0 | 19 | No | 0 | replay / classifier / dashboard |
| ac1ba90 | Add Golden Replay Scenario-Spine Baseline Suite | 6 | 3 | 2 | 0 | 3 | No | 0 | replay / classifier / dashboard |
| f04ef66 | Converge evaluator boundaries, telemetry, and governance | 16 | 2 | 0 | 1 | 14 | No | 0 | docs / audit only |
| 792de85 | Freeze Evaluator Convergence and Boundary Governance | 22 | 15 | 9 | 6 | 7 | No | 0 | other |
| c89f2f4 | Complete Gate Convergence, Semantic Fencing, and Relocation Readiness Hardening | 24 | 22 | 15 | 7 | 2 | Yes | 0 | final_emission_gate; route / speaker / social |
| 0f03dd6 | Gate Boundary Convergence and Compatibility Fencing | 18 | 14 | 5 | 9 | 4 | Yes | 0 | final_emission_gate |
| 177099a | Close Out Realization Failure-Locality | 7 | 0 | 0 | 0 | 7 | No | 0 | docs / audit only |
| 0f80564 | Realization Layer Failure-Locality Hardening | 36 | 25 | 11 | 13 | 11 | Yes | 0 | final_emission_gate; fallback |
| 673118e | PLANNER: Stabilize Failure Locality Seam | 41 | 41 | 17 | 17 | 0 | Yes | 0 | final_emission_gate; replay / classifier / dashboard |
| 29da646 | Adoption Gateway (Finalized) | 267 | 4 | 2 | 2 | 263 | No | 0 | docs / audit only |
| 6dcccd8 | Post-GM adoption gateway fenced | 1407 | 4 | 3 | 1 | 1403 | No | 0 | route / speaker / social |
| 9808d01 | Remove generated pytest artifacts from tracking | 57 | 1 | 0 | 0 | 56 | No | 0 | docs / audit only |
| 5cb8444 | Recover mixed investigation question routing | 538 | 4 | 2 | 2 | 534 | No | 0 | route / speaker / social |
| 53165bb | UI & Freeform Investigation (I) | 93 | 9 | 1 | 4 | 84 | No | 0 | route / speaker / social |
| f3fa4b1 | Preserve player chat in replayed logs | 52 | 8 | 2 | 2 | 44 | No | 0 | replay / classifier / dashboard |
| 773cbe0 | Promote accepted scene opening candidates | 26 | 6 | 2 | 1 | 20 | Yes | 0 | final_emission_gate; fallback |
| f6a4c6f | Promote upstream prepared scene openings before final gate | 135 | 5 | 1 | 1 | 130 | No | 0 | fallback |
| f487f4d | Guard rich scene openings from post-gate shortening | 216 | 6 | 1 | 2 | 210 | No | 0 | fallback |
| 43bdb8b | Collapse start_campaign onto canonical gm_output | 195 | 5 | 1 | 1 | 190 | No | 0 | fallback |
| c6e63b0 | Refresh session snapshot and opening scene details | 7 | 7 | 1 | 3 | 0 | Yes | 0 | final_emission_gate |
| 1b3b3ee | Preserve valid scene openings before deterministic fallback | 5 | 5 | 1 | 1 | 0 | Yes | 0 | final_emission_gate; fallback |
| b0cfd07 | Refine opening scene narration contract | 5 | 5 | 1 | 1 | 0 | No | 0 | fallback |
| 20b1420 | Opening Clean-Up | 3 | 3 | 0 | 0 | 0 | No | 0 | other |
| 9e83820 | Preserve journal openings through selector fallback | 7 | 7 | 1 | 3 | 0 | Yes | 0 | final_emission_gate; fallback |
| ee3af57 | Add perceptual filtering for journal opening facts | 3 | 3 | 0 | 0 | 0 | No | 0 | other |
| 2b293b2 | Restore journal seed facts as opening source | 3 | 3 | 0 | 0 | 0 | No | 0 | other |
| 2013258 | Restrict journal seed facts to perceptual opening content | 7 | 7 | 2 | 2 | 0 | No | 0 | fallback |

### Summary metrics

- Median non-artifact files touched per commit: 6.
- Commits touching 8+ non-artifact files: 11 of 30.
- Commits touching `game/final_emission_gate.py`: 10 of 30.
- Commits touching visibility/referential-clarity surfaces: 2 of 30 by path name, both in the recent Cycle D/E window.

Top non-artifact file hotspots:

| Count | File |
| ---: | --- |
| 15 | `data/combat.json` |
| 15 | `data/session.json` |
| 15 | `data/session_log.jsonl` |
| 10 | `game/final_emission_gate.py` |
| 9 | `tests/test_start_campaign_api.py` |
| 8 | `game/api.py` |
| 8 | `tests/test_final_emission_gate.py` |
| 6 | `game/gm.py` |
| 5 | `game/final_emission_meta.py` |
| 5 | `game/final_emission_validators.py` |

### Cluster observations

- Recent Cycle C/D/E commits are broad but more ownership-explicit: they pair audit files with targeted test/helper files around fallback ownership, visibility fallback routing, golden replay, classifier, and dashboard contracts.
- The worst fanout commits (`673118e`, `0f80564`, `c89f2f4`, `792de85`) predate or sit around ownership-convergence work and touch many production and test files together.
- `game/final_emission_gate.py` remains the main runtime hotspot: 10 touches in 30 commits, and most broad commits that touch it also touch `game/final_emission_meta.py`, validators, `game/gm.py`, or replay/classifier tests.
- A separate persistent hotspot is tracked runtime data snapshots: `data/combat.json`, `data/session.json`, and `data/session_log.jsonl` each appear in 15 commits. These inflate non-artifact fanout and should be treated separately from source fanout in later maintenance metrics.
- Visibility/referential clarity path touches are low by commit count, but the surface is dense: `tests/test_final_emission_visibility.py` is a 958-line owner-like suite, while `tests/test_final_emission_gate.py` still contains visibility route/order/projection sections.

## Part 2 - Visibility / referential-clarity surface map

### `tests/test_final_emission_visibility.py`

- Responsibility: canonical pipeline coverage for player-facing visibility, first mention grounding, referential clarity, visibility metadata, fallback satisfaction through finalization, and a small micro-smoothing/export boundary.
- Role: owner for visibility/first-mention/referential behavior at pipeline level; also contains some downstream finalization checks.
- Repeated assertions/metadata checks: many tests assert `visibility_*`, `first_mention_*`, and `referential_clarity_*` metadata shapes, replacement booleans, violation kinds, and safe fallback text behavior.
- Protective duplication: yes. The suite checks negative and positive examples for unseen NPCs, hidden/discoverable facts, active interlocutors, pronouns before first explicit entity, same/next sentence ambiguity, descriptor reanchors, quoted speaker tags, and nonperson pronouns. This breadth looks intentional because failures would otherwise collapse into final-gate symptoms.
- Comments-only clarification candidate: mark owner/downstream boundaries near the finalization/micro-smoothing tests and near helper imports from `game.final_emission_gate`.
- Possible future thinning: metadata shape checks that repeat the same default-presence expectation could potentially move behind a shared assertion helper, but only after confirming each test still owns a distinct behavior.
- Risk if modified: high. This is the clearest owner suite for visibility and referential clarity; thinning the wrong assertion would make final-gate failures harder to localize.

### Visibility sections of `tests/test_final_emission_gate.py`

- Responsibility: final-gate orchestration, route order, visibility fallback route helper importability/callability, selector snapshots, sealed branch visibility-before-N4 ordering, and final output metadata projection.
- Role: downstream/orchestration owner for how visibility plugs into final emission, not the primary owner of visibility semantics.
- Repeated assertions/metadata checks: route tags such as `visibility_enforcement_replaced`, `visibility_replacement_applied`, owner bucket fields, fallback pool/kind, order arrays, and metadata projection payload shapes.
- Protective duplication: yes where it verifies orchestration order, final emitted source snapshots, and selector distinction between visibility-specific and generic terminal replacements.
- Comments-only clarification candidate: label that these sections are final-gate integration/projection smoke and should not grow semantic visibility matrices already owned by `tests/test_final_emission_visibility.py` and `game/narration_visibility.py`.
- Possible future thinning: route helper dataclass shape tests may be candidates if `game/final_emission_visibility_fallback.py` gains/keeps direct owner tests elsewhere, but current evidence shows these tests are the only visible lock for several helper builders.
- Risk if modified: very high. `tests/test_final_emission_gate.py` is 7,967 lines and tightly coupled to a 10,636-line runtime hotspot; broad edits here can reintroduce gate ownership drag.

### `tests/test_golden_replay.py`

- Responsibility: replay-level structural invariants, scenario-spine validation, observed-turn projection, drift classification bridge, no scaffold leakage, route/speaker/fallback/final-emission metadata observation.
- Role: projection and regression coverage. It should explain drift and preserve replay-observable contracts, not own runtime legality.
- Repeated assertions/metadata checks: `route_kind`, `selected_speaker_id`, `final_emitted_source`, `fallback_family`, `opening_fallback_owner_bucket`, `trace.social_contract_trace`, scaffold leakage exclusions, and observed raw signal presence.
- Protective duplication: yes. Projection tests intentionally re-check owner bucket and prepared-emission fields because the dashboard/classifier depends on replay-shaped observations.
- Comments-only clarification candidate: add owner comments around direct final-gate calls and opening fallback projection tests to prevent treating replay projection as runtime fallback ownership.
- Possible future thinning: repeated `text_must_not_include` scaffold lists and repeated `allow_unavailable` clauses may be helperized or centralized later.
- Risk if modified: medium-high. Losing projection fields would weaken failure dashboard locality even if runtime behavior remains correct.

### `tests/test_failure_classifier.py`

- Responsibility: classification rules for replay failures, dashboard row construction, empty/one-row markdown rendering, opt-in artifact generation, precision evidence, prepared-emission owner attribution, sanitizer owner splits, and fallback bucket projections.
- Role: owner for classifier logic and diagnostic ownership mapping.
- Repeated assertions/metadata checks: `category`, `primary_owner`, `secondary_owner`, `investigate_first`, `emission_sublayer`, source-family tags, owner buckets, rejection reasons, evidence column contents.
- Protective duplication: yes. Many rows intentionally assert both classification and evidence so owner locality does not silently degrade.
- Comments-only clarification candidate: identify which tests own taxonomy behavior versus dashboard rendering smoke.
- Possible future thinning: rendering checks that duplicate contract tests could be reduced only after contract coverage is confirmed.
- Risk if modified: medium-high. Bad thinning would cause replay failures to classify to vague or wrong owners.

### `tests/test_failure_dashboard_controlled_failures.py`

- Responsibility: controlled known-bad replay-shaped probes and dashboard triage columns.
- Role: projection/smoke plus classifier behavior validation on known-bad cases; opt-in probe suite.
- Repeated assertions/metadata checks: expected `category`, `primary_owner`, `secondary_owner`, `investigate_first`, `emission_sublayer`, fallback owner buckets, sanitizer/prepared-emission evidence, route/speaker/social owners.
- Protective duplication: yes and explicitly documented in comments for opening fallback, sealed fallback, and dashboard projection locks.
- Comments-only clarification candidate: already has useful comments; possible only to label it as projection ownership, not runtime prose ownership.
- Possible future thinning: low priority; the controlled matrix is compact relative to the classifier surface and gives strong locality.
- Risk if modified: medium. Removing expected owner fields would reduce dashboard diagnostic confidence.

### `tests/test_failure_classification_contract.py`

- Responsibility: row schema/taxonomy contract, allowed categories/owners/severities/replay tags/source families/evidence fields, renderer validation, and docs coverage for taxonomy.
- Role: owner for classification contract shape.
- Repeated assertions/metadata checks: invalid field rejection, owner bucket allowed values, runtime response-type repair taxonomy, upstream prepared emission owner/source family, sanitizer strict-social split fields, post-gate mutation sublayers.
- Protective duplication: yes. The suite intentionally locks cross-layer vocabulary used by replay, classifier, and dashboard.
- Comments-only clarification candidate: comments already clarify that opening and sealed fallback owner buckets are cross-layer contract values, not deterministic prose ownership.
- Possible future thinning: unlikely now; this is small (252 lines) and high-leverage.
- Risk if modified: high. Contract drift can make dashboard rows invalid or owner labels ambiguous.

### `game/final_emission_visibility_fallback.py`

- Responsibility: visibility fallback routing helpers, dataclass payload grouping, metadata stamping, fallback owner-bucket classification, and route dispatch contexts.
- Role: helper owner for visibility fallback routing/projection; explicitly must not author fallback prose or write final output.
- Repeated assertions/metadata checks: helper tests in `tests/test_final_emission_gate.py` assert dataclass equality, metadata update order, route decisions, owner bucket classifier, no prose literals, and non-mutating route selectors.
- Protective duplication: yes, because this module is an extracted pressure-reduction surface from final gate and must remain prose-free.
- Comments-only clarification candidate: module docstring is already clear; tests could better mark direct helper ownership versus gate orchestration.
- Possible future thinning: not yet; as a pressure-relief extraction, keeping helper shape tests helps prevent logic drifting back into the gate.
- Risk if modified: medium-high. Mistakes would route visibility failures to the wrong fallback family or owner bucket.

### `game/narration_visibility.py`

- Responsibility: read-only narration visibility contract, visible/discoverable/hidden fact collection, entity alias/kind/role maps, referential candidate detection, first mention validation, referential clarity validation, visibility validation.
- Role: engine owner for visibility/referential validation semantics.
- Repeated assertions/metadata checks: downstream tests inspect validation outputs, checked entities/facts, violation kinds, first-mention offsets, and safe-harbor metadata.
- Protective duplication: yes. It owns core semantics that final-gate tests should not duplicate in full.
- Comments-only clarification candidate: no urgent change; docstring already says read-only.
- Possible future thinning: not in this file during Cycle F unless paired with direct owner tests.
- Risk if modified: very high. It is the primary semantic validator for visibility/referential clarity.

### `game/final_emission_gate.py`

- Responsibility: final emission orchestration, layer ordering, fallback selection, metadata merging, final-route tagging, visibility/first-mention/referential enforcement dispatch, strict-social replacement, interaction continuity, narrative mode output, final packaging.
- Role: runtime orchestrator and historical hotspot; still contains many direct helper functions for opening, fallback, visibility, referential clarity, and finalization.
- Repeated assertions/metadata checks: wide test coverage across `tests/test_final_emission_gate.py`, `tests/test_final_emission_visibility.py`, golden replay, classifier projection, and downstream API/start-campaign tests.
- Protective duplication: some is necessary for order and packaging. Semantic duplication remains risky because it keeps ownership gravitationally centered on the gate.
- Comments-only clarification candidate: do not edit in this task. Future comments-only work could label no-new-semantics sections, but only with human review.
- Possible future thinning: do not thin directly yet. First thin downstream tests around replay/dashboard projection and helper ownership comments.
- Risk if modified: extreme. This is the strongest repeated hotspot and was explicitly excluded from refactor in the task.

## Part 3 - Failure ownership locality

Search basis: tests for `final emission`, `visibility`, `referential`, `first mention`, `fallback`, `classifier`, `dashboard`, `owner`, `route`, `speaker`, `social`, and `NPC`.

### Tests that identify a single primary owner well

- `tests/test_failure_classification_contract.py`: strong single owner for row schema/taxonomy; explicit `primary_owner` validation and owner-bucket contracts.
- `tests/test_failure_classifier.py`: strong single owner for classifier logic; expected rows usually include `primary_owner`, `secondary_owner`, and `investigate_first`.
- `tests/test_failure_dashboard_controlled_failures.py`: strong controlled matrix; cases point to `speaker`, `fallback`, `sanitizer`, `upstream_prepared_emission`, `route`, `projection`, or `emission` with explicit first investigation target.
- `tests/test_final_emission_visibility.py`: strong semantic owner for visibility, first mention, and referential clarity behavior.
- `game/narration_visibility.py` tests via `tests/test_final_emission_visibility.py`: failures should point primarily to visibility validation semantics.
- `tests/test_golden_replay.py` projection tests for prepared emission, sanitizer fallback, opening fallback owner bucket, and strict-social sanitizer owner split: clear projection owner, but some direct final-gate calls still make runtime owner inference easy to blur.

### Tests that still create likely multi-owner fanout

- `tests/test_final_emission_gate.py`: combines helper ownership, final orchestration, visibility fallback routing, route/speaker/social layers, fallback behavior, opening fallback, N4/narrative mode, and final packaging. Failures often require reading both gate logic and extracted helpers.
- `tests/test_golden_replay.py`: intentionally spans replay observation, final gate calls, route/speaker/fallback fields, and classifier bridge. Good for drift, less good as a single-owner failure.
- `tests/test_start_campaign_api.py`: appears repeatedly in history and often couples API, data snapshots, opening/fallback behavior, and final gate output.
- Downstream social/routing tests matched by the broad search (`tests/test_answer_completeness_rules.py`, `tests/test_social_emission_quality.py`, `tests/test_prompt_and_guard.py`, transcript/regression suites) can still fan out through prompt, social, final emission, sanitizer, and fallback behavior unless owner comments are present.

### Failures likely to point to `game/final_emission_gate.py`

- `tests/test_final_emission_gate.py` order, route, final packaging, strict-social gate replacement, opening fallback, terminal fallback, visibility-before-N4, interaction-continuity gate attachment, narrative-mode output enforcement.
- `tests/test_golden_replay.py` direct-seam opening fallback and final emission structural invariant tests when observed final metadata is missing or mismatched.
- `tests/test_failure_dashboard_controlled_failures.py` fallback cases whose `investigate_first` is `game/final_emission_gate.py`, especially terminal fallback, opening fallback, visibility fallback owner bucket projection, and upstream prepared emission projection.

### Failures likely to point to visibility helper files

- `tests/test_final_emission_visibility.py` validation semantics: first check `game/narration_visibility.py`.
- `tests/test_final_emission_gate.py` helper builder/dataclass/route decision/stamping tests around `visibility_fallback`: first check `game/final_emission_visibility_fallback.py`.
- Final-gate visibility orchestration/order tests: check `game/final_emission_gate.py` only after helper semantics are ruled out.

### Failures likely to point to replay/classifier/dashboard projections

- `tests/test_golden_replay.py`: `tests/helpers/golden_replay.py` for observation/projection, then runtime only if the observation is faithful and runtime metadata changed.
- `tests/test_failure_classifier.py`: `tests/helpers/failure_classifier.py` for mapping rules; `tests/helpers/failure_dashboard_report.py` for report rendering/artifact behavior.
- `tests/test_failure_dashboard_controlled_failures.py`: controlled row setup or classifier/dashboard helper first, not runtime.
- `tests/test_failure_classification_contract.py`: `tests/failure_classification_contract.py` first for allowed taxonomy/required fields.

## Part 4 - Candidate Cycle F work blocks

### Safe now - History metric refinement

- Target files: new audit tooling or future audit doc only, not runtime/test assertions.
- Intended improvement: separate source/test fanout from tracked runtime data snapshot fanout (`data/session*.jsonl`, `data/combat.json`) so median maintenance drag is not conflated with fixture churn.
- Exact risk: low; the only risk is misclassifying a runtime fixture as generated artifact.
- Tests to run: none required for docs-only; optional `git log`/metric command rerun.
- Parallelizable: yes, with comments-only ownership mapping.

### Comments-only - Visibility ownership labels

- Target files: `tests/test_final_emission_visibility.py`, visibility sections of `tests/test_final_emission_gate.py`, possibly `tests/README_TESTS.md`.
- Intended improvement: label owner versus downstream/orchestration/projection responsibilities so future failures do not default to gate edits.
- Exact risk: low-medium; comments can become misleading if too broad or if they imply assertions can be removed.
- Tests to run: `python -m pytest tests/test_final_emission_visibility.py tests/test_final_emission_gate.py -q` only if comments touch Python files.
- Parallelizable: yes with replay/classifier comments, but avoid concurrent edits to `tests/test_final_emission_gate.py`.

### Comments-only - Replay/classifier projection labels

- Target files: `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, `tests/test_failure_classification_contract.py`.
- Intended improvement: make explicit that replay/dashboard rows own projection and diagnostic locality, not runtime fallback prose or final-gate semantics.
- Exact risk: low; comments should not soften contract intent.
- Tests to run: `python -m pytest tests/test_golden_replay.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classification_contract.py -q`.
- Parallelizable: yes, as long as only comments change.

### Possible thinning, needs human review - Repeated projection assertion helpers

- Target files: `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`.
- Intended improvement: consolidate repeated `allow_unavailable`, scaffold-exclusion, and owner/evidence row shape checks into local helpers without reducing owner signal.
- Exact risk: medium-high; helperization can hide which field is the owned signal and make failure output less local.
- Tests to run: `python -m pytest tests/test_golden_replay.py tests/test_failure_classifier.py -q`.
- Parallelizable: partly; avoid simultaneous classifier/dashboard contract edits.

### Recon only - Final gate hotspot decomposition map

- Target files: report/audit only; inspect `game/final_emission_gate.py` and `tests/test_final_emission_gate.py`.
- Intended improvement: produce a section-level map of which final-gate tests own orchestration, which are historical regression, and which should move to extracted helper owners in later cycles.
- Exact risk: low if reporting only; high if it turns into refactor work.
- Tests to run: none.
- Parallelizable: yes with metric refinement.

### Do not touch yet - Runtime final-gate refactor or direct assertion thinning

- Target files: `game/final_emission_gate.py`, broad sections of `tests/test_final_emission_gate.py`.
- Intended improvement: eventually reduce hotspot gravity and repeated gate touches.
- Exact risk: extreme; current history shows broad gate edits often fan out across production, tests, replay/classifier/dashboard, and data snapshots.
- Tests to run if ever approved: at minimum `python -m pytest tests/test_final_emission_gate.py tests/test_final_emission_visibility.py tests/test_golden_replay.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classification_contract.py -q`, plus targeted API/start-campaign tests.
- Parallelizable: no for `game/final_emission_gate.py`.

## Bottom line

Fixes are getting more explicit about ownership, but not consistently smaller yet. The median non-artifact fanout is modest at 6 files, but 11 of 30 commits still touch 8+ non-artifact files. `game/final_emission_gate.py` remains the dominant runtime hotspot, while replay/classifier/dashboard work has improved diagnostic ownership at the cost of repeated projection locks. The strongest near-term Cycle F move is not thinning assertions immediately; it is clarifying owner/projection boundaries and measuring fanout with runtime data snapshot churn separated from source/test churn.
