# Realization Triage Ledger

Snapshot source:

- `artifacts/realization_layer_audit/realization_layer_audit.json`
- `artifacts/realization_provenance_audit/realization_provenance_audit.json`

Both audits are advisory, lexical, and intentionally noisy. This ledger records
triage value from the **Block AO** refresh snapshot; it is not a zero-findings
plan and it does not claim the architecture is fully converged.

# Executive Summary

## Audit Totals (Block AO refresh)

| Audit | HIGH | REVIEW | INFO | Total |
| --- | ---: | ---: | ---: | ---: |
| Realization layer audit | 1261 | 710 | 8945 | 10916 |
| Realization provenance audit | 958 | 1280 | 738 | 2976 |

## Post failure-locality pass interpretation

The realization layer is far better protected than raw audit counts imply.
Earlier milestones (through **Block S** in prior ledger language) added tests
and docs for upstream prepared emission provenance, diegetic fallback callers,
retry selectors and branches, `build_messages` projection-only behavior,
response policy enforcement mutation snapshots and manifest, opening fallback,
and final emission source/family snapshots. **Blocks AJ–AN** added API narration
hub route metadata extraction, contract guards, orchestration handoff ordering,
the `_apply_narration_hub_policy_handoff` adapter, and **Block AN** as an
explicit extraction stop point.

**Block AO** re-ran advisory audits, refreshed this ledger and
`docs/realization_cursor_handoff.md`, and added `docs/realization_failure_locality_closeout.md`
— **no production or prose changes.**

Remaining risk sits in **large behavioral surfaces** (`apply_response_policy_enforcement`,
`apply_final_emission_gate`, opening fallback ownership), not in missing tests for
the seams already pinned. Further runtime refactors should be **evidence-driven**
(bug, targeted audit finding, or approved design change), not churn for lexical counts.

# Completed Coverage / Extraction Work

## Block AO — failure-locality closeout

- Advisory audits re-run; totals updated in **Executive Summary** (this file) and
  `docs/realization_cursor_handoff.md`.
- **`docs/realization_failure_locality_closeout.md`** records program summary, risks,
  boundaries, and recommended stop point. No runtime or prose changes.

## Upstream Prepared Emission

- Covered by `tests/test_upstream_response_repairs.py` and
  `tests/test_realization_provenance.py`.
- Prepared answer/action/sanitizer payloads now carry
  `realization_fallback_family=upstream_prepared_emission`.
- Merge behavior normalizes missing, invalid, or legacy family values without
  changing emitted prose.
- Risk is lower: this module is noisy in audits, but it is now an intended
  upstream owner of contract-shaped fallback text.

## Diegetic Fallback Callers

- Covered by `tests/test_diegetic_fallback_narration.py`.
- Direct renderer output remains plain text; callers are responsible for
  provenance.
- Retry terminal callers label selected diegetic fallback as
  `retry_terminal_fallback`.
- Final emission opening repair labels the gate boundary as
  `legacy_diegetic_fallback`.
- Risk is lower at caller boundaries, but the renderer library remains legacy
  infrastructure and should not be rewritten for this block.

## Retry Fallback Selectors And Branches

- Covered by `tests/test_gm_retry.py`.
- `select_deterministic_retry_fallback_line(...)` and
  `select_terminal_retry_fallback_line(...)` exist and are documented in
  `docs/retry_fallback_selector_contract.md`.
- Deterministic retry branches now snapshot answer-context, known-fact,
  open-social, strict-social, uncertainty, and no-op behavior.
- Terminal retry branches now snapshot social terminal, nonsocial terminal
  anchor, and empty-social repair behavior.
- Risk is materially lower. Leave retry fallback mostly alone for now unless a
  Cursor pass needs a small selector/caller cleanup under the existing tests.

## build_messages Projection-Only Behavior

- Covered by `tests/test_build_messages_projection.py`.
- Tests assert supplied app/planner fields are projected without fallback
  authorship or provenance stamping.
- The legacy `resolution["hint"]` append is documented as prompt instruction
  projection, not player-facing fallback authorship.
