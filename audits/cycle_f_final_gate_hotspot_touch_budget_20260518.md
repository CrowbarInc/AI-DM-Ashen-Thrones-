# Cycle F.B Final Gate Hotspot Touch Budget - 2026-05-18

## Scope

Recon only. No runtime code, tests, comments, assertions, helpers, metadata names, or refactors were changed.

Context from Cycle F.A:

- Median true source fanout: 4.
- Commits touching 8+ true source files: 9/30.
- `game/final_emission_gate.py` touched 10/30 recent commits.
- `tests/test_final_emission_gate.py` touched 8/30 recent commits.

This audit asks why those files remain the top maintenance-drag hotspots and proposes a future touch budget.

## Part 1 - Section Map

### Runtime: `game/final_emission_gate.py`

| Lines / functions | Category | Current responsibility | Likely owner | Remain in final gate long-term? | Risk of moving | Repeat-touch pressure |
| --- | --- | --- | --- | --- | --- | --- |
| 281-545: sealed fallback providers and selectors (`_NonStrictSealedFallbackProviders`, `_select_non_strict_replace_path_terminal_sealed_fallback_selection`, `_select_non_strict_replace_path_terminal_sealed_fallback`) | sealed/strict-social handling; fallback routing | Select and assemble non-strict sealed fallback candidates via injected prose owners | Final gate for branch selection; `game/final_emission_sealed_fallback.py` / fallback prose modules for helper shape and prose | Partly. Branch selection may stay; helper assembly may belong in sealed fallback helper module | High: branch order and fallback family metadata are brittle | High: every new terminal branch tends to touch this |
| 546-1142: narration constraint debug and compact metadata builders | metadata projection; route/speaker/social continuity | Builds compact debug payloads for visibility, speaker binding, and narration constraints | `game/final_emission_meta.py` or a debug/projection helper; gate for attachment timing | Partly; projection schema could move, attachment timing stays | Medium: metadata consumers are broad | Medium-high: schema drift and debug signal additions touch gate |
| 1143-1592: tone escalation contract/effective contract/meta/repair/apply | orchestration; helper behavior that may belong elsewhere | Resolves shipped tone contracts, applies narrow repair, merges FEM/debug | Gate for layer order; tone-specific helper/validator for semantics | Mostly no for semantic repair internals; yes for layer call order | Medium-high: repair semantics can alter emitted text | Medium: new tone cases currently land here |
| 1593-2023: narrative authority contract resolution, repair, apply | orchestration; helper behavior that may belong elsewhere | Enforces narrative authority, repairs overclaims/hidden facts, records metadata | Gate for orchestration; narrative authority module/tests for semantics | Only orchestration should remain | High: semantic repair at boundary is sensitive | High: new authority rules touch gate |
| 2024-2495: anti-railroading layer | orchestration; helper behavior that may belong elsewhere | Resolves anti-railroading contract, narrow repairs, skip/apply behavior | Gate for order; anti-railroading module for validation/repair semantics | Mostly no for repair internals | Medium-high | Medium |
| 2496-2821: context separation layer | orchestration; helper behavior that may belong elsewhere | Resolves context separation, repairs pressure bleed, merges metadata | Gate for order; context separation module for semantics | Mostly no for repair internals | Medium-high | Medium |
| 2822-3466: player-facing narration purity and answer-shape primacy | orchestration; packaging/final output; helper behavior that may belong elsewhere | Resolves contracts, repairs scaffold/coaching/pressure-only output, merges fallback/conversation memory metadata | Gate for final sequencing; validators/repairs for text semantics | Mixed; final order stays, repair internals should migrate only with strong tests | High: text mutation rules are hard to localize | High |
| 3467-3807: scene state anchor layer and repairs | orchestration; helper behavior that may belong elsewhere | Resolves scene-state anchor contract, applies minimal repairs, merges metadata | Gate for order; `scene_state_anchoring` owner for semantics | Mostly no for repair internals | High: opening and transition language are fragile | Medium-high |
| 3808-4281: upstream prepared emission and opening fallback helpers (`_opening_*`, `validate_opening_output`, `_opening_scene_safe_fallback_tuple`) | opening fallback; fallback routing | Validates opening shape, selects upstream prepared fallback, handles fail-closed sealed behavior | Gate currently; possible future opening fallback helper owner | Some orchestration remains; validation/composition should likely leave | Very high: opening regressions are common and user-visible | Very high |
| 4282-4921: response type contract enforcement and sentence smoothing/decompression | packaging/final output; helper behavior that may belong elsewhere | Enforces response type, repairs fragments/overpacked sentences, gates candidate shape | Gate for response-type decision; `final_emission_validators.py` / `final_emission_repairs.py` for helpers | Mixed | High: changes can rewrite player text | High |
| 4922-5234: fast path, upstream fallback containment, finalization, route-illegal stock strip | packaging/final output; metadata projection | Final packaging, mutation lineage, overwrite containment, route-illegal contamination strip | Final gate | Yes, mostly | High: last-mile output owner | High |
| 5235-5511: strict-social/basic fallback text helpers and fast fallback neutral composition | sealed/strict-social handling; fallback routing | Builds strict/social fallback labels and neutral opening fallback composition | Gate now; `diegetic_fallback_narration.py` / fallback helpers for prose | Mixed; prose/composition should not grow here | Medium-high | Medium-high |
| 5512-6610: visible scene facts, runtime leads, composed scene intro, grounded scene intro fallback | visibility/referential integration; opening fallback; helper behavior that may belong elsewhere | Builds visibility-safe scene fallback candidates and first-mention composition | Gate currently; `game/narration_visibility.py` for legality, visibility fallback helper for routing, possible opening composition helper | Probably not long-term except selection hook | Very high | Very high |
| 6634-6906: strict-social referential local substitution helpers and default referential metadata | visibility/referential integration; sealed/strict-social handling | Determines when a local strict-social pronoun substitution can avoid hard fallback | Gate for strict-social integration; `narration_visibility.py` for legality | Mixed | Very high: semantic mutation at final boundary | High |
| 6928-7376: scene emit integrity, standard visibility safe fallback | visibility/referential integration; fallback routing | Computes scene emit integrity and selects visibility-safe/global/opening fallback | Gate for routing; helper modules for computation/projection | Mixed | High | High |
| 7377-7905: `_apply_first_mention_enforcement`, `_apply_referential_clarity_enforcement`, `_apply_visibility_enforcement` | visibility/referential integration; orchestration | Calls validators, selects fallback/substitution, stamps metadata, routes final replacement | Final gate for sequencing and final replacement; `game/narration_visibility.py` for legality; `game/final_emission_visibility_fallback.py` for routing/payloads | Yes for orchestration; no for growing legality matrices | Very high | Very high |
| 7906-8579: interaction continuity and speaker bridge (`_apply_interaction_continuity_emission_step`, `enforce_emitted_speaker_with_contract`, `_apply_referent_clarity_pre_finalize`) | route/speaker/social continuity | Bridges emitted speaker/continuity contracts into final output and FEM | Gate for final attachment/order; `speaker_contract_enforcement.py`, interaction continuity modules for semantics | Mixed | High | High |
| 8581-8929: narrative mode output, acceptance quality N4 seam, scene opening reassertion/observability | orchestration; metadata projection; opening fallback | Applies narrative mode output floor, N4 acceptance quality, scene-opening candidate reassertion | Gate for order and final replacement; AQ/NMO modules for semantics | Mixed | High | Medium-high |
| 8945-10636: `apply_final_emission_gate` main entry | orchestration; packaging/final output; fallback routing | Wires all layers, chooses accept/replace path, stamps final metadata/tags/trace | Final gate | Yes | Extreme | Extreme |

