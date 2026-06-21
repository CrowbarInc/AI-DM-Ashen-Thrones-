# BV16 — Symbol Concentration Analysis

**Date:** 2026-06-21
**Method:** Per-symbol AST importer + attribute-use scan (`artifacts/bv16_final_emission_terminal_pipeline_analysis.json`)

---

## Executive answer

Module BU FI **26** is **test-monkeypatch inflated** — canonical `run_gate_terminal_enforcement_pipeline` has BU FI **2 (7%)** with AST FI **8** (2 production exit owners + governance source scans). **Highest AST concentration** is `apply_visibility_enforcement` namespace binding at **16 files** — tests patch visibility via terminal namespace, not owner module. The module is a **sequencer** that delegates behavior to extracted owners; FI reflects **monkeypatch seam concentration**, not heterogeneous utility accretion in production.

## Symbol fan-in (ranked, AST + BU)

| Rank | Symbol | AST FI | BU FI | Category | Authority class |
| --- | --- | --- | --- | --- | --- |
| 1 | `terminal_pipeline` | **24** | 24 | other | accidental-coupling |
| 2 | `apply_visibility_enforcement` | **16** | 16 | visibility | visibility-policy-delegate |
| 3 | `run_gate_terminal_enforcement_pipeline` | **8** | 2 | finalize | canonical-finalize-authority |
| 4 | `_apply_referent_clarity_pre_finalize` | **3** | 3 | finalize | internal-helper |
| 5 | `_apply_fallback_behavior_layer` | **2** | 2 | compatibility | accidental-bridge |
| 6 | `apply_acceptance_quality_n4_floor_seam` | **2** | 2 | N4 | N4-policy-delegate |
| 7 | `apply_interaction_continuity_emission_step` | **2** | 2 | IC | IC-projection-delegate |
| 8 | `attach_interaction_continuity_validation` | **2** | 2 | IC | IC-projection-delegate |
| 9 | `tp` | **2** | 2 | other | accidental-coupling |
| 10 | `apply_strict_social_emergency_fallback_patch` | **1** | 1 | finalize | realization-helper |

## Classification buckets

| Category | Symbols with external use | Top symbol | AST FI | Role |
| --- | --- | --- | --- | --- |
| **Finalize exports** | 3 | `run_gate_terminal_enforcement_pipeline` | **8** | Canonical late-gate enforcement sequencer — accept/replace tail |
| **Visibility exports** | 1 | `apply_visibility_enforcement` | **16** | Owner delegate — monkeypatched via terminal namespace in tests |
| **N4 exports** | 1 | `apply_acceptance_quality_n4_floor_seam` | 2 | Acceptance-quality floor seam delegate |
| **IC exports** | 2 | `attach_interaction_continuity_validation` | 2 | Interaction continuity attach/step delegates |
| **Opening exports** | 0 | `reassert_scene_opening_accepted_candidate` | 0 | Opening accept reassert (via `opening_fallback` alias) — source inspection only |
| **Realization exports** | 0 | `apply_strict_social_emergency_fallback_patch` | 0 | Strict-social emergency fallback patch helper |
| **Compatibility exports** | 1 | `_apply_fallback_behavior_layer` | 2 | Repairs/meta/text imports — internal + monkeypatch only |
| **Module import** | — | `terminal_pipeline (module)` | **24** | Governance introspection, visibility noop hooks, orchestration-order tests |

## Defined vs imported namespace surface

| Kind | Count | Examples | External AST FI |
| --- | --- | --- | --- |
| Defined | 5 | `run_gate_terminal_enforcement_pipeline`, `apply_strict_social_emergency_fallback_patch` | 12 |
| Imported (namespace-bound) | 24 | `apply_visibility_enforcement`, `apply_acceptance_quality_n4_floor_seam`, IC attach/step | 18 |

## Highest fan-in exports (maintenance risk)

| Rank | Symbol | AST FI | BU FI | Risk |
| --- | --- | --- | --- | --- |
| 1 | `apply_visibility_enforcement` (namespace) | 16 | 0 | **Medium** — test monkeypatch seam; owner is `final_emission_visibility_fallback` |
| 2 | `run_gate_terminal_enforcement_pipeline` | 8 | 2 | **Low-medium** — legitimate authority; 2 production paths |
| 3 | module introspection | 24 | — | **Medium** — governance + replay noop hooks |
| 4 | `_apply_referent_clarity_pre_finalize` | 3 | 0 | **Low** — defined helper; direct unit tests + probe harness |
