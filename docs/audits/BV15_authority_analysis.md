# BV15 — Authority Analysis

**Date:** 2026-06-21

---

## Module self-description vs reality

Docstring claims: *canonical orchestration owner for final player-facing emission*; *not the canonical owner for validators, repairs, text formatting, or response_type contracts*.

**Reality matches intent post-BN decomposition.** The module body is a **thin orchestration router** (338 LOC, 1 defined function) that delegates to extracted stack owners (`strict_social_stack`, `non_strict_stack`, `generic_exit`, `gate_context`). FI **30** is inflated by **test/governance introspection** (module-level `feg` imports) rather than production utility accretion.

## Export classification

| Export | Class | Verdict |
| --- | --- | --- |
| `apply_final_emission_gate` | canonical-gate-authority | **Legitimate authority** — sole orchestration entry; BU FI 17 |
| `run_strict_social_composition_trunk`, `run_non_strict_layer_stack`, `run_generic_*_exit` | orchestration-delegate | **Legitimate but stale namespace** — 0 external imports; re-export for BN2 monkeypatch retirement |
| `initialize_gate_execution_context` | orchestration-delegate | Preflight context owner re-export — 0 external imports |
| `get_speaker_selection_contract`, `validate_emitted_speaker_against_contract`, `detect_emitted_speaker_signature` | compatibility-bridge | **Retire** — import `speaker_contract_enforcement` / `emitted_speaker_signature` directly |
| `apply_interaction_continuity_emission_step`, `attach_interaction_continuity_validation` | compatibility-bridge | **Retire** — import `interaction_continuity` directly; governance tests verify identity only |
| `resolve_gate_preflight_pregate_text`, `apply_observe_passive_scene_concrete_beat_upstream_satisfier` | helper | Internal-only re-exports — remove from public namespace |

## Canonical authority determination

| Question | Answer |
| --- | --- |
| Is `final_emission_gate` a legitimate orchestration authority? | **Yes** — single entrypoint owns strict vs non-strict routing |
| Is FI 30 justified by heterogeneous utility? | **No** — 97% test/governance; 1 production importer |
| What is actually authoritative here? | Orchestration sequencing only — stacks/terminal/finalize own behavior |
| Accidental coupling surfaces? | **13 namespace re-exports** — legacy BN2 compat; 0–1 external consumer each |

## Projection helpers vs accidental bridges

| Pattern | Examples | Assessment |
| --- | --- | --- |
| Canonical orchestration | `apply_final_emission_gate` | **Keep centralized** — this is the authority |
| Stack delegation | `run_*_stack`, `run_generic_*_exit` | Delegates already extracted — **remove re-exports** |
| Speaker/IC compat | `get_speaker_selection_contract`, IC attach/step | **Compatibility bridges** — governance-verified identity; retire namespace |
| Module introspection | `import feg` in 16 test files | **Governance coupling** — acceptable short-term; not production hub pressure |
