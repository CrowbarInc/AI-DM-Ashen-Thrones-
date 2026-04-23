# Final emission boundary audit (Block A)

**Branch context:** anti-fragility / boundary hardening prep. **No behavior changes** in Block A—this document inventories where `player_facing_text` (or equivalent candidate strings) can change *after* the model (or upstream selector) has produced text, and classifies each touchpoint.

**Classification legend**

| Tag | Meaning |
|-----|---------|
| **PACKAGING_ALLOWED** | Whitespace collapse, HTML→text sanitizer, terminal punctuation helpers, metadata/sidecar packaging, stripping route-illegal contamination, fingerprint/provenance bookkeeping. |
| **LEGALITY_ALLOWED** | Deterministic rejection or replacement with a **sealed** stock/minimal line when hard illegality or contract failure demands it; no bespoke paraphrase of the failed candidate. |
| **SEMANTIC_DISALLOWED** | Meaning repair, answer repair, dialogue rewriting, narrative reconstruction, cadence smoothing, list→prose conversion, answer reordering, composed fallback prose, structural rewriting—**whether or not** currently implemented at the boundary (see inventory). |
| **UPSTREAM_OWNER** | Belongs before the gate or in planner/response policy/validators-only modules: upstream repairs, social emission routing, narrative planning contracts, pure validation without boundary text surgery. |

---

## 1. `game/final_emission_text.py`

| Location | What mutates | Classification |
|----------|----------------|----------------|
| `_normalize_text` | Collapses internal whitespace to single spaces | **PACKAGING_ALLOWED** |
| `_normalize_text_preserve_paragraphs` | Normalizes within paragraphs; keeps `\n\n` | **PACKAGING_ALLOWED** |
| `_sanitize_output_text` | `<br>` / tag strip / newline cap | **PACKAGING_ALLOWED** |
| `_normalize_terminal_punctuation` | Ensures closing `.` when missing | **PACKAGING_ALLOWED** (tone-adjacent but deterministic) |
| `_global_narrative_fallback_stock_line` | Returns **stock** anchor line from `render_global_scene_anchor_fallback` or fixed string | **LEGALITY_ALLOWED** when used as sealed fallback; **UPSTREAM_OWNER** for scene-anchor content authorship inside `diegetic_fallback_narration` |
| `_capitalize_sentence_fragment` | First alpha uppercased | **PACKAGING_ALLOWED** (surface form) |

**Suspicious-name patterns (helpers):** `normalize`, `sanitize`, `fallback`.

---

## 2. `game/final_emission_validators.py`

| Location | What mutates | Classification |
|----------|----------------|----------------|
| All `validate_*`, `inspect_*`, `candidate_satisfies_*` | Read-only checks on text | **UPSTREAM_OWNER** (validator surface; no `player_facing_text` assignment here) |

**Note:** This module defines *rules* consumed by repairs/gate; moving logic upstream does not change the fact that validators **suggest** repairs elsewhere.

---

## 3. `game/final_emission_repairs.py` (support module; still on the emission path)

### 3.1 Layers that **do not** change text on failure (metadata / reasons only)

- `_apply_answer_completeness_layer`, `_apply_response_delta_layer` — today return original `text` with flags; **UPSTREAM_OWNER** for substantive reorder (explicitly deferred at boundary per meta keys).

### 3.2 Text-changing helpers (mutation points)

