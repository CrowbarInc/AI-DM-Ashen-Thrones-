# Cycle AQ — Test Inventory Compression Recon

**Date:** 2026-06-04  
**Scope:** Read-only reconnaissance. No behavior or reporting changes implemented.

---

## 1. Executive summary

`tests/test_inventory.json` is **fully auto-generated** by `tools/test_audit.py` (schema v2). It is **not hand-edited**. The only **runtime JSON reader** is `tests/test_ownership_registry.py`; CI runs that module in both `content-lint.yml` and `convergence-checks.yml`. Everything else is documentation, generator code, or helper unit tests.

The file is **large maintenance drag** (~5.1 MB, ~128k lines) because it stores **per-test rows for the entire suite** plus **duplicate nodeid lists** at file scope. Roughly **3.1 MB** is the `tests[]` array alone; `files[].collected_nodeids` duplicates the same 4,247 nodeids already present in `tests[]`.

**Drift today:** committed inventory (2026-05-30) vs live `pytest --collect-only` (2026-06-04):

| Metric | Committed inventory | Live collection | Delta |
| --- | ---: | ---: | ---: |
| Test modules | 306 | 307 | +1 (`tests/test_final_emission_sealed_fallback.py`) |
| Collected items | 4,247 | 4,336 | +89 |

Governance tests **still pass** on stale inventory because they validate **registry path presence and heuristic layer alignment**, not **live collection parity**. There is **no `--check` mode** and **no CI step** that regenerates or diffs inventory.

**Low-risk compression thesis:** split **governance-critical** inventory (small, CI-checked) from **diagnostic/triage** inventory (generated on demand, not committed). Keep reporting behavior unchanged by preserving governance assertions and human doc pointers.

Supporting artifacts: `cycle_aq_inventory_consumers.json`, `cycle_aq_inventory_duplication_map.json`.

---

## 2. Current inventory generation path

### Generator

| Item | Detail |
| --- | --- |
| **Script** | `tools/test_audit.py` |
| **Command** | `py -3 tools/test_audit.py` (Windows) / `python tools/test_audit.py` |
| **Output** | `tests/test_inventory.json` |
| **Schema version** | `INVENTORY_SCHEMA_VERSION = 2` (constant in generator) |
| **Runtime** | ~26 s on this machine (4336 tests; includes full `pytest --collect-only`) |

### Generation pipeline (ordered)

1. **`pytest tests/ --collect-only`** — captures all nodeids (non-quiet; full ids).
2. **Glob `tests/test_*.py`** — includes zero-collect modules in `files[]`.
3. **AST parse** — test def names, shadowed duplicates, `game.*` imports, `pytestmark`, per-test decorators.
4. **Heuristics** — architecture layer scores, feature areas, brittleness, overlap hints, Block B clusters.
5. **Import `tests.test_ownership_registry.RESPONSIBILITY_REGISTRY`** — embed `ownership_registry_index` (groups + files_roles).
6. **Write JSON** — `json.dumps(..., indent=2, sort_keys=True)`; only `summary.generated_utc` is non-deterministic.

### Manual vs auto

| Aspect | Mode |
| --- | --- |
| JSON body | **Auto-generated only** |
| `RESPONSIBILITY_REGISTRY` | **Authoritative Python** (embedded into JSON at regen) |
| `_CROSS_FILE_DUPLICATE_ALLOWLIST` | **Authoritative Python** (not in JSON) |
| `# feature:` comments / `@pytest.mark.*` ownership tags | **Authoritative in test source** (read by generator) |
| `tests/TEST_AUDIT.md` prose tables | **Human docs**; counts intentionally delegated to JSON |

### Docs / commands referencing regen

- `tests/TEST_AUDIT.md` — primary operator doc
- `tests/README_TESTS.md`, `tests/TEST_CONSOLIDATION_PLAN.md`
- `docs/architecture_ownership_ledger.md`, `docs/testing/protected_replay_manifest.md`
- `docs/convergence_ci_inventory.md` — notes `test_audit.py` **not yet** in convergence CI

