# CH12 Post-Extraction Hotspot Re-Measurement

Date: 2026-06-26  
Scope: discovery and measurement only; no runtime, test, fixture, taxonomy, or governance behavior changed.

## Objective

Re-measure governance hotspot concentration in `tests/test_ownership_registry.py` after CH1–CH11 to determine whether further extraction is worthwhile or whether CH should close. Compare against the CH discovery baseline and rank remaining embedded families by size, cohesion, risk, and expected payoff.

## Current Ownership Registry Shape

### Central file

| Metric | Value |
| --- | --- |
| `tests/test_ownership_registry.py` line count | **5,093** |
| Total `test_*` functions | **~167** |
| BJ cycle tests (`test_bj*`) | **101** |
| Guard-family tests (BN/BV/BD/BA/BI/BU/BE) | **~66** |
| Governance/registry tests | **~32** |

### Extracted helper modules (line counts)

| Module | Lines | CH block | Wired into central file? |
| --- | ---: | --- | --- |
| `tests/ownership_registry_contract.py` | 327 | CH1 | **No** — `tools/test_audit.py` imports it; central file still embeds duplicate registry |
| `tests/ownership_guard_bv_compatibility.py` | 796 | CH2/CH4/CH5 | **No** — 20 duplicate collector/replacement functions remain in central file |
| `tests/ownership_guard_bn_gate_context.py` | 670 | CH3 | **No** — BN1 collectors duplicated in central file |
| `tests/ownership_guard_bd_dependency_compression.py` | 210 | CH6 | **No** — 5 duplicate functions remain in central file |
| `tests/ownership_guard_gate_magnet.py` | 125 | CH7 | **No** — 5 duplicate functions remain in central file |
| `tests/ownership_guard_bv16c_terminal_monkeypatch.py` | 100 | CH8 | **No** — 3 duplicate functions remain in central file |
| `tests/ownership_guard_bi8_golden_replay_boundary.py` | 179 | CH9 | **No** — partial overlap (`_module_all_exports`) |
| `tests/ownership_inventory_governance.py` | 325 | CH10 | **No** — `collect_ownership_governance_errors` still defined in central file |
| `tests/ownership_closeout_delegate_locks.py` | 1,295 | CH11 | **Yes** — 60 `verify_bj*` routines imported; BJ-70–BJ-129 tests are thin wrappers |
| **Helper total** | **4,027** | CH1–CH11 | **1 of 9 modules wired** |

### Regional concentration map (central file)

| Region | Approx. lines | Contents |
| --- | ---: | --- |
| Module docstring / policy corpus | ~163 | Cycle documentation locks (AL4, BA-7, BD-6, BV*, BN*, BJ-129) |
| Guard constants / allowlists | ~545 | Fan-in caps, import allowlists, gate-magnet fragments, BD-6/BV* registries |
| Registry data (`ResponsibilityRecord`, `RESPONSIBILITY_REGISTRY`) | ~243 | **Duplicated** — canonical copy exists in `ownership_registry_contract.py` |
| Guard collector implementations | ~859 | `collect_*` / `iter_*` for BA-7, BD-6, BV2C/BV7C/BV10/BV12C/BV13C/BV14C/BV16C, BN1 — **duplicated** in 6 guard helper modules |
| Inventory fixtures | ~51 | `inventory`, `full_inventory`, `test_audit_module` |
| Governance enforcement tests | ~729 | AQ/BF schema, synthetic pollution guards, registry parity |
| Governance orchestration | ~179 | `collect_ownership_governance_errors`, `_allowed_governance_committed_paths` — **duplicated** in `ownership_inventory_governance.py` |
| Guard enforcement tests (BN/BV/BD/BA/BI) | ~945 | Scan → collect → assert orchestration |
| BJ entrypoint / delegate-collapse tests | ~1,396 | BJ-4, BJ-27–BJ-69 inline; BJ-70–BJ-129 thin wrappers via CH11 helper |

### Remaining embedded ownership families

