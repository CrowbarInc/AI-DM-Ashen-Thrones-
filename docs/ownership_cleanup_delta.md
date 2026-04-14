# Ownership Cleanup Delta

Final audit re-run after the OC2 and OC3 cleanup passes.

## Evidence used

- `py -3 tools/architecture_audit.py`
- `py -3 -m pytest tests/test_architecture_audit_tool.py`
- `py -3 -m pytest tests/test_fallback_shipped_contract_propagation.py tests/test_stage_diff_telemetry.py tests/test_turn_packet_accessors.py`

Current audit result:

- Repo verdict: `mixed / caution`
- Recommended action mode: `needs targeted ownership cleanup before more features`
- Hotspot mix: `3 localized`, `2 transitional residue`, `2 possible ownership smear`, `1 unclear`

Interpretation:

- The repo has moved materially toward `structurally real, under-consolidated`.
- It has not crossed that line yet.
- The formerly central gate/meta and turn-packet/telemetry contradictions now read as localized boundary cleanup plus compatibility residue, not active co-ownership.
- The remaining real blocker is the prompt-contract seam, with test-governance drift still lowering confidence.

## Seam-by-seam convergence delta

### Response policy contracts

- Prior contradiction / hotspot: response-policy ownership was split across `game/response_policy_contracts.py`, `game/final_emission_repairs.py`, and adjacent prompt-facing helpers.
- Declared owner: `game/response_policy_contracts.py`
- What changed in OC2/OC3 + RP2-R + RP3-R2: owner language was aligned in the ledger, governance docs, and test headers; shipped-contract accessors were re-centered here; direct accessor/materialization assertions now live in `tests/test_response_policy_contracts.py`, while fallback/gate/validator/emission suites are explicitly framed as downstream consumer/application/regression coverage.
- Current apparent owner shape: the canonical runtime owner is explicit and stable in `game/response_policy_contracts.py`, and the practical primary direct-owner suite is explicit and stable in `tests/test_response_policy_contracts.py`; downstream repair, gate, validator, and emission coverage now reads as intentionally secondary rather than repair-centered semantic authority.
- Current status: `governance-aligned; compatibility residue remains`
- Compatibility residue still present: private compatibility accessors remain importable; top-level `fallback_behavior` fallback remains supported for older payloads; top-level `social_response_structure_contract` fallback remains supported for older payloads.
- Recommended next cleanup: rerun the architecture audit and keep watching for any new direct contract assertions drifting back into repair/gate/validator/emission suites.

### Prompt contracts

- Prior contradiction / hotspot: `game/prompt_context.py`, `game/prompt_context_leads.py`, and `game/response_policy_contracts.py` all read like competing homes for prompt-facing obligations.
- Declared owner: `game/prompt_context.py`
- What changed in OC2/OC3 + PC2: the response-policy side was reduced, `game/prompt_context_leads.py` now declares itself as support-only extraction residue instead of a co-equal home, and practical direct prompt-contract assertions were re-anchored in `tests/test_prompt_context.py`.
- AR8 prep note: the remaining practical spread was traced mostly to `tests/test_prompt_compression.py` still carrying several direct exported prompt-contract assertions and to downstream gate/emission suites importing prompt-owner helper builders for shipped-fixture setup. Those direct rule-priority / response-delta / uncertainty / promoted-interlocutor assertions were re-centered into `tests/test_prompt_context.py`, while downstream suites were tightened to read as shipped-consumer coverage.
- Current apparent owner shape: improved but not fully clean. The runtime owner declaration is now clearer, and the practical primary direct-owner suite is visible in `tests/test_prompt_context.py`, but downstream prompt-adjacent suites still create heuristic spread.
- Current status: `conflict reduced; still watch`
- Compatibility residue still present: extracted lead helpers remain importable and adjacent response-policy helpers still blur the prompt bundle boundary.
- Recommended next cleanup: keep collapsing prompt-contract ownership back onto `game/prompt_context.py`, preserve `tests/test_prompt_context.py` as the direct-owner suite, and continue treating downstream suites as secondary coverage rather than equal semantic owners. Watch especially for future direct prompt-export assertions drifting back into `test_prompt_compression.py` or for gate/emission suites re-importing prompt-owner helper builders when a local shipped fixture would do.

