# AR-BL - Implementation Workflow Optimization Planning

## 1. Executive Summary

AR-BL converts the AR-BJ inventory and AR-BK prioritization into a repeatable implementation methodology. The strategy is not to reduce coordination by weakening architecture. The strategy is to make correct coordination predictable.

Implementation strategy:

- Start every nontrivial change by identifying the canonical owner and the relevant contract surface.
- Treat adapters, projections, replay, provenance, governance, tests, and docs as expected follow-on lanes, not as signs of architectural failure.
- Use category-specific checklists so developers know which replay, provenance, governance, and documentation steps apply before editing.
- Publish missing executable contracts before feature expansion in the areas AR-BK identified as high ROI: backend, ruleset, version, and provenance identity.
- Standardize test builders, generated documentation, compatibility evidence collection, and verification sequences.
- Preserve Final Emission authority, runtime/protected replay separation, provenance semantics, governance strength, and direct-owner test placement.

The optimized workflow should make future implementation feel less like architectural archaeology and more like selecting the right lane: gameplay feature, Final Emission change, replay/provenance change, backend extension, ruleset extension, compatibility retirement, or governance update.

Highest-value future infrastructure initiatives:

- Backend contract publication.
- Ruleset/version/provenance contract publication.
- Compatibility-residue register.
- Feature-lane verification guide.
- FEM metadata and protected observed-row builders.
- Registry-driven generated documentation.
- Split-owner matrix/count/report automation.
- Governance refresh workflow.

No production code, refactoring, compatibility retirement, or governance automation was performed in this cycle.

## 2. Standard Feature Workflow

The preferred implementation lifecycle for any nontrivial feature should be:

1. Classify the feature lane.
   - Choose one primary lane: ordinary gameplay, Final Emission, replay, provenance, backend, ruleset, compatibility, or governance.
   - If more than one lane applies, name the primary behavior owner first and list secondary observation/governance lanes.

2. Identify canonical ownership.
   - Use `docs/architecture_ownership_ledger.md`, AR-BI, AR-BJ, AR-BK, module docstrings, and direct-owner tests.
   - Record the runtime owner, adapter/projection owners, direct-owner test suite, downstream suites, and compatibility/support residue.

3. Identify executable contracts and registries.
   - Examples: `game/state_authority.py`, `game/response_policy_contracts.py`, `game/final_emission_boundary_contract.py`, `game/realization_authority.py`, `game/realization_provenance.py`, `game/contract_registry.py`, `tests/helpers/golden_replay_projection_fields.py`, `tests/helpers/failure_classification_split_owner.py`.
   - If the needed contract is missing, stop feature expansion and plan contract publication first.

4. Decide replay and provenance scope.
   - Determine whether the change affects runtime metadata, runtime lineage, protected observation fields, replay diagnostics, or generated evidence.
   - Do not promote diagnostics into protected replay unless policy requires it.

5. Plan adapters and projections.
   - Identify prompt, API, UI, persistence, Final Emission metadata, runtime diagnostic, protected replay, dashboard, and report projections.
   - Adapters may translate; they must not become authoritative owners.

6. Check compatibility obligations.
   - Search the compatibility-residue register once it exists.
   - Until then, check AR-BJ/AR-BK, the ownership ledger, gate cleanup docs, protected replay docs, and relevant tests for legacy aliases, re-exports, old payload shapes, and historical vocabulary.

7. Implement in owner-first order.
   - Owner behavior first.
   - Contract/registry update second.
   - Adapter/projection propagation third.
   - Tests and generated docs after executable truth exists.

8. Update tests by layer.
   - Direct-owner tests for semantics and invariants.
   - Adapter/projection tests for mapping and presence.
   - Downstream smoke tests only for wiring and shipped behavior.
   - Protected replay tests only for protected acceptance fields.
   - Governance tests for boundary drift and registry parity.

9. Update docs and generated artifacts.
   - Update handcrafted doctrine only when ownership or workflow changes.
   - Regenerate generated tables/reports from canonical executable sources.
   - Preserve historical campaign docs as evidence.

10. Verify with the minimal sufficient lane.
   - Use the feature-lane verification guide.
   - Include governance checks only where the feature lane touches governed surfaces.

## 3. Workflow Variants

