# CQ5 — Planned Feature Development Tranche #2 Closeout

**Date:** 2026-06-28  
**Scope:** Second planned feature tranche — sustained development with architectural health as secondary metric.  
**Primary metric:** Feature Velocity Without Architectural Regression  
**Theme:** **NPC interaction** (player-facing social roster, stance visibility, lead freshness on social reveals) — distinct from CQ4 journal improvements  
**Authority:** [CQ4_first_feature_tranche_closeout.md](CQ4_first_feature_tranche_closeout.md), [CB_feature_boundary_registry.json](docs/audits/CB_feature_boundary_registry.json)

---

## Executive Summary

CQ5 delivered **five NPC-interaction features** in a planned tranche, implementing sequentially with targeted validation after each feature and broader validation at completion.

**Outcome:** **PASS.** All five features landed with **zero** replay-helper, fallback, validator, sanitizer, ownership-registry, or golden-artifact changes. **Zero governance changes.** Tranche totals: **5 production files**, **2 test files**, **7 files overall**.

**Velocity:** Feature integration cost **stable vs CQ4** (~1.4 production files/feature). No architectural regression observed.

**Recommendation:** **Continue Planned Feature Development** — NPC interaction features reuse existing social/runtime seams without accumulating subsystem pressure.

---

## 1. Feature Theme

**NPC interaction** — player-facing visibility into who is in-scene, conversation context, NPC stance after social exchanges, and lead-registry freshness when social topics reveal clues.

Reused extension seams:

- `get_npc_runtime` / `apply_npc_runtime_deltas` (existing social runtime)
- `scene_npcs_in_active_scene` (existing interaction roster)
- `response_type_context_snapshot` (existing interaction context)
- `refresh_session_lead_touch` + `_canonical_registry_lead_id` (CQ4 discover-clue pattern)
- `resolve_skill_check` (combat_checks safe domain)

Avoided: Final Emission, replay infrastructure, validator families, sanitizer, ownership registry.

---

## 2. Tranche Plan (Low → High Risk)

| Order | Feature | Objective | Ownership domains | Est. prod | Est. tests | Risk | Player impact |
|---:|---|---|---|---:|---:|---|---|
| 1 | **Skill check `margin`** | Expose roll margin (`total − DC`) in skill check results | `combat_checks_adjudication` | 1 | 1 | **Low** | Medium |
| 2 | **Scene NPC roster in `compose_state`** | Publish in-scene NPCs with runtime stance for UI | `interaction_state`, world read | 2 | 1 | **Low** | High |
| 3 | **`npc_stance` in social resolution metadata** | Attach post-exchange stance snapshot to social results | Social / interaction | 1 | 1 | **Low–med** | Medium |
| 4 | **UI NPC panel + active conversation** | Render scene NPCs and active interaction target | `ui_mode_frontend` | 2 | 0 | **Low–med** | High |
| 5 | **Social clue reveal → lead touch refresh** | Refresh `last_touched_turn` when social resolution carries `clue_id` | Leads via `api.py` orchestration | 1 | 1 | **Med** | Medium |

---

## 3. Implementation Record (Sequential)

### CQ5-01 — Skill check margin

| Category | Detail |
|---|---|
| **Production files** | `game/skill_checks.py` |
| **Tests** | `tests/test_skill_checks.py` |
| **Replay / Fallback / Governance** | None |
| **Unexpected coupling** | None — margin flows automatically into exploration/social `skill_check` metadata |

---

### CQ5-02 — Scene NPC roster in `compose_state`

| Category | Detail |
|---|---|
| **Production files** | `game/social.py` (`build_scene_npc_player_snapshot`), `game/api.py` |
| **Tests** | `tests/test_social.py` (`test_build_scene_npc_player_snapshot_merges_world_and_runtime`) |
| **Replay / Fallback / Governance** | None |
| **Unexpected coupling** | None — read-only publication from world + `npc_runtime` |

---

### CQ5-03 — Social `npc_stance` metadata

| Category | Detail |
|---|---|
| **Production files** | `game/social.py` (`compact_npc_runtime_stance`, extended `_social_result_dict_with_incoming_metadata`) |
| **Tests** | `tests/test_social.py` (`test_question_reveals_topic_clue` stance assertion) |
| **Replay / Fallback / Governance** | None |
| **Unexpected coupling** | None — all 12 social return paths pass `session=` to metadata helper |

---

### CQ5-04 — UI NPC panel + active conversation

| Category | Detail |
|---|---|
| **Production files** | `game/api.py` (`_compose_ui_interaction_snapshot`), `static/app.js`, `static/index.html` |
| **Tests** | None new (consumes `ui.scene_npcs` / `ui.interaction` API contract) |
| **Replay / Fallback / Governance** | None |
| **Unexpected coupling** | None |

---

### CQ5-05 — Social clue reveal → lead touch refresh

| Category | Detail |
|---|---|
| **Production files** | `game/api.py` (SOCIAL_KINDS branch) |
| **Tests** | `tests/test_social.py` (`test_social_clue_reveal_refreshes_registry_lead_touch`) |
| **Replay / Fallback / Governance** | None |
| **Unexpected coupling** | None — mirrors CQ4-05 discover-clue pattern |

---

## 4. Architectural Health Table

| Feature | Production files | Replay | Governance | Fallback | Locality | Unexpected coupling |
|---|---:|---|---|---|---|---|
| CQ5-01 margin | 1 | None | None | None | **Highly local** | None |
| CQ5-02 scene NPCs | 2 | None | None | None | **Highly local** | None |
| CQ5-03 npc_stance | 1 | None | None | None | **Highly local** | None |
| CQ5-04 UI panel | 3 | None | None | None | **Highly local** | None |
| CQ5-05 social lead touch | 1 | None | None | None | **Highly local** | None |

