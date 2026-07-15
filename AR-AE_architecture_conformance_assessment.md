# AR-AE Architecture Conformance Assessment

Date: 2026-07-14  
Scope: documentation-only conformance assessment against `AR-AD_target_architecture_doctrine.md`  
Inputs: `AR-AA_architectural_mapping_discovery.md`, `AR-AB_runtime_authority_and_replay_boundary_map.md`, `AR-AC_architectural_ownership_reconciliation.md`, `AR-AD_target_architecture_doctrine.md`  
Non-goal: runtime refactor, behavior change, schema promotion, replay policy change

## Executive Summary

The current implementation mostly conforms to the AR-AD target architecture doctrine. The system has a stable single-turn runtime spine, explicit domain and state authority declarations, a clear CTIR narration boundary, a coherent prompt/GPT split, durable persistence, strong replay/governance boundaries, and mature provenance/replay evidence.

The main deviations are not architectural failures. They are the transitional areas already named in AR-AD:

- Final emission still carries semantic repair pressure beyond pure legality and packaging.
- Retry/fallback ownership is correct as a multi-axis model, but field vocabulary and consumer interpretation remain cognitively heavy.
- Opening realization is stable but boundary-sensitive because campaign start crosses bootstrap, planning, GPT, fallback, final emission, persistence, and replay.
- Evidence surfaces are powerful but artifact-heavy; canonical/generated/advisory status can still be easy to blur.
- `game.api` is broad by design and remains a coordination hotspot.

No subsystem shows significant divergence from the doctrine. The implementation is sufficiently understood to begin architectural refinement work, provided refinement begins with documentation alignment, field-consumer mapping, and classification of transitional responsibilities rather than immediate runtime movement.

Campaign 1's central architectural question is answered: yes, the project now understands the architecture well enough to begin architectural refinement work. The missing knowledge is not "what owns what"; it is which transitional simplifications are worth paying for, in what order, and with what replay/evidence proof.

## Architecture Conformance Matrix

