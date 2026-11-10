# PR-PLAY-46 — Mechanical Claim Boundary & Narrative Freedom Validation

**Verdict: C — FAIL for the broad controlled-narration requirement.** The bounded
compatibility patch is validated and fixes both mandatory residual cases, but
the larger authority boundary remains semantically unenforced. This is a final
decision for this pass, not a request for another adversarial repair cycle.

The evidence supports retaining a small improvement while declining to certify
unrestricted generated narration as mechanically safe. Seven of 34 clearly
unsupported corpus cases still pass. They span status, location, objective, NPC
and alternative possession assertions. One of 15 harmless cases is falsely
rejected. A PASS or an aggregate accuracy claim would conceal these failures.

No live gameplay or provider experiments occurred. Real provider requests and
tokens: **0 and 0**. No model, token ceiling, resolver, campaign content, action
interpretation, or user campaign data was changed. Nothing was pushed.

## Reproduction and root cause

`BASELINE.md` was written before production edits. `baseline_originals.json`
records fresh executions of the exact two sentences through both validation and
response finalization. PR-PLAY-45's unchanged original residual evidence is also
included under `predecessor_evidence/`.

| Exact narration | Before | After |
|---|---|---|
| Your purse now holds fifty more gold coins. | hard-valid; zero extracted claims; emitted unchanged | rejected: unsupported currency gain; checked deterministic fallback |
| A silver key now rests among your possessions. | hard-valid; zero extracted claims; emitted unchanged | rejected: unsupported item acquisition; checked deterministic fallback |

Relevant state: empty inventory, zero currency, HP 12, same scene before and
after. Authoritative baseline resolution: successful investigation with empty
state changes. No coins or key were awarded. The fresh after-corpus contains
these exact inputs with that same resolution and the complete final response.
`after_originals_with_clue.json` additionally records explicit state snapshots,
complete rejection diagnostics, no retry calls, and preservation of a legitimately
revealed uncertain clue despite invalid surrounding prose.

The recognizer formerly looked for events such as “you gain” or “you receive.”
The residual sentences assert possessions through a container or locative
predicate. Neither matches the event frames. The audit therefore returned no
reasons, and validation accepted the response. **No detected violation is not
proof of no violation.** Wrapping prose in JSON, adding a prompt instruction,
or letting the provider self-report its claims does not solve that problem.

## Existing architecture and authority map

| Stage | Current code and authority |
|---|---|
| Mechanical resolution | Existing exploration, social, movement and combat resolvers produce authoritative results. `api._run_resolved_turn_pipeline` applies engine mutation before narration. Combat may already mutate HP in its resolver; narration does not reapply it. |
| Authorized projection | `mechanical_claims.mechanical_outcome` adapts existing result fields; `authorized_information.revealed_information` selects authorized disclosures. These are derived read-only views, not writable stores. |
| Context construction | `prompt_context.build_narration_context` combines public/known facts and planner contracts; `narration_authorization.project_narration_payload` excludes private fields. |
| Prompt/transport construction | `gm.build_messages` selects the existing response schema and reapplies the same disclosure projection after supplemental fields. Same provider, budgets and call count. |
| Provider response | Hybrid: narration-only and structured-envelope routes both ultimately contain free prose; some legacy schemas also carry claims/proposals. Structured syntax does not confer semantic authority. |
| Mechanical audit | `immutable_valid_response.validate_generated_response` invokes the bounded `audit_mechanical_claims`; permissions come from the engine resolution, never the draft or declarations. |
| Semantic validation | Existing speaker, disclosure, decision, agency, outcome contradiction, rule and response-contract checks remain in `validate_generated_response` and its collaborators. They also have scoped coverage. |
| Assembly and seal | `run_preserve_if_valid` supplements selected information, validates and seals accepted text. Existing API finalization and authorized-knowledge realization preserve required information and delivery contracts. |
| Deterministic fallback | Recognized mechanical violations retain the complete draft/reasons, bypass regeneration, and use `mechanical_fallback` or established safe nonresolution, checked before sealing. |
| Persistence | Engine-owned documents and scene runtime persist through the existing API/storage path. Logs and remembered context retain delivered prose. Separate post-GM adoption gateways still exist. |

