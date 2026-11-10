# PR-PLAY-45 — Narration Input Isolation & Mechanical Claim Validation

Verdict: **B — PARTIAL**. Both original failures and the required offline matrix are repaired, but additional indirect-possession probes expose materially incomplete freeform claim coverage. No live narration experiment is authorized by this result.

## Executive result

Both unchanged PR-PLAY-44 failures are repaired. Private scene/clue material is excluded at context rendering and again immediately before provider transport. Mechanical consequences recognized by the deterministic audit require structured resolver support. A recognized contradictory draft is rejected as a whole; no provider retry or sentence salvage is used for that failure. Fallback preserves selected discoveries and communicates supported effects. Interpretation, action admission and mechanical resolvers are unchanged. The broader freeform invariant is not yet enforceable: the residual probes below still pass validation incorrectly.

Real provider requests: **0**. Real provider tokens: **0**. Live gameplay turns: **0**. No push, campaign experiment, provider configuration, model, token ceiling, campaign fixture or user campaign edit was performed.

## Baseline and root causes

`baseline.txt`, `baseline.xml`, `baseline_contradiction.json`, `baseline_synthetic_context.json`, and `BASELINE.md` preserve the original failures and inputs. The source-level investigation was recorded before production repair.

The legacy hidden-context probe has an additional defect: its default active scene causes `get_effective_scene` to replace the injected scene, while generic system text contains `SECRETS`. The original test failed, but its result alone did not prove content exposure. The actual pre-edit synthetic ledger replay independently confirmed secret text at `scene.discoverable_clues`, `scene.gm_only.hidden_facts`, `scene.clue_records.undiscovered`, and `scene.clue_visibility.implicit`, including repeated actions eligible for narration. That raw replay is retained. No assertion in either original probe was changed. The redundant instruction phrase `HIDDEN FACTS / SECRETS` is now `HIDDEN FACTS`, preserving the prohibition without colliding with the unchanged broad canary assertion.

`gm._scene_layers` and `collect_narration_context_call_kwargs` separated clues but still forwarded all three authority layers. `prompt_context.build_narration_context` reassembled them into the provider payload. `state_channels.project_public_payload` filtered only top-level debug fields. Prompt instructions were the sole protection for nested private facts.

For the successful ledger investigation, authoritative changes contained only clue revelation. The controlled draft, `You receive fifty gold coins and a silver key.`, received `hard_valid=true` from `validate_generated_response`. Existing decision/claim audits did not compare those material consequences with structured resource/inventory results. Clue supplementation appended the legitimate information and the combined false receipt was sealed. Authoritative state itself did not award either resource.

## Narration input inventory

| Source | Authority and projection |
|---|---|
| Campaign | MIXED: title, tone, role and magic style retained; premise, GM guidance and unsurfaced pressure prose excluded. |
| Character | KNOWN: existing player-owned name, HP, conditions and capabilities remain. No other character's private sheet is forwarded. |
| Current scene summary and visible facts | PUBLIC under the existing authored public-field contract; location and summary retained. Semantic misclassification by an author remains a limitation. |
| NPC records | MIXED: canonical active speaker ID/name retained; private agenda, knowledge scope, reliability and hidden motives excluded. Selected dialogue is separately REVEALED. |
| Interactables | MIXED: grounded action/target IDs and public visible descriptions remain; raw objects, clue links and private requirements do not ship. |
| Discovered clues | KNOWN: ID/text/presentation retained, without reveal requirements, future links or private extensions. Depends on character/session discovery state. |
| Undiscovered clues and GM notes | PRIVATE: excluded, including implicit/locked copies. A search intent does not authorize the clue catalog. |
| Quest/lead state | MIXED: existing player lead projections and explicit pending `surface` text remain. Legacy internal pending `hint` objects are excluded. |
| Factions, world events and clocks | MIXED/PRIVATE: complete summaries, unobserved event logs, pressure prose, nested world-pressure and clock summaries excluded. NPC/faction mutation internals stay validator-side unless separately disclosed. |
| History | KNOWN: existing bounded selector uses player input and player-facing GM snippets. Raw private logs and arbitrary metadata are not narration inputs. |
| Resolver result | MIXED: action type, target, success, resolved destination and selected information remain. Raw metadata, hints, hidden rolls, DCs, thresholds, world updates and enemy statistics are excluded. |
| Check result | PUBLIC/REVEALED: skill and success retained; roll/total/DC not forwarded. |
| Planner/decision/recipe | Existing public projections retained as instructions and authorized claims; recursive private extension fields and nested clock/pressure copies are removed. Engine copies remain available to validators. |
| Provider construction | `gm.build_messages` applies the same projection after convenience additions. No new transport or model calls. |
| Fallback | Deterministic selected information and structured effects only; no hidden-clue lookup, campaign dump or resolver hint. |

