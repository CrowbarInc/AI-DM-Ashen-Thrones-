# Post-Evaluator Next-Target Scan

**Status:** Planning / assessment only. No runtime behavior, scoring behavior, or test code is changed by this document. **The Evaluator layer is not being reopened.** Evaluator convergence is closed at maintenance grade per `docs/audits/closeouts/evaluator_convergence_closeout.md` and `docs/evaluator_convergence_inventory.md`; future Evaluator changes remain bug-, audit-, or stale-doc driven only.

This document picks the next highest-value cleanup/convergence target after Evaluator closeout, given the current set of closed seams (Gate, Evaluator, Final-Emission C2, Validation-Layer Objective #11, World Simulation Backbone, Test Ownership Block D, Objective #7 referent seam).

---

## 1. Recommended next target

**CI parity enforcement for the closed convergence seams** — wire the convergence closeout test slices and the existing static-audit fleet into GitHub Actions so the closeouts acquire automated drift protection instead of living only as governance docs.

In one sentence: *the convergence closeouts shipped tests and audits, but CI today only runs `tools/planner_convergence_audit.py`, `tests/test_ownership_registry.py`, and `tools/ci_content_lint.py`.* Everything else — the Evaluator slice, the Gate / FE-C2 boundary tests, the validation-layer audit, the architecture audit, the realization audits, the C1 narration seam audit, the UI-mode separation audit, and the validation coverage audit — relies on humans remembering to run it locally.

**Block name proposal:** *CI Parity Block A — Convergence Closeout CI Wiring (inventory + workflow)*.

---

## 2. Why it is higher-value than alternatives

The user prompt named six candidate areas. Ranked by leverage on the work that has *already* shipped and risk profile:

| Candidate | Leverage on closed work | Risk to runtime | Single-block achievable | Adjacency risk |
| --- | ---: | ---: | ---: | --- |
| **CI parity enforcement (recommended)** | **High** — protects Evaluator + Gate + FE-C2 + Obj #11 + Test Ownership simultaneously | None (CI/workflow + docs only) | **Yes** | Compounds existing assets |
| GPT / expression layer convergence inventory | Medium — new seam, doesn't compound recent closeouts | Medium — touches `game/gm.py` (~6 000 lines, ~100 top-level defs) and `game/gm_retry.py` (~2 700 lines) | No — multi-block (Evaluator-style A→F) | Adjacent to Gate (just closed) |
| Cross-layer convergence meta-tooling | Medium — useful, but the audits exist; what's missing is *running* them | Low | Possibly | Solved more cheaply by CI parity |
| Long-session drift instrumentation | Low — scenario-spine evaluator just shipped (Block E) | Low | Yes, but unjustified now | Risk of reopening Evaluator |
| Scenario-spine observability | Low — owned by Block E in the closeout | Low | n/a | Direct Evaluator overlap |
| Systemic audit tooling | Medium — naturally lands inside the CI parity block as an optional thin meta-runner | Low | Yes | Subsumed by recommended target |

CI parity enforcement is the only candidate that:

- Multiplies the value of **every** convergence closeout that just shipped.
- Carries no runtime risk (purely workflow + docs, optionally a thin meta-runner script).
- Has a clear, concrete acceptance signal (a green Actions run that exercises the recommended slice).
- Cannot accidentally reopen Evaluator, Gate, or FE-C2.

GPT/expression-layer convergence is the obvious second-best long-term target (`game/gm.py` is the largest remaining sediment hotspot and lacks a `gpt_convergence_*` doc family), but it is a multi-block commitment, has higher refactor risk, and would not compound the closeouts. It is recorded here as the **suggested follow-up** after CI parity lands.

---

## 3. Evidence from docs / tests / code

### 3.1 Closeouts that ship test slices but are not enforced in CI

The Evaluator closeout explicitly names a recommended test slice:

```56:57:docs/audits/closeouts/evaluator_convergence_closeout.md
python -m pytest tests/test_evaluator_convergence_closeout.py -q
python -m pytest tests/test_dead_turn_evaluation_threading.py tests/test_playability_eval.py tests/test_behavioral_gauntlet_eval.py tests/test_scenario_spine_eval.py tests/test_final_emission_meta.py tests/test_architecture_audit_tool.py tests/test_validation_layer_audit_smoke.py -q
```

None of those eight test modules are referenced by `.github/workflows/content-lint.yml`. The same is true for the Gate closeout's protected invariants (`tests/test_final_emission_gate.py`, `tests/test_speaker_contract_enforcement.py`-family) and the FE-C2 boundary lock (`tests/test_final_emission_boundary_convergence.py`).

### 3.2 The current CI surface

`.github/workflows/content-lint.yml` is the **only** workflow file in the repo:

```10:38:.github/workflows/content-lint.yml
jobs:
  content-lint:
    name: content-lint
    runs-on: ubuntu-latest
    permissions:
      contents: read

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          # Repo has no pinned interpreter file; 3.11+ matches typical project expectations.
          python-version: "3.12"
          cache: pip
          cache-dependency-path: requirements.txt

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Planner convergence static audit
        run: python tools/planner_convergence_audit.py

      - name: Test ownership registry (governance)
        run: python -m pytest tests/test_ownership_registry.py -q
```

That gives us exactly three things automatically enforced: planner convergence audit, ownership registry pytest, and content-lint Phase 1 (informational, `continue-on-error: true`). Phase 2 is gated behind `if: false`.

### 3.3 Static audits that exist but are not in CI

Inventory under `tools/` (relevant governance/audit subset):

| Tool | Purpose | In CI today? |
| --- | --- | ---: |
| `tools/architecture_audit.py` | Broad repo subsystem governance, ownership / overlap / coupling / archaeology / hotspot scoring | **No** |
| `tools/validation_layer_audit.py` | Objective #11 layer-separation drift (engine / planner / GPT / gate / evaluator) | **No** |
| `tools/final_emission_ownership_audit.py` | Objective C2 advisory drift scan for boundary semantic synthesis | **No** |
| `tools/realization_layer_audit.py` | Realization layer ownership audit | **No** |
| `tools/realization_provenance_audit.py` | Realization provenance / fallback family audit | **No** |
| `tools/c1_narration_seam_audit.py` | C1 narration seam audit | **No** |
| `tools/ui_mode_separation_audit.py` | Objective #15 UI-mode separation audit | **No** |
| `tools/validation_coverage_audit.py` | Objective #12 validation coverage registry audit | **No** |
| `tools/test_audit.py` | Inventory regen + drift checks over `tests/test_inventory.json` (schema v2) | **No** |
| `tools/architecture_audit_runtime.py` / `architecture_audit_tests.py` | Sub-modules of architecture_audit | **No** |
| `tools/planner_convergence_audit.py` | CTIR → narrative_plan → prompt convergence | **Yes** |

Each of these has a guard test (`tests/test_architecture_audit_tool.py`, `tests/test_validation_layer_audit_smoke.py`, `tests/test_validation_coverage_audit.py`, `tests/test_realization_layer_audit.py`, `tests/test_realization_provenance_audit.py`, etc.) — those guard tests are also not in CI.

### 3.4 Where docs already promise enforcement

- `docs/audits/closeouts/evaluator_convergence_closeout.md` — names a recommended pytest slice to run for evaluator-boundary changes (no CI hook).
- `docs/validation_layer_audit.md` — `--strict` mode "exit with status 2 if any **likely_drift** finding is present (default exit 0 so benign within-layer splits do not fail CI unless you opt in)" — explicit CI opt-in language, never wired.
- `docs/final_emission_ownership_convergence.md` (Block D2) — names `tests/test_final_emission_boundary_convergence.py` and `tools/final_emission_ownership_audit.py --strict` as the regression-lock + advisory drift scan; neither runs in CI.
- `docs/validation_layer_separation.md` — "Verification: `tools/validation_layer_audit.py` (non-strict clean on `./game`; `--strict` for CI opt-in)" — explicit CI opt-in language, never wired.
- `docs/architecture_ownership_ledger.md` (Operator Note) — *"Drift audit: `tools/validation_layer_audit.py` runs heuristic checks (imports and a few wording patterns) to help catch ownership mistakes early."* — relies on humans running it.
- `docs/planner_convergence.md` — names the static audit + focused pytest slice; only the audit half is wired.
- `docs/gate_convergence_closeout.md` — Recommended Future Work item: *"CI shadow-equivalence mode … Optional CI job that runs Block T's `install_dual_run_enforce` + Block U probes across a curated fixture set on every change touching `game/final_emission_gate.py` or `game/speaker_contract_enforcement.py`."* — explicitly contemplated, never wired.

### 3.5 Why the leverage is real now (and was not before)

Until very recently the closeouts did not exist. With Evaluator now closed, the repo has **simultaneously** four maintenance-grade convergence boundaries (Gate, Evaluator, FE-C2, Validation Layer Obj #11) plus several supporting convergences (Test Ownership Block D, Objective #7, Objective #9, Objective #12). This is the largest set of "do not regress this" surfaces the repo has ever carried at once. The cost of *not* enforcing them is monotonically increasing.

---

## 4. Risks if ignored

If CI parity is not closed next:

1. **Silent regression of closed seams.** Any of the four maintenance-grade boundaries can drift between PRs without a red light. The convergence-closeout docs become aspirational rather than enforced.
2. **Audit-tool rot.** `tools/architecture_audit.py`, `tools/validation_layer_audit.py`, `tools/final_emission_ownership_audit.py`, `tools/c1_narration_seam_audit.py`, `tools/ui_mode_separation_audit.py`, `tools/validation_coverage_audit.py` have nontrivial test surfaces (`tests/test_architecture_audit_tool.py`, etc.) but no automated invocation. If they break, no one will notice until someone tries to run them locally.
3. **Convergence-doc drift.** Closeout docs reference test names and audit names; refactors elsewhere can rename or move those without the docs updating. CI is the cheapest possible enforcement of "the doc still describes runnable artifacts."
4. **Repeated-effort risk for future cleanups.** The next big sediment target (GPT / expression layer) will want to reuse the same test-slice pattern. Without CI parity, the pattern stays "humans remember"; that scales worse with each new closeout.
5. **Test-inventory drift.** `tests/test_inventory.json` (schema v2) is governance ground truth (`tests/TEST_AUDIT.md`, `docs/architecture_ownership_ledger.md`). If `tools/test_audit.py` does not run in CI, schema v2 drift goes unnoticed until the next manual regen.

None of these are urgent in the next sprint. They are exactly the kind of slow-burn risk that CI exists to absorb.

---

## 5. Suggested first implementation block

**Block A — Convergence CI Inventory + Wiring (Cursor Block B from this scan).**

Goals (Block A only — inventory + a single new workflow file; do not refactor audits, do not change test code):

1. **Inventory the enforcement surface.** Produce a single doc (e.g. `docs/convergence_ci_inventory.md`) that lists, for each closed seam, (a) the canonical closeout doc, (b) the recommended pytest slice, (c) any associated static audit, (d) whether it is currently in CI.
2. **Add one new GitHub Actions workflow** (proposed name `convergence-checks.yml`) parallel to `content-lint.yml`. It should run on `push` and `pull_request`, install requirements, and execute, in order:
   - `python -m pytest tests/test_evaluator_convergence_closeout.py -q` (Evaluator closeout slice, fast).
   - `python -m pytest tests/test_dead_turn_evaluation_threading.py tests/test_playability_eval.py tests/test_behavioral_gauntlet_eval.py tests/test_scenario_spine_eval.py tests/test_final_emission_meta.py tests/test_architecture_audit_tool.py tests/test_validation_layer_audit_smoke.py -q` (Evaluator boundary slice).
   - `python -m pytest tests/test_final_emission_boundary_convergence.py -q` (FE-C2 boundary lock).
   - `python tools/architecture_audit.py --print-summary` (broad governance — keep non-strict initially).
   - `python tools/validation_layer_audit.py --strict` (Objective #11 — strict already exists).
   - `python tools/final_emission_ownership_audit.py --strict` (Objective C2 — strict already exists).
   - `python tools/validation_coverage_audit.py` (Objective #12).
3. **Decide each step's blocking class** in the inventory doc:
   - **Hard fail (`continue-on-error: false`):** strict-mode audits that already promise CI-grade behavior (`validation_layer_audit --strict`, `final_emission_ownership_audit --strict`), Evaluator closeout pytest, FE-C2 boundary pytest.
   - **Soft / informational (`continue-on-error: true`):** broad heuristic audits that have known noise (architecture_audit summary, validation_coverage_audit). These can be promoted to hard-fail in a Block B.
4. **Optionally** add a **thin meta-runner** `tools/run_governance_audits.py` that wraps the static audits into one process for local parity with CI. This is a *script, not a policy engine* — same exit codes, no aggregation logic.
5. **Record the rollout** in `docs/convergence_ci_inventory.md` and a one-line pointer from each closeout doc (`docs/audits/closeouts/evaluator_convergence_closeout.md`, `docs/gate_convergence_closeout.md`, `docs/final_emission_ownership_convergence.md`, `docs/validation_layer_separation.md`) so future readers know enforcement is wired.

**Out of scope for Block A:**

- Touching `game/` runtime modules.
- Adding new evaluator scoring, new gate legality, new repair paths, new audits.
- Reopening any closed Block (Evaluator A–F, Gate A–AA, FE-C2 A–D2, Obj #11 A–D, Test Ownership A–D).
- Promoting the soft audits to hard-fail (defer to Block B once each step is proven stable in real PRs).

**Acceptance for Block A:**

- `docs/convergence_ci_inventory.md` exists and maps every closed convergence to its recommended test slice + audit.
- `.github/workflows/convergence-checks.yml` exists and runs on push / pull_request.
- A green run of the new workflow on `main` (or current branch) demonstrates the slice executes.
- No runtime, scoring, gate, or evaluator behavior changes.
- The Evaluator closeout doc is **not** modified beyond a single pointer line; no Block A–F is reopened.

---

## 6. Tests likely involved

The block touches CI plumbing and a new docs page; existing tests are **invoked**, not changed. The following sets matter for verification (and are exactly the slices the new workflow runs):

**Evaluator boundary slice (from `docs/audits/closeouts/evaluator_convergence_closeout.md`):**

- `tests/test_evaluator_convergence_closeout.py`
- `tests/test_dead_turn_evaluation_threading.py`
- `tests/test_playability_eval.py`
- `tests/test_behavioral_gauntlet_eval.py`
- `tests/test_scenario_spine_eval.py`
- `tests/test_final_emission_meta.py`
- `tests/test_architecture_audit_tool.py`
- `tests/test_validation_layer_audit_smoke.py`

**FE-C2 boundary lock (from `docs/final_emission_ownership_convergence.md` Block D2):**

- `tests/test_final_emission_boundary_convergence.py`
- `tests/test_final_emission_boundary_no_semantic_repair.py` (defensive companion)

**Objective #11 + #12 + governance audit guards (already exist):**

- `tests/test_validation_layer_audit_smoke.py` (also in evaluator slice)
- `tests/test_validation_coverage_audit.py`
- `tests/test_architecture_audit_tool.py` (also in evaluator slice)

**Planner convergence (already wired in CI; included for completeness):**

- `tests/test_planner_convergence_static_audit.py`
- `tests/test_planner_convergence_contract.py`
- `tests/test_planner_convergence_live_pipeline.py`
- `tests/test_prompt_context_plan_only_convergence.py`

**Optional new test (only if a meta-runner is added):**

- `tests/test_run_governance_audits_smoke.py` — would lock the meta-runner's exit code wiring; not required for Block A acceptance.

No test code is modified by Block A. Test code may only be modified in a later block if the new workflow uncovers a stale assertion.

---

## 7. Explicit Evaluator non-reopen note

**Evaluator is not being reopened.** This planning doc:

- Treats `docs/audits/closeouts/evaluator_convergence_closeout.md` as authoritative (offline, read-only, no runtime repairs, no gate legality, no engine truth, no policy by JSON).
- Does not propose changing any of `game/playability_eval.py`, `game/narrative_authenticity_eval.py`, `game/scenario_spine_eval.py`, `game/scenario_spine.py`, `game/telemetry_vocab.py`, `game/stage_diff_telemetry.py`, or evaluator-owned tests.
- Does not propose merging playability and behavioral gauntlet scoring, collapsing scenario-spine transcript metadata into FEM correctness, or treating runner summaries / markdown / normalized telemetry bundles as canonical scoring.
- Treats the Evaluator-closeout test slice as **artifact under enforcement**, not as a surface to extend.

If the new CI run surfaces a flake or a stale assertion in an Evaluator test, the response is the same as the closeout already prescribes: fix the concrete bug, do not broaden Evaluator scope.

---

## 8. What Cursor Block B should do next

> **Block B — Convergence CI Wiring (implementation of this scan's Section 5).**
>
> 1. Create `docs/convergence_ci_inventory.md` mapping every closed convergence → recommended pytest slice → static audit → current CI status.
> 2. Create `.github/workflows/convergence-checks.yml` running, on push and pull_request: the Evaluator closeout slice, the Evaluator boundary slice, the FE-C2 boundary lock, `tools/validation_layer_audit.py --strict`, `tools/final_emission_ownership_audit.py --strict`, `tools/validation_coverage_audit.py`, and `tools/architecture_audit.py --print-summary` (informational).
> 3. Mark each step hard-fail vs informational per Section 5 step 3.
> 4. Add a one-line CI pointer to each closeout doc (`evaluator_convergence_closeout.md`, `gate_convergence_closeout.md`, `final_emission_ownership_convergence.md`, `validation_layer_separation.md`).
> 5. Optionally add `tools/run_governance_audits.py` as a thin local-parity meta-runner (no aggregation logic, same exit codes).
> 6. **Do not** modify any runtime module, evaluator, gate, repair, validator, or existing test under `tests/`. **Do not** reopen Evaluator Blocks A–F, Gate Blocks A–AA, FE-C2 Blocks A–D2, or Validation-Layer Objective #11 Blocks A–D.

After Block B lands and is green for at least one real PR cycle, **Block C** can promote the informational audits to hard-fail (one at a time, each in its own PR), and **Block D** can begin the GPT / expression-layer convergence inventory (parallel to Evaluator Block A) — that is the suggested next major target after CI parity, but it is explicitly out of scope for Block B.