| Subsystem | Current implementation | Target doctrine | Degree of alignment | Assessment |
|---|---|---|---|---|
| Runtime orchestration | `game.api` owns start/chat/action request entry, state loading, eligibility, authoritative mutation orchestration, CTIR placement, GPT/retry orchestration, final-emission handoff, persistence, logging, traces, and response construction. | One turn has one transaction spine; `game.api` remains the runtime transaction owner. | Mostly aligned | The breadth is intentional and doctrinally correct. The remaining issue is local coordination pressure, not ownership divergence. |
| State authority | `game.state_authority` declares domains, read/write rules, cross-domain allowances, and mutation traces; domain modules/storage/API still own actual state behavior. | State authority is a governance contract and guard vocabulary, not a persistence or universal mutation engine. | Fully aligned | The registry-vs-domain-owner split is clear. Partial guard adoption is documented as drift-watch rather than architectural failure. |
| CTIR lifecycle | `game.api` places lifecycle timing; `game.ctir` builds bounded meaning; `game.ctir_runtime` detaches/attaches/stamps retry-stable CTIR. | CTIR is resolved-turn meaning for narration, built after mutation and consumed by prompt construction. | Fully aligned | Lifecycle doctrine and implementation match closely. CTIR remains narration meaning, not canonical state. |
| Prompt construction | `game.prompt_context` and plan/policy helpers package CTIR, visibility, response contracts, and read models; compatibility fallbacks exist when CTIR is absent. | Prompt construction adapts runtime truth; it must not recreate CTIR-owned semantics when CTIR exists. | Mostly aligned | Normal path is aligned. CTIR-absent fallbacks are transitional compatibility residue. |
| GPT routing | `game.gm` and model routing handle model call, guard, route metadata, and upstream error metadata; API owns retry/fallback loop decisions. | GPT owns expression/model I/O; runtime retry/fallback decisions stay in the transaction spine. | Fully aligned | Call/guard mechanics and runtime orchestration are separated as intended. |
| Retry/fallback | API retry loop, `gm_retry`, fallback behavior modules, diegetic/opening/social fallback authors, and provenance packagers all participate. | Fallback uses multi-axis ownership: runtime owner, content author, selector, applicator, provenance packager, recorder, replay observer. | Transitional | Architecturally correct but complex. No single owner should replace the multi-axis model, but field consumer clarity is not complete. |
| Opening realization | API bootstraps scene opening; narrative planning owns structural opening obligations; opening realization curates diegetic basis; deterministic/prepared fallback and final emission participate. | Opening has intentional split ownership across bootstrap, planning, realization, fallback, final emission, persistence, and replay. | Mostly aligned | The split matches doctrine. Boundary sensitivity remains because opening is the densest first-turn handoff. |
| Final emission | Runtime delegate/gate/finalize/meta own final player-facing text, legality, packaging, metadata, repairs, sanitizer, and sealed terminal paths. | Final emission owns legality, selection, packaging, metadata, and sealed terminal exceptions; ordinary semantic synthesis should move upstream over time. | Transitional | The boundary is governed and stable but still carries semantic repair pressure. This is the clearest transitional conformance area. |
| Persistence | `game.storage` owns load/save/envelopes/snapshots/log mechanics; API owns transaction timing and persistence tail. | Storage owns persistence mechanics; API owns when transaction state is complete enough to persist/log. | Fully aligned | The storage/API split is doctrinally sound and stable. |
| Replay | Runtime diagnostic projection lives in `game.final_emission_replay_projection`; protected replay projection/fields/registry live under `tests.helpers` and docs. | Replay dependency is one-way: runtime outputs -> runtime diagnostics -> protected replay/evidence. Runtime must not depend on protected acceptance. | Fully aligned | Static boundary scan found test-side projection imports and allowed test consumption of runtime diagnostics; no runtime import of protected acceptance was observed. |
| Provenance | `game.realization_authority`, `game.realization_provenance`, `game.fallback_provenance_debug`, FEM/meta, and replay projection readers record and interpret fallback/emission provenance. | Provenance explains behavior without owning behavior; write-time stamps differ from read-side projection. | Mostly aligned | Provenance is first-class and stable. The remaining risk is terminology and field fanout, not absence of authority. |
| Governance | Ownership ledger, protected replay manifest, replay governance docs/tests, ownership guards, and audit tools define target ownership and drift-watch. | Governance declares doctrine and checks drift; it must not execute gameplay or become hidden runtime behavior. | Mostly aligned | Governance is mature. Risk remains that abundant advisory/generated artifacts can be mistaken for canonical authority without labels. |

## Dependency Conformance Review

### Confirmed Compliant Relationships

| Relationship | Conformance finding |
|---|---|
| `game.api` -> storage/domain/CTIR/prompt/GPT/final emission | Compliant. This is the intended runtime transaction spine. |
| Domain modules -> state authority guards/read models | Compliant. Domain behavior remains with domain owners while guard vocabulary stays declarative. |
| Prompt construction -> CTIR/read models/response policy | Compliant. Prompt context acts as adapter/packager over approved runtime truth. |
| API -> GPT call/guard modules | Compliant. API invokes model I/O but does not make GPT authoritative state. |
| API/final emission -> provenance packagers | Compliant. Runtime selection/application and provenance packaging are separate axes. |
| Protected replay helpers -> `game.final_emission_replay_projection` | Compliant. Protected replay may consume runtime diagnostics read-only. |
| Governance tests/docs -> runtime modules via static inspection | Compliant. Governance observes boundaries rather than executing gameplay. |

### Transitional Exceptions

