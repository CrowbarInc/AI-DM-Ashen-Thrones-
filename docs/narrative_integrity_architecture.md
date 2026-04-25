# Narrative integrity — runtime module layout

Concise map for “where does this belong?” after the Block 3 split and Block 4 documentation pass. **Behavior is unchanged by this document**; it reflects `game/` as of the consolidation boundary. For **planner convergence** (CTIR → narrative plan → GPT → gate, seam labels, static anti-regression audit), see `docs/planner_convergence.md` — including **developer workflow** commands for the static audit, a focused pytest slice, and CI (`.github/workflows/content-lint.yml`). For **anti-echo + rumor realism** operator detail (status model, repairs, telemetry, evaluator verdicts), see `docs/narrative_authenticity_anti_echo_rumor_realism.md`.

For **validation-layer phase ownership** (engine truth vs planner structure vs GPT expression vs gate legality vs offline evaluator scoring), see `docs/validation_layer_separation.md` and the executable leaf registry `game/validation_layer_contracts.py`.

**Objective N4 (Acceptance Quality floor):** deterministic anti-collapse / playability-floor checks
(contract + pure validation + bounded subtractive repairs) live in `game/acceptance_quality.py`.
This is **adjacent** to Narrative Authenticity (NA): NA keeps anti-echo / signal-density / diegetic
shape ownership; N4 targets thin grounding, single-anchor collapse, abstract-only terminals, and
plot-trailer closes. Maintainer map: `docs/acceptance_quality_layer.md`. **Gate wiring:** after C4
`narrative_mode_output` (and referent/visibility where applicable), `apply_final_emission_gate`
calls `validate_and_repair_acceptance_quality` once per exit path and merges the returned trace
into `_final_emission_meta`. **Activation:** default-off without `prompt_context.narrative_plan`;
default-on with a plan unless `acceptance_quality_contract` disables the layer.

**Objective N3 (Role-based narrative composition):** `game/narrative_planning.build_narrative_plan` emits
`narrative_roles`—five abstract roles (`location_anchor`, `actor_anchor`, `pressure`, `hook`, `consequence`)
with closed-set `signals`, `emphasis_band` (``minimal`` / ``low`` / ``moderate`` / ``elevated`` / ``high``),
and bounded counters or kind-tags (e.g. hook `information_kind_tags`) derived only from sibling plan
slices already built from CTIR-shaped inputs (scene anchors, pressures, `required_new_information`,
`narrative_mode_contract`, visibility-shaped `allowable_entity_references`, `role_allocation`). This is
**shaping guidance only**; CTIR and shipped contracts remain authoritative. Coarse integer weights stay in
`role_allocation`. **Upstream one-step repair:** `game/narration_plan_bundle.build_narration_plan_bundle` runs
`game.narrative_plan_upstream.apply_upstream_narrative_role_reemphasis` after a successful plan build—only
when `validate_narrative_plan(..., strict=False)` passes; it may bump each *weak* family’s `emphasis_band` by
at most one step, capped at ``elevated``, using omission-risk heuristics already encoded in the role rows.
It does not mutate CTIR, contracts, counters, or `role_allocation`. A second invocation on the same dict is
idempotent once `debug.n3_upstream_role_reemphasis.applied` is true. **Prompt shipping:** `game.prompt_context`
appends structural N3 guidance plus a trusted supplemental lane only when the bundled plan validates the same
relaxed gate; compact `prompt_debug.narrative_plan.narrative_roles_skim` includes per-family bands/signal
counts, optional upstream repair summary, and **observability-only** `collapse_observability` (`sig_families_n`,
`low_band_n`, `reinforced_n`, `max_band`, `anchor_hint`)—never legality or scoring. **Single-anchor collapse**
is mitigated by bounded multi-facet composition hints plus optional upstream band nudges; heavy scoring or
template beats stay out of scope (see N4 acceptance-quality for post-generation floor checks).

#### N3 examples (operator / maintainer glance)

