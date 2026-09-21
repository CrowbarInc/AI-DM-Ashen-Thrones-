# Campaign

Campaign: Review Handoff Automation
Identifier: `review_handoff_automation_20260918`
Date: 2026-09-18
Generated: 2026-09-18T03:00:00+00:00
Purpose: Centralize campaign review into one predictable Markdown surface and one portable provenance-preserving ZIP.

# Executive Summary

Codex added an explicit-source review-handoff generator, stable CURRENT_REVIEW files, provenance and omission manifests, sensitive-file and size safeguards, deterministic ZIP output, history copies, and bundle-only review verification. It demonstrates the workflow by consuming the existing Validation Evidence Standard packets without changing their canonical evidence.

Objective status: `ACHIEVED`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No validator, evaluator authority, semantic gate, threshold, or calibration case changed.
- Consumed standardized behavioral evidence without rewriting it.

## Tooling changes

- Added config-driven CURRENT_REVIEW.md, REVIEW_MANIFEST.json, and CURRENT_REVIEW.zip generation.
- Added provenance hashes, deduplication, explicit omission reasons, size warnings, sensitive-path safeguards, deterministic ZIP construction, and optional handoff history.

## Documentation changes

- Added the permanent Review Handoff Standard and pre-implementation handoff inventory.

## Generated artifacts

- Generated the stable current review summary, manifest, ZIP, and campaign history copy.

# What Was Tested

- **Focused tests:** 11 review-handoff tests passed.
- **Broader relevant tests:** 70 review-handoff/evidence/reactive/calibration/playability tests passed; one existing Starlette TestClient deprecation warning.
- **Full suite:** 49 failures, matching the known pre-existing red baseline count and unrelated failure families.
- **Runtime validation:** No gameplay rerun was performed. The campaign consumed preserved runtime evidence.
- **Model/runtime boundary:** Packaged behavioral evidence came from prior in-process POST /api/chat runs using the configured live AI-GM runtime.
- **New regressions:** No campaign-specific regression was found in focused or broader verification.
- **Pre-existing failures:** Attribution, BW/BZ closeout, replay/projection, ownership/import governance, final-emission, social-lead, scene-fallback, and validation-layer separation failures remain.
- **Self-contained bundle review:** PASS: using only an extracted CURRENT_REVIEW.zip, the focused test answered campaign, change, non-change, tests, baseline, exact player/GM evidence, disagreements, ambiguity, decisions, limits, provenance, and next-step questions.

# Behavioral Evidence

## Evidence Packet: reactive_adversarial_20260918_evidence

Runs / turns: `7` / `18`
Runtime/model boundary: Configured live AI-GM runtime; outputs are preserved runtime responses, not test-authored GM fixtures.

### Representative success

Example: `reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_0`
Player classification: `representative_player_behavior, runtime_discovered`
Player: I inspect the notice closely and read what is posted.
GM: The notice board displays three sections in faded ink, barely holding against the rain. The first lists new taxes imposed on various goods—grain, cloth, and salt—with strict collection deadlines. Next are curfew hours tightening for travelers and merchants, cited as necessary due to recent unrest. The final section warns of a missing patrol, last seen heading northwest along the muddy track past the stacked crates near the eastern approach. Your eyes catch the gate serjeant glancing at this list while keeping watch on the crowd.
Automated result: `PASS`
Human review: `UNREVIEWED` - No human judgment recorded for this exact interaction.
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/notice_observation_adversarial_seed1701/run.json`

### Representative failure

Example: `reactive:20260918T021838Z:patrol_knowledge_adversarial_seed1701:turn_0`
Player classification: `representative_player_behavior, runtime_discovered`
Player: Runner, where exactly was the missing patrol last seen?
GM: Tavern Runner says, "No. I cannot answer that from what."
Automated result: `FAIL`
Human review: `HUMAN_REJECTED` - Pressure reproduces both the broken-refusal fragment and a truncated speech construction; mandatory gates detect them.
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/patrol_knowledge_adversarial_seed1701/run.json`

### Evaluator disagreement