| Relationship | Why transitional |
|---|---|
| Final emission -> semantic repair/fallback behavior | Needed to preserve shipped behavior, but target doctrine is legality/packaging plus sealed terminal exceptions. |
| Prompt context -> non-CTIR semantic fallback reads | Compatibility behavior when CTIR is absent; not a second resolved-turn meaning authority. |
| Protected replay -> compressed fallback-family projection | Read-side compatibility over dual runtime vocabulary; not runtime schema collapse. |
| Opening path -> API/planning/realization/fallback/final-emission/persistence/replay | Structurally necessary, but dense enough to remain a documentation and terminology risk. |
| Evidence reports -> governance decisions by human interpretation | Acceptable when explicit, but advisory evidence should not silently become policy. |

### Architectural Drift

No significant architectural drift was identified from the AR-AD doctrine.

Observed drift-watch areas:

- Final-emission semantic repair pressure remains the primary target-state gap.
- Fallback/provenance field vocabulary remains broad enough to invite accidental owner conflation.
- Generated/advisory evidence surfaces are still numerous enough that canonicality labels should be adopted in future docs.

### Potential Future Risks

| Risk | Nature |
|---|---|
| Runtime projection absorbing protected acceptance concerns | Would violate one-way replay dependency if runtime began importing protected field/schema logic. |
| Final emission becoming hidden semantic author | Would weaken runtime truth-before-narration and upstream ownership doctrine. |
| Governance ledgers treated as implementation proof | Would blur target-state doctrine with actual conformance. |
| Advisory reports promoted implicitly | Would create hidden policy outside protected acceptance/governance review. |
| API delegate extraction splitting transaction authority | Could reduce file pressure while damaging the single-spine model if done without doctrine. |

## Transitional Responsibility Review

| Transitional responsibility | Current purpose | Readiness assessment | Rationale |
|---|---|---|---|
| Final-emission semantic repairs | Preserve shipped legality, response shape, safety, and terminal fallback behavior. | Requires additional evidence before simplification | The boundary is stable but needs a repair classification table before any simplification can be judged. |
| Dual fallback-family vocabulary | Preserve diegetic/template fallback family and governed realization provenance family. | Requires additional evidence before simplification | Both fields answer real questions. Simplification needs consumer inventory and replay proof. |
| Fallback ownership field fanout | Explain content author, selector, applicator, provenance, recorder, and observer roles. | Still necessary | The multi-axis model is architecturally correct. Future simplification should target interpretation, not collapse. |
| Opening fallback owner buckets | Let protected replay observe opening fallback source/authorship while runtime carries multiple opening axes. | Requires additional evidence before simplification | Opening remains boundary-sensitive. A handoff checklist should precede any compatibility simplification. |
| CTIR-absent prompt fallbacks | Preserve tolerance for missing/legacy CTIR paths. | Ready for future simplification assessment | Normal doctrine is clear. Next step is evidence that all standard resolved-turn paths attach CTIR before prompt construction. |
| Evidence artifact fanout | Provide replay, recurrence, incidence, provenance, mutation, and drift evidence. | Ready for future simplification assessment | Canonicality categories exist in AR-AD; future work can classify artifacts without touching runtime. |
| API coordination breadth | Keep the full turn transaction coherent. | Still necessary | The broad spine is permanent architecture. Only documentation/delegate clarity is ready for assessment. |
| Final-emission replay projection fanout | Project diagnostic lineage from finalized FEM/provenance. | Still necessary | Read-side fanout is acceptable while one-way dependency holds. Watch for magnet growth. |
| Generated/advisory reports as decision inputs | Support investigation and corrective locality work. | Ready for future simplification assessment | The main need is explicit promotion/canonicality rules, not implementation movement. |

## Architectural Strengths

The following areas should now be treated as long-term foundations:

- Single runtime transaction spine in `game.api`.
- Runtime truth-before-narration doctrine.
- State authority as declarative registry/guard vocabulary rather than universal state engine.
- CTIR lifecycle as the post-mutation, retry-stable resolved-turn meaning boundary.
- Prompt construction as adapter/packager over CTIR and approved read models.
- GPT/model routing as expression and route metadata, not truth ownership.
- Storage/API split for persistence mechanics versus transaction timing.
- Runtime diagnostic projection versus protected replay acceptance split.
- Protected replay registry/fields/manifest as acceptance/governance authority.
- Multi-axis fallback/provenance ownership vocabulary.
- Governance as doctrine/drift-watch rather than runtime behavior.

These are sufficiently mapped, reconciled, and doctrinally stable that future work should avoid reopening their basic ownership unless new evidence contradicts the model.

## Remaining Architectural Risks

| Risk area | Risk |
|---|---|
| Ownership ambiguity | Fallback and opening still invite shorthand phrases like "fallback owner" or "opening owner" that erase multi-axis ownership. |
| Layer ambiguity | Final emission still mixes legality/packaging with some semantic repair pressure. |
| Evidence ambiguity | Generated/advisory artifacts may be mistaken for protected acceptance or governance contracts. |
| Dependency ambiguity | Protected replay may consume runtime diagnostics, but this allowed direction must remain explicit to avoid future reversal. |
| Terminology ambiguity | `fallback_family_used`, `realization_fallback_family`, owner buckets, content owner, selection owner, and sealed sub-kinds remain a dense vocabulary. |
| Documentation ambiguity | AR reports, ownership ledger, protected replay docs, and generated artifacts are all useful; their relative authority needs clearer long-term placement. |
| Refinement sequencing | Architectural refinement can begin, but moving code before classification/consumer mapping could damage stable boundaries. |

## Campaign Readiness Assessment

### Has Campaign 1's central architectural question been answered?

Yes.

The project now understands the architecture well enough to begin architectural refinement work. AR-AA identified the major subsystems, AR-AB mapped runtime authority and replay boundaries, AR-AC reconciled permanent versus transitional ownership, AR-AD established the target doctrine, and AR-AE confirms that the implementation mostly conforms to that doctrine.

### What architectural knowledge is still missing?

The remaining gaps are refinement inputs, not foundational unknowns:

- A final-emission repair classification table.
- A fallback/provenance field consumer map.
- A canonicality pass over generated/advisory evidence artifacts.
- A durable home or cross-reference for the AR-AD doctrine inside long-term docs.
- Evidence that CTIR-absent prompt fallbacks are only compatibility residue on standard paths.

These do not block architectural refinement. They define how refinement should proceed safely.

## Recommendation for AR-AF

AR-AF should be an architectural refinement-readiness plan, still documentation-only.

Recommended AR-AF focus:

1. Produce a final-emission repair classification table: legality-only, packaging-only, sealed terminal exception, upstream-owned semantic synthesis, and unresolved.
2. Produce a fallback/provenance field consumer map separating write-time truth, runtime projection, protected acceptance, generated artifact, and advisory reads.
3. Produce an evidence canonicality inventory for the most-used replay/provenance/fallback artifacts.
4. Decide where the AR-AD doctrine should be cross-referenced in durable docs.
5. Define criteria for when a transitional responsibility is ready for implementation-level simplification in a later cycle.

AR-AF should not move runtime code. Its value is to prepare refinement work so that future implementation changes, if any, are narrow, evidence-backed, and aligned with the stable target architecture.

## Validation Notes

No runtime files were intentionally modified. This cycle produced this documentation artifact only.

Validation performed:

- Read the AR-AA, AR-AB, AR-AC, and AR-AD input reports.
- Ran a targeted static boundary scan for protected replay projection terms in `game/` and `tests/`.
- Ran `git status --short` before writing this report.

Suggested final validation:

- Run `git status --short`.
- Confirm only `AR-AE_architecture_conformance_assessment.md` was added by this cycle, aside from pre-existing untracked AR-AA/AR-AB/AR-AC/AR-AD/foundation discovery artifacts.