PC4-R2 narrowing note:

- `tests/test_prompt_compression.py` now reads more narrowly as prompt-assembly / compression coverage: direct `player_expression_contract` ownership assertions were re-centered in `tests/test_prompt_context.py`, and the prior duplicated structured-turn-summary / no-restatement check was reduced to serialized payload smoke.
- `tests/test_answer_completeness_rules.py` now frames shipped answer-completeness and response-delta contracts as downstream gate / escalation consumers, using a module-local prompt-contract handle instead of a broad prompt-owner import block.
- The remaining prompt spread should now read more as adjacency residue than as co-equal practical ownership, though future audit reruns should still watch for direct prompt-export assertions drifting back into secondary suites.

PC5 narrowing note:

- `tests/test_dialogue_interaction_establishment.py` no longer imports prompt-owner helpers directly; the wait-while-engaged narration-obligation assertion was re-centered in `tests/test_prompt_context.py`, and the dialogue suite now reads as establishment / strict-social consumer coverage instead of a prompt-owner home.
- `tests/test_fallback_shipped_contract_propagation.py` now uses a local shipped-response-policy fixture instead of calling `game.prompt_context.build_response_policy(...)`, with helper and test names tightened to fallback / gate consumption wording.
- The prompt seam should now read narrower around establishment and shipped-fallback adjacency, though future audit reruns should still watch `test_dialogue_interaction_establishment.py`, `test_fallback_shipped_contract_propagation.py`, and any new prompt-adjacent suites for fresh direct builder imports or owner-like contract assertions.

PC6-R2 narrowing note:

- `tests/test_follow_lead_commitment_wiring.py` no longer carries the prompt-export assertion for terminal pending-lead filtering; that owner-side check now lives in `tests/test_prompt_context.py`, leaving the suite focused on follow-lead commitment and lifecycle wiring.
- `tests/test_lead_lifecycle_npc_repeat_suppression.py` now consumes exported narration context instead of importing direct prompt-slice helpers and recency-window constants, with names/docstring tightened to downstream lifecycle wording while preserving repeat-suppression coverage.
- The remaining prompt breadth around lead-adjacent suites should now read more as lifecycle adjacency than as prompt-contract co-ownership, though future audit reruns should still watch for direct prompt-helper imports or owner-like export assertions drifting back into those files.

### Final emission gate vs meta

- Prior contradiction / hotspot: `game/final_emission_gate.py` and `game/final_emission_meta.py` were both being read as possible owners of final-emission metadata behavior.
- Declared owner: `game/final_emission_gate.py` for orchestration, `game/final_emission_meta.py` for metadata-only packaging
- What changed in OC3: owner language now explicitly separates orchestration from metadata packaging; metadata helpers are framed as write-time/read-side schema helpers, not orchestration.
- Current apparent owner shape: `game/final_emission_gate.py` is again the visible orchestration owner; `game/final_emission_meta.py` reads as a subordinate metadata-only support layer.
- Current status: `improved / localized residue`
- Compatibility residue still present: historical tests and broad integration coverage still touch both files, so practical test authority is wider than the ideal boundary.
- Recommended next cleanup: tighten test and doc wording so gate ordering stays primary and metadata packaging remains a secondary helper seam.

### Turn packet vs telemetry

- Prior contradiction / hotspot: `game/turn_packet.py` and `game/stage_diff_telemetry.py` looked like they might both own the packet/telemetry boundary.
- Declared owner: `game/turn_packet.py` for the packet contract boundary, `game/stage_diff_telemetry.py` for telemetry-only observability
- What changed in OC3: gate-side packet resolution was explicitly re-homed to `game.turn_packet.resolve_turn_packet_for_gate`; `game.stage_diff_telemetry.resolve_gate_turn_packet` is now documented as compatibility residue only; focused regressions include `tests/test_stage_diff_telemetry.py` and `tests/test_turn_packet_accessors.py`.
- Current apparent owner shape: `game/stage_diff_telemetry.py` now reads as a telemetry consumer, while the packet boundary remains in `game/turn_packet.py`. The audit classifies the stage-diff seam as localized under-consolidation and the turn-packet-specific hotspot as transitional residue.
- Current status: `improved / localized residue`
- Compatibility residue still present: compatibility wrapper/accessor paths and mixed integration tests still make the seam look wider than it should.
- Recommended next cleanup: keep trimming telemetry-side compatibility entry points and relink tests and docs so packet-owner vs telemetry-consumer authority is unmistakable.