| Symbol | Behavior | Classification |
|--------|----------|----------------|
| `apply_social_response_structure_repair` | Bullets→prose flatten, soft linebreak collapse | **SEMANTIC_DISALLOWED** (list→prose, structure) — *narrow* “dialogue packaging” justification exists in docstring; audit flags for convergence |
| `_flatten_list_like_dialogue` | Strip list markers; join lines; colon→em dash | **SEMANTIC_DISALLOWED** |
| `_collapse_multi_speaker_formatting` | Multiple `Name: "..."` → longest inner quote only | **SEMANTIC_DISALLOWED** (dialogue shape / substance loss) |
| `_merge_substantive_paragraphs` | Paragraphs merged to one | **SEMANTIC_DISALLOWED** |
| `_trim_leading_expository_connectors` | Removes leading connector phrases | **SEMANTIC_DISALLOWED** (cadence / rhetoric) |
| `_collapse_soft_line_breaks` | Single newlines → spaces | **PACKAGING_ALLOWED**–**SEMANTIC_DISALLOWED** borderline; can alter beat breaks |
| `_reduce_expository_density` | Orchestrates collapse + trim | **SEMANTIC_DISALLOWED** |
| `_normalize_dialogue_cadence` | Splits compound sentences; merges short sentences | **SEMANTIC_DISALLOWED** (cadence smoothing) |
| `_restore_spoken_opening` | Prepends “I’ll say it plain:” / “Here’s what I can tell you:” | **SEMANTIC_DISALLOWED** (authored lead-in) |
| `_apply_social_response_structure_layer` | Invokes validator + `apply_social_response_structure_repair` | **SEMANTIC_DISALLOWED** when repair applies |
| `_apply_narrative_authenticity_layer` | Calls `repair_narrative_authenticity_minimal` | **SEMANTIC_DISALLOWED** (narrative reconstruction; owner `game.narrative_authenticity`) |
| `repair_fallback_behavior` | Strips meta voice, fabricated authority, overcertain spans | **LEGALITY_ALLOWED**–**SEMANTIC_DISALLOWED** mix: subtractive strip vs meaning-changing removal |
| `_strip_patterns_from_text`, `_strip_meta_fallback_voice`, `_remove_fabricated_authority`, `_downgrade_overcertain_claims` | Pattern-based deletion/edits | **LEGALITY_ALLOWED** for hard-banned phrases; **SEMANTIC_DISALLOWED** when it removes informative content |
| `_rewrite_meta_fallback_as_diegetic_partial`, `_synthesize_known_edge_phrase`, `_synthesize_next_lead_phrase`, `_fallback_unknown_edge_phrase`, `_ensure_known_unknown_shape`, `_append_next_lead_if_allowed`, `_apply_social_fallback_leak_guard`, `_voice_extracted_next_lead_sentence` | Template / composed diegetic lines | **SEMANTIC_DISALLOWED** (fallback composition) |
| `_smooth_repaired_fallback_line`, `_merge_repeated_fallback_subject_pair` | Merges/smooths sentences | **SEMANTIC_DISALLOWED** |
| `_apply_fallback_behavior_layer` | Runs validator + `repair_fallback_behavior` | Orchestration; inherits classifications above |
| `_repair_referent_clarity_minimal` / `_apply_referent_clarity_emission_layer` | First risky pronoun → explicit label | **SEMANTIC_DISALLOWED** (minimal referent surgery; allow-listed label) |

**Suspicious helpers (search anchors):** `repair`, `smooth`, `normalize`, `collapse`, `flatten`, `restore`, `merge`, `fallback`, `substitute`, `rewrite`, `synthesize`, `cadence`, `structure`, `append_next_lead`.

---

## 4. `game/final_emission_gate.py` (orchestration)

### 4.1 Entry / provenance / finalize

| Stage | What mutates | Classification |
|-------|----------------|----------------|
| `merge_upstream_prepared_emission_into_gm_output` (imported) | Merges prepared fallback strings onto `gm_output` | **UPSTREAM_OWNER** (data prep; see `upstream_response_repairs`) |
| `_apply_upstream_fallback_pregate_containment` | Restores `selector_player_facing_text` snapshot | **PACKAGING_ALLOWED** / **LEGALITY_ALLOWED** (anti-drift restore, not paraphrase) |
| `_finalize_upstream_fallback_overwrite_containment` | Snapshot + `_sanitize_output_text` | **PACKAGING_ALLOWED** |
| `_finalize_emission_output` | `_sanitize_output_text`, `_strip_appended_route_illegal_contamination_sentences`, meta | **PACKAGING_ALLOWED** + **LEGALITY_ALLOWED** (strip route-illegal stock sentences) |
| `_strip_appended_route_illegal_contamination_sentences` | Drops known global placeholder sentences when bundled | **LEGALITY_ALLOWED** (strip-only contamination) |

