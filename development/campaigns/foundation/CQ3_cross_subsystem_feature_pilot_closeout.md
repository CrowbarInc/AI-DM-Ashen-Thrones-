# CQ3 — Cross-Subsystem Feature Pilot Closeout

**Date:** 2026-06-28  
**Scope:** User-visible feature spanning multiple gameplay ownership domains after CQ1/CQ2 single-domain pilots.  
**Primary metric:** Cross-Subsystem Integration Stability  
**Authority:** [CQ2_intermediate_feature_pilot_closeout.md](CQ2_intermediate_feature_pilot_closeout.md), [CB_feature_boundary_registry.json](docs/audits/CB_feature_boundary_registry.json), [docs/state_authority_model.md](docs/state_authority_model.md)

---

## Executive Summary

CQ3 implemented **exploration hidden-fact revelation → journal publication**: successful interactable `discover_clue` investigations with optional `reveals_hidden_fact` now persist earned secrets via `mark_hidden_fact_revealed`, and `build_player_journal` publishes them into `known_facts` through the existing `journal_merge_revealed_hidden_facts` seam.

**Outcome:** **PASS.** The feature coordinates **three ownership domains** (exploration affordances → hidden runtime → player-visible journal) in **4 files** (2 production, 2 tests) with **zero** replay-helper, fallback, validator, governance-registry, or golden-artifact changes. Targeted validation: **67 domain + 22 boundary tests passed**.

**Cross-subsystem stability:** Coordination occurred entirely through **existing public interfaces**; journal publication required no code changes.

**Recommendation:** **Continue Mixed Foundation + Features** — cross-subsystem gameplay features can follow localized orchestration without architectural hubs, with `api.py` authoritative mutation as the expected coordination seam.

---

## 1. Candidate Features (Ranked)

| Rank | Feature | Prod files | Domains | Replay | Governance | Complexity | Player value |
|---:|---|---:|---|---|---|---|---|
| 1 | **Exploration `discover_clue` → hidden fact → journal `known_facts`** ✓ | 2–3 | 3 | Low | Low–med | Med | **High** |
| 2 | Journal `status_effects` from character conditions | 3–4 | 2 | Very low | Low | Low | High |
| 3 | Exploration activity refreshes lead `last_touched_turn` | 2–3 | 2 | Med | Med | Med | Medium |
| 4 | Journal publication of `suspicion_flags` | 2–3 | 2 | Low–med | Low–med | Low | Medium |
| 5 | Exploration E2E condition-penalty in resolution metadata | 2 | 2 | Low–med | Low | Low | Medium |

### Recommendation

**Rank #1 — Exploration hidden-fact revelation → journal.**

Only candidate that **legitimately requires three subsystems** with pre-existing but unwired infrastructure (`mark_hidden_fact_revealed` was production-dead; journal merge already implemented). Opt-in via interactable `reveals_hidden_fact` preserves replay stability for existing content.

---

## 2. Boundary Map

**Feature:** CQ3-01 — Interactable hidden-fact revelation on successful `discover_clue`

### Primary owner

| Module | Domain | Role |
|---|---|---|
| `game/exploration.py` | `world_scenes_affordances` (caution) | Pure resolution: match `reveals_hidden_fact` → `hidden_facts`; attach `metadata.hidden_fact_revealed` |

### Secondary owners

| Module | Domain | Role |
|---|---|---|
| `game/api.py` | Orchestration / `scene_state` | Authoritative mutation: `mark_hidden_fact_revealed` on `discover_clue` |
| `game/storage.py` | `hidden_state` | Existing `mark_hidden_fact_revealed` — **unchanged** |
| `game/journal.py` | `player_visible_state` | Existing `merge_player_journal_known_facts_publication` — **unchanged** |

### Extension seams used

| Seam | Direction |
|---|---|
| `resolve_interactable_hidden_fact_text()` | Exploration lookup (new, side-effect free) |
| `ExplorationEngineResult.metadata["hidden_fact_revealed"]` | Resolution → API orchestration |
| `mark_hidden_fact_revealed(session, scene_id, text)` | Hidden runtime write |
| `journal_merge_revealed_hidden_facts` allow-list | Hidden → player-visible publication |

