# CB Feature Boundary Readiness Audit Discovery

## Summary

This discovery pass classifies feature-readiness boundaries from live code shape, tests, ownership docs, and recent audit evidence. The safest feature domains appear to be localized authoring/evaluator/tooling surfaces: content lint, behavioral/playability evaluators, UI mode policy, model/config routing, and narrow combat/check modules. Caution domains include world/scene/affordance systems, prompt/CTIR/planning, state/storage, social/interaction, telemetry/diagnostics, and API/turn orchestration because they have high consumer counts or indirect replay/final-output effects. Prohibited domains for normal feature work are the current replay/final-emission/speaker/fallback/policy/sanitizer/repair cores and protected replay governance surfaces; changes there should require explicit audit approval or stabilization blocks.

Recent repo history supports that posture: `git log -n 30` is dominated by protected replay trend windows (BW/BZ), semantic mutation attribution (BY), speaker identity parity (BX), maintenance economics (BV), final-emission gate extraction (BJ/BN), fallback ownership compression (BK), replay projection simplification (BL), and recurrence/fallback incidence instrumentation (BQ/BP). The architecture ledger marks the same seams as governed/drift-watch rather than open feature areas.

No product code was modified and no tests were run for this discovery.

## Feature Readiness Matrix

| Domain | Paths | Classification: Safe / Caution / Prohibited | Evidence | Test Coverage | Replay / Golden Risk | Speaker / Policy / Fallback Risk | Recommended Feature Boundary |
|---|---|---|---|---|---|---|---|
| Content lint and validation tooling | `game/content_lint.py`, `game/scene_lint.py`, `game/validation.py`, `tools/run_content_lint.py` | Safe | Author-time deterministic pipeline per `docs/system_overview.md`; AST scan measured low-medium coupling for validation/lint/evaluators: 9 prod modules, fan-in 33, fan-out 11. | `tests/test_content_lint*.py`, `tests/test_scene_validation.py`, `tests/test_validation_coverage_*`, `tests/test_content_lint_tool.py`. | Low if kept author-time and not promoted into runtime replay assertions. | Low unless lint findings are wired into final emission, sanitizer, or policy enforcement. | New feature work acceptable when limited to author-time reports, scene diagnostics, or CLI output with focused tests. |
| Behavioral and playability evaluators | `game/behavioral_evaluators/*`, `game/playability_eval.py`, `tools/run_playability_validation.py` | Safe | Offline scoring/evaluation lane; ownership docs distinguish offline scoring from runtime policy. | `tests/test_behavioral_gauntlet_*`, `tests/test_intent_fulfillment_evaluator.py`, `tests/test_player_agency_evaluator.py`, `tests/test_session_cohesion_evaluator.py`, `tests/test_playability_eval.py`. | Low; normally advisory/report-only. | Low if outputs remain diagnostics and do not mutate response policy or final emission. | Features can extend evaluator metrics/reporting; avoid turning evaluator judgments into gate/fallback behavior. |
| UI mode policy and frontend shell | `static/*`, `game/ui_mode_policy.py`, `game/api_ui_mode.py` | Safe | Small measured domain: 2 prod modules, fan-in 4, fan-out 2; Objective 15 tests isolate UI mode. | `tests/test_ui_mode_policy.py`, `tests/test_ui_mode_backend_integration.py`, `tests/test_ui_mode_regression_matrix_objective15.py`, `tests/test_frontend_ui_mode_hardening_objective15.py`. | Low. | Low to moderate if API response shaping is touched. | Safe for frontend and UI-mode feature work behind existing API contracts. |
| Model/config/upstream availability routing | `game/config.py`, `game/models.py`, `game/model_routing.py`, `game/api_upstream_preflight.py`, `game/upstream_dependent_run_gate*.py` | Safe | Mostly configuration, adapters, and presentation; measured 6 prod modules, fan-in 39, fan-out 6. | `tests/test_model_routing_*.py`, `tests/test_api_upstream_preflight.py`, `tests/test_upstream_dependent_run_*`, `tests/test_startup_and_timestamps.py`. | Low unless routing changes alter deterministic replay behavior. | Moderate if upstream failures trigger fast fallback lanes. | Safe for configuration/presentation features; fallback-trigger semantics need caution guardrails. |
| Combat, conditions, skill checks, adjudication | `game/combat.py`, `game/conditions.py`, `game/skill_checks.py`, `game/noncombat_resolution.py`, `game/adjudication.py` | Safe | Local engine-resolution modules; measured 5 prod modules, fan-in 16, fan-out 10. | `tests/test_combat_resolution.py`, `tests/test_exploration_skill_checks.py`, `tests/test_skill_checks.py`, `tests/test_noncombat_resolution.py`, `tests/test_ctir_noncombat_consumption.py`. | Low to moderate because resolved outcomes can enter CTIR and prompt context. | Low unless social/adjudication query routing is changed. | New gameplay mechanics acceptable with normal focused tests plus CTIR/prompt tests when resolved-turn meaning changes. |
| World, scenes, affordances, clues, leads | `game/world*.py`, `game/scene_*.py`, `game/affordances.py`, `game/exploration.py`, `game/clues.py`, `game/leads.py`, `game/clocks.py`, `data/scenes/*`, `data/world.json` | Caution | Real runtime state and player options; measured 12 prod modules, fan-in 179, fan-out 43. `docs/system_overview.md` makes world progression a canonical seam. | `tests/test_world_*`, `tests/test_scene_*`, `tests/test_affordance_*`, `tests/test_clue_*`, `tests/test_lead_*`, `tests/test_exploration_resolution.py`. | Moderate; scene/world state affects replay observations, prompt context, and protected long-session fixtures. | Moderate through interaction context, social continuity, and fallback visible-fact selection. | Feature work should be narrow, data-backed, and include state/affordance/prompt or replay smoke probes when player-visible choices change. |
| State authority, storage, persistence, campaign/session reset | `game/state_authority.py`, `game/state_channels.py`, `game/storage.py`, `game/session.py`, `game/campaign_state.py`, `game/campaign_reset.py`, `game/defaults.py`, `game/persistence_contract.py`, `data/*.json` | Caution | Central persistence and authority guard layer; measured 8 prod modules, fan-in 284, fan-out 16, with `storage` FI 125 and `defaults` FI 105. Ledger marks state authority as registry + guard owner, not domain behavior owner. | `tests/test_state_authority.py`, `tests/test_state_channels.py`, `tests/test_save_load.py`, `tests/test_snapshots.py`, `tests/test_campaign_*`, `tests/test_runtime_persistence_regression_suite_obj14.py`. | Moderate to high because replay harnesses depend on stable reset/storage semantics. | Moderate through state publication, prompt context, and API orchestration. | Allow only scoped persistence/state features with rollback tests and replay-harness awareness; avoid broad schema or default-state churn without audit. |
| Prompt, CTIR, narrative planning, turn packet | `game/prompt_context*.py`, `game/ctir*.py`, `game/narrative_*.py`, `game/planner_*.py`, `game/turn_packet.py`, `game/narration_*` | Caution | Core resolved-turn/prompt adapter; measured 16 prod modules, fan-in 184, fan-out 73. `docs/system_overview.md` and ledger declare CTIR/prompt boundaries and warn against semantic co-ownership. | `tests/test_prompt_context*.py`, `tests/test_ctir_*.py`, `tests/test_narrative_*`, `tests/test_planner_*`, `tests/test_turn_packet_*`. | Moderate; CTIR and prompt changes can shift replay output and trend windows. | Moderate through response policy, final emission obligations, and narrative-mode constraints. | Feature work requires contract tests and narrow ownership framing; no silent semantic rewrites at prompt/final-emission boundary. |
| Social and interaction routing | `game/social*.py`, `game/interaction_*.py`, `game/dialogue_*.py` | Caution | High coupling: measured 13 prod modules, fan-in 260, fan-out 75; `interaction_context` FI 84. Social exchange emission is a governed seam in the ledger. | `tests/test_social*.py`, `tests/test_interaction_*`, `tests/test_dialogue_*`, `tests/test_broadcast_open_call_social.py`, `tests/test_directed_social_routing.py`. | High for protected replay because route, target, selected speaker, and strict-social outcomes are protected observation families. | High speaker/policy/fallback adjacency, especially strict social and fallback catalog paths. | Feature work should be guarded by direct-owner social tests plus protected replay probes when route/speaker/fallback fields can move. |
| API and turn pipeline orchestration | `game/api.py`, `game/api_turn_support.py`, `game/gm.py`, `game/gm_retry.py`, `run.py` | Caution | Very high fan-in/fan-out: measured 6 prod modules, fan-in 156, fan-out 101; `api` FI 65, `gm` FI 62. Touches runtime behavior, storage, prompt, finalization, retry, fallback, and model calls. | `tests/test_start_campaign_api.py`, `tests/test_api_*`, `tests/test_turn_pipeline_shared.py`, transcript/gauntlet suites. | High; E2E replay and transcript tests flow through this lane. | High because it chooses narration paths, retry/fallback, sanitizer/final-emission entrypoints, and post-emission adoption. | Normal feature work should avoid broad orchestration edits; prefer adding behavior in owned leaf modules and test API as downstream integration. |
| Telemetry, diagnostics, attribution, audit tooling | `game/stage_diff_telemetry.py`, `game/runtime_lineage_telemetry.py`, `game/observability_attribution_read.py`, `tools/*`, `scripts/*`, `docs/audits/*`, `artifacts/*` | Caution | Tooling is mostly report-only, but several diagnostics are tied to recurrence/trend measurements. Measured telemetry/tools bucket: 116 modules, fan-in 86, fan-out 152. | Many audit tests: `tests/test_*report*.py`, `tests/test_runtime_lineage_telemetry.py`, `tests/test_stage_diff_telemetry.py`, `tests/test_attribution_*`, `tests/test_bug_fix_locality_*`. | Moderate to high when metrics feed protected replay trend windows, recurrence history, or bug-locality measurements. | Moderate when attribution reads owner/fallback/policy metadata. | Safe for additive reports; caution for metric schema, history, or trend-window changes. Preserve append-only/history semantics. |
| Golden replay, protected replay, recurrence, drift governance | `tests/helpers/golden_replay*.py`, `tests/helpers/protected_replay_registry.py`, `tests/helpers/replay_*`, `tests/test_golden_replay*.py`, `tests/test_replay_*.py`, `docs/testing/protected_replay_manifest.md`, `tools/refresh_protected_replay_manifest.py`, `tools/run_protected_replay_trend.py` | Prohibited | Acceptance authority. Manifest declares 41 protected observation fields and the split between runtime projection and acceptance projection. Measured 44 replay/governance modules, fan-in 200, fan-out 150. Recent BW/BZ/BQ/BX/BY history is active stabilization. | `python -m pytest -m golden_replay -q`, `tests/test_golden_replay*.py`, `tests/test_protected_replay_registry.py`, `tests/test_replay_*`, BZ/BW tests. | Very high; changes can invalidate trend windows, protected observation schema, recurrence measurements, and CI acceptance. | High because protected fields include route, selected speaker, fallback, sanitizer, mutation, and final text. | Block normal feature work. Only audit-approved stabilization, additive reporting, or manifest-governed changes with explicit replay evidence. |
| Final emission core, metadata, runtime projection, terminal pipeline | `game/final_emission*.py` | Prohibited | Core final-output-critical path. Measured 52 prod modules, fan-in 527, fan-out 285. BV1 says final emission shifted into hubs: `final_emission_meta`, `strict_social_stack`, `terminal_pipeline`; ledger marks gate/repairs/meta as governed drift-watch. | `tests/test_final_emission*.py`, `tests/test_emission_smoke_assertions_contract.py`, `tests/test_ownership_registry.py`, golden replay downstream. | Very high; protected fields include final text, mutation lineage, final emitted source, fallback fields, sanitizer fields, and runtime lineage. | Very high; owns/consumes policy, repair, fallback, sanitizer, speaker observation, and final routing. | Block feature work unless the block is explicitly a stabilization/audit-approved final-emission change. Leaf tests are not enough without replay/ownership proof. |
| Fallback, sanitizer, upstream repairs | `game/fallback_behavior.py`, `game/fallback_provenance_debug.py`, `game/output_sanitizer.py`, `game/upstream_response_repairs.py`, `game/final_emission_*fallback*.py`, `game/opening_deterministic_fallback.py` | Prohibited | Fallback surface is actively measured and high-incidence. BV1 measured fallback area fan-in/fan-out 103/193, 69.16% fallback incidence on 107 FEM artifacts, and incomplete owner buckets. | `tests/test_fallback_*`, `tests/test_output_sanitizer.py`, `tests/test_upstream_response_repairs.py`, opening fallback tests, protected replay. | Very high; fallback family, owner bucket, sanitizer and opening fallback fields are protected observations. | Very high by definition: fallback, sanitizer, repair, and policy cash-out pathways. | Block normal feature work. Require stabilization block with before/after incidence, protected replay, and ownership evidence. |
| Speaker identity and post-emission adoption | `game/speaker_contract_enforcement.py`, `game/emitted_speaker_signature.py`, `game/post_emission_speaker_adoption.py` | Prohibited | Speaker finalize remains recent instability: BX parity and BT divergence audits; BV1 reports speaker projection drift frequency 8 protected rows. Measured 3 prod modules, fan-in 29, fan-out 16. | `tests/test_speaker_contract_*`, `tests/test_bx_speaker_identity_*`, `tests/test_block_s_*`, `tests/test_block_t_*`, protected replay speaker scenarios. | Very high; `selected_speaker_id` and social trace route/speaker fields are protected. | Very high for speaker identity, strict social, and post-emission mutation/adoption. | Block feature work. Changes need explicit speaker-identity audit approval and parity/golden replay evidence. |
| Response policy contracts/enforcement and policy mutation | `game/response_policy_contracts.py`, `game/response_policy_enforcement.py`, `game/response_policy_enforcement_manifest.py`, policy-adjacent prompt/gate consumers | Prohibited | Ledger marks response policy contracts/enforcement as governed drift-watch, with enforcement owning post-GPT mutation and strict-social bypass routing. Tests include mutation snapshots. | `tests/test_response_policy_contracts.py`, `tests/test_response_policy_enforcement_mutation.py`, `tests/test_response_delta_requirement.py`, downstream gate/social tests. | High; protected fields include response type requirements, repairs, and mutation lineage. | Very high; policy enforcement can mutate player-visible meaning and drive fallback/repair. | Block normal feature work; use audit-approved policy blocks only, with mutation snapshots and protected replay probes. |

