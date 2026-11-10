# Campaign

Campaign: AT-OPT-03 Primary Narration Context Attribution and Compression Feasibility
Identifier: `at_opt_03`
Date: 2026-11-08
Generated: 2026-11-08T18:20:42Z
Purpose: Explain why legitimate primary narration requests exceed 20,000 input tokens and identify one safe, measurable compression experiment. Do not change production prompts.

# Executive Summary

Verdict A/PASS. Live provider calls: 0. The captured F3 prompt was not stored. A rebuild from the pre-continuation snapshot is 83,040 bytes and an admission estimate of 27,744, against a recorded 22,777 input tokens. The 4,967-token gap is unattributed. The user JSON is mostly response_policy (21,638 bytes), instructions (12,596), and turn_packet (10,642). Recent log is 306 bytes. Eleven historical gm.call_gpt requests exceed 20,000 input tokens: five openings at 25,294, plus mid-scene primary and retry calls. Expression calls stay near 100-350. Twelve JSON-equal turn-packet policy keys survive because three siblings differ. Dropping only the equal keys saves 2,637 bytes on the reconstruction, admission estimate minus 879. That is the unstarted AT-OPT-04 experiment. Do not bypass the compact-instruction gate. Do not cap production openings at 3,000. Do not open PR-PLAY-80.

Objective status: `A/PASS`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- Ran existing prompt-dedupe tests: 11 passed, 3 failed with KeyError on this already-dirty tree. This cycle did not edit those tests or production prompt code.

## Tooling changes

- Added artifacts/at_opt_03/reconstruct_context.py, a provider-free rebuild that refuses to construct an OpenAI client.

## Documentation changes

- Added the AT-OPT-03 reports under development/campaigns/product_realization/at_opt_03/.
- Prepended the AT-OPT-03 result to docs/NEXT_SESSION.md. Prior handoff history remains.

## Generated artifacts

- Added measurements and the log-correlation scripts under artifacts/at_opt_03/.
- Generated this review handoff. The archive digest sidecar is written after the zip is sealed.

# What Was Tested

- **Focused tests:** pytest of PR-ED provider efficiency, PR-DE exact-contract dedupe, and the manual-play compact prompt test: 11 passed, 3 failed. Failures are KeyError for provider_context_projection, gm_only, and social_context. Production files were not edited.
- **Broader relevant tests:** Not run. No historical 1065 suite.
- **Full suite:** Not run.
- **Runtime validation:** Provider-free rebuild of the F3 snapshot and three chat samples with provider calls disabled. The step-back made no prompt. What do I see built a prompt and did not call the provider. Hello, Gate Guard entered call_gpt.
- **Model/runtime boundary:** Live provider calls: 0. The OpenAI constructor was replaced with a raising stub. provider_client_constructed is false. Byte counts are not provider tokenizer counts.
- **New regressions:** No production edit, so no new product regression was introduced. The three KeyError failures are on the entry tree.
- **Pre-existing failures:** The worktree was already dirty at entry. HEAD does not uniquely identify the executable source. The compact-prompt test and two projection tests fail with missing payload keys.
- **Self-contained bundle review:** The bundle contains the investigation reports, the measurement JSON, and the reconstruction script. TOKEN_ATTRIBUTION.md is omitted by the filename safeguard and is duplicated as INPUT_SIZE_ATTRIBUTION.md. No live play was produced.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Do not start AT-OPT-04 until this attribution is accepted.
- Do not treat the 879-token admission delta as a measured provider saving.
- Do not put the 3,000 verification total on production openings.

# Known Problems / Unresolved Findings

## Campaign-specific

- The captured 22,777-token prompt is still absent, so section shares are reconstruction bytes.
- Historical retries are about 5,470 input tokens above the preceding primary. Current retry samples are 3.6-3.9 KB and do not explain that surplus.
- Scene files used in the rebuild are the F3 http_data copies. The snapshot does not contain scene files. The blob is 862 bytes under the AT-OPT-01 reconstruction.