**No feature exceeded expected locality.**

---

## 5. Integration Metrics (Tranche Totals)

| Category | Count | Files |
|---|---:|---|
| **Production** | **5** | `game/skill_checks.py`, `game/social.py`, `game/api.py`, `static/app.js`, `static/index.html` |
| **Tests** | **2** | `tests/test_skill_checks.py`, `tests/test_social.py` |
| **Replay / Fallback / Validator / Registry / Golden** | **0** | — |
| **Governance** | **0** | — |
| **Total** | **7** | — |

### Per-feature averages (5 features)

| Metric | CQ5 | CQ4 | CQ1–CQ3 avg |
|---|---:|---:|---:|
| Production files / feature | **1.4** | 1.6 | 1.67 |
| Test files / feature | **0.8** | 1.0 | 2.33 |
| Total files / feature | **1.4** | 1.6 | 4.33 |
| Replay/fallback/governance touches | **0** | 0.2* | 0 |

\*CQ4 had one allow-list operation across 5 features.

---

## 6. Validation Summary

### Per-feature targeted runs

Each feature validated before proceeding (skill checks, social engine contracts).

### Tranche completion (broader)

```text
py -3 -m pytest tests/test_skill_checks.py tests/test_social.py \
  tests/test_exploration_skill_checks.py tests/test_ownership_registry.py \
  tests/test_replay_boundary_governance.py tests/test_gate_boundary_governance.py \
  tests/test_ui_mode_policy.py tests/test_exploration_resolution.py -q
```

| Suite | Result |
|---|---|
| Skill checks + social + exploration skill checks | **Passed** |
| Ownership / replay / gate boundary governance | **Passed** |
| UI mode policy + exploration resolution | **Passed** |
| **Total** | **120 passed** (~52 s) |

### Not run (by design)

| Suite | Reason |
|---|---|
| Golden replay | No replay/projection/emit-path changes |
| Full convergence CI | CQ5 scoped to social + boundary + related gameplay slices |

---

## 7. Tranche Assessment

| Question | Answer |
|---|---|
| Did feature velocity remain stable? | **Yes** — 5 features in 7 files, comparable to CQ4's 8 files |
| Did integration costs increase? | **No** — per-feature averages at or below CQ4 |
| Did ownership boundaries remain intact? | **Yes** — social, interaction, skill-check, and UI domains respected |
| Did any subsystem accumulate pressure? | **No** |

### Pressure classification

No subsystem pressure encountered. All coupling was **incidental** at most (shared `social.py` helper reuse across features 2 and 3 — intentional hub, not drift).

---

## 8. Foundation Watch List

Issues **actually encountered** during implementation (demand-driven only):

| Item | Classification | Action |
|---|---|---|
| None | — | No foundation pause required |

Pre-existing items **not triggered** by CQ5 (unchanged from CQ4):

- BU8/BU9 write-path parity drift on final-emission stamps
- `game/journal.py` NPC summarization stub (`npcs: []`)

---

## 9. Trend Comparison (CQ1–CQ5)

| Metric | CQ1 | CQ2 | CQ3 | CQ4 | CQ5 |
|---|---:|---:|---:|---:|---:|
| Features | 1 | 1 | 1 | 5 | **5** |
| Total files | 5 | 4 | 4 | 8 | **7** |
| Production files | 1 | 2 | 2 | 5 | **5** |
| Test files | 3 | 2 | 2 | 3 | **2** |
| Governance changes | 0 | 0 | 0 | 1 | **0** |
| Replay/fallback/validator | 0 | 0 | 0 | 0 | **0** |

### Trend interpretation

| Verdict | Detail |
|---|---|
| Velocity scaling | **Stable** — second 5-feature tranche completed in fewer total files than CQ4 |
| Integration cost trend | **Flat or improving** — no upward drift across CQ4→CQ5 |
| Architectural regression | **None observed** |
| Safe to continue feature cadence | **Yes** |

---

## 10. Recommendation

| Rating | **Continue Planned Feature Development** |
|---|---|

**Rationale:**

- Five NPC-interaction features delivered with **Highly Local** footprint and **zero prohibited-surface touches**.
- Feature velocity **stable** across two consecutive planned tranches (CQ4 + CQ5).
- No governance creep in CQ5 (vs one allow-list op in CQ4).
- Architecture absorbed social/UI/orchestration work without replay or fallback pressure.

**Optional next themes (not CQ5 scope):**

- Exploration depth (observe/investigate metadata, travel UX)
- Inventory usability (if publication seams exist)
- Faction reputation (world_state flags → player-visible)

**Do not yet:** Schedule Targeted Foundation Hygiene unless BU8/BU9 drift blocks CI — unrelated to CQ5.

---

## Files Modified (CQ5 Tranche Diff)

| File | Features | Change |
|---|---|---|
| `game/skill_checks.py` | 01 | `margin` field on skill check results |
| `game/social.py` | 02, 03 | `build_scene_npc_player_snapshot`, `compact_npc_runtime_stance`, metadata helper |
| `game/api.py` | 02, 04, 05 | `compose_state` UI fields, interaction snapshot, social lead touch |
| `static/app.js` | 04 | Scene NPC list + active conversation rendering |
| `static/index.html` | 04 | NPC / conversation panel sections |
| `tests/test_skill_checks.py` | 01 | Margin tests |
| `tests/test_social.py` | 02, 03, 05 | Snapshot, stance, lead touch tests |