## Safe Feature Domains

- Content lint and validation tooling: acceptable for author-time diagnostics, report fields, and scene lint rules when not wired into runtime output.
- Behavioral/playability evaluators: acceptable for advisory scoring, gauntlet summaries, and offline evaluation metrics.
- UI mode policy/frontend shell: acceptable for UI display/policy features that preserve API response contracts.
- Model/config/routing presentation: acceptable for configuration and upstream availability presentation; fallback-trigger semantics remain outside the safe boundary.
- Combat/check/condition mechanics: acceptable for localized mechanics with focused engine tests and CTIR/prompt probes when turn meaning changes.

## Caution Domains

- World/scene/affordance/clue/lead systems: broad player-visible state effects and replay fixture adjacency.
- State/storage/persistence/session reset: high fan-in and replay harness dependence.
- Prompt/CTIR/narrative planning/turn packet: resolved-turn meaning and prompt adapter boundaries can shift final text.
- Social/interaction/dialogue: high coupling and direct route/speaker/fallback adjacency.
- API/GM/turn orchestration: routes through almost every runtime-critical layer.
- Telemetry/diagnostics/audit tooling: mostly report-only, but metric schema/history changes can invalidate trend windows and recurrence analysis.

## Prohibited Domains

- Golden replay/protected replay/projection/recurrence/drift governance.
- Final emission gate, metadata, terminal pipeline, runtime projection, validators, repairs, and final text policy.
- Fallback, sanitizer, upstream response repairs, opening/sealed/visibility fallback ownership.
- Speaker identity, emitted speaker signature, and post-emission adoption.
- Response policy enforcement/contracts where changes can mutate player-visible meaning or response-delta requirements.