### Coordination points

```text
Player investigate (interactable)
  → resolve_exploration_action (discover_clue, metadata.hidden_fact_revealed)
  → _apply_authoritative_resolution_state_mutation (discover_clue branch)
      → mark_interactable_resolved (existing)
      → mark_hidden_fact_revealed (NEW)
  → compose_state / build_player_journal
      → merge_player_journal_known_facts_publication (existing)
```

### Boundaries

| Boundary | Assessment |
|---|---|
| **Replay** | Low — opt-in `reveals_hidden_fact`; no shipped scene JSON changed in pilot |
| **Fallback** | None — no emit-path or fallback modules touched |
| **Governance** | Low–med — caution domain; state-authority allow-list already registers cross-domain operation |

### Can coordination occur through existing interfaces?

**Yes.** No new persistence roots, no journal logic changes, no schema expansion. API orchestration calls existing storage + journal reads existing runtime.

---

## 3. Feature Implemented

### Author-facing opt-in

Interactables may include:

```json
"reveals_hidden_fact": "Exact line matching a scene hidden_facts entry"
```

On successful `discover_clue`:

1. Exploration attaches `metadata.hidden_fact_revealed` and `state_changes.hidden_fact_revealed`.
2. API calls `mark_hidden_fact_revealed` in the `discover_clue` authoritative mutation branch.
3. Journal `known_facts` includes the earned line on next state build.

Matching is exact or case-insensitive against `scene.hidden_facts`.

---

## 4. Integration Cost

| Category | Count | Files |
|---|---:|---|
| **Production** | **2** | `game/exploration.py`, `game/api.py` |
| **Tests** | **2** | `tests/test_exploration_resolution.py`, `tests/test_validation_journal_affordances.py` |
| **Tooling** | **0** | — |
| **Governance/docs (feature diff)** | **0** | — |
| **Replay helpers** | **0** | — |
| **Fallback helpers** | **0** | — |
| **Validator helpers** | **0** | — |
| **Ownership domains involved** | **3** | exploration affordances, hidden runtime, player-visible journal |
| **Total** | **4** | +147 / −3 lines |

**Unexpected architectural expansion:** **None.**

---

## 5. Validation

### Feature + affected gameplay systems

```text
py -3 -m pytest tests/test_exploration_resolution.py \
  tests/test_validation_journal_affordances.py tests/test_discovery_memory.py \
  tests/test_intent_and_runtime.py -q
```

| Result | Detail |
|---|---|
| **67 passed** | ~3.3 s |

New tests:

- `test_resolve_interactable_hidden_fact_text_matches_scene_hidden_facts`
- `test_discover_clue_includes_hidden_fact_metadata_when_interactable_configured`
- `test_discover_clue_cross_subsystem_hidden_fact_reaches_journal`

### Foundation guardrails

```text
py -3 -m pytest tests/test_ownership_registry.py \
  tests/test_replay_boundary_governance.py tests/test_gate_boundary_governance.py -q
```

| Suite | Result |
|---|---|
| Ownership registry | **Passed** |
| Replay boundary governance | **Passed** |
| Gate boundary governance | **Passed** |

### Not run (by design)

| Suite | Reason |
|---|---|
| Golden replay | No manifest/projection changes; no shipped scene content modified |
| Full convergence CI | CQ3 scoped to domain + boundary slices |

---

## 6. Coupling Analysis

| Interaction | Expected? | Tightness | Difficulty |
|---|---|---|---|
| Exploration → resolution metadata | **Yes** | Appropriate | Easy |
| API orchestration → `mark_hidden_fact_revealed` | **Yes** | Appropriate | Easy |
| Hidden runtime → journal publication | **Yes** | **Unexpectedly loose** (zero journal edits) | N/A — already wired |
| Exploration → storage direct call | **No** (by design) | Avoided | — |
| API → journal direct call | **No** (by design) | Avoided | — |

