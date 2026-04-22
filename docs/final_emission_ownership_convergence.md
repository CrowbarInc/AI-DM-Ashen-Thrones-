# Final emission — ownership convergence (Objective C2)

Maintainer-facing **classification and ownership target** for everything that mutates or judges **final player-facing text** after the model. This document **does not** change runtime behavior; it inventories current code and states where each concern **should** land after convergence.

**Related:** `docs/narrative_integrity_architecture.md`, `docs/validation_layer_separation.md`, `docs/architecture_ownership_ledger.md`.

---

## C2 goal (Block A)

Produce a **precise inventory** of final-emission transformations that today perform:

1. **Legality enforcement** — deterministic checks, pass/fail reason codes, bounded substitutions that only **remove** illegal surfaces or **restore** visibility-safe phrasing already authorized by upstream artifacts (no new narrative facts).
2. **Formatting / packaging** — whitespace, punctuation hygiene, paragraph or structural packaging, extraction of accidentally serialized payloads into the intended string field, deduplication of identical surface strings, stable metadata attachment.
3. **Semantic mutation** — invention, reconstruction, reordering **for meaning or contract compliance**, summarization **for emphasis**, bridging missing intent, “completing” thin GPT output with new substantive prose, or **cash-out** of narrative authority from resolution/session in ways that are not purely legality-preserving.

**Block A scope:** classification, ownership decisions, and **minimal** scaffolding (sparse `C2_OWNER_AUDIT` anchors in code). No large refactors.

---

## Canonical convergence rule

At the **final emission boundary**, the system may perform **only**:

- **Legality enforcement** (validators + explicitly bounded, policy-linked repairs that do not invent authoritative facts), and  
- **Packaging** (structure of the string the player sees, metadata, stripping of illegal stock/meta/schema leakage).

Final emission **must not**:

- Invent, reconstruct, reorder-for-meaning, summarize-for-meaning, bridge narrative logic, or silently “complete” intended content that upstream layers failed to supply in a **model-authored** surface.

When today’s code does the latter, the **target owner** is upstream (planner structure, validator-orchestrated **pre-final** repair, strict-social emission fallbacks, or CTIR/API resolved-turn packaging) per the migration notes below.

---

## Inventory (function / helper → behavior → classification)

Classification is one of: **legality** | **packaging** | **semantic mutation**.  
Many rows are **legality + packaging** in one pipeline step; the table uses the **dominant** effect on player-visible *meaning*.

### `game/final_emission_validators.py`

| Current function / helper | Current behavior | Classification |
|----------------------------|------------------|----------------|
| `candidate_satisfies_dialogue_contract` | Regex/heuristic checks vs dialogue / route-legal social replacement | legality |
| `candidate_satisfies_answer_contract` | Thin/direct-answer shape checks | legality |
| `candidate_satisfies_action_outcome_contract` | Action-outcome shape checks vs player tokens | legality |
| `validate_answer_completeness` | Contract-driven completeness / front-load violations (no text mutation) | legality |
| `validate_fallback_behavior` | Uncertainty / partial-shape / meta-voice checks | legality |
| `validate_response_delta` | Echo / delta-kind / early-window checks | legality |
| `validate_social_response_structure` | Dialogue cadence / list-like / expository density flags | legality |
| `validate_referent_clarity` | Prompt-artifact-driven referent risk categories (no repair) | legality |
| `_minimal_answer_contract_repair` | **Synthesizes** direct-answer-shaped lines from resolution / adjudication / social emergency | **semantic mutation** |
| `_minimal_action_outcome_contract_repair` + `_to_second_person_action_clause` + `_action_result_summary` | **Builds** second-person action + outcome sentence from player input + resolution | **semantic mutation** |
| `_social_fallback_resolution`, `_npc_display_name_for_emission` (import) | Resolution-shape helpers feeding repairs | packaging (structure only; paired outputs may be semantic elsewhere) |

### `game/final_emission_repairs.py`

