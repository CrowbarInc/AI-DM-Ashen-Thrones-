# Ashen Thrones AI GM

A local, browser-based solo PF1e-inspired AI GM toolkit built for chat-first play with persistent scenes, world state, faction pressures, projects, and optional action helpers.

## Features
- Chat-first solo campaign play in the browser
- Persistent campaign, scene, character, world, and combat state
- World layer with factions, projects, assets, and event log
- GPT can draft and auto-save new scenes
- Optional combat action helpers for initiative, attacks, spells, and skill checks
- Character sheet import optimized for the exported JSON format used in this project
- One-command startup

## Requirements
- Python 3.9+
- OpenAI API key in `OPENAI_API_KEY`

## Setup
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OPENAI_API_KEY="your_key_here"
# Optional: override the model (defaults to gpt-4o-mini)
# $env:MODEL_NAME="gpt-4o-mini"
python run.py
```

Alternatively, use a local `.env` file for development:

```powershell
Copy-Item .env.example .env
# Edit .env and set OPENAI_API_KEY (never commit the real .env)
python run.py
```

Open:
`http://127.0.0.1:8000`

## Model Configuration
Environment variables define the routing defaults and fallback chain, but the actual model is selected per request in `game.gm.call_gpt(...)` from explicit route inputs such as `purpose`, `retry_attempt`, `retry_reason`, `strict_social`, and `force_high_precision`.

Legacy or single-model-compatible setup:

```powershell
$env:MODEL_NAME="gpt-4o-mini"
$env:ENABLE_MODEL_ROUTING="true"
```

Hybrid setup:

```powershell
$env:MODEL_NAME="gpt-4o-mini"
$env:DEFAULT_MODEL_NAME="gpt-4o-mini"
$env:HIGH_PRECISION_MODEL_NAME="gpt-4.1-mini"
$env:RETRY_ESCALATION_MODEL_NAME="gpt-4.1-mini"
$env:ENABLE_MODEL_ROUTING="true"
```

- `MODEL_NAME` remains backward compatible and seeds `DEFAULT_MODEL_NAME` when newer vars are omitted.
- `DEFAULT_MODEL_NAME`, `HIGH_PRECISION_MODEL_NAME`, and `RETRY_ESCALATION_MODEL_NAME` define the default lane and its stronger fallbacks.
- Strict-social turns and retry escalation can route a GPT call to the stronger configured model.
- Setting `ENABLE_MODEL_ROUTING=false` keeps calls on `DEFAULT_MODEL_NAME` without changing player-facing schemas.
- Deterministic and non-GPT repair paths stay outside the routing system.

See `docs/model_routing_architecture.md` for the current routing note.

## Notes
- The engine owns mechanics and persistence.
- GPT owns narration, scene drafting, world suggestions, and narrative consequences.
- Scene drafting is auto-saved when GPT returns `new_scene_draft`.
- The app starts with the `Ashen Thrones` campaign seed, but the Campaign tab can rewrite it.

## Current Supported Mechanics
- Initiative
- End turn
- Basic attacks
- Daze
- Magic Missile
- Shield
- Risky Strike
- Defensive Stance
- Basic condition framework

## Project Layout
- `game/` backend modules
- `data/` runtime state
- `data/scenes/` scene registry
- `static/` browser UI
- `docs/README.md` this file

## Narrative Authenticity & Signal Quality

Operator-facing map of the **implemented** narrative authenticity (NA) stack: deterministic contract, validation, bounded repair, gate wiring, telemetry, offline evaluator, and how to debug a bad turn. For broader “where does emission logic live?” routing, see `docs/narrative_integrity_architecture.md`.

### Layer stack (architecture)

End-to-end order of responsibility:

1. **Contract (prompt layer)** — `game/prompt_context.py` builds `response_policy.narrative_authenticity` via `game/narrative_authenticity.build_narrative_authenticity_contract` (lazy import at contract assembly to avoid import cycles). The same object is shipped on the turn for prompts and gate reads. `RESPONSE_RULE_PRIORITY` / `RULE_PRIORITY_COMPACT_INSTRUCTION` encode precedence relative to other policies (e.g. answer completeness, response delta, fallback brevity).
2. **Validator** — `game/narrative_authenticity.validate_narrative_authenticity`: multi-signal, deterministic checks only (no LLM). Uses helpers from `game/final_emission_validators` where shared primitives exist; NA-specific logic stays in this module.
3. **Repair** — `game/narrative_authenticity.repair_narrative_authenticity_minimal` (same module as validator): bounded, multi-pass, subtractive-first; re-validates after each successful repair path.
4. **Gate integration** — `game/final_emission_gate.apply_final_emission_gate` calls `game/final_emission_repairs._apply_narrative_authenticity_layer` in a fixed position relative to other emission layers (see **System interactions**).
5. **Meta / trace emission** — `game/final_emission_repairs` merges NA fields into `gm_output["_final_emission_meta"]` via `_merge_narrative_authenticity_meta`; compact trace slices come from `game/narrative_authenticity.build_narrative_authenticity_emission_trace`.
6. **Stage diff visibility** — `game/stage_diff_telemetry.py` records gate-stage snapshots; NA skip/reason codes from `_final_emission_meta` are copied into snapshots for diffing (observability only, not policy).
7. **Evaluator (offline)** — `game/narrative_authenticity_eval.evaluate_narrative_authenticity`: deterministic 0–5 scores on five axes from telemetry (+ light text heuristics); **does not** re-run the validator and **does not** affect the live pipeline.
8. **Validation runner** — `tools/run_playability_validation.py` drives real `POST /api/chat` (FastAPI `TestClient` or `--base-url`), writes artifacts under `artifacts/playability_validation/`, and attaches both `playability_eval` and `narrative_authenticity_eval` per turn. See `docs/playability_validation.md`.

### Enforced behaviors (when the layer runs)

With contract enabled and not skipped for fallback compatibility, validation targets include:

- **No narration → dialogue echo** — Quoted speech must not largely recycle preceding narration tokens/trigrams (`dialogue_echoes_prior_narration`).
- **No low-signal filler responses** — Generic padding / thin atmospheric-only beats fail as `low_signal_generic_reply` when heuristics fire and negative controls do not excuse them; brevity with real dialogue can be allowed via `fallback_compatibility`.
- **No adjacent structural repetition** — Consecutive sentences with scaffold overlap beyond `max_anchor_reuse_clauses` (with continuity allowance) → `adjacent_phrase_reuse`.
- **No follow-up stagnation** — On topic follow-up, overlap with prior GM snippet without meaningful change markers → `follow_up_stale_restatement`; when response-delta is active, a **shadow** `validate_response_delta` failure surfaces as `follow_up_missing_signal_shadow_response_delta` (NA reads delta outcome; it does not implement delta repair).
- **Escalation / follow-up must introduce meaningful change** — Contract flag `require_meaningful_change_on_followup` combines token overlap, `signal_markers_detected`, and `_meaningful_followup_change_vs_prior` heuristics (not interpersonal tone escalation; that is `game/tone_escalation`).
- **NPC dialogue grounded and contextual** — `non_diegetic_meta_voice` rejects validator/system-style fallback voice in player-facing text.

### Anti-goals (do not regress these)

The shipped contract’s `anti_goals` / `fallback_compatibility` blocks encode hard product boundaries:

- **Do not force verbosity** — Short, contract-correct answers must remain valid.
- **Do not invent facts or world state** — Repairs remove, compress, strip echo prefixes, or reorder; they never add new diegetic claims.
- **Do not override fallback correctness** — When fallback uncertainty is active, NA may **skip** (`fallback_uncertainty_brief_compat`) so brevity and uncertainty shapes stay authoritative.
- **Do not duplicate `response_delta` logic** — NA may **call** `validate_response_delta` for a shadow signal only; delta repair stays in the response-delta layer.
- **Do not introduce subjective “quality scoring” into enforcement** — The gate is pass/fail on explicit reason codes. Numeric “scores” exist only in **`narrative_authenticity_eval`** (offline).

### Repair philosophy (hard constraint)

All repair modes in `repair_narrative_authenticity_minimal` honor:

- **Subtractive-first** — Drop redundant sentences, compress weak filler shells, trim dialogue-prefix overlap before considering stronger edits.
- **Compression over rewriting** — Prefer removing low-signal sentences over paraphrasing content.
- **Reordering allowed when deterministic** — e.g. `reorder_followup_high_signal_first` when sentence scoring shows a strict improvement and re-validation passes.
- **No new content generation** — No LLM, no invented clauses; only removals, merges, prefix strips on existing quotes, and order changes that pass `validate_narrative_authenticity`.
- **Preserve correctness and response type** — Repairs must leave the candidate passing NA **and** must not substitute a different contract owner’s obligations (other layers remain responsible for their own shapes).

### Evaluator behavior (`narrative_authenticity_eval`)