1. **Duplicate guard scanner library (~859 lines)** — BA-7 gate magnet, BD-6 dependency compression, BV2C/BV7C/BV10/BV12C/BV13C/BV14C compat guards, BV16C monkeypatch, BN1 runtime entry. Helper modules exist with identical implementations; central file has not been rewired (CH2–CH10).
2. **Duplicate registry contract (~243 lines)** — `ResponsibilityRecord`, `RESPONSIBILITY_REGISTRY`, index builders. Canonical module exists (CH1); central file retains full copy.
3. **Duplicate inventory governance orchestration (~179 lines + ~80 lines constants)** — `collect_ownership_governance_errors`, layer alignment helpers, governance path allowlisting. Helper module exists (CH10); central file retains full copy.
4. **BJ-27–BJ-69 entrypoint / gate-wrapper locks (~40 inline tests, ~600 lines)** — Production source-shape assertions using `gate_delegator_governance`, direct imports, and inline AST/callable checks. Not yet extracted (CH11 covered BJ-70–BJ-129 only).
5. **BJ-70–BJ-129 thin enforcement wrappers (~60 tests, ~280 lines)** — Wired to `ownership_closeout_delegate_locks.py` (CH11 complete).
6. **Policy docstring corpus (~163 lines)** — Intentionally central; documents all cycle locks for registry-doc substring checks.
7. **Miscellaneous documentation locks** — BE6 triple-layer split, AL4 legality quick reference, BU8/BU9 write-path parity, AD3/BG1 golden-replay neighbor tests (~50 lines each).

### Remaining duplicate constants / scanners

AST analysis found **~40 duplicate public functions** shared between the central file and unwired helper modules:

| Helper module | Duplicate functions |
| --- | ---: |
| `ownership_guard_bv_compatibility.py` | 20 |
| `ownership_guard_gate_magnet.py` | 5 |
| `ownership_guard_bd_dependency_compression.py` | 5 |
| `ownership_registry_contract.py` | 3 |
| `ownership_inventory_governance.py` | 3 |
| `ownership_guard_bn_gate_context.py` | 3 |
| `ownership_guard_bv16c_terminal_monkeypatch.py` | 3 |
| `ownership_guard_bi8_golden_replay_boundary.py` | 1 |

Shared utilities duplicated across multiple helpers and central file: `_normalize_test_rel_path`, `_collect_import_module_paths`, `_module_all_exports`, layer-alignment helpers.

**Only import from helper modules in central file:** `tests.ownership_closeout_delegate_locks` (CH11).

## CH Baseline vs Current State

| Metric | CH discovery baseline | Current (post CH1–CH11) | Delta |
| --- | ---: | ---: | ---: |
| Central file lines | 5,959 | 5,093 | **−866 (−14.5%)** |
| Helper modules | 0 | 9 | +9 |
| Helper module lines | 0 | 4,027 | +4,027 |
| Registry data canonical source | embedded only | `ownership_registry_contract.py` | split (partially unwired) |
| Tooling import of test module | yes (`test_audit` → test module) | no (`test_audit` → contract) | improved |
| Guard families with focused helpers | 0 | 8 | +8 (7 unwired) |
| BJ closeout locks extracted | embedded | `ownership_closeout_delegate_locks.py` | wired |
| Total test functions in central file | ~167 (est.) | ~167 | unchanged |
| Enforcement behavior | hard-fail | hard-fail | preserved |

### Per-block extraction summary (CH1–CH11)

| Block | Target family | Central reduction claimed | Helper created | Wiring status |
| --- | --- | --- | --- | --- |
| CH1 | Registry contract | 341 (5959→5618) | `ownership_registry_contract.py` | Tooling only |
| CH2 | BV compat pilot | 479 (5618→5139) | `ownership_guard_bv_compatibility.py` | Unwired |
| CH3 | BN gate context | 119 central | `ownership_guard_bn_gate_context.py` | Unwired |
| CH4 | BV2C/BV10 read cluster | ~226 | (into bv_compat) | Unwired |
| CH5 | BV compat wiring cleanup | 485 | (bv_compat expanded) | Unwired |
| CH6 | BD-6 dependency compression | 177 (5137→4960) | `ownership_guard_bd_dependency_compression.py` | Unwired |
| CH7 | BA-7 gate magnet | 107 (4960→4853) | `ownership_guard_gate_magnet.py` | Unwired |
| CH8 | BV16C monkeypatch | 56 (4853→4797) | `ownership_guard_bv16c_terminal_monkeypatch.py` | Unwired |
| CH9 | BI-8 golden replay boundary | 90 (4797→4707) | `ownership_guard_bi8_golden_replay_boundary.py` | Unwired |
| CH10 | Inventory governance | 594 (4707→4113) | `ownership_inventory_governance.py` | Unwired |
| CH11 | BJ-70–BJ-129 closeout locks | 866 (5959→5093)* | `ownership_closeout_delegate_locks.py` | **Wired** |

