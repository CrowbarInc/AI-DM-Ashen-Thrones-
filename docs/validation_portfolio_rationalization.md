# Ashen Thrones Validation Portfolio Rationalization

Date: 2026-09-18

## Executive conclusion

Ashen Thrones currently carries **19 validation families** across several development eras. The
recommended portfolio is not a single ladder in which every green result means "the game works."
It is a layered evidence architecture with explicit owners:

- **8 RETAIN** because they provide distinct, current evidence.
- **3 CONSOLIDATE** because their useful signals overlap a stronger surviving authority.
- **3 MODERNIZE** because their purpose remains current but implementation or governance is stale.
- **3 RECLASSIFY** because their present names or authority overstate what they prove.
- **1 QUARANTINE** pending confirmation of post-reconciliation ownership policy.
- **1 RETIRE** because historical closeout prose is not a current product requirement.

The 49-test red baseline does not mean 49 product defects. This audit finds **7 likely current product
regressions**, **9 likely current architecture regressions**, **13 documentation-drift failures**,
**9 registry/governance drift failures**, **9 stale expectations**, **1 stale fixture**, and **1
uncertain failure**. Only 9 of the 16 likely current regressions are high-confidence. Classification
does not waive any failure; it determines what question must be answered before repair.

No test, gate, evaluator, fixture, gameplay path, prompt, threshold, calibration policy, or CI rule was
changed. This report proposes later work only.

## Method and scope

The audit reused the Simulated Playtest Observability Audit, Validation Reliability Audit, Semantic
Validation Calibration, Reactive/Adversarial Players, Validation Evidence Standard, Review Handoff,
repository source, current CI configuration, architecture history, and the full-suite run made on
2026-09-18. The machine-readable authority is
`data/validation/validation_family_registry.json`; the generated concise view is
`docs/validation_family_registry.md`.

Family boundaries are conceptual. The 6,433 collected pytest cases overlap multiple systems, so the
registry uses approximate counts rather than pretending every parametrized case has one exclusive
owner. Every current failing test is mapped exactly once.

## Claim classes

The portfolio uses overlapping claim classes rather than an aggregate confidence score:

| Claim class | Establishes | Does not establish |
|---|---|---|
| Structural / Contract | Schemas, imports, ownership, serialization, deterministic invariants | Runtime survivability or prose quality |
| Runtime Integration | Selected production components execute together | Semantic relevance or broad player behavior |
| Semantic Behavioral | A bounded evaluator/human judgment about interaction quality | State truth, broad realism, or unrestricted play |
| State / World Consistency | State and narration/content facts agree within checked scope | General prose quality or fun |
| Human Realism | A human or validated model resembles plausible play within reviewed scope | Product correctness |
| Stress / Adversarial | Boundary-pushing probes survive or expose failures | Typical-player frequency |
| Human Reviewed | A person explicitly judged evidence | Reproducibility outside that evidence |
| Governance / Repository | Declared architecture, provenance, and repository policy agree | Runtime or gameplay quality |

## Authority model

`RELEASE_GATE` is reserved for current deterministic product or architecture requirements.
`CAMPAIGN_GATE` blocks only relevant campaign closure. `SUPPORTING_EVIDENCE`, `DIAGNOSTIC`, and
`WARNING` can influence judgment without independently invalidating the product. `CALIBRATION_TOOL`
measures validator meaning. `MANUAL_REVIEW` makes human judgment authoritative.
`DEVELOPMENT_UTILITY` assists implementation. `HISTORICAL_ONLY` preserves provenance without gating.

No current automated system has sole semantic authority. Human-reviewed evidence is authoritative for
consequential semantic judgments; calibration defines evaluator boundaries; reactive players,
scenario spine, and the playability runner produce complementary evidence.

## Portfolio findings

### What should remain authoritative

- Unit/component contracts and API integration remain release gates within their assertion boundaries.
- Final-emission contracts remain essential, but their compatibility and ownership surface needs
  modernization without weakening emission safety.
- Protected replay remains a controlled structural runtime gate. Its name/reporting must stop implying
  live-model or semantic authority.
- Ownership/import guards should remain potentially authoritative, but are quarantined as a policy
  decision because current failures mix concrete bypasses with possible compatibility-era rules.
- Content lint should become a relevant content-campaign gate after its currently ignored CI semantics
  are made intentional.