| Current function / helper | Current behavior | Classification |
|----------------------------|------------------|----------------|
| `_apply_answer_completeness_layer` / `_repair_answer_completeness_minimal` | **Reorders** sentences (front-load answer, bounded-partial order), **injects** gate phrases, **compresses** pairs for NPC voice | **semantic mutation** (reorder-for-compliance; bridge-like glue) |
| `_apply_response_delta_layer` / `_repair_response_delta_minimal` | **Reorders / trims / compresses** sentences so delta validates (front-load delta, trim echo, swap caveat vs refinement) | **semantic mutation** |
| `apply_spoken_state_refinement_cash_out` | Builds spoken refinement from **session clue/lead** text for answer-pressure | **semantic mutation** (deterministic narrative cash-out; data-grounded but not “packaging only”) |
| `apply_social_response_structure_repair` + `_flatten_list_like_dialogue`, `_collapse_multi_speaker_formatting`, `_merge_substantive_paragraphs`, `_trim_leading_expository_connectors`, `_collapse_soft_line_breaks`, `_reduce_expository_density`, `_normalize_dialogue_cadence`, `_restore_spoken_opening` | Structural dialogue repair: list flattening, paragraph merge, connector trim, density reduction | mixed: **packaging** for format flattening / breaks; **semantic mutation** where density reduction removes or replaces substantive wording |
| `_apply_narrative_authenticity_layer` | NA-scoped deterministic repairs under contract | legality + bounded repair (treat as **legality** lane with narrow mutation; see NA docs) |
| `repair_fallback_behavior` + `_synthesize_*`, `_fallback_*_sentence`, `_rewrite_meta_fallback_as_diegetic_partial`, `_ensure_known_unknown_shape`, `_smooth_repaired_fallback_line`, `_wrap_bare_imperative_lead_for_npc_voice`, `_voice_extracted_next_lead_sentence`, `_append_next_lead_if_allowed`, `_convert_to_single_diegetic_clarifying_question` | **Synthesizes** bounded-partial / clarifying / next-lead / diegetic lines from templates + resolution | **semantic mutation** |
| `_strip_meta_fallback_voice`, `_remove_fabricated_authority`, `_downgrade_overcertain_claims`, `_strip_patterns_from_text` | Removes or softens forbidden **surface** patterns per contract | legality |
| `_apply_referent_clarity_emission_layer` / `_repair_referent_clarity_minimal` | At most one pronoun→explicit-label substitution from **allow-list** | legality (bounded clarity repair; no new entities) |
| `_minimal_*` imports / `_social_fallback_resolution` duplicates | Same as validators column | as above |

### `game/final_emission_gate.py` (orchestration + in-module policy layers)