### Validation today

| Check | Where | Detects stale inventory? |
| --- | --- | --- |
| Registry paths ∈ `files[]` | `test_ownership_registry_governance` | Partially (missing **new registry path** fails) |
| Embedded registry index parity | `test_inventory_embeds_neighbor_registry_index` | No (re-embeds from Python at regen) |
| Schema v2 fields | Multiple ownership tests | No |
| Live collect count / nodeid set | **None** | **No** |
| Regen diff in CI | **None** | **No** |

---

## 3. Inventory consumer map

See `cycle_aq_inventory_consumers.json` for machine-readable grouping.

### Governance / contract tests (reads JSON)

| Consumer | Purpose |
| --- | --- |
| `tests/test_ownership_registry.py` | **Sole JSON reader.** Registry path presence, direct-owner layer alignment, cross-file duplicate allowlist, embedded index coherence, schema v2 field guards, per-test `marker_set` presence. |

### CI (indirect)

| Workflow | Step |
| --- | --- |
| `.github/workflows/content-lint.yml` | `python -m pytest tests/test_ownership_registry.py -q` |
| `.github/workflows/convergence-checks.yml` | `python -m pytest tests/test_ownership_registry.py -q` |

### Generator / helper tests (no JSON read)

| Path | Role |
| --- | --- |
| `tools/test_audit.py` | Writer |
| `tests/test_test_audit_tool.py` | Helper unit tests only |

### Reporting / dashboard

**None.** No dashboard fixture or failure classifier reads `test_inventory.json`. Architecture audit references **docs and tool filenames**, not the JSON blob.

### Replay / protected manifest

**None.** `docs/testing/protected_replay_manifest.md` explicitly separates inventory regen from replay ownership. Golden replay uses its own manifest + `tests/test_golden_replay.py`.

### Documentation only (no JSON parse)

`tests/TEST_AUDIT.md`, `tests/TEST_CONSOLIDATION_PLAN.md`, `tests/README_TESTS.md`, `docs/architecture_ownership_ledger.md`, `docs/narrative_integrity_architecture.md`, `docs/convergence_ci_inventory.md`, `docs/current_focus.md`, `docs/post_evaluator_next_target_scan.md`, cycle R/L/AD closure notes, etc.

### Adjacent (not consumers)

| Path | Relationship |
| --- | --- |
| `tools/architecture_audit.py` | Scans `TEST_AUDIT.md` / `test_audit.py` keywords |
| `tests/validation_coverage_registry.py` | Parallel Objective #12 registry |
| `tools/refresh_protected_replay_manifest.py` | Separate replay manifest authority |

---

## 4. Duplication / staleness findings

See `cycle_aq_inventory_duplication_map.json`.

### External duplication (inventory vs canonical sources)

| Inventory field | Canonical source | Verdict |
| --- | --- | --- |
| `ownership_registry_index` | `RESPONSIBILITY_REGISTRY` in Python | **Derivable** at check time |
| `summary.declared_pytest_markers` | `pytest.ini` | **Derivable** |
| `files[].collected_nodeids`, `tests[]` | `pytest --collect-only` | **Derivable** |
| `files[].game_import_modules` | Test module AST | **Derivable** |
| Heuristic layers/themes/brittleness | Generator rules in `test_audit.py` | **Derived diagnostics** |
| Cross-file duplicate names | pytest collect + AST | **Derivable**; allowlist reasons live in Python only |

### Internal duplication (within JSON)

| Redundant pair | Notes |
| --- | --- |
| `files[].collected_nodeids` ↔ `tests[].nodeid` | Identical 4,247-item set when fresh |
| `files[].collected_test_names` ↔ `tests[].name` | Name suffix of nodeid |
| `files[].ownership_registry_positions` ↔ `ownership_registry_index.files_roles` | Must match; duplicated per file row |
| `cross_file_duplicate_test_names` ↔ `block_b_overlap_clusters` | Same collisions, two shapes |
| File-level hints copied into every `tests[]` row | `likely_architecture_layer`, `file_overlap_hints` |