### Test inventory / governance docs

- Prior contradiction / hotspot: test-governance docs read authoritatively, but practical ownership was not cleanly reconciled against actual pytest homes.
- Declared owner: `tests/TEST_AUDIT.md`
- What changed in OC2/OC3 + GD1-R2: governance language is clearer, ownership terminology is more consistent, broken/stale references are being trimmed, and prompt-governance wording now explicitly distinguishes runtime owner, practical direct-owner suite, and secondary coverage.
- Current apparent owner shape: still a governance map rather than a runtime owner, but less self-contradictory. `tests/TEST_AUDIT.md` now more clearly points to actual runtime/test owners instead of sounding like a competing authority layer.
- Current status: `improving; still audit-sensitive`
- Compatibility residue still present: some historical counts remain snapshot-only, heuristic spread can still over-read downstream prompt-adjacent suites, and the audit may lag until artifacts are regenerated.
- Recommended next cleanup: re-run the audit after these doc repairs, then keep trimming any remaining stale references or wording that makes downstream suites sound like semantic owners.

## Residue vs blockage

Mostly residue now:

- `game/final_emission_gate.py` vs `game/final_emission_meta.py`
- `game/turn_packet.py` vs `game/stage_diff_telemetry.py`
- support-only extraction residue in `game/prompt_context_leads.py`
- compatibility wrappers / old import paths around packet and response-policy accessors

Still real blockage:

- prompt-contract ownership is not yet converged enough to treat as a settled boundary

Still confidence-reducing, but not the same as runtime ownership smear:

- governance docs are subordinate maps, but still need a fresh audit pass to confirm the wording cleanup landed
- documentation coherence was weak enough to matter in the last audit (`18` broken references reported before this cleanup pass)

## Final operator answer

- Best current repo label: `mixed / caution`
- Direction of travel: materially closer to `structurally real, under-consolidated` than before OC2/OC3
- Resume decision: `limited feature work only after one more cleanup seam`

Why:

- the central emit-path seams are no longer the main contradiction;
- the remaining packet/telemetry and gate/meta issues look like cleanup residue, not owner collapse;
- prompt contracts still present a watched seam, though the direct-owner test home is now clearer;
- governance/docs drift still needs a fresh audit confirmation before a clean "resume feature work" call.

Single highest-value remaining cleanup seam:

- `prompt contracts` - finish converging `game/prompt_context.py`, `game/prompt_context_leads.py`, and adjacent response-policy touchpoints into one clearly dominant prompt-contract owner while keeping `tests/test_prompt_context.py` as the practical primary direct-owner suite.

## AR5-R3 final fortification addendum

Final audit re-run after PC1, PC2, and GD1, with a small AR5-R3-only audit-heuristic polish so the report reflects the current state more honestly.

### Evidence used

- `py -3 tools/architecture_audit.py --print-summary`
- `py -3 -m pytest tests/test_architecture_audit_tool.py`
- `py -3 -m pytest tests/test_prompt_context.py tests/test_prompt_compression.py tests/test_prompt_and_guard.py tests/test_final_emission_gate.py tests/test_social_exchange_emission.py`

### Fresh audit result

- Repo verdict: `mixed / caution`
- Recommended action mode: `needs targeted ownership cleanup before more features`
- Documentation coherence: improved from `weak` to `patchy`
- Broken doc references: `0`
- Refreshed hotspot mix: prompt, response-policy, gate/meta, telemetry, and governance all now read as `localized under-consolidation` rather than prompt/doc-specific active smear

### What changed materially

#### Prompt runtime ownership

- `game/prompt_context.py` remains the visible canonical runtime owner.
- The refreshed audit no longer treats prompt contracts as a transcript-dominated `conflict`.
- Current audit state for prompt contracts is now `partial` with mismatch type `ownership_spread_wide`, not `conflict`.
- Practical top test home is again clearly `tests/test_prompt_context.py`, now recognized as `integration / layer interaction` rather than misread as transcript-style protection.

