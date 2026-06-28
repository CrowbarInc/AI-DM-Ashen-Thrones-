# CQ4 — First Planned Feature Tranche Closeout

**Date:** 2026-06-28  
**Scope:** First intentionally planned multi-feature tranche — sustained journal improvements after CQ1–CQ3 pilots.  
**Primary metric:** Feature Development Sustainability  
**Theme:** **Journal improvements** (player-facing codex usability, publication seams, exploration→lead freshness)  
**Authority:** [CQ3_cross_subsystem_feature_pilot_closeout.md](CQ3_cross_subsystem_feature_pilot_closeout.md), [CB_feature_boundary_registry.json](docs/audits/CB_feature_boundary_registry.json), [docs/state_authority_model.md](docs/state_authority_model.md)

---

## Executive Summary

CQ4 delivered **five related journal-improvement features** in a single planned tranche, implementing sequentially with targeted validation after each feature and broader validation once at completion.

**Outcome:** **PASS.** All five features landed with **zero** replay-helper, fallback, validator, sanitizer, ownership-registry, or golden-artifact changes. One **small governance addition** (cross-domain allow-list operation for suspicion publication). Tranche totals: **5 production files**, **3 test files**, **8 files overall**.

**Sustainability:** Average **~1.6 production files per feature** and **~1.0 test files per feature** — at or below CQ1–CQ3 pilot averages. Repeated feature work did **not** increase replay, fallback, or corrective-locality pressure.

**Recommendation:** **Proceed with Planned Feature Development** — the architecture absorbed five consecutive player-facing features without architectural drift.

---

## 1. Feature Theme

**Journal improvements** — natural continuation of CQ3's exploration→journal hidden-fact pipeline. Features share:

- `build_player_journal` publication seams (`player_visible_state`)
- Existing lead registry / scene-runtime data already authoritative
- Optional UI surfacing in `static/` (safe `ui_mode_frontend` domain)

Avoided: replay schema expansion, Final Emission redesign, validator redesign, ownership registry expansion, sanitizer redesign.

---

## 2. Tranche Plan (Low → High Risk)

| Order | Feature | Objective | Ownership domains | Est. prod files | Expected tests | Arch risk | Player value |
|---:|---|---|---|---:|---:|---|---|
| 1 | **Journal `status_effects`** | Surface active character conditions in journal snapshot | `player_visible_state`, `combat_checks_adjudication` (read-only) | 1–2 | 1–2 | **Low** | High |
| 2 | **Lead recency in journal rows** | Add `last_touched_turn` / `last_updated_turn` to compact lead records | `player_visible_state` | 1 | 1 | **Low** | Medium |
| 3 | **UI structured lead buckets** | Render active/pursued/stale leads separately; show status effects & suspicion | `ui_mode_frontend` | 2 | 0–1 | **Low–med** | High |
| 4 | **Journal `suspicion_flags` publication** | Publish earned scene-runtime suspicion flags to journal | `player_visible_state`, `hidden_state` (read seam) | 1–2 | 1–2 | **Low–med** | Medium |
| 5 | **Discover-clue lead touch refresh** | Refresh `last_touched_turn` on related registry lead after successful `discover_clue` | `world_scenes_affordances`, leads (via `api.py` orchestration) | 1–2 | 1–2 | **Med** | Medium |

---

## 3. Implementation Record (Sequential)

### CQ4-01 — Journal `status_effects`

| Category | Detail |
|---|---|
| **Production files** | `game/journal.py`, `game/api.py` |
| **Tests** | `tests/test_validation_journal_affordances.py` (`test_journal_status_effects_from_character_conditions`) |
| **Replay changes** | None |
| **Fallback changes** | None |
| **Governance changes** | None |
| **Unexpected coupling** | None — optional `character` / `condition_definitions` kwargs on `build_player_journal`; `compose_state` passes existing loads |

**Validation:** 14 journal affordance tests passed (subset run after feature).

---

### CQ4-02 — Lead recency fields in compact journal rows

| Category | Detail |
|---|---|
| **Production files** | `game/journal.py` |
| **Tests** | `tests/test_lead_obsolescence_and_journal_alignment.py` (expected row shape updated) |
| **Replay changes** | None |
| **Fallback changes** | None |
| **Governance changes** | None |
| **Unexpected coupling** | None |

**Validation:** 8 lead/journal alignment tests passed.

---

