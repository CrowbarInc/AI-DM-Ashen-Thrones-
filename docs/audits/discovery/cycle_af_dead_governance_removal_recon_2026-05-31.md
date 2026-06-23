# Cycle AF — Dead Governance Removal Recon

**Date:** 2026-05-31  
**Scope:** Reconnaissance only — no deletions, refactors, or manifest refreshes were performed.  
**Method:** Repo-wide glob for governance naming patterns; substring reference scan across text sources (excluding `codex_pytest_tmp/`); manual classification of clusters; CI/workflow and pytest touchpoint review.

---

## Executive Summary

- **Total governance artifacts found:** **~216** (206 filtered governance paths + ~10 generated audit artifact pairs under `artifacts/`)
- **Active authority:** **~42** — CI-hard-fail registries/closeouts, executable Python registries, protected replay manifest chain, primary ownership docs
- **Superseded:** **~28** — older cycle recons/closures and pre–Cycle K replay docs replaced by newer closeouts or `docs/testing/protected_replay_manifest.md`
- **Duplicate:** **~12** — parallel `docs/` vs `game/` copies, dual cycle-doc locations (`docs/reports/` vs `docs/cycles/` vs repo root), paired inventory+closeout docs where one is authoritative
- **Historical-only:** **~95** — cycle block notes, dated audits, surface inventories, failure-dashboard operationalization memos (context useful; not operationally authoritative)
- **Dead/unused:** **~25** — zero incoming references by filename/stem scan (listed below; several are recent closure docs with no back-links yet)
- **Unclear:** **~14** — advisory audit artifacts, `docs/post_evaluator_next_target_scan.md` (partially stale vs shipped CI), drift-prone `game/` doc copies
- **Top recommended contraction opportunities:**
  1. **Archive zero-ref failure-dashboard + Cycle G validation txt/memoes** under `audits/` (15 files) — no runtime/test/CI consumers.
  2. **Deduplicate `game/` mirror docs** (`state_authority_model.md` byte-identical; `validation_layer_separation.md` / `narrative_integrity_architecture.md` drifting) → single `docs/` authority.
  3. **Consolidate cycle closure storage** — move repo-root `cycle_ad_*` / `cycle_ae_*` into `docs/cycles/` and add a thin index in `docs/current_focus.md` instead of scattered closure files.
  4. **Retire documentary replay baselines** (`audits/golden_replay_baseline_2026-05-11.md`, `audits/golden_replay_readiness_2026-05-11.md`) after confirming `docs/testing/protected_replay_manifest.md` + `tools/refresh_protected_replay_manifest.py` cover all acceptance claims.
  5. **Fold `docs/ownership_cleanup_delta.md` AR18–AR19 snapshot** into `docs/architecture_ownership_ledger.md` navigation; treat the delta file as archive-only (currently 1 ref, self-referential).

---

## Artifact Inventory

### Legend

| Classification | Meaning |
| --- | --- |
| **Active authority** | Referenced by CI, pytest governance tests, runtime imports, or declared as canonical in `docs/current_focus.md` / `docs/convergence_ci_inventory.md` |
| **Superseded** | Replaced by a newer registry, closeout, manifest, or cycle |
| **Duplicate** | Substantial overlap with another artifact |
| **Historical-only** | Evidence / chronology; not enforced |
| **Dead/unused** | No references found outside self |
| **Unclear** | Needs human review before removal |

### Tier 1 — Machine-enforced governance (Active authority)

