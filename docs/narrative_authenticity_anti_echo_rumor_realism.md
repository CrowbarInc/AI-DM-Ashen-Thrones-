# Anti-echo and rumor realism (shipped behavior)

This document describes the **implemented** rumor-realism and anti-echo behaviors in `game/narrative_authenticity.py`, how telemetry exposes them, and how operators should read failures. It complements the stack overview in `docs/README.md` and the module map in `docs/narrative_integrity_architecture.md`.

## What this layer does

- **Anti-echo (NA-wide)** — Blocks narration→dialogue recycling, adjacent structural reuse, follow-up stagnation, low-signal generic replies, and non-diegetic meta voice (see `validate_narrative_authenticity`).
- **Rumor realism (rumor / secondhand turns only)** — When `trace.rumor_turn_active` is true and `rumor_realism.enabled`, the validator scores **secondhand realism categories** (source limitation, uncertainty/distortion, perspective/bias, net-new detail) against quoted or unquoted substantive slices, and applies **overlap / verbatim** rules between the rumor slice and recent GM narration or same-turn narration outside quotes.

## When `rumor_turn_active` is true (high level)

`classify_rumor_secondhand_turn` scans the player prompt (and light context) for gossip / hearsay lexicon (`rumors`, `what have you heard`, `word on the street`, etc.). The classifier writes reason codes and trigger spans into the contract `trace` (`rumor_turn_active`, `rumor_turn_reason_codes`, `rumor_trigger_spans`). The gate copies that trace into validation metrics (`rumor_turn_active`) for emission.

## Validator reason codes (rumor-related)

Common rumor failures include:

| Code | Meaning (short) |
| --- | --- |
| `rumor_uses_identical_phrasing_for_known_fact` | Long phrase-identical overlap with prior GM or same-turn narration when identical phrasing is forbidden. |
| `rumor_repeats_recent_narration` | Heavy paraphrase-style reuse of recent GM narration without enough realism signal. |
| `rumor_restates_scene_description` | Same-turn narration outside quotes is recycled into the rumor slice. |
| `rumor_adds_no_new_signal` | Required realism category not satisfied (see `require_one_of`). |
| `secondhand_info_lacks_source_limitation` | No hearsay / limitation / channel framing. |
| `secondhand_info_lacks_uncertainty_or_bias` | Neither uncertainty/distortion nor perspective/bias markers detected. |

Echo and low-signal rumor codes can co-exist; repair order is **echo-class first**, then bounded rumor transforms.

## Repair modes (bounded rumor path)

`repair_narrative_authenticity_minimal` runs **dialogue-echo repair before rumor repair** (source order). Rumor bounded repairs (`_repair_rumor_realism_bounded`) only consider subtractive / reorder transforms on quoted clauses (or unquoted sentence drop when there is no quote), each **re-validated** before acceptance:

- `drop_echoed_rumor_clause` — Remove echoing clause(s) or unquoted echoing sentences.
- `compress_redundant_reported_speech` — Collapse duplicate clauses inside a quote.
- `reorder_distinct_rumor_clause_first` — Deterministic reorder by signal / echo penalty.
- **Low-signal transforms** (only when **not** under rumor low-signal relaxation for repair gating): `compress_generic_rumor_shell`, `retain_source_limited_clause_only`, `retain_uncertain_clause_only`, `retain_biased_clause_only`.

## Terminal state model (`narrative_authenticity_status`)

Emitted on `_final_emission_meta` when the layer finishes a checked path:

| Status | Meaning |
| --- | --- |
| `pass` | Checked, passed, not repaired, not rumor-relaxed. |
| `relaxed` | Checked, passed under rumor **low-signal relaxation** (`narrative_authenticity_rumor_relaxed_low_signal` true; see relaxation flags). |
| `repaired` | Checked, repair succeeded; `narrative_authenticity_repair_mode` / `repair_modes` name the winning strategy. |
| `fail` | Checked terminal failure (including repair-failed outcomes as wired by the emission layer). |

**Unset status** — If `narrative_authenticity_checked` is false, there is **no** terminal `narrative_authenticity_status`. Read `narrative_authenticity_skip_reason` when present. **Unset status is not a success signal**; it means skip / unchecked / non-terminal.

## Allowed fact overlap vs forbidden phrase-identical reuse

With `allow_partial_fact_overlap` true, a rumor can reuse **facts** if realism signals are present (source / uncertainty / bias / net-new). **Phrase-identical** reuse of long spans against prior GM or same-turn narration still fails when `forbid_identical_phrasing_even_when_overlap_allowed` is true (default): paraphrase the same fact with hearsay framing instead of copying the prior sentence.

