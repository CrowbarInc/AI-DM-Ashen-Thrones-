# Campaign

Campaign: PR-PLAY — System-Agnostic Object Identity and Manipulation Architecture
Identifier: `pr_play_object_identity_architecture`
Date: 2026-11-09
Generated: 2026-11-09T10:53:32.513535+00:00
Purpose: Bounded implementation-ready architectural design; no production implementation.

# Executive Summary

# PR-PLAY — System-Agnostic Object Identity and Manipulation Architecture

Milestone: `pr_play_object_identity_architecture`. Date: 2026-11-09.
Predecessor: `pr_play_t06_persistent_manipulation` (BLOCKED investigation complete).
Verdict: **A/PASS for the bounded architectural investigation**. No framework has been implemented. Original T06 remains unsupported.

## Decision

Select **Option B: a lightweight common object-instance layer over existing specialized stores**, using Option C's shared validated mutation envelope as its write boundary. B is the selected architecture; C alone is insufficient because a common event cannot identify two identical imported items. Preserve character inventory as the initial persistence host. Do not build a second inventory in the experimental physical ledger, or turn scene templates into campaign-state documents.

Introduce one proposed semantic owner, `game.object_instances`, delegated from existing API resolution staging. It owns identity invariants, validated instance changes and read projections; storage owns bytes. This fills a demonstrated missing owner rather than adding another parser/physical resolver. Existing local interaction, travel, inspection, social and combat owners keep their operations. They share references and normalized receipts, and call the instance owner only for object-state deltas. The experimental physical owner must delegate overlapping writes before it can coexist for a migrated object.

## Findings grounded in current files

- `game/defaults.py:87` stores a Spellbook row with `id`, name, quantity and usable. `game/importers/pf_json_importer.py:70` uses armor slugs and `gear_N`; these are not guaranteed campaign instance identifiers. Weapon attacks are separate mechanics rows, not proof of corresponding possessions.
- `game/referenced_surface.py` is explicitly read-only. Authored interactable IDs are scene-local addresses. The experimental `physical_adjudication._objects` enumerates controlled scene facts/interactables, not carried equipment; `_write_props` stores another physical overlay in session.
- `game/storage.py:285–292` preserves character JSON. Its runtime commit scope supports exception rollback, and snapshots include character/session/world/combat/log. Neither JSON nor a snapshot supplies missing gameplay authority. Character saves currently use a non-atomic JSON writer; local process locks and best-effort rollback are not crash-safe multi-file transactions.
- Acquisition delta projection exists, but `mechanical_claims.py:25` explicitly supports synthetic resolver deltas. A full game-source inventory found no general inventory acquisition/transfer/equip/consume semantic writer. Those are gaps, not existing integration APIs to invent by name.
- T04 already completes transient contact through `local_interaction`; T06 declines before prerequisites/resolver application. A parser synonym patch cannot repair instance, material, mutation and inspection authority.
- `docs/ruleset_contract_registry.md` says the current engine is PF1e-inspired with no pluggable ruleset loader. Portability below is a proposed contract assessment, not current multi-system functionality.

## Contract and scope

Core instance identity is an opaque campaign-scoped ID independent of item definition IDs, with revision and creation provenance. A single authoritative record has one placement; possession, legal ownership and equipment relation have separate meanings. Optional state begins with bounded markings. A sleeve is a stable part selector of clothing, not a new inventory item. Ruleset references and mechanics remain namespaced optional data.

An engine-validated proposal carries target/revision, request identity, operation, evidence-backed preconditions, source content/provenance and adapter decision. Only atomic application of the validated delta produces an applied receipt. Inspection reads current active markings from the same instance, including after reload or transfer. No prose reconstruction or hidden-catalog copying.

Mundane affordances allow bounded use of positively established accessible material without an inventory grant; uncertain material remains unknown. Small nonvaluable incidental details can be proposed only within an explicit campaign policy and must be recorded if subsequently consequential. No weapons, consumables, secrets, combat advantages or quest resources may arise from that policy. Ordinary clothing needs explicit character-context evidence before lazy promotion; the word “sleeve” alone does not create it.

## Validation and limits

All 1,296 predecessor protected source/test/data hashes match entry. An expanded 1,581-file source/tool manifest captures current integrity. Reference baseline remains **405 passed / 20 failed of 425**, predecessor diagnostics **6/6**, physical/persistence controls **93/93**. Fresh preservation: **143 passed / 0 failed / 0 errors / 0 skipped**; exact counts are in `artifacts/pr_play_object_identity_architecture/validation_summary.json`. This cycle does not relabel historical counts as a fresh full baseline. No full suite, live-provider run, gameplay benchmark, successful inscription or held-out portability test is claimed. Negative design controls are conceptual obligations only.