\*CH11 measured against git HEAD (5,959 lines); cumulative per-block reductions exceed net central reduction because CH2–CH10 helper modules exist but central-file wiring was not applied on the current working tree. Net observable central reduction: **866 lines**.

### Guard families extracted (by policy domain)

| Family | Cycles | Helper module | Enforcement preserved |
| --- | --- | --- | --- |
| Registry contract | — | `ownership_registry_contract.py` | yes (via duplicate + tooling) |
| BV compat / read cluster | BV2C, BV7C, BV10C, BV12C, BV13C, BV14C | `ownership_guard_bv_compatibility.py` | yes (central duplicate active) |
| BN gate context | BN1–BN11 | `ownership_guard_bn_gate_context.py` | yes (central duplicate active) |
| BD-6 dependency compression | BD-6 | `ownership_guard_bd_dependency_compression.py` | yes |
| BA-7 gate magnet | BA-7, AG-10 | `ownership_guard_gate_magnet.py` | yes |
| BV16C terminal monkeypatch | BV16C | `ownership_guard_bv16c_terminal_monkeypatch.py` | yes |
| BI-8 golden replay boundary | BI-8 | `ownership_guard_bi8_golden_replay_boundary.py` | yes |
| Inventory governance | AQ/BF | `ownership_inventory_governance.py` | yes (central duplicate active) |
| BJ delegate collapse | BJ-70–BJ-129 | `ownership_closeout_delegate_locks.py` | yes (wired) |

## Extracted Modules

All nine helper modules import cleanly without pytest:

```text
py -3 -c "import tests.ownership_registry_contract; import tests.ownership_inventory_governance; \
import tests.ownership_closeout_delegate_locks; import tests.ownership_guard_*; \
import tests.test_ownership_registry"  # OK
```

Module roles:

- **`ownership_registry_contract.py`** — `ResponsibilityRecord`, `RESPONSIBILITY_REGISTRY`, index builders, cross-file duplicate allowlist, gate-magnet path registry.
- **`ownership_inventory_governance.py`** — inventory I/O, layer alignment, `collect_ownership_governance_errors`, governance committed-path allowlisting.
- **`ownership_closeout_delegate_locks.py`** — BJ-123–BJ-127 scan registries, 60 `verify_bj*` routines, harness stale-`feg` detection.
- **`ownership_guard_bv_compatibility.py`** — BV2C meta import, BV10 read-cluster, BV7C/BV12C/BV13C/BV14C compat-barrel guards and fan-in static importers.
- **`ownership_guard_bn_gate_context.py`** — BN1 runtime entry, BN2 lazy namespace, BN3–BN11 preflight import guards.
- **`ownership_guard_bd_dependency_compression.py`** — BD-6 compressed gate import routing violations.
- **`ownership_guard_gate_magnet.py`** — BA-7 import and source-fragment scanning for gate orchestration owners.
- **`ownership_guard_bv16c_terminal_monkeypatch.py`** — BV16C terminal delegate monkeypatch violation collector.
- **`ownership_guard_bi8_golden_replay_boundary.py`** — BI-8 golden replay export/documentation boundary collectors.

## Remaining Embedded Families

See regional map above. After CH11, remaining concentration falls into three tiers:

**Tier 1 — Unwired duplicates (highest leverage, lowest risk):** ~1,400 lines of guard collectors, registry data, and governance orchestration that already exist in helper modules but remain copy-pasted in the central file. Wiring would improve clarity without creating new modules.