## Missing Evidence

- A fresh full architecture import/fan-in report committed for all domains, not just this AST spot check.
- Current `tests/TEST_AUDIT.md` and `tests/test_inventory_governance.json` refresh status for post-BZ test ownership.
- Per-domain recent failure/flake history, including skips/xfails separated from ordinary snapshot mentions.
- Fresh protected replay trend-window health after this audit date, including whether BZ movement classifications are now stable.
- Runtime traffic or representative replay incidence for speaker mismatch branches; BV1 notes this is not measured.
- Longitudinal fallback incidence beyond the first denominator-bearing BV1 snapshot.
- A machine-readable feature-boundary allow/block registry that future work can query before touching files.

## Recommended Next Blocks

| Block | Title | Purpose | Target files | Success condition | Primary metric impact |
|---|---|---|---|---|---|
| CB1 | Feature Boundary Registry | Convert this discovery into a machine-readable allow/caution/prohibit registry. | `docs/audits/CB_feature_boundary_readiness_discovery.md`, new `docs/audits/CB_feature_boundary_registry.json` or `tools/audits/*` | Every domain has owners, path globs, and required guardrails. | Feature Readiness increases by making boundaries enforceable. |
| CB2 | Safe Domain Pilot | Validate that one safe feature domain can accept additive work with normal tests. | `game/content_lint.py`, `tools/run_content_lint.py`, related tests | Additive diagnostic change lands without replay/final-emission/speaker surface changes. | Feature Readiness increases for low-risk feature throughput. |
| CB3 | Caution Guardrail Template | Define required probes for caution-domain changes. | `docs/testing/*`, `tests/README_TESTS.md`, candidate world/prompt/social tests | Each caution domain has a minimal test bundle and replay-smoke decision rule. | Feature Readiness improves through predictable review gates. |
| CB4 | Prohibited Domain Approval Gate | Establish explicit audit approval criteria for final emission/replay/speaker/fallback/policy changes. | `docs/audits/*`, `docs/testing/protected_replay_manifest.md`, `tests/README_TESTS.md` | Prohibited-domain changes require named audit approval, protected replay command, and metric-impact note. | Feature Readiness improves by preventing destabilizing feature churn. |
| CB5 | Metric Stability Inventory | Identify which reports/history files are trend-window sensitive. | `tools/*trend*`, `tools/*recurrence*`, `artifacts/golden_replay/*`, `docs/audits/BZ*` | Append-only and schema-sensitive artifacts have documented change rules. | Protects Feature Readiness by preserving measurement continuity. |
| CB6 | Speaker/Fallback Runtime Frequency Probe | Close BV1 missing evidence on representative frequency of speaker mismatch and fallback branches. | `tools/*fallback*`, `tests/helpers/golden_replay*`, `artifacts/golden_replay/*` | Report separates protected replay recurrence from representative runtime incidence. | Improves readiness classification confidence for high-risk domains. |
| CB7 | Ownership Drift Watch Refresh | Re-run ownership/import audits after BZ/CA changes and compare to BV1. | `scripts/bu_final_emission_coupling_discovery.py`, `tools/architecture_audit.py`, `docs/audits/BV1_maintenance_cost_matrix.md` | Updated fan-in/fan-out table shows whether hubs are stable, shrinking, or growing. | Improves Feature Readiness by detecting coupling drift before feature work. |