- Risk is lower. Do not spend refactor budget here until larger ownership moves
  are complete.

## Response Policy Enforcement Split Readiness

- Covered by `tests/test_response_policy_enforcement_mutation.py`.
- `game/response_policy_enforcement_manifest.py` classifies metadata-only,
  validation-only, text-mutating, fallback/provenance-relevant, and legacy
  ambiguous subpaths.
- `docs/response_policy_enforcement_split_plan.md` records the intended split
  order without changing runtime behavior.
- Risk is lower for observation, but the function remains a high-risk post-GPT
  text mutation hub and still requires Cursor for the actual split.

## Opening Fallback And Final Gate Source Snapshots

- Covered by `tests/test_final_emission_gate.py` and
  `tests/test_diegetic_fallback_narration.py`.
- Opening deterministic fallback exact text, context source, failed-closed
  behavior, and FEM provenance are snapshotted.
- Final emission gate source branches now include snapshots for valid generated
  candidates, upstream prepared repairs, opening deterministic fallback, global
  scene fallback, and strict social terminal fallback.
- Risk is lower for branch identification. The final gate remains the largest
  and highest-risk behavioral surface.

# Low-Risk / Leave Alone For Now

- `game.upstream_response_repairs`: noisy but now protected as the upstream
  prepared emission owner. Keep metadata and payload shape stable.
- `game.diegetic_fallback_narration`: legacy render text is intentionally
  retained. Keep renderer text unchanged; enforce provenance at callers.
- `game.gm.build_messages`: treat as projection-only. Avoid prompt semantics
  refactors unless a test proves projection drift.
- Retry fallback selectors: the selector/caller boundary now exists. Avoid
  polishing unless needed for a specific high-value behavioral extraction.
- Final emission metadata helpers: keep them visible and noisy. They are
  observability infrastructure, not cleanup targets.

# Remaining High-Risk Behavioral Items

## apply_response_policy_enforcement split

- File/function: `game/response_policy_enforcement.py::apply_response_policy_enforcement` (compatibility re-export: `game.gm`)
- Current status: orchestration + contract helpers moved to runtime owner (Block AI1); manifest/runtime alignment complete (Block AI2). Mutation snapshots and split-readiness manifest exist.
- Remaining risk: the function still mutates `player_facing_text` after GPT and
  before final emission. Some paths are ordinary deterministic enforcement,
  while validator voice, secret leak guard, scene momentum, passive escalation,
  and topic pressure are fallback/provenance-relevant.
- Required future action: Cursor should split metadata projection and
  validation-only work from text-mutating enforcement, preserving exact current
  order and emitted text. Start with metadata-only helpers, then validation-only
  state/update normalization, then deterministic text-mutating helpers. Leave
  fallback/provenance-relevant paths until each has branch-specific assertions.
- Risk: HIGH.

## Opening fallback ownership move upstream

- File/functions:
  `game/final_emission_gate.py::_deterministic_opening_fallback_text_and_meta`,
  `_opening_scene_safe_fallback_tuple`, `_enforce_response_type_contract`
- Current status: exact fallback text, source context, failed-closed behavior,
  family classification, and FEM provenance are covered.
- Remaining risk: the gate still composes opening fallback prose from curated
  opening facts. The inputs are bounded and tested, but ownership belongs
  upstream of final emission.
- Required future action: Cursor should move opening fallback authorship into an
  upstream prepared opening payload while preserving exact text and metadata.
  The final gate should select prepared opening fallback text and record source,
  not compose the line.
- Risk: HIGH.

## final_emission_gate gate-local fallback reduction

- File/function: `game/final_emission_gate.py::apply_final_emission_gate`
- Current status: final source/family snapshots cover important branches, and
  opening fallback provenance is explicit.
- Remaining risk: the gate remains the largest dependency hub for candidate
  validation, prepared emission selection, strict social terminal output,
  fallback containment, global scene fallback, opening fallback, and metadata
  packaging.
