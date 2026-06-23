# AI-DM Project Development Retrospective — March 2026 to Present

**Reporting period:** March 16, 2026 through June 23, 2026  
**Repository commit period:** March 19, 2026 through June 23, 2026  
**Assessment basis:** current repository source, tests, documentation, audits, generated artifacts, Git history, and the exported OneNote development logs in `history/development_logs/`.

## Executive Summary

Since March, the project has moved from a promising local AI-GM prototype into a **feature-stabilized prototype / internal-alpha system with selective feature readiness**.

The visible accomplishment is a browser-based solo game loop with persistent campaign, scene, character, world, combat, social, exploration, clue, lead, project, clock, and journal behavior. The deeper accomplishment is architectural: the project no longer treats GPT narration as the place where game meaning, state, and correctness are decided. Engine and domain systems now own truth and resolution; CTIR snapshots resolved-turn meaning; planning systems produce bounded structural plans; GPT expresses those plans; deterministic gates enforce legality; and offline evaluators, replay harnesses, telemetry, audits, and scorecards explain what happened.

The March-April era created capability quickly. It established social targeting, authoritative leads, discovery and journal integration, travel and scene transitions, information visibility, response contracts, speaker discipline, narrative authenticity, persistent world progression, deterministic non-combat resolution, schema and state authority, prompt/context separation, UI modes, persistence safety, and long-session validation.

The May-June era changed the development posture. Rather than continuing to add behavior into already-dense narration and final-emission paths, the project concentrated on failure locality, replay acceptance, ownership extraction, fallback authorship, speaker parity, semantic-mutation attribution, recurrence tracking, test ownership, maintenance economics, and feature-boundary governance. This work did not merely add more tests. It created a repository-wide operational model for answering:

- what system owned a decision;
- where text first changed;
- why a fallback was selected;
- which speaker was expected and finally observed;
- whether a replay drifted;
- which bug class recurred;
- which tests own a contract;
- and whether a proposed feature touches a safe, caution, or prohibited boundary.

The conservative conclusion is that the project is **not ready for unrestricted feature-first development across the whole codebase**. It is ready to resume feature work in explicitly safe domains, and to proceed carefully in caution domains under the CB guardrails. Replay governance, final emission, fallback/sanitizer repair, speaker identity/adoption, and response-policy contracts remain protected maintenance surfaces.

The best high-level summary is:

> In roughly three months, the project built both an AI-driven tabletop game engine and the engineering controls needed to keep that engine from silently rewriting its own rules. The system is now meaningfully playable, testable, replayable, and auditable, but still requires boundary cleanup and clean-suite restoration before broad feature expansion is prudent.

## Phase Timeline

### 1. Initial architecture and safety foundation — March 16-24

The earliest development logs show that the project began with a broad but recognizable architecture: player input, intent classification, deterministic exploration/social/combat paths, mutable JSON state, prompt construction, and GPT narration. The first work was not purely feature-oriented. It immediately addressed architectural inconsistencies and dangerous ownership ambiguity.

Major results included:

- engine-first routing for structured actions;
- typed, context-anchored uncertainty instead of generic refusal/fallback prose;
- targeted retries rather than unconstrained regeneration;
- separation of clue possession from clue presentation;
- social target resolution and active-speaker constraints;
- scene-local actor validation;
- hard campaign reset and bootstrap/runtime separation;
- final string-boundary protection against scaffold or structured-payload leakage;
- route-specific social fallback isolation;
- early final-emission legality gates.

The March commits corroborate this progression: `5e0bfe0`, `7e65d92`, `09863c6`, the March 22 foundation and contamination cleanups, `3110993` for social target resolution, and `863d09a` for the lead-to-consequence vertical slice.

This phase established the project’s governing principle: **the engine decides; GPT narrates**.

### 2. Structured exploration and engine-result systems — March 25-April 5

The project then built structured systems around exploration and discovery rather than leaving them as prompt conventions.

Major results included:

- normalized player intent and addressable actions;
- deterministic exploration and skill-check outcomes;
- authoritative clue discovery and lead creation;
- explicit lead commitment, resolution, and obsolescence hooks;
- transition rules and destination binding;
- NPC promotion from scene-local actors into persistent world entities;
- a journal rebuilt to consume authoritative lead state;
- synthetic-player and manual-gauntlet harnesses;
- information visibility and first-mention enforcement;
- dedicated test ownership and fast/full test lanes.

