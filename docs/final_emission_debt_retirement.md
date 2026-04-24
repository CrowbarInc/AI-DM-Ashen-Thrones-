# Final emission debt retirement (first pass)

This document freezes the **boundary contract** for `game/final_emission_*` and adjacent gate wiring. Runtime refactors follow this spec; see `game/final_emission_contract.py` for import-safe vocabulary mirrors.

## Final emission — allowed responsibilities

Final emission **may only**:

1. **Enforce legality** — run deterministic checks, assert allow-listed mutation kinds (`game/final_emission_boundary_contract`), reject or replace output only along contracted terminal paths.
2. **Strip / package output** — whitespace and HTML cleanup, route-illegal contamination stripping, punctuation normalization, FEM / debug sidecar packaging.
3. **Merge safe metadata / telemetry** — bounded dict merges, skip reasons, evaluator-facing projections that do not invent diegetic facts.
4. **Select already-prepared upstream outputs** — read `upstream_prepared_emission` and similar fields populated **before** the gate (`game/upstream_response_repairs`, prompt assembly), without minting substitute answer/action prose at the boundary.

## Final emission — forbidden responsibilities

Final emission **must not**:

1. Semantically reconstruct narration or “fix” model meaning after the fact.
2. Invent, extend, or repair narrative content to satisfy answer completeness, response delta, or social expectations.
3. Reorder sentences or paragraphs to front-load answers or deltas.
4. Add spoken openings, bridge lines, or dialogue cadence edits for voice cosmetics.
5. Smooth prose, split clauses for readability, or tune cadence for quality optics.
6. Choose alternate phrasing because it reads “better” while changing truth-conditions or social stance.
7. Compose fallback meaning except **subtractive** removal of contract-banned stock phrases / overcertainty spans already classified as legality strips, or hard terminal routes explicitly allow-listed.

## Semantic repair (definition)

**Semantic repair** is any transform whose **primary intent** is to change what the player should understand happened in the fiction, including:

- Adding, removing, or swapping facts, entities, motives, quantities, or feasibility.
- Rewriting refusals/partials so the *propositional content* differs (not merely stripping meta-voice boilerplate).
- Reordering or merging sentences so an answer “counts” as complete or a delta “reads” as new.
- Minting spoken leads, next-step hints, or clarifying questions from templates when upstream did not supply them as prepared text.
- Cadence / monologue / dialogue-shape edits whose goal is social naturalism rather than byte-level packaging.

Legality-only **subtractive** strips (remove spans matching forbidden patterns) are not semantic repair when they do not replace removed spans with new composed prose.

## Packaging-only normalization (definition)

**Packaging-only normalization** changes **transport shape** without intending to change diegetic commitments, for example:

- Collapsing redundant whitespace, normalizing newlines, stripping HTML tags.
- Uniform terminal punctuation on already-finalized strings.
- Merging telemetry dicts, clipping evidence strings, sorting log keys.
- Replacing illegal route-global fallback text with a **sealed** deterministic replacement explicitly authorized as a legality terminal.

If a transform changes *which facts are asserted*, it is not packaging-only.

## Ownership map (upstream vs boundary)

| Concern | Owns it (primary) |
| --- | --- |
| Answer completeness | Prompt / policy assembly, model instruction, `upstream_response_repairs` prepared text, pre-gate cash-outs — **not** final emission composition. |
| Response delta | Same upstream layers; final emission may **validate** and record failure only. |
| Social response shape | `social_exchange_emission` and related social resolution paths; final emission validates / defers. |
| Fallback construction | `upstream_response_repairs`, diegetic fallback narrators, social emission — not template synthesis at the gate. |
| Narrative authenticity | `narrative_authenticity` (+ evaluator modules); gate merges traces, does not “fix” realism. |
| Acceptance quality | `acceptance_quality` (invoked from gate orchestration but not as free-form prose author). |
| Narrative mode | `narrative_mode_contract` and callers that set mode contracts. |
| Visibility / referential clarity | Referent tracking producers in the prompt path; final emission may apply **minimal** pronoun→label substitution only when the full artifact explicitly authorizes a single label (contracted narrow path). |

## Migration checklist (legacy repair helpers)

Use this when retiring helpers in `game/final_emission_repairs.py` and similar:

1. **Classify** the helper: semantic repair vs packaging vs legality strip (document the call in this file’s debt notes if ambiguous).
2. **Move semantic work** to the row in the ownership table above; ensure `prompt_context` / `upstream_prepared_emission` carries any substitute text.
3. **Replace gate calls** with validation + FEM skip/fail metadata only, if the boundary must not mutate text.
4. **Rename** symbols that trip `FINAL_EMISSION_FORBIDDEN_IDENTIFIER_SUBSTRINGS` once behavior has moved (keeps audit noise low).
5. **Shrink** the snapshot sets in `tests/test_final_emission_debt_retirement.py` after each removal.
6. **Run** `pytest tests/test_final_emission_*.py` and integration tests touching social / fallback paths.

## Related references

- `docs/final_emission_ownership_convergence.md` — Objective C2 convergence notes.
- `game/final_emission_boundary_contract.py` — mutation kind classification.
- `game/final_emission_contract.py` — allowed/forbidden vocabulary + forbidden identifier substrings.

## Current boundary status after retirement

- **Block B** removed final-emission semantic helpers (spoken-opening restore, dialogue cadence shaping, substantive merge, expository trims, fallback template synthesis, answer-shape primacy moves, and related “smooth / reconstruct” surfaces). `tests/test_final_emission_debt_retirement.py` keeps **empty** substring snapshots for `game/final_emission_*.py` and guards exact retired symbol names so those helpers cannot return as live identifiers.
- **Block C** owns **upstream-prepared** answer/action lines and sanitizer-shaped stock in `game/upstream_response_repairs.py`, attaching `upstream_prepared_bundle_origin` for payload assembly provenance. The gate reads prepared text only; it does not mint contract-shaped prose when upstream preparation is missing or invalid.
- **Final emission** is **legality + packaging + metadata only**: validators, subtractive strips, whitespace/HTML normalization, FEM merges, and selection of already-prepared upstream fields. It does **not** perform semantic repair or fallback synthesis when upstream-prepared emission is absent or malformed—those cases are **reported** via `upstream_prepared_emission_valid`, `upstream_prepared_emission_reject_reason`, and related RTD1 / FEM keys (`response_type_upstream_prepared_absent` when nothing usable was supplied for answer/action repair).
- **Attribution:** `upstream_prepared_emission_attribution` (when set) becomes `upstream_prepared_emission_source` on the FEM / RTD1 surface. `upstream_prepared_bundle_origin` remains on the `upstream_prepared_emission` dict for assembly tracing and is **not** copied into FEM, so the two channels do not overwrite each other.
- **Tests that lock the boundary:** `tests/test_final_emission_debt_retirement.py`, `tests/test_final_emission_boundary_convergence.py`, `tests/test_final_emission_gate.py`, `tests/test_final_emission_repairs.py`, `tests/test_final_emission_validators.py`, `tests/test_final_emission_meta.py`, `tests/test_upstream_response_repairs.py`, plus social/fallback/acceptance suites listed in the objective’s pytest commands.
