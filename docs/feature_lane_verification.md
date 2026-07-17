# Feature-Lane Verification Guide

This guide helps contributors choose the smallest safe verification lane for a change.
It does not add governance, change runtime behavior, or replace canonical owners.

Use it before implementation when a change touches more than one file, contract, test
area, projection, replay surface, generated artifact, or governance document.

## Preservation Rules

- Start with the canonical owner. Adapters, projections, tests, docs, and UI-facing
  views consume or translate owner decisions; they do not become the authority.
- Extend direct-owner tests for semantic invariants before adding downstream smoke.
- Keep runtime diagnostic projection separate from protected replay acceptance.
- Treat provenance as evidence explaining behavior, not as behavior selection.
- Keep Final Emission as the last-mile legality, sealing, selection, packaging, and
  traceability boundary.
- Keep validators and repairs separate: validators predicate, repairs mutate only
  within bounded authority and with evidence.
- Do not retire compatibility without caller evidence, replay/provenance review, and
  focused governance checks.

## Lane Overview

| Change Lane | Canonical Owner Category | Contract / Registry Surfaces | Replay / Provenance Consideration | Test Layer | Governance | Documentation |
|---|---|---|---|---|---|---|
| Ordinary gameplay feature | Domain owner plus `game.api` for transaction order | State authority, domain result models, CTIR when resolved-turn meaning changes | Usually runtime trace only; protected replay only if protected behavior changes | Domain direct-owner tests, API/pipeline smoke when wiring changes | State/test ownership if new domain or suite | Domain docs only when contract or workflow changes |
| Final Emission change | Gate, metadata, validator, repair, sanitizer owner as applicable | Boundary taxonomy, FEM metadata helpers, validator/repair contracts | Check FEM metadata, runtime lineage, protected replay only if promoted | Final Emission direct-owner tests; orchestration tests for order only | Gate/final-emission boundary governance if boundary changes | Gate cleanup/closeout docs only for policy changes |
| Protected replay change | Protected replay acceptance owner | `PROTECTED_OBSERVATION_FIELDS`, extraction registry, manifest/projection helpers | Central concern; never feed protected acceptance back into runtime | Projection registry, manifest parity, protected replay tests | Replay boundary governance | Protected replay manifest/generated sections |
| Provenance change | Runtime provenance owner | Fallback family registry, provenance helpers, FEM/runtime lineage fields | Provenance explains behavior; it must not select behavior | Realization provenance, FEM metadata, runtime projection tests | Replay boundary if observed by protected replay | Provenance/fallback docs when vocabulary changes |
| Backend contract work | Backend contract owner; model routing remains distinct | Backend id/version/provider/capability/request/response/error contract | Backend identity may later feed provenance; do not add provider behavior yet | Backend contract tests, existing model-routing tests | Guard against provider logic spreading | Backend decision record or contract doc |
| Ruleset contract work | Ruleset contract owner plus domain mechanics owners | Ruleset id/version/family/capabilities/state and CTIR compatibility | Ruleset identity may later feed save/replay/provenance | Ruleset contract tests, domain/CTIR identity tests when applicable | Guard against ruleset conditionals in prompt, Final Emission, or replay | Ruleset decision record or contract doc |
| Compatibility work | Current compatibility owner/support surface | Existing alias, shim, old payload, or legacy vocabulary contract | Must prove no replay/provenance loss before retirement | Caller/import tests, negative legacy tests, focused direct-owner tests | Compatibility import and replay governance when applicable | Compatibility register and retirement closeout |
| Governance change | Governance doc/test/tool owner | Ownership ledger, test inventory, validation registry, split-owner matrix, CI inventory | Usually observational; must not become runtime behavior | Focused governance tests or tool smoke | Central concern; preserve hard-fail/advisory/deferred status | Governance docs and command pointers |
| Documentation / generated artifact change | Documentation owner or executable registry owner | Source registry for generated sections; handcrafted docs for doctrine | Do not reclassify replay/provenance authority in docs alone | Doc parity checks if existing; no new tests by default | Preserve existing governance status | Mark generated source and refresh command |