**Plan body — `narrative_roles`:** five fixed keys (`location_anchor`, `actor_anchor`, `pressure`, `hook`, `consequence`). Each row is bounded metadata: an `emphasis_band`, a sorted closed-set `signals` list, and small counters or tags (for example hook `information_kind_tags`). There is no prose and no second copy of CTIR.

**Skim — `prompt_debug.narrative_plan.narrative_roles_skim`:** per-family `emphasis_band`, `signal_n`, and `signals_head` (first few signal strings). Optional `upstream_role_reemphasis` mirrors a trimmed bundle trace (`applied`, `skip_reason`, `reinforced_families`). `collapse_observability` adds counts plus `anchor_hint` (`none` | `high_band_vs_sparse_peers` | `low_signal_coverage`); treat it as **read-only contrast**, not a gate or score—CTIR and shipped contracts still decide conflicts.

**Upstream trace — `narrative_plan.debug.n3_upstream_role_reemphasis`:** JSON-safe dict with `applied`, `weak_roles`, `reinforced_families`, `actions` (for example `bump_emphasis:hook:minimal->low`), `skip_reason` when nothing ran, and short `safety_notes`. Same trust gate as the plan’s relaxed validator; idempotent per plan object once `applied` is true.

**Block C1 (post-AER):** This file is a maintainer-facing consolidation map alongside `docs/current_focus.md` and the governance docs in `tests/TEST_AUDIT.md` / `tests/TEST_CONSOLIDATION_PLAN.md`.

---

## Post-AER Consolidation Rules

These rules apply while the repo is in **post-AER consolidation** (see `docs/current_focus.md`). They exist to prevent cleanup passes from accidentally becoming feature work.

- **No behavior expansion** — consolidation PRs do not add gameplay systems, new mechanics, or UI complexity.
- **No new policy layers** unless **required by a bug fix** — prefer tightening existing **orchestration** and contracts over inventing parallel enforcement stacks.
- **Extraction is allowed** only when it **reduces ambiguity** or **test overlap** (for example, a **pure** validator already split to `final_emission_validators.py`)—not when it spreads **orchestration** across owners.
- **`game/final_emission_gate.py` remains the `apply_final_emission_gate` orchestration owner** — helpers may be split out when they are clearly **pure** (validators), **deterministic** repairs, shared text utilities, or **metadata-only** glue; anything that orders layers, integrates sanitizer paths, or seals strict-social emit paths stays in **orchestration** unless a later pass proves a zero-ambiguity move.
- **Test files should have one primary ownership domain each**, with **smoke overlap** elsewhere only when two layers (for example, pure routing table vs full `/api/chat` stack) intentionally assert different depths.

---

## Consolidation Targets (runtime + tests)