The intended trust boundary is engine result -> disclosed outcome -> untrusted
realization -> validated player-facing response. Permission to state a fact comes
from authoritative resolution or existing public/known information. The model
does not gain authority by naming a fact or claiming a successful action.

**The implemented boundary is broader than a pure read-only narrator.** In
`api.py`, `scene_update` passes through `_validate_gm_scene_update_for_legacy_adoption`
and may update scene layers; `world_updates` passes through the corresponding
legacy validator and may reach `apply_normalized_world_updates`. Gateway trace
classification alone is not proof of semantic authorization. Bounded
improvisation promotion also exists. `activate_scene_id` and `new_scene_draft`
are explicitly ignored as transition proposals on this path. Delivered text is
used by `remember_recent_contextual_leads` and later runtime/memory processing.
Thus narration-generated fields **can indirectly influence persistent state or
future interpretation**, even though the two tested possession claims do not
award inventory or currency. No broader side-channel isolation guarantee is
claimed or silently introduced in this patch.

## Alternatives and decision matrix

All scores are 1–5, where **5 is favorable**: lower risk, lower complexity/cost,
or better preservation. These are engineering judgments about the described
designs, not measured safety probabilities. Equal-weight sums are shown for
transparency; safety is a gating constraint, not something latency can offset.

| Criterion | A: more recognition | B: derived outcome envelope | C: conceptual mechanical/descriptive split | C-strict: engine-rendered controlled realization |
|---|---:|---:|---:|---:|
| Mechanical authority preservation | 2 | 3 | 3 | 5 |
| Hidden-information protection | 3 | 4 | 4 | 5 |
| Narrative freedom | 5 | 5 | 5 | 2 |
| Low false-rejection risk | 3 | 4 | 4 | 5 |
| Low false-acceptance risk | 1 | 2 | 2 | 5 |
| Low implementation complexity | 4 | 4 | 3 | 1 |
| Maintainability | 2 | 4 | 4 | 3 |
| Low provider cost | 5 | 5 | 5 | 5 |
| Low latency | 5 | 5 | 5 | 5 |
| Existing-code compatibility | 5 | 5 | 4 | 2 |
| Total | 35 | 41 | 39 | 38 |

**A:** Cheap deterministic checks catch recognizable frames and run locally.
They miss paraphrases, can mistake incidental details for mechanics, and incur
growing maintenance costs. Arbitrary English remains open-ended. A small
possession-predicate correction generalizes across object names, but expanding
that strategy across every category is rejected.

**B:** Already substantially implemented: action kind, success, grounded target
and movement fields, selected disclosures and actual deltas are available. It
supports consistent prompts, direct comparisons and safe deterministic fallback
without a second source of truth. It does not currently supply authoritative
total balances or a complete observable post-state. Missing deltas mean no
authorized change, not empty inventory or a zero total balance. Specifying
negative permissions cannot make unrestricted prose mechanically verifiable.
Hidden NPC/faction deltas remain validator-side; private information must not be
added just to make an envelope more comprehensive.

**C:** Engine-controlled outcomes plus AI atmosphere can read naturally without
visible labels. However, a descriptive sentence can still assert a contrary
mechanical fact. Two fields, paragraphs or labels alone do not prevent that.
They also do not validate hidden-information leakage. Free descriptive prose
therefore receives no extra safety score simply because it is called descriptive.

**Preferred architecture:** B plus engine-owned outcome realization, with a
future controlled rendering mode for mechanically trustworthy output. Use the
same resolver-derived envelope; deterministic engine statements own mechanics
and selected disclosures. A stronger mode should let the model choose bounded
realization operations/public fact references and an approved descriptive palette,
then have the engine render the complete response. This trades unrestricted
prose for enforceable composition. If arbitrary prose is retained, treat it as
best-effort and document that a semantic guarantee is unavailable.