The authoritative lead sequence is especially important. Commits `d2b6161`, `b983a16`, `a984cf8`, `7147b44`, `96c925f`, `7388055`, `ca4a825`, and `22bbe82` show a shift from “GPT mentions a lead” to engine-owned lead lifecycle, with the journal and prompt context consuming that state.

By early April, the project could do more than answer a prompt: it could create, preserve, pursue, resolve, obsolete, and display structured investigative state.

### 3. World, session, and state-persistence systems — April 5-22

The next phase strengthened the persistent game beneath narration.

Major results included:

- explicit scene state anchoring and interaction continuity;
- deterministic transition authority and destination binding;
- world projects, faction pressure, clocks, flags, and event progression;
- persistent campaign/session/combat/scene state;
- unified state-domain ownership (`world_state`, `scene_state`, `interaction_state`, `player_visible_state`, `hidden_state`);
- canonical schema contracts and explicit legacy adapters;
- CTIR as the resolved-turn semantic snapshot;
- runtime persistence envelopes with versioning and integrity metadata;
- atomic runtime saves;
- validate-first, all-or-nothing snapshot restore with rollback;
- concurrency guards around persistence operations;
- public, author, and debug channel separation.

The April 19-22 commit sequence is the architectural hinge:

- `68f2590` — Canonical Turn Intermediate Representation;
- `d46cf12` — pre-narration planning;
- `1d3580d` — unified state authority;
- `f14e081` — schema unification;
- `4782a71` — public/debug/author separation;
- `dedbee4` — deterministic non-combat resolution;
- `cd2832b` — world simulation backbone;
- `2101201` — persistence and session integrity hardening;
- `427ee61` — UI mode separation.

This is where the project became a persistent engine with a narration layer, rather than a narration application with attached JSON.

### 4. Social, combat, mechanics, and narrative-contract integration — April 5-25

Social play received the densest early hardening because it exposed the greatest mismatch between freeform model output and game-owned intent.

Major results included:

- active interlocutor and directed-address resolution;
- response-type gating;
- answer-completeness rules;
- response-delta and anti-echo rules;
- speaker selection discipline;
- social interruption progression and anti-loop behavior;
- social response-structure validation;
- interaction-continuity rules;
- tone/escalation constraints;
- narrative-authority and anti-railroading boundaries;
- dialogue/social plans derived from CTIR;
- strict-social fallbacks that fail closed into speaker-owned output;
- deterministic combat helpers for initiative, attacks, spells, conditions, and turn progression;
- deterministic non-combat resolution contracts for exploration/social outcomes.

By the April convergence work, dialogue-bearing output required a valid structural plan; GPT was no longer allowed to choose a speaker, infer intent, or invent social pressure simply because a reply sounded plausible. Action outcomes, transitions, openings, continuations, dialogue, and answer/exposition each gained an explicit ownership chain from CTIR/planning through prompt consumption and final validation.

### 5. Prompt/context compression and player-facing UX — April 4-26

The prompt and UI layers matured in parallel.

Major results included:

- prompt context rebuilt around authoritative leads and CTIR;
- conversational-memory window discipline;
- bounded, role-specific narrative-plan projections;
- referent and clause-level tracking;
- information visibility and spoiler filtering;
- player-visible, author, and debug state channels;
- browser tabs and payloads separated by UI mode;
- narrative authenticity and anti-echo telemetry;
- acceptance-quality floor checks;
- opening-scene convergence and preservation of curated opening facts;
- canonical `gm_output` convergence for campaign start and normal turns.

The significance is not prompt cleverness. It is that prompt construction became a **read-side transport layer**. It consumes authoritative state, CTIR, visibility contracts, and plans; it is not allowed to re-resolve the turn or back-write truth.

### 6. Replay, diagnostics, and audit-governance phase — May 4-June 22

May marked a deliberate pivot from capability growth to stabilization and explainability.

The first stabilization programs fenced the post-GPT adoption gateway, hardened realization failure locality, converged evaluator and gate boundaries, and built the first golden replay baseline. Subsequent cycles created:

- a protected golden-replay acceptance lane;
- failure classification and dashboard artifacts;
- runtime lineage events;
- fallback selection/content/authorship attribution;
- final-emission mutation taxonomy;
- opening-fallback ownership contracts;
- long-session 20-turn, then 25-turn protected replay;
- snapshot/resume persistence replay;
- advisory 50-turn aggregate session validation;
- replay drift taxonomy, risk, trends, and hotspot reports;
- speaker contract risk and end-to-end parity cases;
- first semantic-mutation attribution;
- bug-class recurrence history and governance;
- attribution completeness and bug-fix locality metrics;
- test inventory, direct-owner suites, and ownership-registry guards;
- maintenance hotspot and fan-in/fan-out analysis.