## Quoted vs unquoted (high level)

Quoted spans drive clause splitting for bounded repairs. Same-turn narration used for `rumor_restates_scene_description` is taken from **non-quoted** regions. Unquoted rumor echo can still be repaired via sentence drop when there is no quote span.

## Fallback relaxation (rumor)

`rumor_realism.fallback_compatibility` gates **validator-side** relaxation via `_rumor_relaxed_signal_requirement` (brevity alone, bounded-partial under uncertainty, source-limited refusal language, answer shape). When relaxation applies to a failing requirement set, the validator marks `rumor_realism_relaxed_low_signal` and relaxation flags instead of hard-failing those requirement rows.

**Repair gating** uses the same helper’s **boolean** `relaxed_low_signal`: when true, **low-signal-specific** rumor transforms are disabled; **echo-class** rumor repairs still run (AER2/AER3 split).

## Clean-pass rumor telemetry

On a clean rumor pass, emission still attaches slim `narrative_authenticity_metrics` / `evidence` when `rumor_turn_active` is true so operators retain overlap counts, signal counts, and trigger spans in `narrative_authenticity_trace`.

## AER4 edge cases (operator clarity)

1. **Relaxation flags without `status="relaxed"`** — A bounded-partial or brevity relaxation can set `narrative_authenticity_relaxation_flags` while the terminal status stays absent or `fail` if another hard failure (for example `rumor_repeats_recent_narration`) still blocks pass.
2. **Unset status** — Layer skip or validator skip: not a checked pass; read `narrative_authenticity_skip_reason`.
3. **Nested vs top-level flags** — Nested trace may expose `rumor_relaxation_flags`; top-level meta uses `narrative_authenticity_relaxation_flags`. Both should agree when emission is consistent.
4. **Pass fixtures need genuine paraphrase** — Phrase-identical quoted rumor can still **correctly** fail as identical phrasing even when the underlying fact is allowed under overlap policy.

## Operator debugging (short)

| Question | Where to look |
| --- | --- |
| Why did this rumor fail? | `narrative_authenticity_reason_codes`, `rumor_missing_realism_categories` in evidence, overlap metrics (`rumor_overlap_jaccard`, `rumor_overlap_trigram`). |
| Why **repaired** instead of **pass**? | `narrative_authenticity_status == "repaired"` and `narrative_authenticity_repair_mode` / `repair_modes` — the model line failed NA and subtractive repair cleared it. |
| Why **relaxed** instead of **pass**? | `narrative_authenticity_rumor_relaxed_low_signal` true and relaxation flags; validator accepted under compatibility, not a strict full-signal pass. |
| Why is **status unset**? | `narrative_authenticity_checked` false — read `narrative_authenticity_skip_reason` (`response_type_contract_failed`, `fallback_uncertainty_brief_compat`, etc.). |
| How do I know repair happened? | `narrative_authenticity_repaired` / `repair_applied`, repair mode fields, and diff fingerprints in stage telemetry when enabled. |
| Trigger spans / classifier codes? | `narrative_authenticity_trace.rumor_trigger_spans`, `rumor_turn_reason_codes`. |
| Overlap metrics vs missing-realism categories? | Overlap metrics measure **text reuse** against prior / narration; missing-realism categories list which **hearsay obligations** (source, uncertainty, bias, net-new) were absent. They are orthogonal signals. |

## Offline evaluator (`narrative_authenticity_eval`)

The evaluator adds:

- `narrative_authenticity_verdict` — `clean_pass`, `relaxed_pass`, `repaired_pass`, `fail`, `unchecked`, or `missing_telemetry` (never flatten repaired/relaxed into generic “pass”).
- `rumor_realism_axes` — Five 0–5 axes: `rumor_echo_control`, `secondhand_realism`, `rumor_repair_success`, `rumor_relaxation_correctness`, `rumor_state_hygiene`, derived **only** from shipped meta/trace (no validator replay).

## Known limitations

- Low-signal rumor transforms require **multi-clause** quoted inner structure (`;` or em dash boundaries, or long comma splits); single-clause quotes will not hit `compress_generic_rumor_shell`.
- Relaxation and overlap policies are **contract-driven**; fixtures must set `rumor_realism` overrides when testing edge shapes.
- Evaluator axes are **heuristic summaries** for humans and artifacts; they are not a second gate.