| Path | Type | Classification | Referenced By | Authority Claim | Notes |
| --- | --- | --- | --- | --- | --- |
| `tests/test_ownership_registry.py` | Python registry + pytest | Active authority | CI (`convergence-checks.yml`, `content-lint.yml`), `tests/test_inventory.json`, `tools/test_audit.py`, governance docs | Direct-owner map for test modules; blocks downstream suites claiming gate legality ownership | Consumes live `tests/test_inventory.json` |
| `tests/test_inventory.json` | JSON inventory | Active authority | `test_ownership_registry.py`, `tools/test_audit.py`, `TEST_AUDIT.md` | Schema v2 test inventory index | Regenerate via `py -3 tools/test_audit.py` |
| `tools/test_audit.py` | Tool | Active authority | CI content-lint, ownership tests, `TEST_AUDIT.md` | Regenerates inventory; static drift checks | Pair with ownership registry |
| `tests/validation_coverage_registry.py` | Python registry | Active authority | `test_validation_coverage_registry.py`, `test_validation_coverage_audit.py`, `tools/validation_coverage_audit.py` | Objective #12 feature→surface map | Governance/tooling only |
| `tools/validation_coverage_audit.py` | Tool | Active authority | CI hard-fail (`--strict`), `docs/convergence_ci_inventory.md` | Validates registry entries point at real tests/tools | |
| `game/contract_registry.py` | Python registry | Active authority | Runtime emission paths, `test_contract_registry*.py`, `test_emergency_fallback_registry_static_drift.py`, planner audit | Canonical prompt projection keys + emergency fallback ID sets | Metadata only; prevents schema drift |
| `game/validation_layer_contracts.py` | Python registry | Active authority | `validation_layer_audit.py`, ownership registry, runtime modules | Five-layer validation phase IDs | Leaf executable registry |
| `game/state_authority.py` | Python registry | Active authority | Runtime storage/API, `test_state_authority.py`, `docs/state_authority_model.md` | Domain guard registry | Executable authority |
| `docs/testing/protected_replay_manifest.md` | Manifest doc | Active authority | Golden replay helpers, Cycle AB/AC closeouts, Cycle K audits, refresh tool | PROTECTED/SUPPORTING/ADVISORY replay set + generated field paths | **Current replay acceptance doc of record** |
| `tools/refresh_protected_replay_manifest.py` | Tool | Active authority | Manifest doc, CI indirectly via replay gate | Regenerates protected field path section | `--check` suitable for CI promotion |
| `tests/helpers/golden_replay_projection.py` | Python projection | Active authority | `test_golden_replay.py`, manifest, failure dashboard | `protected_field_paths()` source of truth for manifest generation | |
| `tests/helpers/golden_replay.py` | Python harness | Active authority | `test_golden_replay.py`, failure dashboard, protected replay docs | Drift evaluation + protected expectation helpers | 21 active refs (tests+runtime touch via imports) |
| `tests/helpers/golden_replay_fixtures.py` | Python fixtures | Active authority | `test_golden_replay.py`, Cycle AC closure | Scenario seed/harness extraction (AC-1+) | |
| `tests/test_golden_replay.py` | Pytest | Active authority | CI `-m golden_replay`, manifest | Protected + supporting replay scenarios | Executable acceptance gate |
| `docs/convergence_ci_inventory.md` | CI inventory | Active authority | `convergence-checks.yml` comments, closeout docs, `run_governance_audits.py` | Maps closed seams → pytest/audit steps | **CI parity doc of record** |
| `.github/workflows/convergence-checks.yml` | CI config | Active authority | Entire convergence closeout chain | Hard-fail governance enforcement | |
| `docs/evaluator_convergence_closeout.md` | Closeout | Active authority | CI, `test_evaluator_convergence_closeout.py`, convergence inventory | Evaluator maintenance-grade freeze | |
| `tests/test_evaluator_convergence_closeout.py` | Pytest closeout | Active authority | CI hard-fail | Locks evaluator convergence invariants | |
| `docs/gate_convergence_closeout.md` | Closeout | Active authority | CI, `test_gate_convergence_closeout.py`, Cycle AB closure | Gate maintenance-grade freeze | |
| `tests/test_gate_convergence_closeout.py` | Pytest closeout | Active authority | CI hard-fail | Gate convergence snapshot tests | |
| `docs/final_emission_ownership_convergence.md` | Closeout | Active authority | FE boundary tests, `final_emission_ownership_audit.py`, runtime docstrings | FE-C2 ownership doctrine | |
| `tools/final_emission_ownership_audit.py` | Tool | Active authority | CI `--strict`, convergence inventory | Advisory→strict ownership drift signals | |
| `docs/validation_layer_separation.md` | Contract doc | Active authority | Validation layer audit, ownership ledger, CI inventory | Objective #11 phase ownership | **Canonical path** (`docs/`) |
| `tools/validation_layer_audit.py` | Tool | Active authority | CI `--strict`, smoke tests | Static layer drift detection | |
| `docs/architecture_ownership_ledger.md` | Ledger | Active authority | `current_focus.md`, ownership registry docs, architecture audit | Runtime→test ownership routing | Primary human ownership map |
| `docs/narrative_integrity_architecture.md` | Architecture doc | Active authority | `current_focus.md`, TEST_CONSOLIDATION_PLAN, convergence inventory | Emit-path module map + consolidation rules | **Canonical path** |
| `docs/state_authority_model.md` | Authority doc | Active authority | Runtime modules, ledger, state tests | Unified state domain contract | **Canonical path** |
| `tests/TEST_AUDIT.md` | Test governance doc | Active authority | Ownership registry, consolidation plan, CI inventory | Test routing / RT* decisions | |
| `tests/TEST_CONSOLIDATION_PLAN.md` | Test governance doc | Active authority | Ownership registry, `current_focus.md` | Overlap / smoke discipline | |
| `docs/current_focus.md` | Focus / navigation | Active authority | README, testing docs, architecture audits | Completed vs active consolidation targets | Operator entry point |

### Tier 2 — Advisory / informational governance (Mixed: Active doc + Informational enforcement)

| Path | Type | Classification | Referenced By | Authority Claim | Notes |
| --- | --- | --- | --- | --- | --- |
| `tools/run_governance_audits.py` | Meta-runner | Active authority (informational tier) | `convergence_ci_inventory.md`, CI continue-on-error steps | Bundles architecture + realization + C1 + UI audits | Non-blocking in CI |
| `tools/architecture_audit.py` + `artifacts/architecture_audit/*` | Audit + artifact | Active authority (informational) | CI, `test_architecture_audit_tool.py` | Broad architecture heuristics | Generated JSON/MD refreshed by tool |
| `tools/realization_layer_audit.py` + artifacts | Audit + artifact | Unclear → Informational | CI, realization tests/docs | Realization surface intent | Not hard-fail |
| `tools/realization_provenance_audit.py` + artifacts | Audit + artifact | Unclear → Informational | CI, provenance tests/docs | Failure locality / provenance | Pairs with triage ledger doc |
| `docs/realization_failure_locality_closeout.md` | Closeout | Historical-only (doc) / Informational (tool chain) | Realization audits, triage ledger | Failure locality freeze narrative | No dedicated CI pytest slice |
| `docs/realization_triage_ledger.md` | Ledger | Historical-only | Realization closeout, audits | Triage routing chronology | Superseded in practice by closeout + audits |
| `docs/evaluator_convergence_inventory.md` | Inventory | Duplicate / Historical-only | Closeout doc, convergence inventory | Evaluator seam listing | **Narrower duplicate** of closeout + CI inventory |
| `docs/gate_cleanup_inventory.md` | Inventory | Duplicate / Active pointer | Gate closeout, Cycle AB closure, runtime doc sync | Gate hotspot inventory | Still updated by recent cycles; merge candidate into gate closeout |
| `docs/planner_convergence.md` | Closeout doc | Active authority | `content-lint.yml`, planner audit/tests | Planner convergence freeze | Lives in **content-lint**, not convergence-checks |
| `tools/planner_convergence_audit.py` | Tool | Active authority | `content-lint.yml` | Planner static audit | Do not duplicate in convergence-checks |
| `game/planner_input_manifest.py` | Python manifest | Active authority | Planner convergence tests/audit | Planner input key registry | Runtime metadata |
| `game/response_policy_enforcement_manifest.py` | Python manifest | Active authority | Response policy tests | Enforcement surface manifest | Runtime metadata |
| `game/realization_provenance.py` | Runtime module | Active authority | Golden replay projection, runtime FEM | Governed provenance taxonomy | Not a “doc artifact” but governs replay projection |
| `game/realization_authority.py` | Runtime module | Active authority | Realization tests/runtime | Realization authority seam | |
| `game/narrative_authority.py` | Runtime module | Active authority | Narrative authority tests | Narrative authority rules | |
| `docs/post_evaluator_next_target_scan.md` | Planning scan | Superseded / Unclear | Essentially self + architecture artifact | Recommended CI parity block | **Partially stale** — CI parity largely landed in `convergence_ci_inventory.md` + workflow |
| `docs/ownership_cleanup_delta.md` | Chronicle | Historical-only | Self-referential (1 ref) | AR18–AR19 ownership delta history | Explicitly “historical evidence”; navigation header points to ledger |

