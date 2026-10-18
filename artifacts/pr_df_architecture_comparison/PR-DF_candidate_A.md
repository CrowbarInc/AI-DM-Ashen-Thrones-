# PR-DF Candidate A — Current Deterministic Pipeline

Candidate A is the pipeline in the architecture map. This file evaluates it as an architecture. Current bugs are listed separately from structural limits.

## Mechanisms

**Interpretation.** `establish_ordinary_gameplay_contract` builds a resolution contract from the utterance, the referent catalog, discourse focus, and visible turns. The deterministic fast path runs first. A model interpreter runs only on abstention, and only when live interpretation is enabled. The interpreter's system text says it does not decide what exists, what is true, or what happens next. Operations are a closed enum.

**Resolver selection.** `select_ordinary_resolver` reads the contract operation, subject, and commitment. Unresolved or uncommitted operations become `generation`, which means no specialized resolver. Adjudication families come from the subject. Combat is selected only when the contract subject is combat, the session is in combat, and the commitment is executed now. An attack parsed outside combat is discarded in `chat`.

**Action composition.** `segment_mixed_player_turn` can separate speech from a declared action. The chat cascade then tries one winning normalized action. There is no dependency graph. A second clause survives only when a parser returns it inside that one action, or when a later travel override replaces the action under `committed_travel_recorded`.

**State authority.** Specialized resolvers produce a resolution dict. `_apply_authoritative_resolution_state_mutation` applies it. Narration is requested from the mutated state. `state_authority` rejects model-named owners.

**Provider context.** `build_messages` serializes the post-resolution payload. After PR-DE, seven JSON-equal top-level contracts are omitted. The `response_policy` children, the smaller continuity snapshot, the decision, the recipe, the scene, and the speaker contract remain. On the revised S1 payload the largest remaining pieces are `response_policy` (22,698 bytes, 25.9%), `instructions` (13,947 bytes, 15.9%), `gm_resolution_decision` (8,349 bytes, 9.5%), and `decision_facing_answer_recipe` (6,707 bytes, 7.7%).

**Validation.** Policy enforcement, visibility checks, narration-state consistency, and the final emission gate run on model text. Failure can trigger up to two targeted retries, then a deterministic fallback line (`obligation_preserving_fallback_line` and related engine text).

**Recovery.** Malformed interpretation does not become a target. A contradicting parser result is dropped. An unsupported downtime action does not delegate. A pending check returns an engine prompt and skips narration. Post-narration adoption is the weak recovery path: the gateway observes and allows legacy shape-valid updates.

## Behavior by situation

| Situation | What the architecture does | What is only a current defect |
|---|---|---|
| Ordinary actions | Contract subject selects social, exploration, travel, or combat. PR-CK shows desk investigation and a named social greeting reaching the same kinds from `action` and `chat`. | Shared-pipeline dialogue-lock failures remain. |
| Unusual actions | Unknown or uncommitted operations fall through to `generation` or to a blocked noncombat outcome. The model may still narrate inside the decision. | A missing verb pattern is a lexicon gap. A deterministic pipeline can add a pattern without becoming a planner. |
| Compound actions | The segmenter plus one winning action. Contingency text forces classification back onto the raw utterance. | No evidence in this cycle that both halves of an arbitrary compound are resolved as ordered steps. |
| Ambiguous requests | Contract can set `ambiguous` / clarification. Fallback text asks which referent was meant, or states that the reference cannot be resolved. | Clarification quality depends on the fallback line and the narration validators. |
| Conversation | Directed entry, discourse focus, speaker contract, and social resolver. S1–S3 are narration-only social payloads. Follow-up fixtures carry prior visible turns. | Inherited strict-social and speaker failures in the shared suite. |
| Hidden information | Visibility contract plus hidden-fact instructions. H1 stays off the reduced-context projector. Bounded improvisation rejects hidden-information wording. | Prompt instructions can be ignored by the model. Detection is the validator, not the architecture diagram. |
| Mechanical resolution | `resolve_attack` rolls and writes HP. Skill defaults on an exploration action can require a check before narration. A diplomacy check can finish without a provider call (PR-CK). | Synthetic fixtures patch `roll_die`. Authored scenes in the PR-DE note have no enemies. |

## Strengths

- Authority is named, and the main mutation happens before narration.
- Ordinary play reuses one contract instead of racing peer parsers. The race is reduced to a gated cascade.
- Failure can be a structured non-result: blocked, ambiguous, unsupported, pending check, off-scene target.
- The same fixtures already produce byte counts, hashes, resolver labels, and envelope labels with zero provider calls.
- Retries are bounded.
- Improvisation has a typed reject path for consequential and mechanical content.

## Limits that belong to this shape

- Open-ended wording is only as good as the fast path, the segmenter, and the operation enum. Anything else is `generation` plus a large narration prompt.
- One winning action is a poor fit for ordered compounds ("do X, then Y if it works").
- The narration request is large even for a preference question, because the payload carries policy, decision, recipe, and scene machinery whether or not the turn needs them.
- Independent world activity is a per-chat tick, not a schedule the utterance can opt into. Waiting and asking both tick.
- The model can still influence state after narration through the observe-only gateway. That is a hole in the current tree. It is also the kind of hole a deterministic design is able to close by making the gateway refuse. Closing it is out of scope here.

## Limits that are not inherent

Wrong resolver on a specific sentence, unbound M1 movement, notice-board test failures, and the 24 shared-pipeline failures are evidence about this tree. They are not a reason to treat every future deterministic classifier as incapable of those cases.

## What A must keep in the experiment

Pin `enable_model_interpretation=False` and `ASHEN_DISABLE_LIVE_INTERPRETATION` so A's score is the deterministic path. The existing interpreter is a latent second call. Leaving it on would mix A with a fragment of B.
