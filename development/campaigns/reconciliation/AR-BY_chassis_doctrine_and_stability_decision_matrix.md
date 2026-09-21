# AR-BY - Chassis Doctrine and Stability Decision Matrix

Campaign: Campaign 6 - Chassis Strategy

Scope: doctrine conversion from AR-BX evidence. This cycle does not redesign architecture, repeat repository discovery, move packages, or change runtime behavior.

## 1. Executive Summary

Ashen Thrones now has a stable long-term architectural chassis. Campaigns 1-5 recovered and operationalized the architecture; AR-BX confirmed that repository structure, executable contracts, tests, and current doctrine consistently reinforce the same dependency direction.

The long-term posture is conservative: foundational architecture should be treated as settled, and future work should attach through known owners and contracts. Architectural change now requires specific evidence of a product need, recurring coordination cost, unresolved contradiction, or executable limitation. Mere availability of a cleaner abstraction is not sufficient.

Permanent doctrine centers on one runtime transaction spine, deterministic domain simulation, explicit state authority, CTIR resolved-turn meaning, prompt/adaptation as a consumer of truth, backend/model expression as non-authoritative realization, Final Emission as last-mile legality and packaging, persistence as document storage, replay/projection/evidence as observational, provenance as explanation rather than selection, and governance as doctrine/test stewardship rather than gameplay execution.

Official extension mechanisms are likewise bounded: ordinary gameplay extends through domain owners and state authority; backend work extends through model routing/backend adapter contracts; ruleset work extends through action/schema/mechanics/state/identity contracts; replay/provenance/diagnostics extend through read-side registries and producer-owned metadata; content extends through validation and schema surfaces. Internal helper families remain internal.

No major architectural campaign appears necessary before controlled feature expansion. Remaining architectural work is optional and product-triggered: public tooling facade, player-safe provenance redaction, saved-campaign migration policy, executable backend/ruleset registries, or multi-provider/multi-ruleset support.

## 2. Permanent Architectural Doctrine