### 4.2 `apply_final_emission_gate` — principal `out["player_facing_text"]` writers

| Stage | What mutates | Classification |
|-------|----------------|----------------|
| Strict-social suppression path | `sanitize_player_facing_output` strip-only | **PACKAGING_ALLOWED** |
| `build_final_strict_social_response` | Full strict-social pipeline | **SEMANTIC_DISALLOWED** + **LEGALITY_ALLOWED** (large; delegates to social stack) |
| `_enforce_response_type_contract` | May replace with upstream prepared lines | **LEGALITY_ALLOWED** / **UPSTREAM_OWNER** (prepared text) |
| `_apply_*` layers from `final_emission_repairs` | NA, SRS, fallback behavior, referent clarity | Per §3 |
| In-module layers: tone escalation, narrative authority, anti-railroading, context separation, narration purity, answer shape primacy, scene state anchor, fast fallback neutral composition | Narrow deterministic repairs | Mostly **SEMANTIC_DISALLOWED** (sentence surgery / composition); some **LEGALITY_ALLOWED** if purely subtractive |
| `enforce_emitted_speaker_with_contract` | Speaker repair | **SEMANTIC_DISALLOWED** (dialogue attribution shape) |
| `_apply_visibility_enforcement` → `_apply_first_mention_enforcement`, `_apply_referential_clarity_enforcement` | Full replace with visibility-safe fallbacks or local pronoun substitution | **LEGALITY_ALLOWED** (sealed pool) + **SEMANTIC_DISALLOWED** (local substitution) |
| `_apply_interaction_continuity_emission_step` | May replace with minimal social line | **LEGALITY_ALLOWED** |
| `_apply_fallback_behavior_layer` | See repairs | Mixed |
| `_apply_referent_clarity_pre_finalize` | Pronoun→label | **SEMANTIC_DISALLOWED** |
| Narrative mode output failure (strict) | `minimal_social_emergency_fallback_line` | **LEGALITY_ALLOWED** |
| `_apply_acceptance_quality_n4_floor_seam` | N4 subtractive repair or sealed replace | **PACKAGING_ALLOWED** (whitespace / terminal drop) + **LEGALITY_ALLOWED** (fallback replace) |

**Non–strict-social replace path:** `_standard_visibility_safe_fallback` family, scene integrity globals, banned stock phrase reasons — **LEGALITY_ALLOWED** when sealed.

**Suspicious symbols in-gate (grep anchors):** `_repair_*`, `_apply_*_layer`, `_finalize_*`, `_smooth`, `sanitize`, `composition`, `fallback`, `rebind`, `primacy`.

---

## 5. `game/upstream_response_repairs.py`

| Symbol | Behavior | Classification |
|--------|----------|----------------|
| `build_minimal_answer_contract_repair_text`, `build_minimal_action_outcome_contract_repair_text`, `build_upstream_prepared_emission_payload` | Composes deterministic contract lines | **UPSTREAM_OWNER** (must run **before** gate; not final-boundary packaging) |
| `apply_spoken_state_refinement_cash_out` | Appends templated refinement tail to `player_facing_text` | **UPSTREAM_OWNER** by design (Block C move); **SEMANTIC_DISALLOWED** if invoked late |

**`player_facing_text` assignment:** `apply_spoken_state_refinement_cash_out` only (pre-gate).

---

## 6. `game/acceptance_quality.py`

| Symbol | Behavior | Classification |
|--------|----------|----------------|
| `validate_acceptance_quality` | Pure validation | **UPSTREAM_OWNER** |
| `repair_acceptance_quality_minimal` | Whitespace normalize; optional **terminal sentence drop** | **PACKAGING_ALLOWED** + bounded subtractive (**LEGALITY_ALLOWED** framing); still changes player-visible length |
| `validate_and_repair_acceptance_quality` | Loop orchestration | Called from gate seam |

---

## 7. `game/social_exchange_emission.py`