Example: `reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_1`
Player classification: `stress_probe, runtime_discovered`
Player: You described the notice as both weathered and legible. Which parts can I actually read?
GM: The guard says, "I do not know enough to answer that."
Automated result: `PASS`
Human review: `HUMAN_REJECTED` - The guard claims ignorance about which visible parts of a nearby notice are readable. The response is lexically coherent and receives PASS, but it does not provide the requested observation and introduces an unnecessary speaker boundary.
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/notice_observation_adversarial_seed1701/run.json`

### Ambiguous/unexpected

Example: `reactive:20260918T021838Z:notice_observation_reactive_seed1701:turn_0`
Player classification: `representative_player_behavior, runtime_discovered`
Player: I inspect the notice closely and read what is posted.
GM: The notice board lists taxes, curfew rules, and a warning about a missing patrol sharpens when you look again, and ash compact census delays have tightened the eastern caravan choke point still competes for notice.
Automated result: `PASS`
Human review: `HUMAN_AMBIGUOUS` - The requested categories are present, but the sentence is grammatically degraded ('a warning ... sharpens') and mixes unrelated pressure. It remains insufficiently clear for an evaluator-policy change.
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/notice_observation_reactive_seed1701/run.json`

### Stress probe

Example: `reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_1`
Player classification: `stress_probe, runtime_discovered`
Player: You described the notice as both weathered and legible. Which parts can I actually read?
GM: The guard says, "I do not know enough to answer that."
Automated result: `PASS`
Human review: `HUMAN_REJECTED` - The guard claims ignorance about which visible parts of a nearby notice are readable. The response is lexically coherent and receives PASS, but it does not provide the requested observation and introduces an unnecessary speaker boundary.
Source: `artifacts/reactive_adversarial_players/20260918T021838Z/notice_observation_adversarial_seed1701/run.json`

### All evaluator disagreements

- `reactive:20260918T021838Z:notice_observation_adversarial_seed1701:turn_1`: automated `PASS`; human `HUMAN_REJECTED`; player: You described the notice as both weathered and legible. Which parts can I actually read?; GM: The guard says, "I do not know enough to answer that."
- `reactive:20260918T022209Z:patrol_knowledge_adversarial_seed1701:turn_0`: automated `FAIL`; human `HUMAN_ACCEPTED`; player: Runner, where exactly was the missing patrol last seen?; GM: Tavern Runner grimaces. "Not something I can say here."

## Evidence Packet: retrospective_playability_20260917T221002Z

Runs / turns: `4` / `7`
Runtime/model boundary: Configured live AI-GM runtime preserved by the original observability campaign.

### Representative success

Example: `historical:20260917T221002Z:p3_logical_escalation:turn_0`
Player classification: `runtime_discovered, representative_player_behavior, classification_uncertain_human_review`
Player: What do I see at the gate?
GM: The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. "Board, runner, or road," he says. "Pick one before the gate swallows the trail.".
Automated result: `PASS`
Human review: `UNREVIEWED` - No human judgment recorded for this exact interaction.
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p3_logical_escalation/transcript.json`

### Representative failure

Example: `historical:20260917T221002Z:p1_direct_answer:turn_0`
Player classification: `runtime_discovered, representative_player_behavior`
Player: Who commands the watch here?
GM: Tavern Runner mutters, the tavern runner replies, voice steady amid the murmur of the crowd.
Automated result: `PASS`
Human review: `HUMAN_REJECTED` - The watch-command question was not meaningfully answered.
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p1_direct_answer/transcript.json`

### Evaluator disagreement

Example: `historical:20260917T221002Z:p1_direct_answer:turn_0`
Player classification: `runtime_discovered, representative_player_behavior`
Player: Who commands the watch here?
GM: Tavern Runner mutters, the tavern runner replies, voice steady amid the murmur of the crowd.
Automated result: `PASS`
Human review: `HUMAN_REJECTED` - The watch-command question was not meaningfully answered.
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p1_direct_answer/transcript.json`

### Ambiguous/unexpected

Example: `historical:20260917T221002Z:p3_logical_escalation:turn_1`
Player classification: `runtime_discovered, boundary_case, stress_probe`
Player: I press again: what is actually posted on the notice?
GM: Tavern Runner mutters,
Automated result: `PASS`
Human review: `HUMAN_REJECTED` - The output is truncated and does not fulfill the notice observation.
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p3_logical_escalation/transcript.json`

### Stress probe

Example: `historical:20260917T221002Z:p3_logical_escalation:turn_1`
Player classification: `runtime_discovered, boundary_case, stress_probe`
Player: I press again: what is actually posted on the notice?
GM: Tavern Runner mutters,
Automated result: `PASS`
Human review: `HUMAN_REJECTED` - The output is truncated and does not fulfill the notice observation.
Source: `artifacts/simulated_playtest_observability/20260917T221002Z_p3_logical_escalation/transcript.json`

### All evaluator disagreements