| Architectural Boundary | Decision | Rationale | Supporting Evidence |
|---|---|---|---|
| Runtime transaction spine | Confirm as permanent doctrine. | A turn has one orchestration spine; delegates may be extracted only if `game/api.py` retains transaction order authority. | AR-BX Stable Boundary Candidates: runtime transaction order; AR-BI permanent doctrine and canonical dependency model; `docs/feature_lane_verification.md` ordinary gameplay lane. |
| Domain simulation owns game truth | Confirm as permanent doctrine. | Mechanics outcomes must be resolved by engine/domain modules before narration, prompt, Final Emission, replay, or governance observes them. | AR-BX: domain simulation owns mechanics truth; AR-BI doctrine items 2 and 15; `docs/ruleset_contract_registry.md` RCR-04/RCR-05/RCR-07. |
| State authority governs mutation/read boundaries | Confirm as permanent doctrine. | State ownership must remain explicit, inspectable, and guarded; model output must not mutate runtime truth. | AR-BX: state authority registry/guards; `game/state_authority.py`; `docs/architecture_ownership_ledger.md`; `docs/ruleset_contract_registry.md` RCR-08. |
| CTIR owns resolved-turn meaning | Confirm as permanent doctrine. | CTIR is the canonical post-resolution, pre-prompt meaning object; prompt and turn packet are consumers, not alternate semantic authorities. | AR-BX: CTIR resolved-turn meaning; AR-BI doctrine item 4; ownership ledger CTIR section. |
| Prompt/adaptation packages approved truth | Confirm as permanent doctrine. | Prompt construction adapts CTIR/state/contracts for expression and must not decide mechanics, validation verdicts, or final legality. | AR-BX: prompt/adaptation; ownership ledger Prompt Contracts; backend registry BCR-04. |
| Response policy contracts ship policy shape | Confirm as permanent doctrine. | Response policy contracts define shape/resolution helpers; validators, repairs, gate order, and FEM packaging remain separate owners. | AR-BX: response policy contracts; ownership ledger Response Policy Contracts; `docs/feature_lane_verification.md`. |
| Model routing is deterministic route selection | Confirm as permanent doctrine. | Route selection is explicit, diagnostic, and separate from provider invocation, prompt content, domain mechanics, replay acceptance, and provenance authority. | AR-BX: model routing; backend registry BCR-01/BCR-02/BCR-08; AR-BI permanent boundary inventory. |
| Backend/model I/O produces candidate expression only | Confirm as long-term doctrine for the current provider and future adapters. | Backend output is not domain truth; future providers must normalize request/response/error shapes behind backend boundaries. | AR-BX: backend call adapter; backend registry BCR-03/BCR-05; AR-BI doctrine item 6. |
| Final Emission owns last-mile legality, sealing, selection, packaging, and traceability | Confirm as permanent doctrine. | Final Emission is a durable boundary; semantic repair residue is managed drift-watch, not evidence for redesign. | AR-BX: Final Emission boundary; AR-BI doctrine item 8; AR-BF; ownership ledger Final Emission sections. |
| Validators predicate; repairs mutate only within bounded authority; sanitizers strip/package/drop | Confirm as permanent doctrine. | These are distinct owner responsibilities, not interchangeable policy or extension layers. | AR-BX: validators vs repairs vs sanitizers; AR-BD vocabulary; ownership ledger. |
| Fallback has split ownership and governed provenance | Confirm as permanent doctrine. | Fallback content, selection, application, provenance, and observation must stay traceable and must not collapse into a single ungoverned authority. | AR-BX: fallback/provenance classification; AR-BI fallback boundary; version/provenance registry VPCR-03/06. |
| Persistence owns envelopes/storage mechanics, not gameplay semantics | Confirm as permanent doctrine. | Persistence stores versioned runtime documents and compatibility-normalized payloads; it does not decide ruleset behavior or replay authority. | AR-BX: persistence envelope; `game/persistence_contract.py`; `docs/runtime_persistence_envelope.md`; AR-BI. |
| Replay/projection/evidence observe finalized runtime surfaces | Confirm as permanent doctrine. | Replay acceptance and diagnostic projection must remain downstream; runtime must not depend on protected replay structures. | AR-BX: replay/projection observes runtime; version/provenance registry VPCR-01/02/11; `tests/README_TESTS.md` gate/replay governance. |
| Provenance explains behavior; it does not select behavior | Confirm as permanent doctrine. | Provenance is evidence and lineage, not a behavior dispatch mechanism. | AR-BX: provenance explains behavior; `docs/feature_lane_verification.md`; version/provenance registry VPCR-03/04/05/06. |
| Diagnostics and telemetry are explanatory read-side surfaces unless explicitly runtime-packaged | Confirm as permanent doctrine. | Diagnostics may summarize runtime behavior but must not become hidden policy engines. | AR-BX: diagnostics/lineage/evidence; AR-BI diagnostics/telemetry boundary; ownership ledger Stage Diff Telemetry. |
| Governance declares doctrine, tests ownership, and watches drift | Confirm as permanent doctrine. | Governance is not gameplay execution; direct-owner tests and workflows preserve architecture. | AR-BX: governance declares/watches; AR-BW governance clarity; `docs/governance_refresh_workflow.md`; `tests/README_TESTS.md`. |
| Compatibility residue is managed evidence, not co-equal ownership | Confirm as permanent doctrine. | Legacy paths remain supported only through compatibility evidence and retirement packages. | AR-BX: compatibility residue; AR-BI doctrine item 14; `docs/compatibility_residue_register.md`; AR-BW risks. |
| Local UI/product projection consumes API/runtime truth | Confirm as stable local doctrine. | UI may grow locally but must not become state authority, replay authority, or Final Emission mutator. | AR-BX feature trace for richer UI; AR-BI UI/tooling projection row. |

## 3. Official Extension Strategy