### Architectural friction

| Friction | Type | Future work? |
|---|---|---|
| `mark_hidden_fact_revealed` was unwired despite journal merge existing | **Incomplete prior wiring** | Document in architecture ledger; optional content pass to add `reveals_hidden_fact` to scenes |
| `api.py` is the cross-domain mutation hub for exploration outcomes | **Expected orchestration** | Not foundation debt — intentional seam per state authority model |
| Caution domain (`world_scenes_affordances`) requires replay-smoke decision when changing shipped scenes | **Process** | Not triggered — opt-in field only, no data changes in pilot |

**Did implementation require touching modules outside expected ownership lane?**

**Partially expected:** `game/api.py` is outside exploration/journal modules but is the **documented authoritative mutation owner** for exploration resolutions. No broadening of subsystem ownership for convenience.

---

## 7. Feature Scalability Assessment

| Question | Assessment |
|---|---|
| Can future cross-subsystem features follow the same pattern? | **Yes**, when existing storage/journal seams exist |
| Integration cost scaling observed? | **Stable** — 4 files despite 3 domains (vs CQ1: 5 files/1 domain, CQ2: 4 files/1 domain) |
| Recurring friction for foundation? | (1) Document dead-code seams when publication exists without writers; (2) caution-domain replay-smoke checklist for content changes |

Cross-subsystem coordination **did not** require new hubs, compatibility shims, or registry expansion. The architecture absorbed a three-domain feature at **similar file count** to single-domain pilots because **publication was already derived** and **writes were already allow-listed**.

---

## 8. CQ1 / CQ2 Comparison

| Metric | CQ1 | CQ2 | CQ3 |
|---|---:|---:|---:|
| Total files | 5 | 4 | **4** |
| Production files | 1 | 2 | **2** |
| Test files | 3 | 2 | **2** |
| Tooling | 1 | 0 | 0 |
| Ownership domains | 1 | 1 | **3** |
| Replay/fallback/validator/governance | 0 | 0 | **0** |
| User-visible impact | Author CLI | Combat/skill outcomes | **Earned secrets in journal** |
| Classification | Highly Local | Highly Local | **Highly Local (cross-domain)** |

### Trend

| Interpretation | Verdict |
|---|---|
| Integration cost vs CQ1/CQ2 | **Stable** — same 4-file footprint |
| Cross-subsystem tax | **Low** — extra domains did not multiply file count when existing seams were used |
| Hidden architectural pressure | **None observed** in pilot scope |

CQ3 demonstrates that **domain count ≠ integration cost** when coordination uses existing interfaces and derived publication.

---

## 9. Recommendation

| Rating | **Continue Mixed Foundation + Features** |
|---|---|

**Rationale:**

- Three-domain feature landed with **Highly Local** file footprint and **zero prohibited-surface touches**.
- Cross-subsystem coordination through `api.py` authoritative mutation + existing storage/journal seams remained **bounded and predictable**.
- No golden replay regeneration; boundary governance held.

**Optional hygiene (not blockers):**

- Add architecture ledger note linking `reveals_hidden_fact` content pattern to `mark_hidden_fact_revealed` + journal merge.
- When adding `reveals_hidden_fact` to shipped scenes, run replay-smoke per caution-domain guardrails.

**Not yet:** **Begin Planned Feature Development** at full velocity in caution/prohibited domains without per-feature boundary maps. **Schedule Targeted Foundation Hygiene** only if BU8/BU9 write-path drift (pre-existing) blocks CI.

---

## Files Modified (CQ3 Feature Diff)

| File | Change |
|---|---|
| `game/exploration.py` | `resolve_interactable_hidden_fact_text()`; `discover_clue` metadata/state_changes |
| `game/api.py` | `discover_clue` branch calls `mark_hidden_fact_revealed` |
| `tests/test_exploration_resolution.py` | Lookup + metadata tests |
| `tests/test_validation_journal_affordances.py` | End-to-end exploration → runtime → journal test |
