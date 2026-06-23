# CB5 Caution Domain Pilot

**Block:** CB5 — Telemetry Caution-Domain Pilot  
**Registry domain:** `telemetry_diagnostics_audit`  
**Classification:** Caution (lowest-risk caution tier)  
**Guardrail template:** [`CB3_caution_domain_guardrails.md`](CB3_caution_domain_guardrails.md)  
**Safe pilot precedent:** [`CB2_safe_domain_pilot.md`](CB2_safe_domain_pilot.md)  
**Pilot date:** 2026-06-23

---

## Feature Implemented

**Option D — New audit visualization/reporting statistic**

Added **`architecture_layer_file_counts`** to the full diagnostic test-inventory payload produced by `tools/test_audit.py`:

1. **`summarize_architecture_layer_file_counts(file_rows)`** — pure helper counting test modules per heuristic `likely_architecture_layer` (`gate`, `engine`, `transcript`, etc.).
2. **Full diagnostic JSON** — new top-level field `architecture_layer_file_counts` (sorted keys) on `build_inventory_payload()` output; **not** written to committed `tests/test_inventory_governance.json`.
3. **CLI output** — when writing full diagnostic (`--full` or `--output`), prints one line: `Architecture layer file counts (heuristic): engine: N; gate: M; …`

Additive author-time triage only. No metric history rewrite, no trend-window tooling, no replay-governance changes.

---

## Domain Classification

**Caution** — `telemetry_diagnostics_audit`

| Attribute | Value |
|---|---|
| Risk level | Low–Medium (additive report scope) |
| Guardrails | CAUTION_G1, CAUTION_G3 (CAUTION_G2 not triggered) |
| Registry paths | `tools/**`, `tests/TEST_AUDIT.md` (tooling lane) |

---

## Files Modified

| File | Change |
|---|---|
| `tools/test_audit.py` | `summarize_architecture_layer_file_counts()`; full payload field; CLI print in `write_full_inventory()` |
| `tests/test_test_audit_tool.py` | Unit tests for summarizer; governance boundary test (statistic excluded from committed JSON) |

### Boundary verification (pre-implementation)

| File | Registry domain | Classification |
|---|---|---|
| `tools/test_audit.py` | `telemetry_diagnostics_audit` | caution |
| `tests/test_test_audit_tool.py` | `telemetry_diagnostics_audit` (tool contract) | caution |

**Imports added:** None (no new import statements).

**Guardrails triggered:**

| Guardrail | Triggered? |
|---|---|
| CAUTION_G1 — narrow scope | Yes — single additive statistic on full diagnostic only |
| CAUTION_G2 — replay smoke | **No** — negative case documented below |
| CAUTION_G3 — high-coupling contract | Yes — governance JSON shape preserved; statistic excluded from committed artifact |

---

## Replay-Smoke Requirement

**Level:** None (negative case)

Per CB3 replay-smoke standard: additive telemetry/report extensions with no schema or history change do **not** require replay smoke.

| Check | Result |
|---|---|
| Player-visible behavior changed | No |
| Protected observation fields at risk | No |
| Trend-window / recurrence artifacts modified | No |
| Qualifying tier (R1–R6) | **N/A** |

**Evidence (CB3 format):**

```markdown
## Replay smoke (CB3)

- **Domain:** telemetry_diagnostics_audit
- **Tier:** N/A (negative case)
- **Command:** none required
- **Observation families at risk:** none — additive full-diagnostic aggregate only
- **Result:** PASS (not required)
```

---

## Escalation Review

Verified against CB3 escalation triggers E1–E8:

| Trigger | Fired? | Notes |
|---|---|---|
| E1 — `game/final_emission*` | **No** | No production code modified |
| E2 — fallback/sanitizer/repair | **No** | |
| E3 — speaker identity | **No** | |
| E4 — response policy | **No** | |
| E5 — replay governance | **No** | No `tests/helpers/golden_replay*`, manifest, or trend tools touched |
| E6 — protected observation paths | **No** | |
| E7 — new fallback behavior | **No** | |
| E8 — post-GPT policy mutation | **No** | |

**Import tripwire scan (`tools/test_audit.py`):** No prohibited-domain imports.

**Escalation required:** None. Work remained in caution workflow.

---

## Protected Field Impact

**Expected impact:** None

The statistic aggregates heuristic architecture-layer labels on test **file** rows. It does not read runtime FEM, project replay observations, or modify `PROTECTED_OBSERVATION_FIELDS`.

---

## Validation Results

