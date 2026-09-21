# Validation Evidence Standard

> **No important player-facing PASS without inspectable behavioral evidence.**

> **Tests may remain numerous and sophisticated. Evidence must remain simple enough for a human to inspect.**

## Purpose

This standard governs claims about player-facing behavior in Ashen Thrones. Automated validation
remains essential, but a green check, score, percentage, test count, campaign summary, or completion
statement is not by itself evidence of semantic gameplay quality.

The standard exists because historical playability runs counted unanswered intent, broken refusals,
unfulfilled observations, and `Tavern Runner mutters,` as overall PASS. Those results were internally
consistent with the evaluator then in use, but the evidence surface did not force a reviewer to look at
what the player and GM actually said.

This is an audit layer, not another validator or score. It does not change gameplay, evaluator policy,
or historical verdicts.

## Claim vocabulary

- **Structural evidence** proves deterministic code/data contracts such as schema, serialization,
  ownership, imports, API shape, registry consistency, replay invariants, or state transitions.
- **Runtime evidence** proves that a real execution path ran and produced a valid response object. It
  does not imply semantic correctness.
- **Semantic behavioral evidence** concerns whether player-facing output meaningfully addressed intent,
  fulfilled observation, maintained coherence, preserved agency, or continued conversation sensibly.
- **Human-realism evidence** concerns whether tested player behavior resembles plausible human play.
  It is independent of semantic correctness.
- **Stress-test evidence** comes from unusual, adversarial, or validator-targeting inputs. It is useful
  but must not be described as representative human play.
- **Human-reviewed evidence** records an explicit human judgment over the underlying interaction.

Categories may overlap. They must not be collapsed into a confidence score.

Structural-only validation must declare `evidence_scope: structural_only` and must not claim
`semantic_behavioral_evidence`. Structural tests do not need artificial gameplay transcripts.

## Player-input metadata

Behavioral examples use one or more explicit labels:

- `representative_player_behavior`
- `boundary_case`
- `stress_probe`
- `synthetic_positive_control`
- `synthetic_negative_control`
- `human_captured`
- `runtime_discovered`
- `classification_uncertain_human_review`

Classification uncertainty is recorded rather than guessed. A stress probe may also be runtime
discovered or a boundary case, but it must never silently become evidence of ordinary human play.

## Evidence packet

The standard packet is:

```text
artifacts/validation_evidence/<campaign>/
  evidence_summary.md
  evidence_manifest.json
```

The manifest may reference canonical source artifacts instead of copying them. It embeds exact selected
interaction fields so the packet remains directly inspectable and records the canonical source path for
traceability.

Every behavioral example records:

- campaign, scenario/run ID, and turn index
- exact player input and input classification
- simulated-player rationale when applicable
- relevant prior player/GM context
- exact GM player-facing output
- original semantic or historical result
- mandatory gates, or explicit historical unavailability
- diagnostic result and full automated evaluation
- runtime validity
- final-emission metadata when available
- continuation action or termination reason
- source artifact path
- human-review status and rationale
- evaluator-disagreement history and calibration reference

## Required summary questions

`evidence_summary.md` must state what was tested, runtime path, GM boundary, player-input mode, run/turn
counts, automated conclusions, representative successes and failures, disagreements, unexpected or
ambiguous behavior, and what remains unproven. Aggregates may orient the reviewer but cannot replace
the underlying examples.

Every required category appears even when empty:

- Representative Success
- Boundary Success
- Representative Failure
- Severe / Worst Failure
- Evaluator Disagreement
- Unexpected / Unclassified Behavior
- Stress Probe

An empty category says exactly: `No example observed in this campaign.`

## Deterministic selection

Input ordering is canonical source-run path followed by turn index. The shared implementation applies:

1. Representative success: first automated PASS labeled representative behavior and not human-rejected
   or human-ambiguous.
2. Boundary success: first automated PASS or human-accepted boundary example, excluding rejected or
   ambiguous evidence.
3. Representative failure: first automated or human-rejected failure labeled representative behavior.
4. Severe/worst failure: highest priority for `INVALID_RUN`, then greatest mandatory-gate failure count,
   then lowest diagnostic score; source order breaks ties.
5. Evaluator disagreement: first explicit disagreement.
6. Unexpected/unclassified: first `HUMAN_AMBIGUOUS` or explicitly unexpected example.
7. Stress probe: first example labeled `stress_probe`.