#### Practical prompt test authority

- `tests/test_prompt_context.py` is now the strongest practical direct-owner suite in the audit evidence.
- Downstream prompt-facing coverage still keeps the seam broad enough that practical ownership is not singular yet.
- The remaining spread is mostly broad-suite residue plus compatibility-preserving adjacency, not evidence that runtime authority has shifted away from `game/prompt_context.py`.

#### Governance / doc coherence

- Broken-reference drag is no longer the main issue: the fresh audit reports `0` broken references.
- Inventory/governance docs now land as `partial` / `partially clearer`, not as the earlier broken-link-driven uncertainty state.
- The remaining governance hotspot is now mainly heuristic: docs are subordinate governance maps, but practical-affinity inference for a docs-led concern is still imperfect.

### Residue vs blockage after AR5-R3

Prompt contracts are no longer the clearest active blocker in the old sense:

- runtime ownership is visibly centered on `game/prompt_context.py`;
- the practical primary direct-owner suite is visibly centered on `tests/test_prompt_context.py`;
- downstream suites and governance docs now read more as spread/residue than as competing authorities.

What still blocks a clean `resume limited feature work` call is the broader remaining under-consolidation:

- `response policy contracts` still carried enough practical/governance drift before the RP3-R2 alignment pass that a fresh audit rerun was still warranted;
- the repo still carries heavy archaeology and high centrality signals in the scorecard;
- several adjacent seams are still only `partial`, even if they are now localized rather than structurally smeared.

### Final AR5-R3 gate decision

- Best current repo label: `mixed / caution`
- Closest alternate label: `structurally real, under-consolidated`, but the repo has not crossed that threshold yet
- Limited feature work justified now: `no`
- Operator call: `one more cleanup seam first`

### Single highest-value remaining seam

- `response policy contracts`

Why this is now the best next seam:

- prompt contracts have downgraded from blocker-shaped conflict to localized partial spread;
- governance/docs no longer look stale or broken enough to be the primary drag;
- in the refreshed audit immediately before RP3-R2, response-policy ownership still showed the strongest runtime-vs-practical-home drift.

## RP3-R2 authority alignment addendum

This pass was intentionally governance-only and did not change runtime behavior.

- Canonical runtime owner remains `game/response_policy_contracts.py`.
- Practical primary direct-owner suite remains `tests/test_response_policy_contracts.py`.
- `tests/test_fallback_shipped_contract_propagation.py`, `tests/test_response_delta_requirement.py`, `tests/test_final_emission_gate.py`, `tests/test_social_exchange_emission.py`, and `tests/test_final_emission_validators.py` are now documented consistently as downstream secondary coverage.
- Remaining residue is documented as compatibility/adjacency only: private compatibility accessors remain importable, and top-level `fallback_behavior` / `social_response_structure_contract` fallbacks remain supported.
- The seam should now present one cleaner owner story to the next full audit, with residual watch items focused on future drift rather than current repair-centered wording.

## AR6-R3 final post-RP3 audit gate

Final audit rerun after RP1, RP2, and RP3, with a small AR6-R3 audit-only heuristic polish so an already-aligned dominant owner is not over-penalized just because adjacent downstream suites still exist.

### Evidence used

- `py -3 tools/architecture_audit.py --print-summary`
- `py -3 -m pytest tests/test_architecture_audit_tool.py`
- `py -3 -m pytest tests/test_response_policy_contracts.py tests/test_fallback_shipped_contract_propagation.py tests/test_response_delta_requirement.py tests/test_final_emission_gate.py tests/test_final_emission_validators.py tests/test_social_exchange_emission.py`
- `py -3 -m pytest tests/test_prompt_context.py tests/test_prompt_compression.py tests/test_prompt_and_guard.py`
- `py -3 -m pytest tests/test_stage_diff_telemetry.py tests/test_turn_packet_accessors.py`

### Fresh audit result

- Repo verdict: `mixed / caution`
- Recommended action mode: `needs targeted ownership cleanup before more features`
- Hotspot mix: `4 localized under-consolidation`, `3 transitional residue`, `1 possible ownership smear`, `0 unclear`
- Response policy hotspot state: `transitional residue`, not a primary blocker

