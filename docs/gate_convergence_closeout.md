# Gate Convergence Closeout

**Status:** Closeout / freeze. The Gate (`apply_final_emission_gate` and supporting modules) is treated as **maintenance-grade converged**.
This document is the formal stop-point for Blocks A–AA; further changes should be **bug-driven**, **audit-driven**, or **performance-driven**, not broad refactors.

**Companion docs:**

- `docs/gate_cleanup_inventory.md` — full per-seam inventory and Block-by-block convergence record (Blocks A–AA).
- `docs/final_emission_boundary_audit.md` — boundary mutation taxonomy.
- `docs/final_emission_ownership_convergence.md` — final-emission ownership map.

---

## Original Problems

The Gate convergence initiative started with several intertwined problems that made the final emission boundary fragile and hard to reason about:

- **Hidden semantic mutation.** Gate-internal helpers (e.g. tone, narrative authority, narration purity, anti-railroading, scene-state anchor, fast-fallback neutral composition, response-delta, social response structure) silently rewrote player-facing text under the guise of "validation," with no consistent classification telling reviewers which mutations were legality-allowed vs semantically disallowed.
- **Fallback authorship ambiguity.** Opening fallback prose could be authored either upstream (`upstream_prepared_opening_fallback`) or composed locally inside the Gate (`_deterministic_opening_fallback_text_and_meta`), with no clear precedence rule and no observable authorship marker on emitted FEM.
- **Speaker-repair ownership blur.** `enforce_emitted_speaker_with_contract` performed `local_rebind`, `canonical_rewrite`, and `narrator_neutral` repairs and additionally mutated `eff_resolution.social` via `_sync_eff_social_to_resolution`, with no taxonomy entry distinguishing this from packaging.
- **Opening compatibility-local prose authorship.** When upstream prepared snapshots were absent or incomplete, the Gate composed opening prose locally without surfacing that authorship choice in metadata or telemetry, making the residue invisible to tests and audits.
- **Dialogue-plan vs speaker timing ambiguity.** `_enforce_dialogue_plan_invariant_on_strict_social` runs **before** `enforce_emitted_speaker_with_contract`. Canonical-only dialogue plans against alias openers triggered subtractive strip on the **pregate** text, producing what looked like "speaker-repair drift" but was actually dialogue-plan attribution mismatch.
- **Orchestration density.** A single function (`apply_final_emission_gate`) carried strict-social branching, response-type contracts, ~20 boundary layers, sealed-replace selection, finalize sanitization, and provenance containment, with no separable contract surfaces for individual concerns.
- **Invisible compatibility residue.** Disabled repair helpers, legacy alias shims (e.g. `_compat_opening_fallback_text_from_gm`), top-level FEM fallback reads, and private sealed selectors lived alongside active code with no tagged "residue" or "removable-after-deprecation" markers.

---

## What Was Converged

The Blocks A–AA effort delivered the following structural and observability convergences. Together they make the Gate **failure-localized**, **ownership-mapped**, **contract-guarded**, and **heavily snapshotted**:

- **Mutation taxonomy** — `game/final_emission_boundary_contract.py` defines the canonical `PACKAGING_ALLOWED`, `LEGALITY_ALLOWED`, and `SEMANTIC_DISALLOWED` allowlists with `classify_final_emission_mutation` / `assert_final_emission_mutation_allowed`. Unknown kinds fail closed.
- **Semantic-disallowed fencing** — every formerly silent semantic repair layer (tone, NA, AR, context separation, narration purity, answer-shape primacy, scene anchor, fast-fallback neutral composition, response delta, social response structure, narrative authenticity) is now validation/metadata-only at the boundary; mutation paths are explicitly classified `SEMANTIC_DISALLOWED` and **never** passed to `assert_final_emission_mutation_allowed`.
- **Upstream-prepared opening preference** — `maybe_attach_upstream_prepared_opening_fallback_payload` runs at gate entry on `scene_opening` turns and `_upstream_prepared_opening_fallback_payload_if_usable` is the canonical structural-usability predicate; selectors prefer upstream-prepared payloads (Blocks G, I).
- **Fail-closed opening attach policy** — empty / non-attachable curated facts (Block H), missing curated-facts schema (Block J), incomplete stub payloads (Block I, recoverable), and observed `maybe_attach` build failure (Blocks M, N) all route to a sealed marker (`OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER`) instead of silently composing locally.
- **Compatibility-local visibility** — when the Gate still runs `_deterministic_opening_fallback_text_and_meta` (for legacy / helper-only callers), authorship is emitted as `opening_fallback_authorship_source = OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` and the kind `compose_opening_fallback_compatibility_local` remains `SEMANTIC_DISALLOWED`.
- **Speaker-contract extraction** — `get_speaker_selection_contract`, `validate_emitted_speaker_against_contract`, `_apply_speaker_contract_repairs`, `_try_local_rebind_opening_speaker`, `_sync_eff_social_to_resolution`, and `_merge_speaker_enforcement_into_outputs` live in `game/speaker_contract_enforcement.py` (Block R). Gate keeps the `enforce_emitted_speaker_with_contract` orchestration entry to preserve test patch semantics.
- **Shadow-equivalence harnesses** — `tests/helpers/speaker_relocation_shadow_harness.py` (Block T) and `tests/helpers/post_speaker_finalize_probe.py` (Block U) prove speaker-boundary equivalence and inventory the first post-speaker layer that diverges normalized text. `tests/helpers/speaker_gate_order.py` locks strict-social phase order.
- **Alias-aware dialogue-plan validation** — `pregate_attributed_label_matches_dialogue_social_plan` (Blocks Y, Z) accepts canonical ids/names plus **declared** alias rows (`allowed_pregate_speaker_labels` / `writer_attribution_label`) with required `speaker_alias_resolution_source` provenance. No fuzzy / inferred-from-prose matching.
- **Relocation readiness criteria** — Block AA records the conditional go for **logic** relocation (dual-run shadow harness in CI) and the no-go for **timing** relocation (finalize-stack divergence not proven, FEM merge shape differs from isolated mirror, dependency on declared alias bundles).

---

## Intentional Remaining Residue

These items are **knowingly retained** at maintenance grade. They are documented in `docs/gate_cleanup_inventory.md` and have direct-owner tests; none are silent bugs.

- **`local_rebind` remains Gate-timed.** `_apply_speaker_contract_repairs` still runs `speaker_contract_local_rebind` inside the strict-social trunk after NA / tone / narrative-authority. Block AA records this as a conditional-go relocation candidate; runtime move is **not** scheduled for this release line.
- **`canonical_rewrite` / `narrator_neutral` remain legality fallbacks.** Both are taxonomy-classified `SEMANTIC_DISALLOWED` (honest authorship), but operationally they are the only deterministic legality fallbacks for invalid strict-social speaker ownership and empty allowed-speaker contracts. Relocation requires co-migrating NA / tone / narrative-authority ordering.
- **Finalize divergence remains downstream-dependent.** Block U lists post-speaker layers (`dialogue_plan_subtractive_strip`, visibility / first-mention / referential clarity, N4 acceptance quality, IC attach, finalize sanitizer) that may still reshape normalized text after speaker enforcement. This is **not** a Gate cleanup gap; it is the surface where future product / contract decisions land.
- **Compatibility-local opening helpers retained intentionally.** `_deterministic_opening_fallback_text_and_meta` is still reachable when callers bypass `maybe_attach_upstream_prepared_opening_fallback_payload` (legacy fixtures, helper-only tests, no-attach-failure path with attachable curated facts). Block L explicitly chose **not** to remove the composer; Block O classifies which tests are intentional bypass anchors.
- **Helper-level bypass tests retained intentionally.** Tests like `test_opening_failure_recovers_via_deterministic_fallback_not_action_outcome`, `test_opening_scene_safe_fallback_tuple_recovers_text_only_stub_without_compat_local`, `test_deterministic_opening_fallback_helper_exact_text_and_meta_snapshot`, and the Block H/J fail-closed anchors **deliberately** call helpers without running `maybe_attach`. They lock compatibility-local behavior, stub recovery telemetry, and fail-closed semantics that the harnessed tests cannot observe.