Key dated milestones include:

- `ac1ba90` (May 11) — golden replay baseline;
- `2619bb5` (May 26) — replay acceptance gate promotion;
- `3582d48` (May 28) — long-session stability;
- `92f7213` (May 30) — sustained-session validation;
- `a7d6025` (June 10) — bug-class recurrence tracking;
- `d65a535` (June 19) — runtime fallback incidence instrumentation;
- `ea80d52` (June 20) — speaker finalization divergence audit;
- `a31cb35` (June 21) — protected replay trend window;
- `d7895ba` (June 22) — speaker identity end-to-end parity;
- `0e5fe3a` (June 22) — first semantic mutation attribution;
- `ce36d0c` (June 23) — feature-boundary readiness audit.

The project’s hidden infrastructure became a major product asset in this phase.

### 7. Feature-readiness and maintenance closeout — June 20-23

The final phase converted accumulated stabilization knowledge into explicit development policy.

The CB program classified 16 domains:

- **5 safe** for normal feature work under lightweight guardrails;
- **6 caution** domains requiring focused tests and replay-smoke decisions;
- **5 prohibited** domains requiring audit/stabilization approval.

It validated one safe-domain pilot and one caution-domain pilot, measured speaker/fallback incidence, refreshed coupling and ownership drift, reconciled test-governance inventory drift, and issued a final **MODERATE** feature-readiness rating.

Documentation governance also reached a closeout: 472 retained records were classified, with no unknown ownership. The remaining documentation population is predominantly generator-owned, path-contract-owned, or intentionally historical rather than unmanaged debt.

The result is not blanket permission to build anywhere. It is a practical map of where feature work can resume without reopening the most fragile acceptance boundaries.

## Capability Growth

Compared with March, the project can now:

1. **Run a persistent solo campaign loop.** It maintains campaign, world, scene, session, character, combat, conditions, projects, clocks, factions, NPCs, clues, leads, journals, and interaction state.
2. **Resolve structured exploration and non-combat actions.** Intent, checks, outcomes, clues, transitions, and world updates have deterministic contracts rather than prose-only interpretation.
3. **Support bounded combat mechanics.** Initiative, end-turn, basic attacks, several spells/stances, skill checks, and conditions have engine paths.
4. **Sustain structured social play.** Directed address, active interlocutors, speaker contracts, continuity, response shape, escalation, interruption, and fallback behavior are explicitly governed.
5. **Manage investigative progression.** Leads have lifecycle state, commitments, relations, resolution, obsolescence, NPC payoff, and journal integration.
6. **Advance a persistent world.** Projects, faction pressure/agendas, world clocks, flags, and progression nodes can change independently of immediate narration.
7. **Preserve and restore runtime state safely.** Versioned envelopes, integrity checks, atomic writes, snapshots, rollback, and coherency validation protect mutable runtime files.
8. **Separate player, author, and debug experiences.** Public output is stripped of diagnostic and hidden-state channels; author/debug views are explicit siblings.
9. **Construct narration from resolved meaning.** CTIR and narrative plans carry turn meaning, roles, dialogue structure, transition nodes, opening/continuation structure, and answer/exposition obligations.
10. **Validate player-facing output deterministically.** The final-emission stack checks route legality, speaker identity, visibility, referents, response shape, anti-echo, narrative authenticity, acceptance quality, and scaffold leakage.
11. **Test sustained sessions.** Protected 25-turn replay, resume persistence, and advisory 50-turn aggregate paths provide multi-turn evidence.
12. **Explain failures.** Replay rows and diagnostics expose route, speaker, fallback, owner, source family, mutation, sanitizer, and continuity evidence.
13. **Track recurrence and maintenance cost.** Bug-class recurrence, fallback incidence, attribution completeness, fan-in/fan-out, corrective locality, and feature-boundary readiness are measurable.

## Architecture Evolution

### From ad hoc narration to a layered authority chain

The architecture now follows a recognizable forward flow:

`engine truth -> CTIR -> narrative plan -> prompt projection -> GPT expression -> deterministic gate -> offline evaluator`

Each layer has explicit non-ownership rules:

- the engine owns truth and mutation;
- CTIR owns bounded resolved-turn meaning;
- the planner owns structure and obligations;
- prompt context owns packaging, not re-resolution;
- GPT owns expression, not truth or legality;
- the gate owns deterministic legality and bounded repair, not subjective scoring;
- evaluators own offline scoring and diagnostics, not live behavior.