| Symbol | Behavior | Classification |
|--------|----------|----------------|
| `apply_social_exchange_retry_fallback_gm` | Rewrites `player_facing_text` with `_standard_mode_social_retry_payload_floor` | **UPSTREAM_OWNER** (retry path before final gate in normal pipeline); **LEGALITY_ALLOWED** / **SEMANTIC_DISALLOWED** depending on routing—**not** `final_emission_gate` |

---

## 8. Tests that directly exercise final-emission repair behavior

| Test module | Role |
|-------------|------|
| `tests/test_final_emission_gate.py` | Orchestration order, scene state anchor, interaction continuity, fast fallback composition, visibility, referent pre-finalize, acceptance quality seam |
| `tests/test_final_emission_repairs.py` | Repair helpers and layer wiring |
| `tests/test_final_emission_validators.py` | Validator + `_apply_referent_clarity_emission_layer` integration |
| `tests/test_fallback_behavior_repairs.py` | Fallback behavior contract + FEM meta continuity |
| `tests/test_final_emission_scene_integrity.py`, `tests/test_final_emission_visibility.py` | Secondary gate-adjacent surfaces |
| `tests/test_final_emission_boundary_no_semantic_repair.py` | Block C integration: no list→prose / delta rewrite / multi-speaker collapse at final emission |

---

## 9. Consolidated “suspicious mutation helper” index (cross-module)

Use this as a grep checklist for later blocks:

- **repair / smooth / normalize:** `_normalize_text`, `_normalize_dialogue_cadence`, `_smooth_repaired_fallback_line`, `repair_*`, `_repair_*`
- **collapse / flatten / merge:** `_collapse_*`, `_flatten_list_like_dialogue`, `_merge_substantive_paragraphs`, `_merge_repeated_fallback_subject_pair`
- **restore / rewrite / synthesize:** `_restore_spoken_opening`, `_rewrite_meta_fallback_as_diegetic_partial`, `_synthesize_*`
- **fallback / substitute / append:** `repair_fallback_behavior`, `_append_next_lead_if_allowed`, `_fallback_unique_join`, `minimal_social_emergency_fallback_line`, `_standard_visibility_safe_fallback`
- **cadence / structure:** `_apply_social_response_structure_layer`, `apply_social_response_structure_repair`, `_normalize_dialogue_cadence`
- **decompress (historical):** finalize meta still records `sentence_decompression_applied` — verify stays **false** at boundary (see `_finalize_emission_output`)

---

## 10. Boundary contract added in Block B

Block B adds a **contract-only** module, `game/final_emission_boundary_contract.py`, that freezes canonical **mutation kind** strings into three buckets:

- **PACKAGING_ALLOWED** — whitespace/HTML/punctuation normalization, route-illegal stripping, final-emission meta packaging, preserving candidate text unchanged.
- **LEGALITY_ALLOWED** — sealed hard replace, contract-failure rejection, strict-social terminal fallback.
- **SEMANTIC_DISALLOWED** — completeness/delta/social-structure repairs, list/speaker flattening, spoken-opening restore, dialogue cadence, narration reconstruction, composed fallbacks, edge-phrase synthesis, answer reordering, microstructure smoothing, narrative repair, semantic fallback composition.

API (Block B): `classify_final_emission_mutation`, `is_packaging_allowed`, `is_legality_allowed`, `is_semantic_disallowed`, `assert_final_emission_mutation_allowed`. **Unknown** mutation kinds **fail closed** (raise); they are not treated as allowed.

Block B did **not** change runtime final-emission behavior by itself. **Block C** wires the contract into `final_emission_gate.py` / `final_emission_repairs.py` (asserts + disabled semantic repairs); the Block A inventory table remains the historical survey unless explicitly revised in a later doc pass.

Tests: `tests/test_final_emission_boundary_contract.py`.

---

## 11. Block C wiring notes (runtime boundary)

**What final emission still owns**