Classifications depend on the current character, active scene, resolved target, discovery state and selected disclosure. Presence in a scene or NPC record does not grant disclosure.

## Projection specification and examples

`game/narration_authorization.py` makes a detached, read-only projection. It runs in `build_narration_context`, including diagnostic assembly, and after GM supplemental fields. It preserves shared public contract identity within each projection, avoiding planner-contract identity regressions.

New fields: `authorized_information` (newly selected facts with source/status), `authorized_mechanical_outcome` (bounded actual effects), and `authorized_dialogue` when a resolved NPC topic was selected. Previously known clue records remain distinct from newly revealed information. Public atmosphere and observable scene facts remain available after unsuccessful investigation or denied movement. Missing information grants no permission to invent it.

Before: the ledger context contains `SECRET merchant faction rendezvous` as an undiscovered clue and `SECRET patron controls the faction` as a GM-only fact. After: both strings are absent, while public rain/ledger facts and the legitimately revealed ledger contents remain. Compare `baseline_synthetic_context.json` and `after_synthetic_context.json`. The independent observatory test additionally probes GM notes, world events, pressure prose, clocks, interactable private extensions and NPC private profile data.

## Mechanical validation contract

`game/mechanical_claims.py` extends the established `validate_generated_response` boundary; it does not replace existing speaker, visibility, decision, envelope, agency or contradiction checks. The adapter consumes explicit resolver deltas, real combat damage and self-targeted effects, resolved movement, and selected discoveries. Synthetic exchange fixtures use explicit deltas because the repository has no general merchant inventory/currency resolver. No narration-derived mutation is written.

The deterministic recognizer distinguishes acquisition/loss, currency gain/spend, injury/healing, conditions, travel, routes, objectives, discoveries, NPC/faction state assertions, encounters and quantified time. It checks amounts, object identity, destination and supported result, including mixed supported/unsupported claims. Common passive transfers are normalized into the same audit. Named actors without a matching actor-specific grant are conservatively rejected. Provider declarations, raw player requests, authored background prose and private metadata cannot grant an effect. The existing rule validator also receives deterministic authorized consequence text, so a legitimate route unlock is not falsely rejected as an invented rule.

Observation of an item does not mean receipt. A quoted NPC assertion is a speaker claim rather than a confirmed mechanical event; adjacent narration still undergoes validation. Conditional and figurative frames are not rejected solely for words such as gold, wound or travel. Existing NPC speaker/disclosure checks still apply.

## Rejection, fallback and state integrity

Before: the unsupported coins/key draft is accepted and sealed. After: validation reports `unsupported_mechanical_claim:currency_gained` and `unsupported_mechanical_claim:items_added`; only the authorized ledger discovery reaches the player. `after_original_contradiction.json` and `rejection_fallback.json` retain reasons and output. `rejected_provider_output` preserves the complete original provider string; `rejected_mechanical_draft` also retains the supplemented candidate.

Both first-attempt and retry mechanical violations bypass arbitrary sentence salvage and terminate in checked deterministic fallback. No extra provider retry is introduced. Tests verify that a prior unrelated invalid response may trigger the existing single retry, but a mechanical violation in that retry is safely rejected. A terminal fallback validation failure replaces the draft with a controlled non-claiming response, never the original contradictory prose.

Validation and projection do not mutate authoritative input. Tests compare resolutions before/after, preserve HP/location/inventory/resources, verify a synthetic merchant transaction applies once, and exercise actual production `enemy_take_turn` damage without applying it again. `transaction_integrity.json` records the once-only exchange. `user_campaign_integrity.json` compares the complete data fingerprint against independent PR-PLAY-43 evidence; it is not mislabeled as a new task-start snapshot.

## Required cases and cross-scenario results

All sixteen required cases pass: A hidden clue isolation; B GM notes; C newly revealed clue; D known information; E unsupported item; F unsupported currency; G supported item; H unsupported damage; I supported damage; J denied travel; K supported travel; L unsupported discovery; M atmosphere; N metaphor; O NPC speculation; P mixed claims preserving the clue. `required_tests.json` identifies every exact test.

All six unfamiliar scenarios pass: merchant exchange, wilderness injury, dungeon exploration, NPC conversation, failed travel, and uncertain partial discovery. Supported examples are accepted and unsupported additions rejected. Scenario names/item IDs are not production validation rules. `cross_scenarios.json` gives exact results. Additional adversarial tests cover losses, spending, healing, conditions, route/objective changes, NPC/faction changes, time, combat, passive transfers, named actors, wrong quantities, extra items and provider self-authorization.

## Regression evidence and changed expectations

Exact commands and raw output are preserved in `final_command.txt`, `baseline_combined_command.txt`, `baseline*.txt/xml`, `context_baseline.txt/xml`, `context_regression.txt/xml`, `focused.txt/xml`, and `final_combined_regression.txt/xml`. Machine-readable counts and individual carried-forward failures are in `regression_comparison.json` and `summary.json`. The final combined run uses a dedicated temporary directory and no overlapping pytest invocation.