- Validation Evidence and Review Handoff remain campaign gates for evidence and review delivery, not
  product-quality gates.

### Semantic hierarchy

1. **Human authority:** Manual gauntlet reviews and explicit human labels on preserved evidence.
2. **Calibration authority:** The semantic calibration corpus defines what automated evaluator outputs
   mean for included concepts.
3. **Evidence generation:** Reactive/adversarial players, scenario spine, playability runtime, and
   manual runs exercise different temporal/input shapes.
4. **Automated evaluation:** Playability and behavioral checks supply bounded signals. Neither is a
   sole semantic verdict.
5. **Controlled development evidence:** N1 and synthetic sessions prove deterministic harness/state
   contracts, not live-model quality or human realism.

The playability name is presently misleading because a PASS can coexist with a serious semantic miss.
The protected replay term "live" is also misleading where the GM response is stubbed. Behavioral
gauntlet rules should become named diagnostics under calibration rather than a parallel semantic
authority. None of these systems is obsolete merely because calibration/reactive work is newer.

### Structural hierarchy

The intended structural authority is: subsystem owner contracts, API integration, selected protected
runtime replay, static content integrity, and explicitly affirmed architecture boundaries. Replay
projection dashboards, trend histories, generated registries, and closeout documents support those
owners; they should not acquire duplicate release authority merely because they are easy to assert.

Architecture Reconciliation strengthens the case for current facade and owner boundaries, but weakens
the authority of temporary compatibility counts, byte snapshots, migration aliases, and historical
campaign-document requirements. Age alone was not used as a retirement criterion.

## Overlap and duplication

| Area | Overlapping families | Deliberate future split |
|---|---|---|
| Final emission | Owner contracts, protected replay, replay diagnostics | Owner tests gate local contract; protected replay gates selected integration; trend/projection remains diagnostic |
| Short semantic interaction | Playability, calibration, reactive players, manual gauntlet | Runtime generates evidence; calibration interprets automation; human review owns ambiguous/high-consequence verdicts |
| Long sessions | Scenario spine, N1, synthetic sessions | Scenario spine covers production scripted runtime; synthetic lane owns deterministic harness contracts |
| Behavioral heuristics | Playability evaluator, behavioral gauntlet, calibration | Calibration owns meaning; heuristic checks become features/diagnostics |
| Architecture | General audits, import/ownership guards, generated registries | Affirmed boundaries gate; inventories and movement reports diagnose |
| Review/provenance | Evidence Standard, Review Handoff | Evidence Standard defines behavioral evidence; Handoff delivers selected review material |

Redundancy remains where mechanisms fail differently. The recommendation removes duplicate authority,
not every repeated observation.

## Mock and stub authority

Mocks are appropriate for deterministic orchestration and failure-path control. The defect is inflated
claim scope:

- API tests with a patched GM prove request/state/response plumbing.
- Protected replay with fixed GM text proves selected pipeline invariants.
- Synthetic/N1 runs prove harness and state contracts.
- Behavioral gauntlet rows prove only that supplied text avoids enumerated patterns.

None proves production-model semantics. Real configured runtime is exercised by campaign-operated
playability, scenario-spine, reactive-player, and manual-gauntlet runs. Even there, automated scores
remain bounded and preserved transcripts matter.

## Current red baseline

Command: `python -m pytest -q --tb=short`

Result: **49 failed from 6,433 collected tests**. The retained output did not preserve the final
pass/skip breakdown, so this audit does not infer it. One existing Starlette TestClient deprecation
warning was present. The exact failure
records and rationale are in
`artifacts/validation_portfolio/current_failure_classification.json`.

| Likely cause | Count | Representative meaning |
|---|---:|---|
| Current product regression | 7 | NameError in social fallback; blank-scene narration; missing actionable leads |
| Current architecture regression | 9 | Direct authority imports, unregistered write paths, validation-layer separation |
| Documentation drift | 13 | Missing BW/BZ historical closeout files |
| Registry/governance drift | 9 | Attribution completeness, classifier manifests, marker count |
| Stale expectation | 9 | Historical percentages, byte snapshots, compatibility counts |
| Stale fixture | 1 | Canonical replay input no longer triggers historical repair eligibility |
| Uncertain | 1 | Long-session diagnostic stability requires reproduction |