- **Packaging:** `_sanitize_output_text`, `_normalize_text` / `_normalize_text_preserve_paragraphs` at orchestration seams, `_strip_appended_route_illegal_contamination_sentences`, upstream fallback fingerprint containment restores, N4 `validate_and_repair_acceptance_quality` bounded subtractive seam (packaging-class whitespace / terminal drop only inside that module), and subtractive **fallback-behavior** strip passes (`strip_meta_fallback_voice_surfaces`, `strip_fabricated_authority_surfaces`, `trim_overcertain_claim_spans`) guarded by `assert_final_emission_mutation_allowed`.
- **Legality:** sealed stock/minimal replacements from `_standard_visibility_safe_fallback`, first-mention and referential-clarity **full replace** paths, generic gate `replaced` branch, strict-social `minimal_social_emergency_fallback_line` on hard contract failures, N4 floor replace when the candidate still fails after the bounded seam — each asserted with `hard_replace_illegal_output_with_sealed_fallback` (or strict-social terminal equivalent metadata).
- **Validation / metadata:** all `validate_*` layers, FEM merges, `allow_semantic_text_repair=False` referent pre-finalize (validation + skip metadata only), answer-completeness / response-delta **check-only** paths with `*_boundary_semantic_repair_disabled` flags.

**What semantic repair was disabled or moved**

- **Social response structure:** `apply_social_response_structure_repair` / list→prose flatten and related structural dialogue fixes no longer run in `_apply_social_response_structure_layer`; upstream owner: **planner / `upstream_response_repairs` / `social_exchange_emission`** (shape before gate).
- **Narrative authenticity:** `repair_narrative_authenticity_minimal` removed from `_apply_narrative_authenticity_layer`; upstream owner: **`game.narrative_authenticity`** and acceptance/planner seams before final emission.
- **Referent clarity (pronoun→label):** `_apply_referent_clarity_emission_layer(..., allow_semantic_text_repair=False)` from `_apply_referent_clarity_pre_finalize`; tests and upstream tooling may still call the layer with `allow_semantic_text_repair=True`. Upstream owner: **prompt_context / turn_packet preparation** or **`upstream_response_repairs`**.
- **Finalize:** participial / micro-smooth / decompress remain **off** (no calls); helpers may remain as dead code for upstream relocation.

**Contract wiring**

- `game.final_emission_boundary_contract.assert_final_emission_mutation_allowed` is invoked at selected gate finalize / containment / N4 / visibility-sealed / referent-passthrough sites and inside `repair_fallback_behavior` for each subtractive strip class.

**Tests**

- `tests/test_final_emission_boundary_no_semantic_repair.py` — integration checks for list-like dialogue, delta non-rewrite, multi-speaker preservation, awkward narration passthrough, and N4 sealed replace.

---

## 12. Block A conclusion

- **Single orchestration choke point:** `apply_final_emission_gate` plus `_finalize_emission_output`.
- **Largest semantic repair surface outside gate:** `final_emission_repairs.py` (social structure, narrative authenticity delegation, fallback-behavior strips/synthesis, referent clarity).
- **Upstream text mutation before gate:** `upstream_response_repairs.apply_spoken_state_refinement_cash_out`, `merge_upstream_prepared_emission_into_gm_output`, social retry fallback in `social_exchange_emission`.
- **Static enforcement:** `tests/test_final_emission_boundary_audit.py` defines `DISALLOWED_BOUNDARY_MUTATION_MARKERS` (union of SDK markers and gate-only semantic regression markers; Block D scans active source with docstrings and full-line comments stripped).

---

## 13. Block D — Maintainer reference

### Final Emission Owns

- **Packaging:** whitespace/HTML sanitizer, terminal punctuation normalization where already wired, route-illegal contamination stripping, final-emission meta packaging, `preserve_candidate_text` when the gate only reassigns text that was already validated at the boundary.
- **Legality:** sealed hard replace (`hard_replace_illegal_output_with_sealed_fallback`), contract-failure rejection paths, strict-social terminal fallback, N4 acceptance-quality floor replace when the candidate remains illegal after the bounded subtractive seam.
- **Subtractive-only fallback cleanup:** `strip_meta_fallback_voice_surfaces`, `strip_fabricated_authority_surfaces`, `trim_overcertain_claim_spans` inside `repair_fallback_behavior` (each guarded by `assert_final_emission_mutation_allowed`).
- **Validate-and-record:** answer completeness, response delta, social response structure, narrative authenticity, referent clarity (with `allow_semantic_text_repair=False` at the gate pre-finalize seam) — failures set metadata and `*_boundary_semantic_repair_disabled` flags without rewriting meaning at the boundary.