### What changed materially vs stale artifacts

Actual architecture improvement, not just rerendering:

- Runtime ownership is now visibly centered on `game/response_policy_contracts.py`, with the audit resolving that module as the canonical owner instead of reading repairs as a co-owner.
- Practical test ownership is now visibly centered on `tests/test_response_policy_contracts.py`, with downstream fallback / gate / validator / emission suites reading as secondary consumers instead of semantic authorities.
- Governance and docs now reinforce the same owner story; they no longer act like the main drag on this seam.

Artifact refresh only:

- The rerun regenerated `artifacts/architecture_audit/architecture_audit.json` and `artifacts/architecture_audit/architecture_audit.md`.
- AR6-R3 added only tiny audit/report polish so aligned owner-plus-direct-owner seams classify as residue when the remaining spread is compatibility or adjacency only.

### Response-policy finalization call

#### Runtime ownership

- Canonical runtime owner: `game/response_policy_contracts.py`
- `game/final_emission_gate.py` now consumes the canonical bundle materializer directly.
- `game/final_emission_repairs.py` and `game/final_emission_validators.py` read as downstream consumers, not contract authorities.

#### Practical test ownership

- Practical primary direct-owner suite: `tests/test_response_policy_contracts.py`
- `tests/test_fallback_shipped_contract_propagation.py`, `tests/test_response_delta_requirement.py`, `tests/test_final_emission_gate.py`, `tests/test_final_emission_validators.py`, and `tests/test_social_exchange_emission.py` now read as downstream secondary coverage.

#### Governance / doc authority

- `docs/architecture_ownership_ledger.md`, `docs/narrative_integrity_architecture.md`, `docs/architecture_audit_readme.md`, and `tests/TEST_AUDIT.md` now tell the same owner story.
- Governance/doc wording is no longer the primary reason response policy looks smeared.

### Residue still allowed

- private compatibility accessors remain importable
- top-level `fallback_behavior` fallback remains supported
- top-level `social_response_structure_contract` fallback remains supported
- downstream consumer/application/regression suites still touch shipped response-policy data

These now read as compatibility or adjacency residue, not as evidence that response policy is still repair-centered.

### Repo-level gate after AR6-R3

- Response policy is no longer the primary active blocker.
- Prompt contracts remain `localized under-consolidation`: runtime ownership is visible in `game/prompt_context.py`, but practical coverage is still broad across `tests/test_prompt_context.py`, `tests/test_prompt_compression.py`, and `tests/test_prompt_and_guard.py`.
- Gate/meta and telemetry/packet seams remain localized cleanup rather than owner collapse.
- The last remaining smear-shaped hotspot is `social_exchange_emission mixed repair/contract role`.

### Final decision

- Best current repo label: `mixed / caution`
- Threshold crossed to `structurally real, under-consolidated`: `not yet`
- Limited feature work justified now: `no`
- Operator call: `one more cleanup seam first`

### Single highest-value remaining seam

- `social_exchange_emission mixed repair/contract role`

Why this is now the best next seam:

- response policy has downgraded to `transitional residue`
- prompt contracts remain broad but no longer read like the clearest smear-shaped contradiction
- the refreshed audit now reports only one remaining possible ownership-smear hotspot, and it is centered on `game/social_exchange_emission.py`

## AR7-R3 final post-social_exchange_emission audit gate

Final audit rerun after SE1, SE2, and SE3, plus a tiny AR7-R3-only audit-classification polish so an explicitly downstream owner with direct-owner test authority is not still forced into a smear label just because gate/retry adjacency remains.

### Evidence used

- `py -3 tools/architecture_audit.py --print-summary`
- `py -3 -m pytest tests/test_architecture_audit_tool.py tests/test_social_exchange_emission.py tests/test_strict_social_emergency_fallback_dialogue.py`
- `py -3 -m pytest tests/test_social_emission_quality.py tests/test_dialogue_interaction_establishment.py tests/test_narration_transcript_regressions.py`

### Fresh audit result