Runtime summary: `game/final_emission_gate.py` is a hotspot because it owns final sequencing and replacement, but it also still contains many layer-specific semantic helpers. Repeat touches come from both legitimate gate orchestration and helper behavior that may eventually deserve stronger direct ownership outside the gate.

### Tests: `tests/test_final_emission_gate.py`

| Lines / tests | Category | Current responsibility | Likely owner | Remain in final gate long-term? | Risk of moving | Repeat-touch pressure |
| --- | --- | --- | --- | --- | --- | --- |
| 14-506: acceptance quality N4 practical owner suite | orchestration; metadata projection | Verifies N4 gate seam ordering, repair/replace FEM shape, disabled/default contract behavior | Gate for seam/order; AQ module for semantics | Mostly yes for seam tests | Medium | Medium |
| 507-1269: interaction continuity, referent pre-finalize, response delta, speaker enforcement order | route/speaker/social continuity; metadata projection | Locks final-gate interaction continuity attachment, speaker bridge metadata, layer order, mutation taxonomy | Gate for order/projection; speaker/IC modules for semantics | Partly | High | High |
| 1270-1506: Block E strict-social referential substitution | visibility/referential integration; sealed/strict-social handling | Ensures strict-social local referential substitution is fenced, skipped, and metadata-visible | Gate for strict-social integration; `tests/test_final_emission_visibility.py` for legality | Partly | High | High |
| 1507-1780: Block F speaker repair and scene-state anchor ordering | route/speaker/social continuity; historical regression lock | Guards speaker enforcement invocation boundaries and metadata taxonomy | Gate for order; speaker enforcement module for semantics | Partly | Medium-high | Medium |
| 1780-2493: scene state anchor tests | helper behavior that may belong elsewhere; orchestration | Checks repair variants, metadata, skip reasons, contract resolution, no upstream builder calls | Mixed; direct scene-state owner should own repair semantics | Some should move only after owner exists | High | Medium-high |
| 2494-3008: narration constraint debug tests | metadata projection | Verifies compact debug shape, null safety, missing/sensitive input omission, metadata surfacing | Projection/debug owner; gate for surfacing | Maybe projection helper owner long-term | Medium | Medium |
| 3009-3738: narrative authority, anti-railroading, context separation | helper behavior that may belong elsewhere; orchestration | Locks contract resolution, skip/apply behavior, narrow repairs, order around scene-state anchor | Gate for layer order; each policy module for semantics | Mixed | High | High |
| 3739-4636: purity, answer shape, opening validator/fallback, upstream prepared emission | opening fallback; packaging/final output; fallback routing | Checks opening validation, deterministic/upstream fallback, fail-closed paths, final emitted family/source | Gate for final replacement; opening/fallback helpers for semantics | Mixed; opening cluster creates high drag | Very high | Very high |
| 4637-4936: terminal repair, visibility safe fallback, sealed branch selector/order snapshots | visibility/referential integration; sealed handling; metadata projection | Distinguishes visibility, N4, opening RT, strict-social, and generic terminal replacement branches | Gate for branch/order/projection | Yes, but should stay thin | High | High |
| 4937-6709: Block AI final gate reduction contract guards and extracted helper tests | helper behavior that may belong elsewhere; fallback routing; visibility/referential integration | Verifies extracted visibility/sealed fallback helpers, no prose literals, payload shapes, non-mutating selectors, injected prose owners | Helper module owner tests, currently staged in gate test file | Long-term no for many helper shape tests | Medium-high | Very high until moved |
| 6711-7117: additional opening fallback and curated facts tests | opening fallback; historical regression lock | Locks opening curated fact source preference, fail-closed sealed metadata, polluted fact avoidance | Gate currently; opening fallback owner could absorb some | Mixed | High | Very high |
| 7166-7391: purity and answer-shape primacy integration | packaging/final output; helper behavior that may belong elsewhere | Verifies purity/ASP pass/repair/replace at gate boundary | Gate for integration; purity/ASP helpers for semantics | Mixed | High | Medium-high |
| 7392-7736: social response structure downstream integration | route/speaker/social continuity; orchestration | Ensures SRS ordering, skip paths, metadata merge, strict/non-strict replacement behavior | Gate for order/projection; social response module for semantics | Partly | Medium-high | Medium |
| 7737-7819: appended global-visibility stock / finalization strip | packaging/final output; historical regression lock | Last-mile owner is `_finalize_emission_output`; strips appended stock after containment | Final gate | Yes | High | Medium |
| 7821-7967: narrative mode output tests | orchestration; metadata projection; sealed/strict-social handling | Checks NMO shipped contract enforcement, skip reasons, replacement route, strict-social terminal fallback | Gate for seam/order; NMO module for semantics | Partly | High | Medium |

