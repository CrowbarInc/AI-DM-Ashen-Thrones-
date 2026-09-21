# AR-BT - Backend Contract Registry Implementation

## 1. Executive Summary

Package 6 was implemented by creating a centralized Backend Contract Registry at
`docs/backend_contract_registry.md`.

The registry documents existing backend-facing architectural contracts for model
routing, backend configuration, GPT call adaptation, prompt message adaptation,
upstream error normalization, upstream API preflight, upstream-dependent run
gating, backend diagnostics, and backend compatibility.

The package is documentation-only. It does not implement new backends, change
runtime routing, modify provider logic, alter replay schemas, update provenance
behavior, change governance policy, or update CI behavior.

## 2. Backend Contract Inventory

| Contract ID | Contract | Authoritative Implementation |
|---|---|---|
| BCR-01 | Model routing decision | `game/model_routing.py::ModelRouteDecision`, `game/model_routing.py::resolve_model_route` |
| BCR-02 | Backend model configuration | `game/config.py` |
| BCR-03 | GPT call adapter | `game/gm.py::call_gpt` |
| BCR-04 | Prompt message adapter | `game/gm.py::build_messages`, API usage in `game/api.py` |
| BCR-05 | Upstream error normalization | `game/gm.py::_classify_upstream_gpt_error`, `_status_code_from_upstream_error`, `_error_code_from_upstream_error` |
| BCR-06 | Upstream API preflight status | `game/api_upstream_preflight.py::UpstreamApiPreflightStatus`, `run_upstream_api_preflight`, `get_latest_upstream_api_preflight` |
| BCR-07 | Upstream-dependent run gate | `game/upstream_dependent_run_gate.py::compute_upstream_dependent_run_gate`, `game/upstream_dependent_run_gate_presentation.py` |
| BCR-08 | Backend diagnostics and model-route metadata | `game/gm.py::_attach_model_route_metadata`, `_log_model_route` |
| BCR-09 | Backend compatibility surface | `game/config.py`, `game/model_routing.py`, `docs/compatibility_residue_register.md` row `CR-14` |

The registry includes purpose, consumers, compatibility requirements,
replay/provenance implications, versioning status, verification methods, and
future extensibility notes for each contract.

## 3. Ownership Mapping

| Owner Category | Registry Responsibility |
|---|---|
| Model routing owner | Route decision inputs, selected model, route family, route reason, and disabled-routing fallback behavior. |
| Configuration owner | Environment loading, lazy API key validation, and model environment fallback chain. |
| GM/model-call owner | Live backend call adapter, provider response normalization, model-route metadata, and upstream error normalization. |
| Prompt/GM owner | Message shape passed to backend and prompt payload assembly from authoritative state. |
| Upstream preflight owner | Health probe, cached status row, startup diagnostics, and skip-env interpretation. |
| Upstream run-gate owner | Cached-health-to-operator gate mapping and presentation. |
| Compatibility planning owner | Legacy backend configuration inventory and retirement prerequisites. |

Each owner is documented with explicit non-ownership boundaries to prevent
backend contracts from absorbing gameplay resolution, Final Emission legality,
protected replay policy, or provenance authority.

## 4. Consumer Mapping

| Consumer | Consumed Contracts |
|---|---|
| `game.api` shared turn pipeline | GPT call adapter, prompt message adapter, upstream-dependent run gate. |
| Retry orchestration | GPT call adapter, upstream error normalization, backend diagnostics metadata. |
| Model routing tests | Model routing, configuration, call adapter, diagnostics metadata. |
| Upstream preflight tests | Configuration, error normalization, preflight status. |
| Upstream run-gate tests | Preflight status and run-gate payloads. |
| Protected/golden replay | Finalized downstream payloads that may indirectly contain backend diagnostics. |
| Compatibility register | Backend model configuration and legacy routing compatibility. |
| Documentation/governance reviewers | All backend contract registry rows. |

## 5. Compatibility Assessment

The registry records the active backend compatibility requirements:

| Compatibility Surface | Status | Requirement |
|---|---|---|
| `MODEL_NAME` legacy env var | Permanent Compatibility | Continue to seed `DEFAULT_MODEL_NAME` when newer env vars are omitted. |
| `ENABLE_MODEL_ROUTING=false` | Active compatibility | Keep calls on `DEFAULT_MODEL_NAME` without player-facing schema changes. |
| Single OpenAI Responses API adapter | Active | Keep provider-specific response handling inside the backend boundary. |
| Safe fallback GM dict on upstream exception | Active | Preserve expected response shape for API callers. |
| Cached upstream preflight | Active | Run gate consumes cache only and performs no hidden network probe. |
| Route metadata in GM output | Active | Keep metadata diagnostic unless separately promoted. |

## 6. Version Status

The registry documents current versioning as stable but mostly unversioned by
formal schema:

| Contract Area | Version Status |
|---|---|
| Model route decision | Stable unversioned dataclass. |
| Backend env vars | Stable env-var contract with legacy compatibility. |
| GM output from `call_gpt` | Stable dict shape by convention. |
| Upstream error normalization | Stable internal dict shape. |
| Preflight status | Stable typed dict. |
| Upstream run gate | Stable dict shape. |
| Backend diagnostics metadata | Stable key set by convention. |

Future versioned backend/provider work can now use the registry as the contract
publication surface rather than rediscovering backend conventions.

## 7. Verification Strategy

Package verification was documentation-focused:

1. Confirm the Backend Contract Registry exists.
2. Confirm registry source references resolve to existing repository files.
3. Confirm cross-links from existing architecture/governance docs were added.
4. Search the registry and linked docs for expected backend contract anchors.
5. Confirm no backend implementation, tests, scripts, data, artifacts, CI, or
   generated audit outputs were changed by this package.
6. Review the registry for required fields: owner, authoritative implementation,
   consumers, compatibility, replay/provenance implications, version status,
   verification, and future extensibility notes.

Focused backend tests were not run because this package did not change backend
behavior. The registry names the required focused test commands for future
behavioral backend changes.

## 8. Verification Results

| Verification | Result |
|---|---|
| `Test-Path docs\backend_contract_registry.md` | Passed. |
| `Test-Path` for referenced implementation files: `game\model_routing.py`, `game\gm.py`, `game\api_upstream_preflight.py`, `game\upstream_dependent_run_gate.py`, `game\upstream_dependent_run_gate_presentation.py` | Passed. |
| `rg` for registry anchors and cross-links in `docs/backend_contract_registry.md`, `docs/governance_refresh_workflow.md`, `docs/model_routing_architecture.md`, `docs/README.md` | Passed. |
| Scope check for `game`, `tests`, `scripts`, `.github`, `data`, and `artifacts` | Passed for AR-BT: no backend/runtime/test/CI/data/artifact changes were made by this package. |

Existing dirty-worktree changes from earlier packages remain present and were
not reverted.

## 9. Risks

| Risk | Assessment | Mitigation |
|---|---|---|
| Documentation appears to publish new behavior | Low. Registry states that implementation modules remain authoritative. | Registry repeatedly marks itself documentation-only and does not add new runtime surfaces. |
| Backend/provider ownership ambiguity | Reduced. Contracts now name canonical owners and non-owner boundaries. | Future backend changes should update the relevant BCR row and focused tests. |
| Compatibility retirement by implication | Low. Registry points legacy env-var retirement back to the Compatibility Residue Register. | Any retirement requires a separate package. |
| Replay/provenance confusion | Low. Each row classifies replay/provenance implications and prevents backend diagnostics from becoming replay/provenance authority. | Reviewers should use the registry checklist before backend changes. |
| Future provider expansion drift | Medium if providers are added without registry updates. | Governance workflow now lists the Backend Contract Registry as a governed artifact. |

## 10. Package Closeout

Was the Backend Contract Registry successfully implemented?

Yes. `docs/backend_contract_registry.md` now centralizes current backend-facing
contracts and records owner, implementation, consumer, compatibility,
replay/provenance, versioning, verification, and extensibility information.

Are backend contracts now centrally discoverable?

Yes. The registry is linked from `docs/governance_refresh_workflow.md`,
`docs/model_routing_architecture.md`, and `docs/README.md`.

Can future backend expansion proceed using explicit architectural contracts?

Yes. Future backend or provider work can now begin from explicit BCR rows and
the verification commands named by contract area.

## 11. Campaign Assessment

Campaign 5 can proceed. Backend contract coverage is sufficient for current
repository evidence: the registry covers model routing, configuration, call
adapter, prompt message adapter, response/error normalization, preflight,
run-gate, diagnostics, and compatibility.

Additional backend contract refinement is not required before the next package
unless future repository evidence introduces a new backend-facing surface.

## 12. Recommended Next Cycle

Recommendation: Proceed to Package 7.

Repository evidence:

| Evidence | Result |
|---|---|
| Existing model routing architecture | `docs/model_routing_architecture.md` already defines routing inputs and behavior boundaries. |
| Existing backend implementation surfaces | `game/config.py`, `game/model_routing.py`, `game/gm.py`, `game/api_upstream_preflight.py`, and run-gate modules exist and are referenced. |
| Compatibility evidence | `docs/compatibility_residue_register.md` row `CR-14` documents model routing legacy compatibility. |
| Verification links | Registry names focused tests for model routing, config, preflight, run-gate, and GM adapter behavior. |
| Scope preservation | No backend behavior or runtime files were modified by AR-BT. |

## 13. Files Required for External Review

### Required

| File | Reason |
|---|---|
| `docs/backend_contract_registry.md` | New centralized backend contract registry. |
| `docs/governance_refresh_workflow.md` | Governed artifact cross-link and refresh trigger for backend contract changes. |
| `docs/model_routing_architecture.md` | Existing routing architecture now points to registry. |
| `docs/README.md` | User-facing model configuration docs now point to registry. |
| `AR-BT_backend_contract_registry_implementation.md` | Package implementation closeout. |

### Optional

| File | Reason |
|---|---|
| `game/config.py` | Authoritative backend env-var and lazy secret implementation. |
| `game/model_routing.py` | Authoritative model route decision implementation. |
| `game/gm.py` | Authoritative GPT call adapter, prompt message adapter, error normalization, and route metadata implementation. |
| `game/api_upstream_preflight.py` | Authoritative upstream preflight implementation. |
| `game/upstream_dependent_run_gate.py` | Authoritative upstream-dependent run gate implementation. |
| `game/upstream_dependent_run_gate_presentation.py` | Operator-facing run-gate presentation implementation. |
| `docs/compatibility_residue_register.md` | Backend compatibility evidence, especially `CR-14`. |
| `tests/test_model_routing_config.py`, `tests/test_model_routing_runtime.py`, `tests/test_model_routing_escalation.py` | Focused model routing verification references. |
| `tests/test_api_upstream_preflight.py`, `tests/test_upstream_dependent_run_bhc2.py`, `tests/test_upstream_dependent_run_gate_presentation.py` | Focused preflight and run-gate verification references. |