### CB3 minimum validation bundle

| Tier | Requirement | Command | Result |
|---|---|---|---|
| **Unit** | Tool helper + governance boundary | `py -m pytest tests/test_test_audit_tool.py -q` | **50 passed** |
| **Integration** | Attribution report contract (domain neighbor) | `py -m pytest tests/test_attribution_completeness_metric.py -q` | **included in 50 passed** |
| **Replay smoke** | Negative case — not required | N/A | **PASS (skipped by rule)** |
| **Ownership** | Governance JSON unchanged | `git status tests/test_inventory_governance.json` | **Unmodified** |

### Governance drift note

`py tools/test_audit.py --check` reports **pre-existing** inventory drift (+19 test files not in committed governance JSON). This predates CB5 and is **not** caused by the pilot feature:

- `architecture_layer_file_counts` is **full-diagnostic only**
- `build_governance_payload()` / committed `tests/test_inventory_governance.json` are **unchanged**
- Pilot does not regenerate governance JSON

### Restrictions compliance

| Restricted area | Modified? |
|---|---|
| `final_emission*` | No |
| `replay*` / `protected_replay*` | No |
| `fallback*` | No |
| `sanitizer*` / `repair*` | No |
| `speaker*` | No |
| `response_policy*` | No |

---

## Lessons Learned

### Were CB3 guardrails sufficient?

**Yes.** CAUTION_G1 scope framing and CAUTION_G3 governance-contract rules were enough to implement and review the change without ambiguity. The per-domain bundle correctly identified `tests/test_test_audit_tool.py` as the tool contract home.

### Was replay-smoke guidance clear?

**Yes.** The “additive report / negative case” rule in CB3 made the replay-smoke decision immediate. No time spent running unnecessary `golden_replay` suites.

### Were escalation rules adequate?

**Yes.** E5 (replay governance) and import tripwire list provided a fast pre-implementation check. String references to `final_emission_gate` inside **existing** heuristic scoring logic in `test_audit.py` are not new imports and did not trigger escalation.

### Improvements before broader caution work

1. **Pre-existing governance drift** — 19 test files missing from committed governance JSON should be resolved in a dedicated inventory refresh (not bundled with feature pilots).
2. **Full vs governance artifact docs** — CB3 could add an explicit note: new full-diagnostic fields are caution-safe when excluded from `GOVERNANCE_SUMMARY_FIELDS` and `build_governance_payload()`.
3. **Constant-only / string-reference rule** — Heuristic source scanners that *mention* prohibited module names in AST/string analysis should be distinguished from runtime imports (extends CB2 constant-only note).

---

## Pilot Outcome

### **PASS**

| Criterion | Result |
|---|---|
| Feature in `telemetry_diagnostics_audit` | PASS |
| CAUTION_G1 + CAUTION_G3 satisfied | PASS |
| CAUTION_G2 negative case documented | PASS |
| No E1–E8 escalation | PASS |
| Domain tests pass | PASS (50/50) |
| No prohibited-path modifications | PASS |
| No protected-field impact | PASS |

### Recommended next Safe/Caution candidates

| Priority | Domain | Suggested work |
|---|---|---|
| 1 | `world_scenes_affordances` | Data-only `data/scenes/**` affordance with CAUTION_G2 replay-smoke decision |
| 2 | `telemetry_diagnostics_audit` | Second additive field in a different report tool (e.g. stage-diff read-side summary) |
| 3 | `behavioral_playability_evaluators` | Safe-domain follow-on (CB2 stretch) |

### Recommended CB6 scope

Per CB1 discovery block list, **CB6 — Speaker/Fallback Runtime Frequency Probe** closes BV1 missing evidence on representative speaker-mismatch and fallback branch incidence (distinct from protected replay recurrence). CB5 confirms caution telemetry pilots work; CB6 should stay **measurement/report-only** in `tools/**` and `artifacts/golden_replay/**` read paths without modifying prohibited emit modules.

---

## Cursor Feedback

| Item | Value |
|---|---|
| **Feature chosen** | Option D — `architecture_layer_file_counts` audit statistic + CLI line |
| **Files touched** | `tools/test_audit.py`, `tests/test_test_audit_tool.py` |
| **Replay-smoke level** | None (CB3 negative case; additive full-diagnostic only) |
| **Escalation triggers encountered** | None |
| **PASS/FAIL** | **PASS** |
| **Recommended CB6 scope** | Speaker/fallback runtime frequency probe — read-side incidence reporting, BV1 evidence gap, no emit-path changes |
