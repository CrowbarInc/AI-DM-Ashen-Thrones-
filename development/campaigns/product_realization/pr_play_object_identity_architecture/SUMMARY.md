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