## Pre-existing baseline

- Primary narration still sends the full policy scaffold when a turn reaches call_gpt.
- must_advance_scene is true on the reconstructed frontier-gate turn because transition_required is true, so the compact instruction list stays off.
- Three existing prompt tests fail with KeyError on this dirty tree.

# Missing Concepts / Future Capabilities

- A stored copy of the provider payload, or a section-size log written at dispatch without storing prompt text.
- A live tokenizer count for the equal-key deletion.

# What This Campaign Does NOT Prove

- It does not prove a provider-billed token saving.
- It does not prove that narration quality survives the equal-key deletion. No live narration was generated.
- It does not prove the compact instruction list can be forced while transition_required is true.
- It does not prove a Gameplay Benchmark result. No benchmark was run.
- The 11 passed tests were not written for the mixed-key change. They do not cover it.

# Recommended Next Step

Stop. Do not start AT-OPT-04. The proposed experiment is a mixed-key drop inside omit_duplicate_turn_packet_policy, with the equal values left on response_policy. Do not open PR-PLAY-80. Do not cap production openings at 3,000.

# Review Bundle Contents

Bundle file count: `12`
Bundle ZIP size: `000000083729` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/campaigns/product_realization/at_opt_03/SUMMARY.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/campaigns/product_realization/at_opt_03/SUMMARY.md`.
- `support/development/campaigns/product_realization/at_opt_03/CONTEXT_ASSEMBLY_MAP.md`: Assembly flow, conditional inclusion, and duplication points. Canonical source: `development/campaigns/product_realization/at_opt_03/CONTEXT_ASSEMBLY_MAP.md`.
- `support/development/campaigns/product_realization/at_opt_03/INPUT_SIZE_ATTRIBUTION.md`: Review copy of the attribution report. The TOKEN_ filename is omitted by the handoff safeguard. Canonical source: `development/campaigns/product_realization/at_opt_03/INPUT_SIZE_ATTRIBUTION.md`.
- `support/development/campaigns/product_realization/at_opt_03/COMPRESSION_FEASIBILITY.md`: Provider-free before and after sizes and what each cut removes. Canonical source: `development/campaigns/product_realization/at_opt_03/COMPRESSION_FEASIBILITY.md`.
- `support/development/campaigns/product_realization/at_opt_03/OPTIMIZATION_CANDIDATES.md`: Ranked candidates with risks and confidence. Canonical source: `development/campaigns/product_realization/at_opt_03/OPTIMIZATION_CANDIDATES.md`.
- `support/development/campaigns/product_realization/at_opt_03/AT_OPT_04_PROPOSAL.md`: The single next experiment, its fixtures, and its non-goals. Canonical source: `development/campaigns/product_realization/at_opt_03/AT_OPT_04_PROPOSAL.md`.
- `support/development/campaigns/product_realization/at_opt_03/INTEGRITY.md`: Branch, dirty-tree preservation, test counts, and the zero-provider confirmation. Canonical source: `development/campaigns/product_realization/at_opt_03/INTEGRITY.md`.
- `support/artifacts/at_opt_03/measurements.json`: Machine-readable reconstruction, experiments, and ledger rows. Canonical source: `artifacts/at_opt_03/measurements.json`.
- `support/artifacts/at_opt_03/reconstruct_context.py`: Reproducible provider-free measurement script. Canonical source: `artifacts/at_opt_03/reconstruct_context.py`.
- `support/docs/NEXT_SESSION.md`: Authoritative orientation after this cycle. Prior sections are preserved. Canonical source: `docs/NEXT_SESSION.md`.

## Explicit omissions

- `development/campaigns/product_realization/at_opt_03/TOKEN_ATTRIBUTION.md`: sensitive filename pattern: TOKEN_ATTRIBUTION.md

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