| Extension Point | Classification | Intended Usage | Ownership | Expected Stability |
|---|---|---|---|---|
| Domain owner plus API wiring | Primary Extension Point | Ordinary gameplay systems, world-state behavior, mechanics, domain state changes. | Domain modules, `game/api.py` for transaction order, `game/state_authority.py` for state boundaries. | Indefinite. This is the default feature path. |
| State authority registry/guards | Primary Extension Point | New domains, mutators, read permissions, and explicit cross-domain write seams when genuinely required. | `game/state_authority.py`; direct-owner tests. | Indefinite, with conservative change review. |
| Action/schema/content validation | Primary Extension Point | New action types, content packages, scene fields, affordances, import/normalization surfaces. | `game/scene_actions.py`, `game/schema_contracts.py`, `game/validation.py`, `game/affordances.py`. | Indefinite for content/gameplay growth. |
| Non-combat framework | Primary Extension Point | New non-combat kinds or materially changed domain policies that need normalized resolved-turn outcomes. | `game/noncombat_resolution.py` plus CTIR/prompt consumers. | Stable but version-sensitive. |
| Response policy contracts | Secondary Extension Point | New response-shape contracts shipped to prompt/Final Emission consumers. | `game/response_policy_contracts.py`. | Stable; additions require direct-owner tests. |
| CTIR slices and projection | Secondary Extension Point | New resolved-turn meaning fields consumed by prompt, replay, diagnostics, or tools. | `game/ctir.py`, `game/ctir_runtime.py`, CTIR owner tests. | Stable; extend cautiously. |
| Model routing | Secondary Extension Point | New deterministic model lanes or escalation policies. | `game/model_routing.py`, `game/config.py`, backend registry BCR-01/BCR-02. | Stable; diagnostics remain non-authoritative. |
| Backend adapter/provider boundary | Future Only | Additional providers, local inference, fake backend tests, provider error normalization. | Future backend adapter owner; current substrate is `game/gm.py::call_gpt`, model routing, preflight, run gate. | Stable as a target; executable multi-provider support is future implementation. |
| Upstream preflight/run gate | Specialized Extension Point | Provider health rows and operator-facing live-run validity. | `game/api_upstream_preflight.py`, `game/upstream_dependent_run_gate.py`. | Stable; not replay policy. |
| Ruleset identity/capability contract | Future Only | Alternate ruleset identity, version, family, capability, and compatibility publication. | Future ruleset contract owner; current substrate in ruleset registry and domain contracts. | Stable as a target; executable alternate-ruleset support is future implementation. |
| Persistence envelope/document kinds | Specialized Extension Point | New persisted document kinds, explicit version checks, saved-runtime compatibility. | `game/persistence_contract.py`, storage owners. | Stable; migration policy may evolve deliberately. |
| Protected replay observation registry | Specialized Extension Point | New protected fields/scenarios and generated manifest updates. | Protected replay/golden projection test helpers and manifest tooling. | Stable for verification; runtime must not depend on it. |
| Runtime provenance and FEM metadata | Specialized Extension Point | New producer-owned provenance keys, fallback-family taxonomy changes, runtime lineage fields. | `game/realization_provenance.py`, `game/final_emission_meta.py`, runtime lineage owners. | Stable; changes are replay-sensitive. |
| Diagnostics/report tooling | Specialized Extension Point | New read-side inspection, recurrence, stability, failure dashboard, or debugging outputs. | `tools/`, `tests/helpers/`, projection owners, generated-doc governance. | Stable as observational tooling. |
| Compatibility residue register | Specialized Extension Point | Adding, classifying, or retiring compatibility surfaces through evidence. | `docs/compatibility_residue_register.md` and owning implementation/tests. | Stable planning surface; retirement requires package approval. |
| Generic plugin framework | Internal Only / Not Approved | Not an official extension strategy. | No owner. | Revisit only with concrete product requirements and evidence. |
| Final Emission helper internals | Internal Only | No external attachment; use owner contracts rather than private preflight/repair/sanitizer helpers. | Final Emission owner modules. | Permanently internal unless a future package proves a real API need. |

