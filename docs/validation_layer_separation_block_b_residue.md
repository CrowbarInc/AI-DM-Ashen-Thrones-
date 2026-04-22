# Block B residue (Objective #11)

Maintainer inventory of **compatibility-shaped** seams left intentionally stable across Blocks A–D. This file is a **checklist**, not an alternate registry: canonical ownership remains `game/validation_layer_contracts.py` and `docs/validation_layer_separation.md`.

---

## Classification

| Item | Class | Notes |
|------|-------|-------|
| Gate module split (`final_emission_gate` / `repairs` / `validators` [+ `meta` at packaging]) | **Still tolerated** | One canonical **gate** layer; multiple files are a benign within-layer split. |
| NA shadow read of `validate_response_delta` | **Still tolerated** | Diagnostic only; canonical pass/fail and `response_delta_*` meta remain gate-owned. |
| Numeric heuristics inside NA (`generic_filler_score`, overlap ratios, …) | **Still tolerated** | In-validator **diagnostics**, not offline evaluator axes and not gate “scoring.” |
| Evaluator entrypoint name `evaluate_narrative_authenticity` in `narrative_authenticity_eval` | **Still tolerated** | Offline module naming; live stack must not import it for legality. |

**Resolved and removable:** none at Block D — all rows above still describe live behavior; removing a bullet without a code change would mis-document the tree.

**Promoted summary:** the high-signal residue bullets also appear (compact) under **Fenced tolerated residue** in `docs/validation_layer_separation.md`.

The following lines use the `- **Title:**` shape so `tools/validation_layer_audit.py` can extract stable themes (keep this block in sync with the sections below):

- **Module split under the gate:** `final_emission_gate`, `final_emission_repairs`, and `final_emission_validators` remain separate files but one canonical **gate** layer; imports are not duplicate ownership.
- **NA shadow read:** When `response_delta` is active, NA may re-run the `validate_response_delta` predicate for diagnostics only; shadow outcomes are non-authoritative; canonical `response_delta_*` meta stays gate-owned.
- **Numeric heuristics inside NA:** Metrics such as `generic_filler_score` and overlap ratios are **diagnostic** in the NA validator, not evaluator artifacts and not gate scoring enforcement; offline `narrative_authenticity_eval` remains the harness for axis scores.
- **Evaluator module name:** `evaluate_narrative_authenticity` lives in `game.narrative_authenticity_eval` (offline); the live stack does not import it for legality.

---

## Tolerated items (non-authoritative detail)

### Gate layer split across multiple files

- Non-owning / non-authoritative — file boundaries do **not** create a second legality layer; orchestration and repair wiring remain the single **gate** phase.
- Would become a real violation if — different files imported **evaluator** modules for live enforcement, or one file claimed exclusive **scoring** enforcement while another claimed **legality** for the same concern without a single orchestration owner.

### NA shadow read of the delta predicate

- Non-owning / non-authoritative — shadow outcomes must not replace gate-written `response_delta_*` metadata or primary delta repair.
- Would become a real violation if — NA imported `final_emission_gate` / `final_emission_repairs` for orchestration, wrote canonical `response_delta_*` keys as legality (not labeled shadow/diagnostic), or caused evaluator-style retries driven by NA scores.

### Numeric heuristics inside NA

- Non-owning / non-authoritative — metrics support trace/debug and NA’s own checks; they are **not** the offline harness scores in `narrative_authenticity_eval`.
- Would become a real violation if — those numbers were used as live pass/fail **quality ranks** in the gate, or were documented as the canonical **evaluator** artifact for the same obligation.

### Evaluator module naming (`narrative_authenticity_eval`)

- Non-owning / non-authoritative — the name reflects offline tooling; it does not grant live enforcement rights.
- Would become a real violation if — `game.api`, `final_emission_gate`, or any live orchestration path imported `narrative_authenticity_eval` (or called `evaluate_narrative_authenticity`) to steer legality, repairs, or retries.