## Lane Checklists

### Ordinary Gameplay Feature

- Identify the domain owner and whether `game.api` orchestration changes.
- Check state authority if a new state domain, read path, or write path is involved.
- Check CTIR only if resolved-turn meaning changes.
- Add direct-owner domain tests first.
- Add API/pipeline smoke only for transaction wiring.
- Add replay/provenance coverage only when protected or evidence-bearing behavior changes.

### Final Emission Change

- Identify whether the change belongs to gate orchestration, metadata packaging,
  validators, repairs, sanitizer, or runtime lineage.
- Classify any boundary mutation through the final-emission boundary taxonomy.
- Keep semantic repair upstream or fenced as disallowed at the boundary.
- Add direct-owner tests for semantics and orchestration tests only for ordering/wiring.
- Update runtime lineage or protected replay only when the field meaning requires it.

### Protected Replay Change

- Confirm the field or behavior is protected acceptance, not diagnostic-only.
- Update protected field/extraction/manifest surfaces together.
- Keep runtime code independent from protected replay helpers.
- Run projection, manifest, protected replay, and replay-boundary governance checks.
- Document the field as protected acceptance.

### Provenance Change

- Identify the producer of the evidence and the owner of the vocabulary.
- Stamp through provenance helpers instead of ad hoc literals where helpers exist.
- Preserve distinct fallback/provenance vocabularies unless a consumer inventory proves
  a safe change.
- Add direct-owner provenance tests before dashboard or replay consumers.
- Keep provenance out of behavior selection.

### Backend Contract Work

- Publish contract shape before provider expansion.
- Keep model routing separate from backend/provider identity.
- Do not add provider branches to existing realization code as part of contract work.
- Verify required fields and normalized errors/capabilities.
- Add drift guards only if the package explicitly includes governance updates.

### Ruleset Contract Work

- Publish identity/capability contract before alternate ruleset behavior.
- Keep mechanics in domain/ruleset owners.
- Keep CTIR, prompt, Final Emission, persistence, and replay as consumers or observers.
- Verify required identity and compatibility fields.
- Do not scatter ruleset conditionals through prompt, Final Emission, or replay.

### Compatibility Work

- Start from the [Compatibility-Residue Register](compatibility_residue_register.md).
- Look up or create compatibility-register evidence before changing behavior.
- Gather fresh caller/import evidence.
- Check replay, provenance, dashboard, classifier, and generated artifact consumers.
- Preserve compatibility until retirement evidence is complete.
- Produce a closeout for any approved retirement package.

### Governance Change

- State the failure prevented.
- Choose the focused governance owner; avoid placing unrelated checks in registry
  identity files.
- Preserve existing hard-fail, informational, and deferred meanings unless a package
  explicitly changes them.
- Keep governance out of runtime behavior.
- Provide clear corrective action in any new or changed check.

### Documentation / Generated Artifact Change

- Decide whether the doc is doctrine, workflow, executable-contract summary,
  generated artifact, advisory evidence, or historical record.
- Link to executable truth instead of manually restating it when possible.
- Mark generated sections with source and refresh command.
- Do not rewrite historical campaign records as part of current workflow cleanup.

## Reviewer Checklist

- Does the change identify one primary canonical owner?
- Are adapters and projections limited to translation or observation?
- Are direct-owner tests used for semantic assertions?
- Are downstream tests limited to wiring, smoke, or observation?
- Is protected replay touched only for protected acceptance behavior?
- Does provenance remain evidence-only?
- Are Final Emission mutation kinds classified when boundary behavior changes?
- Is compatibility preserved unless retirement evidence is complete?
- Are governance docs/checks preserving current authority and enforcement status?
- Are generated artifacts updated only from their executable source?

## Stop Conditions

Stop and return to package planning if a change requires any of the following but the
current package did not approve it:

- production code changes;
- replay schema changes;
- Final Emission taxonomy changes;
- backend or ruleset contract publication;
- compatibility retirement;
- new builders or fixtures;
- governance automation;
- generated artifact regeneration;
- moving authority between owners.