| Domain | Cleanup intent |
| --- | --- |
| **Final emission metadata packaging** | Normalize `_final_emission_meta` (and related) packaging so emit **orchestration** owns composition; avoid duplicate meta mutation sites. |
| **Telemetry normalization seam (Objective #13)** | **Completed consolidation**: `game/final_emission_meta.py` owns **FEM packaging + read-side normalization** for `_final_emission_meta` (and helpers such as :func:`~game.final_emission_meta.assemble_unified_observational_telemetry_bundle`); `game/telemetry_vocab.py` owns the **shared canonical event vocabulary** (phase/action/scope/reasons + envelope); `game/final_emission_gate.py` remains **orchestration/write-timing**; `game/stage_diff_telemetry.py` owns **bounded raw snapshots/transitions** plus its own canonical event projection; `game/narrative_authenticity_eval.py` owns **offline scores** plus evaluator canonical events. All telemetry projections are **observational** — they must not drive gate legality. No policy by JSON. |
| **Prompt / sanitizer ownership boundaries** | Keep **pre-generation** contracts in prompt/guard paths vs **post-GM** string hygiene in sanitizer paths; document **smoke overlap** vs **canonical owner** for each invariant. For prompt-contract assembly specifically, the canonical runtime owner is `game/prompt_context.py`, the practical primary direct-owner suite is `tests/test_prompt_context.py`, and downstream prompt consumers stay secondary. **Applied (C3):** prompt/guard vs sanitizer pytest homes remain split per ``tests/TEST_CONSOLIDATION_PLAN.md`` (*Block C3 applied*). |
| **Social / emission ownership boundaries** | Keep strict-social emission, escalation machinery, retry-terminal fallback suites, and catch-all social tests from competing as co-equal **canonical owners** of the same string families. |
| **Transcript duplicate assertion thinning** | Transcripts prove sequencing and cross-turn state; reduce duplicate substring locks where a smaller **contract-driven** test already owns the gate. |
| **Lead / clue cleanup** | **Deferred** until after **prompt/sanitizer** and **social/emission** batches — see `tests/TEST_CONSOLIDATION_PLAN.md` → *Next consolidation order*. |
| **Objective #7 referent seam** | **Documented + regression-hardened (Block D):** deterministic artifact owner `referent_tracking.py`; prompt ship + compact mirror; post-GM validator/repair/gate wiring per *Objective #7* section above. |

---

## Observational telemetry pipeline (Block C)

**Hard rule:** telemetry is **observational only** — it records what ran for debugging, audits, and
offline harnesses. It must **never** decide legality, layer order, retries, repairs, or emitted
text. Do not encode new policy by adding JSON keys and branching on them in orchestration.

**Vocabulary owner:** :mod:`game.telemetry_vocab` defines the shared phase/action/scope tokens,
reason-list shaping, and the single ``build_telemetry_event`` envelope. FEM, stage-diff, and the
evaluator keep their **raw** field semantics; projections only normalize into that envelope.

**Layers:**

1. **Raw / source** — Pipeline-owned dicts unchanged at rest: FEM under the emission debug lane
   (and legacy top-level compatibility), ``metadata["stage_diff_telemetry"]`` snapshots/transitions,
   validator internal ``failure_reasons`` / ``skip_reason`` shapes before they are packaged into FEM.
2. **Normalized read helpers** — :func:`game.final_emission_meta.normalize_final_emission_meta_for_observability`
   and :func:`game.final_emission_meta.normalize_merged_na_telemetry_for_eval` coerce **known**
   nested subtrees to stable empty dict/list forms without inventing new policy fields.
3. **Canonical observational projections** — :func:`game.telemetry_vocab.build_telemetry_event` is the only
   envelope for cross-domain comparison. Each projection (FEM, stage-diff, evaluator) supplies
   ``phase``, ``owner``, ``action``, ``reasons``, ``scope``, and a bounded ``data`` allow-list.
   Multiple raw reason families (for example FEM ``narrative_authenticity_failure_reasons`` vs
   ``narrative_authenticity_reason_codes``) should be **merged** into canonical ``reasons`` at
   projection time, not duplicated as parallel top-level event keys.
4. **Unified observational bundle** — :func:`game.final_emission_meta.assemble_unified_observational_telemetry_bundle`
   joins normalized FEM, FEM events, stage-diff events + curated ``stage_diff_surface``, and
   evaluator events for **read-side** inspection only; it is not a runtime policy bus.

**Canonical event fields** (see :mod:`game.telemetry_vocab`): ``phase``, ``owner``, ``action``,
``reasons``, ``scope``, ``data``.

---

## Opening + structured start (UX1 / OF1 seam)

- **Opening-scene realization** (deterministic contract + basis) is owned by `game/opening_scene_realization.py` and wired through **`game/prompt_context.py`** on the normal narration stack — not by final-emission construction.
- **Structured “Start Campaign”** is a bootstrap HTTP path (`POST /api/start_campaign`) that feeds the same **`_run_resolved_turn_pipeline`** as chat; it does not introduce a parallel prompt assembler.
- **Shared normalization:** `_opening_scene_normalized_action_and_resolution(...)` in `game/api.py` is the single bundle for internal bootstrap vs player-typed campaign-start cues (transcript-facing fields differ; action id / type / target scene stay aligned).
- **Shared persistence tail:** `_complete_opening_turn_persistence_like_chat(...)` appends the transcript row, traces, and optional `campaign_started` latch for both chat and structured start after GM output exists.
- **Session/UI latch:** `session.campaign_started` is authoritative; `compose_state()` exposes `ui.campaign_started` and `ui.campaign_can_start` (fresh transcript + turn index zero only).
- **Final emission** (`apply_final_emission_gate`, sanitizer) remains a **downstream** consumer of opening/start construction — not a co-owner of opening basis assembly.

### C1-A — Scene opening convergence (Narrative Plan owns the opener contract)

Runtime narration follows **CTIR → Narrative Plan `scene_opening` → `prompt_context` → GPT → gate**. Structural `scene_opening` (anchors, closed-set `opening_reason`, visible-fact anchor ids/categories, prohibited codes—**prose-free**) is emitted only from **`game/narrative_planning.build_narrative_plan`** at the upstream bundle seam (`game/narration_plan_bundle`, `game/narrative_plan_upstream`). **Runtime may mark opening need** (for example `narration_obligations.is_opening_scene`, resume-after-restore via `SESSION_NARRATION_RESUME_ENTRY_PENDING_KEY` / `session_view["resume_entry"]` / `planning_session_interaction`), but **closed-set opening reason** for seam validation must go through **`infer_scene_opening_reason`** in `narrative_planning` or the approved guard path in **`game/narration_seam_guards`** (`scene_opening_seam_invalid` on failure). **`prompt_context`** consumes **plan projection** (`public_narrative_plan_projection_for_prompt`) plus renderer-only **`opening_scene_realization`** (basis shaping, `patch_opening_export_with_plan_scene_opening`, `merge_opening_instructions`, prohibited-content expansion from **`prohibited_opener_lines_from_codes` / `default_prohibited_opener_content`**). **`opening_scene_realization` is not an independent opener authority** alongside the plan: there is no valid opening path without a **stamp-matched bundle** and, when required, a valid plan **`scene_opening`**. Missing or invalid required `scene_opening` is a **seam failure** (`scene_opening_seam_invalid` / planner bypass trace), **not** silent fallback narration. Maintainer scan: `tools/planner_convergence_audit.py` (C1-A heuristics bundled with planner convergence).

## Objective #7 — Referent tracking & post-GM referent clarity (derivative seam)

This seam is **derivative-only**: it records bounded, JSON-safe projections and applies **deterministic** post-GM checks/repairs. It is **not** a general referent resolver, clause parser, semantic NLP engine, or a layer that overrides `interaction_context`, CTIR, visibility contracts, or other upstream authorities. **Upstream wins on conflict.**

### Ownership map (runtime)

| Concern | Canonical owner |
| --- | --- |
| Deterministic construction + schema validation of the **full** referent artifact | `game/referent_tracking.py` (`build_referent_tracking_artifact`, `validate_referent_tracking_artifact`) |
| Build **once** per prompt bundle and ship the full artifact on the prompt contract | `game/prompt_context.py` — exports `referent_tracking` on the narration / prompt context |
| **Compact** turn-packet mirror (observability / transport only; **not** a second full artifact) | `game/turn_packet.py` (packet boundary) — field `referent_tracking_compact` holds only: `referent_artifact_version`, `active_interaction_target`, `referential_ambiguity_class`, `ambiguity_risk` |
| Post-GM **validation** (prefers full artifact; compact-only paths abstain from repair-driving semantics) | `game/final_emission_validators.py` — `validate_referent_clarity` |
| Post-GM **bounded repair** (at most one safe pronoun substitution; no new names beyond allow-lists) | `game/final_emission_repairs.py` — `_apply_referent_clarity_emission_layer` and helpers |
| **Orchestration** (wire the layer on all finalize paths before final sealing / downstream debug attachment) | `game/final_emission_gate.py` — `_apply_referent_clarity_pre_finalize` |
| Authoritative **social / addressee** resolution and interaction-state mutation | **`game/interaction_context.py`** (unchanged; referent artifact **reads** bounded slices, it does not re-resolve targets) |

### Implemented behavior (precise)

- **Visibility-gated named references:** forbidden/off-visible ids contribute to `_referent_forbidden_display_names` so the validator can flag **disallowed_named_reference_in_text**; repair never inserts those strings.
- **Conservative pronoun handling:** opening-window pronoun heuristics (`_opening_has_pronoun_risk`) combined with `pronoun_resolution.strategy == "unresolved"` and `referential_ambiguity_class` drive **ambiguous_pronoun_environment** / **pronoun_before_anchor** signals — no GPT, no deep parse.
- **Structural ambiguity signaling:** `referential_ambiguity_class`, `ambiguity_risk`, and `forbidden_or_unresolved_patterns` are carried on the **full** artifact only; the compact mirror repeats **class + risk** for observability.
- **Interaction-target continuity support:** `interaction_target_continuity` on the full artifact records drift/prior/current/signal ids; **target_continuity_drift** / **unsupported_target_switch** categories gate repairs conservatively.
- **Full prompt artifact priority:** `validate_referent_clarity` sets `referent_validation_input_source` to `full_artifact` whenever a valid full artifact is present; violation categories are derived from the **full** artifact even if a compact mirror is also attached.
- **Compact packet observability only:** if only `referent_tracking_compact` exists, validation runs with **empty** `referent_violation_categories` and records `unresolved_referent_ambiguity` from the compact class — repair **abstains** (`limited_input_no_full_artifact`); no reconstruction of the full artifact from the mirror.
- **Bounded repair:** `_repair_referent_clarity_minimal` performs **at most one** pronoun→explicit-label substitution (first regex match only); no chaining.
- **Pinned active-target label:** `referent_repair_label_source == "active_interaction_target_pinned"` only when the validator’s visibility-safe, drift-free conditions hold (continuity subject entity matches visible `active_interaction_target`, etc.).
- **No second semantic authority:** no model inference; no dependency on free-form clausal semantics beyond bounded string/id checks already described.

### What was explicitly not built

Do **not** describe this seam as: a general referent resolver; a clause parser; a semantic NLP engine; or an authority that overrides `interaction_context`, CTIR, or visibility owners. Packet consumers must **not** treat `referent_tracking_compact` as equivalent to `prompt_context["referent_tracking"]`.

## Flow (high level)

1. **Turn input** hits `game.api` / `game.api_turn_support` (not detailed here).
2. **Coarse routing** (`game.interaction_routing`) classifies dialogue vs world-action lanes (dialogue lock, OOC/engine guards, etc.).
3. **Social commitment breaks** (`game.social_continuity_routing`) decide when continuity yields to explicit non-social redirection; session hooks may be applied via `game.interaction_context` re-exports.
4. **Targeting**
   - **Vocative / substring helpers:** implemented in `game.interaction_context`; **thin re-exports** in `game.dialogue_targeting` for a stable import surface.
   - **Authoritative social target** (precedence-ordered binding): **`game.interaction_context.resolve_authoritative_social_target`** — intentionally **not** moved to `dialogue_targeting` (import-cycle risk; keeps parsing next to context mutation).
5. **Contracts / policy read side:** `game.response_policy_contracts` is the canonical runtime owner for shipped response-policy contract resolution. It resolves shipped `response_type_contract` plus read-side accessors for shipped `answer_completeness`, `response_delta`, `fallback_behavior`, interaction continuity, and last-player-input probing for the gate. Private compatibility accessors and top-level `fallback_behavior` / `social_response_structure_contract` fallbacks may remain importable for older payloads, but that residue is compatibility-only rather than a second semantic home.
6. **Strict-social and emission helpers:** `game.social_exchange_emission` (downstream strict-social emission application consumed by the gate; not the validator/repair home and not the owner of gate layer ordering).
7. **Deterministic validation:** `game.final_emission_validators` (`validate_*`, `inspect_*`, `candidate_satisfies_*`).
8. **Repairs / layer wiring:** `game.final_emission_repairs` (`apply_*`, `merge_*`, skip helpers, and repair-side consumers of shipped policy contracts).
9. **Acceptance quality (N4) floor:** `game.acceptance_quality` — contract + `validate_and_repair_acceptance_quality`; `game.final_emission_gate` owns ordering and FEM merge (not a second NA layer; see `docs/acceptance_quality_layer.md`).
10. **Shared text / patterns:** `game.final_emission_text` (normalization, regex scaffolding — no policy **orchestration**).
11. **Orchestration + compatibility:** `game.final_emission_gate.apply_final_emission_gate` wires sanitizer, remaining in-module policy layers (tone, narrative authority, anti-railroading, context separation, scene anchor, speaker selection, etc.), logging, and metadata. `game.final_emission_meta.py` remains metadata-only packaging/read-side support rather than a co-equal orchestration home. **Historical tests** may still import private helpers from `final_emission_gate` even though implementation lives in extracted modules — prefer importing from the real **canonical owner** for new code.

Post-gate sanitization and other emit-path modules (`game.output_sanitizer`, etc.) stay as documented in existing suites.

**Objective C2 (Block D2 lock-in):** Final-emission **ownership** (upstream meaning vs boundary legality/packaging vs strict-social seam) is summarized in `docs/final_emission_ownership_convergence.md`. Regression locks: `tests/test_final_emission_boundary_convergence.py` and `tools/final_emission_ownership_audit.py` (advisory drift scan; `--strict` optional).

## Test ownership (canonical)

See **`tests/TEST_AUDIT.md`** for the current governance map and **`tests/TEST_CONSOLIDATION_PLAN.md`** for recorded consolidation boundaries. Those docs should follow runtime owners and practical direct-owner suites rather than overrule them. **`tests/test_inventory.json`** is the machine-readable inventory (regenerate with `py -3 tools/test_audit.py`).

Examples aligned with this layout:

| Concern | Primary test homes |
| --- | --- |
| Full `/api/chat` stack + gate integration | `test_turn_pipeline_shared.py` |
| Pure routing table / dialogue lock | `test_dialogue_routing_lock.py` |
| Directed social / vocative / emergent actor | `test_directed_social_routing.py` |
| Prompt-context bundle / shipped prompt contracts | `test_prompt_context.py` (practical primary direct-owner suite); `test_prompt_compression.py`, `test_final_emission_gate.py`, `test_social_exchange_emission.py`, `test_narration_transcript_regressions.py`, and `test_prompt_and_guard.py` remain secondary coverage |
| Response-policy contract read side | `test_response_policy_contracts.py` (practical primary direct-owner suite for direct accessor and bundle-materialization semantics); `test_fallback_shipped_contract_propagation.py`, `test_response_delta_requirement.py`, `test_final_emission_gate.py`, `test_social_exchange_emission.py`, `test_final_emission_validators.py`, `test_interaction_continuity_contract.py`, and `test_interaction_continuity_validation.py` remain secondary downstream consumer/application/regression/continuity coverage |
| Stage-diff telemetry / observability | `test_stage_diff_telemetry.py` (practical primary direct-owner suite for direct `game.stage_diff_telemetry` helper/accessor semantics, snapshot/transition packaging, bounded telemetry storage, and telemetry-owned observability fields); `test_turn_packet_stage_diff_integration.py` remains downstream turn-packet + gate/retry consumer coverage, and `test_narrative_authenticity_aer4.py` remains downstream narrative-authenticity regression / evaluator-consumer coverage. `game/turn_packet.py` remains the packet-boundary owner, while `game.stage_diff_telemetry.resolve_gate_turn_packet(...)` remains compatibility residue only |
| Strict-social exchange emission seam | `test_social_exchange_emission.py` (practical primary direct-owner suite for downstream emission semantics, including terminal dialogue application once contract resolution is already known); `test_strict_social_emergency_fallback_dialogue.py`, `test_social_emission_quality.py`, and `test_dialogue_interaction_establishment.py` remain secondary downstream / compatibility / harness coverage |
| Target authority regressions | `test_social_target_authority_regressions.py` |
| Contextual minimal repair | `test_contextual_minimal_repair_regressions.py` |
| Empty social / retry / terminal fallback | `test_empty_social_retry_regressions.py` |
| Final emission gate ordering / contracts | `test_final_emission_gate.py` (practical primary direct-owner suite for direct orchestration-order, final-route, and continuity-adjacent gate-step semantics); downstream suites such as `test_social_exchange_emission.py`, `test_turn_pipeline_shared.py`, `test_stage_diff_telemetry.py`, `test_social_emission_quality.py`, `test_dead_turn_detection.py`, `test_answer_completeness_rules.py`, `test_response_delta_requirement.py`, `test_interaction_continuity_speaker_bridge.py`, `test_interaction_continuity_validation.py`, `test_interaction_continuity_repair.py`, and transcript/regression harnesses remain secondary consumer / observability / regression / continuity-consumer coverage |
| **Objective C2 final-boundary ownership** (upstream prepared emission, strip-only sanitizer, explicit absent-prepared traces) | `tests/test_final_emission_boundary_convergence.py` (scenario + repair-layer invariants); `test_final_emission_gate.py` / `test_upstream_response_repairs.py` remain orchestration and upstream-payload owners; `tools/final_emission_ownership_audit.py` is a maintainer advisory scan |
| **Objective #7 referent artifact + post-GM clarity** | `test_referent_tracking.py` — construction/schema of `build_referent_tracking_artifact`; `test_prompt_context.py` — prompt bundle + **compact** `turn_packet.referent_tracking_compact` shape (no full-artifact duplication); `test_final_emission_validators.py` + `test_final_emission_gate.py` — `validate_referent_clarity` + `_apply_referent_clarity_emission_layer` / `_apply_referent_clarity_pre_finalize` seam locks. Optional tiny shared fixtures: `tests/helpers/objective7_referent_fixtures.py`. Player-facing **visibility** referential clarity (`validate_player_facing_referential_clarity`) remains owned by `game/narration_visibility.py` with suites such as `test_referential_clarity_*.py` — a separate, older seam from the prompt-artifact referent pack. |

## Intentionally deferred (non-goals for this consolidation)

- **Authoritative target resolution** stays in `interaction_context` — **deferred** extraction to `dialogue_targeting` while cycle coupling with roster/context writes remains risky.
- **Large policy-layer clusters** (tone escalation, narrative authority, anti-railroading, scene anchor, speaker enforcement, etc.) remain **in** `final_emission_gate.py` for **orchestration** — only validators/repairs/text/contracts were split out; further extraction is **deferred** optional work unless it clearly reduces ambiguity.
- **Debug / trace glue** tied to `apply_final_emission_gate` stays with **orchestration** unless a later pass isolates it without churn.
- **Lead/clue consolidation** (test and runtime overlap reduction) remains **deferred** until **prompt/sanitizer** and **social/emission** batches per `TEST_CONSOLIDATION_PLAN.md` — not part of the first post-AER consolidation slice.
- **Broad test-file merges** and mass marker refactors remain **deferred** per `TEST_AUDIT.md`.

## When to extend behavior

| You are changing… | Start in… |
| --- | --- |
| Dialogue vs action routing rules | `interaction_routing.py` |
| When social continuity breaks | `social_continuity_routing.py` |
| Vocative parsing (no precedence policy change) | `interaction_context.py` (+ re-export in `dialogue_targeting.py` if adding a public helper) |
| Who is the authoritative addressee | `interaction_context.resolve_authoritative_social_target` |
| What response shape the writer owed | `response_policy_contracts.py` |
| Whether text satisfies a contract (no side effects) | `final_emission_validators.py` |
| N4 acceptance-quality contract / floor checks / canonical validate+repair+revalidate seam | `acceptance_quality.py` (orchestrated via `validate_and_repair_acceptance_quality` from `final_emission_gate.py`) |
| How to repair or skip a policy layer | `final_emission_repairs.py` |
| Normalization / shared patterns | `final_emission_text.py` |
| Layer order, sanitizer integration, strict-social path, logging | `final_emission_gate.py` (**orchestration** owner) |
| Referent tracking **artifact** construction / JSON schema | `referent_tracking.py` |
| Where the full referent artifact is attached to the prompt bundle | `prompt_context.py` |
| Post-GM referent clarity validation / bounded pronoun repair | `final_emission_validators.py` / `final_emission_repairs.py` (wired by `final_emission_gate.py`) |
