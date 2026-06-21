# BV6 — Residual Referential-Clarity Elimination Feasibility

**Date:** 2026-06-21  
**Question:** Can the last `referential_clarity_hard_replacement` event be eliminated?

---

## Short answer

| Scope | Zero RC fallbacks achievable? | Mechanism |
|---|---|---|
| **Replay runtime corpus** | **Yes — already achieved** | BV3E + BV4B cleared all replay-sourced RC events |
| **BV3D combined corpus (replay + fixtures)** | **Yes, with measurement policy change** | Exclude negative controls from incidence numerator |
| **BV3D combined corpus via repair expansion** | **Theoretically yes, not recommended** | EC-M01 contract expansion (unsafe speaker guess) |

---

## Option A — Repair safely (deterministic, no contract change)

**Feasibility: NO**

| Requirement | Status |
|---|---|
| Unique grounded entity | **Missing** — 2 named candidates, 4 visible persons |
| Interlocutor / social NPC | **Absent** |
| Single visible person shortcut | **Unavailable** |
| Post-repair re-validation | Would fail if wrong entity chosen |

Any "safe" repair would require guessing which of two explicitly named NPCs spoke — violating the BV3A/BV3E ownership guard at `_resolve_grounded_person_entity_for_referential_repair` (multi-person + no contextual grounding → `None`).

**Verdict:** Cannot eliminate OBS-M002 safely without changing safety semantics.

---

## Option B — Repair with contract expansion (EC-M01)

**Feasibility: POSSIBLE but high risk**

Proposed expansion (from BV4B-RC / EC-M01):

- Allow dialogue-attribution `he`/`she` repair when **both candidates are visible** and **one matches scene salience heuristics** (e.g., first-named entity, last-mentioned entity, gate-adjacent role).

| Risk | Severity |
|---|---|
| Wrong speaker attribution | **High** — `"Back away"` could be guard captain or tavern runner |
| Speaker contract regression | **Medium** — strict-social boundary unaffected, but observe narration voice shifts |
| Replay divergence | **Medium** — ~30 archive shapes share OBS-001 pattern per BV3A inventory |
| False-positive alias match | **Low** — not alias-driven |

**Verdict:** Elimination via expansion is **technically feasible** but **contradicts BV3E rejection** and reintroduces speaker-guess liability on a shape that currently fails closed.

---

## Option C — Intentionally retain (negative control)

**Feasibility: YES — current state**

The event is a **measurement artifact**, not a production regression:

| Evidence | Detail |
|---|---|
| Fixture id | `bv3a_negative_control_multi_person_hard_replace` |
| Source test | `test_observe_ambiguous_speaker_without_interlocutor_still_hard_replaces` |
| Materializer | `tools/bv3d_build_positive_control_corpus.py` |
| Purpose | Prove hard replace still fires for ungrounded multi-person dialogue |

Retaining this path preserves:

- regression coverage for ineligible observe shapes,
- contrast with OBS-M001 (positive control),
- BV3D eligibility measurement validity (applied/eligible coverage).

**Verdict:** **Recommended** for runtime behavior; requires **measurement split** if incidence target is 0%.

---

## Option D — Measurement scope adjustment (no behavior change)

**Feasibility: YES — low risk**

Split BV3D incidence into:

| Bucket | RC hard replace |
|---|---:|
| `replay_runtime` | **0** |
| `measurement_fixtures.negative_control` | **1** |
| `measurement_fixtures.positive_control` | **0** |

Implementation surfaces:

- Add `measurement_class` filter to `bv3a_referential_clarity_metrics.py`
- Report `referential_clarity_hard_replacement_count_replay_only` separately
- Keep negative control in fixture corpus for activation tests

**Verdict:** Achieves **metric = 0 on replay** without compromising safety or test coverage.

---

## Feasibility matrix

| Option | RC count → 0 | Safe | Effort | Recommended |
|---|---|---|---|---|
| A. Safe repair | no | yes | — | no |
| B. EC-M01 expansion | yes | **no** | medium | no |
| C. Retain behavior | no (metric stays 1) | yes | none | **yes (behavior)** |
| D. Measurement split | yes (replay metric) | yes | low | **yes (reporting)** |

---

## Conclusion

Complete elimination of the **hard-replace behavior** for this shape is **not safely achievable** without speaker guessing.

Complete elimination of **replay-sourced RC fallbacks is already achieved**.

Achieving **incidence metric = 0** on the BV3D corpus is achievable via **Option D** (measurement split) without code-path changes to repair contracts.