### Staleness / drift risk

**Likely to go stale quickly**

- Entire `tests[]` array when tests are added/renamed/parametrized (+89 since last regen).
- `files[].collected_nodeids` / counts in `summary`.
- `feature_area_primary_counts`, spread rankings (diagnostic only).

**Slower-moving**

- `ownership_registry_index` (changes only when `RESPONSIBILITY_REGISTRY` edits).
- Registry-governed `files[]` rows (~41 paths in `files_roles`; 17 responsibility groups).

**Current drift examples (live − inventory)**

- New module: `tests/test_final_emission_sealed_fallback.py` (not in committed `files[]`).
- Renames/moves: acceptance-quality tests moved out of `test_final_emission_gate.py` into `test_acceptance_quality.py`; diegetic fallback test renamed (`legacy_diegetic` → `upstream_prepared_realization`).

**Automatic detection gaps**

| Gap | Impact |
| --- | --- |
| No live-vs-committed nodeid diff | Large silent drift (current +89 items) |
| No CI regen/`--check` | Contributors can merge stale JSON |
| New tests outside registry | **No inventory update required** unless registry edited |
| New registry direct_owner path | **Fails** governance until regen (path missing from `files[]`) |
| Deleted test file still in JSON | **Not detected** unless registry still references it |
| `test_inventory_per_test_rows_include_marker_set` | Requires `tests[]` in committed JSON |

---

## 5. Ownership boundary findings

### Who owns the inventory?

| Layer | Owner |
| --- | --- |
| **Runtime contract** | `tests/test_ownership_registry.py` + `tools/test_audit.py` trio |
| **Human map** | `tests/TEST_AUDIT.md` |
| **Practical direct-owner suite** | Governance tests in `test_ownership_registry.py` |
| **Ledger prose** | `docs/architecture_ownership_ledger.md` → concern `test inventory / governance docs` |

### Downstream suites that should **not** need inventory knowledge

- Gate, replay, evaluator, transcript, and smoke suites (assert behavior; only optional `# feature:` tags for heuristics).
- `tests/test_golden_replay.py`, failure dashboard probes, validation coverage registry consumers.
- Architecture audit (doc/tool keyword scan suffices).

### Leakage through inventory (diagnostic, not runtime)

- Gate-owned assertions do **not** leak via JSON; inventory heuristics may **label** gate-adjacent files (`likely_architecture_layer: gate`) but tests do not read that at runtime.
- `block_b_overlap_clusters` and `import_hub_modules` are **triage diagnostics** for consolidation campaigns — not CI gates except schema presence.
- Embedded registry index duplicates Python registry — useful for offline doc tooling, not for replay/manifest.

---

## 6. Refresh-flow findings

### Current refresh command

```bash
py -3 tools/test_audit.py
```

(from repo root; same interpreter as pytest)

### Gaps

| Expected capability | Status |
| --- | --- |
| Single regen command | **Exists** |
| `--check` / dry-run diff vs committed | **Missing** |
| CI regen or drift gate | **Missing** (`docs/convergence_ci_inventory.md` deferred) |
| Pre-commit hook | **None** |
| Separate inventory-only commit policy | **Documented** (Cycle AE recon) but not enforced |

### Determinism

- **Mostly deterministic:** sorted keys, stable ordering in lists.
- **Non-deterministic:** `summary.generated_utc` only.
- **Environment-sensitive:** requires working pytest collection (same as CI).

### Regen side effects

- Overwrites ~5 MB JSON → large PR noise when bundled with logic changes.
- Re-embeds registry from current Python (will match if registry unchanged).

---

## 7. Recommended AQ block sequence

Low-risk only; preserve governance test behavior and doc reporting intent.

