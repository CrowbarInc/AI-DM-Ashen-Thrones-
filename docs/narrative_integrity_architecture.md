# Narrative integrity — runtime module layout

Concise map for “where does this belong?” after the Block 3 split and Block 4 documentation pass. **Behavior is unchanged by this document**; it reflects `game/` as of the consolidation boundary. For **anti-echo + rumor realism** operator detail (status model, repairs, telemetry, evaluator verdicts), see `docs/narrative_authenticity_anti_echo_rumor_realism.md`.

For **validation-layer phase ownership** (engine truth vs planner structure vs GPT expression vs gate legality vs offline evaluator scoring), see `docs/validation_layer_separation.md` and the executable leaf registry `game/validation_layer_contracts.py`.

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
| **Telemetry normalization seam (Objective #13)** | **Completed consolidation**: `game/final_emission_meta.py` is the **canonical telemetry schema/normalization/mutation seam** for `_final_emission_meta` (FEM) and related helpers; `game/final_emission_gate.py` remains the **orchestration/write-timing owner**; `game/stage_diff_telemetry.py` remains **observational projection only**; evaluator/playability/reporting tooling are **offline consumers** only. Do not reintroduce ad hoc `_final_emission_meta` mutation or bespoke local consumer shaping. No policy by JSON. |
| **Prompt / sanitizer ownership boundaries** | Keep **pre-generation** contracts in prompt/guard paths vs **post-GM** string hygiene in sanitizer paths; document **smoke overlap** vs **canonical owner** for each invariant. For prompt-contract assembly specifically, the canonical runtime owner is `game/prompt_context.py`, the practical primary direct-owner suite is `tests/test_prompt_context.py`, and downstream prompt consumers stay secondary. **Applied (C3):** prompt/guard vs sanitizer pytest homes remain split per ``tests/TEST_CONSOLIDATION_PLAN.md`` (*Block C3 applied*). |
| **Social / emission ownership boundaries** | Keep strict-social emission, escalation machinery, retry-terminal fallback suites, and catch-all social tests from competing as co-equal **canonical owners** of the same string families. |
| **Transcript duplicate assertion thinning** | Transcripts prove sequencing and cross-turn state; reduce duplicate substring locks where a smaller **contract-driven** test already owns the gate. |
| **Lead / clue cleanup** | **Deferred** until after **prompt/sanitizer** and **social/emission** batches — see `tests/TEST_CONSOLIDATION_PLAN.md` → *Next consolidation order*. |
| **Objective #7 referent seam** | **Documented + regression-hardened (Block D):** deterministic artifact owner `referent_tracking.py`; prompt ship + compact mirror; post-GM validator/repair/gate wiring per *Objective #7* section above. |

---

## Opening + structured start (UX1 / OF1 seam)

- **Opening-scene realization** (deterministic contract + basis) is owned by `game/opening_scene_realization.py` and wired through **`game/prompt_context.py`** on the normal narration stack — not by final-emission construction.
- **Structured “Start Campaign”** is a bootstrap HTTP path (`POST /api/start_campaign`) that feeds the same **`_run_resolved_turn_pipeline`** as chat; it does not introduce a parallel prompt assembler.
- **Shared normalization:** `_opening_scene_normalized_action_and_resolution(...)` in `game/api.py` is the single bundle for internal bootstrap vs player-typed campaign-start cues (transcript-facing fields differ; action id / type / target scene stay aligned).
- **Shared persistence tail:** `_complete_opening_turn_persistence_like_chat(...)` appends the transcript row, traces, and optional `campaign_started` latch for both chat and structured start after GM output exists.
- **Session/UI latch:** `session.campaign_started` is authoritative; `compose_state()` exposes `ui.campaign_started` and `ui.campaign_can_start` (fresh transcript + turn index zero only).
- **Final emission** (`apply_final_emission_gate`, sanitizer) remains a **downstream** consumer of opening/start construction — not a co-owner of opening basis assembly.

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
9. **Shared text / patterns:** `game.final_emission_text` (normalization, regex scaffolding — no policy **orchestration**).
10. **Orchestration + compatibility:** `game.final_emission_gate.apply_final_emission_gate` wires sanitizer, remaining in-module policy layers (tone, narrative authority, anti-railroading, context separation, scene anchor, speaker selection, etc.), logging, and metadata. `game.final_emission_meta.py` remains metadata-only packaging/read-side support rather than a co-equal orchestration home. **Historical tests** may still import private helpers from `final_emission_gate` even though implementation lives in extracted modules — prefer importing from the real **canonical owner** for new code.

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
| How to repair or skip a policy layer | `final_emission_repairs.py` |
| Normalization / shared patterns | `final_emission_text.py` |
| Layer order, sanitizer integration, strict-social path, logging | `final_emission_gate.py` (**orchestration** owner) |
| Referent tracking **artifact** construction / JSON schema | `referent_tracking.py` |
| Where the full referent artifact is attached to the prompt bundle | `prompt_context.py` |
| Post-GM referent clarity validation / bounded pronoun repair | `final_emission_validators.py` / `final_emission_repairs.py` (wired by `final_emission_gate.py`) |
