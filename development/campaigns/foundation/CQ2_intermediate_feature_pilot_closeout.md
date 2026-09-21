# CQ2 — Intermediate Feature Readiness Pilot Closeout

**Date:** 2026-06-28  
**Scope:** Moderately more connected gameplay feature after CQ1 diagnostics pilot.  
**Primary metric:** Architectural Spillover  
**Authority:** [CQ1_feature_readiness_pilot_closeout.md](CQ1_feature_readiness_pilot_closeout.md), [CB_feature_boundary_registry.json](docs/audits/CB_feature_boundary_registry.json)

---

## Executive Summary

CQ2 implemented **condition template penalty enforcement** — wiring existing `attack_penalty`, `skill_penalty`, `save_penalty`, and `damage_penalty` effects from condition templates (Shaken, Sickened, etc.) into combat attack resolution, combat skill rolls, enemy turns, Will saves, and exploration/social `resolve_skill_check()`.

**Outcome:** **PASS.** The feature changed **real gameplay outcomes** (hit/miss, pass/fail) while staying in **4 files** (2 production, 2 tests) within the `combat_checks_adjudication` safe domain. Zero replay helpers, fallback helpers, validator helpers, governance files, or golden artifact regeneration. Domain tests: **34 passed**. Ownership/replay/gate boundary: **22 passed**.

**Spillover:** **None outside expected ownership lane.**

**Recommendation:** **Continue Mixed Foundation + Features** — CQ1 low integration cost is **repeatable** for safe-domain gameplay mechanics, not an isolated diagnostics artifact.

---

## 1. Candidate Features (Ranked)

| Rank | Feature | Prod files | Tests | Replay | Governance | Corrective locality |
|---:|---|---:|---:|---|---|---|
| 1 | **Condition penalty enforcement (Shaken/Sickened templates)** ✓ | 2–3 | 2–3 | Low–med | Low | Low |
| 2 | Skill check margin / degree-of-success metadata | 1 | 2 | None–low | Low | Very low |
| 3 | Journal structured lead buckets in player UI | 2–3 | 2 | None | Low–med | Low |
| 4 | Adjudication `state_query` answers (HP, conditions) | 1–2 | 2 | **Med** | **Med** | Med |
| 5 | Interactable `gated: true` skill-check trigger | 1 | 2–3 | Low–med | Low | Low |

### Recommendation

**Rank #1 — Condition penalty enforcement.**

Only candidate that is clearly **gameplay-behavioral** (changes hit/miss and pass/fail) while using a **pre-existing extension seam** (`get_effect_value()` in `conditions.py`, same pattern as `current_ac()`). Templates and data already exist in `data/conditions.json`; only resolution wiring was missing.

---

## 2. Architectural Boundary Review

**Feature:** CQ2-01 — Condition template penalty enforcement  
**Registry domain:** `combat_checks_adjudication` (**safe**)

### Owning module

| Module | Role |
|---|---|
| `game/conditions.py` | **Authority** for effect aggregation (`get_effect_value`, `has_effect`, `current_ac`) — **unchanged**; existing seam reused |
| `game/combat.py` | Combat attack, spell save, combat skill, enemy turn resolution |
| `game/skill_checks.py` | Exploration/social deterministic skill check resolution |

### Neighboring modules (not modified)

| Module | Relationship |
|---|---|
| `game/api.py` | Already passes `conditions` to `resolve_attack` / `resolve_spell`; `resolve_skill` uses optional param + lazy load |
| `game/exploration.py` | Calls `resolve_skill_check(character, ...)` — character dict carries `conditions` |
| `game/final_emission_*` | Emit path — not touched |
| `game/output_sanitizer.py` | Not touched |
| `tests/helpers/golden_replay*` | Not touched |

### Extension seam

- **`get_effect_value(entity, definitions, key)`** — aggregates template `default_effects` and instance overrides; already used for AC and action gates.
- **Resolution return payloads** — additive roll fields (`condition_attack_penalty`, `condition_penalty`, etc.) when penalties apply.

### Boundaries

| Boundary | Assessment |
|---|---|
| **Replay** | Low risk — outcomes change only when entities carry penalty conditions; golden fixtures without Shaken/Sickened unaffected |
| **Ownership** | Stays in `combat_checks_adjudication` required_tests |
| **Fallback** | No fallback imports or behavior |
| **Validator** | No validator-family involvement |

### Isolation answer

**Yes.** The feature remains inside the combat/conditions/skill-checks subsystem. No ownership registry edits, no protected schema expansion, no emit-path coordination.

---

## 3. Feature Implemented

### Behavior

When a character or enemy has conditions with template penalties (e.g. Shaken: `attack_penalty: 2`, `skill_penalty: 2`, `save_penalty: 2`):

| Resolution path | Penalty applied |
|---|---|
| `resolve_attack()` | Subtract `attack_penalty` from attack total; subtract `damage_penalty` from damage dealt |
| `resolve_spell()` (Daze Will save) | Subtract enemy `save_penalty` from save total |
| `resolve_skill()` (combat) | Subtract `skill_penalty` from skill modifier |
| `enemy_take_turn()` | Subtract enemy `attack_penalty` / `damage_penalty` |
| `resolve_skill_check()` | Subtract actor `skill_penalty`; expose `base_modifier` + `condition_penalty` when nonzero |

Penalties use the same sign convention as `current_ac()` (`ac_penalty` subtracted via `get_effect_value`).

---

## 4. Integration Cost

