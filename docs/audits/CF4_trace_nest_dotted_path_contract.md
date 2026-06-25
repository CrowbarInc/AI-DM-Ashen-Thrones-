# CF4 — Trace Nest / Dotted Protected Path Contract

## Executive Summary

Golden replay exposes **4 dotted protected registry paths** nested under `observed["trace"]`, backed by **3 trace containers** with container-level unavailable routing and raw presence. All 37 flat protected fields remain top-level keys on the observed turn; dotted paths are never flattened to top-level keys.

**Nested Projection Contract Clarity (primary metric):** Before CF4, trace nest behavior was locked only through BL3 integration tests and scattered `lookup_observation_path` assertions in `test_golden_replay_projection.py`. After CF4, every dotted path and trace container has a contract row in `tests/helpers/trace_nest_contract.py`, and **23 focused unit tests** in `tests/test_cf4_trace_nest_dotted_path_contract.py` lock extraction, normalization, unavailable inheritance, malformed input, and registry/manifest parity.

**Runtime behavior unchanged.** Trace assembly and unavailable routing were not modified.

---

## Protected Path Inventory

| Category | Count | Examples |
|----------|-------|----------|
| Flat protected fields | 37 | `route_kind`, `fallback_family`, `final_text` |
| Dotted protected fields | 4 | `trace.canonical_entry.target_actor_id`, … |
| Trace containers (unavailable/presence) | 3 | `trace.canonical_entry`, `trace.turn_trace`, `trace.social_contract_trace` |
| Diagnostic-only trace keys | 3 | `canonical_entry_path`, `canonical_entry_reason`, `canonical_entry_target_actor_id` |

### Dotted protected paths

| Protected Path | Source | Owner | Test Owner |
|----------------|--------|-------|------------|
| `trace.canonical_entry.target_actor_id` | `debug_traces[].canonical_entry` or `snap.debug.last_debug_trace` | `project_turn_observation` | `test_cf4_trace_nest_dotted_path_contract.py` |
| `trace.canonical_entry.target_source` | same | same | same |
| `trace.canonical_entry.reason` | same | same | same |
| `trace.social_contract_trace.route_selected` | `debug_traces[].turn_trace.social_contract_trace` (normalized nest) | `project_turn_observation` | same |

---

## Dotted Path Matrix

| Path | Classification | Projection Rule | Notes |
|------|----------------|-----------------|-------|
| `trace.canonical_entry.target_actor_id` | trace_derived | Copy `canonical_entry.target_actor_id` → `observed.trace.canonical_entry` | 1:1 from debug trace |
| `trace.canonical_entry.target_source` | trace_derived | Copy `canonical_entry.target_source` | |
| `trace.canonical_entry.reason` | trace_derived | Copy `canonical_entry.reason` | |
| `trace.social_contract_trace.route_selected` | trace_normalized_nest | Read `turn_trace.social_contract_trace.route_selected`; project as `observed.trace.social_contract_trace` sibling | Source nested; observed nest flattens |

**Not protected but projected on trace nest:**

| Key | Classification | Notes |
|-----|----------------|-------|
| `trace.turn_trace` | trace_derived | Full turn_trace dict; container-only (no protected leaves) |
| `trace.canonical_entry_path` | diagnostic-only | Lifted from debug trace root |
| `trace.canonical_entry_reason` | diagnostic-only | Lifted from debug trace root |
| `trace.canonical_entry_target_actor_id` | diagnostic-only | Lifted from debug trace root |

---

## Trace Container Ownership

| Container | Projection Owner | Extraction Owner | Protected Leaves | Risk |
|-----------|------------------|------------------|------------------|------|
| `trace.canonical_entry` | `project_turn_observation` builds `trace_observed` | `_trace_from_payload_or_snapshot` → `trace.get("canonical_entry")` | 3 dotted paths | Low — single assembly path |
| `trace.turn_trace` | same | `_trace_from_payload_or_snapshot` → `trace.get("turn_trace")` | none | Low — presence/unavailable only |
| `trace.social_contract_trace` | same (extracted from `turn_trace`) | `_trace_from_payload_or_snapshot` → nested read | 1 dotted path | Medium — normalize nest vs source shape |

**Duplication:** None for protected dotted extraction. `route_kind` (flat) and `trace.social_contract_trace.route_selected` (dotted) both read routing evidence — intentional dual surface (CF1 precedence vs trace leaf).

**Normalization:** No separate trace normalizer; malformed `canonical_entry` non-mapping → `{}` at assembly time.

---

## Unavailable Behavior