---

## Protected Architectural Invariants

These invariants must hold across any future Gate change. They are enforced by direct tests, by the boundary contract module, and by Blocks B–AA inventory rows:

- **Gate does not infer meaning from prose.** No layer parses player-facing text to discover meaning, repair semantics, or invent attribution beyond what `_dialogue_bearing_signals` / declared contracts already extract.
- **Semantic repair must remain classified honestly.** `SEMANTIC_DISALLOWED` taxonomy entries (`speaker_contract_local_rebind`, `speaker_contract_canonical_rewrite`, `speaker_contract_neutral_bridge`, `effective_social_resolution_sync`, `strict_social_referential_substitution`, `compose_opening_fallback_compatibility_local`, `interaction_continuity_repair`, `interaction_continuity_malformed_speaker_bridge`, plus the validation-only repair kinds) must **not** be passed to `assert_final_emission_mutation_allowed`.
- **No mutation path may masquerade as packaging.** Adding new mutation kinds requires a new taxonomy entry in `game/final_emission_boundary_contract.py`. `classify_final_emission_mutation` raises `ValueError` on unknown kinds (fail closed).
- **Upstream-prepared opening fallback remains canonical.** Selectors prefer `_upstream_prepared_opening_fallback_payload_if_usable`. Compatibility-local composition must record `opening_fallback_authorship_source = OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL`.
- **Dialogue-plan alias acceptance must remain declared-only.** `pregate_attributed_label_matches_dialogue_social_plan` accepts canonical ids/names and **declared** alias rows (`allowed_pregate_speaker_labels` / `writer_attribution_label`) with `speaker_alias_resolution_source` provenance.
- **No inferred speaker aliases.** `speaker_alias_resolution_source = "inferred_from_prose"` is forbidden by validator. Builders may only read `ctir.interaction.continuity_snapshot` and `referent_tracking` for declared alias rows.
- **No fuzzy speaker matching.** Pregate attribution comparison is exact (slug equality / case-fold string equality). Substring / regex / similarity matching is forbidden.
- **Speaker relocation requires parity harnesses.** Any future move of `local_rebind` / repair timing must extend Block T shadow-equivalence and Block U finalize-divergence probes through `_finalize_emission_output` for the touched scenario before merging.

---

## Stop-Point Decision

- **Further cleanup is optional.** The Gate is failure-localized, ownership-mapped, contract-guarded, and heavily snapshotted. Remaining residue is intentional and documented.
- **Future work should be bug/audit/perf-driven.** Open a focused block (or follow-up doc section) only when a specific defect, telemetry signal, or product decision motivates a change.
- **No broad refactor currently justified.** Speaker repair relocation, dialogue-plan timing changes, and opening compatibility-local removal all require co-migration of multiple layers and are not net-positive at this stop-point.
- **Experimental relocation belongs on isolated branches only.** Any `local_rebind` / repair timing experiment must run behind a feature flag or on a branch with mandatory dual-run + finalize-probe coverage before re-evaluation.

---

## Recommended Future Work

Small, optional list — not commitments:

- **Optional branch-only relocation experiment.** Branch-only or feature-flagged early `local_rebind`, with mandatory Block T / Block U dual-run extended through `_finalize_emission_output`.
- **Finalize divergence attribution tooling.** A reusable probe (or CI mode) that, given a fixture, reports which post-speaker layer first changes normalized text — useful when triaging downstream regressions.
- **Stricter `dialogue_social_plan` allowlist / versioning.** Block AA Phase 3: top-level allowlist validation in `validate_dialogue_social_plan` + `version` bump if/when undocumented producer keys cause drift.
- **CI shadow-equivalence mode.** Optional CI job that runs Block T's `install_dual_run_enforce` + Block U probes across a curated fixture set on every change touching `game/final_emission_gate.py` or `game/speaker_contract_enforcement.py`.

---

**Recommendation:** **End the Gate cleanup initiative at Block AB.** The Gate layer is at maintenance-grade convergence. New work should reopen specific seams only when bug, audit, or perf evidence requires it.
