# NEXT_SESSION

Start here:

```text
Read docs/DEVELOPMENT_CONSTITUTION.md, then docs/NEXT_SESSION.md and the
authoritative documents it identifies, before beginning substantive work.
```

## Project

Ashen Thrones

## Current Era

Product Realization

## Last Completed Cycle

`PR-AR — AI Experience / Gameplay: Perception Narration Authority and Audible Non-Invention`

Housekeeping after PR-AR: repository runtime / development / archive
boundaries, then a Git checkpoint of accumulated Product Realization
(PR-AC through PR-AR) plus that reorganization. See
`development/reports/REPOSITORY_ORGANIZATION_runtime_development_archive_boundaries.md`.

## Current Objective

Proceed from PR-AR evidence toward the highest-leverage remaining obstacle to
ordinary play: observe fallback stock repeatedly appending the same two-fact
gate pair after a now-grounded listen/observe turn.

Repository organization did not change this Product Realization priority.

## Established Facts

- Architecture Reconciliation Era completed; Campaign 6 chassis closed
  (`development/campaigns/reconciliation/AR-CA_campaign6_chassis_strategy_closeout.md`).
- Repository organization completed. Campaign reports live under
  `development/campaigns/`. Generated evidence stays in `artifacts/`.
  Disposable pytest/agent output goes to `development/tmp/`. Agents load
  Constitution → `NEXT_SESSION` → named authorities only; do not recursively
  load the development archive.
- Validation authority hierarchy:
  - structural PASS ≠ semantic playability
  - automated playability PASS = SUPPORTING_EVIDENCE
  - behavioral gauntlets = DIAGNOSTIC
  - protected replay = controlled structural/runtime invariants, not live-model
    semantic quality
  - semantic calibration = primary calibrated semantic authority
- RC-10 = A and RC-21 = B + C are implemented. See
  `docs/rc10_rc21_policy_implementation.md`.
- AI is not authoritative over mechanics or state. Narration does not
  instantiate an NPC.
- PR-AD through PR-AQ remain as previously established. Do not reopen them
  without new causal evidence.
- PR-AQ remains settled: T16 walk+listen is existing `observe`; local walking
  is existing `custom`; local movement ≠ scene travel; listen is perception,
  not sound creation.
- PR-AR found the remaining T16 failure to be CLASS I with earliest causal
  defect CLASS A. HA focus treated a visual crowd/presence fact as
  `speaking_group` and told the model to prefer voices. Downstream perception
  grounding did not flag unsupported speech/audible events, so invented
  whispers/complaints survived. Structured state did not mint them; that was
  not sufficient.
- First incorrect authority decision: `resolve_implicit_human_adjacent_focus`
  + `_hint_for_focus_bundle` licensed speech from visual presence.
- Authoritative T16 perception input on the live scene file: people/cluster
  and written notice facts exist; no authored current whisper/complaint/
  overheard-topic fact exists. Presence ≠ speech. Empty listen may use
  existing diegetic quiet.
- Narration-context finding: the HA hint overstated crowd facts as audible
  authority. Prompt-contract change was limited to those HA hints.
- Post-generation finding: category grounding now covers speech-act and
  cross-modal perceptible events against the authorized blob. Not a noun
  blacklist.
- Final-emission finding: FEM did not independently catch T16 speech.
  Replacement uses existing quiet / authorized facts. PR-AP was not reopened.
- Atmosphere vs assertion: limitation/quiet texture may remain; speakers,
  speech, events, and evidence may not be invented.
- No new sound system, perception owner, or world-authority owner. No
  canonical Frontier Gate sound/speech was added to make T16 valid.
- Authorized audible facts and authored current speech can still be realized
  and paraphrased. Unsupported expansion fails closed.
- Invented time/count/price/redirect are RELATED BUT DISTINCT seams, not
  permission to start a project-wide State ↔ Narration campaign.

## Decisions Pending

None. No user decision is required before the next slice.

## Decisions Made

- RC-10 = A. Evidence-only raw-token fence.
- RC-21 = B + C. Authored-scene follow-up plus canonical lead registry.
- PR-AC through PR-AQ decisions remain as previously recorded.
- PR-AR confirmed existing observe / HA listen / perception grounding can
  represent audible non-invention once visual presence is not treated as
  speech authority.
