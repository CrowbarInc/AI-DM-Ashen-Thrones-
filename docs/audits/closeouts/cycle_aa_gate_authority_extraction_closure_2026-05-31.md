# Cycle AA / Block AA5 — Gate Authority Extraction Closure

Date: 2026-05-31  
Model: Codex / GPT-5.5 Thinking  
Status: **Cycle AA closed** (AA1–AA4 complete; no further production extraction in AA5)

## Executive recommendation

**Close Cycle AA.** AA1–AA4 moved the planned low–medium-risk decision/projection surfaces out of `game/final_emission_gate.py` while preserving orchestration, compatibility wrappers, and replay invariants. Remaining gate code is intentionally dense **orchestration** plus **deferred high-risk policy** (tone, narrative authority, anti-railroading, context separation, narration purity, answer-shape primacy, ASP).

One optional **documentation-only** follow-up (not required for closure): refresh the gate module docstring to list `fallback_provenance_debug` containment and `final_emission_meta` accept-path / narration-constraint projection; soften the sealed-fallback docstring at `_select_non_strict_replace_path_terminal_sealed_fallback_selection` (“gate-owned providers” → “gate-injected provider callbacks”). Do **not** delete compatibility wrappers or chase wrapper deletion in AA5.

---

## Files changed across AA1–AA4

Working-tree delta on `feature/failure-locality` (uncommitted at audit time; reflects AA1–AA4 work):

| File | Role in cycle | Approx. delta |
|------|----------------|---------------|
| `game/final_emission_gate.py` | Orchestration hub; wrappers retained | ~725 lines touched, net contraction |
| `game/fallback_provenance_debug.py` | **AA1** — Block I upstream fast-fallback provenance containment | +107 lines |
| `game/final_emission_meta.py` | **AA2 / AA4** — accept-path `final_emitted_source`; narration-constraint debug projection | +372 lines |
| `game/final_emission_sealed_fallback.py` | **AA3 / AA2b** — non-strict sealed provider assembly; realization-family stamping helpers | +157 lines |

Reference recon (pre-implementation): `docs/cycles/cycle_aa_gate_authority_extraction_recon_2026-05-31.md`.

Gate size after extractions: **~9,078** non-blank lines (down from recon estimate ~10,391; ~100 `def` symbols remain in-module).

---

## Authority moved out of the gate

| Block | What moved | Canonical owner | Gate retains |
|-------|------------|-----------------|--------------|
| **AA1** | Upstream fast-fallback provenance containment decisions (when to restore selector text, pre-gate vs finalize kinds, fingerprint checks) | `game.fallback_provenance_debug` — `upstream_fallback_canonical_provenance`, `apply_upstream_fallback_pregate_containment`, `finalize_upstream_fallback_overwrite_containment` | Thin `_upstream_fallback_*` wrappers; orchestration calls in `apply_final_emission_gate` / `_finalize_emission_output` |
| **AA2** | Accept-path `final_emitted_source` precedence ladder (strict + generic accept) | `game.final_emission_meta.infer_accept_path_final_emitted_source` | Branch-specific `initial_source` + layer-meta gathering; FEM writes |
| **AA2b** | Sealed / strict-social terminal realization-family stamping on replace paths | `game.final_emission_sealed_fallback` (`stamp_*_realization_family`), `game.social_exchange_emission.project_strict_social_replace_realization_family` | Response-type repair debug still calls `attach_realization_fallback_family` for opening/upstream/dialogue repair kinds (RT-local debug, not terminal sealed replace) |
| **AA3** | Non-strict sealed fallback **provider assembly** (callable wiring to opening/social/passive/global builders) | `game.final_emission_sealed_fallback.build_non_strict_sealed_fallback_providers` | `_build_non_strict_sealed_fallback_providers` compatibility wrapper injecting gate-local tuple builders; branch **selection** still via `assemble_non_strict_sealed_fallback_selection` |
| **AA4** | Narration-constraint debug **projection** (defaults, build, meta merge primitives) | `game.final_emission_meta` — `default_narration_constraint_debug`, `build_narration_constraint_debug`, `merge_narration_constraint_debug_meta` | Thin `_default/_build/_merge_narration_constraint_*` wrappers; `_merge_narration_constraint_debug_into_outputs` orchestration (visibility contract resolve + speaker contract gather) |