Exactly one next cycle: **`pr_play_object_instance_identity` — Stable Identity for Existing Inventory Singletons**. Add durable IDs/revisions to explicitly migrated existing quantity-one rows; preserve legacy behavior and prove save/reload. Do not activate marking, clothing assumptions, physical routing or any additional ruleset. Later phases implement one marking and inspection before integrating T06. See NEXT_STEP_DECISION.md and IMPLEMENTATION_ROADMAP.md.

Production files changed: **0**. Live provider calls: **0**. No commit/push. All fourteen reports and machine-readable evidence are indexed by INTEGRITY.md and the review manifest.


Objective status: `A/PASS — architecture only`.

# Changes Made

## Production changes

- None (0).

## Validation changes

- No tests/fixtures modified; existing 143-test preservation selection executed.

## Tooling changes

- Cycle-local evidence/validation/seal helpers only.

## Documentation changes

- Fourteen architecture reports; NEXT_SESSION prepended with history preserved.

## Generated artifacts

- Source/evidence inventories, conceptual matrices and standard fresh stable/dated review archives.

# What Was Tested

- **Focused tests:** 143 passed / 0 failed / 0 errors / 0 skipped, provider-free preservation.
- **Broader relevant tests:** 425-test predecessor reference 405/20; 1,296 predecessor hashes identical. Full baseline not rerun.
- **Full suite:** Not run.
- **Runtime validation:** Existing T04/T05/pre-seal/persistence and negative T06 controls only; no implemented marking.
- **Model/runtime boundary:** 0 live provider calls; fail-closed external network and production-data write guards.
- **New regressions:** No failures in selected 143 existing controls; no broader regression claim.
- **Pre-existing failures:** 20 in predecessor 425 selection; unchanged byte provenance, not repaired or freshly rerun.
- **Self-contained bundle review:** Independently reopen stable and dated ZIPs; verify canonical hashes and manifests, all 14 reports, Option B, portability, roadmap, single next milestone and preserved handoff history. Final evidence is archive_verification.json.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Review the Option B architecture and narrow next implementation scope. No approval is required to finish this design/handoff; implementation remains outside this request.

# Known Problems / Unresolved Findings

## Campaign-specific

- Original T06 still unsupported; proposed identity/marking/inspection/adapter contracts unimplemented.
- Existing file-backed rollback is best-effort on exceptions, not crash-atomic or multi-process.

## Pre-existing baseline

- Twenty baseline failures and T01/T02/T07/T08/T10/T12 gameplay limitations remain.

# Missing Concepts / Future Capabilities

- Persistent instance identity, carried-item mutation/inspection, durable operation dedupe and equipment/material binding await phased implementation.

# What This Campaign Does NOT Prove

- Successful original or controlled inscription; transfer/removal/reload of a modified object; implemented alternate rulesets; broad playability; full suite; live-model or benchmark acceptance.

# Recommended Next Step

Exactly one: pr_play_object_instance_identity — Stable Identity for Existing Inventory Singletons. See NEXT_STEP_DECISION.md; do not begin implementation automatically.

# Review Bundle Contents