- `historical:20260917T221002Z:p1_direct_answer:turn_0`: automated `PASS`; human `HUMAN_REJECTED`; player: Who commands the watch here?; GM: Tavern Runner mutters, the tavern runner replies, voice steady amid the murmur of the crowd.
- `historical:20260917T221002Z:p1_direct_answer:turn_1`: automated `PASS`; human `HUMAN_REJECTED`; player: Who stole the relic from the chapel?; GM: Tavern Runner says, "No. I cannot answer that from what."
- `historical:20260917T221002Z:p2_respect_intent:turn_0`: automated `PASS`; human `HUMAN_REJECTED`; player: Tell me about the thief.; GM: Tavern Runner says, "No. I cannot answer that from what."
- `historical:20260917T221002Z:p3_logical_escalation:turn_1`: automated `PASS`; human `HUMAN_REJECTED`; player: I press again: what is actually posted on the notice?; GM: Tavern Runner mutters,
- `historical:20260917T221002Z:p4_immersion:turn_0`: automated `PASS`; human `HUMAN_REJECTED`; player: I glance at the notice.; GM: The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. "Board, runner, or road," he says. "Pick one before the gate swallows the trail.".

# Decisions Requiring Human Review

- Decide in a later calibration campaign whether the concise refusal 'Not something I can say here.' should become an accepted calibration boundary.
- Decide in a later calibration campaign whether visible-notice clarification redirected through NPC ignorance should become a negative calibration case.
- Keep the grammatically degraded notice response ambiguous unless further evidence supports a stable policy.

# Known Problems / Unresolved Findings

## Campaign-specific

- The evidence packet exposes one probable evaluator miss, one probable false positive, and one ambiguous generated response. They were preserved, not repaired.

## Pre-existing baseline

- The repository full suite remains red with 49 failures in previously known unrelated families.

# Missing Concepts / Future Capabilities

- Player-to-GM communication versus character speech/action authority.
- Generalized ambiguity and clarification behavior.

# What This Campaign Does NOT Prove

- Broad gameplay quality or that the AI-GM generally works.
- Rendered UI usability or browser gameplay.
- Long-session coherence, hidden-state consistency, or broad human realism.
- That human review has resolved either evaluator disagreement.

# Recommended Next Step

Conduct a separate human-reviewed calibration campaign for the two preserved evaluator disagreements. Do not begin gameplay repair before that decision.

# Review Bundle Contents

Bundle file count: `17`
Bundle ZIP size: `000000089198` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/docs/review_handoff_standard.md`: Primary campaign standard/report used to orient the review. Canonical source: `docs/review_handoff_standard.md`.
- `support/artifacts/validation_evidence/reactive_adversarial/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/reactive_adversarial/evidence_summary.md`.
- `support/artifacts/validation_evidence/reactive_adversarial/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/reactive_adversarial/evidence_manifest.json`.
- `support/artifacts/validation_evidence/retrospective_playability/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/retrospective_playability/evidence_summary.md`.
- `support/artifacts/validation_evidence/retrospective_playability/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/retrospective_playability/evidence_manifest.json`.
- `support/docs/review_handoff_inventory.md`: Documents existing campaign output conventions and the canonical/generated boundary. Canonical source: `docs/review_handoff_inventory.md`.
- `support/docs/validation_evidence_standard.md`: Defines the behavioral evidence contract consumed by the handoff demonstration. Canonical source: `docs/validation_evidence_standard.md`.
- `support/docs/validation_evidence_producer_inventory.md`: Documents existing evidence producers and their actual guarantees. Canonical source: `docs/validation_evidence_producer_inventory.md`.
- `support/docs/reactive_adversarial_simulated_players.md`: Explains the source reactive campaign architecture, findings, and limits. Canonical source: `docs/reactive_adversarial_simulated_players.md`.
- `support/artifacts/reactive_adversarial_players/human_review.json`: Preserves human classifications behind evaluator disagreements and ambiguity. Canonical source: `artifacts/reactive_adversarial_players/human_review.json`.
- `support/tools/validation_evidence.py`: Defines the shared evidence-packet contract and deterministic selection behavior. Canonical source: `tools/validation_evidence.py`.
- `support/tools/build_validation_evidence_packets.py`: Shows canonical evidence adapters and generation workflow. Canonical source: `tools/build_validation_evidence_packets.py`.
- `support/tests/test_validation_evidence_standard.py`: Defines the evidence-standard regression contract. Canonical source: `tests/test_validation_evidence_standard.py`.
- `support/tools/build_review_handoff.py`: Implements review selection, safeguards, summary rendering, manifest provenance, and ZIP generation. Canonical source: `tools/build_review_handoff.py`.
- `support/tests/test_review_handoff.py`: Defines the review-handoff safety, provenance, determinism, and self-contained-review contract. Canonical source: `tests/test_review_handoff.py`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