Test summary: `tests/test_final_emission_gate.py` remains hot because it is both the integration suite and a holding area for direct helper tests that were extracted from the gate. That is safer than losing coverage, but it keeps helper ownership psychologically and mechanically tied to final gate.

## Part 2 - Recent Touch Reason Analysis

Scope: last 30 commits that touched either `game/final_emission_gate.py` or `tests/test_final_emission_gate.py`.

| SHA | Title | Gate file touched | Gate test touched | Likely reason | Category |
| --- | --- | --- | --- | --- | --- |
| 8ddb183 | E: Test Signal Ownership Thinning | No | Yes | Test signal thinning / ownership comments around fallback-family tests | cleanup/comments |
| 6c00e6e | D: Final Emission Gate Pressure Reduction | Yes | Yes | Extracted/separated sealed and visibility fallback helpers; updated replay/classifier projections | fallback ownership |
| a5c9146 | Cycle C: contract fallback ownership and mutation lineage | Yes | Yes | Contract fallback owner buckets and mutation lineage projection | fallback ownership |
| c89f2f4 | Complete Gate Convergence, Semantic Fencing, and Relocation Readiness Hardening | Yes | Yes | Gate convergence, speaker relocation readiness, semantic fencing | route/speaker/social integration |
| 0f03dd6 | Gate Boundary Convergence and Compatibility Fencing | Yes | Yes | Boundary contract and compatibility fencing around validators/response policy | broad refactor |
| 0f80564 | Realization Layer Failure-Locality Hardening | Yes | Yes | Failure-locality work across realization, gate, validators, GM, response repairs | broad refactor |
| 673118e | PLANNER: Stabilize Failure Locality Seam | Yes | No | Planner/final-emission seam stabilization and metadata/validator integration | broad refactor |
| 773cbe0 | Promote accepted scene opening candidates | Yes | Yes | Accepted opening candidate promotion before fallback | opening fallback |
| c6e63b0 | Refresh session snapshot and opening scene details | Yes | No | Opening scene details and API/gate alignment | opening fallback |
| 1b3b3ee | Preserve valid scene openings before deterministic fallback | Yes | Yes | Regression lock for valid openings not being replaced | regression lock |
| 9e83820 | Preserve journal openings through selector fallback | Yes | No | Opening selector fallback path via API/gate | opening fallback |
| d6bad74 | Enforce curated opening facts in fallback | Yes | Yes | Opening fallback curated fact enforcement | opening fallback |
| 6351b33 | Preserve curated opening facts through fallback | Yes | Yes | Curated opening facts through fallback plus final emission metadata/text/validators | opening fallback |
| f79b713 | Canon vs Runtime | Yes | Yes | Runtime/canon split across API, GM, social continuity, final emission | broad refactor |
| a6573c7 | Cleanup (IV) | No | Yes | Test cleanup | cleanup/comments |
| ca576ad | Cleanup (I) | Yes | Yes | Cleanup touching gate/social exchange/tests | cleanup/comments |
| 1caa404 | Answer / Exposition Convergence | Yes | No | Answer/exposition contract convergence across boundary/repairs/validators | new behavior |
| 7d4c11d | Dialogue / Social Convergence | Yes | No | Dialogue social plan integration through GM/final emission | route/speaker/social integration |
| 4bbecf9 | Final-Emission Debt Retirement | Yes | No | Debt retirement and extracted contract/repairs/validators/meta | broad refactor |
| 02ab9b0 | Final Emission Boundary Hardening | Yes | Yes | Boundary hardening, no-semantic-repair constraints, repairs/meta | broad refactor |
| 1b4980d | Acceptance Quality Layer (Anti-Collapse / Playability Gate) | Yes | Yes | New acceptance-quality N4 layer and FEM tests | new behavior |
| d5bc6e6 | Narrative Mode Enforcement (Hard Contract) | Yes | Yes | New narrative mode output enforcement and metadata | new behavior |
| 335926e | Final Emission Ownership Convergence | Yes | Yes | Ownership convergence across API, gate, repairs, validators, visibility tests | broad refactor |
| d9488cd | Telemetry Normalization | Yes | No | FEM/debug telemetry normalization | projection/metadata update |
| 9b5ffa0 | Mini-Consolidation Pass | Yes | No | Consolidation around final emission meta/gate | broad refactor |
| c4b8cb5 | Validation Layer Separation (Hard Rule) | Yes | No | Validation-layer separation across gate/meta/repairs | broad refactor |
| 0ad6541 | Clause / Referent Tracking Layer | Yes | Yes | Referent tracking integration with gate/repairs/validators | visibility/referential integration |
| 4782a71 | Public vs Debug vs Author State Separation | Yes | Yes | Public/debug separation across GM, metadata, post-emission adoption, visibility tests | broad refactor |
| 0ccff41 | Architecture Audit [VIII] | No | Yes | Test/audit ownership cleanup | cleanup/comments |
| 7ca4702 | Architecture Audit [VII] | No | Yes | Architecture ownership cleanup touching gate tests | cleanup/comments |