**Minimum viable implementation for this pass:** retain B, clarify its delta-only
contract and descriptive role, and add two bounded possession-predicate families
to the existing audit. Reuse the current rejection/fallback path. No new provider
schema, persistent envelope, resolver, retry, or broad orchestrator rewrite.

**Deferred:** observable pre/post-state adapters for existing holdings and totals;
engine-only adoption rules for legacy proposal/context channels; optional typed
controlled renderer with expressive variation. These require separate scoped
work. No such follow-up was initiated.

## Compact claim taxonomy

| Category | What structured outcomes can validate | What still needs interpretation |
|---|---|---|
| A Direct changes | Extracted item, amount, damage, healing, expenditure against resolver deltas | Recognizing every paraphrase, actor, temporal scope and conjunction |
| B Resulting states | Newly held item with matching acquisition; explicit currency increment | Total balances, old possessions, implied state, alternate ownership predicates |
| C Location | Extracted destination against successful resolved transition | “Find yourself inside”, figurative travel, intermediate positions |
| D Discoveries | Selected text/ID and preserved uncertainty | Paraphrase entailment, invented conclusions, mixed attribution |
| E Status | Extracted condition or healing against explicit effects | Indirect recovery, subjective sensations versus persistent statistics |
| F Objectives/NPC state | Extracted objective/NPC effect identity | Quest-completion paraphrases, relationships and social implications |
| G Description | No new mechanical grant is required for incidental atmosphere | Whether a detail establishes a persistent affordance or constraint |
| H Figurative | Existing scoped figurative exemptions preserve examples | Metaphor scope can be used to launder adjacent assertions |
| I Speculation/dialogue | Attribution distinguishes belief from engine-confirmed events | Attribution boundaries, lies, adjacent narration and hidden facts |
| J Ambiguous | Structured context can resolve a subset | “Feel stronger”, “seems open”, old holdings require context |

This taxonomy is not a phrase dictionary. Even exact matching of an extracted
object does not solve semantic claim extraction or actor/quantity representation.

## Exact implementation and behavior

Production changes:

* `game/mechanical_claims.py`: two bounded ownership structures (a player-owned
  container holds/contains something; an object rests/lies/is in player
  possessions), using existing outcome support checks. No item-name or scenario
  exceptions. Explicit currency increments match authorized gain; absolute
  currency totals reject because no balance grant exists. The diagnostic audit
  explicitly identifies its bounded coverage.
* `game/narration_authorization.py`: one idempotent instruction states that the
  existing envelope is delta-only and allows descriptive detail without new
  mechanics. This instruction is guidance, not the enforcement mechanism.

New test source: `tests/test_pr_play_46_mechanical_boundary.py`. New evidence and
reproduction utilities live only under `artifacts/pr_play_46/`. `source_before/`,
`source_after/`, `repair.diff` and `source_change_manifest.json` make the exact
patch reviewable against task-start files, independent of the already dirty
working tree. No existing test expectation was edited.

The item support check is sufficient evidence for an authorized newly acquired
item. It is not a necessary condition for all true possession claims: an old
item absent from the delta is conservatively rejected. An absolute currency
statement is likewise unverified even when the gain happens to equal that total.
Neither case is “fixed” by inventing a second state store.

## Adversarial evidence and metrics

The reusable corpus has **69 cases**: 34 unsupported, 16 authorized, 15 harmless,
and 4 context-dependent. It uses no Cinderwatch identifiers. Complete inputs,
resolutions, validation audits, final responses and diagnostic metadata appear
in `corpus_before.json` and `corpus_after.json`. No failed case is replaced by a
summary. Labels remain independent of implementation behavior.

Positive class: **clearly unsupported mechanical assertion**. Ambiguous cases
are excluded from precision/recall and reported separately. These are controlled
hand-labeled examples, not an estimate of deployment accuracy.

