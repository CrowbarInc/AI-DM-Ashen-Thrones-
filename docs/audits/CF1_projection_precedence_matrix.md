# CF1 — Projection Precedence Contract Matrix

## Executive Summary

Every multi-source replay projection precedence chain in the acceptance golden-replay path is now documented with an explicit decision table, a canonical owner, and focused table-driven tests where gaps existed. **Runtime behavior is unchanged** — this block adds contract documentation and failure locality only.

**Projection Precedence Concentration (primary metric):** Before CF1, major precedence rules were embedded inside `golden_replay_projection_extractors.py` (978 LOC) and exercised primarily through `tests/test_golden_replay_projection.py` (28 broad tests). After CF1, **seven acceptance-side precedence chains** have dedicated contract matrices and **39 new unit tests** across four focused modules that fail with the owning function name in the traceback.

Remaining concentration: reporting tools (`fallback_incidence_report`, `compare_scenario_spine_reruns`, `run_scenario_spine_validation`) implement **parallel** route/lineage/fallback precedence with intentional surface-specific differences (notably empty-list lineage behavior). These are documented as secondary owners, not merged into acceptance.

---

## Projection Chains

| Chain | Canonical Owner | Consumers | Existing Tests |
|-------|-----------------|-----------|----------------|
| Selected speaker ID | `_resolve_selected_speaker_id` — `tests/helpers/golden_replay_projection_speaker.py` | `project_turn_observation`, parity, failure classifier, trend normalization | BX3 parity in `test_golden_replay_projection.py`; **CF1:** `test_cf1_speaker_projection_precedence.py` |
| Selected speaker source label | Same function | `selected_speaker_source` on observed turn | Same as above |
| Final speaker observation read (replay) | `read_final_speaker_observation_for_replay` — `golden_replay_projection_speaker.py` | `final_speaker_observation`, `speaker_projection_parity` | BX3 parity; partial lane test in `test_golden_replay_projection.py`; **CF1:** `test_cf1_speaker_projection_precedence.py` |
| Final speaker resolution (runtime) | `build_final_speaker_observation` — `game/final_emission_speaker_observation.py` | Stamps evidence consumed by replay read helper | `test_final_emission_speaker_observation.py` |
| Fallback family (FEM two-field) | `project_replay_fallback_family_from_fem` — `golden_replay_projection_fallbacks.py` | Protected `fallback_family`, classifiers, incidence tools | Dual-family tests in `test_golden_replay_projection.py`, `test_final_emission_meta.py`; **CF1:** `test_cf1_fallback_family_precedence.py` |
| Fallback family (lineage bridge) | `_project_replay_fallback_family` → `_resolve_fallback_family` — same module | Same | Opening projection integration; **CF1:** `test_cf1_fallback_family_precedence.py` |
| Runtime lineage (payload vs FEM rebuild) | `_runtime_lineage_events_from_payload` — `golden_replay_projection_extractors.py` | `runtime_lineage_events`, bridge fallback, long-session summaries | `test_golden_replay_fallback_opening_projection.py`; **CF1:** `test_cf1_runtime_lineage_precedence.py` |
| Route kind (acceptance) | `_resolve_route_kind` — `golden_replay_projection_extractors.py` | Protected `route_kind`, presence routing | Indirect via projection tests; **CF1:** `test_cf1_route_and_trace_precedence.py` |
| Trace source (acceptance inputs) | `_trace_from_payload_or_snapshot` — `golden_replay_projection_extractors.py` | Trace nest fields on observed turn | Indirect; **CF1:** `test_cf1_route_and_trace_precedence.py` |
| FEM read (sidecar vs legacy) | `read_final_emission_meta_dict` — `game/final_emission_meta.py` | All FEM-backed projection | `test_final_emission_channel_separation.py` |
| FEM read (payload envelope) | `read_final_emission_meta_from_turn_payload` — `game/final_emission_meta.py` | Acceptance FEM inputs | `test_final_emission_meta.py` |
| Emission-debug lane read | `read_emission_debug_lane_from_turn_payload` — `game/final_emission_meta.py` | Speaker read, FEM lane | `test_final_emission_meta.py` |
| Accept-path `final_emitted_source` ladder | `infer_accept_path_final_emitted_source` — `game/final_emission_meta.py` | Runtime FEM stamping (upstream of replay) | `test_final_emission_meta.py`, Block M4 lock in `test_final_emission_gate_selector_snapshots.py` |
| Runtime fallback kind selection | `_fem_selected_fallback_projection` — `game/final_emission_replay_projection.py` | `build_fem_runtime_lineage_events` | Extensive `test_final_emission_meta.py`, fallback family projection files |
| Recurrence-key detail token | `build_recurrence_key` — `game/runtime_lineage_telemetry.py` | Lineage telemetry / recurrence | `test_runtime_lineage_telemetry.py` |
| Route kind (reporting) | `_route_kind` — `tools/fallback_incidence_report.py` | Fallback incidence reports | `test_fallback_incidence_report.py` |
| Runtime lineage (transcript meta) | `_runtime_lineage_events_for_turn` — `tools/run_scenario_spine_validation.py` | Scenario-spine transcripts | `test_run_scenario_spine_validation.py` |