### CQ4-03 — UI structured lead buckets

| Category | Detail |
|---|---|
| **Production files** | `static/app.js`, `static/index.html` |
| **Tests** | None new (consumes existing journal API contract) |
| **Replay changes** | None |
| **Fallback changes** | None |
| **Governance changes** | None |
| **Unexpected coupling** | None — journal panel no longer merges `unresolved_leads` into clues list (structured buckets replace flat merge) |

**Validation:** UI contract unchanged at API level; journal backend tests still pass.

---

### CQ4-04 — Journal `suspicion_flags` publication

| Category | Detail |
|---|---|
| **Production files** | `game/journal.py`, `game/state_authority.py` |
| **Tests** | `tests/test_validation_journal_affordances.py`, `tests/test_state_authority.py` |
| **Replay changes** | None |
| **Fallback changes** | None |
| **Governance changes** | **Yes** — `journal_merge_suspicion_flags` added to `HIDDEN_STATE` → `PLAYER_VISIBLE_STATE` allow-list (mirrors CQ3 hidden-fact publication pattern) |
| **Unexpected coupling** | None |

**Validation:** suspicion publication + state authority allow-list tests passed.

---

### CQ4-05 — Discover-clue lead touch refresh

| Category | Detail |
|---|---|
| **Production files** | `game/api.py` |
| **Tests** | `tests/test_validation_journal_affordances.py` (`test_discover_clue_refreshes_registry_lead_touch`) |
| **Replay changes** | None |
| **Fallback changes** | None |
| **Governance changes** | None |
| **Unexpected coupling** | None — uses existing `refresh_session_lead_touch` + `_canonical_registry_lead_id`; no new lead mutation API |

**Validation:** discover-clue cross-subsystem + lead touch tests passed.

---

## 4. Integration Metrics (Tranche Totals)

| Category | Count | Files |
|---|---:|---|
| **Production** | **5** | `game/journal.py`, `game/api.py`, `game/state_authority.py`, `static/app.js`, `static/index.html` |
| **Tests** | **3** | `tests/test_validation_journal_affordances.py`, `tests/test_lead_obsolescence_and_journal_alignment.py`, `tests/test_state_authority.py` |
| **Replay helpers** | **0** | — |
| **Fallback helpers** | **0** | — |
| **Validator helpers** | **0** | — |
| **Golden artifacts** | **0** | Not regenerated |
| **Total (tranche diff)** | **8** | — |

### Per-feature averages (5 features)

| Metric | CQ4 avg | CQ1 | CQ2 | CQ3 | CQ1–CQ3 avg |
|---|---:|---:|---:|---:|---:|
| Production files / feature | **1.6** | 1.0 | 2.0 | 2.0 | **1.67** |
| Test files / feature | **1.0** | 3.0 | 2.0 | 2.0 | **2.33** |
| Total files / feature | **1.6** | 5.0 | 4.0 | 4.0 | **4.33** |
| Ownership domains / feature | **1.4** | 1 | 1 | 3 | **1.67** |
| Replay/fallback/validator touches | **0** | 0 | 0 | 0 | **0** |

**Note:** CQ4 per-feature file counts are lower than single-feature pilots because `game/journal.py` served as the shared publication hub for features 1, 2, and 4 — expected reuse, not spillover.

### Unexpected architectural expansion

**None** beyond one documented allow-list operation (`journal_merge_suspicion_flags`).

---

## 5. Validation Results

### Per-feature targeted runs

Each feature validated before proceeding to the next (journal, lead alignment, state authority slices).

### Tranche completion (broader)

```text
py -3 -m pytest tests/test_validation_journal_affordances.py \
  tests/test_lead_obsolescence_and_journal_alignment.py \
  tests/test_state_authority.py tests/test_ownership_registry.py \
  tests/test_replay_boundary_governance.py tests/test_gate_boundary_governance.py \
  tests/test_lead_lifecycle_vertical_slice.py tests/test_exploration_resolution.py \
  tests/test_ui_mode_policy.py -q
```

| Suite | Result |
|---|---|
| Journal affordances + lead alignment + state authority | **52 passed** |
| Ownership / replay / gate boundary governance | **Passed** |
| Lead lifecycle vertical slice + exploration resolution | **Passed** |
| UI mode policy | **Passed** |

### Not run (by design)