### Tier 3 — Cycle / audit documentary artifacts (mostly Historical-only)

| Path pattern | Count (approx) | Classification | Referenced By | Notes |
| --- | ---: | --- | --- | --- |
| `docs/cycles/cycle_*_{recon,closure}_*.md` | 35 | Historical-only | Cross-cycle citations, occasional closeout chains | Canonical **recent** closures: AB, AC, AD, AE, AA, S, T, U, O, P, N, M, L, J, I, H |
| `docs/cycles/cycle_*_{recon,closure}_*.md` | 6 | Historical-only / Duplicate location | Same as above | **Newer home** for AA, AB, AC, S cycles — prefer this over scattered copies |
| `docs/audits/cycle_k_block_k*.md` | 7 | Historical-only | Cycle K recon, protected replay promotion | Led to manifest + CI replay gate |
| `audits/cycle_{c,d,e,f,g,q}_*.md` | ~45 | Historical-only / Superseded | Older cycle cross-refs | Pre–Cycle K fallback/ownership thinning evidence |
| `audits/*_surface_inventory_*.md` | 5 | Historical-only | Failure dashboard era docs | Superseded by later cycle closeouts + classifier tests |
| `audits/failure_dashboard_*.md` (except `failure_dashboard_latest.md`) | 10 | Dead/unused (9 zero-ref) | Failure classifier tests reference **helpers**, not these memos | Safe archive candidates |
| `audits/failure_owner_matrix.md` | Matrix | Historical-only | Classifier / cycle docs | Owner routing reference, not CI-enforced |
| `audits/replay_failure_corpus.md` | Corpus doc | Historical-only | Replay/cycle docs | Diagnostic corpus, not manifest |
| `audits/golden_replay_baseline_2026-05-11.md` | Baseline doc | Superseded | Manifest declares it “documentary baseline” | **Superseded by** `protected_replay_manifest.md` for acceptance |
| `audits/golden_replay_readiness_2026-05-11.md` | Readiness doc | Superseded | Realization audit artifact refs | Pre-promotion checklist |
| Root `cycle_ad_*`, `cycle_ae_*` | 4 | Historical-only / Duplicate location | AD closure links recon by relative path | Should live under `docs/cycles/` for consistency |
| `docs/cycles/cycle_r_*.md` | 7 | Historical-only | Cycle R recon cross-refs | Test fanout / inventory refresh block notes |
| `docs/cycles/cycle_ad_test_authority_consolidation_closure_2026-05-31.md` | Closeout | Historical-only (zero back-ref) | Linked from recon only | **Authoritative AD narrative** but not linked from index docs yet |

### Tier 4 — Duplicate `game/` documentation copies

| Path | Type | Classification | Referenced By | Authority Claim | Notes |
| --- | --- | --- | --- | --- | --- |
| `game/state_authority_model.md` | Doc copy | Duplicate | **None** (all refs use `docs/state_authority_model.md`) | Same title as docs copy | **Byte-identical** to `docs/` — safe delete candidate after redirect grep |
| `game/validation_layer_separation.md` | Doc copy | Duplicate (drifting) | Self + docs cross-links only | Claims canonical but points at `docs/` paths | **485 bytes shorter** than docs copy — drift risk |
| `game/narrative_integrity_architecture.md` | Doc copy | Duplicate (drifting) | Self references | Parallel architecture map | **209 bytes shorter** than docs copy — drift risk |

---

## Duplicate / Superseded Clusters

### 1. Final emission authority

| Item | Detail |
| --- | --- |
| **Governance topic** | Final emission orchestration, boundary, ownership |
| **Files involved** | `docs/final_emission_ownership_convergence.md`, `docs/final_emission_boundary_audit.md`, `docs/final_emission_gate_reduction_plan.md`, `docs/gate_convergence_closeout.md`, `docs/gate_cleanup_inventory.md`, `tests/test_final_emission_gate.py`, `tools/final_emission_ownership_audit.py` |
| **Current apparent authority** | Runtime: `game/final_emission_gate.py`; tests: `tests/test_final_emission_gate.py`; doctrine: `final_emission_ownership_convergence.md`; CI: boundary tests + ownership audit |
| **Superseded/duplicate candidates** | `final_emission_gate_reduction_plan.md` (planning), `final_emission_boundary_audit.md` (pre-closeout audit), much of `gate_cleanup_inventory.md` post–Cycle AB |
| **Evidence** | Cycle AB closure explicitly freezes topology; gate closeout declares maintenance grade; CI inventory hard-fails FE-C2 slice |
| **Risk** | **Medium** — pruning gate inventory rows could drop useful hotspot notes |

### 2. Fallback ownership / provenance / topology

| Item | Detail |
| --- | --- |
| **Governance topic** | Fallback families, provenance stamps, topology collapse |
| **Files involved** | `docs/testing/protected_replay_manifest.md`, `game/realization_provenance.py`, `game/diegetic_fallback_narration.py`, `docs/cycles/cycle_ab_fallback_topology_collapse_closure_2026-05-31.md`, `docs/cycles/cycle_ab_fallback_topology_collapse_recon_2026-05-31.md`, `audits/opening_fallback_surface_inventory_2026-05-11.md`, `audits/cycle_e_*fallback*` (8+ files) |
| **Current apparent authority** | Manifest (AB3/AB6 sections) + projection code; runtime dual-field contract |
| **Superseded/duplicate candidates** | All Cycle E/F opening-fallback audit memos; surface inventories under `audits/*_surface_inventory_*` |
| **Evidence** | AB closure lists completed blocks; manifest updated for dual-family + sealed sub-kind projection |
| **Risk** | **Low** for archive of pre-AB audit memos; **High** for manifest/projection code |