### Touch reason summary

Approximate dominant categories:

- Broad refactor / convergence: 10 commits.
- Opening fallback: 5 commits.
- Cleanup/comments/test ownership: 5 commits.
- New behavior/layers: 3 commits.
- Route/speaker/social integration: 2 commits.
- Fallback ownership: 2 commits.
- Projection/metadata update: 1 commit.
- Visibility/referential integration: 1 commit.
- Regression lock: 1 commit.

### Legitimate gate ownership

These touches were mostly legitimate because the gate is the final sequencer and final-output owner:

- New policy/layer insertion: acceptance quality, narrative mode output, answer/exposition convergence.
- Layer ordering and final replacement routing.
- Final metadata/tag/trace projection when it is produced by final output decisions.
- Strict-social versus non-strict branch selection.
- Last-mile packaging and post-gate containment.
- Regression locks proving valid opening candidates are not replaced.

### Missing helper/test ownership elsewhere

These touch reasons suggest helper/test ownership could be stronger outside `tests/test_final_emission_gate.py`:

- Visibility fallback helper payload/dataclass/metadata shape tests now live in the gate test file even though `game/final_emission_visibility_fallback.py` exists.
- Opening fallback composition and curated-fact selection still have many direct gate tests; a dedicated opening fallback owner could reduce gate-test pressure.
- Policy-layer semantic repair tests for narrative authority, anti-railroading, context separation, purity, answer-shape primacy, and scene-state anchor are intermixed with gate order tests.
- Debug/projection schema helpers are tested in the gate file rather than a projection/meta helper suite.