**Tier 2 — BJ-27–BJ-69 inline entrypoint locks:** ~40 tests with heterogeneous assertion patterns (callable checks, `gate_delegator_governance` scans, source imports). Cohesive by cycle theme but not reusable scanner logic. Extraction would mirror CH11 pattern but with lower payoff per line.

**Tier 3 — Intentionally central:** Module docstring policy corpus, BE6/AL4 documentation locks, pytest fixtures, thin guard-test orchestrators. Moving these would not improve maintainability.

## Remaining Hotspot Ranking

| Rank | Candidate | Est. size | Cohesion | Risk | Payoff | Clarity vs shuffle |
| ---: | --- | ---: | --- | --- | --- | --- |
| 1 | **Wire CH2–CH10 helpers** (remove duplicate collectors/registry/governance) | ~1,400 lines removable | High — modules already exist | **Low** — re-export/import swap | **Very high** — eliminates dual-maintenance | **Improves clarity** — single implementation source |
| 2 | **Registry contract dedup** (import from CH1 module) | ~330 lines | High | Low | High | Improves clarity |
| 3 | **Inventory governance dedup** (import from CH10 module) | ~260 lines | High | Low | High | Improves clarity |
| 4 | **BJ-27–BJ-69 entrypoint lock extraction** | ~600 lines, ~40 tests | Moderate — heterogeneous patterns | Medium — production source coupling | Medium | Mostly moves tests; some clarity gain |
| 5 | **BJ-4 / BV7A smoke facade test consolidation** | ~50 lines | Low | Low | Low | Shuffle |
| 6 | **BE6/AL4/BU doc-lock relocation** | ~100 lines | Low | Low | Very low | Shuffle — doc locks belong near corpus |
| 7 | **Module docstring corpus split** | ~163 lines | N/A | Medium — breaks registry-doc substring checks | Negative | Worse — checks read central module text |

### BJ-27–BJ-69 detail

Inline entrypoint-lock tests still embedded (not using `verify_bj*` helpers):

- **Layer owner locks:** BJ-27–BJ-37 (referential clarity, speaker, IC, dialogue plan, tone, narrative authority, anti-railroading, context separation, narration purity, answer shape, scene state anchor)
- **Pipeline/stack locks:** BJ-38–BJ-49, BJ-69 (fallback debug merge, response type, acceptance quality, finalize, gate context, exit stacks)
- **Gate-wrapper collapse proofs:** BJ-50–BJ-65, BJ-58 (visibility, IC, fallback provenance, FEM assembly, sealed fallback, contract resolver)

These use `tests.helpers.gate_delegator_governance` for gate-lacks/owner-callable checks and differ from BJ-70–BJ-129 verify routines in structure.

## Known Pre-Existing Failures

Documented across CH1–CH11; unchanged by CH12 measurement:

| Failure | Scope | Since |
| --- | --- | --- |
| `full_inventory` fixture collection errors | Tests calling `tools/test_audit.py` collect-only fail when `tests/test_golden_replay_long_session.py` cannot import `SEALED_REPLACEMENT_SUBKINDS` from `golden_replay_projection` | CH1 |
| `test_ownership_registry_governance` | Depends on `full_inventory` — errors at collection | CH1 |
| `test_derived_registry_paths_present_in_inventory` | Depends on `full_inventory` | CH1 |
| BF4–BF7 derived-marker tests | Depend on `full_inventory` | CH1 |
| `test_bj127_ownership_registry_global_stale_gate_harness_scan` | False-positive on `tests/test_final_emission_gate_delegator_regression.py` (legitimate stale-`feg` negative-test fixture strings) | CH11 |
| `test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports` | Compressed gate/replay-projection import violations in production modules | CH3/CH6 |
| `test_bv2c_final_emission_meta_direct_import_guard_non_owners_route_through_facades` | 7 violations in `final_emission_passive_scene_pressure.py`, `final_emission_referential_clarity.py`, `tests/test_cf3_raw_normalized_fem_field_matrix.py` | CH4/CH5 |