## Exact Commands Run

### Search commands

```powershell
Get-ChildItem -Force
rg --files
git status --short
Get-ChildItem game -File | Select-Object -ExpandProperty Name
Get-ChildItem tests -File | Select-Object -ExpandProperty Name
Get-ChildItem docs\audits -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name
Get-ChildItem docs -File | Select-Object -ExpandProperty Name
rg -n "^(from game|import game)" game tests tools scripts docs --glob "*.py" --glob "!artifacts/**"
rg -n "TODO|FIXME|xfail|skip\(|skipif|snapshot|golden|fragile" game tests docs audits --glob "*.py" --glob "*.md" --glob "!artifacts/**"
rg -n "final emission|final_emission|replay|golden|speaker|fallback|policy|sanitizer|repair|mutation|drift|trend window|Feature Readiness|prohibited|safe feature" docs docs\audits audits BZ*.md --glob "*.md" --glob "*.txt"
git log --oneline -n 30
Get-Content docs\architecture_ownership_ledger.md -TotalCount 240
Get-Content docs\system_overview.md -TotalCount 220
Get-Content docs\testing\protected_replay_manifest.md -TotalCount 180
Get-Content docs\audits\BV1_maintenance_cost_matrix.md -TotalCount 160
Get-Content docs/audits/discovery/docs\audits\discovery\BZ_protected_replay_trend_window_2_discovery.md -TotalCount 180
```