### Over-centralization signals

- `game/final_emission_gate.py` combines orchestration with many layer-specific repair and composition helpers.
- `tests/test_final_emission_gate.py` combines final-gate integration, helper module direct tests, semantic policy tests, projection schema checks, and historical regression locks.
- Opening fallback and visibility/referential integration create repeated touch pressure because failures often need both routing/projection and semantic/fallback candidate reasoning.
- Broad refactor commits repeatedly include `game/final_emission_gate.py`, `game/final_emission_meta.py`, `game/final_emission_validators.py`, and `tests/test_final_emission_gate.py`, showing the boundary is improving but still not fully owned.

## Part 3 - Touch Budget Proposal

### When touching `game/final_emission_gate.py` is justified

Touch the runtime gate only when the change is about:

- Final layer ordering in `apply_final_emission_gate`.
- Accept/replace path selection.
- Final emitted text assignment, final tags, final route, or mutation lineage.
- Dispatch into already-owned helper/validator modules.
- Final metadata merge timing where the gate is the only place all signals meet.
- Strict-social versus non-strict branch orchestration.
- Last-mile packaging/containment after all upstream layers run.

Avoid touching the runtime gate when the change is primarily:

- Visibility legality semantics.
- First-mention or referential-clarity legality matrices.
- Helper dataclass shape or payload construction.
- Failure dashboard taxonomy.
- Replay observation projection.
- Pure metadata constants/accessors.
- GM/API route selection before final emission.
- Prose/fallback line authorship.