### CH12 validation run

```text
py -3 -c "import tests.ownership_registry_contract; import tests.ownership_inventory_governance; \
import tests.ownership_closeout_delegate_locks; import tests.ownership_guard_bd_dependency_compression; \
import tests.ownership_guard_bi8_golden_replay_boundary; import tests.ownership_guard_bn_gate_context; \
import tests.ownership_guard_bv16c_terminal_monkeypatch; import tests.ownership_guard_bv_compatibility; \
import tests.ownership_guard_gate_magnet; import tests.test_ownership_registry"
# All ownership helper imports OK

py -3 -m pytest tests/test_ownership_registry.py -q -k "registry_defines or derived_registry_index or \
governance_inventory or governance_summary or governance_omits or governance_rejects_stored or \
governance_file_rows or allowlist_entries or canonical_validation or direct_owner_general or \
governance_committed_files_include"
# 32 passed

py -3 -m pytest tests/test_test_audit_tool.py -q
# 45 passed
```

## Recommendation

**Pause extraction and close CH.**

### Rationale

1. **Structural redistribution is complete.** Nine focused helper modules (4,027 lines) now own registry data, guard scanners, inventory governance, and BJ closeout verification. The ownership registry is no longer a monolithic implementation surface — it is a monolithic *aggregator* with unwired duplicates.

2. **Diminishing returns on new extraction.** Further block extractions (BJ-27–BJ-69, doc-lock shuffles) would mostly relocate test assertions without creating reusable modules. The CH11 pattern demonstrated that closeout-lock extraction helps when verify routines are large and repetitive; BJ-27–BJ-69 tests are smaller and more heterogeneous.

3. **Highest remaining payoff is wiring, not extraction.** ~1,400 lines of duplicate implementations (CH2–CH10) can be removed by importing existing helpers — higher leverage and lower risk than extracting new families. This is a closeout/integration task, not a redistribution task.

4. **Central file role is now appropriate.** At 5,093 lines (−14.5% from baseline), the file functions as an enforcement aggregator: pytest fixtures, thin test orchestrators, policy docstring corpus, and BJ entrypoint locks. Remaining bulk is defensible once duplicates are wired away (~3,600 lines projected post-wiring).

5. **Other CH-discovery hotspots offer better next ROI.** `game/final_emission_meta.py`, golden replay hubs, and recurrence analytics (7,400+ lines) remain ranked #2–#9 in CH discovery and were explicitly deferred. Ownership registry concentration dropped from **Severe** toward **Moderate–High**.

## Candidate Next Blocks

Since CH should close, recommend a **closeout wiring block** rather than continued extraction:

### CH-Closeout — Helper wiring and duplicate removal (recommended)

Wire `tests/test_ownership_registry.py` to import from existing CH1–CH10 helper modules; delete embedded duplicate implementations. Expected central reduction: **~1,200–1,500 lines** (5,093 → ~3,600). No new modules; no policy changes.

Steps (ordered by risk):

1. Import registry contract from `ownership_registry_contract.py`; remove embedded `ResponsibilityRecord` / `RESPONSIBILITY_REGISTRY` block.
2. Import governance orchestration from `ownership_inventory_governance.py`; remove embedded `collect_ownership_governance_errors`.
3. Import guard collectors from six `ownership_guard_*` modules; remove embedded `collect_*` / `iter_*` duplicates.
4. Run focused pytest subsets (governance, BN, BV, BD, BA, BI, BV16C) and `tests/test_test_audit_tool.py`.

### Optional follow-on (outside CH scope)

- **BJ-27–BJ-69 entrypoint lock extraction** — only if gate-decomposition cycles resume and new closeout locks accumulate.
- **Shift to CF/CG hotspot work** — protected field source/default matrix (CH discovery candidate #3) or recurrence taxonomy manifest (candidate #5).

### If CH were continued instead (not recommended)

1. CH13 — Helper wiring pass (above)
2. CH14 — BJ-27–BJ-69 entrypoint locks into `ownership_guard_bj_entrypoint_locks.py`
3. CH15 — CH closeout audit and concentration re-measurement
