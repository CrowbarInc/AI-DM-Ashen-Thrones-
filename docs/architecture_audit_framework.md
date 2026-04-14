# Architecture Audit Framework

This audit is an operator-facing durability check for the repo's deterministic integrity stack. It asks whether ownership, coupling, documentation, and tests make structural change cheap and safe, or whether the stack only appears coherent until a refactor lands.

## Audit Dimensions

### Ownership clarity

- Green: one file or module family is the clearly documented owner, and nearby docs/tests agree.
- Yellow: an owner is implied, but neighboring modules still share language or partial responsibilities.
- Red: multiple modules appear to co-own the same rule, or no owner is documented.
- Repo example: `game/final_emission_gate.py` is explicitly documented as the orchestration owner, while `game/final_emission_validators.py` and `game/final_emission_repairs.py` are split into pure validation and deterministic repair roles.
- Why it matters: deterministic stacks fail when a rule can be changed in two places and still look "correct" locally.

### Overlap / duplicate enforcement

- Green: docs and tests identify a canonical owner and allow only thin smoke overlap.
- Yellow: overlap is acknowledged, but duplicated assertions or helpers still spread across neighboring files.
- Red: multiple suites or modules enforce the same invariant as peers.
- Repo example: `tests/test_prompt_and_guard.py` and `tests/test_output_sanitizer.py` already document a pre-generation vs post-GM boundary, but they remain a hotspot for duplicate phrase-locking risk.
- Why it matters: duplicate enforcement makes deterministic behavior expensive to change and hard to reason about.

### Extension ease

- Green: adding a new rule extends an obvious owner with limited imports and bounded helper sprawl.
- Yellow: extension is possible, but requires touching several cross-cutting files.
- Red: adding one rule likely forces edits across orchestration, compatibility, telemetry, and tests without a stable seam.
- Repo example: `game/stage_diff_telemetry.py` reuses `game.turn_packet.get_turn_packet()` instead of inventing a parallel state accessor, which lowers extension cost for observability.
- Why it matters: deterministic systems stay healthy when new constraints slot into existing seams instead of creating parallel stacks.

### Removal clarity

- Green: dead code can be removed with a small dependency surface and clear downstream ownership.
- Yellow: removal is possible, but compatibility notes, historical imports, or broad fan-in require caution.
- Red: historical behavior, private helper imports, or mixed ownership make safe removal unclear.
- Repo example: the narrative integrity docs explicitly warn that historical tests may still import private helpers from `final_emission_gate`, which raises removal risk even after extraction.
- Why it matters: a resilient integrity stack can shed obsolete layers without hidden breakage.

### Cost visibility

- Green: docs, telemetry, and artifact tooling make structural complexity visible before a change lands.
- Yellow: some cost signals exist, but not all subsystem boundaries expose their change surface clearly.
- Red: the repo gives little visibility into which modules, tests, or docs a structural change will disturb.
- Repo example: `game/narrative_authenticity.py`, `game/final_emission_meta.py`, and `game/stage_diff_telemetry.py` show active work to keep telemetry and meta shapes explicit rather than implicit.
- Why it matters: deterministic stacks depend on cheap inspection, not gut feel.

### Test alignment

- Green: tests name a canonical home for the invariant, and documentation explains why.
- Yellow: tests exist, but ownership is broad or scattered.
- Red: runtime ownership exists without a matching test home, or tests compete as equal owners.
- Repo example: `tests/TEST_AUDIT.md`, `tests/TEST_CONSOLIDATION_PLAN.md`, and `tools/test_audit.py` form an explicit inventory layer for canonical owners, overlap hotspots, and suite archaeology.
- Why it matters: deterministic integrity is only durable when test structure matches code structure.

### Historical residue / archaeology risk

- Green: old deferrals and compatibility notes are rare, explicit, and easy to isolate.
- Yellow: the repo carries some deferred extractions or historical compatibility shims, but they are documented.
- Red: "legacy", "historical", "compatibility", or deferred ownership notes are common enough that new work risks stepping into fossilized behavior.
- Repo example: `docs/current_focus.md` and `docs/narrative_integrity_architecture.md` deliberately mark deferred extraction areas like authoritative social target resolution and large policy clusters in `final_emission_gate.py`.
- Why it matters: archaeology risk is where deterministic systems quietly turn into foundations of sand.

## Non-Goals

- This audit does not prove code quality.
- This audit does not prove game quality.
- This audit does not replace playtesting.
- This audit is about structural resilience and change economics.
