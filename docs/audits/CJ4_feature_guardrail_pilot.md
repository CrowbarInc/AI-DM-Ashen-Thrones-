# CJ4 — Feature Guardrail Pilot

**Date:** 2026-06-26  
**Scope:** Measurement and documentation only.  
**Primary metric:** Feature Locality  
**Pilot authority:** [CB2_safe_domain_pilot.md](CB2_safe_domain_pilot.md)  
**Corrective comparator:** [CJ2_first_post_ca_corrective_locality_validation.md](CJ2_first_post_ca_corrective_locality_validation.md)

---

## Feature Selected

| Field | Value |
|---|---|
| **Feature ID** | CJ4-01 / CB2 Option D |
| **Name** | Content lint `code_family_counts` report metric + CLI summary |
| **Commit** | `ce36d0c` (CB: Feature Boundary Readiness Audit — CB2 pilot slice) |
| **Date** | 2026-06-23 |
| **Registry domain** | `content_lint_validation` (**safe**) |
| **Risk profile** | Low — author-time diagnostics only |

### Why this feature qualifies

CB2 was explicitly designed as the **safe-domain pilot** to prove bounded feature throughput under the CB feature boundary registry. The implemented enhancement:

1. **Production-facing** — extends `ContentLintReport.as_dict()` and the content-lint CLI with a new diagnostic field.
2. **Intentionally low risk** — additive report serialization; no lint rules, emit path, or gameplay behavior changed.
3. **Avoids prohibited surfaces** — no schema redesign, ownership-registry edits, recurrence identity changes, or protected replay restructuring.
4. **Recently completed and documented** — CB2 closeout with PASS status and 37/37 domain tests.

**Scope note:** Parent commit `ce36d0c` also contains CB audit/discovery artifacts (~144 files). CJ4 measures **only the CB2 feature slice** (4 files, +71 / −9 lines), not the full program commit.

### Feature description

Added author-time **code-family summary** diagnostics:

- `message_code_family()` — first dot segment of a lint code (e.g. `graph.unreachable_scene` → `graph`).
- `summarize_message_code_families()` — counts messages by family.
- `code_family_counts` — new field on `ContentLintReport.as_dict()`.
- CLI quiet summary — optional `code_families=graph:2,scene:1` metric when findings exist.

Guardrails satisfied: **SAFE_G1** (focused domain tests), **SAFE_G2** (author-time / advisory boundary).

---

## Files Modified

| file | subsystem | category |
|---|---|---|
| `game/content_lint.py` | content lint validation pipeline | Runtime |
| `tools/run_content_lint.py` | content lint CLI | Tooling |
| `tests/test_content_lint.py` | content lint unit suite | Test |
| `tests/test_content_lint_tool.py` | content lint CLI contract suite | Test |

**Diff size (feature slice only):** 4 files, +71 / −9 lines.

No documentation, governance, replay, projection, classification, or generated-artifact files were modified for this feature.

---

## Locality Measurements

### Totals

| Category | Count |
|---|---:|
| **Total files changed** | 4 |
| Runtime | 1 |
| Gameplay | 0 |
| Projection | 0 |
| Replay | 0 |
| Classification | 0 |
| Governance | 0 |
| Test | 2 |
| Documentation | 0 |
| Tooling | 1 |
| Generated artifact | 0 |

### Distribution

| Tier | Assessment |
|---|---|
| **Classification** | **Highly Local** |

Rationale:

- Single safe registry domain (`content_lint_validation`).
- One production module (`game/content_lint.py`).
- All changes confined to domain `required_tests` plus the domain CLI tool.
- Zero cross-cutting architectural surfaces touched.

Tier reference:

| Tier | Heuristic |
|---|---|
| Highly Local | ≤5 files, ≤1 production runtime module, single domain, no governance/replay/projection |
| Mostly Local | ≤12 files, ≤2 production, one feature family |
| Mixed | Multiple subsystems or repair families |
| Broad | >15 files or wide unrelated fanout |
| Highly Distributed | Multi-hundred-file or generated-artifact dominated |

### Fanout

| Metric | CJ4-01 (feature) | CJ2-01 (corrective) |
|---|---:|---:|
| Total files | **4** | 9 |
| Production (`game/`) | 1 | 1 |
| Test files | 2 | 7 |
| Governance files | **0** | 5 |
| Replay files | **0** | 1 |
| Projection files | **0** | 0 |
| Classification files | **0** | 0 |
| Tooling files | 1 | 0 |
| Generated artifacts | **0** | 0 |

**Subsystem spread:** 1 logical feature area (author-time content lint diagnostics).

---

## Foundation Interaction

| Architectural system | Participated? | Expected? | Localized? |
|---|---|---|---|
| Ownership registry (`tests/test_ownership_registry.py`) | **No** | — | — |
| Replay helpers (`golden_replay*`, replay facades) | **No** | Yes (excluded by design) | — |
| Projection helpers (`golden_replay_projection*`, CF owners) | **No** | Yes | — |
| Classifier contracts (`failure_classification*`) | **No** | Yes | — |
| Governance inventory (BU4 CSV, registry contract) | **No** | Yes | — |
| Hotspot infrastructure (CK reports, watch) | **No** | Yes | — |
| Feature boundary registry (CB) | **Yes** (governance-of-process, not code) | **Yes** | Pre-implementation boundary map only |
| Pre-existing `game.storage` import in CLI | Unchanged constant (`SCENES_DIR`) | Yes | Constant-only; no persistence API expansion |

