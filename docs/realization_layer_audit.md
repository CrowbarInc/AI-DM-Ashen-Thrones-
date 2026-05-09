# Realization Layer Audit

`tools/realization_layer_audit.py` is an advisory static scanner for Narrative
Realization / Prompt Realization semantic reconstruction risk.

It looks at likely realization-layer files such as prompt construction, GPT calls,
retry fallback, final emission, upstream repairs, and diegetic fallback renderers.
The goal is to find places that may be acting like a second Planner by inferring
semantics, reconstructing missing truth, inventing fallback facts, composing prose
from raw state, or repairing missing narrative obligations after planning.

## How to run

From the repo root:

```bash
python tools/realization_layer_audit.py
```

The tool prints a console summary and writes:

- `artifacts/realization_layer_audit/realization_layer_audit.json`
- `artifacts/realization_layer_audit/realization_layer_audit.md`

## Severity meanings

- `HIGH`: A suspicious fallback, emergency, repair, invention, reconstruction, or
  synthesis term appears near player-facing prose, final emission, GPT output,
  retry fallback, or raw-state language. Read the hunk first; this is not proof.
- `REVIEW`: Semantic reconstruction language appears in a prompt/GPT/Gate layer
  but is not clearly player-facing.
- `INFO`: Usually comments, docs, constants, or benign references that are useful
  context but not immediate refactor targets.

## Why findings are not failures yet

This audit is intentionally not CI-enforced. The scanner is lexical and advisory,
so it will find comments, historical notes, intentionally named contracts, and
other benign references. A finding means "inspect this seam", not "the code is
wrong".

That makes the report useful before enforcement exists: it creates a focused map
of suspicious seams without forcing broad runtime rewrites or brittle zero-finding
assertions.

## Future refactor support

The report helps target fallback/prose ownership work by showing where realization
layers mention reconstruction, repair, fallback authorship, raw state, or GPT output
in close proximity. Future blocks can retire or reclassify those seams one at a time
instead of refactoring prompt construction, retry, and gate behavior broadly.

## Relationship to `game.realization_authority`

`game.realization_authority` is the canonical ledger for which layers may realize,
package, validate, select prepared text, or apply sealed terminal fallback. This
audit imports only that lightweight ledger and includes its authority profiles and
fallback classifications in the generated report.

Interpret audit findings alongside that ledger. For example, a legacy fallback
renderer may produce findings because it is classified as `LEGACY`, while a
Planner-backed prepared emission may be expected but still needs provenance
metadata.