The defensible answer to the "49 failures" question is therefore: **7 likely current product defects,
9 likely architecture defects, 32 likely stale/administrative/registry/fixture failures, and 1
uncertain**. That is not permission to bulk-delete 33 tests. Medium/low-confidence classifications
require owner confirmation, and registry drift can expose a real architecture problem underneath.

## Maintenance cost

Very-high burden clusters are final-emission contracts, replay projection/diagnostics, and architecture
governance. Historical evidence shows repeated expectation cascades across final-emission metadata,
projection, failure classification, dashboards, and generated docs. High burden includes the broad
pytest estate, protected replay, scenario spine, and import/ownership scans. New evidence/handoff
standards are low burden because they package explicit sources and do not duplicate product judgment.

The target is ownership locality: one authoritative contract per property, with downstream diagnostics
consuming it. Maintenance burden alone does not justify retirement.

## Validation gaps

| Gap | Importance | Partial coverage | Likely authority | Timing |
|---|---|---|---|---|
| State to narration consistency | Critical | Content lint, metadata, selected replay assertions | Future dedicated state/narration contract plus reviewed evidence | Before 1.0; design after this review |
| NPC/hidden-fact knowledge consistency | High | Scenario scripts and local state tests | State/world consistency layer | Before 1.0 for core flows |
| Long-session semantic continuity | High | Scenario spine and manual runs | Scripted runtime evidence plus human review | Before 1.0, initially manual-supported |
| Rendered browser workflow | High | Backend UI policy tests only | Browser automation and targeted visual review | Before 1.0 |
| Player-to-GM vs character authority | High | Preserved calibration disagreement | Calibration corpus then runtime evidence | Before broad semantic gating |
| General ambiguity/clarification | High | One ambiguous reactive case | Human-labeled calibration | Before broad semantic gating |
| Realistic human player behavior | Moderate | Manual runs; reactive players are intentionally adversarial | Human sessions/curated traces | Manual/deferred automation |

Do not build every gap simultaneously. State/narration consistency and rendered core workflow are the
largest absent product authorities; semantic concept gaps should be expanded through calibration, not
an unvalidated generative-player score.

## Target validation architecture

1. **Repository and governance integrity:** affirmed architecture boundaries, ownership/import guards,
   evidence provenance, and review delivery. Administrative reports support but do not gate.
2. **Structural and contract correctness:** subsystem tests, final-emission owner contracts, and content
   integrity.
3. **Runtime integration correctness:** API integration and a small controlled protected-replay gate.
4. **State and world consistency:** current content checks plus a future state/narration authority.
5. **Semantic interaction correctness:** human judgment owns consequential verdicts; calibration owns
   evaluator meaning; runtime systems generate inspectable evidence.
6. **Long-session behavioral consistency:** scenario spine plus human-reviewed sustained sessions.
7. **Rendered player experience:** currently absent; future browser workflow authority.
8. **Human spot-check and calibration:** manual gauntlets and maintained boundary corpus.

Each layer reports separately. There is no aggregate "game quality" score.

## Staged rationalization plan

### Stage A: Safe retirement

After human approval, archive/recover any available BW/BZ provenance and retire the 13 historical
closeout-document assertions as current gates. Do not delete first.

### Stage B: Reclassification

Rename/report controlled protected replay, playability, and synthetic sessions according to their
actual claim boundaries. Change authority only through an explicit policy change.

### Stage C: Consolidation

Move unique behavioral-gauntlet diagnostics under semantic calibration; merge N1 deterministic
contracts into synthetic-session ownership; separate authoritative replay invariants from projection
and trend diagnostics. Prove equivalent coverage before removal.

### Stage D: Modernization

Localize final-emission ownership contracts, separate architecture gates from generated parity, and
make content-lint CI treatment intentional. Preserve the purposes named in the registry.

### Stage E: Baseline repair

Reproduce and repair confirmed product defects, then reaffirm/fix current architecture violations.
Update stale registries only after deciding whether source or policy is authoritative.

### Stage F: Gap development

Design state/narration consistency, core browser workflow validation, semantic concept expansion, and
long-session human-reviewed evidence in that order of product risk. This campaign implements none.

## Risk analysis

- Retiring closeout assertions loses no runtime protection, but may lose historical intent; archive or
  explicitly record unavailable provenance first.
- Consolidating replay diagnostics can lose trend/recurrence visibility; inventory unique reports and
  preserve read-only history before changing gate ownership.