| Current function / helper | Current behavior | Classification |
|----------------------------|------------------|----------------|
| `apply_final_emission_gate` | Orders validators, repairs, sanitizer, strict-social sealing, meta merges | packaging (orchestration) + invokes other classes |
| `_enforce_response_type_contract` | On failure, swaps in **minimal answer / action / strict-social dialogue** repairs | **semantic mutation** when repair path used |
| `_apply_tone_escalation_layer` / `_repair_tone_escalation_narrow` | Tone contract repairs | **semantic mutation** (voice / intensity rewrite) |
| `_apply_narrative_authority_layer` / `_repair_narrative_authority_narrow` | Removes or replaces NA-marked sentences | **semantic mutation** (authority / outcome framing) |
| `_apply_anti_railroading_layer` / `_apply_single_anti_railroading_repair_pass` / `_repair_head_straight_dest` | Rewrites railroading phrasing | **semantic mutation** (planner-like steering removal with replacement prose) |
| `_apply_context_separation_layer` / `_repair_context_separation_narrow` | Separates player knowledge vs PC knowledge surfaces | legality + bounded rewrite → **semantic mutation** where replacement text is generated |
| `_apply_player_facing_narration_purity_layer` | Removes / replaces non-diegetic or purity violations | mixed: **legality** when stripping; **semantic mutation** when substituting full alternate sentences |
| `_apply_answer_shape_primacy_layer` / `_repair_answer_shape_primacy_leading_pressure` | Moves or trims “pressure” vs payload ordering | **semantic mutation** (compliance reordering) |
| `_apply_scene_state_anchor_layer` / `_repair_scene_state_anchor_minimal` / `_repair_actor_opening` / `_repair_action_tether` / `_repair_location_opening` | Prepends **contract token** anchors (`At …`, actor/action tethers) | **semantic mutation** at surface (rebinds opening meaning using bucketed tokens; not pure whitespace) |
| `_repair_fragmentary_participial_splits` / `_repair_participial_fragment` | Rewrites dangling participial fragments into finite clauses | **semantic mutation** (grammar repair changes reading) |
| `_apply_fast_fallback_neutral_composition_layer` / `_build_fast_fallback_opening_scene_template` | Replaces malformed fast-fallback text with **scene-template** composition | **semantic mutation** |
| `_apply_visibility_enforcement` | Removes or replaces visibility-violating wording per policy | legality (with possible **semantic mutation** when replacement is full sentence stock) |
| `_apply_first_mention_enforcement`, `_apply_referential_clarity_enforcement`, `_apply_speaker_contract_repairs`, `_apply_interaction_continuity_emission_step` | Speaker / continuity / first-mention repairs | mixed: **legality** when drop-only; **semantic mutation** when generating bridge or replacement prose |
| `_apply_referent_clarity_pre_finalize` | Delegates to repairs referent layer | legality |
| `_apply_upstream_fallback_pregate_containment` | Containment of upstream fallback shapes | legality / packaging |

### `game/output_sanitizer.py`

| Current function / helper | Current behavior | Classification |
|----------------------------|------------------|----------------|
| `resembles_serialized_response_payload` / `extract_player_text_from_serialized_payload` / `strip_serialized_payload_fragments` | Detect / extract / strip JSON schema leakage | **packaging** (recovery of intended field) |
| `_strip_internal_prefixes` | Removes `planner:` / `validator:` style prefixes | legality |
| `sanitize_player_facing_output` | Full pipeline: split sentences, classify, rewrite, validate, coherence | **semantic mutation** dominates (diegetic templates, analytical rewrites, fallbacks) |
| `_rewrite_line`, `_rewrite_sentence_atomically`, `_rewrite_instructional_sentence`, `rewrite_analytical_sentence`, `_rewrite_directive_sentence`, `_rewrite_implicit_instruction_sentence`, `_rewrite_identity_system_sentence` | Replace scaffold / analytical / directive / identity lines with **template** or social fallback prose | **semantic mutation** |
| `_diegetic_uncertainty_fallback`, `_simple_diegetic_fallback`, `_SCENE_AMBIGUITY_FALLBACKS`, `_NPC_IGNORANCE_FALLBACKS`, `_PROCEDURAL_INSUFFICIENCY_FALLBACKS` | **Fresh** fallback lines from pools | **semantic mutation** |
| `_split_sentences` + quote/attribution merge helpers | Merges splits for attribution / orphan quotes | **packaging** |
| `_classify_sentence_action` / `_fails_final_validation_heuristics` | Drop vs rewrite routing | legality + **semantic mutation** on rewrite |
| `final_coherence_pass` / `_cohere_sentences` | Dedupe, terminal punctuation, lowercase drop heuristics | **packaging** + light legality (fragment drop) |
| `final_validation_pass` | Second pass with `_simple_diegetic_fallback` | **semantic mutation** |
| `atomic_rewrite_enforcement_pass` | Template / fallback enforcement on sentence list | **semantic mutation** |
| Post–`apply_final_emission_gate` strict-social **sealed** path (`post_final_emission_gate` + `strict_social_terminal_clamp`) | Returns `gate_sealed_text` without further rewrite | **packaging** (no-op / passthrough boundary) |