### Test discovery commands

```powershell
Get-ChildItem tests -File | Select-Object -ExpandProperty Name
rg -n "TODO|FIXME|xfail|skip\(|skipif|snapshot|golden|fragile" game tests docs audits --glob "*.py" --glob "*.md" --glob "!artifacts/**"
```

### Import / fan-out commands

The first attempt failed because `python` was not on PATH:

```powershell
@'
# AST import-count script omitted here for brevity; same script as below.
'@ | python -
```

Successful AST import/fan-in/fan-out measurement:

```powershell
@'
import ast
from pathlib import Path
files=list(Path('game').glob('**/*.py'))+list(Path('tests').glob('**/*.py'))+list(Path('tools').glob('**/*.py'))+list(Path('scripts').glob('**/*.py'))
modules={}
for p in files:
    if any(part in {'__pycache__'} for part in p.parts):
        continue
    mod='.'.join(p.with_suffix('').parts)
    modules[mod]=p
imports={m:set() for m in modules}
for m,p in modules.items():
    try:
        tree=ast.parse(p.read_text(encoding='utf-8'))
    except Exception:
        continue
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith(('game','tests','tools','scripts')):
                    imports[m].add(a.name)
        elif isinstance(n, ast.ImportFrom) and n.module:
            name=n.module
            if name.startswith(('game','tests','tools','scripts')):
                imports[m].add(name)
fan_in={m:0 for m in modules}
for m, outs in imports.items():
    for out in outs:
        for cand in modules:
            if out==cand or out.startswith(cand+'.'):
                fan_in[cand]+=1
                break
patterns={
 'API / turn pipeline':['game.api','game.api_turn_support','game.gm','game.gm_retry'],
 'Final emission core':['game.final_emission'],
 'Replay / golden governance':['tests.helpers.golden_replay','tests.helpers.protected_replay','tests.helpers.replay','tests.test_golden_replay','tests.test_replay','tools.refresh_protected_replay','tools.run_protected_replay'],
 'Speaker identity':['game.speaker','game.emitted_speaker','game.post_emission_speaker'],
 'Fallback / repairs / sanitizer':['game.fallback','game.final_emission_visibility_fallback','game.final_emission_sealed_fallback','game.final_emission_opening_fallback','game.opening_deterministic_fallback','game.upstream_response_repairs','game.output_sanitizer'],
 'Social / interaction':['game.social','game.interaction','game.dialogue'],
 'Prompt / CTIR / planning':['game.prompt','game.ctir','game.narrative','game.planner','game.turn_packet'],
 'World / scenes / affordances':['game.world','game.scene','game.affordances','game.exploration','game.clues','game.leads','game.clocks'],
 'State / storage / persistence':['game.storage','game.state','game.campaign','game.session','game.defaults','game.persistence'],
 'Combat / checks / conditions':['game.combat','game.conditions','game.skill_checks','game.noncombat','game.adjudication'],
 'Validation / lint / evaluators':['game.validation','game.content_lint','game.behavioral_evaluators','game.playability','game.narrative_authenticity_eval'],
 'Telemetry / diagnostics / audit tooling':['game.stage_diff','game.runtime_lineage','game.observability','tools.','scripts.'],
 'Frontend / UI mode':['game.api_ui_mode','game.ui_mode_policy'],
 'Model/config/routing':['game.models','game.model_routing','game.config','game.api_upstream_preflight','game.upstream_dependent_run_gate'],
}
for domain,prefs in patterns.items():
    mods=[m for m in modules if any(m.startswith(pref) for pref in prefs)]
    tests=[m for m in mods if m.startswith('tests.')]
    prod=[m for m in mods if m.startswith('game.')]
    total_fi=sum(fan_in.get(m,0) for m in mods)
    total_fo=sum(len(imports.get(m,set())) for m in mods)
    top=sorted(((fan_in.get(m,0), len(imports.get(m,set())), m) for m in mods), reverse=True)[:8]
    print(f'## {domain}')
    print(f'modules={len(mods)} prod={len(prod)} tests={len(tests)} fan_in={total_fi} fan_out={total_fo}')
    for fi,fo,m in top:
        print(f'  {m} FI={fi} FO={fo} path={modules[m]}')
'@ | & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -
```

### Tests run

No pytest tests were run. This was a discovery/audit pass only.