This is the project’s most important architectural change.

### From shared mutable blobs to governed state domains

State is now divided into five domains with canonical owners and guarded cross-domain operations. Player-visible state is a derived publication surface, not a truth store. Hidden state cannot be reconstructed from narration. GPT output cannot directly mutate world, scene, interaction, visible, or hidden authority.

### From duplicated result shapes to canonical contracts

Schema contracts centralize normalization and legacy adaptation for engine results, world updates, affordances, interaction targets, clues, projects, and clocks. Non-combat semantics flow through `resolution["noncombat_resolution"]` into CTIR rather than being reconstructed from raw prompt hints or legacy social fields.

### From a monolithic final gate to owned terminal pipelines

The final-emission gate remains high-risk, but its role changed substantially. The original gate mixed orchestration, semantic rewriting, speaker repair, fallback prose authorship, visibility, packaging, and metadata. Through the convergence and BI-BM decomposition work, the public gate became a thinner facade over strict/non-strict stacks, terminal pipelines, validators, repairs, metadata readers, visibility/fallback routers, and finalize modules.

The gate closeout reports a reduction from 9,316 lines to 308 lines at the facade in the measured BV period. That did not eliminate complexity; it redistributed it into named owners. The later BV5 revalidation found meaningful maintenance-cost reduction in several scoped surfaces, while still recording residual hubs.

### From tests as accumulation to tests as ownership

The test suite now has:

- a machine-readable inventory;
- direct-owner and neighbor roles;
- protected replay markers;
- ownership-registry governance;
- split-owner acceptance matrices;
- focused CI parity commands;
- explicit separation of smoke, transcript, gauntlet, evaluator, compatibility, and direct-owner suites.

As of June 23, the current tree collects **5,806 tests across 406 test modules**. This scale is both evidence of coverage and a maintenance risk; the ownership work exists to keep that scale from becoming unstructured duplication.

## Stability and Reliability Improvements

### Replay stability

The repository has progressed from transcript examples and manual gauntlets to protected replay:

- six short structural scenarios form the BW trend corpus;
- the protected lane checks route, speaker, source, owner, mutation, and final-text fingerprints;
- repeat-run BW and BZ windows recorded zero internal golden transcript drift;
- protected replay is a hard-fail CI lane;
- a 25-turn social-inquiry replay is acceptance-protected;
- snapshot/resume continuity is covered;
- 50-turn aggregate validation exists as advisory evidence.

On June 23, the current `-m golden_replay` lane ran cleanly: **6 passed**.

### Speaker stability

Speaker ownership moved from prompt advice to a contract spanning selection, validation, repair, final observation, replay projection, and risk scoring.

The BX guard matrix protects:

- role alias to canonical actor;
- canonical actor identity;
- distinct same-role actors;
- ambiguous multi-actor cases that must fail closed rather than falsely align.

Runtime artifact measurement found 0 speaker-repair events in the scoped 95-turn BV3D corpus, but the project correctly treats that as low-confidence incidence evidence rather than proof that the speaker boundary is low risk.

### Semantic mutation prevention and attribution

The final-emission boundary now distinguishes packaging-allowed, legality-allowed, and semantic-disallowed mutations. Unknown mutation kinds fail closed. Upstream-prepared answer/action/opening content is preferred over boundary invention.

June’s BY work added the ability to identify the **first normalized text-changing boundary** across policy, sanitizer, fallback, repair, and final-emission buckets. This closes an important diagnostic gap: “the final text changed” can now be separated from “this was the first layer that changed it.”

### Failure locality

Failure-locality work added:

- route, speaker, fallback, source-family, owner-bucket, mutation, sanitizer, and lineage fields;
- deterministic failure categories and investigation targets;
- replay failure dashboards;
- stage-diff snapshots;
- realization provenance audits;
- direct-owner test maps;
- closeout documents that name intentional residue and “do not casually reopen” boundaries.

This reduced the need to diagnose every bad output by reading the entire API-to-gate call chain.

### Fallback authorship

Fallback behavior was one of the largest historical risk families. The project now distinguishes:

- opening, visibility, sealed, sanitizer, social, retry, and terminal fallbacks;
- selection owner versus content owner;
- upstream-prepared versus compatibility-local authorship;
- owner buckets, source families, repair kinds, and recurrence identities;
- runtime incidence versus protected-replay recurrence.