### `game/social_exchange_emission.py`

| Current function / helper | Current behavior | Classification |
|----------------------------|------------------|----------------|
| `minimal_social_emergency_fallback_line`, `lawful_strict_social_dialogue_emergency_fallback_line`, `strict_social_ownership_terminal_fallback` | Deterministic **emergency** dialogue lines from resolution | **semantic mutation** intended as **(c)** strict-social **shaping** (documented seam owner) |
| `social_fallback_line_for_sanitizer` / `deterministic_social_fallback_line` | Contextual fallback selection for sanitizer / open-social recovery | **semantic mutation** (c) |
| `apply_strict_social_sentence_ownership_filter` / `apply_strict_social_ownership_enforcement` | Drops or retains sentences by ownership / interruption rules | **legality** (filter) + packaging |
| `normalize_social_exchange_candidate` | Normalizes candidate shape for gate | **packaging** |
| `build_open_social_solicitation_recovery` | Builds recovery text from visible facts / templates | **semantic mutation** (c) |
| `apply_strict_social_terminal_dialogue_fallback_if_needed` / `repair_strict_social_terminal_dialogue_fallback_if_needed` | Terminal clamp to lawful dialogue | **semantic mutation** (c) |
| `_merge_interruption_chunk`, `_forced_interruption_progression_line` | Interruption merge / progression line | mixed: **packaging** (merge) vs **semantic mutation** (forced line) |

### `game/final_emission_text.py` (shared utilities)

| Current function / helper | Current behavior | Classification |
|----------------------------|------------------|----------------|
| `_normalize_text`, `_normalize_text_preserve_paragraphs`, `_normalize_terminal_punctuation`, `_capitalize_sentence_fragment`, `_sanitize_output_text` | Collapse whitespace, paragraph preservation, terminal punctuation, light HTML strip | **packaging** |
| `_global_narrative_fallback_stock_line` | Deterministic stock line from scene anchor renderer | **semantic mutation** when used as **replacement** narrative (used from gate composition paths) |

### `game/narrative_planning.py` / `game/prompt_context.py` / `game/response_policy_contracts.py`

| Scope | Current behavior | Classification |
|--------|------------------|----------------|
| `narrative_planning.py` | No direct imports of `sanitize_player_facing_output` / `apply_final_emission_gate` in C2 Block A search scope | **n/a** (not a final-emission mutator module) |
| `prompt_context.py` | Documents gate ownership of `response_delta_*`; assembles prompt bundles | **planner** (upstream of final emission) |
| `response_policy_contracts.py` | Resolves shipped policy **shapes** for gate consumers | **planner** (contract structure, not final text mutation) |

---

## Semantic mutation rows — upstream owner, migration note, target bucket

Bucket key: **(a)** planner-owned pre-GPT structure · **(b)** validator-owned bounded upstream repair (before final seal) · **(c)** strict-social emission-owned fallback shaping · **(d)** CTIR/API-owned deterministic resolved-turn packaging before final emission.

| Item | Target upstream owner | Migration note | Bucket |
|------|------------------------|----------------|--------|
| `_minimal_answer_contract_repair` / `_minimal_action_outcome_contract_repair` | `prompt_context` + `response_policy_contracts` **planner** guidance; `api` / turn pipeline for **resolved-turn** prompts | Model should emit compliant **answer** / **action_outcome** with check prompts surfaced **before** final gate; gate should **fail** or pass through with reason codes instead of minting lines | **(a)** + **(d)** |

