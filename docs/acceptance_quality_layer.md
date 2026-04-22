# Acceptance Quality layer (Objective N4)

Maintainer-facing contract for **Objective N4**: a **runtime quality-floor** seam adjacent to the
live gate stack. This document describes intent and ownership; executable policy lives in
`game/acceptance_quality.py`. **Gate wiring:** `game.final_emission_gate.apply_final_emission_gate`
invokes the single orchestration entrypoint `validate_and_repair_acceptance_quality` after C4
`narrative_mode_output` assessment (and visibility / referent passes where applicable), merges the
returned trace into `_final_emission_meta`, and never re-implements validate/repair/revalidate
locally. N4 defaults **on** only when `prompt_context.narrative_plan` is present on the emission
dict (the shipped bundle seam); without that slice the contract resolves with `enabled: false` so
narrow harnesses stay unchanged until a plan is attached. With a plan present, optional
`acceptance_quality_contract.enabled: false` disables the floor while leaving other plan slices
unchanged. Unknown `trailer_phrase_patterns_version`
values on shipped overrides are **not** coerced to v1 at the gate: they reach the validator, which
records `trailer_phrase_patterns_version_unresolved` in evidence when no pattern table exists for that
version.

---

## Ownership

| Concern | Canonical owner |
| --- | --- |
| N4 contract resolution (deterministic, JSON-shaped policy) | `game.acceptance_quality.build_acceptance_quality_contract` |
| Pure validation (candidate text + contract in → verdict out) | `game.acceptance_quality.validate_acceptance_quality` |
| Bounded subtractive repairs (non-inventive) | `game.acceptance_quality.repair_acceptance_quality_minimal` |
| Compact trace slices for FEM packaging | `game.acceptance_quality.build_acceptance_quality_emission_trace` |
| Validate + bounded repair + re-validate + trace (canonical single call) | `game.acceptance_quality.validate_and_repair_acceptance_quality` |
| Stack ordering, FEM merge, deterministic replace on persistent N4 fail | `game.final_emission_gate.apply_final_emission_gate` |

After a hard replace, FEM reflects the **actually emitted** deterministic fallback (including
`final_route`, `final_emitted_source`, and the second N4 trace from re-running the canonical seam on
that line)—not a pretend pass on the rejected candidate.

---

## Non-goals (hard)

- **Not a second playability evaluator** — Offline harnesses (`game.playability_eval`, runners) stay
  read-only; N4 does not import them or mirror numeric axis judgments into live enforcement.
- **No LLM judging** — All checks are deterministic patterns, counts, and span rules.
- **No freeform subjective scoring** — No “vibes,” no 0–10 quality tiers at the gate for N4.
- **No boundary completion prose** — Repairs may only normalize whitespace or drop a terminal
  sentence when policy allows; they must not author new diegetic claims.
- **Not Narrative Authenticity (NA)** — NA continues to own anti-echo, low-signal filler, adjacent
  reuse, follow-up stagnation / response-delta shadow reads, and related repairs where documented.
  N4 targets **anti-collapse / floor** failures called out for this objective.

---

## Placement in the pipeline (conceptual)

Forward order remains `engine → planner → gpt → gate → (offline) evaluator`. N4 is a **gate-phase
floor** on **post–narrative-mode-output** candidate text: it runs after shipped C4 output legality
has been assessed (and after visibility on non–strict-social accept paths), still before interaction
continuity validation attachment and `_finalize_emission_output`. It must **not** read evaluator
artifacts or write engine truth.

---

## Relation to Narrative Authenticity (NA)

NA enforces **signal density, echo avoidance, and diegetic shape** within its shipped contract. N4
is **orthogonal**: it asks whether the text still offers a **playable floor**—multiple grounding
signal families, non-collapsed anchors in the closing span, a terminal that is not purely
abstract mood, and not a “plot trailer” stinger—using a **separate** narrow ruleset. Prefer
**presence of signal families** over fuzzy richness scoring.

---

## Relation to the playability evaluator

The playability evaluator remains **offline-only**, consuming transcripts and telemetry. N4, when
enforced live, is **legality-shaped pass/fail** on explicit reason codes, not numeric regression of
playability scores. Evaluator output must never feed gate pass/fail (see
`docs/validation_layer_separation.md`).

---

## Example pass / fail sketches

**Fail — thin grounding floor** — “Yes.” or “They agree.” with no second grounding family across
the full candidate when `require_grounding_floor` is on and `minimum_grounding_signals` is not met.

**Fail — single-anchor collapse** — Many tokens in the tail window repeat one salient content word
with too few distinct anchors (deterministic token share / distinct-count rules).

**Fail — abstract-only terminal** — Last sentence matches a bundled abstract-only template (e.g.
tension / situation hand-wave) **and** that terminal span matches **zero** concrete grounding
families.

**Fail — plot-trailer terminal** — Terminal span hits a bundled trailer idiom table (versioned by
`trailer_phrase_patterns_version`).

**Pass** — Short but concrete: two or more grounding families present, terminal not abstract-only,
no trailer hit, anchors not collapsed per thresholds.

**Repair (bounded)** — With `allow_terminal_sentence_drop_repair`, a trailer/abstract-only failure
may drop the **last sentence** when at least one prior sentence remains; caller must re-run
`validate_acceptance_quality`.

---

## Why this is runtime legality / quality-floor — not scoring

The gate’s job is **orchestrated legality**: explicit booleans, bounded repairs, and stable reason
codes. N4 adds **floor checks** that are still **deterministic predicates**—they are not a
latent-space “quality model.” Numeric or axis **scoring** belongs in offline evaluator artifacts
only; mixing scoring into live enforcement would violate the five-layer separation.

---

## Versioning

`ACCEPTANCE_QUALITY_VERSION` in `game/acceptance_quality.py` bumps when the **default** resolved
contract semantics change in a breaking way for tests or operators. Pattern tables use
`trailer_phrase_patterns_version` (and future siblings) so harnesses can pin pattern sets without
forking the whole module.