| Path / Container | Unavailable Rule | Tested | Notes |
|------------------|------------------|--------|-------|
| `trace.canonical_entry` | Container empty → listed unavailable | CF4 + BL3 | Leaf lookups return `MISSING` |
| `trace.turn_trace` | Container empty → listed unavailable | CF4 + BL3 | No protected leaves |
| `trace.social_contract_trace` | Container empty → listed unavailable | CF4 + BL3 | Independent of `turn_trace` presence |
| Dotted leaves (4) | **Inherited** via parent prefix | CF4 parametrized | `protected_path_covered_by_unavailable` |
| Flat protected fields | Per-field `unavailable_key` (CF2) | CF2 | Separate contract |

**Parent/child agreement:** When parent container is unavailable, children are **represented** (AK5/CF4) even if `lookup_observation_path` returns `MISSING`. Unavailable is explicit on container keys only, not repeated per leaf.

---

## Consistency Findings

| Path | Registry | Schema | Manifest | Routing (CF2) | Tests | Status |
|------|----------|--------|----------|---------------|-------|--------|
| Each of 4 dotted paths | Yes | Yes (structural_drift) | Yes | Parent unavailable row | CF4 + BL3 + AK5 | Complete |
| 37 flat paths | Yes | Yes | Yes | CF2 matrix | CF2 + BL3 | Complete (separate block) |
| Trace containers | N/A (not registry paths) | N/A | N/A | CF2 unavailable | CF4 + BL3 | Complete |

**Broad-only coverage before CF4:** Rich trace leaf values in `test_golden_replay_projection.py` (BL2/BL3). CF4 adds per-path parametrized extraction and unavailable inheritance without full turn assembly variance.

---

## Tests Added

| File | Count | Families protected |
|------|-------|-------------------|
| `tests/helpers/trace_nest_contract.py` | (helper) | 4 dotted rows + 3 container rows |
| `tests/test_cf4_trace_nest_dotted_path_contract.py` | 23 | Inventory; dotted extraction; nest normalization; sparse unavailable; parent inheritance; malformed canonical; snapshot fallback; partial trace; diagnostic keys; manifest parity; representation |

**Existing tests retained:** `test_ak5_every_protected_path_is_projected_or_marked_unavailable`, `test_bl3_trace_fixture_presence_pipeline_locked`, `test_cf1_route_and_trace_precedence` (trace source precedence).

---

## Behavior Changes

**None.** CF4 documents and tests existing trace nest semantics:

1. Dotted protected values live under `observed["trace"]`, accessed via `lookup_observation_path(observed, "trace.…")`.
2. `social_contract_trace` is extracted from `turn_trace` but projected as a trace sibling.
3. Empty/malformed containers → unavailable at container granularity.
4. Dotted leaves inherit unavailable representation from parent prefix.

---

## Remaining Risks

1. **Dual route surfaces** — flat `route_kind` and dotted `trace.social_contract_trace.route_selected` can diverge when precedence sources disagree (CF1 owns flat; CF4 owns dotted leaf).

2. **`trace.turn_trace` container** — tracked for presence/unavailable but has no protected leaves; consumers may confuse with nested `social_contract_trace` source shape.

3. **Diagnostic lifted keys** — `canonical_entry_*` top-level trace keys are not protected; drift tooling must not treat them as acceptance schema.

4. **Classifier dotted paths** — excluded from flat classifier evidence (AO2); failures on dotted paths route through structural drift, not optional evidence copy.

5. **No dedicated malformed `turn_trace` test** — only `canonical_entry` malformed case locked; low risk given same `isinstance(..., Mapping)` guard.

---

## Recommended Next Block

**Proceed with CF5 unchanged** (if planned: synthetic row / fixture governance or classifier evidence bridge), with CF4 carry-forwards:

1. Add a single cross-surface test if CF5 touches classifiers: when `route_kind` and `trace.social_contract_trace.route_selected` conflict, document expected drift bucket owner.
2. Consider exporting `dotted_protected_field_paths()` from the public replay facade for tooling.
3. Do **not** flatten dotted paths to top-level observed keys without explicit schema migration — nested lookup is acceptance authority.

CF4 acceptance criteria met:

- [x] Every dotted protected path has a contract row
- [x] Every nested path has a canonical owner (`project_turn_observation` + extraction registry)
- [x] Trace container ownership explicit
- [x] Unavailable routing for nested paths independently testable
- [x] Registry/schema/manifest parity verified for all 4 dotted paths
- [x] 23 focused tests for trace families
- [x] Runtime behavior unchanged
- [x] CF5 can proceed without guessing nested projection policy