### Routing table

| Symptom / failure type | Investigate first | Touch final gate? | Notes |
| --- | --- | --- | --- |
| Visibility legality wrong: unseen NPC, hidden fact, discoverable fact, first mention, ambiguous pronoun | `game/narration_visibility.py`; `tests/test_final_emission_visibility.py` | Usually no | Gate should only route enforcement and stamp results. |
| Visibility fallback route chooses wrong owner bucket/pool/kind | `game/final_emission_visibility_fallback.py`; relevant helper tests | Maybe | Touch gate only if dispatch order or selected fallback wiring is wrong. |
| Visibility replacement happens before/after wrong final layer | `game/final_emission_gate.py`; `tests/test_final_emission_gate.py` | Yes | Ordering is legitimate gate ownership. |
| `visibility_*` metadata missing from replay/dashboard row | `tests/helpers/golden_replay.py`; `tests/helpers/failure_classifier.py`; `tests/helpers/failure_dashboard_report.py` | Rarely | If FEM metadata is present but projection missing, do not touch gate. |
| Final route/tag/final emitted source wrong after accept/replace | `game/final_emission_gate.py` | Yes | This is core gate ownership. |
| Final metadata constant/accessor drift | `game/final_emission_meta.py`; `tests/test_final_emission_meta.py` | Rarely | Gate only if merge timing is wrong. |
| Candidate validation predicate wrong | `game/final_emission_validators.py`; boundary tests | Rarely | Gate should call validators, not own new validator logic. |
| Text repair helper wrong or too broad | `game/final_emission_repairs.py`; repair tests | Rarely | Gate only if repair is invoked in wrong phase. |
| Opening fallback prose/curated fact composition wrong | Opening fallback helper/selector tests; currently gate tests until owner exists | Maybe | High-pressure area. Prefer recon/comments before moving. |
| Opening valid candidate replaced incorrectly | `game/final_emission_gate.py`; opening fallback tests | Yes | Accept/replace gating is legitimate. |
| Strict-social fallback selected on wrong path | `game/final_emission_gate.py`; strict-social emission tests | Yes | Branch selection is gate-owned. |
| Strict-social prose/content is poor | `game/social_exchange_emission.py`; strict-social prose owner tests | Usually no | Gate should not become prose owner. |
| Speaker attribution or emitted speaker contract wrong | `game/speaker_contract_enforcement.py`; social/speaker tests | Maybe | Gate only for final enforcement timing/attachment. |
| Route kind / selected speaker wrong before emission | `game/gm.py`, `game/api.py`, interaction/social routing modules | Usually no | Gate consumes route/speaker outputs unless final enforcement changes them. |
| Golden replay observation field missing/wrong | `tests/test_golden_replay.py`; `tests/helpers/golden_replay.py` | Rarely | Touch gate only if runtime FEM truly lacks the signal. |
| Failure classifier assigns wrong owner/investigation target | `tests/helpers/failure_classifier.py`; `tests/test_failure_classifier.py` | No | Classification is diagnostic projection. |
| Dashboard markdown missing evidence/column | `tests/helpers/failure_dashboard_report.py`; dashboard tests | No | Report rendering is not gate-owned. |
| Failure classification taxonomy rejects/accepts wrong label | `tests/failure_classification_contract.py`; `tests/test_failure_classification_contract.py` | No | Contract-only. |
| GM output shape or upstream prepared payload absent | `game/gm.py`, `game/api.py`, upstream response repair helpers | Maybe | Gate only if final attach/recovery is wrong. |
| Last-mile scaffold/stock phrase remains after finalization | `game/final_emission_gate.py` | Yes | `_finalize_emission_output` is final packaging owner. |