**Block B landed (2026-04-22):** Contract-shaped answer/action fallback **construction** now lives in `game/upstream_response_repairs.py`; `apply_final_emission_gate` merges `upstream_prepared_emission` at entry and `_enforce_response_type_contract` **consumes** `prepared_answer_fallback_text` / `prepared_action_fallback_text` only (no boundary synthesis). Missing prepared text sets `response_type_upstream_prepared_absent` on the response-type debug path. **Sanitizer:** API turn path passes `sanitizer_boundary_mode="strip_only"` with upstream empty-fallback stock so `sanitize_player_facing_output` does not mint diegetic substitutes on that path; legacy default mode unchanged for unit tests. Strict-social dialogue terminal repairs remain owned by `game/social_exchange_emission.py` as before.
| `_enforce_response_type_contract` minimal repair path | Same as above | Keep validator; move **text generation** to upstream deterministic packaging or retry policy | **(d)** |
| `_repair_answer_completeness_minimal` (front-load, partial order, gate phrase inject) | `prompt_context` answer_completeness instructions; optional **(b)** replay repair | Reordering to satisfy “answer first” is **compliance theater** at the boundary; belongs in **retry / planner** or bounded pre-final pass explicitly labeled non-final | **(a)** / **(b)** |
| `_repair_response_delta_minimal` | `prompt_context` delta prompts; **(b)** if any repair stays | Same: delta repair is **semantic reorder**; prefer writer retry with clearer `previous_answer_snippet` contract | **(a)** / **(b)** |
| `apply_spoken_state_refinement_cash_out` | `api` / session publishers + **(d)** turn packaging | Spoken refinement should be **pre-authored** in structured turn output or prompt-visible snippet, not assembled at gate | **(d)** |
| `repair_fallback_behavior` stack (`_synthesize_*`, templates, clarifying question synthesis) | `prompt_context` + shipped `fallback_behavior` contract consumption | Partial/clarifying **shapes** should be model-produced within contract; gate strips meta voice **only** | **(a)** |
| `sanitize_player_facing_output` diegetic rewrites | `gm` / guard paths + **(a)** | Scaffold leakage should be **prevented** pre-GM; sanitizer retains **strip-only** + serialized extraction | **(a)** |
| `_apply_tone_escalation_layer`, `_apply_narrative_authority_layer`, `_apply_anti_railroading_layer`, `_apply_context_separation_layer`, `_apply_player_facing_narration_purity_layer` | `prompt_context` / planner constraints; evaluator feedback offline | Narrow each to **strip / mark fail** vs generating replacement sentences | **(a)** / **(b)** |
| `_apply_answer_shape_primacy_layer` | Planner pressure/payload ordering | Same as answer completeness | **(a)** |
| `_apply_scene_state_anchor_layer` minimal repairs | `prompt_context` scene anchor section; **(d)** | Opening tether belongs in **prompt-visible** anchor hints, not silent prepend at gate | **(a)** / **(d)** |
| `_repair_fragmentary_participial_splits` | Retry / planner instruction (“complete sentences”) | Grammar-coherence belongs in **model pass** or bounded **retry**, not silent finite-verb invention | **(a)** |
| `_apply_fast_fallback_neutral_composition_layer` | `api` fast-fallback path + **(d)** | Composition should produce valid neutral text **before** final emission | **(d)** |
| `_global_narrative_fallback_stock_line` when used to **replace** empty/malformed emission | Scene packaging owner (`api` / narrative planning handoff) | Stock line as **last-resort** might remain **(c)** or **(d)** only if explicitly framed as non-authoritative filler with stable reason codes | **(d)** |
| `build_open_social_solicitation_recovery` | `social_exchange_emission` (keep) vs move orchestration | Already **(c)** owner; ensure gate does not **duplicate** recovery synthesis | **(c)** |

---

## Explicitly **allowed** final-emission operations (convergence target)