| Category | Count | Files |
|---|---:|---|
| **Production** | **2** | `game/combat.py`, `game/skill_checks.py` |
| **Tests** | **2** | `tests/test_combat_resolution.py`, `tests/test_skill_checks.py` |
| **Tools** | **0** | — |
| **Governance/docs (feature diff)** | **0** | — |
| **Replay helpers** | **0** | — |
| **Fallback helpers** | **0** | — |
| **Validator helpers** | **0** | — |
| **Total** | **4** | +122 / −14 lines |

**Unexpected architectural expansion:** **None.**

---

## 5. Validation

### Domain tests (required — SAFE_G1)

```text
py -3 -m pytest tests/test_combat_resolution.py tests/test_skill_checks.py \
  tests/test_exploration_skill_checks.py tests/test_noncombat_resolution.py -q
```

| Result | Detail |
|---|---|
| **34 passed** | ~2.4 s |

New tests:

- `test_shaken_condition_reduces_attack_total_and_can_flip_hit`
- `test_shaken_condition_reduces_combat_skill_check_modifier`
- `test_shaken_condition_reduces_skill_check_and_can_flip_success`

### Foundation guardrails (targeted)

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
| Golden replay (`-m golden_replay`) | No replay helper or manifest changes; fixtures unlikely to carry Shaken |
| Full convergence CI | CQ2 scoped to domain + boundary slices |

---

## 6. Unexpected Coupling

| Coupling | Type | Action |
|---|---|---|
| Lazy `storage.load_conditions()` in `skill_checks.py` when actor has `conditions` but context lacks `condition_definitions` | **Incidental** — avoids `api.py` / `exploration.py` edits; loads only when conditions present | Document; optional future hygiene: pass `condition_definitions` from callers |
| Lazy `storage.load_conditions()` in `combat.resolve_skill()` via `_condition_definitions()` | **Incidental** — same pattern | Same |
| `resolve_skill()` signature extended with optional `conditions` param | **Architectural (minor)** — backward compatible default | No foundation cycle required |

**Did implementation require touching modules outside the expected ownership lane?**

**No.** All production edits are in `game/combat.py` and `game/skill_checks.py`. Tests stay in domain owner files. No `api.py`, `exploration.py`, registry, replay, or emit-path modules modified.

---

## 7. Spillover Assessment

| Question | Answer |
|---|---|
| Modules outside expected lane touched? | **No** |
| Replay schema / projection changed? | **No** |
| Governance inventory / registry changed? | **No** |
| Fallback pressure introduced? | **No** |
| Validator pressure introduced? | **No** |
| Golden artifacts regenerated? | **No** |

**Spillover rating:** **None observed.**

CTIR note: combat hints embedding roll totals may change when conditions present (e.g. miss where hit previously). Protected replay rows without penalty conditions should remain stable.

---

## 8. CQ1 Comparison & Trend

| Metric | CQ1 (`scene_finding_counts`) | CQ2 (condition penalties) | Delta |
|---|---:|---:|---|
| Total files | 5 | **4** | −1 |
| Production files | 1 | **2** | +1 |
| Test files | 3 | **2** | −1 |
| Tooling files | 1 | **0** | −1 |
| Governance/replay/fallback/validator | 0 | **0** | 0 |
| Lines changed | +66 / −3 | +122 / −14 | +53 net |
| User-visible surface | Author CLI metric | **Combat/skill outcomes** | Gameplay step-up |
| Classification | Highly Local | **Highly Local** | Stable |

### Trend assessment

**Integration cost remained stable** with a **modest production-file increase** (+1) reflecting genuine gameplay connectivity rather than architectural spillover.

| Interpretation | Verdict |
|---|---|
| Normal variance | **Yes** — fewer total files than CQ1; one extra production module is expected for mechanics vs diagnostics |
| Hidden architectural pressure | **No evidence** — zero prohibited-surface touches |
| Beginning of feature scaling cost | **Not yet** — still ≤2 production modules, ≤2 test files, single safe domain |

CQ1's low cost was **repeatable**, not a fortunate isolated case — but only within **safe registry domains** with established extension seams.

---

## 9. Recommendation

| Rating | **Continue Mixed Foundation + Features** |
|---|---|

**Rationale:**

- Gameplay feature landed with **Highly Local** spillover profile (4 files, 0 prohibited surfaces).
- Integration cost **stable vs CQ1** despite materially higher user impact.
- `get_effect_value()` seam proved sufficient for mechanics extension without validator/replay/governance fanout.

**Optional follow-ups (not CQ2 scope):**

- Pass `condition_definitions` from `exploration.py` context builder to avoid lazy storage load (hygiene, not blocker).
- Run golden replay spot-check if any protected fixture adds Shaken/Sickened conditions.
- Schedule **Targeted Foundation Cycle** only if BU8/BU9 write-path drift (pre-existing) blocks CI — unrelated to CQ2.

**Do not yet:** infer that caution/prohibited domains (adjudication routing, world/scene affordances, emit path) will stay equally local.

---

## Files Modified (CQ2 Feature Diff)

| File | Change |
|---|---|
| `game/combat.py` | Apply condition penalties in attack, spell save, combat skill, enemy turn; expose penalty fields in rolls |
| `game/skill_checks.py` | Apply `skill_penalty` in `resolve_skill_check()`; optional context definitions + lazy load |
| `tests/test_combat_resolution.py` | Shaken attack miss-flip + combat skill penalty tests |
| `tests/test_skill_checks.py` | Shaken skill check success-flip test |
