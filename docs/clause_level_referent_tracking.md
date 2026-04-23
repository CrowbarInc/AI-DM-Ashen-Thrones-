# Clause-level referent tracking (Objective N5)

Maintainer-facing contract for **Objective N5**: a **bounded extension** of the existing referent-tracking lane so the stack can carry **clause-level referent metadata** (the optional root field **`clause_referent_plan`**) deterministically. N5 reduces RC/FM-style ambiguity (pronoun anchoring, target continuity, explicit naming pressure) **without** introducing a new semantic authority, prose inference, duplicated planner truth, or overlap with CTIR ownership.

This document is the **design and integration contract** for N5. Runtime wiring (construction in `game/referent_tracking`, strict validation, **`referent_clause_prompt_hints`** projection in `game/prompt_context`, gate read-side consumption) is covered here; focused regressions include `tests/test_referent_tracking_clause_plan.py`, `tests/test_referent_clarity_clause_consumption.py`, and `tests/test_n5_boundary_regressions.py`.

---

## N5 contract (non-negotiable)

### Owner

- **Canonical construction and schema evolution for the referent-tracking artifact** remain owned by `game/referent_tracking.py` (same module as Objective #7 foundation).

### Upstream authority (unchanged)

N5 **does not** compete with or reinterpret:

| Authority | Role relative to N5 |
|-----------|---------------------|
| **CTIR** (`game.ctir`, `game.ctir_runtime`) | Canonical **resolved-turn meaning** for the narration attempt. N5 may consume **bounded identifiers and slices** already present in CTIR-shaped inputs (for example addressed-entity id lists); it must not re-derive turn semantics from CTIR textually or invent parallel “meaning.” |
| **`interaction_context` / interaction continuity** | Authoritative **interaction targeting** and conversational framing. Clause slots that mention “target” or “interlocutor” attach **candidates and flags** derived from these contracts—not from model prose. |
| **`narration_visibility`** | **Visibility constraints** and published entity slices. Every entity id carried in clause rows must remain consistent with visibility rules already enforced at the referent artifact boundary. |

### N5 nature

- **Derivative-only:** Clause rows are projections from already-structured inputs (visibility, speaker selection, interaction contracts, narrative plan rows where they are **structural** carriers, turn packet route fields, bounded CTIR id lists, etc.). No hidden inference graph.
- **Deterministic-only:** Same inputs → same artifact; no randomness, no model calls, no confidence scores from inference.

### Hard prohibitions

1. **No free-prose semantic parsing** — Do not tokenize narration, parse natural language into roles, or classify sentences with NLP. N5 is not a linguistics layer.
2. **No second narrative plan** — `clause_referent_plan` is **not** a parallel `narrative_plan`; it does not author scene beats, obligations, or mode structure. It is referent **metadata** keyed to a small closed set of **clause slots** needed by prompt/gate contracts.
3. **No back-write of state** — The artifact is read-side transport and gate input. It must not mutate `session`, `world_state`, CTIR, or any persistence root (see `docs/state_authority_model.md`).

### Relationship to validation phases

N5 aligns with `docs/validation_layer_separation.md`:

- **Planner (`game.prompt_context`)** may ship bounded read-side slices (including optional **`referent_clause_prompt_hints`** derived from **`clause_referent_plan`**) as **structure**, not as re-resolution of CTIR.
- **Gate (`game.final_emission_repairs` + `game.final_emission_validators`)** may **read** optional **`clause_referent_plan`** rows for legality checks and **bounded subtractive / substitution** repairs already scoped to referent clarity—without becoming a new meaning owner.

---

## Artifact goal (bounded extension)

### Canonical root unchanged

The existing **referent tracking artifact** produced by `build_referent_tracking_artifact` remains the **canonical owner document**: versioned root, `active_entities`, `pronoun_resolution`, `forbidden_or_unresolved_patterns`, `interaction_target_continuity`, etc. Consumers that ignore N5 keep working.

### New bounded substructure (optional)

Add an **optional** root field that carries **per–clause-slot** metadata only:

- **Clause slots** — A small, explicitly enumerated set of slots (for example tied to prompt/gate “beats” or shipped response-shape clauses), **not** arbitrary sentence indices in player text.
- **Subject / object attachment candidates** — Bounded lists of **entity ids** drawn only from visibility-visible ids and the same normalization rules as the rest of the artifact (`normalize_entity_id`).
- **Allowed explicit fallback labels per clause slot** — Narrow allow-list derived from `safe_explicit_fallback_labels` / `allowed_named_references` style rows for **those** candidate ids only (no novel names from prose).
- **Pronoun risk per clause slot** — Closed-set buckets (reuse the existing pronoun bucket vocabulary where applicable, for example `he_him`, `she_her`, `they_them`, `it_its`, `unknown`) attached to **slots**, not inferred spans.
- **Target-switch risk per clause slot** — Boolean or small enum flags derived from structured signals already on the artifact (for example conflicting interaction target signals, drift flags)—**not** from parsing “who switched” in emitted text.

### Explicit non-deliverables

- **No generated prose** in the artifact (no suggested narration strings).
- **No NLP / no model inference.**
- **No arbitrary token parsing** of free text to discover entities or roles.

---

## Strict minimal schema proposal (backward compatible)

### Root

- Keep the artifact **compact** at the root: existing keys remain as today.
- Add one **optional** field:

| Field | Type | Semantics |
|-------|------|-----------|
| `clause_referent_plan` | `list[dict]` \| omitted | When absent, behavior matches pre-N5 consumers. When present, each element is one **clause slot** row. |

### Row shape (JSON-safe, small rows)

Each dict in `clause_referent_plan` should stay **small** and use only **JSON-serializable** atoms. Proposed fields (all optional unless noted for a given implementation phase, but names should stabilize here):

| Key | Type | Notes |
|-----|------|-------|
| `clause_id` | `str` | Stable id within the plan for this slot; derived from structured slot identity (for example enum + ordinal), not from hashing prose. |
| `clause_kind` | `str` | Closed-set label for the slot’s role in prompt/gate (for example `opening_anchor`, `social_reply`, `delta_followup`)—defined in code as constants, not free tags. |
| `subject_candidate_ids` | `list[str]` | Sorted, capped, normalized entity ids from visibility / upstream contracts only. |
| `object_candidate_ids` | `list[str]` | Same constraints as subject. |
| `preferred_subject_id` | `str` \| `null` | Single id when a deterministic preference rule applies; must appear in `subject_candidate_ids` when non-null. |
| `preferred_object_id` | `str` \| `null` | Same for object list. |
| `allowed_explicit_labels` | `list[str]` | Small list of **display strings** already authorized for those candidates (subset of artifact-level safe labels), clipped and deduplicated. |
| `risky_pronoun_buckets` | `list[str]` | Closed set; union or slice of bucket labels relevant to **this slot**’s subject/object candidates. |
| `target_switch_sensitive` | `bool` | True when structured signals indicate this slot is sensitive to interaction-target drift or conflicting targets. |
| `ambiguity_class` | `str` | Slot-local class in a **small closed vocabulary** aligned with or narrowed from artifact-level `referential_ambiguity_class`—never an open-ended NLP label. |

### Id discipline

- All ids are **bounded** (length caps consistent with `normalize_entity_id` / `_MAX_ID_LEN` family).
- All ids are **derived from already-structured inputs only** (visibility lists, CTIR addressed-entity lists, speaker contracts, narrative plan structural ids where applicable, turn_packet route fields). **Never** from scanning emitted or draft prose for names.

### Validation note

`validate_referent_tracking_artifact` allows `clause_referent_plan` under strict mode and validates list depth, row keys, and id membership against the same visibility discipline as the rest of the artifact.

---

## Anti-overengineering (explicit scope ceiling)

Do **not** add as part of N5:

- A **sentence parser** or dependency parse of model output.
- **Token or character span** tracking into narration text.
- A **cross-paragraph coreference graph** or global discourse model.
- Any subsystem that **rewrites full emitted text from scratch** from N5 rows.

Do:

- Emit **only** the bounded clause slots **required** by existing or narrowly added **prompt contracts** and **gate** predicates—enumerated in code, capped in list length.

---

## Integration plan (file-level)

| Concern | Owner module | Role |
|---------|--------------|------|
| **Builder** | `game/referent_tracking.py` | Extend `build_referent_tracking_artifact` (and validation) to populate optional `clause_referent_plan` from structured inputs only; keep deterministic ordering. |
| **Prompt consumer** | `game/prompt_context.py` | Ship trimmed views of clause rows into prompt payloads where contracts require them; **read-only** projection—no CTIR or engine truth mutation. |
| **Bundle transport** | `game/narration_plan_bundle.py` | Continue to attach full `referent_tracking` under `renderer_inputs`; stamp alignment with CTIR remains as today. Optional: mirror compact clause indices into `turn_packet` only if an existing compact pattern requires it (prefer full artifact on prompt_context for gate). |
| **Gate legality / repair consumer** | `game/final_emission_repairs.py` (and `game/final_emission_validators` for predicates) | Extend referent-clarity validation/repair to optionally use per-slot hints (for example choose substitution label compatible with **that** clause slot’s `allowed_explicit_labels`). **Bounded** repairs only—same philosophy as current first-pronoun substitution. |
| **Tests** | `tests/` | New **focused** unit tests for row construction ordering, caps, and visibility membership; integration tests for bundle → prompt_context → gate handoff when wired. No large harness expansion. |

---

## Related documents

- `docs/ctir_prompt_adapter_architecture.md` — CTIR vs planner adapter; N5 stays subordinate to CTIR.
- `docs/validation_layer_separation.md` — Gate vs planner vs engine phases.
- `docs/state_authority_model.md` — No back-write from derived bundles.
- `tests/test_n5_boundary_regressions.py` — Block D boundary regressions (ownership, read-side consumption, repair bounds, omission/compact behavior).
- `game/referent_tracking.py` — Artifact owner.
- `game/prompt_context.py` — Prompt packaging consumer.
- `game/narration_plan_bundle.py` — Bundle assembly and `referent_tracking` transport.
- `game/final_emission_repairs.py` — Referent clarity emission layer (`_apply_referent_clarity_emission_layer`).
