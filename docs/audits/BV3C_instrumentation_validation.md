# BV3C — Instrumentation Validation

**Date:** 2026-06-21  
**Field under test:** `referential_clarity_upstream_repair_applied`

---

## Validation checklist

| Check | Result | Evidence |
|---|---|---|
| **Stamped correctly** when repair succeeds | **PASS** | Unit test + code path |
| **Preserved correctly** through visibility/RC stages | **PASS** | Snapshot restore pattern |
| **Emitted correctly** in finalized FEM | **PASS** on eligible turns | `_final_emission_meta` after `finalize_emission_output` |
| **Visible in replay artifacts** | **PASS** (field present when code runs) | Refreshed turns show attempted/eligible/applied flags |
| **Visible in incidence metrics** | **PASS** (reads FEM directly) | `tools/bv3a_referential_clarity_metrics.py` |
| **Non-zero on replay corpus** | **FAIL (expected)** | 0 true — no eligible activations |

**Verdict:** Instrumentation is **functionally correct**; **0% activation reflects eligibility/corpus**, not a missing or broken stamp.

---

## 1. Stamping (write path)

**Owner:** `game.final_emission_referential_clarity.apply_observe_referential_clarity_upstream_repair`

| Event | Meta written |
|---|---|
| Function entry (defaults) | `upstream_repair_attempted=false`, `applied=false`, `eligible=false` |
| Validation fails on observe | `attempted=true`, `eligible=<bool>`, `unrepaired_violation_count=N` |
| Local substitution succeeds | `applied=true`, `entity_id=…`, `unrepaired=0`, `producer_repair_kind=referential_clarity_local_substitution` |

**Code reference:**

```715:719:game/final_emission_referential_clarity.py
    meta["referential_clarity_upstream_repair_applied"] = True
    meta["referential_clarity_upstream_repair_entity_id"] = subst_dbg.get("referential_clarity_repair_entity_id")
    meta["referential_clarity_unrepaired_violation_count"] = 0
    meta["referential_clarity_checked_entities"] = validation.get("checked_entities") or []
    stamp_producer_repair_kind(meta, PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_LOCAL_SUBSTITUTION)
```

**Test evidence:** `tests/test_bv3a_observe_referential_clarity_repair.py::test_observe_dialogue_he_says_repairs_via_upstream_not_hard_fallback` — asserts `referential_clarity_upstream_repair_applied is True`.

---

## 2. Preservation (pipeline)

Visibility and referential enforcement reset referential meta defaults but **preserve upstream repair fields** via snapshot:

```1568:1570:game/final_emission_visibility_fallback.py
    preserved_repair_meta = _referential_clarity_repair_meta_snapshot(meta)
    _apply_default_referential_clarity_meta(meta, passed=None)
    _restore_referential_clarity_repair_meta(meta, preserved_repair_meta)
```

Snapshot keys explicitly include `referential_clarity_upstream_repair_applied` (`_referential_clarity_repair_meta_snapshot` in `final_emission_referential_clarity.py`).

When repair **not** applied, downstream may overwrite violation samples; upstream booleans from attempted-but-failed path **remain** (observed: `attempted=true`, `applied=false` on replay turns).

---

## 3. Emission (finalize / session log)

| Stage | Key | Notes |
|---|---|---|
| FEM dict | `_final_emission_meta` | Canonical key per `FINAL_EMISSION_META_KEY` |
| Finalize | `finalize_emission_output` | Packaging-only; does not strip upstream flags |
| Session log | Nested under turn GM output / debug | Readable via `_walk_mappings` |

Consumer tests use `read_final_emission_meta_dict` / `final_emission_meta_from_output` — same path as replay scanners.

---

## 4. Replay artifact visibility

### Refreshed turns (post-BV3B)

Example: `artifacts/scenario_spine_validation/20260621T123556Z/.../run_debug.json` turn 1:

```json
{
  "referential_clarity_upstream_repair_attempted": true,
  "referential_clarity_upstream_repair_applied": false,
  "referential_clarity_upstream_repair_eligible": false,
  "referential_clarity_unrepaired_violation_count": 1
}
```

Fields are **present and false** — instrumentation emits; repair did not qualify.

### Stale turns (pre-BV3A archive)

44 observe FEM instances: upstream fields **null** — instrumentation did not exist at finalize time. This is **historical absence**, not projection stripping.

---

## 5. Metrics / lineage projection

| Consumer | Reads `upstream_repair_applied`? | Notes |
|---|---|---|
| `tools/bv3a_referential_clarity_metrics.py` | **Yes** | Direct FEM get |
| `game.final_emission_replay_projection.build_fem_runtime_lineage_events` | **No** | Projects `referential_clarity_local_substitution_applied` and hard replacement; upstream flag is diagnostic-only |

Incidence reports using lineage alone would **under-report upstream repair** even if applied — current metric script reads FEM correctly.

---

## 6. False-negative risk assessment

| Risk | Severity | Finding |
|---|---|---|
| Field never stamped | — | Ruled out by unit test |
| Field stripped after stamp | Low | Snapshot restore covers downstream stages |
| Scan reads wrong FEM | **Medium** | Nested/debug + archived pre-BV3A FEM mixed into corpus |
| Validation pass skips `attempted` | **Low** | By design; can look like “not reached” vs “reached and passed” |

---

## Conclusion

`referential_clarity_upstream_repair_applied` is **implemented and wired correctly**. Replay shows **0%** because **no scanned observe turn completes an eligible upstream repair**, not because the field is dropped or never written.
