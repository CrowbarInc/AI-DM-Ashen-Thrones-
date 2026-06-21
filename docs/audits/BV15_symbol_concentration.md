# BV15 — Symbol Concentration Analysis

**Date:** 2026-06-21
**Method:** Per-symbol AST importer scan (`artifacts/bv15_final_emission_gate_analysis.json`)

---

## Executive answer

Module FI **30** is **orchestration-dominant** — `apply_final_emission_gate` holds **17 BU FI (56%)**. Unlike pre-BN gate monoliths, the module defines **one** function; remaining namespace surface is **13 re-exports** from extracted stack owners (speaker contract, interaction continuity, strict/non-strict stacks, gate context). Secondary FI is **module-level introspection** (`import game.final_emission_gate as feg`) for governance, monkeypatch, and source inspection — not heterogeneous utility accretion.

## Symbol fan-in (ranked, BU baseline)

| Rank | Symbol | BU FI | AST FI | Category | Authority class |
| --- | --- | --- | --- | --- | --- |
| 1 | `feg` | **17** | 17 | other | accidental-coupling |
| 2 | `apply_final_emission_gate` | **17** | 15 | orchestration | canonical-gate-authority |
| 3 | `feg_module` | **1** | 1 | other | accidental-coupling |
| 4 | `get_speaker_selection_contract` | **1** | 1 | compatibility | compatibility-bridge |

## Classification buckets

| Category | Re-export / defined count | Top symbol | AST FI | Role |
| --- | --- | --- | --- | --- |
| **Orchestration exports** | 1 defined | `apply_final_emission_gate` | **17** | Canonical gate orchestration entry — routes strict-social vs non-strict stacks |
| **Gate authority re-exports** | 6 | `run_strict_social_composition_trunk` | 0 external | Stack trunk delegates — namespace legacy only post-BN2 |
| **Compatibility re-exports** | 5 | `get_speaker_selection_contract` | 1 | Speaker/IC bridges — BJ-129 thin-boundary compat; no production imports |
| **Helper re-exports** | 2 | `resolve_gate_preflight_pregate_text` | 0 | Internal preflight — imported into gate body only |

## Namespace re-export inventory (non-orchestration)

| Symbol | Origin module | External AST FI | Assessment |
| --- | --- | --- | --- |
| `SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES` | `game.speaker_contract_enforcement` | 0 | Retire re-export — import origin directly |
| `apply_interaction_continuity_emission_step` | `game.interaction_continuity` | 0 | Retire re-export — import origin directly |
| `apply_observe_passive_scene_concrete_beat_upstream_satisfier` | `game.final_emission_passive_scene_pressure` | 0 | Retire re-export — import origin directly |
| `attach_interaction_continuity_validation` | `game.interaction_continuity` | 0 | Retire re-export — import origin directly |
| `detect_emitted_speaker_signature` | `game.emitted_speaker_signature` | 0 | Retire re-export — import origin directly |
| `get_speaker_selection_contract` | `game.speaker_contract_enforcement` | 1 | Migrate consumers to origin |
| `initialize_gate_execution_context` | `game.final_emission_gate_context` | 0 | Retire re-export — import origin directly |
| `resolve_gate_preflight_pregate_text` | `game.final_emission_gate_preflight_pregate_text` | 0 | Retire re-export — import origin directly |
| `run_generic_accept_exit` | `game.final_emission_generic_exit` | 0 | Retire re-export — import origin directly |
| `run_generic_replace_exit` | `game.final_emission_generic_exit` | 0 | Retire re-export — import origin directly |
| `run_non_strict_layer_stack` | `game.final_emission_non_strict_stack` | 0 | Retire re-export — import origin directly |
| `run_strict_social_composition_trunk` | `game.final_emission_strict_social_stack` | 0 | Retire re-export — import origin directly |
| `validate_emitted_speaker_against_contract` | `game.speaker_contract_enforcement` | 0 | Retire re-export — import origin directly |

## Highest fan-in exports (maintenance risk)

| Rank | Symbol | BU FI | Risk |
| --- | --- | --- | --- |
| 1 | `apply_final_emission_gate` | 17 | **Low-medium** — legitimate authority; 1 production path via `final_emission_runtime` |
| 2 | module introspection (`feg`) | — | **Medium** — test/governance coupling; not production sprawl |
| 3 | `get_speaker_selection_contract` | 1 | **Low** — compat re-export; migrate to `speaker_contract_enforcement` |