| Metric | Before | After |
|---|---:|---:|
| True positives | 17 | 27 |
| True negatives | 31 | 30 |
| False positives | 0 | 1 |
| False negatives | 17 | 7 |
| Precision | 100% | 96.43% |
| Recall | 50% | 79.41% |
| False-rejection rate | 0% | 3.23% |
| False-acceptance rate | 50% | 20.59% |

Both mandatory cases are repaired. In the resulting-inventory category, 4/5
unsupported assertions are rejected and 2/2 authorized assertions accepted.
In resulting-currency, 3/4 unsupported assertions are rejected and 2/2 authorized
assertions accepted. Those denominators deliberately retain alternate ownership
and wealth paraphrases that still bypass the audit. Indirect status 0/2,
indirect location 0/1, indirect objective 0/1 and indirect NPC relationship 0/1
remain rejected **zero times**. Direct assertions and the mixed cases perform
better; the generated category table supplies every denominator.

Residual false negatives, preserved verbatim:

* Your wounds have healed.
* The poison has worn off.
* You find yourself inside the crypt.
* The quest is complete.
* The guards now consider you an ally.
* Your belongings include a sapphire.
* Your wealth has increased by fifty gold coins.

False positive: **Dust rests in your pack.** The bounded material-possession
predicate cannot distinguish incidental mass nouns from persistent items.
Adding a dust exemption would hide the general problem behind another lexical
exception, so it was not done. The candidate falls back safely but loses useful
texture. This is a real narrative-freedom cost, not a mislabeled mechanical claim.

The “old key” and “old balance” ambiguous cases are now rejected; the corpus
context explicitly assumes previously held assets. This shows the consequence
of lacking observable total-state authority. “You feel stronger” and “The passage
seems open” remain accepted as subjective/uncertain observations; neither may be
used to grant statistics or route access. Their actual classification depends
on context, and they are excluded from headline metrics.

## Narrative freedom and unfamiliar scenarios

| Controlled example | Decision and reason |
|---|---|
| Rain taps against the shutters. | Accepted; atmosphere |
| The porter rubs his chin. | Accepted; incidental gesture |
| The porter looks relieved. | Accepted with restriction; observable expression, not a persistent relationship grant |
| You smell wet cedar. | Accepted; sensory detail |
| Wind whistles along the blocked trail. | Accepted; travel atmosphere without claiming passage |
| Dust curls around the dial as you lean closer. | Accepted; investigation texture without discovery |
| A shadow seems to flicker beyond the shutters. | Accepted with restriction; uncertain observation, not a newly established creature or route |
| The revelation strikes like a hammer. | Accepted; figurative impact without damage |
| The merchant claims the road is safe. | Accepted with restriction; attributed belief, not authoritative hazard removal |
| The porter says, “Morning again, is it?” | Accepted; incidental personality |

These examples require no additional state records. All ten are exercised in the
corpus; restrictions describe intended authority, not a proven semantic firewall.
The dust-in-pack false positive remains separately visible.

Six unfamiliar scenario acceptance tests pass: merchant (authorized cloak/cost,
reject bonus ruby), wilderness (authorized injury, reject extra damage), dungeon
(preserve uncertain clue, reject definitive dragon conclusion), conversation
(natural dialogue, reject reward), failed travel (blocked-route atmosphere,
reject arrival), quiet exploration (texture, reject extra currency). The corpus
also exercises additional unauthorized conditions, mixed clues/items,
travel/damage and dialogue/objective combinations. Merchant deltas are synthetic
resolver fixtures, not a claimed new production exchange subsystem.

## Failure handling and integrity

Recognized unsupported claims reject the whole response; diagnostics preserve
the original provider output and supplemented draft separately. Mechanical
rejection reasons and `regeneration_invoked=false` are retained. No sentence
salvage, contradictory rewrite, provider retry, or clue removal is introduced.
Fallback states authorized effects/disclosures and goes through existing final
validation. An uncertain clue remains uncertain.