---

## Precedence Matrices

### 1. Selected speaker ID

**Owner:** `_resolve_selected_speaker_id`

| Inputs | Expected Winner | Expected Output | Covered By |
|--------|-----------------|-----------------|------------|
| `final_reply_owner` present | Trace key 1 | ID + source `turn_trace.social_contract_trace` | CF1 speaker matrix |
| `final_reply_owner` null, `reply_owner_actor_id` present | Trace key 2 | ID + trace source | CF1 |
| Keys 1–2 null, `visible_grounded_speaker` present | Trace key 3 | ID + trace source | CF1 |
| Trace empty, snap has `interaction_context.active_interaction_target_id` | Transcript snapshot | ID + snapshot source path | CF1, `test_transcript_gauntlet_campaign_cleanliness.py` |
| Trace + snap empty, `social.npc_id` present | Resolution fallback | ID + `resolution.social.npc_id` | CF1 |
| All absent | None | `(None, None)` | CF1 |
| Conflicting trace vs snap vs resolution | Trace (first key wins) | Trace ID | CF1 |
| `final_reply_owner=""` (empty string) | Trace (non-None) | ID `""`, source `None` (falsy guard) | CF1 |

### 2. Final speaker observation read (replay)

**Owner:** `read_final_speaker_observation_for_replay`

| Inputs | Expected Winner | Expected Output | Covered By |
|--------|-----------------|-----------------|------------|
| Lane has mapping `final_speaker_observation` | Emission-debug lane | Lane observation dict | CF1 |
| Lane absent, `gm_output.metadata.emission_debug` has obs | Runtime finalize path | GM-output observation | CF1 |
| Lane + GM nested absent, payload root has emission_debug | Payload direct read | Payload observation | CF1 |
| All absent | None | `None` | CF1, `test_golden_replay_projection.py` |
| Lane value non-mapping | Fall through | Next source | CF1 |
| Lane null | Fall through | GM-output or payload | CF1 |
| Lane vs GM conflicting values | Lane | Lane canonical_speaker_id | CF1 |

### 3. Fallback family (FEM two-field)

**Owner:** `project_replay_fallback_family_from_fem` via `_first_present(fem, REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS)`

| Inputs | Expected Winner | Expected Output | Covered By |
|--------|-----------------|-----------------|------------|
| Both `fallback_family_used` and `realization_fallback_family` | Diegetic first | `fallback_family_used` value | CF1, `test_golden_replay_projection.py` |
| `fallback_family_used` null, realization present | Provenance field | `realization_fallback_family` | CF1 |
| Both absent | None | `None` | CF1 |
| Both explicit null | None | `None` | CF1 |
| `fallback_family_used=""` | Diegetic (non-None) | `""` | CF1 |
| Conflicting non-null values | Diegetic | Diegetic value | CF1 |

### 4. Fallback family (lineage bridge)

**Owner:** `_resolve_fallback_family` (after FEM two-field pass)

| Inputs | Expected Winner | Expected Output | Covered By |
|--------|-----------------|-----------------|------------|
| FEM family absent; `final_route=replaced`, source=`neutral_reply_speaker_grounding_bridge`, sealed `fallback_selected` lineage event | Bridge inference | `neutral_reply_speaker_grounding_bridge` | CF1, opening projection test |
| Same route/source but no sealed lineage event | None | `None` | CF1 |
| FEM diegetic present + bridge conditions met | FEM diegetic | Diegetic value (bridge skipped) | CF1 |
| Bridge conditions but `final_route != replaced` | None | `None` | CF1 |