### 3. Replay protection / golden replay

| Item | Detail |
| --- | --- |
| **Governance topic** | Protected replay acceptance |
| **Files involved** | `docs/testing/protected_replay_manifest.md`, `tests/test_golden_replay.py`, `tests/helpers/golden_replay*.py`, `tools/refresh_protected_replay_manifest.py`, `audits/golden_replay_baseline_2026-05-11.md`, `docs/audits/cycle_k_block_k1_protected_replay_declaration_2026-05-26.md`, `docs/audits/cycle_k_replay_promotion_recon_2026-05-26.md` |
| **Current apparent authority** | Manifest + pytest `-m golden_replay` + refresh tool |
| **Superseded/duplicate candidates** | `golden_replay_baseline_2026-05-11.md`, `golden_replay_readiness_2026-05-11.md`, Cycle K block docs (historical promotion evidence) |
| **Evidence** | Manifest header cites baseline as “documentary” only; Cycle AC closure states manifest bytes unchanged |
| **Risk** | **Low** for archiving baseline docs; **High** for manifest/tests |

### 4. Test ownership / inventory registry

| Item | Detail |
| --- | --- |
| **Governance topic** | Test direct-owner registry |
| **Files involved** | `tests/test_ownership_registry.py`, `tests/test_inventory.json`, `tools/test_audit.py`, `tests/TEST_AUDIT.md`, `tests/TEST_CONSOLIDATION_PLAN.md`, `tests/README_TESTS.md`, `docs/architecture_ownership_ledger.md`, `docs/cycles/cycle_ad_test_authority_consolidation_{recon,closure}_2026-05-31.md` |
| **Current apparent authority** | Live trio: ownership registry test + inventory JSON + test_audit tool |
| **Superseded/duplicate candidates** | Cycle L recon/closure (compression narrative), Cycle R block notes (inventory refresh evidence) |
| **Evidence** | `current_focus.md` marks Block D complete; CI hard-fails ownership registry in two workflows |
| **Risk** | **High** for registry trio; **Low** for archiving Cycle L/R markdown evidence |

### 5. Validation coverage / contract registries

| Item | Detail |
| --- | --- |
| **Governance topic** | Objective #12 coverage map + contract key drift |
| **Files involved** | `tests/validation_coverage_registry.py`, `game/contract_registry.py`, `docs/objective12_validation_contract.md`, `tests/test_validation_coverage_registry.py`, `tests/test_contract_registry_static_drift.py`, `tests/test_emergency_fallback_registry_static_drift.py` |
| **Current apparent authority** | Python registries + strict audit tools |
| **Superseded/duplicate candidates** | `objective12_validation_contract.md` if fully mirrored in registry module docstring |
| **Evidence** | CI hard-fails validation coverage audit; contract registry imported by emission + planner audits |
| **Risk** | **High** |

### 6. CI / convergence seam mapping

| Item | Detail |
| --- | --- |
| **Governance topic** | Which closeouts are CI-enforced |
| **Files involved** | `docs/convergence_ci_inventory.md`, `.github/workflows/convergence-checks.yml`, `.github/workflows/content-lint.yml`, `docs/post_evaluator_next_target_scan.md` |
| **Current apparent authority** | `convergence_ci_inventory.md` + workflows |
| **Superseded/duplicate candidates** | `post_evaluator_next_target_scan.md` (CI parity recommendation largely implemented) |
| **Evidence** | Workflow steps match inventory matrix; post-evaluator doc still claims only 3 CI checks |
| **Risk** | **Low** to archive stale scan after header update |

### 7. Cycle closure doc locations (same cycle, multiple paths)

| Item | Detail |
| --- | --- |
| **Governance topic** | Cycle closeout status |
| **Files involved** | `docs/cycles/cycle_ab_fallback_topology_collapse_closure_2026-05-31.md` **and** `docs/cycles/cycle_ab_fallback_topology_collapse_recon_2026-05-31.md`; AD/AE at repo root vs AC/AA under `docs/cycles/` |
| **Current apparent authority** | Newest closure doc per cycle (AB→reports closure; AC→cycles closure) |
| **Superseded/duplicate candidates** | Recon docs after closure (keep one recon + one closure per cycle); inconsistent folder placement |
| **Evidence** | AB recon in `docs/cycles/`, AB closure in `docs/reports/` — asymmetric |
| **Risk** | **Low** for consolidation; **Medium** if links break in external notes |

### 8. Failure dashboard / classifier governance

| Item | Detail |
| --- | --- |
| **Governance topic** | Failure classification & dashboard contracts |
| **Files involved** | `tests/helpers/failure_dashboard_report.py`, `tests/helpers/failure_classifier.py`, `tests/test_failure_classifier.py`, `audits/failure_dashboard_latest.md`, 10+ zero-ref `audits/failure_dashboard_*` memos |
| **Current apparent authority** | Test helpers + `failure_dashboard_latest.md` (operational snapshot) |
| **Superseded/duplicate candidates** | Cycle B–F failure dashboard operationalization memos (zero refs) |
| **Evidence** | Classifier tests import helpers, not audit memos; `failure_dashboard_latest.md` still referenced |
| **Risk** | **Low** for zero-ref memos; **Medium** for `failure_dashboard_latest.md` |

### 9. State / validation doc mirrors in `game/`

| Item | Detail |
| --- | --- |
| **Governance topic** | Maintainer-facing architecture contracts |
| **Files involved** | `docs/state_authority_model.md`, `docs/validation_layer_separation.md`, `docs/narrative_integrity_architecture.md` vs `game/*.md` copies |
| **Current apparent authority** | **`docs/` paths only** — all runtime/test imports reference `docs/...` in comments |
| **Superseded/duplicate candidates** | All three `game/*.md` copies |
| **Evidence** | Zero imports of `game/state_authority_model.md`; hash compare shows exact duplicate (state) and drift (others) |
| **Risk** | **Low** for identical copy; **Medium** for drifting copies (may confuse editors) |

---

