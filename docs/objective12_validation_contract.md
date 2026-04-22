# Objective #12 — Validation coverage contract and registry

**Scope:** governance and tooling only. This objective does **not** add a new runtime gameplay layer, a second scoring pipeline, or policy scattered across ad-hoc JSON blobs. It consolidates **ownership clarity**: one canonical place to answer *“What behavioral validation is required for this feature?”*

**Artifacts:**

- This contract — rules, vocabulary, and non-duplication guarantees.
- Machine-readable registry — `tests/validation_coverage_registry.py` (importable; validated by pytest).

---

## Branch posture (alignment)

- **Consolidation:** reduce ambiguous overlap between suites; prefer one **canonical owner** per feature/domain and explicit **smoke overlap** only where harness depth differs materially.
- **Ownership clarity:** registry entries name an `owner_domain` and point at existing tests, tools, or scenario IDs — they do not invent new authorities.
- **No new runtime architecture layer:** nothing here changes `game/` execution paths or player-facing behavior.
- **No policy by scattered JSON blobs:** coverage intent lives in the registry module (and this doc), not in unrelated data files.

---

## What counts as a “feature/domain” entry

A registry row describes a **coherent product or engineering concern** (a feature, seam, or responsibility slice) whose correctness is defended by **one or more validation surfaces**. It is **not** a pytest file listing, a marker inventory, or a duplicate of evaluator internals.

**Minimum conceptual bar:**

- Identifiable **user- or operator-visible risk** (wrong narration, wrong state, broken contract, regressions in a named scenario), **or**
- A **structural responsibility** (for example, a validation-layer contract) that must stay stable across refactors.

Each entry is **declarative**: it records *which existing harnesses* must stay green for that concern, not *how* evaluators score.

---

## Required fields (registry schema)

Each entry includes:

| Field | Meaning |
|--------|--------|
| `feature_id` | Stable snake_case identifier (must be unique across the whole registry; duplicates are rejected). |
| `title` | Short human title. |
| `owner_domain` | Canonical engineering or product domain owning primary coverage decisions for this feature (non-empty for all rows). |
| `status` | `draft` \| `active` \| `deprecated`. |
| `required_surfaces` | Non-empty set from the **allowed enum** (below); no duplicate members (stored as a set). |
| `transcript_modules` | Tuple of `tests/*.py` module paths for **transcript** regression (empty iff `transcript` is not required). |
| `behavioral_gauntlet_axes` | Tuple of known axis names for **behavioral gauntlet** coverage (empty iff not required). |
| `manual_gauntlets` | Tuple of manual gauntlet IDs (`g1`–`g12`, case-insensitive) for **manual gauntlet** coverage (empty iff not required). |
| `playability_scenarios` | Tuple of allowed **playability smoke** scenario IDs (pytest function names in `tests/test_playability_smoke.py`; empty iff not required). |
| `unit_contract_modules` | Tuple of `tests/*.py` modules for **unit_contract** / fast structural coverage (empty iff not required). |
| `integration_smoke_modules` | Tuple of `tests/*.py` or `tools/*.py` modules for **integration_smoke** (empty iff not required). |
| `notes` | **Explanatory only** — ownership nuance, deferrals, or consolidation context; **not** a machine-checkable substitute for pointer fields. |
| `optional_smoke_overlap` | **Explanatory only** — human-readable list of **other** suites or modules that may touch the same risk when harness depth differs materially; must not introduce duplicate evaluator logic. |

### Satisfying `required_surfaces` (normative)

- If a surface appears in `required_surfaces`, the **corresponding typed tuple field** must be non-empty. This is enforced by `validate_registry()` / `validate_entries()` in `tests/validation_coverage_registry.py` for **every** status.
- **`notes` and `optional_smoke_overlap` do not satisfy surfaces.** They may cite paths for human readers, but validation never treats prose blobs as canonical pointers.
- There is **no “stringly-typed” policy** through long `notes` paragraphs: obligations live in enum members + typed tuples only.
- **Objective #12 does not add a second evaluator** and does not duplicate scoring logic in the registry; typed fields **point** at existing tests, tools, or scenario IDs.

For `ACTIVE` rows, the validator additionally checks (where applicable): duplicate entries within a single pointer tuple, allowlisted manual gauntlet and playability IDs, known behavioral gauntlet axis names, and that declared `tests/` / `tools/` paths exist on disk. Allowlists are minimal constants co-located with the registry module.

**Primary ownership** should be obvious from `owner_domain` plus the smallest sufficient `required_surfaces` set and the pointer tuples that hold **canonical**, machine-validated links.

---

## Allowed validation surface types (`required_surfaces`)

Finite enum (exact spellings for the registry):