The measured fallback rate fell from 69.16% in a broad legacy artifact scan to 1.05% in the scoped BV3D corpus. The reports explicitly warn that these populations are not directly comparable and that corpus scope dominates the headline. The valid conclusion is that fallback behavior is more legible and appears far less prevalent in the current scoped corpus—not that fallback risk has been universally eliminated.

### Corrective locality and recurrence tracking

The project established two forms of longitudinal maintenance evidence:

- a human-reviewed corrective-change baseline with median **7 effective files per fix** and **2.5 production files per fix**;
- bug-class recurrence history across protected replay, including active speaker, emission, fallback, and sanitizer keys.

The recurrence system is operational but immature as an outcome program: observability and forecasting are strong, while governance health, remediation outcomes, and lifecycle closure remain below target.

### Test ownership and documentation organization

Maintenance readiness now includes:

- direct-owner test registry;
- test inventory drift checks;
- CI/local command parity;
- split-owner acceptance contracts;
- audit manifest and documentation governance;
- generator-owned and test-owned path classification;
- closeout/discovery/evidence/metric organization.

This matters because the repository’s safety system is now large enough to become its own failure mode if ownership is unclear.

## Technical Debt and Risk Reduction

### Risks materially reduced or governed

| Historical risk | Current status |
|---|---|
| GPT narration mutating game truth | Architecturally prohibited; state-domain and validation-layer contracts govern the boundary |
| Generic, non-diegetic uncertainty | Replaced by typed, context/speaker-aware uncertainty and route-specific fallback |
| Wrong or off-scene speaker | Scene-local validation, speaker contracts, parity tests, and final observation now govern it |
| Social fallback leaking into scene/global narration | Strict-social terminal paths fail closed into social-only output |
| Prompt layer re-deciding resolved meaning | CTIR-first architecture and adapter tests prohibit reconstruction when CTIR exists |
| Hidden facts leaking to player output | Visibility contracts, channel separation, sanitizer/gate tests, and UI modes govern publication |
| Partial campaign reset contamination | Fresh-state factory and root-replacement reset paths |
| Persistence corruption or partial restore | Versioned envelopes, atomic writes, validate-first restore, rollback, coherency checks |
| Transition narration without state transition | Transition plan/convergence chain and scenario-spine enforcement |
| Silent semantic repair in the final gate | Mutation taxonomy, upstream-prepared content, attribution, and first-mutation probes |
| Replay failures with no owner | Failure classifier, dashboard, owner buckets, recurrence keys, and investigation targets |
| Test duplication with no canonical owner | Direct-owner registry, inventory governance, ownership guards |
| Documentation sprawl with unknown authority | Documentation inventory and governance closeout; zero unknown files in reviewed population |

### Risks reduced but not retired

- Final emission remains a high-coupling acceptance surface even after decomposition.
- Speaker repair timing and late post-speaker mutation still require protected evidence.
- Fallback incidence remains corpus-sensitive and lacks representative live-traffic measurement.
- Prompt/CTIR fan-in increased during late development and requires watchful contract tests.
- The visibility-fallback router remains a growing hub.
- Replay governance is powerful but expensive; schema and helper changes can create broad test fan-out.
- Long-session proof is deterministic and fixture-based, not proof of live-model campaign quality.
- Scheduler/off-screen world-event semantics remain deliberately deferred.
- Persistence migration across future schema versions is scaffolded but not proven through multiple real version upgrades.

## Evidence Table