| Suite | Reason |
|---|---|
| Golden replay (`-m golden_replay`) | No replay/projection/emit-path changes |
| Full convergence CI | CQ4 scoped to journal + boundary + related gameplay slices |

---

## 6. Architectural Drift Assessment

| Pressure type | Increased? | Detail |
|---|---|---|
| **Replay pressure** | **No** | Zero replay helpers, manifest, or golden changes |
| **Governance pressure** | **Minimal** | One allow-list operation; no registry inventory expansion |
| **Fallback pressure** | **No** | Zero emit-path or fallback module touches |
| **Corrective locality cost** | **No** | Each feature fixable in ≤2 production files; journal hub reuse is intentional |

### Why the architecture absorbed the work

1. **`build_player_journal` is a stable publication hub** — CQ3 established hidden-fact merge; CQ4 extended the same pattern for status effects, recency fields, and suspicion flags without new persistence roots.
2. **`api.py` orchestration seam is predictable** — lead touch refresh followed CQ3's `discover_clue` mutation branch pattern; no new cross-domain writers.
3. **UI changes stayed in safe domain** — frontend consumed existing journal keys; no API contract breakage.
4. **Pre-existing dead seams were wired, not invented** — `refresh_session_lead_touch` existed but was unused in exploration outcomes; suspicion flags existed in runtime but were unpublished.

### Subsystem responsible (if friction had appeared)

Would have been **`game/journal.py` publication hub** or **`game/api.py` mutation orchestration** — both already documented in the state authority model. No new hotspot emerged.

---

## 7. Trend vs CQ1–CQ3

| Interpretation | Verdict |
|---|---|
| Integration cost scaling with feature count | **Stable / improving** — 5 features in 8 files vs ~4 files per single pilot |
| Cross-subsystem tax | **Low** — highest-risk feature (lead touch) used 1 production file + existing APIs |
| Governance creep | **Bounded** — 1 allow-list op across 5 features |
| Journal hub becoming a magnet? | **Not yet** — all additions are publication-only derived fields; no back-writes |

CQ1–CQ3 proved individual features integrate cleanly. **CQ4 proves consecutive features in the same theme remain inexpensive** when reusing established publication and orchestration seams.

---

## 8. Remaining Foundation Hotspots

| Hotspot | Status | Notes |
|---|---|---|
| BU8/BU9 write-path parity (`final_emission_meta` stamps) | Pre-existing | Unrelated to CQ4; not a tranche blocker |
| `game/journal.py` NPC summarization (`npcs: []` stub) | Open | Natural CQ5 journal candidate |
| Caution-domain replay-smoke when changing shipped scene JSON | Process | Not triggered — no shipped content modified |
| Pass `condition_definitions` from exploration callers (CQ2 hygiene) | Optional | Still valid; CQ4 uses compose_state wiring instead |

---

## 9. Recommendation

| Rating | **Proceed with Planned Feature Development** |
|---|---|

**Rationale:**

- Five consecutive player-facing features completed with **Highly Local** footprint (8 files, 0 prohibited surfaces except one documented allow-list op).
- Per-feature averages **at or below** CQ1–CQ3 pilot costs despite higher cumulative player value.
- No replay churn, no fallback/validator pressure, no golden regeneration.
- Journal publication hub and `api.py` orchestration absorbed the tranche without architectural drift.

**Next tranche candidates (optional):**

- NPC journal summaries (journal publication)
- Exploration lead staleness UX (world/scenes caution domain)
- Inventory usability (if inventory publication seams exist)

**Do not yet:** infer equal locality for emit-path or Final Emission features without per-feature boundary maps.

---

## Files Modified (CQ4 Tranche Diff)

| File | Features | Change |
|---|---|---|
| `game/journal.py` | 01, 02, 04 | `status_effects`, lead recency fields, `suspicion_flags` publication seams |
| `game/api.py` | 01, 05 | Pass character/conditions to journal; discover_clue lead touch refresh |
| `game/state_authority.py` | 04 | `journal_merge_suspicion_flags` allow-list |
| `static/app.js` | 03 | Structured lead buckets, status effects, suspicion UI |
| `static/index.html` | 03 | Journal panel sections |
| `tests/test_validation_journal_affordances.py` | 01, 04, 05 | Status effects, suspicion, lead touch tests |
| `tests/test_lead_obsolescence_and_journal_alignment.py` | 02 | Compact row shape |
| `tests/test_state_authority.py` | 04 | Allow-list assertion |