- Repo verdict: `mixed / caution`
- Recommended action mode: `needs targeted ownership cleanup before more features`
- Hotspot mix: `5 localized under-consolidation`, `3 transitional residue`, `0 possible ownership smear`, `0 unclear`
- Score total: `9/18`
- Social-exchange hotspot state: `transitional residue`, not a primary blocker

### What changed materially vs artifact refresh

Real architecture improvement from SE1 and SE2:

- Runtime role is now visibly centered on `game/social_exchange_emission.py` as downstream strict-social emission/application, not contract or repair authority.
- Practical test ownership is now visibly centered on `tests/test_social_exchange_emission.py`, with `tests/test_strict_social_emergency_fallback_dialogue.py`, `tests/test_social_emission_quality.py`, and `tests/test_dialogue_interaction_establishment.py` reading as secondary downstream / compatibility coverage.
- Governance authority now tells the same story in `docs/architecture_ownership_ledger.md`, `tests/TEST_AUDIT.md`, and adjacent architecture docs.

Artifact/rerender correction only:

- SE3 itself was wording-only.
- AR7-R3 added only tiny audit/report polish so `social_exchange_emission mixed repair/contract role` can downgrade to `transitional residue` when the seam shows an explicit downstream owner story plus compatibility residue, instead of being hard-forced to `possible ownership smear`.

### Social-exchange finalization call

#### Runtime ownership

- Canonical runtime owner for the seam: `game/social_exchange_emission.py`
- Practical orchestration owner for the wider final-emission subsystem remains `game/final_emission_gate.py`
- `game/gm.py` and `game/gm_retry.py` still carry the legacy repair-shaped alias only on downstream retry/compatibility paths; they do not now read as semantic owners

#### Practical test ownership

- Practical primary direct-owner suite: `tests/test_social_exchange_emission.py`
- Secondary downstream / compatibility coverage: `tests/test_strict_social_emergency_fallback_dialogue.py`, `tests/test_social_emission_quality.py`, `tests/test_dialogue_interaction_establishment.py`

#### Governance / doc authority

- `docs/architecture_ownership_ledger.md` now declares the seam as `runtime owner -> direct-owner suite -> downstream secondary / compatibility coverage`
- `tests/TEST_AUDIT.md` now reinforces the same owner story instead of treating retry-terminal or quality coverage as equal semantic owners

### Residue vs remaining blockage after AR7-R3

Allowed residue now:

- legacy `repair_strict_social_terminal_dialogue_fallback_if_needed(...)` alias remains importable
- downstream retry wiring still passes through `game/gm.py` / `game/gm_retry.py`
- broad integration/regression suites still touch the seam from adjacent final-emission paths

Still-blocking under-consolidation elsewhere:

- `prompt contracts` remain the widest practical-owner spread in the refreshed audit (`coverage_spread: 9`)
- `response policy contracts` did not stay purely `transitional residue` in the raw rerun; they currently score as `localized under-consolidation` because direct contract-resolution assertions still spread across `tests/test_response_policy_contracts.py`, `tests/test_interaction_continuity_contract.py`, and `tests/test_interaction_continuity_validation.py` (`coverage_spread: 6`)
- final-emission orchestration remains highly central and archaeology-heavy even though the social seam itself no longer reads as smear-shaped

### Final decision gate

- Best current repo label: `mixed / caution`
- Threshold crossed to `structurally real, under-consolidated`: `not yet`
- Limited feature work justified now: `no`
- Operator call: `one more cleanup seam first`

### Single highest-value remaining seam

- `prompt contracts`

Why this is now the best next seam:

- the last smear-shaped social-emission blocker has downgraded to transitional residue
- prompt ownership still shows the broadest practical direct-owner spread, with `tests/test_prompt_context.py`, `tests/test_prompt_compression.py`, and `tests/test_prompt_and_guard.py` all still reading as primary homes in the audit
- response policy still needs tightening too, but the prompt seam remains wider and more audit-dominant in the refreshed evidence

## AR8-R5 final prompt-width audit gate after PC5 and PC6

Final audit rerun after the PC5 and PC6 prompt-width cleanup passes, plus one tiny AR8-R5 audit-only interpretation polish so lead-lifecycle suites that only consume exported prompt-context builders are less likely to be misread as co-equal prompt owners.