| Workflow | Canonical Owner | Required Contracts | Required Adapters | Replay/Provenance | Required Tests | Governance | Documentation |
|---|---|---|---|---|---|---|---|
| Gameplay feature | Domain owner plus `game/api.py` for transaction order | State authority, domain model/result contract, CTIR if resolved-turn meaning changes | API, CTIR, prompt context, UI if visible | Usually runtime trace/provenance; protected replay only if protected behavior changes | Domain direct-owner, API/pipeline smoke, CTIR/prompt tests if touched | State authority and test ownership checks if new domain/suite | Domain docs only if contract/workflow changes |
| Final Emission change | `game/final_emission_gate.py`, `game/final_emission_meta.py`, validators/repairs/sanitizer owner as applicable | Boundary taxonomy, FEM metadata helpers, validator/repair contract | Runtime metadata, runtime lineage, protected projection if field is protected | High; determine FEM and protected observation effect | Direct-owner Final Emission suite, boundary contract, orchestration order, projection tests | Gate boundary, final-emission boundary, validation layer if applicable | Gate cleanup/closeout docs only for policy changes; generated taxonomy if available |
| Replay change | Protected replay owner for acceptance; runtime projection owner for diagnostics | `PROTECTED_OBSERVATION_FIELDS`, extraction registry, replay registry/manifest | Runtime payload reader, extraction helpers, manifest/report generators | Central concern; protect runtime/protected boundary | Projection registry, protected replay, manifest parity, classifier overlap if touched | Replay boundary governance | Protected replay manifest/generated docs |
| Provenance change | Runtime provenance owner (`realization_provenance`, FEM meta, runtime lineage owner) | Fallback family registry, provenance fields, version bundle when available | FEM metadata, runtime lineage, replay diagnostics, reports | High; avoid using provenance as behavior selector | Realization provenance, FEM metadata, runtime projection, relevant replay diagnostics | Provenance/realization audits if stable, replay boundary if observed | Provenance docs/generated family table if changed |
| Backend extension | Future backend contract/adapter owner; current adjacent owners are `model_routing` and `gm` | Backend id/version/provider/capability/request/response/error contract | Backend adapter, GM realization consumption, route metadata, diagnostics | Provider/backend identity must be provenance-ready before expansion | Backend contract tests, fake backend tests, model routing runtime tests | Drift guard preventing provider logic from spreading | Backend decision record and contract docs |
| Ruleset extension | Future ruleset contract/registry owner plus domain mechanics owners | Ruleset id/version/family/capabilities/mechanics compatibility | Domain mechanics, CTIR, persistence, replay metadata, UI capability projection | Ruleset identity affects replay/save/provenance | Ruleset contract tests, domain tests, CTIR/persistence/replay identity tests | Drift guard preventing ruleset conditionals in prompt/Final Emission/replay | Ruleset decision record and contract docs |
| Compatibility retirement | Current compatibility owner/support surface plus affected consumers | Existing compatibility contract and retirement criteria | Import redirects, mappers, legacy test fixtures, reports | Must prove no replay/provenance loss | Caller/import tests, negative legacy tests updated, focused direct-owner tests | Compatibility import governance and replay governance if observed | Active residue register and retirement closeout |
| Governance change | Governance doc/test/tool owner | Ownership ledger, TEST_AUDIT, inventory JSON, validation registry, split-owner matrix | CI workflow/docs, generated reports | Usually observational only | Governance direct-owner tests and tool smoke | Central concern; preserve hard-fail vs advisory status | Governance docs and command references |

## 4. Coordination Checklists

### Protected Replay Field

- Confirm the field is acceptance-worthy, not merely diagnostic.
- Update `PROTECTED_OBSERVATION_FIELDS` and drift bucket.
- Update extraction registry/defaults.
- Add projection test for presence and path coverage.
- Regenerate/check protected replay manifest.
- Check classifier/dashboard overlap only if the field participates in evidence.
- Run protected replay/projection/governance tests.
- Document authority as protected acceptance, not runtime behavior.

### Final Emission Metadata

- Identify whether the field is gate orchestration, metadata packaging, validator evidence, repair evidence, sanitizer lineage, runtime lineage, or protected observation.
- Update the canonical metadata owner first.
- Keep gate ordering in `apply_final_emission_gate` explicit.
- Update runtime lineage only if the field explains finalized FEM.
- Update protected replay only if policy requires protected acceptance.
- Add/extend FEM metadata builder fixtures once available.
- Run direct-owner Final Emission tests, boundary contract tests if mutation kinds are involved, and projection tests if fields propagate.