- Required future action: Cursor should reduce gate-local prose authorship one
  branch at a time. Start only with branches backed by prepared upstream text or
  sealed fallback pools. Do not rewrite the whole function broadly.
- Risk: EXTREME.

## API narration hub simplification

- File/function: `game/api.py::_build_gpt_narration_from_authoritative_state`
- Current status (**Blocks AJ–AM + Block AN stop point**): Path-selection and Block AL
  orchestration handoff order are snapshotted; route metadata helpers are contract-tested;
  `_apply_narration_hub_policy_handoff` isolates the response-policy seam after GPT/retry.
  **Block AN** (`test_block_an_*`) guards the extraction boundary and registers Block AL /
  Block AM test names — treat further hub extraction as **paused** unless a concrete bug or
  audit finding warrants it. Safe follow-up work is **docs and advisory audit refresh** only.
- What stays in the hub on purpose: CTIR/planner/bundle setup, prompt construction,
  GPT/retry/upstream-fallback orchestration, GM merges from prompt payload, policy handoff
  adapter call, finalize annotations (`annotate_narration_path_kind`, continuation
  classification). Final emission remains **`api_turn_support`** / `apply_final_emission_gate`.
- Remaining risk if someone reopens the hub: orchestration edits can still change semantics
  without touching obvious text owners; rely on Block AL ordering tests and narrow regressions.
- Required future action: **no broad hub extraction** for failure-locality unless justified;
  otherwise refresh documentation and re-run advisory audits as needed.
- Risk: **Mitigated for extraction churn** by AJ–AN tests; behavioral edits to the hub body
  remain **HIGH** and should stay rare and evidence-driven.

## Retry fallback: current status / likely leave alone for now

- File/functions:
  `game/gm_retry.py::apply_deterministic_retry_fallback`,
  `force_terminal_retry_fallback`,
  `select_deterministic_retry_fallback_line`,
  `select_terminal_retry_fallback_line`
- Current status: selectors exist, selector purity is tested, branch outputs are
  snapshotted, and retry family metadata is asserted.
- Remaining risk: retry fallback still authors emergency text from bounded
  inputs after GPT/retry failure, but that is now explicit and local.
- Required future action: likely leave alone for now. If touched, prefer
  metadata/debug cleanup under the existing selector contract rather than
  changing branch behavior.
- Risk: MODERATE after current coverage; HIGH only if prose behavior changes.

# Recommended Refactor Order

## Codex-safe audit/test work

1. Re-run advisory audits and refresh docs when runtime changes land.
2. Add narrow tests only when they freeze current behavior or metadata shape.
3. Keep `docs/realization_cursor_handoff.md`,
   `docs/realization_failure_locality_closeout.md`,
   `docs/retry_fallback_selector_contract.md`, and
   `docs/response_policy_enforcement_split_plan.md` in sync.
4. Do not wire the advisory audits into CI yet.
5. Do not change production prose or behavior in Codex cleanup passes.

## Cursor-required behavioral work

1. Split `apply_response_policy_enforcement` metadata/validation paths away
   from text-mutating enforcement.
2. Move opening fallback authorship upstream while preserving exact fallback
   text and provenance snapshots.
3. Reduce `final_emission_gate` fallback authorship branch-by-branch, starting
   only with prepared or sealed sources.
4. **API narration hub:** Blocks AJ–AM delivered; **Block AN** documents a **stop point**
   — do not resume hub extraction unless bug- or audit-driven; safe work is docs/audit
   refresh (`docs/realization_cursor_handoff.md`, this ledger).
5. Revisit retry fallback last, and likely leave it unchanged unless the above
   work exposes a concrete local cleanup.

# Explicit Non-Goals

- Do not claim audit findings should be zero.
- Do not refactor behavior as part of ledger refresh.
- Do not change runtime prose.
- Do not broaden `final_emission_gate` rewrites. It is the most dangerous place
  to make sweeping changes because many branches now rely on source/provenance
  snapshots.
- Do not move diegetic fallback renderer text just to quiet lexical findings.