## Likely Removal or Consolidation Candidates

| Path | Candidate Action | Risk | Evidence | Why This Should Wait For ChatGPT |
| --- | --- | --- | --- | --- |
| `game/state_authority_model.md` | Delete (duplicate) | Low | Byte-identical to `docs/`; 0 unique refs | Confirm no external bookmarks; add single canonical pointer if any script globbed `game/*.md` |
| `game/validation_layer_separation.md` | Delete or merge → `docs/` | Medium | Drifting duplicate; docs version longer | Diff drift content — may contain accidental unique edits |
| `game/narrative_integrity_architecture.md` | Delete or merge → `docs/` | Medium | Drifting duplicate | Same as above |
| `audits/failure_dashboard_contract_lock_2026-05-11.md` | Archive | Low | 0 refs | Batch with other failure_dashboard memos |
| `audits/failure_dashboard_cycle_b_closure_2026-05-11.md` | Archive | Low | 0 refs | Historical Cycle B evidence |
| `audits/failure_dashboard_final_integration_audit_2026-05-11.md` | Archive | Low | 0 refs | Superseded by classifier tests |
| `audits/failure_dashboard_operationalization_2026-05-11.md` | Archive | Low | 0 refs | |
| `audits/failure_dashboard_probe_harness_2026-05-11.md` | Archive | Low | 0 refs | |
| `audits/failure_dashboard_sample.md` | Archive | Low | 0 refs | |
| `audits/failure_locality_assessment.md` | Archive | Low | 0 refs | Realization closeout supersedes intent |
| `audits/post_gate_sanitizer_rewrite_surface_inventory_2026-05-12.md` | Archive | Low | 0 refs | Cycle L/G work absorbed elsewhere |
| `audits/cycle_g_block{1,2,3}_full_suite_validation_20260519.txt` | Archive | Low | 0 refs | Raw test logs |
| `audits/cycle_g_runtime_stability_suite_hygiene_recon_20260518.md` | Archive | Low | 0 refs | |
| `audits/cycle_g_tracked_runtime_snapshot_churn_recon_20260519.md` | Archive | Low | 0 refs | |
| `audits/cycle_f_opening_projection_fixture_helper_recon_20260518.md` | Archive | Low | 0 refs | AC harness extraction superseded |
| `audits/cycle_f_routing_policy_decision_memo_20260518.md` | Archive | Low | 0 refs | |
| `audits/cycle_e_test_signal_ownership_thinning_closure_2026-05-17.md` | Archive | Low | 0 refs | Cycle AD/L supersede ownership narrative |
| `audits/golden_replay_baseline_2026-05-11.md` | Archive | Low | Manifest cites as documentary only | Verify no human runbooks still point here exclusively |
| `audits/golden_replay_readiness_2026-05-11.md` | Archive | Low | 4 doc refs only | Update refs to manifest |
| `docs/post_evaluator_next_target_scan.md` | Archive or supersede header | Low | Stale CI claim; 2 refs | Merge still-useful GPT-layer ranking into a living doc |
| `docs/ownership_cleanup_delta.md` | Archive (keep AR18–19 excerpt in ledger) | Medium | 1 ref; large historical file | Ensure AR18–19 snapshot preserved in ledger before move |
| `docs/evaluator_convergence_inventory.md` | Merge → closeout + CI inventory | Low | 4 refs; narrow duplicate | Avoid losing seam table rows |
| `docs/cycles/cycle_t_maintenance_locality_reduction_closure_2026-05-30.md` | Move/index under `docs/cycles/` | Low | 0 back-refs | Folder consistency only |
| Root `cycle_ad_*`, `cycle_ae_*` (4 files) | Move → `docs/cycles/` | Low | Closure zero back-refs | Fix relative links in AD closure |
| `docs/cycles/cycle_r_block_r{1b,1c,r2,r3}_*.md` | Archive | Low | 0 refs each | Block-complete notes |
| `docs/cycles/cycle_aa_gate_authority_extraction_closure_2026-05-31.md` | Keep but index | Low | 0 back-refs | Recent closure — add to cycle index, don’t delete |
| `docs/cycles/cycle_ac_replay_surface_compression_closure_2026-05-31.md` | Keep but index | Low | 0 back-refs | Authoritative AC narrative |

---

## Tests / Runtime Touchpoints

Governance artifacts with **direct runtime or CI enforcement**:

| Enforcement surface | Governance artifacts consumed |
| --- | --- |
| **CI `convergence-checks.yml`** | Protected replay manifest path, evaluator/gate closeout tests, FE boundary tests, validation layer audit, validation coverage audit, ownership registry, governance audit runner |
| **CI `content-lint.yml`** | Planner convergence audit, ownership registry, test inventory regeneration checks |
| **Pytest `-m golden_replay`** | `protected_replay_manifest.md`, `golden_replay*.py` helpers, scenario fixtures |
| **`tests/test_ownership_registry.py`** | `test_inventory.json`, embedded registry constants, `validation_layer_contracts` |
| **`tests/test_contract_registry*.py`** | `game/contract_registry.py` emergency fallback + planner key sets |
| **`tests/test_validation_coverage_registry.py`** | `validation_coverage_registry.py` entry schema |
| **`tests/test_*_convergence_closeout.py`** | Matching closeout markdown contracts |
| **`tests/test_architecture_audit_tool.py`** | `artifacts/architecture_audit/architecture_audit.json` |
| **`tests/test_realization_*_audit.py`** | Realization audit artifacts |
| **`tests/test_failure_classifier.py` / dashboard helpers** | Classifier contract (not audit memos); writes/reads `audits/failure_dashboard_latest.md` in some flows |
| **Runtime imports** | `contract_registry.py`, `validation_layer_contracts.py`, `state_authority.py`, `realization_provenance.py`, planner/response policy manifests |

---

## Files To Pass Back To ChatGPT

### Required