## 4. Internal Architectural Boundaries

| Internal Area | Why It Remains Internal | Risk if Exposed | Recommendation |
|---|---|---|---|
| Final Emission preflight helpers | They support one gate ordering contract and are not independent policy surfaces. | External callers would freeze helper order and recreate split gate ownership. | Permanently internal; document as owner-scoped implementation. |
| Final Emission repair helpers | Repairs are bounded legality/packaging mechanisms with drift-watch residue. | They could become unauthorized content synthesis or semantic rewrite APIs. | Permanently internal; use boundary taxonomy and direct-owner tests. |
| Sanitizers/output scrubbing | Sanitizers strip/package/drop illegal output artifacts. | External use could turn them into ad hoc semantic mutation layers. | Permanently internal except through owning Final Emission paths. |
| Fallback internals | Fallback has split content/selection/application/provenance/observer ownership. | Ungoverned fallback extension would break provenance and replay observability. | Permanently internal; add fallback only through owner-reviewed packages. |
| Replay/projection helper internals | Projection observes finalized runtime surfaces. | Runtime dependency on projection would invert the architecture. | Keep runtime independent; expose only test/tool contracts. |
| Compatibility adapters | They preserve legacy callers/payloads under explicit evidence. | New work could hide behind legacy shims instead of owner contracts. | Keep compatibility scoped; retire only through compatibility packages. |
| Contract metadata registry internals | `game/contract_registry.py` is metadata-only. | Treating metadata rows as enforcement would move behavior into a non-runtime registry. | Keep metadata-only; do not publish runtime behavior from it. |
| Governance guard helpers | They enforce known ownership boundaries in tests. | Feature logic could leak into test support, making governance brittle and circular. | Keep test-only and import-light. |
| Evidence/report scripts | They generate read-side evidence, not runtime behavior. | Generated evidence could become duplicated manual doctrine or runtime dependency. | Keep observational; follow generated-doc governance. |
| UI projection helpers | They serve local API/UI visibility policy. | External tooling could couple to raw internal shapes before a facade exists. | Treat as local product surface; public facade requires separate decision. |
| Test fixtures/helpers | They provide verification mechanics. | Production use would collapse test/runtime separation. | Keep test-only. |

No AR-BX evidence supports publishing new public APIs for these internal areas.

## 5. Architecture vs Implementation Matrix

| Future Work Area | Implementation | Local Evolution | Major Architecture | Notes |
|---|---:|---:|---:|---|
| Ordinary gameplay subsystem | X |  |  | Attach through domain owner, state authority, CTIR if meaning changes, direct-owner tests. |
| World-state behavior change | X |  |  | Implementation unless it requires a new state domain or cross-domain write seam. |
| New action/content/campaign package | X |  |  | Use scene/action/schema/content validation. |
| New non-combat kind | X | X |  | Usually implementation; framework-version or CTIR changes are local evolution. |
| Final Emission legality/packaging rule | X | X |  | Owner-scoped implementation; boundary taxonomy changes are local evolution. |
| Final Emission semantic ownership change |  | X |  | Deliberate local evolution only; current residue is drift-watch, not redesign. |
| New response policy contract | X | X |  | Extend owner contract and direct tests; not a chassis change. |
| New protected replay observation | X | X |  | Verification/projection evolution; runtime remains independent. |
| New diagnostic/reporting tool | X |  |  | Pure read-side implementation if it does not affect runtime metadata production. |
| New provenance field/taxonomy | X | X |  | Producer-owned and replay-sensitive; local evolution if taxonomy changes. |
| Backend provider adapter extraction | X | X |  | Deliberate implementation/local architecture before any second provider. |
| Additional AI provider | X | X |  | Use backend adapter contract; not major architecture if provider-specific logic stays contained. |
| Ruleset identity/capability publication | X | X |  | Future implementation/local architecture; required before alternate ruleset behavior. |
| Alternate ruleset support | X | X |  | Not a major reconsideration if it follows published identity/capability/domain contracts. |
| Saved-campaign migration policy |  | X |  | Product-triggered local architecture around persistence/version compatibility. |
| Public tooling/API facade |  | X | X | Local evolution for modest tooling; major architecture only for hosted/multi-user/event model. |
| Player-facing provenance redaction/explanation |  | X |  | Optional product architecture; not debt. |
| Generic plugin system |  |  | X | Not approved; would require a future campaign with concrete requirements. |
| Package moves for aesthetics |  |  |  | Not recommended; no AR-BX evidence of foundational packaging concern. |
| Compatibility retirement | X | X |  | Evidence-driven package work, not doctrine change. |