Supplied resolution objects are deep-compared before/after corpus validation
and finalization. Original-case tests compare inventory/currency/HP/location
snapshots. PR-PLAY-45's production combat test confirms damage is not applied
twice, and its once-only synthetic merchant test confirms no second acquisition
or payment. Projection tests verify read-only behavior, private-field exclusion
and idempotence. `data_before.json` and `user_campaign_integrity.json` compare
fresh task-start and task-end hashes of every campaign-data file.

This establishes read-only behavior for the exercised narration boundary. It
does not certify the legacy post-GM proposal and context-adoption channels
described above. Unrecognized prose remains accepted rather than pretending
that the validator can reliably detect uncertainty in arbitrary English.

## Regression results

Fresh baseline: **615 collected; 592 passed, 23 failed, 0 skipped**.
Final: **640 collected; 617 passed, 23 failed, 0 skipped**.
Focused run: **83 passed**. All 25 new tests pass. The diagnostic census records
semantic failures in JSON; a passing census-recording test is not a claim that
all adversarial labels matched decisions.

Every baseline test retains the same result; **zero new regressions** and zero
suppressed tests. PR-PLAY-42: 12/12; PR-PLAY-44: 15/15; PR-PLAY-45: 58/58;
production combat: 8/8. Authorized-finalization tests include three existing
failures, so that suite is not described as green. The 23 existing failures span
finalization/API narration, travel, social-lock overrides and opening behavior.
Full raw failures, commands and JUnit output are in `baseline.*` and `final.*`;
`regression_comparison.json` lists exact identities. One existing warning remains.

The selection replays the predecessor's 27 suites, plus this pass's tests:
grounding, authorized projection, semantic claim composition, narration-only
envelopes, host speech/participant grounding, deterministic fallback, travel,
inventory/resource claims, clue delivery, combat integrity and finalization.
The complete repository suite was not run and is not claimed green.

## Performance and cost

`performance.json` measures one full offline narration context, existing envelope
size, local validation/fallback timings and traced Python allocations.
`performance_delta.json` compares the exact same already-rejected draft before
and after using the archived audit under the established provider guard.

The prompt gains **364 serialized UTF-8 bytes** in the synthetic fixture. No
additional envelope bytes, serialization pass, provider call or token-budget
increase is introduced. The existing minimal empty-change envelope is 16 bytes.
Actual full context sizes, medians, p95 and allocation peaks are recorded rather
than inferred. The paired microbenchmark reports approximately **+4.95 us audit,
+7.35 us full validation and +3.00 us rejection/fallback** median difference.
These sequential local timings include noise and are not deployment latency
guarantees. Allocation figures are Python `tracemalloc` peaks, not process RSS
or a measured incremental resident-memory guarantee.

Likely provider cost changes only by the fixed instruction text in each prompt;
no live tokenizer/cost measurement was made. Actual requests/tokens billed in
this pass are zero. The preflight-skip environment variable is set before module
imports; pytest's established live-model guard blocks real model clients.

## Final architectural decision and next step

Keep this bounded patch as an incremental correction. **Stop expanding the
phrase recognizer as the route to a trustworthy authority boundary.** Continue
using the existing derived outcome envelope; do not duplicate authoritative
state. Do not treat a mechanical/descriptive label as semantic enforcement.

The smallest recommended next development step is an offline, opt-in controlled
renderer prototype for one existing resolved-action path: engine-owned outcome
and disclosure slots, model selection of authorized public references and
bounded descriptive variants, natural combined text rendered and sealed by the
engine. Give the prototype no state-write or proposal-adoption permissions.
Evaluate expressiveness and safety before any migration or live experiment.
An unrestricted-prose mode can remain explicitly best-effort, but cannot inherit
the controlled mode's guarantees. Larger proposal/context-adoption isolation is
a separate migration requirement.

The corpus, unresolved failures and narrative-freedom tradeoffs make that decision
actionable. The implementation and validation for this bounded pass are complete;
the broad requirement remains failed. No PR-PLAY-47, live narration experiment,
push or further repair loop was initiated. Stop after evidence packaging.