- `docs/cycle_af_dead_governance_removal_recon_2026-05-31.md` (this report)
- `docs/convergence_ci_inventory.md` (CI authority map)
- `docs/architecture_ownership_ledger.md` (ownership routing)
- `docs/testing/protected_replay_manifest.md` (replay acceptance)
- `tests/test_ownership_registry.py` + `tests/test_inventory.json` + `tools/test_audit.py`
- `tests/validation_coverage_registry.py` + `tools/validation_coverage_audit.py`
- `game/contract_registry.py`
- Closeout trio: `docs/evaluator_convergence_closeout.md`, `docs/gate_convergence_closeout.md`, `docs/final_emission_ownership_convergence.md`
- `.github/workflows/convergence-checks.yml`

### Useful if available

- `docs/current_focus.md` (active vs completed consolidation)
- `docs/narrative_integrity_architecture.md`, `docs/validation_layer_separation.md`, `docs/state_authority_model.md`
- `docs/cycles/cycle_ad_test_authority_consolidation_closure_2026-05-31.md`, `docs/cycles/cycle_ac_replay_surface_compression_closure_2026-05-31.md`, `docs/cycles/cycle_ab_fallback_topology_collapse_closure_2026-05-31.md`
- `tests/TEST_AUDIT.md`, `tests/TEST_CONSOLIDATION_PLAN.md`
- Duplicate candidates: `game/state_authority_model.md`, `game/validation_layer_separation.md`, `game/narrative_integrity_architecture.md`
- Zero-ref archive batch listing (§Likely Removal) for block generation

### Only needed if there is ambiguity

- `docs/ownership_cleanup_delta.md` (AR18–AR19 historical snapshot — large)
- `docs/post_evaluator_next_target_scan.md` (stale vs current CI)
- `docs/gate_cleanup_inventory.md` vs `docs/gate_convergence_closeout.md` diff
- `audits/failure_dashboard_latest.md` vs zero-ref failure_dashboard memos
- Drift diff between `docs/` and `game/` validation_layer / narrative_integrity copies

---

## Recommended Next Blocks

ChatGPT could generate these **implementation blocks** next (not executed in Cycle AF):

1. **Block AF-1 — Zero-ref audit archive pack**  
   Move the 15 zero-ref `audits/failure_dashboard_*`, Cycle G txt/logs, and selected Cycle E/F memos to `docs/archive/cycles/` with a one-page index; no content edits inside archived files.

2. **Block AF-2 — Canonical doc dedupe (`game/` mirrors)**  
   Diff `game/validation_layer_separation.md` and `game/narrative_integrity_architecture.md` against `docs/`; port any unique lines; delete mirrors; add CI/content-lint grep guard banning new `game/*.md` architecture copies.

3. **Block AF-3 — Cycle closure index + folder normalization**  
   Create `docs/cycles/README.md` listing AA→AE closures with status; relocate root `cycle_ad_*` / `cycle_ae_*` into `docs/cycles/`; fix relative links; add backlinks from `docs/current_focus.md`.

4. **Block AF-4 — Replay documentary retirement**  
   Update `protected_replay_manifest.md` to drop “documentary baseline” pointer or replace with internal history link; archive `audits/golden_replay_baseline_2026-05-11.md` and `golden_replay_readiness_2026-05-11.md`; grep-update remaining refs.

---

## Validation

Recon-only constraint verified:

```text
git status --short docs/cycle_af_dead_governance_removal_recon_2026-05-31.md
```

Expected: only the new recon report is an intentional addition. Temporary local scanner scripts (`_recon_ref_scan.py`, `_recon_analyze.py`, `_recon_ref_scan.json`) were used for analysis and should **not** be committed.

---

## AF-1 Archive Applied (2026-05-31)

**Block:** AF-1 — Low-risk dead governance archive  
**Archive location:** `docs/archive/dead_governance/2026-05-31/`  
**Index:** `docs/archive/dead_governance/2026-05-31/README.md`

### Files archived (16)

Moved from `audits/` → archive (git mv, content unchanged):

1. `failure_dashboard_contract_lock_2026-05-11.md`
2. `failure_dashboard_cycle_b_closure_2026-05-11.md`
3. `failure_dashboard_final_integration_audit_2026-05-11.md`
4. `failure_dashboard_operationalization_2026-05-11.md`
5. `failure_dashboard_probe_harness_2026-05-11.md`
6. `failure_dashboard_sample.md`
7. `failure_locality_assessment.md`
8. `post_gate_sanitizer_rewrite_surface_inventory_2026-05-12.md`
9. `cycle_g_block1_full_suite_validation_20260519.txt`
10. `cycle_g_block2_full_suite_validation_20260519.txt`
11. `cycle_g_block3_full_suite_validation_20260519.txt`
12. `cycle_g_runtime_stability_suite_hygiene_recon_20260518.md`
13. `cycle_g_tracked_runtime_snapshot_churn_recon_20260519.md`
14. `cycle_f_opening_projection_fixture_helper_recon_20260518.md`
15. `cycle_f_routing_policy_decision_memo_20260518.md`
16. `cycle_e_test_signal_ownership_thinning_closure_2026-05-17.md`

### Files intentionally not touched

- **Do-not-modify guard list** (convergence CI inventory, ownership ledger, protected replay manifest, registries, closeouts, workflows, runtime, test semantics)
- `audits/failure_dashboard_latest.md` (operational snapshot — still referenced)
- `audits/golden_replay_baseline_2026-05-11.md`, `audits/golden_replay_readiness_2026-05-11.md` → **AF-4**
- `game/state_authority_model.md`, `game/validation_layer_separation.md`, `game/narrative_integrity_architecture.md` → **AF-2**
- `docs/cycles/cycle_ad_*` / `docs/cycles/cycle_ae_*` (normalized in AF-3), recent cycle closures under `docs/cycles/` → **AF-3**
- `docs/cycles/cycle_r_block_r*.md`, `docs/post_evaluator_next_target_scan.md`, `docs/ownership_cleanup_delta.md` (non-zero-ref or medium risk)

### Validation commands run

```bash
python -m pytest tests/test_ownership_registry.py -q          # 17 passed
python -m pytest tests/test_validation_coverage_audit.py -q   # 5 passed
python tools/validation_coverage_audit.py --strict            # exit 0, registry validation OK
python -m pytest tests/test_golden_replay.py -q               # 59 passed (~15s)
python -m pytest -m golden_replay -q                          # SKIPPED — collection error in unrelated module (test_narration_transcript_regressions import); fixed in AF-1B
```

