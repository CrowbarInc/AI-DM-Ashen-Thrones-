# 05 — Authority Preservation

- Pending intention: eligible pending/clarification records are copied with revised_text and pending status, with no executable proposal. Status and scene checks are unchanged; stale scenes retain the no-pending safeguard.
- Executed action: existing refusal remains; tests assert unchanged input records and no context update. Frozen executed-action holdout still passes without social resolution or world mutation.
- World ownership: only entry selection changed. No resolver, bridge, world writer, validator, gameplay permission or state owner changed. API tests preserve world, active scene and character plus gameplay session fields, inventory/clocks/scene/turn and pending/executed records. Normal delivered-history and save metadata writes remain allowed.
- No fabrication: explicit revision without pending state returns the existing clarification and no context update. Ambiguous/conversational corrections emit no intention update and do not clear unrelated pending context.
- Disclosure: public-evidence selection and existing addressee/disclosure owners are unchanged. New API assertions do not reveal a hidden maker's mark; existing disclosure/provenance suites pass. This is scoped regression evidence, not a proof over every possible provider output.
- Existing authorization holdouts: all 28 pass. Existing PR-EG referent failures remain unchanged and separate; no witness or bind predicate was relaxed to obtain green results.

Baseline/fixture/experiment preservation: 3,564 files hashed before repair; zero missing or changed on final check. baseline_hashes.json and preservation_check.json retain details. Protected scopes include ATGB definitions, frozen capture/assessment artifacts, tests/fixtures, PR-EG-R6-R5 evidence and experimental candidates. No authority was granted to the model; no experimental candidate was merged.
