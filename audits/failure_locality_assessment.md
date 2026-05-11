# Failure Locality Assessment

## What Is Already Good?

- Golden replay now has compact deterministic scenarios and a helper layer that projects route, speaker, FEM, fallback, response-type, scaffold leakage, and trace fields into one row.
- Drift taxonomy already exists: `exact_drift`, `structural_drift`, `semantic_drift`.
- Dotted-path assertions make nested trace failures readable and dashboard-friendly.
- FEM is a strong final-emission observability substrate. `final_emitted_source`, response-type repair fields, fallback family, opening fallback metadata, and `post_gate_mutation_detected` are already present.
- Scenario-spine evaluation has structured failures/warnings and metadata completeness checks.
- Route traceability is decent through `canonical_entry`, `canonical_entry_reason`, and `social_contract_trace`.
- Speaker ownership is better than average: speaker contract, final reply owner, emitted speaker signature, and enforcement metadata are all explicit surfaces.
- Validation-layer separation is documented in `game/validation_layer_contracts.py`; evaluator surfaces are mostly read-only/advisory.
- Stage-diff telemetry gives compare-ready before/after snapshots without becoming an engine truth store.

## What Currently Destroys Locality?

- Late-stage repair in `game/final_emission_gate.py` can make upstream failures appear as emission text drift.
- The final emission stack has many sublayers; `post_gate_mutation_detected` says mutation happened, but not always which sublayer caused the final visible delta.
- Sanitizer rewriting/recovery can replace visible text after planning, which may erase evidence of the upstream candidate.
- Fallback substitution can happen upstream-prepared, strict-social, gate-local, sanitizer-local, or terminal fallback paths. FEM helps, but the owner is not always deterministic from final text alone.
- Missing route metadata is currently represented as replay `unavailable`, which is useful but owner-ambiguous unless raw payload/debug trace is inspected.
- Text-derived state updates after GM output can shift later routing/speaker outcomes, making the next turn look like a route failure when the prior turn mutated addressability/state.
- Normalization/adaptation can hide malformed legacy input if the dashboard only consumes normalized output.

## What Most Threatens <=2 Minute Classification?

- Ambiguous late mutation in final emission gate.
- Missing or unprojected route/social contract trace.
- Fallback source split across upstream-prepared, gate compatibility, strict-social, sanitizer, and terminal safe fallback paths.
- Sanitizer mode/changed-count not consistently projected in golden rows.
- Evaluator failures that describe symptoms but do not map to runtime owner without structural replay fields.

## Which Layers Are Still Ambiguous?

- Final emission repair sublayers: validator cause vs repair effect vs semantic mutation.
- Sanitizer vs emission: whether internal leakage means sanitizer failed, was bypassed, or received unrecoverable text.
- Projection vs route: when route metadata is absent from replay row.
- Fallback vs emission: when gate selects a fallback authored by an upstream/prepared fallback system.
- Continuity vs route vs speaker: active target, canonical target, and emitted speaker can disagree in different ways.

## Which Systems Appear Ownership-Clean?

- Golden replay helper: clearly test/replay projection and drift classification.
- FEM read/write/normalization helpers: central metadata lane with documented raw vs normalized surfaces.
- Scenario-spine evaluator: offline evaluator, not live policy.
- Schema contracts: deterministic normalize/validate/adapt functions with stable reason codes.
- State authority: explicit domain owner and mutation guard registry.
- Dialogue social plan: structural-only plan with validation and alias provenance.

## Which Systems Still Violate or Strain Separation of Concerns?

- Final emission gate remains a necessary but overloaded orchestration point for validation, repair, fallback selection, semantic mutation, speaker enforcement, metadata stamping, and final packaging.
- Output sanitizer creates context-aware fallback text and imports strict-social emission helpers; practical, but cross-layer.
- Some repair modules still do semantic boundary work that architecture docs already identify as transitional debt.
- Text-derived post-GM state updates can feed future route/speaker behavior.
- Evaluator observability bundling is read-only today, but future dashboard logic must avoid back-propagating evaluator classifications into live legality.

## Top 5 Blockers To Deterministic Failure Locality

1. No canonical dashboard owner-map yet: drift fields do not automatically map to primary/secondary owner.
2. Final emission sublayer attribution is not granular enough for every text mutation.
3. Route/projection ambiguity when `route_kind` or `social_contract_trace` is unavailable.
4. Fallback provenance is rich but split across several families and selection points.
5. Sanitizer leakage/rewriting lacks a consistently projected run summary in replay rows.

## Recommended Hook Locations For Implementation Phase

- Classification should live beside replay tooling first: `tests/helpers/golden_replay.py` or a new test-only helper, consuming existing rows.
- Runtime owner taxonomy should be a small data map, not embedded in gate logic.
- Dashboard rows should read raw FEM through `read_final_emission_meta_from_turn_payload` and normalized observability through `normalize_final_emission_meta_for_observability`.
- Route/speaker hooks should consume `trace.canonical_entry` and `turn_trace.social_contract_trace`, not re-resolve routing.
- Stage-diff should be used as supporting evidence for mutation boundaries, not as a second truth source.