### Remaining recommended blocks

- **AF-2** — Canonical doc dedupe (`game/` mirror docs)
- **AF-3** — Cycle closure index + folder normalization
- **AF-4** — Replay documentary retirement (baseline/readiness docs + manifest pointer)

---

## AF-1B Collection Repair (2026-05-31)

**Block:** AF-1B — Restore pytest collection for `-m golden_replay`

### Root cause

`tests/test_narration_transcript_regressions.py` imported `_response_type_contract` from `tests/test_fallback_behavior_gate.py`. That private helper was **removed during Cycle R Block R1-B** when shared gate fixtures moved to `tests/helpers/final_emission_gate_fixtures.py` as the public `response_type_contract()`. `test_fallback_behavior_gate.py` already imports the new helper; the transcript module did not.

This was **stale test residue**, not caused by AF-1 archival moves.

### Fix applied

**File changed:** `tests/test_narration_transcript_regressions.py`

- Import `response_type_contract` from `tests.helpers.final_emission_gate_fixtures` (preference A: current public helper).
- Keep `_fallback_contract` / `_answer_contract` imports from `test_fallback_behavior_gate` (still defined there).
- Replace `_response_type_contract("answer")` → `response_type_contract("answer")`.

No compatibility shims, no replay semantic changes.

### Before / after command results

| Command | Before AF-1B | After AF-1B |
| --- | --- | --- |
| `python -m pytest tests/test_narration_transcript_regressions.py -q` | Not run (blocked by import at collection) | **41 passed** |
| `python -m pytest -m golden_replay -q` | **ERROR** — `ImportError: cannot import name '_response_type_contract'` during collection | **59 passed** (~19s) |
| `python -m pytest tests/test_golden_replay.py -q` | 59 passed (direct module; marker collection broken) | **59 passed** (~15s; one transient Windows tmp-path flake on first rerun, green on retry) |

---

## AF-2 Game Mirror Governance Deduplication (2026-05-31)

**Block:** AF-2 — Remove duplicate/drifting `game/*.md` governance mirrors; `docs/` is sole authority.

### Pair classification

| Pair | Classification | Action |
| --- | --- | --- |
| `docs/state_authority_model.md` ↔ `game/state_authority_model.md` | **Byte-identical** (14,209 bytes) | Deleted `game/` copy |
| `docs/validation_layer_separation.md` ↔ `game/validation_layer_separation.md` | **Near-duplicate; docs/ newer** (docs +485 B). Game had shorter `Verification` line only; docs adds *Relationship to architecture audit* + CI parity pointer. **No unique game-only content.** | Deleted `game/` copy (docs superset) |
| `docs/narrative_integrity_architecture.md` ↔ `game/narrative_integrity_architecture.md` | **Near-duplicate; docs/ newer** (docs +209 B). Docs adds governance-scope split note (architecture audit vs validation-layer audit). **No unique game-only content.** | Deleted `game/` copy (docs superset) |

### Files removed (3)

- `game/state_authority_model.md`
- `game/validation_layer_separation.md`
- `game/narrative_integrity_architecture.md`

### Files converted to stubs

None — zero non-self references to `game/*.md` paths; deletion preferred over pointer stubs.

### References updated

None required. Pre-existing references already target `docs/state_authority_model.md`, `docs/validation_layer_separation.md`, and `docs/narrative_integrity_architecture.md` (runtime docstrings, audit tools, governance docs). Only this recon report had listed the `game/` paths as duplicate candidates.

### Unique content preserved

No porting needed — `docs/` versions strictly supersede the `game/` mirrors for both drifting pairs.

### Remaining `game/*.md` governance docs

**None** from this duplicate cluster. Other `game/*.md` files (if any) were out of AF-2 scope.

### Validation commands run

```bash
python -m pytest tests/test_ownership_registry.py -q          # 17 passed
python -m pytest tests/test_validation_coverage_audit.py -q   # 5 passed
python tools/validation_coverage_audit.py --strict            # exit 0, registry validation OK
python -m pytest -m golden_replay -q                          # 59 passed (~19s)
```

---

## AF-3 Cycle Closure Normalization (2026-05-31)

**Block:** AF-3 — Consolidate cycle recon/closure docs under `docs/cycles/`

### Inventory summary

| Classification | Count | Action |
| --- | ---: | --- |
| Already canonical in `docs/cycles/` | 6 | Kept (AA/AB/AC/S recon+closure partial set) |
| Misplaced — repo root | 4 | Moved (`cycle_ad_*`, `cycle_ae_*`) |
| Misplaced — `docs/reports/cycle_*` | 32 | Moved |
| Misplaced — `tests/cycle_r_*` | 7 | Moved |
| Duplicate byte-identical pairs | 0 | None found |
| Superseded copies archived | 0 | No deletions; split-location pairs merged by move only |

**Out of scope (unchanged):** `audits/cycle_{c–q}_*.md`, `docs/audits/cycle_k_*`, active CI closeouts (`docs/*_convergence_closeout.md`), `docs/cycle_af_dead_governance_removal_recon_2026-05-31.md`.

### Files moved (43) — all via `git mv` → `docs/cycles/`

**From repo root (4):**

- `cycle_ad_test_authority_consolidation_recon_2026-05-31.md`
- `cycle_ad_test_authority_consolidation_closure_2026-05-31.md`
- `cycle_ae_change_locality_optimization_recon_2026-05-31.md`
- `cycle_ae_change_locality_optimization_closure_2026-05-31.md`

**From `tests/` (7):**

- `cycle_r_test_fanout_reduction_recon_2026-05-30.md`
- `cycle_r_block_r1a_fixture_dependency_map_2026-05-30.md`
- `cycle_r_block_r1b_helper_extraction_2026-05-30.md`
- `cycle_r_block_r1c_gate_import_leakage_closure_2026-05-30.md`
- `cycle_r_block_r2_passive_phrase_ban_thinning_2026-05-30.md`
- `cycle_r_block_r3_final_route_downstream_narrowing_2026-05-30.md`
- `cycle_r_block_r4_inventory_registry_refresh_2026-05-30.md`