- PR-AR confirmed player hypothesis, recent prose, and NPC presence do not
  authorize overheard speech.
- The generalization principle (content may be specific; systems must be
  general) lives in `docs/product_realization_validation.md`.

## Current Known Defects

Dominant class: observe fallback stock repeatedly appending the same two-fact
gate pair on look-around / some listen replacements.

Severe sibling residue:

- T13 `already_searched` can still truncate (`with…`).
- Live model can still invent a time, count, price, or redirect when the
  engine correctly has no authored social answer.
- Replay / opening `Gate Guard mutters` / `"Word is,"` can still appear.
  Do not reopen PR-AI without new causal evidence.
- Untargeted look-around can still repeat the same two-fact gate stock.
- Some natural paraphrases (`posted notices`) still miss `notice_board`.
- Follow-up paraphrases that do not overlap an owned topic or landed public
  clue can still refuse.
- Addressing `"Gate Serjeant"` can resolve to `gate_guard`.
- Post-return observe can still bleed prior-scene geography.
- Local observation questions (`What's nearby?`) can collapse.
- Unresolved travel can still be narrated as scene stock.
- Evaluator lexical false negatives on short grounded-absence listen lines.
- `"The guard says"` generic absent-speaker label.

A Windows `PermissionError` on shared pytest temp remains environmental.

## Authoritative Documents

1. `docs/DEVELOPMENT_CONSTITUTION.md`
2. `development/campaigns/product_realization/PR-AR_perception_narration_authority_audible_non_invention.md`
3. `development/campaigns/product_realization/PR-AQ_physical_action_typing_compound_perception_realization.md`
4. `docs/product_realization_validation.md`
5. `development/campaigns/product_realization/PR-AH_grounded_observation_non_invention.md`
6. `development/campaigns/product_realization/PR-AJ_authoritative_lead_provenance_social_prose_non_ingestion.md`
7. `development/campaigns/product_realization/PR-AO_investigation_result_provenance_non_invention.md`
8. `development/campaigns/product_realization/PR-AP_grounded_refusal_realization_grammar.md`
9. `docs/state_authority_model.md`
10. `docs/rc10_rc21_policy_implementation.md`
11. `docs/semantic_validation_calibration.md`
12. `development/campaigns/reconciliation/AR-AD_target_architecture_doctrine.md`
13. `docs/review_handoff_standard.md` (review export only; not this handoff)
14. `development/README.md` (directory taxonomy only)

## Validation Baseline

PR-AR perception-narration tests: passed
(`tests/test_perception_narration_authority_audible_non_invention.py`).

PR-AD through PR-AQ owner tests, intent parser, HA listen, observation,
investigation, referenced surface, fallback-behavior, narration-consistency,
state-authority, clue, FEM validator/repair, and calibration-corpus focused
files: green except documented pre-existing reds, 0 new failed from PR-AR.

Round #1 calibration corpus recheck: 13/13
(`artifacts/prar_perception_authority/round1_calibration/`).

Extended R2-MT01-AR replay:
`artifacts/prar_perception_authority/extended_replay/`.

Freeform perception-authority probe:
`artifacts/prar_perception_authority/freeform_probe/`.

Authoritative full suite last recorded before later Product Realization
cycles: 6,450 collected, 6,351 passed, 0 failed, 99 skipped
(`artifacts/policy_implementation/post_implementation_suite.xml`).

PR-AR did not re-run that full suite. Remaining known reds are BY3/BY4/BZ
mutation-attribution generators and frontier-gate long-session golden replay
from intended player-facing realization changes. Those baselines were not
weakened. Do not treat a structural result as semantic playability.

## Deliberately Deferred Residue

Leave these deferred unless later evidence elevates them:

- Absent-speaker `"The guard says"` default label.
- `compat_pending_lead_needed` still keys off a scene target only.
- Intent parsing still reads `pending_leads` as the pursuit surface.
- Broader lead/clue overlap reduction (`docs/current_focus.md`).
- `_TEXT_LEAD_SPECS` compatibility text-hook library.
- House Verevin / rooftop invention.
- Remaining scene-transition Unicode / operator-encoding.
- PR-AB tooling / product-integrity concern.
- General prompt rewrite or NPC dialogue redesign.
- New authoritative knowledge store.
- Project-wide State ↔ Narration campaign.
- Protected-replay baseline refresh.
- Filling other stub scenes (`eastern_square`, `wild_moors`, `alley`, …).
- Broad observation-variety work, except as required to stop stock stacking
  if that becomes the selected slice.