| Block | Goal | Risk | Behavior change |
| --- | --- | --- | --- |
| **AQ1 — Drift visibility** | Add `tools/test_audit.py --check` comparing summary counts + registry path set + schema version to committed JSON (or `.git` HEAD). Optional CI step (~26 s). | Low | None |
| **AQ2 — Split artifact** | Commit slim `tests/test_inventory_governance.json` (files[] rows for registry paths + summary + cross-file dups + schema fields). Move full `tests[]` + triage aggregates to `artifacts/test_inventory_full.json` (gitignored or CI artifact). | Low | None if ownership tests read slim file or generator emits both |
| **AQ3 — Drop internal dupes** | Stop writing `files[].collected_nodeids` / `collected_test_names` when `tests[]` present (or drop `tests[]` — see AQ4). | Low | None |
| **AQ4 — Derive registry index** | Remove embedded `ownership_registry_index` from committed JSON; build at test time in `_load_inventory()` or in `--check`. Governance tests already compare to live `RESPONSIBILITY_REGISTRY`. | Low | None |
| **AQ5 — Narrow per-test retention** | If governance only needs `tests[].marker_set`, store marker map `{nodeid: marker_set}` for registry paths only (~41 files), not all 4k+ tests. | Low–medium | Requires adjusting `test_inventory_per_test_rows_include_marker_set` |
| **AQ6 — CI wiring** | Add `--check` to `convergence-checks.yml` (or content-lint) after ownership pytest; document in `docs/convergence_ci_inventory.md`. | Low | None (fails only when drift) |
| **AQ7 — Doc adapter** | `TEST_AUDIT.md` points to slim governance JSON for CI truth and documents full regen for local triage. | Low | None |

**Defer (higher risk or behavior-adjacent)**

- Removing heuristic/triage fields used by human consolidation workflows without a replacement report.
- Merging with `validation_coverage_registry.py` (different contract).
- Auto-regen on every CI run without check-first ( hides intentional stale windows).

---

## 8. Files likely needed for implementation

| File | AQ role |
| --- | --- |
| `tools/test_audit.py` | `--check`, split emitters, dedupe fields, optional slim schema v3 |
| `tests/test_ownership_registry.py` | Point `_INVENTORY_PATH` at slim file; derive registry index; adjust marker_set test scope |
| `tests/test_test_audit_tool.py` | Cover `--check` and new helpers |
| `tests/test_inventory.json` | Shrink or replace with governance subset |
| `.github/workflows/convergence-checks.yml` | Optional `--check` step |
| `.github/workflows/content-lint.yml` | Optional duplicate or sole drift gate |
| `docs/convergence_ci_inventory.md` | CI truth update |
| `tests/TEST_AUDIT.md` | Regen docs / dual-artifact explanation |
| `.gitignore` | If full diagnostic JSON moves to `artifacts/` |

**Probably not needed**

- Replay manifest, golden replay tests, validation coverage registry, architecture audit core logic.

---

## Commands run

```powershell
# Collection vs inventory drift
py -3 -c "import subprocess,sys,glob,json; from pathlib import Path; ..."

# Governance tests
py -3 -m pytest tests/test_ownership_registry.py tests/test_test_audit_tool.py -q

# Inventory size
(Get-Item tests/test_inventory.json).Length
(Get-Content tests/test_inventory.json | Measure-Object -Line).Lines

# Regen timing (reverted afterward — did not leave working tree changes)
Measure-Command { py -3 tools/test_audit.py }
git checkout -- tests/test_inventory.json
```

### Test results

| Command | Result |
| --- | --- |
| `py -3 -m pytest tests/test_ownership_registry.py tests/test_test_audit_tool.py -q` | **32 passed** |
| Live collect vs committed inventory | **+89 tests, +1 file** (stale but green) |
| `py -3 tools/test_audit.py` timing | **~26.3 s** (regen reverted) |

---

## Files to pass back if static recon insufficient

Static inspection was sufficient for this recon. Optional follow-up passes:

1. **`git diff tests/test_inventory.json`** after a fresh regen — quantify post-AQ baseline churn.
2. **Recent commits touching `test_final_emission_sealed_fallback.py` and acceptance-quality splits** — confirm registry neighbor updates needed in AQ1 refresh.
3. **CI runtime budget sign-off** — ~26 s collect+audit may affect which workflow hosts `--check`.