**No unexpected foundation interaction.** The feature stayed entirely within the CB2 safe-domain boundary verification table. SAFE_G2 negative check confirmed no new imports from `final_emission*`, `fallback*`, `response_policy*`, or `golden_replay*`.

---

## Comparison with CJ2

### Corrective locality (CJ2-01)

| Dimension | CJ2 corrective |
|---|---|
| Classification | Mostly Local |
| Total files | 9 |
| Production files | 1 |
| Dominant categories | Governance (5), Replay (1), Runtime (1) |
| Trigger | Post-CH registry enforcement drift + facade contract gap |
| Architectural churn | Guard allowlists, replay facade re-export, BU4 inventory parity |

### Feature locality (CJ4-01)

| Dimension | CJ4 feature |
|---|---|
| Classification | **Highly Local** |
| Total files | **4** |
| Production files | 1 |
| Dominant categories | Runtime (1), Test (2), Tooling (1) |
| Trigger | Deliberate safe-domain throughput pilot |
| Architectural churn | **None** beyond domain-local helpers |

### Observations

**Did feature work require broader architectural edits than corrective work?**

**No.** Feature locality is **strictly narrower** than CJ2 corrective locality:

| Comparison | Feature vs corrective |
|---|---|
| Total fanout | 4 vs 9 (−56%) |
| Governance touches | 0 vs 5 |
| Replay touches | 0 vs 1 |
| Test-path touches | 2 vs 7 |
| Production touches | 1 vs 1 (tie) |

Corrective work after CE/CF/CG/CH required governance guard updates and replay facade repair even though production edit size was similarly small (2 lines in `final_emission_referential_clarity.py`). Feature work in a **registry-mapped safe domain** avoided those surfaces entirely.

### What architectural improvements enabled feature locality?

1. **CB feature boundary registry** — `content_lint_validation` domain with explicit `required_tests` and safe classification removed ambiguity about where the feature could land.
2. **SAFE_G1 / SAFE_G2 guardrails** — required focused domain tests and prohibited emit-path coupling before implementation began.
3. **CE/CF/CG decomposition (indirect benefit)** — content lint was never on the golden-replay/projection/classification critical path, so foundation churn in those areas did not block or absorb this feature.
4. **CH governance extraction (contrast, not participation)** — corrective work had to update extracted guard modules; safe-domain feature work never entered that enforcement graph.
5. **Author-time module boundary** — `game/content_lint.py` docstring and import graph already isolated from gameplay hot path; pilot extended serialization only.

---

## Architectural Assessment

**Did the current foundation help keep feature work local?**

**Yes — with concrete evidence.**

| Evidence | Detail |
|---|---|
| Domain-scoped file set | All 4 touched files appear in `CB_feature_boundary_registry.json` under `content_lint_validation` |
| Zero prohibited imports | Post-change scan: no `final_emission*`, `fallback*`, `speaker*`, `replay*` imports added |
| Test locality | Failures would surface in `test_content_lint*.py` only — domain `required_tests` per SAFE_G1 |
| No registry test run required | Unlike prohibited-domain work (PROHIBITED_G3), CB2 did not need `test_ownership_registry.py` |
| Replay / emission impact | Documented **none** in CB2; confirmed by file set |
| Mixed Development viability | Safe-domain pilot PASS demonstrates at least one feature class can land without governance/replay fanout |

**Limitation (honest scope):** This pilot validates **safe-domain** Mixed Development only. Caution and prohibited domains (final emission, replay, classification, ownership registry) remain higher-friction — as CJ2 demonstrated for corrective work on the registry surface.

---

## Recommendation

| Rating | **Excellent** |
|---|---|

**Rationale:**

- Feature achieved **Highly Local** classification (4 files, 1 production module, 0 governance/replay/projection/classification).
- Feature fanout is **narrower than CJ2 corrective work** despite similar production file count.
- CB guardrails (registry + SAFE_G1/G2) provided sufficient pre-implementation scoping without post-hoc architectural repair.
- Domain tests pass (37/37) with ~9 s runtime — appropriate test scope, no full-suite or registry dependency.
- Pilot matches CC/CB readiness judgment: safe-domain throughput is proven; caution/prohibited domains still require stronger gates.

**Caveat for broader Mixed Development:** Repeat this pattern only in **safe** or carefully scoped **caution** domains. Do not infer from CB2 that emit-path or registry-adjacent features will stay equally local.

---

## Test Results

### Commands

```text
python -m pytest tests/test_content_lint.py tests/test_content_lint_tool.py -q --tb=short
```

### Results

| Command | Outcome | Runtime |
|---|---|---|
| `tests/test_content_lint.py` + `tests/test_content_lint_tool.py` | **37 passed** | ~9.0 s |

No ownership registry, golden replay, projection, or classification suites were required — consistent with SAFE_G1/SAFE_G2 and CB2 negative boundary checks.

---

## Completion Criteria

| Criterion | Status |
|---|---|
| Representative feature analyzed | ✅ CB2 `code_family_counts` safe-domain pilot |
| Feature locality measured | ✅ Highly Local (4 files) |
| Compared against corrective locality | ✅ Narrower than CJ2 (9 files, governance-heavy) |
| Foundation interaction documented | ✅ No unexpected hotspot participation |
| Report completed | ✅ This document |