**From `docs/reports/` (32):** all `cycle_*.md` files (H–U block notes, recon, and closure reports including `cycle_ab_fallback_topology_collapse_closure_2026-05-31.md`, `cycle_s_runtime_drift_compression_closure_2026-05-30.md`, etc.).

**Total in `docs/cycles/` after normalization:** 49 cycle markdown files + `README.md` index.

### Duplicates archived/deleted

None. Prior split-location pairs (e.g. AB recon in `docs/cycles/` + closure in `docs/reports/`) were **relocated**, not deduplicated—no byte-identical conflicts.

### References updated

Bulk path rewrite (`docs/reports/cycle_` → `docs/cycles/cycle_`, `tests/cycle_r_` → `docs/cycles/cycle_r_`) across **29 markdown files**, including cycle cross-links, `tests/TEST_AUDIT.md`, `audits/cycle_q_replay_cost_compression_recon_2026-05-29.md`, and this recon report. AD/AE closure docs use same-directory relative recon links.

**New index:** `docs/cycles/README.md`

### Canonical location

**`docs/cycles/`** is now the single home for cycle recon/closure/block reports (Cycles H–AE + R). Active CI closeouts and registries remain under `docs/` as documented in the index.

### Validation commands run

```bash
python -m pytest tests/test_ownership_registry.py -q          # 17 passed
python -m pytest tests/test_validation_coverage_audit.py -q   # 5 passed
python tools/validation_coverage_audit.py --strict            # exit 0, registry validation OK
python -m pytest -m golden_replay -q                          # 59 passed (~17s)
```

### Remaining recommended block

- **AF-4** — Replay documentary retirement (baseline/readiness docs + manifest pointer)

---

## AF-4 Replay Baseline Retirement (2026-05-31)

**Block:** AF-4 — Retire obsolete documentary replay baselines; `docs/testing/protected_replay_manifest.md` is sole current protected replay acceptance authority.

### Source doc classification

| File | Classification | Notes |
| --- | --- | --- |
| `audits/golden_replay_baseline_2026-05-11.md` | **Historical-only** + **Superseded** | Pre–Cycle K human-readable scenario baseline (9 rows). Not loaded by pytest. Was cited as “documentary baseline” in manifest and “current baseline artifact” in `tests/README_TESTS.md` — **stale current-authority refs**. |
| `audits/golden_replay_readiness_2026-05-11.md` | **Historical-only** + **Superseded** | Pre-promotion readiness recon (Cycle Track A). Referenced only as audit history in cycle/surface-inventory docs — **not current authority**. |

Neither file is referenced by Python, CI workflows, or pytest helpers. Safe to archive after redirecting stale authority pointers.

### Files archived (2)

Moved from `audits/` → `docs/archive/dead_governance/2026-05-31/` (git mv, content unchanged):

1. `golden_replay_baseline_2026-05-11.md`
2. `golden_replay_readiness_2026-05-11.md`

### References updated (10 files)

Stale **current-authority** pointers redirected to `docs/testing/protected_replay_manifest.md` with archival wording; historical citations updated to archive paths:

| File | Change |
| --- | --- |
| `docs/testing/protected_replay_manifest.md` | Dropped “Current documentary baseline”; manifest declared sole acceptance authority; archive path for historical baseline |
| `tests/README_TESTS.md` | Replaced “current baseline artifact” link |
| `docs/audits/cycle_k_block_k1_protected_replay_declaration_2026-05-26.md` | Sources reviewed → archive path + manifest note |
| `docs/audits/cycle_k_replay_promotion_recon_2026-05-26.md` | 6 refs updated (inventory table, entry points, drift vocabulary, K1 proposal, file list) |
| `audits/cycle_q_replay_cost_compression_recon_2026-05-29.md` | Inventory table + summary bullet |
| `audits/opening_fallback_surface_inventory_2026-05-11.md` | Existing-audits list + replay cross-refs |
| `audits/thin_answer_fallback_surface_inventory_2026-05-12.md` | Golden coverage section |
| `docs/cycles/cycle_o_final_emission_gate_contraction_recon_2026-05-28.md` | Fixture/artifact list |
| `docs/archive/dead_governance/2026-05-31/README.md` | Added AF-4 entries; removed from “not moved” |
| `docs/cycle_af_dead_governance_removal_recon_2026-05-31.md` | This section |

**Intentionally unchanged:** `docs/cycles/cycle_t_maintenance_locality_reduction_recon_2026-05-30.md` commit `ac1ba90` file list (historical commit metadata). Archived file `golden_replay_readiness_2026-05-11.md` self-reference at line 154 (in-archive content unchanged).

### Current replay authority

**`docs/testing/protected_replay_manifest.md`** — protected/supporting/advisory scenario classification, reproduction command, and generated protected-field paths (via `tools/refresh_protected_replay_manifest.py --check`).

Executable gate: `python -m pytest -m golden_replay -q` / `tests/test_golden_replay.py`.

### Validation commands run

```bash
python -m pytest tests/test_ownership_registry.py -q
python -m pytest tests/test_validation_coverage_audit.py -q
python tools/validation_coverage_audit.py --strict
python -m pytest -m golden_replay -q
python tools/refresh_protected_replay_manifest.py --check
```

(Results recorded below after execution.)

```text
python -m pytest tests/test_ownership_registry.py -q          # 17 passed
python -m pytest tests/test_validation_coverage_audit.py -q   # 5 passed
python tools/validation_coverage_audit.py --strict            # exit 0, registry validation OK
python -m pytest -m golden_replay -q                          # 59 passed (~17s)
python tools/refresh_protected_replay_manifest.py --check     # exit 0, manifest in sync
```

### Files to pass back to ChatGPT

- `docs/cycle_af_dead_governance_removal_recon_2026-05-31.md` (this report, AF-4 section)
- `docs/testing/protected_replay_manifest.md`
- `docs/archive/dead_governance/2026-05-31/README.md`
- `tests/README_TESTS.md`