| Value | Intent |
|--------|--------|
| `transcript` | Deterministic or transcript-runner regressions; locks multi-turn / export contracts. |
| `behavioral_gauntlet` | Compact deterministic behavioral gauntlet stack (`evaluate_behavioral_gauntlet`, smoke, eval contract). |
| `manual_gauntlet` | Human-scripted passes per `docs/manual_gauntlets.md` and related tooling. |
| `playability` | Live-path playability scenarios; scoring authority remains existing playability evaluators. |
| `unit_contract` | Fast structural / API / invariant tests (including “contract” modules under `tests/`). |
| `integration_smoke` | Broader pytest or tool smoke (`integration_smoke_modules`); not a substitute for other surfaces when those are required — use sparingly and explain rationale in `notes` if helpful. |

A feature **may require one or more** surfaces. Choosing multiple surfaces is normal when risks span deterministic contracts, human feel, and live API behavior.

---

## Canonical ownership (how to declare it)

1. **One primary domain per entry:** `owner_domain` names who decides what “done” means for validation of that feature (for example `narration_visibility`, `emission_gate`, `playability`, `validation_layer`).
2. **Typed pointers, not prose:** canonical ownership is reinforced by **concrete tuple fields** — `transcript_modules`, `behavioral_gauntlet_axes`, `manual_gauntlets`, `playability_scenarios`, `unit_contract_modules`, and `integration_smoke_modules` — that point at **existing** tests, tools, or scenario IDs. Prose in `notes` elaborates; it does not carry enforceable coverage.
3. **Deprecations:** when consolidating, mark superseded rows `deprecated` in the registry and say in `notes` which `feature_id` is canonical — avoid silent duplicate rows with competing claims.

---

## Avoiding duplicate evaluator logic

- **Existing evaluators remain the only scoring authority** for their domains (for example playability scoring, behavioral gauntlet axes, narrative authenticity operators where applicable).
- **This objective does not create a second evaluator** and does not add parallel threshold logic in the registry or in new “coverage” code. The registry and `validate_registry()` only enforce **structural** coverage declarations (IDs, modules, axes), not scores or rubrics.
- Registry entries **reference** tests, tools, and scenario IDs that already call or depend on those evaluators; they do not re-score or reinterpret outputs.
- Tests may assert on **return shapes, reasons, or gates**, but must not fork **numerical / rubric** scoring into a shadow implementation. If a new check is needed, extend the **canonical** evaluator or its approved contract tests — then **point** the registry at that home via the appropriate typed field.

---

## Distinguishing coverage kinds

| Kind | What it is | Typical pointers |
|------|-------------|------------------|
| **Transcript regression** | Deterministic multi-turn sessions, transcript runner, synthetic transcripts — locks contracts and regressions, not prose wording. | `transcript_modules` (and human context in `notes` only). |
| **Behavioral gauntlet** | Deterministic axis-scoped behavior smoke; advisory where attached to manual reports. | `behavioral_gauntlet_axes`, `tests/helpers/behavioral_gauntlet_eval.py`, smoke tests. |
| **Manual gauntlet** | Named scripted human passes; human judgment owns pass/fail. | `manual_gauntlets`, `docs/manual_gauntlets.md`, `tools/run_manual_gauntlet.py`. |
| **Playability** | End-to-end `/api/chat` (or equivalent) behavioral validation with **existing** playability evaluators as sole scoring authority. | `playability_scenarios`, `tests/test_playability_smoke.py`, `tools/run_playability_validation.py`. |
| **Unit / contract tests** | Fast structural, API, or AST contract tests under `tests/`. | `unit_contract_modules`. |
| **Integration smoke** | Broader smoke across pytest or tools. | `integration_smoke_modules`. |
| **Optional smoke overlap** | Same risk touched by another module for **different harness depth** (for example fast unit vs full transcript). | `optional_smoke_overlap` — descriptive; must justify material difference; still **no** duplicate evaluator. |

---

## Smoke overlap rules

- **Allowed** when harness depth **materially** differs (depth, determinism, cost, or fixture scope), and the overlap is **declared** in `optional_smoke_overlap`.
- **Not allowed** as a substitute for missing canonical coverage: if `transcript` is required, a thin `integration_smoke` alone is insufficient. Any time-bounded consolidation exception must still be reflected in `required_surfaces` and the matching typed fields — not only in `notes`.
- Overlap rows must still **forbid evaluator duplication** (see above).

---

## How to use this with consolidation work

1. Add or update a registry row when a feature’s validation story changes.
2. Prefer tightening **ownership** and pointers over adding new suites.
3. Full population of the registry across the codebase is **incremental** (later blocks); early rows should remain **accurate** and `draft` where intent is not yet locked.

---

## Canonical question

**“What behavioral validation is required for this feature?”**  
→ See `tests/validation_coverage_registry.py` for the machine-readable map, and this doc for definitions and rules. For pytest lanes and markers, continue to use `docs/testing.md` and `tests/README_TESTS.md`.