| Accomplishment | Evidence files / commits / tests / logs | Why it matters |
|---|---|---|
| Engine-first project foundation | `history/development_logs/AI DM Development [I].pdf`; commits `5e0bfe0`, `7e65d92`, `09863c6`; `docs/system_overview.md` | Establishes deterministic ownership rather than prose-owned gameplay |
| Authoritative leads and investigation lifecycle | Commits `d2b6161` through `22bbe82`; `game/leads.py`; `tests/test_lead_*`; `tests/test_follow_lead_commitment_wiring.py` | Makes investigation persistent, actionable, and journal-visible |
| Social target and speaker authority | `game/interaction_context.py`; `game/speaker_contract_enforcement.py`; commits `3110993`, `5a56291`; `tests/test_directed_social_routing.py`; `tests/test_speaker_contract_enforcement.py` | Prevents wrong-target and wrong-speaker narration from being treated as acceptable prose variance |
| CTIR-first resolved-turn semantics | Commit `68f2590`; `game/ctir.py`; `game/ctir_runtime.py`; `docs/ctir_prompt_adapter_architecture.md`; `tests/test_ctir_*` | Gives retries and prompts one stable, engine-derived meaning snapshot |
| Unified state authority | Commit `1d3580d`; `game/state_authority.py`; `docs/state_authority_model.md`; `tests/test_state_authority.py` | Prevents prompt/output state from becoming a competing truth store |
| Schema unification | Commit `f14e081`; `game/schema_contracts.py`; `docs/schema_unification_pass.md`; `tests/test_schema_contracts.py` | Replaces scattered compatibility coercions with testable canonical adapters |
| Deterministic non-combat resolution | Commit `dedbee4`; `game/noncombat_resolution.py`; `tests/test_noncombat_resolution.py`; `tests/test_objective8_block_d_authority_lock.py` | Ensures social/exploration outcomes are engine semantics, not inferred from narration |
| Persistent world simulation | Commit `cd2832b`; `game/world_progression.py`; `docs/world_simulation_backbone.md`; `tests/test_world_progression_*`; `tests/test_world_simulation_backbone_*` | Supports projects, faction pressure, clocks, and flags beyond the immediate scene |
| Safe runtime persistence | Commit `2101201`; `docs/runtime_persistence_envelope.md`; `tests/test_runtime_persistence_regression_suite_obj14.py`; `tests/test_save_load.py` | Protects long-running campaigns from partial writes and unsafe restores |
| Player/author/debug separation | Commits `4782a71`, `427ee61`; `docs/objective15_ui_mode_separation.md`; `game/state_channels.py`; `tests/test_ui_mode_*` | Reduces spoiler and diagnostic leakage into the player experience |
| Narrative planning and convergence | Commits `d46cf12`, `bcb14fc`, `26ab008`; `game/narrative_planning.py`; `game/narration_plan_bundle.py`; `docs/planner_convergence.md`; `tests/test_planner_convergence_*` | Moves structure upstream and makes missing plans diagnosable rather than silently improvised |
| Dialogue/social convergence | Commit `7d4c11d`; `docs/dialogue_social_convergence.md`; `game/dialogue_social_plan.py`; `tests/test_dialogue_social_convergence.py` | Requires dialogue-bearing text to trace to an engine/planner-owned social plan |
| Transition convergence | Commit `eebb5c7`; `docs/transition_convergence.md`; `tests/test_narrative_planning_transition_node.py`; `tests/test_prompt_context_transition_node_consumption.py` | Prevents narrated location/time changes without corresponding planned state transitions |
| Final-emission ownership convergence | Commits `335926e`, `02ab9b0`, `4bbecf9`; `docs/final_emission_ownership_convergence.md`; `docs/gate_convergence_closeout.md`; `tests/test_final_emission_boundary_*` | Limits the terminal boundary to legality/packaging and makes semantic rewriting explicit |
| Failure-locality program | Commits `673118e`, `0f80564`, `177099a`; `docs/audits/closeouts/realization_failure_locality_closeout.md`; `tests/test_realization_*` | Turns broad narration failures into named seams and provenance evidence |
| Protected golden replay | Commits `ac1ba90`, `2619bb5`; `docs/testing/protected_replay_manifest.md`; `tests/test_golden_replay_structural_invariants.py`; `.github/workflows/convergence-checks.yml` | Creates acceptance-blocking end-to-end structural regression protection |
| Sustained-session validation | Commits `3582d48`, `92f7213`; `docs/audits/closeouts/cycle_n_long_session_stability_closure_2026-05-27.md`; `docs/audits/closeouts/cycle_u_sustained_session_validation_closure_2026-05-30.md`; `tests/test_golden_replay_long_session.py` | Provides 25-turn protected and 50-turn advisory evidence beyond single-turn tests |
| Replay trend windows | Commits `a31cb35`, `b0803f2`; `docs/audits/closeouts/BW_protected_replay_trend_window_closeout.md`; `docs/audits/closeouts/BZ_protected_replay_trend_window_2_closeout.md`; `tests/test_golden_replay_trend.py` | Measures repeated-run drift without over-locking exact prose |
| Speaker end-to-end parity | Commit `d7895ba`; `docs/audits/closeouts/BX_speaker_identity_end_to_end_parity_closeout.md`; `tests/test_bx_speaker_identity_golden_replay.py` | Protects canonical, alias, distinct-actor, and ambiguous-speaker cases |
| First semantic mutation attribution | Commit `0e5fe3a`; `docs/audits/discovery/BY_first_semantic_mutation_attribution_discovery.md`; `tests/test_by_first_semantic_mutation_attribution.py` | Identifies the first layer that changed output instead of only observing final drift |
| Bug-class recurrence tracking | Commit `a7d6025`; `artifacts/golden_replay/bug_recurrence_history.json`; `artifacts/golden_replay/bug_recurrence_history.md`; `tests/test_replay_bug_class_recurrence.py` | Makes repeated defect families measurable and assignable |
| Corrective-change locality baseline | Commit `5f0ad53`; `docs/audits/CA_program_closeout.md`; `docs/baselines/ca_corrective_locality_baseline.json`; `artifacts/ca3_corrective_locality_report.json` | Quantifies how expensive real fixes are and distinguishes fixes from refactors/governance work |
| Feature-boundary readiness | Commit `ce36d0c`; `docs/audits/CB_CLOSE_feature_boundary_readiness.md`; `docs/audits/CB1_feature_boundary_registry.md`; `docs/audits/CB_feature_boundary_guardrails.md` | Converts architectural caution into actionable safe/caution/prohibited development rules |
| Documentation governance | `docs/audits/documentation_governance_closeout.md`; `docs/audits/documentation_inventory.csv`; `docs/audits/audit_manifest.md` | Prevents audit evidence from becoming unowned maintenance debris |
| Current protected acceptance health | June 23, 2026 local verification: `python -m pytest -m golden_replay -q` -> 6 passed | Confirms the current protected short replay lane is green |
| Current test scale | June 23, 2026 collection: 5,806 tests across 406 modules | Demonstrates broad regression coverage while also explaining maintenance pressure |

