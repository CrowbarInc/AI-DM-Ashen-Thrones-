# Playability validation runner (P3)

This project’s **playability scores** come only from `game.playability_eval.evaluate_playability`. The CLI `tools/run_playability_validation.py` is a thin harness: it drives `POST /api/chat`, records the transcript, and attaches the evaluator’s return value per turn. It does **not** re-score, infer pass/fail from thresholds, or interpret GM quality beyond writing evaluator output to disk.

Playability validation is the **final** player-facing validation layer: deterministic evaluation plus transcript-backed tests and the scenario runner. It is **validation and observability** only; it does not add runtime mechanics.

## Evaluation Model

- Playability is evaluated **per turn**
- The evaluator consumes:
  - `player_prompt`
  - `gm_text` or `gm_output.player_facing_text`
  - prior-turn context when present (`prior_player_prompt`, `prior_gm_text`, optional `debug_traces` pass-through)
- **Output:** axis scores, overall score, pass/fail (all from the evaluator return dict)

## Session Summary Behavior

- Session summaries are **not** native evaluator outputs for a whole session
- They are **derived** from the **final turn** evaluation for that scenario run

**Reason:** the evaluator is designed for turn-level analysis; avoiding cross-turn aggregation keeps the contract simple.

## Authority Rule (Reinforce)

**Do not:**

- reinterpret evaluator output
- recompute scores
- introduce secondary validation logic

**All** playability judgment comes from `evaluate_playability(...)`.

## Prerequisites

- Default mode uses FastAPI `TestClient` against the in-process app (same route as production: `/api/chat`). That executes the real chat pipeline (including model calls when configured).
- Optional `--base-url` sends HTTP `POST {base}/api/chat` instead (for a running server).

## Usage

```text
python tools/run_playability_validation.py --list
python tools/run_playability_validation.py --scenario p1_direct_answer
python tools/run_playability_validation.py --all
```

Flags:

| Flag | Meaning |
|------|---------|
| `--list` | Print scenario ids, turn counts, and one-line descriptions; exit. |
| `--scenario ID` | Run a single scenario. |
| `--all` | Run all scenarios (each run uses its own artifact folder). |
| `--no-reset` | Skip `apply_new_campaign_hard_reset()` before each scenario (default is to reset). |
| `--artifact-dir PATH` | Root for output folders (default: `artifacts/playability_validation/`). |
| `--base-url URL` | Remote origin for `/api/chat` (e.g. `http://127.0.0.1:8000`). |
| `--http-timeout SEC` | Timeout for remote chat when `--base-url` is set. |

## Scenarios

Preset **player lines** only (no rubric in the tool). Names align with evaluator axes; exemplar wording matches `tests/test_playability_eval.py`.

| Id | Focus |
|----|--------|
| `p1_direct_answer` | Direct-answer exemplars |
| `p2_respect_intent` | Broad prompt then narrowing follow-up |
| `p3_logical_escalation` | Same-topic pressure across two turns |
| `p4_immersion` | Short diegetic player line |

## Artifacts

**Roles:** `transcript.json` holds raw turns plus `playability_eval` per turn. `summary.json` is a thin wrapper over the **final** turn’s evaluator output only. `run_debug.json` is diagnostic only and is **not** part of the validation contract.

Each run writes a directory:

`artifacts/playability_validation/{UTC_TIMESTAMP}_{scenario_id}/`

Files:

- **`transcript.json`** — `turns[]` entries each contain `turn_index`, `player_prompt`, `gm_text`, `resolution_kind` (raw `resolution["kind"]` from the API when present), **`playability_eval`** (the full dict from `evaluate_playability(...)`), and **`narrative_authenticity_eval`**: the full dict from `game.narrative_authenticity_eval.evaluate_narrative_authenticity(...)` (telemetry-based; **not** a second playability rubric and **not** used for runtime enforcement).
- **`summary.json`** — Mirrors evaluator fields only (see below). Values are taken from the **last turn’s** `playability_eval` for that scenario (the evaluator always scores a single payload; there is no multi-turn aggregate inside the evaluator).
- **`run_debug.json`** — Same as transcript plus `api_ok` / `api_error` per turn for troubleshooting.

### `summary.json` shape

```json
{
  "report_version": 1,
  "scenario_id": "p1_direct_answer",
  "overall": { "...": "..." },
  "axis_scores": { "direct_answer": 0, "...": 0 },
  "failures": [],
  "warnings": []
}
```

- `overall` is exactly `evaluate_playability(...)["overall"]`.
- `axis_scores` maps each key in `["axes"]` to that axis object’s `"score"`.
- `failures` / `warnings` are exactly `evaluate_playability(...)["summary"]["failures"]` and `["warnings"]`.

No fields are recomputed in the CLI.

## Evaluator payload per turn

After each chat response, the runner builds the evaluator input as:

- `player_prompt` — string sent to `/api/chat`.
- `gm_text` — `gm_output.player_facing_text` from the response.
- `prior_player_prompt` / `prior_gm_text` — previous turn’s player line and GM text (empty on the first turn).
- `debug_traces` — copied from `session["debug_traces"]` when present (opaque pass-through for immersion-related signals).

Then it sets `playability_eval` to `evaluate_playability(that_dict)`.

It also sets `narrative_authenticity_eval` to `evaluate_narrative_authenticity(turn_packet, payload, _final_emission_meta_from_chat_payload(payload))`. That evaluator is fail-closed if `_final_emission_meta` / NA telemetry is missing (`missing_narrative_authenticity_telemetry`) and includes `narrative_authenticity_verdict` plus `rumor_realism_axes` for shipped-state reporting. Authority rule is unchanged: **do not** reinterpret or recompute either evaluator’s scores—read the written dicts only. For NA field meanings and debugging, see **Narrative Authenticity & Signal Quality** in `docs/README.md` and `docs/narrative_authenticity_anti_echo_rumor_realism.md`.