- Punctuation normalization and consistent terminal punctuation **without** changing word choice or sentence order for policy compliance.
- Whitespace cleanup and soft-break normalization.
- Paragraph packaging (preserve `\n\n` where contracts require dialogue layout).
- Route-illegal **stock** sentence stripping and replacement with **reason-coded** failure or **explicitly owned** emergency lines (see strict-social seam).
- Removal of prohibited / meta / system / schema leakage (including serialized JSON firewall extraction).
- Stable **`_final_emission_meta`** and gate debug packaging (`final_emission_meta.py` orchestration consumer).
- **Legality validators** and pass/fail reason codes; no-op pass-through when the candidate already satisfies contracts.
- Bounded **referent clarity** pronoun substitution from **explicit allow-list** labels only (per Objective #7 narrative).
- Visibility enforcement that **drops** non-visible references or replaces with **already authorized** paraphrase from policy tables (when no new fact is introduced — tighten over time to strip-first).

---

## Explicitly **disallowed** final-emission operations (convergence anti-goals)

- Generating a **direct answer** fallback line not already present as model output or deterministic **resolved-turn** packaged text.
- Generating an **action outcome** sentence from player input + resolution at the boundary.
- **Semantic sentence reordering** solely to create contract compliance (answer-first, delta-first, caveat swap).
- **Compression** intended to create new emphasis or implied meaning beyond removing exact duplicates.
- **Bridge text** that resolves missing narrative intent or “finishes” the model’s partial thought with new substance.
- **Planner-like reconstruction** (scene anchors, participial repair, analytical → scenic rewrite) at the sanitizer or silent gate layer.
- **Narrative authority cash-out** (hidden facts, outcomes, anti-railroad replacements) that is not purely **legality-preserving** removal.

---

## Maintainer workflow

1. When touching emit path, locate the symbol in the inventory above and prefer **moving synthesis upstream** per the bucket table.  
2. Keep `docs/architecture_ownership_ledger.md` aligned with this file for **gate vs repairs** convergence language.  
3. Use sparse `C2_OWNER_AUDIT` anchors in code to mark **packaging-only** safe zones vs **move-upstream** debt.

### Repo expectation convergence (Block D1)

Tests under `tests/` should prefer **`final_route`**, **`fallback_kind`**, tags, and **`_final_emission_meta`** reason codes over expecting last-mile prose repair (bounded partial, fast-fallback composition rewrite, gate sentence reorder). When the pipeline emits **explicit replace or nonsocial minimal fallback**, assert that path instead of brittle diegetic substrings that assumed pre-C2 boundary synthesis.

### Anti-regression lock-in (Block D2, 2026-04-22)

**Goal:** make the shipped C2 boundary **hard to regress silently**.

- **Behavioral invariants** live in `tests/test_final_emission_boundary_convergence.py` (scenario-style gate + strip-only sanitizer cases: thin answer/action with upstream markers, strict-social terminal repair kind, upstream-absent explicit debug, route-illegal stock packaging, meta prefix strip, serialized payload extraction, clean pass-through).
- **Advisory static drift scan:** `tools/final_emission_ownership_audit.py` (default exit 0; `--strict` fails on **signal**-class heuristics only). Complements `tools/validation_layer_audit.py` (Objective #11), which is a different seam.

---

## Revision

| Date | Note |
|------|------|
| 2026-04-22 | Initial C2 Block A inventory from static read of `final_emission_gate.py`, `final_emission_repairs.py`, `final_emission_validators.py`, `output_sanitizer.py`, `social_exchange_emission.py`, `final_emission_text.py`; planner modules grep-scoped as above. |
| 2026-04-22 | C2 Block B: upstream `upstream_prepared_emission` + `upstream_response_repairs.py`; gate consumes prepared answer/action text; API strip-only sanitizer path; metadata `response_type_upstream_prepared_absent` / narration_constraint `upstream_prepared_absent`. |
| 2026-04-22 | C2 Block D1: repo-wide pytest expectations converged to validate-only / strip-only / explicit-replace semantics; integration suites updated for malformed fast-fallback, opening contamination, and transcript terminal paths. |
| 2026-04-22 | C2 Block D2: boundary invariant tests extended; `tools/final_emission_ownership_audit.py` advisory drift scan; docs aligned to shipped runtime (meaning upstream; final emission legality + packaging; strict-social seam; evaluator read-only). |