## Current Project Maturity

### Assessment: feature-stabilized prototype / internal alpha

The project is beyond a simple prototype:

- it has a real persistent engine and browser UI;
- major gameplay domains have deterministic ownership;
- it can sustain scripted multi-turn sessions;
- protected replay gates critical structural behavior;
- persistence, visibility, state authority, and output legality have explicit contracts;
- failures are observable and increasingly attributable;
- feature boundaries are classified.

It is not yet comfortably “ready for feature-first development” as a whole:

- critical acceptance surfaces remain prohibited for normal feature work;
- live-model and long-campaign evidence is limited;
- maintenance cost is still concentrated in final emission, fallback, replay, prompt/CTIR, and ownership governance;
- current governance checks are not fully green on the in-progress repository state;
- no clean current full-suite run is preserved as release evidence.

The most accurate label is therefore:

> **Internal alpha / feature-stabilized prototype, selectively ready for feature development in safe domains.**

## Remaining Gaps

### 1. Restore a clean current acceptance baseline

The current tree collects 5,806 tests, but a current clean full-suite result is not available.

The checked-in `docs/audits/evidence/full_suite_results.txt` is historical: it records 1,438 passed and one failed test from a much smaller suite. It must not be used as the current health claim.

June 23 spot verification found:

- protected golden replay: **6 passed**;
- gate/final-emission closeout slice: production-contract tests passed, but evaluator closeout failed because the current documentation reorganization moved `docs/evaluator_convergence_closeout.md` while its test still expects the old path;
- ownership registry: **7 failures**, including known layer-heuristic, compressed-import, meta-facade, stale harness-scan, production-write-path parity, and producer-stamp pairing issues.

Before broad feature work, the repository should finish the documentation/path migration and return required governance/ownership lanes to green.

### 2. Long-session continuity beyond deterministic fixtures

Current evidence is strong for deterministic 25-turn social inquiry, snapshot/resume, and advisory 50-turn aggregate structure. It does not prove:

- live-model stability over 50+ turns;
- campaign continuity over days/weeks;
- semantic quality under unbounded player input;
- nightly stress behavior;
- recovery from partial model/API failures during long sessions.

### 3. Replay drift and corpus breadth

The protected short corpus is intentionally small. Exact prose is not hard-gated, and the long-session/direct-intrusion lanes remain supporting or advisory in several places. More corpus breadth is needed before replay can represent the diversity of actual play.

### 4. Feature-safe boundaries need broader pilot evidence

CB proved one safe and one caution pilot. The other safe/caution domains are classified but not equally exercised under real feature throughput. A few additional pilots would turn process confidence into empirical confidence.

### 5. Scheduler and world-event behavior

The world-simulation backbone deliberately defers:

- richer off-screen scheduling and cadence;
- temporal event orchestration;
- advanced faction planning;
- authored dependency graphs;
- duplicate faction identity cleanup.

These are major 1.0 capability gaps if the intended experience includes an independently evolving campaign world.

### 6. Persistence across real schema upgrades

The runtime envelope is ready for migrations, but the repository does not yet contain evidence from multiple shipped persistence versions across real patches. A playable 1.0 should prove:

- version-to-version migration;
- rollback when migration fails;
- preservation of long-running campaign state across releases;
- compatibility policy for authored scene/world content.

### 7. Maintenance drag and remaining hotspots

The project reduced several hotspots, especially the final-emission facade and test megastructures, but did not eliminate systemic cost.

Watch areas include:

- `game/final_emission_*`;
- visibility/fallback routing;
- `game/prompt_context.py` and CTIR/planner fan-in;
- social/interaction authority;
- replay projection and governance helpers;
- ownership-registry and generated audit contracts;
- large modules such as `game/interaction_context.py`, `game/api.py`, and `game/gm.py`.

Future work should prefer leaf-module changes with explicit owner tests rather than reopening orchestration hubs.

### 8. Recurrence program outcome evidence

The recurrence system can observe, classify, forecast, and prioritize. It has less evidence that remediation actually closes recurrence classes over time. Governance health, lifecycle closure, and effectiveness calibration remain below the program’s own targets.

### 9. Live operational telemetry

Speaker and fallback incidence are currently derived from artifact corpora, not representative live traffic. Before a 1.0 claim, the project would benefit from privacy-safe, session-level operational counters for:

- fallback selection;
- speaker mismatch/repair;
- retry escalation;
- semantic replacement;
- persistence recovery;
- long-session degradation.

## Missing or Incomplete Evidence

The following evidence would materially strengthen a future release-readiness retrospective:

1. A clean, dated full-suite run for the current 5,806-test tree.
2. Clean required governance lanes after the documentation reorganization.
3. Current CI run links or exported CI summaries for protected replay and strict audits.
4. Real full `tools/run_scenario_spine_validation.py --all-branches` artifacts using the intended model configuration.
5. A representative live-play corpus rather than only deterministic or archived artifact corpora.
6. A preserved pre-BW recurrence snapshot; BZ correctly reports that historical BW-to-BZ recurrence movement cannot be reconstructed without it.
7. Multi-version persistence migration fixtures from actual released schema versions.
8. Additional safe/caution feature pilots beyond the two CB pilots.
9. Post-baseline qualifying corrective fixes; CA cannot compare locality trends until at least five new CA1-qualified fixes exist.

## What Must Happen Before Comfortable Feature-First Development

The project does not need another broad stabilization crusade before any feature work. It does need a clean stop line:

1. Finish the current documentation/path reorganization and restore closeout test paths.
2. Resolve or explicitly rebaseline the seven current ownership-registry failures.
3. Produce and retain a clean full-suite run.
4. Keep protected replay green and preserve its manifest/registry checks.
5. Run at least one additional safe-domain and one additional caution-domain feature pilot.
6. Continue to block normal feature work in the five prohibited domains.
7. Establish the next long-session/live-play evidence target before changing routing, speaker, fallback, response-policy, or terminal-emission behavior.

After those steps, the project can safely operate in a **feature-first, boundary-aware** mode: normal development in safe domains, controlled development in caution domains, and maintenance-only work in prohibited domains.

## Final Assessment

### What has actually been accomplished since March?

The project has built much more than an AI narrator.

It has built:

- a persistent tabletop game state engine;
- structured exploration, social, non-combat, and limited combat resolution;
- authoritative clues, leads, projects, clocks, factions, scenes, and journals;
- a CTIR and planning architecture that separates meaning from prose;
- state, schema, visibility, persistence, and UI authority contracts;
- deterministic output legality and bounded repair systems;
- multi-turn and replay validation;
- speaker, fallback, and semantic-mutation governance;
- failure classification and attribution;
- recurrence and maintenance-economics measurement;
- test and documentation ownership;
- explicit feature-safety boundaries.

The March prototype could produce and persist an AI-mediated game experience. The June system can also inspect that experience, replay it, classify its failures, constrain its mutation points, identify ownership, and decide where future changes are safe.

That hidden infrastructure is the central accomplishment. It is what makes the difference between a clever prototype that works until it does not, and an internal-alpha system that can be maintained, audited, and improved without depending entirely on developer memory.

The work is not finished. Broad behavior surfaces remain expensive, current governance lanes need a clean closeout, live long-session evidence is thin, and a comfortable playable 1.0 still requires more real-session continuity, world scheduling, migration, and operational validation.

But the project has crossed an important threshold:

> It is no longer primarily trying to discover whether an AI GM can be made to work. It is now governing how that AI GM works, how failures are caught, and where future development can proceed without destabilizing the game.
