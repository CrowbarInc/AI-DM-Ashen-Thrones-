# CB2 Safe Domain Pilot

**Block:** CB2 — Safe Domain Pilot  
**Registry domain:** `content_lint_validation`  
**Registry reference:** [`CB_feature_boundary_registry.json`](CB_feature_boundary_registry.json)  
**Pilot date:** 2026-06-23

---

## Feature Implemented

**Option D — New CLI reporting metric**

Added an author-time **code-family summary** to the content lint report and CLI:

1. **`code_family_counts`** — new field on `ContentLintReport.as_dict()` counting messages by the first segment of each lint `code` (e.g. `graph.unreachable_scene` → family `graph`).
2. **CLI summary metric** — one-line output now includes `code_families=graph:2,scene:1` when findings exist (sorted families, omitted when the report has zero messages).

Helpers: `message_code_family()`, `summarize_message_code_families()`.

This is additive diagnostics only: no lint rules changed, no runtime behavior changed, no new consumers on the gameplay emit path.

---

## Files Modified

| File | Change |
|---|---|
| `game/content_lint.py` | Added `message_code_family`, `summarize_message_code_families`; extended `ContentLintReport.as_dict()` with `code_family_counts` |
| `tools/run_content_lint.py` | CLI summary line includes `code_families=…`; detail lines use shared `message_code_family` |
| `tests/test_content_lint.py` | Unit tests for family summarization and report shape |
| `tests/test_content_lint_tool.py` | CLI/json-out contract tests for new metric |

**Boundary verification (pre-implementation):**

| File | Registry domain | Classification |
|---|---|---|
| `game/content_lint.py` | content_lint_validation | safe |
| `tools/run_content_lint.py` | content_lint_validation | safe |
| `tests/test_content_lint.py` | content_lint_validation (required_tests) | safe |
| `tests/test_content_lint_tool.py` | content_lint_validation (required_tests) | safe |

**Guardrails triggered:** SAFE_G1, SAFE_G2 only.

---

## Registry Classification

**Safe** (`content_lint_validation`)

---

## Guardrails Satisfied

### SAFE_G1 — Focused domain tests

| Requirement | Status |
|---|---|
| Focused pytest in domain `required_tests` | **PASS** — `tests/test_content_lint.py`, `tests/test_content_lint_tool.py` |
| New behavior has assertions | **PASS** — `test_summarize_message_code_families_groups_by_first_segment`, `test_cli_summary_includes_code_family_metric_for_warnings`, updated `test_report_as_dict_roundtrip_shape` |

### SAFE_G2 — Author-time / advisory boundary

| Requirement | Status |
|---|---|
| Outputs remain author-time / CLI / JSON report only | **PASS** — metric is derived from existing `ContentLintMessage` list at report serialization time |
| No new prohibited-path imports | **PASS** — see Dependency Check |
| No wiring into gate / fallback / policy / replay | **PASS** — `lint_all_content` pipeline unchanged; no new runtime consumers |

---

## Dependency Check

### `game/content_lint.py` imports

| Module | Prohibited? |
|---|---|
| `game.scene_graph` | No |
| `game.scene_lint` | No |
| `game.validation` | No |
| `game.schema_contracts` | No |
| `game.utils` | No |

No imports from: `final_emission*`, `fallback*`, `speaker*`, `response_policy*`, `replay*`, `protected_replay*`, `sanitizer*`, `repair*`.

### `tools/run_content_lint.py` imports

| Module | Prohibited? |
|---|---|
| `game.content_lint` | No |
| `game.storage` (SCENES_DIR constant only) | No — pre-existing; path constant for default scenes directory |

No caution-domain logic added. `game.storage` import is unchanged from pre-pilot CLI (SCENES_DIR default only; no persistence mutations).

---

## Replay Impact Assessment

**Expected impact:** None

Lint report serialization and CLI stdout formatting only. No replay helpers, golden replay markers, or protected observation fields touched.

---

## Final Emission Impact Assessment

**Expected impact:** None

No `game/final_emission*` modules modified. Content lint module docstring already states it is not used on the gameplay hot path; this pilot preserves that boundary.

---

## Speaker Impact Assessment

**Expected impact:** None

No speaker contract, signature, or adoption modules touched.

---

## Fallback Impact Assessment

**Expected impact:** None

No fallback, sanitizer, or repair modules touched.

---

## Validation Results

### Tests run

```text
py -m pytest tests/test_content_lint.py tests/test_content_lint_tool.py -q
```

### Results

```text
.....................................                                    [100%]
37 passed
```

### Import scan (modified production/tool files)

```text
game/content_lint.py  — no prohibited imports
tools/run_content_lint.py — no prohibited imports
```

### Runtime execution path

**Unchanged.** `lint_all_content` rule passes, message collection, and exit-code semantics are identical; only report `as_dict()` shape and CLI summary formatting are extended.

---

## Lessons Learned

### Was the registry sufficient?

**Yes.** The `content_lint_validation` domain paths, `required_tests`, and SAFE_G1/G2 guardrails were enough to scope the pilot without ambiguity. Pre-implementation boundary verification mapped every touched file to the safe domain in one pass.

### Were any classifications unclear?

| Topic | Observation |
|---|---|
| `game.storage` in CLI | Pre-existing `SCENES_DIR` import; registry lists `game/storage.py` under **caution** (`state_storage_persistence`), but the CLI only reads a path constant. Pilot did not expand storage usage. CB3 could add a note: constant-only imports vs persistence API calls. |
| `code_family_counts` on clean reports | Metric omitted from CLI when zero messages (empty `code_families`); JSON always includes `code_family_counts` (empty dict). Acceptable; document in CLI help if authors expect always-on metric. |
| Test file ownership | Registry lists `tests/test_content_lint*.py` patterns; pilot also updated `test_content_lint_tool.py` — covered by registry `required_tests` glob. |

---

## Readiness Scoring

### Pilot Status: **PASS**

| Criterion | Result |
|---|---|
| Feature entirely within safe domain | PASS |
| Only SAFE guardrails required | PASS |
| No prohibited / caution boundary violations | PASS |
| Domain tests pass | PASS (37/37) |

### Recommended next Safe-domain candidates

| Priority | Domain | Suggested pilot |
|---|---|---|
| 1 | `behavioral_playability_evaluators` | Add one offline gauntlet summary column (advisory only) |
| 2 | `ui_mode_frontend` | Add UI mode display label behind existing API contract |
| 3 | `combat_checks_adjudication` | Add localized condition effect with focused engine test |
| 4 | `model_config_routing` | Config presentation only — avoid fallback-trigger semantics |

### Recommended CB3 refinements

1. **Constant-only import rule** — Document when a caution-domain module may be imported for constants/paths only (e.g. `SCENES_DIR`) without triggering caution guardrails.
2. **Report-field additive checklist** — Template for safe-domain JSON report extensions (field name, always vs conditional presence, backward-compat note).
3. **Caution escalation tripwire** — Explicit rule: if a safe-domain change adds imports from `game.api`, `game.gm`, or `game.prompt_context`, escalate to caution review even when file paths remain in a safe glob.

---

## Cursor Feedback

| Item | Value |
|---|---|
| **Feature chosen** | Option D — `code_family_counts` report field + CLI `code_families=` metric |
| **Files touched** | `game/content_lint.py`, `tools/run_content_lint.py`, `tests/test_content_lint.py`, `tests/test_content_lint_tool.py` |
| **Guardrails triggered** | SAFE_G1, SAFE_G2 |
| **PASS/FAIL** | **PASS** |
| **CB3 refinements** | Constant-only import rule; report-field checklist; safe→caution import tripwire |