### Final Emission Must Never Own

- Dialogue list→prose flattening, multi-speaker collapse, cadence merges, spoken-opening injection, narrative authenticity text repair, referent pronoun→label substitution at the gate, response-delta echo rewrites, answer reordering, composed fallback answer bodies, edge-phrase synthesis, micro-sentence smoothing, or any LLM/SDK call to “fix” candidate text.

### Upstream Owners for Semantic Repair

- **`game.upstream_response_repairs`:** contract-shaped minimal lines, prepared emission merge, spoken-state refinement cash-out (must run pre-gate).
- **`game.social_exchange_emission`:** strict-social retry / terminal dialogue shaping where routed before final emission.
- **`game.narrative_authenticity`:** `repair_narrative_authenticity_minimal` and evaluator-facing repair loops (not invoked from final emission layers after Block C).
- **Planner / prompt preparation:** referent artifact richness, turn-packet hints, response policy materialization so text arrives gate-ready.

### How To Debug Boundary Validation Failure

1. Read `AssertionError` / `ValueError` from `assert_final_emission_mutation_allowed` — it names **`kind`** and **`source`** (call-site string).
2. If `kind` is unknown, add it to `PACKAGING_ALLOWED`, `LEGALITY_ALLOWED`, or `SEMANTIC_DISALLOWED` in `final_emission_boundary_contract.py` with the correct bucket (semantic repairs belong in `SEMANTIC_DISALLOWED` only, not as allowed asserts).
3. If a validator fails but text must not change at the boundary, confirm the layer sets `*_boundary_semantic_repair_disabled` and leaves `player_facing_text` unchanged; then fix upstream policy or repair hooks.
4. For FEM meta contradictions (e.g. repair-applied flags true while boundary is validate-only), inspect `tests/test_final_emission_boundary_no_semantic_repair.py` expectations.

### How To Add A New Final Emission Mutation Safely

1. Pick a **new canonical mutation kind string** (snake_case, specific verb+noun).
2. Classify it in `final_emission_boundary_contract.py` into exactly one of `PACKAGING_ALLOWED`, `LEGALITY_ALLOWED`, or `SEMANTIC_DISALLOWED`. If it changes meaning, it must be **`SEMANTIC_DISALLOWED`** and must **not** be passed to `assert_final_emission_mutation_allowed`.
3. At the single mutation site in `final_emission_gate.py` or `final_emission_repairs.py`, call `assert_final_emission_mutation_allowed(kind, source="…")` with a stable `source=` tag.
4. Extend `tests/test_final_emission_boundary_contract.py` integration tests if regex extraction needs a new call shape (prefer one-line string literal for `kind`).
5. Update this doc’s inventory table if the mutation is user-visible.

### Static Regression Lock

- **`tests/test_final_emission_boundary_audit.py`:** SDK markers forbidden in gate and repairs; semantic-repair markers forbidden in **gate** active source (docstrings / full-line `#` stripped).
- **`tests/test_final_emission_boundary_contract.py`:** every `assert_final_emission_mutation_allowed("…")` kind is contract-known and not `SEMANTIC_DISALLOWED`; unknown kinds still raise from `classify_final_emission_mutation`; subtractive fallback strips remain `PACKAGING_ALLOWED` and do not append synthesized lead prose.
- **`tests/test_final_emission_boundary_no_semantic_repair.py`:** integration checks that list-like dialogue, multi-speaker blocks, awkward narration, referent ambiguity, NA failures, and SRS failures do not flip semantic-repair success flags or rewrite text at the boundary.
