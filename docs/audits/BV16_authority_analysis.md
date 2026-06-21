# BV16 — Authority Analysis

**Date:** 2026-06-21

---

## Module self-description vs reality

Docstring claims: *late gate terminal enforcement pipeline (visibility through IC attach)*; *shared accept/replace exit tail*; visibility/N4 owned by extracted modules and **called directly here**.

**Reality matches intent.** The module is a **finalize sequencer** (350 LOC, 5 defined functions) that orders calls to **already-extracted owners** (visibility, N4, opening, IC, repairs, narrative-mode output). BU FI **26** is inflated by **16 test files** patching imported symbols via terminal namespace — not by production utility sprawl (only **2** production importers).

## Export classification

| Export | Class | Verdict |
| --- | --- | --- |
| `run_gate_terminal_enforcement_pipeline` | canonical-finalize-authority | **Legitimate authority** — ordered late enforcement tail; BU FI 2 |
| `apply_strict_social_emergency_fallback_patch` | realization-helper | **Legitimate helper** — strict-social emergency path; 1 test direct import |
| `GateTerminalEnforcementProfile` | finalize | **Legitimate type** — profile routing for accept/replace paths |
| `_apply_referent_clarity_pre_finalize` | internal-helper | **Legitimate internal** — pre-finalize referent clarity pass; 3 direct uses |
| `apply_visibility_enforcement` | visibility-policy-delegate | **Delegate — accidental test bridge** — owner is `final_emission_visibility_fallback` |
| `apply_acceptance_quality_n4_floor_seam` | N4-policy-delegate | **Delegate — accidental test bridge** — owner is `final_emission_acceptance_quality` |
| `apply_interaction_continuity_emission_step`, `attach_interaction_continuity_validation` | IC-projection-delegate | **Delegate — accidental test bridge** — owner is `interaction_continuity` |
| `opening_fallback` / `reassert_scene_opening_accepted_candidate` | opening-projection-delegate | **Delegate** — owner is `final_emission_opening_fallback`; generic_accept only |
| Repairs/meta/text imports | accidental-bridge | **Internal composition** — should not be monkeypatch targets |

## Canonical authority determination

| Question | Answer |
| --- | --- |
| Is terminal pipeline a legitimate finalize authority? | **Yes** — single sequencer owns accept/replace enforcement order |
| Is FI 26 justified by heterogeneous production utility? | **No** — 92% test; 2 production importers on canonical entry |
| What is actually authoritative here? | **Enforcement sequencing** — visibility/N4/IC/opening/realization owned elsewhere |
| Accidental coupling surfaces? | **24 namespace-bound imports** — test monkeypatch seams, not production API |

## Projection helpers vs accidental bridges

| Pattern | Examples | Assessment |
| --- | --- | --- |
| Canonical finalize sequencer | `run_gate_terminal_enforcement_pipeline` | **Keep centralized** — this is the authority |
| Owner delegation (in-body) | `apply_visibility_enforcement`, N4 floor seam, IC attach | **Correct** — direct calls to owners inside sequencer |
| Namespace-bound imports | Same symbols exposed on module object | **Accidental bridges** — enable test monkeypatch via terminal namespace |
| Emergency fallback patch | `apply_strict_social_emergency_fallback_patch` | **Realization helper** — could move to sealed_fallback owner; low FI |
| Module introspection | `import terminal_pipeline as tp` in 20+ tests | **Governance + replay noop overhead** |