**Not moved (by design):** replay read projection (`final_emission_replay_projection`), in-gate policy layers, `_enforce_response_type_contract`, visibility hard-replace routing, interaction continuity, N4/NMO acceptance policy, strict-social terminal selection (`social_exchange_emission`).

---

## Wrappers intentionally retained

| Symbol | Delegates to | Why kept |
|--------|--------------|----------|
| `_upstream_fallback_canonical_provenance` | `fallback_provenance_debug` | Historical imports; gate monkeypatch sites (e.g. containment tests) |
| `_apply_upstream_fallback_pregate_containment` | same | same |
| `_finalize_upstream_fallback_overwrite_containment` | same | `test_final_emission_gate` patches `_finalize_upstream_fallback_overwrite_containment` |
| `_default/_build/_merge_narration_constraint_debug*` | `final_emission_meta` | `test_final_emission_gate` asserts via `feg._build_narration_constraint_debug` |
| `_build_non_strict_sealed_fallback_providers` | `final_emission_sealed_fallback` | Injects gate-local passive-pressure / global tuple builders |
| `_select_non_strict_replace_path_terminal_sealed_fallback` | selection + `as_legacy_tuple()` | Legacy five-tuple test/imports |
| `_opening_scene_safe_fallback_tuple` | `final_emission_opening_fallback` adapter | First-mention composition injection |
| `_select_acceptance_quality_n4_sealed_fallback_line` | `final_emission_sealed_fallback` | Injects `minimal_social_emergency_fallback_line` + global tuple builder |

Deleting these wrappers without migrating test import paths fails the user rule (“do not delete wrappers unless tests prove safe”).

---

## Remaining authority inventory (`final_emission_gate.py`)

### Intentionally retained orchestration

- `apply_final_emission_gate` (~L8323+) — layer ordering, strict vs generic branches, upstream merge, FEM merges, logging, tags, route outcomes.
- `_finalize_emission_output` — packaging-only sanitize/strip, channel projection, provenance **call**, scene-opening reassert hook.
- Layer sequencing via `final_emission_repairs` imports (AC, RD, SRS, NA authenticity, fallback behavior, etc.).
- `_merge_narration_constraint_debug_into_outputs` — wires RT debug + visibility contract + speaker selection into meta-owned payload.
- Non-strict sealed **branch selection** orchestration (`_select_non_strict_replace_path_terminal_sealed_fallback_selection`) — mode/opening/social flags + `assemble_non_strict_sealed_fallback_selection`.
- Visibility enforcement **routing** (delegates payloads to `final_emission_visibility_fallback`).
- Acceptance-quality N4 floor seam, narrative-mode output legality assessment (orchestration + policy bits documented in-function).

### Compatibility wrappers (low-risk residue; not worth AA5 extraction)

- Provenance, narration-constraint, sealed-provider, opening, legacy sealed tuple wrappers (table above).

### High-risk policy layers (deferred AA5+ per recon rules)

| Cluster | Approx. line region | Decision authority |
|---------|---------------------|-------------------|
| Tone escalation | ~L819–1244 | Contract resolve, skip, narrow repair, apply |
| Narrative authority | ~L1269–1699 | Contract resolve, sentence-span repairs, apply |
| Anti-railroading | ~L1700–2171 | Contract synthesis/fallback build, repair passes, apply |
| Context separation | ~L2172–2544 | Contract resolve, repair, apply |
| Player-facing narration purity | ~L2545–2780 | Contract resolve, repair, apply |
| Answer-shape primacy | ~L2781–3142 | Validate/repair/apply ASP |
| Scene state anchor | ~L3143–3818 | SSA contract, opening repairs |
| Response type enforcement | ~L3709–4008 | Accept/repair/replace per `required_response_type` |
| Dialogue plan invariant (strict-social) | ~L639–743 | Block vs allow strict-social emission |
| Interaction continuity | ~L7704–8315 (recon) | IC validate/repair before finalize |
| Fast-path eligibility | ~L4355–4400 | Skip heavy layers when safe |
| Scene/passive fast-fallback composition | ~L4576+ | Passive pressure candidates, diegetic templates (injected into sealed providers) |

### Low-risk projection/helper residue (acceptable at closure)