The summary also lists every evaluator disagreement, so deterministic representative selection cannot
hide a second disagreement. Human-selected additions are allowed only when labeled as human-selected
and must not replace deterministic selections.

## Human review

Review status is separate from automated evaluation:

- `UNREVIEWED`
- `HUMAN_ACCEPTED`
- `HUMAN_REJECTED`
- `HUMAN_AMBIGUOUS`

Review records preserve rationale, review date when available, whether semantic policy changed, and a
calibration case ID when promoted later. Review never rewrites the source evaluator result.

## Disagreement history

Evaluator disagreements are permanent evidence. A record keeps the original exchange, result, gates,
human judgment, later evaluator result if one exists, calibration reference, and policy-change status.
The original result remains present after calibration.

The initial packet preserves both current examples:

- PASS with human rejection: notice-legibility observation redirected through NPC ignorance.
- FAIL with human acceptance: `Not something I can say here.` as a coherent diegetic refusal.

Neither disagreement changes evaluator policy in this campaign.

## Ambiguous evidence

Evidence can remain `HUMAN_AMBIGUOUS`. Ambiguity is not converted into a semantic rule. The degraded
notice sentence is preserved this way because it includes requested categories but is grammatically
damaged and mixed with unrelated pressure.

## Missing concepts

Packets record conceptual gaps under `missing_concepts_future_capabilities`. Initial gaps include:

- authority for distinguishing player-to-GM communication, character speech, character action, and
  mixed intent
- generalized clarification behavior for genuinely ambiguous player utterances

These records prevent missing architecture from being patched with increasingly complex local
heuristics. The evidence standard does not implement either capability.

## Integration guidance

Use `tools.validation_evidence` for campaigns making player-facing behavioral claims. Producers should
normalize canonical artifacts into examples, call `build_packet(...)`, validate, and write through
`write_packet(...)`. `tools/build_validation_evidence_packets.py` demonstrates adapters for reactive
schema-v3 evidence and historical playability schema-v2 evidence.

Appropriate consumers include playability, reactive/adversarial, future narration/state, generative
player, and browser gameplay campaigns. Scenario-spine, manual-gauntlet, synthetic, and replay lanes
should integrate only when their report makes a player-facing semantic claim. Purely structural lanes
must not generate meaningless gameplay evidence.

## Completion-report requirement

Future player-facing campaign handoffs include a **Behavioral Evidence** section naming:

- evidence packet path
- run and turn count
- runtime/model boundary
- representative success and failure
- evaluator disagreements
- ambiguous or unexpected behavior
- human-review status
- what remains unproven

Use narrow claims such as `Six reactive runs completed through /api/chat` or `The semantic evaluator
detected 11 mandatory failures`. Do not claim `playability validated`, `behavior verified`, `AI-GM
working`, or `simulation successful` unless inspectable evidence supports that full scope.

## Initial packets

- Reactive/adversarial standard packet:
  `artifacts/validation_evidence/reactive_adversarial/`
- Historical playability retrospective:
  `artifacts/validation_evidence/retrospective_playability/`

The retrospective leaves all schema-v2 PASS values intact and annotates later human judgment and
calibration references beside them. It does not rerun gameplay or reconstruct missing mandatory gates.

## Limitations

- A packet makes evidence easy to inspect; it does not make an evaluator correct.
- Human review quality still depends on reviewer care and scope.
- Deterministic selection prevents flattering cherry-picks but cannot define severity for every future
  domain without an explicit campaign-specific extension.
- Exact text may contain historical encoding damage; preservation takes priority over silent rewriting.
- Referenced source artifacts must remain retained for full provenance.
- This standard does not prove rendered UI behavior, broad human realism, hidden-state consistency,
  long-session coherence, or generalized semantic correctness.

## Campaign verification

Validation Evidence Standard implementation verification on 2026-09-18:

- Packet generation completed for the reactive/adversarial and historical playability evidence without
  rerunning gameplay.
- Focused standard test module: 12 passed.
- Broader focused evidence/reactive/calibration/playability suite: 59 passed, with one existing
  Starlette `TestClient` deprecation warning.
- Full repository suite: 49 failed. This matches the known red baseline count and the same unrelated
  attribution, missing BW/BZ closeout, replay/projection, ownership/import-governance, final-emission,
  social-lead, scene-fallback, and validation-layer separation families. No failure names the evidence
  packet implementation, builder, generated packets, or evidence-standard tests.

The campaign did not repair those failures, rerun gameplay for cleaner examples, or change any GM,
gameplay, evaluator, gate, threshold, or calibration behavior.