### Evidence used

- `py -3 tools/architecture_audit.py --print-summary`
- `py -3 -m pytest tests/test_architecture_audit_tool.py`
- `py -3 -m pytest tests/test_prompt_context.py tests/test_follow_lead_commitment_wiring.py tests/test_lead_lifecycle_npc_repeat_suppression.py tests/test_prompt_compression.py tests/test_prompt_and_guard.py`

### Fresh audit result

- Repo verdict: `mixed / caution`
- Recommended action mode: `needs targeted ownership cleanup before more features`
- Hotspot mix: `5 localized under-consolidation`, `3 transitional residue`, `0 possible ownership smear`, `0 unclear`
- Score total: `9/18`
- Prompt hotspot state: still `localized under-consolidation`, not a fresh smear

### What changed vs AR7 + PC5/PC6 expectations

#### Prompt practical-owner spread

- `tests/test_prompt_context.py` remains the strongest practical prompt-owner suite and the clearest direct-owner home in the rerun.
- The PC5 adjacency drivers did stay out: `tests/test_dialogue_interaction_establishment.py` and `tests/test_fallback_shipped_contract_propagation.py` no longer appear in the prompt practical-owner trio.
- The PC6 lead-adjacent suite `tests/test_follow_lead_commitment_wiring.py` also stayed out of the prompt-owner shortlist.
- The lead-lifecycle suites now read more clearly as downstream adjacency than before: after the tiny audit polish, `tests/test_lead_lifecycle_npc_repeat_suppression.py`, `tests/test_lead_lifecycle_vertical_slice.py`, and `tests/test_lead_progression_turn_pipeline_integration.py` were pushed into secondary prompt coverage rather than practical primary homes.

#### Why the seam still did not converge

- The rerun exposed fresh direct helper/import spread from social-adjacent suites instead of the lead-adjacent suites that dominated the PC5/PC6 watchlist.
- The prompt concern still resolves to `ownership_spread_wide` with practical-owner mix centered on:
  - `tests/test_prompt_context.py`
  - `tests/test_social_escalation.py`
  - `tests/test_social_interaction_authority.py`
- The same rerun also keeps `tests/test_social_speaker_grounding.py` as a direct-runtime prompt-context home just below the mixed-owner cutoff.
- This reads as real residual prompt-contract/helper spread, not merely audit over-reading of the lead lifecycle.

#### Residue vs blockage after the rerun

- Mostly residue:
  - lead-lifecycle adjacency through exported narration/prompt context
  - `prompt_context_leads` extraction residue
  - `social_exchange_emission` compatibility / retry adjacency
- Still real blockage:
  - direct `game.prompt_context` helper ownership remains too broad across prompt-owner and social-adjacent suites
  - prompt practical coverage is still not singular enough to call the seam structurally settled

#### Stable seams

- `response policy contracts` remains visible and stable at runtime, but still scores `localized under-consolidation` because practical coverage remains spread across `tests/test_response_policy_contracts.py`, `tests/test_interaction_continuity_contract.py`, and `tests/test_interaction_continuity_validation.py`.
- `social_exchange_emission mixed repair/contract role` remains stable as `transitional residue`, not a blocker-shaped hotspot.

### Final decision gate

- Best current repo label: `mixed / caution`
- Threshold crossed to `structurally real, under-consolidated`: `not yet`
- Limited feature work justified now: `no`
- Operator call: `one more cleanup seam first`

### Why this gate stays closed

- The repo no longer has smear-shaped hotspots, which is real progress.
- The prompt seam is narrower around lead-lifecycle adjacency than it was before PC5/PC6.
- But the rerun did not produce a singular practical prompt-owner home; it surfaced a different direct-helper spread across social-adjacent suites instead.
- That means the remaining width is no longer mainly the old lifecycle-adjacency story, but it is still real enough to keep prompt contracts as the highest-value cleanup seam.

### Single highest-value remaining seam

- `prompt contracts`

Most valuable next tightening, based on this rerun only:

- keep `tests/test_prompt_context.py` as the direct-owner suite for prompt-contract/helper semantics
- stop secondary social-adjacent suites from directly importing prompt-owner helper internals where exported consumer behavior or local fixtures would suffice