### 5. Runtime lineage (acceptance: payload vs FEM rebuild)

**Owner:** `_runtime_lineage_events_from_payload`

| Inputs | Expected Winner | Expected Output | Covered By |
|--------|-----------------|-----------------|------------|
| Nested `fem_runtime_lineage_events` key present (non-empty list) | Payload stamp | Normalized payload events (max 16) | CF1, opening projection test |
| Key present with explicit `[]` | Payload (authoritative empty) | `[]` — **no FEM rebuild** | CF1, opening projection test |
| Key absent, non-empty FEM | FEM rebuild | `build_fem_runtime_lineage_events(fem)` | CF1 |
| Key absent, empty FEM | None | `[]` | CF1 |
| Payload events conflict with FEM-derived events | Payload | Payload events only | CF1 |

**Note:** Transcript builder (`_runtime_lineage_events_for_turn`) **skips** empty lists and falls through — documented divergence, not a bug.

### 6. Route kind (acceptance)

**Owner:** `_resolve_route_kind`

| Inputs | Expected Winner | Expected Output | Covered By |
|--------|-----------------|-----------------|------------|
| `social_contract_trace.route_selected` present | Trace | Trace value | CF1 |
| Trace absent, `resolution_compact.kind` present | Compact debug | Compact kind | CF1 |
| Both absent, `resolution.kind` present | Resolution | Resolution kind | CF1 |
| All absent | None | `None` | CF1 |
| Trace null | Compact or resolution | Next non-null | CF1 |
| Conflicting trace vs compact vs resolution | Trace | Trace value | CF1 |

### 7. Trace source (acceptance inputs)

**Owner:** `_trace_from_payload_or_snapshot`

| Inputs | Expected Winner | Expected Output | Covered By |
|--------|-----------------|-----------------|------------|
| `payload.debug_traces` has compact entry | Payload traces | Latest compact trace entry | CF1 |
| Payload traces absent, `session.debug_traces` present | Session nested | Session trace entry | CF1 |
| Both absent, `snap.debug.last_debug_trace` present | Snapshot fallback | Snapshot trace dict | CF1 |
| All absent | None | `{}` | CF1 |

### 8. Speaker projection parity (observation vs selection)

**Owner:** `project_speaker_projection_parity` — **does not override** `selected_speaker_id`; compares only.

| Final status | Selected ID vs canonical | Parity status | Covered By |
|--------------|--------------------------|---------------|------------|
| `resolved`, IDs match | Aligned | `aligned` | `test_golden_replay_projection.py` BX3 |
| `resolved`, IDs differ | Mismatch | `mismatch` | BX3 |
| `ambiguous` | Any | `final_ambiguous` (legacy ID preserved) | BX3 |
| `unresolved` | Any | `final_unresolved` | BX3 |
| Observation absent | N/A | `missing_final_observation` | BX3 |

---

## Ownership Findings

| Chain | Single Owner? | Duplicate Logic? | Risk |
|-------|---------------|------------------|------|
| Selected speaker ID | Yes — `golden_replay_projection_speaker.py` | Transcript fallback in `transcript_snapshots.latest_target_id` (called, not duplicated) | Low |
| Final speaker read (replay) | Yes — same module | Runtime `read_final_speaker_observation` is producer read, not a second precedence policy | Low |
| Fallback family FEM | Yes — `golden_replay_projection_fallbacks.py` | Reporting `_observed_family`, rerun `_turn_fallback` scan similar fields with tool-specific paths | Medium (reporting drift) |
| Fallback bridge | Yes — same module | None in acceptance | Low |
| Runtime lineage (acceptance) | Yes — `golden_replay_projection_extractors.py` | Transcript + incidence tools use **different** empty-list semantics | Medium (documented divergence) |
| Route kind (acceptance) | Yes — extractors | `fallback_incidence_report._route_kind`, `compare_scenario_spine_reruns._turn_route`, failure classifier tuple | Medium (reporting-only) |
| Trace source | Yes — extractors | None | Low |
| FEM read paths | Yes — `final_emission_meta.py` | Runtime adapters delegate to same readers | Low |
| Accept-path source ladder | Yes — `infer_accept_path_final_emitted_source` | Replacement paths use direct fallback source (separate contract) | Low (M4 locked) |
| Runtime fallback kind | Yes — `final_emission_replay_projection.py` | Acceptance consumes output; does not re-derive kind | Low |
| `_first_present` helper | Partial | **Duplicated** in `golden_replay_projection_fields.py` and `golden_replay_projection_extractors.py` (identical implementation) | Low (behavioral sync risk) |