Bundle file count: `65`
Bundle ZIP size: `000000468217` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/SUMMARY.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/ACTION_OWNERSHIP_MAP.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/ACTION_OWNERSHIP_MAP.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/ACTION_RESOLUTION_CONTRACT.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/ACTION_RESOLUTION_CONTRACT.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/ARCHITECTURE_OPTIONS.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/ARCHITECTURE_OPTIONS.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/CORE_RULESET_BOUNDARY.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/CORE_RULESET_BOUNDARY.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/EXISTING_OBJECT_ARCHITECTURE.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/EXISTING_OBJECT_ARCHITECTURE.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/IMPLEMENTATION_ROADMAP.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/IMPLEMENTATION_ROADMAP.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/INTEGRITY.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/INTEGRITY.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/MODIFICATION_CONTRACT.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/MODIFICATION_CONTRACT.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/MUNDANE_AFFORDANCE_POLICY.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/MUNDANE_AFFORDANCE_POLICY.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/NEXT_STEP_DECISION.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/NEXT_STEP_DECISION.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/OBJECT_INSTANCE_CONTRACT.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/OBJECT_INSTANCE_CONTRACT.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/RULESET_PORTABILITY.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/RULESET_PORTABILITY.md`.
- `support/development/campaigns/product_realization/pr_play_object_identity_architecture/T04_T06_INTEGRATION.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_object_identity_architecture/T04_T06_INTEGRATION.md`.
- `support/artifacts/pr_play_object_identity_architecture/acceptance_review.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/acceptance_review.json`.
- `support/artifacts/pr_play_object_identity_architecture/action_owner_references.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/action_owner_references.json`.
- `support/artifacts/pr_play_object_identity_architecture/after_manifest.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/after_manifest.json`.
- `support/artifacts/pr_play_object_identity_architecture/architecture_comparison.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/architecture_comparison.json`.
- `support/artifacts/pr_play_object_identity_architecture/architecture_negative_controls.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/architecture_negative_controls.json`.
- `support/artifacts/pr_play_object_identity_architecture/entry_current_review.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/entry_current_review.md`.
- `support/artifacts/pr_play_object_identity_architecture/entry_git_status.txt`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/entry_git_status.txt`.
- `support/artifacts/pr_play_object_identity_architecture/entry_identity.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/entry_identity.json`.
- `support/artifacts/pr_play_object_identity_architecture/entry_next_session.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/entry_next_session.md`.
- `support/artifacts/pr_play_object_identity_architecture/evidence_manifest.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/evidence_manifest.json`.
- `support/artifacts/pr_play_object_identity_architecture/existing_contract_excerpts.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/existing_contract_excerpts.json`.
- `support/artifacts/pr_play_object_identity_architecture/files_inspected.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/files_inspected.json`.
- `support/artifacts/pr_play_object_identity_architecture/final_git_status.txt`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/final_git_status.txt`.
- `support/artifacts/pr_play_object_identity_architecture/implementation_dependencies.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/implementation_dependencies.json`.
- `support/artifacts/pr_play_object_identity_architecture/investigate.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/investigate.py`.
- `support/artifacts/pr_play_object_identity_architecture/milestone_identity.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/milestone_identity.json`.
- `support/artifacts/pr_play_object_identity_architecture/object_model_references.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/object_model_references.json`.
- `support/artifacts/pr_play_object_identity_architecture/persistence_references.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/persistence_references.json`.
- `support/artifacts/pr_play_object_identity_architecture/prepare_review.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/prepare_review.py`.
- `support/artifacts/pr_play_object_identity_architecture/preservation.log`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/preservation.log`.
- `support/artifacts/pr_play_object_identity_architecture/preservation_junit.xml`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/preservation_junit.xml`.
- `support/artifacts/pr_play_object_identity_architecture/proposed_contract_examples.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/proposed_contract_examples.json`.
- `support/artifacts/pr_play_object_identity_architecture/report_inventory.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/report_inventory.json`.
- `support/artifacts/pr_play_object_identity_architecture/ruleset_portability_matrix.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/ruleset_portability_matrix.json`.
- `support/artifacts/pr_play_object_identity_architecture/seal_review.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/seal_review.py`.
- `support/artifacts/pr_play_object_identity_architecture/source_changes.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/source_changes.json`.
- `support/artifacts/pr_play_object_identity_architecture/source_inventory.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/source_inventory.json`.
- `support/artifacts/pr_play_object_identity_architecture/state_mutation_references.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/state_mutation_references.json`.
- `support/artifacts/pr_play_object_identity_architecture/validate_existing.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/validate_existing.py`.
- `support/artifacts/pr_play_object_identity_architecture/validation_command.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/validation_command.json`.
- `support/artifacts/pr_play_object_identity_architecture/validation_execution.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/validation_execution.json`.
- `support/artifacts/pr_play_object_identity_architecture/validation_summary.json`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `artifacts/pr_play_object_identity_architecture/validation_summary.json`.
- `support/docs/NEXT_SESSION.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/state_authority_model.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `docs/state_authority_model.md`.
- `support/docs/ruleset_contract_registry.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `docs/ruleset_contract_registry.md`.
- `support/docs/review_handoff_standard.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `docs/review_handoff_standard.md`.
- `support/game/storage.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `game/storage.py`.
- `support/game/physical_adjudication.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `game/physical_adjudication.py`.
- `support/game/integrated_play.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `game/integrated_play.py`.
- `support/game/models.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `game/models.py`.
- `support/game/defaults.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `game/defaults.py`.
- `support/game/importers/pf_json_importer.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `game/importers/pf_json_importer.py`.
- `support/game/noncombat_resolution.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `game/noncombat_resolution.py`.
- `support/game/local_interaction.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `game/local_interaction.py`.
- `support/game/player_http_projection.py`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `game/player_http_projection.py`.
- `support/development/campaigns/product_realization/pr_play_t06_persistent_manipulation/SUMMARY.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_t06_persistent_manipulation/SUMMARY.md`.
- `support/development/campaigns/product_realization/pr_play_t06_persistent_manipulation/MANIPULATION_CONTRACT.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_t06_persistent_manipulation/MANIPULATION_CONTRACT.md`.
- `support/development/campaigns/product_realization/pr_play_t06_persistent_manipulation/REGRESSION_RESULTS.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_t06_persistent_manipulation/REGRESSION_RESULTS.md`.
- `support/development/campaigns/product_realization/pr_play_t04_local_action/ACTION_CONTRACT.md`: Explicit evidence for the architecture decision, persistence boundary, portability or integrity. Canonical source: `development/campaigns/product_realization/pr_play_t04_local_action/ACTION_CONTRACT.md`.

## Explicit omissions

- `artifacts/pr_play_object_identity_architecture/before_manifest.json`: duplicate content of artifacts/pr_play_object_identity_architecture/after_manifest.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