- Automatically turning mentioned nouns into interactables.
- Adding a roster-board interactable that existing content does not justify.
- Adding a stew price or menu/economy simulation.
- Adding last-reader / board-history facts merely to answer T14.
- Adding patrol timing or personnel merely to answer T15.
- Adding canonical Frontier Gate sounds merely to make listen interesting.
- New conversation-state stack or second global router.
- Comprehensive compound-intent / N-action execution.
- Coordinate-level local movement or five-senses simulation.
- Deleting `remember_recent_contextual_leads`.
- Flattening all refusals to `"I don't know."`
- Universal grammar checker / prose-rewriting layer.

Do not treat residual lead-system items as open RC-10/RC-21 questions.

## Do Not Reopen Without Evidence

- Validation-authority hierarchy
- RC-11 / RC-13 expectation maintenance
- GD-01 CO99 governance-context advance
- Confirmed baseline repair and validation cleanup
- Semantic calibration as semantic authority
- Protected replay as structural/runtime authority
- Architecture Reconciliation chassis doctrine
- RC-10 = A
- RC-21 = B + C
- Existing state/domain owners
- PR-AD through PR-AQ settled decisions listed in the prior handoff
- PR-AR's decision not to add a new sound system, perception owner, or
  world-authority owner
- PR-AR's visual-presence ≠ speech-authority boundary
- PR-AR's treatment of empty listen as valid grounded absence
- PR-AR's refusal to start a project-wide State ↔ Narration campaign from
  auditory invention alone
- PR-AQ's local-movement ≠ scene-travel boundary
- PR-AQ's treatment of listen as perception attempt, not sound creation
- Repository file-placement taxonomy in the Constitution (`game/`/`data/`/`static/`
  runtime; `docs/` governance; `development/campaigns/` reports; `artifacts/`
  generated evidence; `development/tmp/` disposable output)

## Recommended Next Action

Observe fallback stock after repaired T16 perception: listen/observe is now
typed and no longer invents whispers/complaints, but ordinary look-around and
some listen replacements still append the same two gate facts.

Primary lane: AI Experience. Secondary lane: Gameplay.

PR-AR repaired perception narration authority. The next ordinary-play blocker
is observe-stock repetition, not a missing action type, not a stew price, and
not a broader State ↔ Narration campaign unless later evidence outranks this
stock-stacking residue. T13 already_searched truncation and opening-mutter
residue are siblings. Do not reopen PR-AR grounding, PR-AQ typing, PR-AP
grammar, PR-AO provenance, PR-AH confrontation grounding, or PR-AI ownership
unless new evidence shows they cause the stock-stacking failure. Do not start
pricing/economics.

No user decision is required.

## Minimum Files for the Next Agent

- `docs/DEVELOPMENT_CONSTITUTION.md`
- `development/README.md`
- `development/reports/REPOSITORY_ORGANIZATION_runtime_development_archive_boundaries.md`
- `development/campaigns/product_realization/PR-AR_perception_narration_authority_audible_non_invention.md`
- `artifacts/prar_perception_authority/extended_replay/runs/20260920T221938Z_R2-MT01-AR/transcript.md`
- `artifacts/prar_perception_authority/freeform_probe/20260920T222131Z_probe.md`
- `development/campaigns/product_realization/PR-AH_grounded_observation_non_invention.md`
- `game/diegetic_fallback_narration.py`
- `game/perception_grounding.py`

## Git / Worktree Caveats

This remains one Git repository. No second repository was created.
Historical campaign files remain in Git at their new paths under
`development/campaigns/` and `development/archive/`.

The Product Realization checkpoint through PR-AR plus repository
organization has been committed on `feature/product-realization`.
Disposable replay mutations in `data/session.json`, `data/world.json`,
`data/combat.json`, and `data/session_log.jsonl` were restored before
that commit. `data/scenes/old_milestone.json` was kept as intentional
PR-AF destination content.

Future pytest/agent scratch goes to `development/tmp/` and is Git-ignored.
No root `codex_pytest_tmp*` directories remained at checkpoint time.

## Last Updated

2026-09-20 / Product Realization checkpoint through PR-AR and repository
reorganization