---

## Test Coverage

| Chain | Unit | Integration | Golden | Gap |
|-------|------|-------------|--------|-----|
| Selected speaker ID | **CF1** (8 cases) | BX3 parity, BX E2E | Structural invariants | Empty-string source label edge (now documented) |
| Final speaker read | **CF1** (6 cases) | BX3 | Protected BX scenarios | Runtime resolution ladder separate |
| Fallback family FEM | **CF1** (7 cases) | Dual-family projection tests | Golden replay | Malformed non-string field shapes |
| Fallback bridge | **CF1** (4 cases) | Opening projection | — | — |
| Runtime lineage payload | **CF1** (4 cases) | Opening projection | Long-session | Transcript divergent path (intentional) |
| Route kind acceptance | **CF1** (6 cases) | Projection presence | — | — |
| Trace source | **CF1** (4 cases) | Full projection | — | — |
| Accept-path source ladder | M4 lock + meta unit | Gate selector | — | Covered |
| Runtime fallback kind | Meta unit suite | 8 fallback projection files | — | Covered at runtime layer |
| Route kind reporting | Incidence unit | — | — | Not acceptance authority |

---

## Changes Made

### Tests added

| File | Cases | Chains locked |
|------|-------|---------------|
| `tests/test_cf1_speaker_projection_precedence.py` | 14 | Speaker selection + final observation read |
| `tests/test_cf1_fallback_family_precedence.py` | 11 | FEM two-field + bridge resolution |
| `tests/test_cf1_runtime_lineage_precedence.py` | 4 | Payload vs FEM rebuild |
| `tests/test_cf1_route_and_trace_precedence.py` | 10 | Route kind + trace source |

**Total: 39 new parametrized unit tests**, all passing.

### Documentation added

- This file: `docs/audits/CF1_projection_precedence_matrix.md`

### Refactors

- None. Precedence logic was not moved or altered.

### Behavior changes

- **None.** All matrices document and test existing behavior, including edge cases (empty-string trace ID, explicit empty lineage list blocking FEM rebuild).

---

## Remaining Risks

1. **`_first_present` duplication** between `golden_replay_projection_fields.py` and `golden_replay_projection_extractors.py` — identical logic in two modules; a future edit could desync null/absent handling.

2. **Parallel reporting precedence** — `fallback_incidence_report`, `fallback_projection_gap_reality_audit`, and `compare_scenario_spine_reruns` implement route/fallback/lineage selection for diagnostics with broader field scans. They are not wrong, but changes to acceptance precedence will not automatically propagate.

3. **Transcript vs acceptance lineage empty-list semantics** — golden replay treats `fem_runtime_lineage_events: []` as authoritative; scenario-spine transcript builder skips empty lists and rebuilds from FEM. This is intentional but easy to misread as a bug.

4. **Speaker source label falsy guard** — when trace returns empty string ID, source label is `None` despite ID being "selected". Documented in CF1 matrix; not changed.

5. **Broad integration tests still required** — CF1 improves failure locality for precedence owners; `test_golden_replay_projection.py` and protected BX/golden scenarios remain necessary end-to-end gates.

---

## Recommended Next Block

**Proceed with CF2 unchanged** (projection default / unavailable / presence routing matrix), with one priority adjustment:

- CF2 should treat **`_first_present` deduplication** as an optional low-risk hygiene item if touched during presence routing work.
- CF2 should **not** attempt to unify reporting-tool precedence with acceptance — document-only cross-links are sufficient unless a tool explicitly claims acceptance parity.

CF1 acceptance criteria met:

- [x] Every projection precedence chain documented
- [x] Every precedence chain has a canonical owner identified
- [x] Precedence matrices exist for every multi-source acceptance decision
- [x] Focused precedence tests exist for all major acceptance chains
- [x] Runtime behavior unchanged
- [x] Projection failure locality improved (39 narrow tests vs broad integration only)