### Backend Capability

- Do not add provider conditionals to `game.gm.call_gpt`.
- Publish or extend backend contract first.
- Distinguish model route from backend/provider identity.
- Define capability, request, response, and error fields.
- Add deterministic fake backend tests.
- Add provenance fields only after ownership is clear.
- Add drift guard preventing provider logic from spreading into prompt context, Final Emission, replay, or persistence.

### Ruleset Capability

- Do not add scattered ruleset conditionals.
- Publish or extend ruleset contract first.
- Identify ruleset id, version, family, capability, mechanics contract, state compatibility, CTIR compatibility, and provenance label.
- Keep mechanics in domain/ruleset owners, not prompt/Final Emission/replay.
- Add CTIR/persistence/replay identity only after contract shape is stable.
- Add fake or minimal second ruleset tests before broad alternate-ruleset work.

### Fallback Change

- Identify content author, selector, applicator, provenance packager, runtime diagnostic owner, and protected replay owner.
- Update `game/realization_authority.py` only for governed family/profile changes.
- Stamp via `game/realization_provenance.py` helpers.
- Preserve dual diegetic/governed fallback-family semantics unless consumer evidence supports a change.
- Check opening compatibility-local and legacy fallback residue.
- Add direct-owner tests before golden replay or dashboard consumers.

### Validator Addition

- Confirm the validator predicates and does not repair.
- Place it in the canonical validation owner.
- Define reason codes/evidence shape.
- Decide whether Final Emission gate only orchestrates it or owns the legality boundary.
- Add direct-owner validator tests.
- Add gate orchestration test only for ordering/wiring.
- Add governance/audit updates only if a validation layer boundary changes.

### Repair Addition

- Confirm repair is bounded and allowed at the intended layer.
- Classify any Final Emission mutation kind in boundary taxonomy.
- If semantic, move upstream or keep fenced as `SEMANTIC_DISALLOWED`.
- Preserve validator/repair separation.
- Add direct-owner repair tests and boundary tests.
- Update provenance/FEM metadata if the repair changes shipped output or evidence.

### Compatibility Retirement

- Enter residue in active compatibility register.
- Gather fresh import/caller evidence.
- Gather runtime/replay incidence if behavior may still occur.
- Identify protected replay, dashboard, classifier, docs, and generated artifact consumers.
- Replace compatibility tests with retirement/negative tests only after consumer proof.
- Produce closeout with retained behavior and verification.

### Governance Addition

- Define the failure prevented.
- Choose hard-fail, informational, or deferred status.
- Place tests in the focused governance owner, not generic registry files by default.
- Keep runtime behavior out of governance tools.
- Add clear failure messages and corrective action.
- Update CI inventory and test README only where workflow changes.

### Documentation Update

- Decide authority level: doctrine, executable contract summary, generated artifact, advisory evidence, or historical record.
- Generate tables from executable registries when possible.
- Preserve historical AR/audit records.
- Link to canonical source instead of restating current truth in multiple places.
- Mark generated sections with source and refresh command.

## 5. Repository Implementation Standards

Recommended standards:

- Owner-first implementation: behavior changes start in the canonical owner.
- Contract-first expansion: backend and ruleset work begins with executable contracts before adapters or feature behavior.
- Registry publication: shared vocabulary, fields, and ids should have one published executable source when they are current contract truth.
- Adapter isolation: adapters translate between owners and representations; they do not own decisions.
- Projection discipline: runtime diagnostic projection and protected replay projection remain separate.
- Provenance discipline: provenance explains behavior; it does not select behavior.
- Validator/repair separation: validators predicate; repairs mutate only within bounded authority and with metadata.
- Direct-owner testing: semantic invariants live in the owner suite; downstream suites verify wiring/observation only.
- Generated documentation from registries: generated tables should come from executable sources and carry refresh commands.
- Compatibility evidence before retirement: no compatibility removal without caller/replay/governance evidence.
- Minimal verification lanes: run focused tests/audits based on feature category rather than defaulting to broad suites.
- Builder use in tests: common FEM, protected observed row, failure/dashboard, and contract payloads should use explicit builders once available.

Standards to avoid:

- Adding global constants for similar-looking vocabulary without proving a shared meaning.
- Moving authority into replay, tests, UI, API adapters, prompt context, or generated docs.
- Treating file count or owner frequency as proof of poor design.
- Updating docs before executable contract truth is clear.
- Promoting diagnostic fields into protected replay by default.

## 6. Infrastructure Initiative Catalog

| Initiative | Purpose | Dependencies | Architectural Constraints | Benefit | Risk | Priority |
|---|---|---|---|---|---|---|
| Feature-lane verification guide | Give developers a minimal test/audit/doc path by change type | AR-BJ/AR-BK/AR-BL | Must preserve direct-owner vs downstream distinction | High | Low | Immediate |
| Compatibility-residue register | Centralize active residue, callers, tests, retirement evidence | Fresh import/caller evidence over time | Must not imply retirement without proof | High | Low | Immediate |
| FEM metadata builders | Reduce repeated hand-built FEM fixtures | Builder design; owner-suite review | Test-only; must not own FEM schema | High | Low | Near-term |
| Protected observed-row builders | Reduce protected replay fixture churn | Protected field registry | Must derive from protected registry; no runtime dependency | High | Low-medium | Near-term |
| Failure/dashboard matrix helpers | Reduce matrix/report/dashboard duplication | Split-owner matrix source | Must preserve evidence and dashboard semantics | Medium-high | Low-medium | Near-term |
| Generated documentation appendices | Generate tables from executable registries | Stable source registry and parity checks | Generated docs cannot become authority over source | Medium-high | Low | Near-term |
| Split-owner count/report automation | Remove manual expected-count coordination | Existing matrix/report renderer | Must preserve hard-fail parity | High | Low | Near-term |
| Backend contract publication | Publish provider-neutral identity/capability/request/response/error boundary | AR-BG/AR-BH | Must not implement second provider yet; model routing remains distinct | Very High | Low-medium | Near-term |
| Ruleset contract publication | Publish ruleset id/version/capability/state/CTIR compatibility | AR-BG/AR-BH | Must not scatter mechanics conditionals | Very High | Low-medium | Near-term |
| Version/provenance bundle plan | Define how runtime/ruleset/backend/model/prompt/CTIR/persistence/FE/replay identities travel | Backend/ruleset contracts | Provenance observes; does not select behavior | High | Medium | Long-term |
| Governance refresh workflow | Clarify when to refresh inventory JSON, manifests, matrix reports, CI docs | Current tools | Must not weaken hard-fail governance | Medium | Low | Near-term |
| Compatibility retirement playbook | Standardize retirement blocks and closeout evidence | Compatibility register | Must preserve replay/provenance/consumer behavior | Medium | Medium | Long-term |
| Backend fake adapter test harness | Replace ad hoc provider fakes after contract exists | Backend contract | Must be provider-neutral | Medium-high | Low-medium | Long-term |
| Ruleset fake/minimal adapter tests | Enable safe alternate-ruleset contract validation | Ruleset contract | Must keep CTIR/prompt/FE non-authoritative | Medium-high | Medium | Long-term |

## 7. Developer Experience Assessment

Current onboarding friction:

- New contributors must know which files are owners, adapters, projections, downstream consumers, or compatibility residue.
- The correct test lane is not always obvious from file names.
- Final Emission changes require understanding gate order, metadata packaging, boundary taxonomy, validators, repairs, sanitizer, runtime lineage, and protected replay.
- Replay changes require knowing the difference between runtime diagnostic lineage and protected replay acceptance.
- Backend and ruleset expansion are documented architecturally but not yet published as executable contracts.
- Compatibility evidence is scattered across AR reports, audit docs, module comments, and tests.
- Large tests and hand-built payloads make it easy to copy fixtures without understanding ownership.

Knowledge that currently depends on repository familiarity:

- Which docs are current doctrine vs historical evidence.
- Which governance checks are hard-fail vs advisory.
- Whether a field belongs in protected replay or diagnostic projection only.
- Whether fallback vocabulary is shared, translated, compatibility-only, or intentionally distinct.
- Which compatibility surfaces are still active.
- Which generated artifacts are authoritative, advisory, or historical.

Knowledge that can become discoverable:

- Feature-lane verification guide.
- Compatibility-residue register.
- Generated registry appendices with source and refresh command.
- Test builders with names that encode normal vs compatibility payloads.
- Contract modules for backend, ruleset, and version/provenance identity.
- Checklists embedded in workflow docs and linked from `tests/README_TESTS.md`.
- Clear authority labels on generated docs and evidence artifacts.

Expected developer-experience improvement:

- Less time spent rediscovering ownership.
- Fewer missed projection/replay/doc steps.
- Lower fixture churn.
- Safer expansion sequencing for backend and rulesets.
- Clearer boundary between implementation improvement and architecture redesign.

## 8. Implementation Readiness Assessment

Future feature work can proceed under the current doctrine, with caveats.

Ready now:

- Ordinary gameplay work inside existing domain owners and current single-ruleset architecture.
- Final Emission changes when they use existing boundary taxonomy and direct-owner tests.
- Replay/provenance changes when they preserve runtime/protected projection separation.
- Governance additions when they use focused owner suites and clear hard-fail/advisory placement.

Ready after workflow planning:

- Protected replay field additions, once the checklist and generated-doc workflow are used.
- FEM metadata changes, once builders and projection checklist are planned.
- Split-owner matrix changes, once count/report automation is planned.
- Compatibility retirement candidates, once active residue register and evidence collection exist.

Not ready for feature expansion without contract publication:

- Second provider or local backend.
- Alternate rulesets.
- Replay/save portability across ruleset/backend versions.
- Player-facing explanation over provenance bundles.

Assessment:

The architecture is implementation-ready. The workflow is partially ready. AR-BL should be followed by sequencing infrastructure initiatives before major backend/ruleset expansion.

## 9. Campaign Assessment

Campaign 5 has successfully transitioned from analysis into actionable implementation planning.

- AR-BJ mapped where coordination occurs.
- AR-BK ranked the costs and identified owner-preserving reduction opportunities.
- AR-BL defines repeatable workflows, checklists, implementation standards, and infrastructure initiatives.

No architectural concerns emerged. The costs remain primarily implementation and workflow concerns. The campaign is now ready to sequence infrastructure initiatives rather than continue broad discovery.

Roadmap implication:

- Do not start with feature expansion that depends on missing contracts.
- Do not start with compatibility retirement.
- Start by sequencing workflow/infrastructure initiatives that make future feature work safer and cheaper.

## 10. Recommended Next Cycle

Recommended next cycle: **AR-BM - Infrastructure Initiative Prioritization and Sequencing**.

AR-BM should:

- Rank the initiatives in Section 6 by dependency, ROI, and risk.
- Define scoped implementation blocks without implementing them yet.
- Assign each block a canonical owner, prerequisites, verification lane, and stop condition.
- Separate immediate workflow/documentation improvements from contract-publication projects and future compatibility retirement.
- Confirm the first implementation-ready initiative after AR-BM.

Only recommend a different next cycle if new repository evidence shows an urgent blocking gap in the workflow plan.

## 11. Files Required for External Review

Required:

- `AR-BL_implementation_workflow_optimization_planning.md`
- `AR-BK_coordination_cost_classification_and_reduction_opportunities.md`
- `AR-BJ_coordination_cost_inventory_and_workflow_discovery.md`
- `AR-BI_boundary_reconciliation_campaign_closeout.md`
- `AR-BG_ruleset_backend_and_version_provenance_boundary_inventory.md`
- `AR-BH_minimal_extensibility_contract_definition.md`
- `AR-AD_target_architecture_doctrine.md`
- `docs/architecture_ownership_ledger.md`
- `tests/README_TESTS.md`
- `docs/convergence_ci_inventory.md`
- `game/final_emission_boundary_contract.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/contract_registry.py`
- `tests/helpers/golden_replay_projection_fields.py`
- `tests/helpers/failure_classification_split_owner.py`

Optional:

- `game/api.py`
- `game/gm.py`
- `game/model_routing.py`
- `game/final_emission_gate.py`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/test_final_emission_meta.py`
- `tests/test_final_emission_boundary_contract.py`
- `tests/test_split_owner_acceptance_matrix_contract.py`
- `docs/testing/protected_replay_manifest.md`
- `docs/gate_convergence_closeout.md`
- `docs/gate_cleanup_inventory.md`
- `docs/planner_convergence.md`
- `docs/maintenance/CR_protected_replay_recurrence_separation_discovery.md`