- **Inputs** — Merges NA keys from `meta` with `gm_output["_final_emission_meta"]` (`_merge_na_meta`).
- **No re-validation** — Uses telemetry keys only; does not call `validate_narrative_authenticity`.
- **Deterministic scoring** — Five legacy axes, each scored 0–5: `signal_gain`, `anti_echoing`, `followup_evolution`, `non_generic_specificity`, `npc_voice_grounding`.
- **Verdict + rumor axes** — `narrative_authenticity_verdict` (`clean_pass` / `relaxed_pass` / `repaired_pass` / `fail` / `unchecked` / `missing_telemetry`) and `rumor_realism_axes` + `rumor_realism_axis_reasons` summarize shipped NA status, repair modes, relaxation flags, and rumor telemetry without flattening repaired/relaxed into a generic pass. See **`docs/narrative_authenticity_anti_echo_rumor_realism.md`**.
- **Fail-closed on missing telemetry** — If the response lacks `_final_emission_meta` and the caller did not supply any NA keys, returns `passed: false`, all scores `0`, `reasons: ["missing_narrative_authenticity_telemetry"]`, `narrative_authenticity_verdict: "missing_telemetry"`, and zeroed rumor axes.
- **Artifacts** — `tools/run_playability_validation.py` writes `narrative_authenticity_eval` next to `playability_eval` in `transcript.json` / `run_debug.json`.
- **Not enforcement** — Evaluator output is for operators and regression artifacts; it does not feed back into the gate.

### Debugging workflow: how to debug a bad response

1. Open `gm_output["_final_emission_meta"]` on the finalized chat payload (same structure whether you inspect API JSON or runner artifacts).
2. Check NA fields:
   - `narrative_authenticity_reason_codes` — failing codes when checked and failed; also mirrored from validator `failure_reasons`.
   - `narrative_authenticity_metrics` — numeric overlap/filler/signal summaries (slimmed for emission).
   - `narrative_authenticity_evidence` — short clips (matched patterns, ngrams, echo spans).
   - `narrative_authenticity_skip_reason` — why the layer did not enforce (e.g. `fallback_uncertainty_brief_compat`, `contract_disabled`, layer skip from repairs).
   - `narrative_authenticity_repair_applied` / `narrative_authenticity_repaired` / `narrative_authenticity_repair_mode` — whether subtractive repair fixed the text.
3. Decide:
   - **Was NA triggered?** `narrative_authenticity_checked` true; if false, read `narrative_authenticity_skip_reason`.
   - **Was it repaired?** `narrative_authenticity_repaired` or `narrative_authenticity_repair_applied` true; `narrative_authenticity_repair_mode` names the winning strategy.
   - **Did the gate replace the whole candidate?** If `_final_emission_meta["final_route"] == "replaced"`, the emitted text is a deterministic fallback, not the model line NA saw. Check `rejection_reasons_sample` and `gm_output["debug_notes"]` for the `final_emission_gate:replaced:` prefix (may include `narrative_authenticity_unsatisfied_after_repair` when repair could not clear failures).
   - **Did fallback behavior or a later layer reshape text without full replace?** On the accept path, compare fingerprints/previews in `stage_diff_telemetry`; inspect `fallback_behavior_*` in `_final_emission_meta`, `fallback_kind` / tags on `gm_output`, and snapshot `fallback_source` / `fallback_stage`.
4. Cross-check **`narrative_authenticity_eval`** (from the runner or by calling `evaluate_narrative_authenticity`):
   - `scores` — per-axis 0–5 view of telemetry.
   - `narrative_authenticity_verdict` / `rumor_realism_axes` — explicit pass vs relaxed vs repaired vs fail vs unchecked (see `docs/narrative_authenticity_anti_echo_rumor_realism.md`).
   - `reasons` — deterministic explanations (includes `narrative_authenticity_gate_failed_unrepaired` when the gate left a failure in place).
5. **Classify the failure layer**
   - **NA** — reason codes under `narrative_authenticity_*` with checked true.
   - **response_delta** — primary ownership: `response_delta_*` meta; NA may only cite `follow_up_missing_signal_shadow_response_delta`.
   - **fallback** — `narrative_authenticity_skip_reason` of `fallback_uncertainty_brief_compat` or strong `fallback_behavior_*` / provenance traces after NA ran.
   - **continuity / other** — `game/interaction_continuity` and strict-social paths are separate; use their meta and `social_response_structure_*` fields, not NA codes.

### Telemetry field reference (`narrative_authenticity_metrics` / `evidence`)