The original gameplay-only baseline had 354 passes and 23 failures. Original context-only baseline had 157 passes. Exact combined baseline: 531 passed, 26 failed (the original 23, the two original PR-PLAY-44 probes, and one Windows file-operation failure). Final combined: **592 passed, 23 failed, 0 skipped**, 615 collected; no previously passing baseline test now fails. All **58 new pytest cases pass**. Two additional diagnostic adversarial probes fail the broader claim contract and remain explicitly unresolved.

Earlier overlapping/variable runs produced Windows `os.replace` access-denied errors during temporary campaign resets; those outputs remain in `combined_contention.*`, and both additional affected opening tests passed separately (`opening_variance.*`). The exact combined pre-change replay also records a Windows temporary-file failure. These are not repaired or suppressed. Initial matrix harness mistakes and the supported-route rejection are preserved as raw intermediate results. A final projection-shape check also caught removal of neutral planner pressure fields; the projection now retains `world_pressure=null` and `clock_summaries=[]` while excluding their private content, preserving existing planner convergence assertions without changing them.

Changed existing assertions, all intentional contract updates:

* `tests/test_exploration_skill_checks.py`: replace expected roll=10, total=12, DC=8 with absence checks; retain successful skill-check outcome and narration instruction checks.
* `tests/test_prompt_context.py`: expect the equivalent hidden-facts instruction label without `/ SECRETS`; exclude private promoted-NPC profile/knowledge/reliability/agenda data while retaining canonical speaker identity; turn undiscovered hinting off; assert absence of GM-only and undiscovered records in place of obsolete layering instructions; exclude a pending internal hint while retaining its independently public surface.

No other existing assertion was changed. In particular neither original PR-PLAY-44 failure was weakened, skipped or xfailed. The source snapshots and task-relative `repair.diff` distinguish this repair from pre-existing dirty workspace edits.

## Size, overhead and provider budget

For the same synthetic ledger sequence, full serialized narration messages shrink from approximately 93,001 to 85,982 bytes (7.55%) and 87,126 to 82,979 bytes (4.76%). `context_size.json` records final exact measurements; small later contract additions may shift these illustrative values. These are bytes, not measured token counts, and remain relatively large because existing public planner contracts were retained. No token ceiling was raised and no unrelated optimization was performed.

The local microbenchmark executes 1,000 short deterministic audits; exact elapsed time is in `validation_timing.json` (about 0.37 seconds total, or 0.37 ms per short audit in the final run; earlier local measurements varied). It excludes provider latency and is not a performance guarantee. Projection performs detached dictionary copies twice at the two existing boundaries; that copy overhead was not separately timed. Provider requests/tokens/live turns remain zero; preflight was disabled before all application imports and the established autouse transport guard remained enabled.

## Source manifest, limitations and next step

Exact source/test files changed: `game/gm.py`, `game/prompt_context.py`, `game/immutable_valid_response.py`, `game/narration_authorization.py`, `game/mechanical_claims.py`, `tests/test_pr_play_45_narration_authority.py`, `tests/test_prompt_context.py`, `tests/test_exploration_skill_checks.py`. Packaging/evidence files are under `artifacts/pr_play_45` and `handoff`. SHA-256 source and archive manifests are included.

The recognizer is a bounded English grammar, not a proof of arbitrary language. `residual_adversarial.json` records two explicit failing diagnostic probes: `Your purse now holds fifty more gold coins.` and `A silver key now rests among your possessions.` Both have no supporting effects, should be rejected, but return `hard_valid=true`. They are reported as failures, not folded into the passing required matrix or marked xfail/skipped. This is why the overall verdict is PARTIAL despite repairing both original probes. Expanding verb lists cannot establish a universal semantic boundary; indirect possession and state assertions need further structured-claim alignment or a carefully defined conservative prose contract before AI narration can be expanded.

Other limitations include complex coordination, unusual attribution, implicit quantity/unit conversions, semantically mislabeled public authoring fields, and paraphrased uncertainty. Exact matching conservatively rejects some legitimate paraphrases and actor-ambiguous consequences. NPC/faction mutation narration needs separately authorized public disclosure; raw internal mutations are not exposed for prose quality. Existing authored clue supplementation may repeat a paraphrase. The invariant is tested and enforced for the covered consequence frames; unrestricted model prose remains unsafe.

Recommended next step: review the archived contract and add a larger offline adversarial/paraphrase corpus, especially indirect possession changes, named-actor grants and attribution scope, before considering any separately authorized controlled AI narration experiment. Do not automatically route every action through AI narration. PR-PLAY-46 was not initiated. Stop after packaging.