- `_resolve_narration_constraint_debug_visibility_contract` — thin `build_narration_visibility_contract` wrapper for debug merge.
- `_current_speaker_binding_bridge` — reads emission_debug bridge.
- Fragment/participial finalize helpers (C2-disabled at boundary).
- Global visibility stock sentence strip helpers (finalize packaging adjunct).

**Not recommended before closure:** moving `_merge_narration_constraint_debug_into_outputs` or deleting narration/provenance one-liner wrappers — test surface is gate-private and behavior-neutral.

---

## Stale ownership comments

| Location | Issue | Severity |
|----------|-------|----------|
| `_select_non_strict_replace_path_terminal_sealed_fallback_selection` docstring: “gate-owned providers” | Provider **assembly** lives in `final_emission_sealed_fallback`; gate owns **injected prose builders** (passive pressure, global tuple). Wording is slightly misleading, not functionally wrong. | Low — doc-only fix optional |
| Module header (L1–50) | Does not yet mention AA1 provenance owner or AA2/AA4 meta projection under “Not the canonical owner for”. Still accurate for validators/repairs; incomplete post-AA. | Low — doc-only |
| `docs/cycles/cycle_aa_gate_authority_extraction_recon_2026-05-31.md` line map | Pre-AA line numbers (e.g. L4751 containment, L9199 `final_emitted_source`) are obsolete. Historical recon only. | Informational |
| `_narrative_mode_output_legality_assessment` ownership block (L8157+) | Still accurate (planner vs validator vs gate orchestration). | OK |
| `fallback_provenance_debug` mutation `source=` strings still say `gate._apply_*` | Intentional trace compatibility for Block I fingerprints. | OK |

No comment was found that **falsely claims** provenance containment or narration-constraint **build logic** still lives in the gate; implementation delegates correctly. Residual risk is **under-documentation**, not lying ownership.

---

## Validation result

Command (AA5 targeted bundle):

```text
.\.venv\Scripts\python.exe -m pytest tests/test_final_emission_gate.py tests/test_final_emission_meta.py tests/test_final_emission_opening_fallback.py tests/test_opening_fallback_owner_bucket.py tests/test_golden_replay.py tests/test_failure_classification_contract.py -q --tb=short
```

| Run | Result |
|-----|--------|
| **381 tests collected** | |
| First run (default `codex_pytest_tmp`) | **380 passed**, **1 failed** — `test_golden_replay_directed_npc_question_structural_invariants` with `PermissionError` on `combat.json` replace (Windows file lock in shared tmp; **environmental**, not gate logic) |
| Re-run non-golden modules | **326 passed** (gate + meta + opening + owner bucket + failure classification) |
| Re-run `test_golden_replay.py` with `--basetemp=codex_pytest_tmp_aa5_closure` | **55 passed** |

**Conclusion:** All targeted tests pass when golden replay uses an isolated basetemp. No golden snapshot updates performed. No regressions attributed to AA1–AA4 extractions.

---

## Replay / golden status

- Protected golden scenarios: **pass** under isolated basetemp (55 tests in `test_golden_replay.py`).
- `final_emitted_source`, fallback provenance traces, sealed replace routing, and opening owner buckets remain governed by existing contract tests (`test_failure_classification_contract.py`, opening fallback suites).
- Replay projection remains in `game.final_emission_replay_projection` (unchanged in AA).

---

## AA5 decision: close vs one more cleanup

| Option | Verdict |
|--------|---------|
| **Close AA** | **Recommended.** Planned extractions complete; gate is thinner; high-risk clusters explicitly deferred; wrappers serve tests and import stability. |
| **One more low-risk extraction** (e.g. delete narration/provenance wrappers, move `_merge_narration_constraint_debug_into_outputs` to meta) | **Not recommended.** Marginal line savings; requires test import migration and monkeypatch path updates; violates “honest closure over risky over-thinning.” |
| **Doc-only cleanup** (module header + sealed-selection docstring) | Optional, non-blocking. |

---

## Out of scope (unchanged)

Per cycle rules, do **not** extract in AA: tone / narrative authority / anti-railroading / context separation / purity / ASP policy layers; do not update golden snapshots; do not delete wrappers without proven test migration.

Next cycle (**AA5+** or dedicated blocks): one policy layer per block with full replay bundle, starting with highest fan-out only after dedicated audit (`_enforce_response_type_contract` split is recon-marked uncertain).