## Part 4 - Next Block Recommendations

### Safe now - Gate Touch Budget Doc Linkage

- Label: Safe now.
- Target files: audit/docs only, possibly `docs/current_focus.md` or a future ownership note document.
- Intended drag reduction: make the touch budget visible before future final-gate edits.
- Risk: low; docs can become stale.
- Tests to run: none for audit/docs-only.
- Parallelizable: yes.

### Comments-only - Gate Test Cluster Headers

- Label: Comments-only.
- Target files: `tests/test_final_emission_gate.py`.
- Intended drag reduction: label clusters as orchestration, projection, helper-owner, historical regression, or semantic-policy coverage so future edits choose the right owner first.
- Risk: medium because misleading comments in this file could steer future changes badly.
- Tests to run: `python -m pytest tests/test_final_emission_gate.py -q`.
- Parallelizable: no if another block touches the same file.

### Recon only - Opening Fallback Owner Map

- Label: Recon only.
- Target files: audit only; inspect `game/final_emission_gate.py`, `tests/test_final_emission_gate.py`, opening fallback related tests/helpers.
- Intended drag reduction: identify whether opening fallback composition/curated-fact selection can have a direct owner outside the gate.
- Risk: low if reporting only; high if it turns into extraction without review.
- Tests to run: none.
- Parallelizable: yes.

### Possible helper extraction, needs human review - Visibility Fallback Helper Test Relocation

- Label: Possible helper extraction, needs human review.
- Target files: likely a new or existing direct-owner test file for `game/final_emission_visibility_fallback.py`; current source is `tests/test_final_emission_gate.py` Block AI helper tests.
- Intended drag reduction: remove helper-shape pressure from the gate test file while preserving projection/route confidence.
- Risk: medium-high; moving tests can weaken perceived gate coverage or lose order/projection signal.
- Tests to run: `python -m pytest tests/test_final_emission_gate.py tests/test_final_emission_visibility.py -q`.
- Parallelizable: not with other edits to the same gate test cluster.

### Do not touch yet - Runtime Gate Decomposition

- Label: Do not touch yet.
- Target files: `game/final_emission_gate.py`.
- Intended drag reduction: eventually move layer-specific semantic helpers out of the final gate.
- Risk: extreme; this file owns final sequencing and emitted output, and broad refactors historically create high fanout.
- Tests to run if ever approved: at minimum `python -m pytest tests/test_final_emission_gate.py tests/test_final_emission_visibility.py tests/test_golden_replay.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py tests/test_failure_classification_contract.py -q`, plus targeted API/start-campaign and social/speaker suites.
- Parallelizable: no.

## Bottom Line

Final gate touches are not mostly frivolous. Many are legitimate because the gate owns final sequencing, final emitted output, replacement routing, and metadata merge timing. The over-centralization problem is that too many semantic helpers and direct helper tests still live in or near the gate, especially around opening fallback, visibility/referential enforcement, and policy-layer repairs. The safest next block is comments-only cluster labeling in `tests/test_final_emission_gate.py`, followed by recon on opening fallback ownership before any helper extraction is attempted.