| Field | Meaning |
| --- | --- |
| `generic_filler_score` | 0–1 heuristic density of generic padding / weak shells / atmospheric-only patterns in the emitted text. |
| `adjacent_phrase_overlap` | Ratio of adjacent sentence pairs that hit structural reuse to total pairs; pairs drive `adjacent_phrase_reuse` when over budget. |
| `quote_narration_overlap` | Token Jaccard between narration preceding a quote and the quoted span; paired with trigram overlap for echo detection. |
| `followup_overlap` | Token Jaccard between current text and prior GM snippet when topic follow-up is active (no response-delta shadow path). |
| `signal_markers_detected` | Count of follow-up “new signal” markers (reactions, perspective shifts, refusal boundaries, digits, etc.). |
| `matched_filler_patterns` | Which named filler regex families fired (evidence list; used to justify generic score / removals). |
| `reused_ngrams` | Shared scaffold trigrams between the first failing adjacent pair (debug for structural duplication). |

### System interactions

- **`response_delta`** — NA **reuses** `validate_response_delta` for follow-up shadow failures only; all delta repairs and `response_delta_*` meta stay in `final_emission_repairs._apply_response_delta_layer`.
- **`fallback_behavior`** — Runs in the gate **after** NA (and after several other layers); it may replace or reshape text **after** NA repairs. NA explicitly skips enforcement when fallback uncertainty compatibility applies.
- **`social_response_structure`** — Applied **before** NA in the gate sequence so dialogue shape is stable before echo/signal checks.
- **`narrative_authority`** — Applied **after** NA (tone escalation sits between them in the main pipeline).
- **Evaluator** — Consumes merged NA telemetry only; never mutates pipeline output.

Canonical emission order for the policy stack around NA (see `final_emission_gate.apply_final_emission_gate`): answer completeness → response delta → social response structure → **narrative authenticity** → tone escalation → narrative authority → anti-railroading → context separation → player-facing narration purity → answer shape primacy → scene state anchor → fast fallback neutral composition → … → fallback behavior (late pass; can override earlier repairs).

### Circular import constraint

**Why lazy imports exist** — `game/narrative_authenticity` must import shared sentence splitting and related helpers from `game/final_emission_validators` inside `validate_narrative_authenticity` (and repair helpers), while `final_emission_validators` / `final_emission_repairs` / `final_emission_gate` already depend on the NA surface. Eager top-level imports would create a cycle.

**Dependency risk** — Moving imports to module top level can hard-fail import of `game` or produce partial initialization.

**Rule** — **Do not** convert NA’s lazy imports inside `validate_narrative_authenticity` / repairs to eager imports without restructuring ownership (e.g. extracting shared primitives to a leaf module). Same pattern applies to `prompt_context`’s deferred import of `build_narrative_authenticity_contract`.

### Known limitations

- **Heuristic detection** — Token/trigram/pattern based; not semantic “understanding” of good prose.
- **Bounded repair** — If subtractive passes cannot satisfy all active failures, NA stays failed (`narrative_authenticity_failed` true) and may contribute `narrative_authenticity_unsatisfied_after_repair` to the gate’s aggregated `reasons`, which can force `final_route: replaced` (see debugging workflow).
- **Evaluator reflects telemetry** — High scores do not prove literary quality; low scores can follow from unrelated gate skips or missing meta.
- **Signal-first objective** — The system optimizes for non-echo, non-stagnation, and signal density, not for creative excellence.

### Maintenance guidance

- **Extend filler detection** — Add patterns to `_GENERIC_FILLER_PATTERNS` (or the scoring function) with unit tests in `tests/test_narrative_authenticity.py`; prefer evidence-producing named patterns so operators can see `matched_filler_patterns`.
- **Tune thresholds** — Adjust overlap/filler cutoffs in `validate_narrative_authenticity` with golden strings; watch `generic_filler_score` distribution and false positives on short legal replies.
- **Add negative controls** — Follow `_diegetic_signal_negative_control` patterns: new excuses must be **deterministic** and **inspectable** in evidence, not vibes-based.
- **Validate changes** — Run `pytest` on NA tests and `python tools/run_playability_validation.py --scenario …` (or `--all`); inspect `narrative_authenticity_eval` in artifacts alongside `playability_eval`.

### Design principles

- **Determinism over cleverness** — Same text + same contracts ⇒ same outcome.
- **Subtractive repair over generative repair** — Never “write a better paragraph” inside NA.
- **Single source of truth (telemetry → evaluator)** — Offline scores read `_final_emission_meta` / merged NA keys only.
- **Non-interference with correctness layers** — NA defers under fallback uncertainty and does not duplicate answer completeness or response delta enforcement.