Future gameplay systems should overwhelmingly be pure implementation. They become local evolution only when they introduce new identity/version/state/domain/public-facade contracts. They become major architecture only if they try to replace the transaction spine, invert replay/runtime dependency, move mechanics to GPT/Final Emission, or introduce a broad plugin/public integration model.

## 6. Long-Term Chassis Principles

1. Preserve one runtime transaction spine.
2. Domain simulation owns game truth; narration and model output do not.
3. State authority must name owners before state mutation spreads.
4. CTIR is the canonical resolved-turn meaning surface between domain resolution and prompt adaptation.
5. Prompt/adaptation packages approved truth; it does not create truth.
6. Model routing and backend providers are expression infrastructure, not gameplay authority.
7. Extend contracts and owners, not central orchestration by default.
8. Keep Final Emission as last-mile legality, sealing, selection, packaging, metadata, and traceability.
9. Validators predicate; repairs remain bounded; sanitizers strip/package/drop.
10. Fallback behavior must remain provenance-bearing and split by content, selection, application, and observation.
11. Persistence stores runtime documents; it does not own mechanics or replay policy.
12. Replay, projection, diagnostics, and evidence observe after runtime; they must not drive runtime decisions.
13. Provenance explains behavior; it must not select behavior.
14. Direct-owner tests own semantic invariants before downstream smoke tests are added.
15. Compatibility is preserved until evidence justifies retirement.
16. Documentation should point to executable authority instead of duplicating it where possible.
17. Manual registries are governance aids, not behavior changes.
18. Internal helpers are not extension points unless a future package explicitly promotes them.
19. Product-triggered architecture should be deliberate, narrow, and evidence-backed.
20. Architectural stability is the default; reopening foundational doctrine requires concrete contradiction or product need.

## 7. Remaining Evolution Areas

Backend adapter/provider implementation:

- Classification: implementation evolution with local architecture.
- Status: optional until a second provider, local inference, or deterministic fake backend becomes product scope.
- Not debt: AR-BX found the path documented and current provider stable.

Ruleset identity/capability and alternate ruleset support:

- Classification: implementation evolution with local architecture.
- Status: future only until alternate rulesets are in scope.
- Not debt: current engine-first ruleset is stable; identity/version/capability fields should precede alternate behavior.

Version/provenance bundle formalization:

- Classification: local architecture / implementation.
- Status: useful when backend/ruleset/save/replay portability requires it.
- Not debt: existing runtime provenance and versioned surfaces are adequate for current behavior.

Saved-campaign migration policy:

- Classification: optional product architecture.
- Status: future only if long-lived campaigns must survive ruleset/backend/schema transitions.

Public tooling or hosted/multi-user facade:

- Classification: optional product architecture; potentially major only for hosted/evented/multi-user integrations.
- Status: not required for local UI/product growth.

Player-facing provenance explanation and hidden-information redaction:

- Classification: optional product architecture.
- Status: future product decision; current provenance remains internal/evidence-facing.

Executable contract registries/generated appendices:

- Classification: governance/tooling evolution.
- Status: optional; useful only if manual registry drift becomes costly enough to justify generation/enforcement.

Compatibility retirement:

- Classification: implementation/local governance evolution.
- Status: proceed only through evidence-backed retirement packages.

Generic plugin architecture:

- Classification: optional major architecture, not approved.
- Status: explicitly out of scope unless concrete ruleset/backend/tool/content requirements justify it.

## 8. Chassis Stability Assessment

Ownership clarity: High.

AR-BX found stable owners for runtime transaction, domain simulation, state authority, CTIR, prompt/adaptation, response policy, backend route/call surfaces, Final Emission, persistence, replay/projection, provenance, diagnostics, and governance. AR-BI and the ownership ledger already classify downstream and compatibility paths as consumers rather than co-owners.

Dependency stability: High.

The long-term dependency direction is settled: player intent -> runtime transaction -> domain simulation/state authority -> CTIR -> prompt/adaptation -> realization/backend -> Final Emission -> persistence/log/response -> replay/projection/evidence/diagnostics -> governance. AR-BX found no evidence requiring a dependency inversion or redesign.

Extension maturity: Medium-high.

Ordinary gameplay, content, action/schema, CTIR, response policy, model routing, persistence, replay/provenance, diagnostics, and governance extension paths are mature. Backend provider and alternate ruleset mechanisms are documented and architecturally ready, but executable multi-provider and alternate-ruleset support remain future implementation.

Governance maturity: High, with manual drift risk.

The repository has direct-owner tests, ownership ledger, feature-lane guide, governance refresh workflow, compatibility register, replay governance, generated-doc strategy, and contract registries. Manual registry drift remains the main weakness, already mitigated by AR-BW governance guidance.

Coordination resistance: High.

Campaign 5 reduced rediscovery through lane guidance and registries. AR-BX found that future contributors can avoid central coordination by starting at owner modules, extending direct-owner tests, and treating adapters/projections as consumers.

Implementation readiness: High.

Controlled feature work can proceed inside the chassis. Feature work should not require another architecture campaign unless it introduces public/hosted facade requirements, actual multi-ruleset loading, multi-provider provider dispatch, formal migration policy, or a generic plugin model.

## 9. Architectural Confidence Statement

Yes. Future contributors can confidently build upon this chassis without repeatedly revisiting foundational architecture.

AR-BX found that repository evidence reinforces the same architecture recovered by Campaigns 1-5: one runtime transaction spine, domain-owned mechanics, state authority, CTIR, prompt adaptation, bounded backend/model expression, durable Final Emission, persistence as storage, replay/evidence as observational, provenance as explanatory, and governance as drift stewardship. It also found no foundational packaging concern and no need for a generic plugin framework.

The main remaining uncertainties are not foundational instability. They are product-triggered choices or implementation sequencing:

- whether to implement additional backend providers,
- whether to implement alternate rulesets,
- whether to formalize saved-campaign migration,
- whether to expose public/hosted tooling facades,
- whether to present provenance to players,
- and whether manual contract registries eventually need executable generation.

Those questions should be handled as narrow future packages or decision records, not as a reason to reopen the chassis.

## 10. Recommended Next Cycle

Recommended title: **AR-BZ - Chassis Closeout Readiness and Contributor Doctrine Pack**

Objective: produce the narrow final Campaign 6 closeout package that turns AR-BX and AR-BY into a contributor-facing doctrine map: where to start, which doctrine is permanent, which extension paths are approved, what is internal-only, and what future work requires a decision record.

Scope:

- Analysis/documentation only.
- No production behavior changes.
- No new architecture.
- No package movement.

Questions it should answer:

- Is Campaign 6 ready to close after AR-BY?
- Which single file or small doc set should future contributors read first?
- Should a concise contributor-facing chassis map be added or should existing docs be cross-linked only?
- What stop conditions should force a future decision record rather than ordinary implementation?

Why this is narrower than AR-BY:

- AR-BX gathered evidence.
- AR-BY established doctrine.
- AR-BZ should only package the doctrine for use and decide whether Campaign 6 can close.