- Consolidating N1 can lose deterministic branch fingerprints; migrate those exact contracts.
- Consolidating behavioral gauntlet can lose named reason codes; preserve them as calibrated features.
- Modernizing final emission must preserve player-facing safety, owner metadata, and fallback/repair
  boundaries throughout replacement.
- Quarantining ownership/import governance is not disabling it. The project needs an explicit map of
  which post-reconciliation facades and writers remain authoritative before any waiver or repair.

## Human decision surface

### Decision 1: Historical closeout assertions

**Question:** Should BW/BZ closeout-document existence remain a current release condition?

**Recommendation:** No; archive provenance and retire the gate. **Confidence: high.** Keeping it means
13 administrative failures remain coupled to product readiness. Retiring without archival review risks
losing historical context.

### Decision 2: Ownership and import policy

**Question:** Which currently flagged facade/write-path rules remain intentional after Architecture
Reconciliation?

**Recommendation:** Reaffirm the desired map before repair; keep the family quarantined meanwhile.
**Confidence: medium.** Enforcing all rules blindly may restore obsolete compatibility boundaries;
waiving them blindly may erase deliberate ownership.

### Decision 3: Semantic campaign gate

**Question:** Should automated playability PASS independently close player-facing campaigns?

**Recommendation:** No. Require inspectable runtime evidence plus human review for consequential claims
until calibration is broader. **Confidence: high.** The cost is human attention on selected evidence;
the benefit is avoiding demonstrated false confidence.

### Decision 4: Replay diagnostic authority

**Question:** Should projection snapshots, trend histories, and recurrence dashboards independently
block release?

**Recommendation:** Only a named minimal invariant set should gate; the remainder should diagnose.
**Confidence: medium.** Consolidation reduces churn but must preserve unique recurrence visibility.

## What successful rationalization preserves

After approved retirement and eventual consolidation/modernization, Ashen Thrones would still retain:
local contracts, API wiring, final-emission safety, controlled protected runtime paths, content
integrity, affirmed architecture ownership, scripted long-session evidence, calibrated semantic
interpretation, reactive stress evidence, human judgment, and portable provenance/review.

It would lose only mandatory historical closeout prose and duplicate authority in synthetic,
behavioral, replay-projection, and generated-governance layers. Unique fingerprints, reason codes, and
trend history must migrate before deletion. The resulting estate is more trustworthy because every
green or red signal has a named claim boundary and owner, not because the raw test count is smaller.

## Limitations

- Family counts are architectural groupings, not exclusive per-test partitions.
- Failure classifications are evidence-based triage, not root-cause proofs; 23 are medium confidence
  and 2 are low confidence.
- No gameplay was rerun for this audit; preserved behavioral evidence was sufficient for authority
  analysis.
- CI authority was read from current configuration and prior audit findings; this campaign did not
  change it.
- Git history establishes eras and churn patterns but cannot recover every original design intent.
- Browser validation and generalized state/narration consistency remain absent, so no existing PASS can
  cover them.

## Commands executed

```powershell
Get-Content -LiteralPath 'C:\Users\Master Mandalcio\.codex\attachments\1631008a-21c6-4d48-b6d3-7f86278c4b50\pasted-text.txt' -Raw
rg --files tests tools scripts .github data\validation artifacts
rg -n "pytest|gauntlet|playability|golden_replay|scenario_spine|synthetic|validation" pyproject.toml pytest.ini setup.cfg tox.ini .github README.md docs
git log --oneline -40

& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools\build_validation_portfolio.py

$env:PYTHONPATH='.\.venv\Lib\site-packages'
& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m pytest tests\test_validation_portfolio.py tests\test_review_handoff.py -q --tb=short

& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m pytest tests\test_validation_portfolio.py tests\test_review_handoff.py `
  tests\test_validation_evidence_standard.py tests\test_semantic_calibration_corpus.py `
  tests\test_reactive_player_validation.py -q --tb=short

& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  tools\build_review_handoff.py `
  --config data\validation\review_handoffs\validation_portfolio_rationalization.json `
  --generated-at 2026-09-18T05:00:00+00:00
```

The full-suite baseline command `python -m pytest -q --tb=short` was completed immediately before this
campaign's classification work and supplied the current 6,433-case, 49-failure input.
