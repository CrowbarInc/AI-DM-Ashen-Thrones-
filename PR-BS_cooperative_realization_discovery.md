# PR-BS Cooperative Realization Discovery

Date: 2026-10-04. Mode: discovery only. Model/API calls during this discovery: zero. Live gameplay validation during this discovery: zero. No implementation, commit, or push.

Primary evidence: `handoff/CURRENT_REVIEW.md`, `handoff/payload_breakdown.json`, and `artifacts/pr_br_closeout_live_revalidation/`.

## A. Executive Finding

The realization model is expensive and still failing first pass because the prompt currently gives it a large, overlapping contract stack but not a small operational recipe for satisfying that stack. The model receives the authority boundary in several correct but diffuse forms: system prompt rules, top-level `response_policy`, `turn_packet`, `mechanical_resolution` metadata, `resolution_contract`, `gm_resolution_decision`, `realization_claims`, visibility contracts, narrative plan, and retry feedback. The validator then enforces a narrower semantic contract than the model appears to internalize: consequential assertions must either realize authorized decision claims or be a permitted bounded proposal with the right provenance, modality, premise links, and relation kind.

This explains the observed combination:

- `0/4` first-pass acceptance: each first attempt used ordinary GM-answering instincts to add a causal/evidential/status/preference proposition that the validator did not authorize.
- Poor exploitation of valid authority: A1 had an `infer` act scoped to `qualified_possibilities_only`, but the model was not given a compact, example-like "valid answer shape" for bounded inference; it overreached into structural failure, neglect, time, and leads.
- Conservative retries: retry feedback is predominantly rejection-oriented, and retries receive the same large base context plus a new warning. The model can avoid rejection by dropping declarations and consequential content, so it collapses toward safe restatement/nonresolution.
- 25k-33k generation inputs: dominant size is not scene/world facts. It is static and semi-static prompt/policy material, large response policy/turn packet/narrative plan structures, duplicated contract/decision representations, and full resend on retry.
- 238k total tokens for four turns: every turn retried, and retry resends the original system prompt plus unchanged base user payload, adding 5k-7k chars of feedback.

Architecture status: **A - PR-BR remains closed.** The observed defects are AI experience, gameplay usefulness, and performance/cost issues. The authority boundary rejected unauthorized state and did not show systemic provenance/state-integrity failure.

## B. Runtime Request Map

| Step | file -> function/class | Responsibility |
| --- | --- | --- |
| 1 | `game/api.py -> chat` | Main `/api/chat` orchestration: load state, increment turn, advance world tick/clock, segment/classify input, route social/exploration/adjudication, then prepare narration. |
| 2 | `game/live_resolution.py -> attach_interaction_obligation` | Attaches `resolution_contract` and live resolution mode metadata to the resolution object. |
| 3 | `game/resolution_contract.py -> ResolutionContract` and helpers | Canonical owner for operation, target, dimensions, epistemic mode, expected resolution, raw input, and discourse binding. |
| 4 | `game/gm_resolution_decision.py -> build_gm_resolution_decision` / `attach_gm_resolution_decision` | Builds `GMResolutionDecision`, `epistemic_acts`, `answer_relations`, `unresolved_qualifiers`, and `realization_claims`. |
| 5 | `game/prompt_context.py -> build_narration_context` | Canonical model-facing prompt-context packager: instructions, visibility, response policy, turn packet, narrative plan, memory, scene/world, bounded improvisation projection. |
| 6 | `game/gm.py -> build_messages` | Adds extra instruction strings and returns exactly two base messages: `SYSTEM_PROMPT` and JSON-serialized payload. |
| 7 | `game/gm.py -> call_gpt` | Sends `client.responses.create(... input=messages)`. |
| 8 | `game/response_policy_enforcement.py -> guard_gm_output` and `game/gm_resolution_decision.py -> audit_realization_envelope_against_decision` | Parses structured envelope, validates declarations/narration against authority. |
| 9 | `game/immutable_valid_response.py -> run_preserve_if_valid` | Accepts hard-valid response, regenerates once with structured feedback when invalid, then preserves immutable output or safe nonresolution. |
| 10 | `game/api.py` retry loop + `game/gm_retry.py -> build_retry_prompt_for_failure` | Selects targeted retry failures, appends retry feedback to the unchanged original messages, calls model again. |
| 11 | `game/bounded_improvisation.py` | Validates low-consequence `improvisation_proposals`; accepted entries are runtime continuity, not authored world truth. |

## C. Context Composition Table

| Component | Source | Representative size | Static or turn-specific | Duplication class | Needed for authority? | Needed for quality? | Finding |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| System prompt | `game/gm.py:183-323` | 12,543 chars | Mostly static | Necessary plus stale/competing rules | Yes | Yes | Contains schema, claim rules, bounded improvisation, direct-answer and momentum rules. It also encourages concrete answering/hooks that can compete with strict claim authority. |
| Instructions list | `game/prompt_context.py`, `game/gm.py:4113-4240` | A1 26,068 chars | Mixed | Accidental/legacy duplication | Partly | Yes | Largest A1 user component. Many unique strings, not a few repeated literals. Cost comes from accumulated contract layers. |
| Response policy | `game.prompt_context -> build_response_policy` | A1 20,609 chars; A2 top-level 21,229 chars | Turn-specific derivative | Necessary plus accidental duplication | Yes | Yes | Validating/shaping policy is model-visible, but also appears through turn packet and mechanical metadata. |
| Turn packet | `game.turn_packet`, projected by `prompt_context` | A1 10,668 chars; A2 nested response policy 6,096 chars | Turn-specific derivative | Necessary/legacy duplication | Yes | Yes | Carries canonical turn shape but mirrors policy/contract facts also present top-level. |
| Narrative plan | `game.narration_plan_bundle` via `prompt_context` | A1 4,475 chars | Turn-specific derivative | Necessary redundancy | No direct authority | Yes | Useful shaping layer; subordinate to CTIR/visibility/policy. |
| Resolution contract | `game.resolution_contract`, attached by `live_resolution` | A2 compact 522 chars; full nested 3,822 chars | Turn-specific | Accidental/legacy duplication | Yes | Yes | Same semantic contract appears compact and full inside mechanical metadata/decision. |
| GMResolutionDecision | `game.gm_resolution_decision` | A1 2,124 chars; A2 top 2,961 and nested 3,508 chars | Turn-specific | Accidental duplication | Yes | Yes | Canonical authority decision, but repeated in places. |
| Realization claims | `GMResolutionDecision.realization_claims` | A2 1,233 chars copied in both locations | Turn-specific | Accidental duplication | Yes | Yes | The same authorized rows are duplicated. |
| Scene/world/character/campaign | storage via `build_narration_context` | Scene 1,716; character 1,059; campaign 1,057 | Mixed | Necessary | Yes | Yes | Not the dominant cost in the measured A1/A2 payloads. |
| Conversation/memory | recent log + conversational memory window | grows with turns | Turn-specific | Necessary/uncertain | Sometimes | Yes | Supports continuity; selected memory and logs are growth vectors. |
| Retry feedback | `immutable_valid_response` and `gm_retry` | A1 5,068 chars; A2 6,676 chars | Retry-specific | Necessary but verbose | Yes | Yes | Includes validation findings and repeats contract/decision context. It mostly teaches avoidance. |

Deterministic measurements are recorded in `artifacts/pr_bs_cooperative_realization_discovery/context_inventory.json`.

## D. Duplication Map

| Semantic information | Locations | Classification | Why |
| --- | --- | --- | --- |
| Resolution contract | Top-level compact projection, nested mechanical/resolution metadata, retry tail | Accidental/legacy duplication | Same operation/dimension/target/raw input is represented in multiple shapes. |
| GMResolutionDecision | Top-level `gm_resolution_decision`, nested metadata/debug, retry feedback | Accidental duplication | Canonical decision is useful, but duplicate copies add size and create multiple reading paths. |
| Realization claims | Decision rows plus repeated nested copies | Accidental duplication | Same claim IDs/text/provenance copied twice in A2 measurement. |
| Response policy | Top-level `response_policy`, `turn_packet`, prompt contracts, system prose | Necessary plus accidental duplication | Different consumers need policy, but model receives both large object and prose/rule summaries. |
| Player raw text | Contract raw input, turn summary/projection, speaker-selection debug preview | Legacy/debug-only leakage | A1 generation projection omitted full question in one place but preserved it in debug preview. |
| Authority rules | System prompt, instructions array, response policy, visibility contract | Necessary redundancy | Multiple layers serve different concerns, but volume and conflicts dilute the operational path. |
| Retry validation findings | Feedback plus existing candidate metadata | Necessary/uncertain | Feedback is necessary; size and negative framing are questionable. |
| Emission debug | Mechanical resolution metadata | Debug-only leakage | Helpful for traces; not clearly needed in provider context. |

## E. Model/Validator Mismatch Map

| Rejection family | What model did | What validator expected | Model-visible? | Mismatch |
| --- | --- | --- | --- | --- |
| `unauthorized_resolution_decision_fact` | Declared/phrased consequential propositions beyond decision rows. | Only realize authorized `realization_claims`, or valid bounded proposals explicitly permitted by decision. | Partly, in schema/rules/decision. | The validator rule is exact; prompt asks for direct, concrete GM answers and does not provide a compact valid answer recipe per decision. |
| `unauthorized_evidential_relation` | Turned visible damage into "indicating structural failure." | Observation-level inference must stay qualified and not establish a new evidential/causal relation beyond scope. | Partly. | `qualified_possibilities_only` was visible but not translated into acceptable sentence/declaration examples. |
| `unsupported_narrator_lead` | Added neglect/harsh conditions or further leads. | Specific leads require explicit decision authorization or attributed epistemic source. | Partly. | Scene momentum and question-answer pressure plausibly encourage leads, while validator forbids unsupported lead generation. |
| `unauthorized_declared_claim` | Declared sudden-pull cause or baker refusal as authored fact. | Generated proposal/incidental/NPC speech must not request authored world-fact authority. | Yes, but diffuse. | Schema puts `authored_world_fact` in the same declaration surface as generated/npc/incidental lanes, inviting over-declaration. |
| `unauthorized_certainty_upgrade` | Recast known observations as showing broader certainty/damage state. | Restate exact authorized facts or keep uncertainty. | Partly. | Model tries to be helpful by synthesizing; validator treats synthesis as a new claim. |
| `embedded_premise_unlinked` | Said the cause of "the hard pull" is unknown, treating the hard pull as a premise. | Link epistemic-status claims to the hypothesis row and preserve conditionality. | Partly. | Premise-link mechanics are present but operationally hard to use under large context. |
| Ordinary NPC improvisation | Declared an NPC refusal as established authored fact. | Spoken refusal can be plain narration/low-consequence improvisation, with no consequential declaration. | Yes, but ambiguous. | "Every consequential proposition" plus schema encourages declaring dialogue content; mundane speech boundary is not salient enough. |

## F. A1 Case Study

A1 asked what the bell damage suggested. The contract carried `dimension: interpretation`, `epistemic_mode: unknown_allowed`, and the decision contained an `infer` act with authority `observation`, status `inferred`, and scope `qualified_possibilities_only`. The model therefore had permission for bounded observation-level inference, not permission to establish cause, actor, history, neglect, unsafe status, or gameplay leads.

The initial envelope overreached: "structural failure" was rejected as `unauthorized_evidential_relation`, and neglect/harsh conditions were rejected as `unsupported_narrator_lead`. The retry then emitted an empty claim list and a safe restatement of the two visible facts. That final answer passed, but it did not answer the interpretation request.

Most likely cause: inadequate operational representation of the authorization. The authorization existed, but the prompt did not clearly turn it into a small allowed pattern such as: "You may say only that the two visible support failures could be consistent with stress or force; do not name a cause, actor, time, neglect, safety status, or next lead." The retry feedback then made rejection avoidance more salient than useful bounded inference.

## G. B1 Case Study

B1 asked a baker which loaf they usually keep. The scene had a baker and loaves, but no authored preference. The decision established the baker's existence and the stall fact; it did not authorize a durable preference or secret. The model's first attempt declared "The baker refuses to reveal which loaf they usually keep for themselves" as an established authored world fact. The validator rejected this as `unauthorized_declared_claim`.

The retry succeeded by using an empty `declared_claims` list and ordinary quoted speech: `"I'm not comfortable saying which loaf I keep for myself," ...`. That shows the architecture can allow mundane NPC improvisation, but the prompt/schema makes the model think ordinary dialogue content belongs in the same declaration lane as world facts. The bounded improvisation instructions allow ordinary refusals/mannerisms, but they compete with the structured claim declaration rule and the schema field list.

## H. Retry Analysis

Retry is expensive because construction appends feedback to the unchanged original messages. `game/api.py:3041-3048` and `3149-3155` use `list(messages) + [{"role": "user", "content": retry_instruction}]`, so the full system prompt and full base JSON are resent. The measured A1 retry resent 12,543 system chars and 90,681 base user chars, then added 5,068 feedback chars. A2 resent 12,543 system chars and 108,086 base user chars, then added 6,676 feedback chars.

The retry mechanism mostly teaches the model how to avoid another rejection. It says what failed and keeps the same contract, but it does not expose a compact accepted-answer shape for the remaining authority. A1 and B1 show that dropping declarations can pass. A2/A3 show that after repeated invalid attempts, deterministic fallback chooses safe observations/nonresolution rather than useful answer completion.

## I. Long-Session Growth Risks

Demonstrated growth between A1 and later calls comes from:

- conversation/session history and recent log growth;
- temporal authority buckets such as `player_hypotheses`, `rejected_consequential`, and active claim/discourse state;
- larger decision files/traces as prior claims and rejection history accumulate (`A1_decision_1.json` 9,856 bytes; `A3_decision_3.json` 16,530 bytes);
- selected conversational memory and contextual thread selection;
- world tick/clock/progression slices;
- repeated contract/policy mirrors inside nested metadata;
- retry feedback adding validation findings on top of the unchanged base payload.

The code supports monotonic risk through session logs, bounded improvisation ledger entries, rejected proposal buckets capped in some places, and temporal discourse/proposition state. The observed four turns are not enough to prove operational unsustainability alone, but the construction path is clearly sensitive to turn count because model-facing memory/context is derived from growing session and log structures.

## J. Candidate Implementation Slices

Ranked by Chapter II priorities.

| Rank | Slice | Deficiency addressed | Layer | Player-visible benefit | First-pass acceptance | Useful-response rate | Token/call effect | Risk | Testability | Micro-live later? |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Decision-facing answer recipe projection | Model sees authority but not the exact valid response shape. | `gm_resolution_decision` -> `prompt_context`/`gm.py` | More useful first answers, especially bounded inference/uncertainty. | High | High | Medium, can replace verbose duplicate guidance | Low-medium | Deterministic payload tests and validator acceptance fixtures | Yes |
| 2 | Retry "remaining authorized answer" compact feedback | Retry mainly says what not to do. | `immutable_valid_response` / `gm_retry` | Retries answer instead of collapsing to restatement. | None on first pass | High on retries | Medium; feedback can be smaller | Low | Deterministic retry prompt tests | Yes |
| 3 | Ordinary NPC speech declaration guidance | Schema encourages over-declaring mundane dialogue. | `gm.py` prompt/schema and bounded improvisation docs | Natural social answers without fact pollution. | Medium | Medium-high | Small | Low | B1-style fixtures | Possibly |
| 4 | Provider payload canonicalization inventory cleanup | Same contract/decision/policy appears multiple times. | `prompt_context`/payload projection | Lower latency/cost, less instruction dilution. | Medium | Medium | High | Medium | Deterministic payload size/snapshot tests | Yes |
| 5 | Debug-only provider-context scrub | Debug/emission metadata leaks into model payload. | `prompt_context`/state channels | Less clutter and cost. | Low-medium | Medium | Medium | Low-medium | Payload key denylist tests | Maybe |

## K. Recommended First Implementation Slice

Recommended first slice: **Decision-facing answer recipe projection**.

Create a compact, model-facing projection derived from `GMResolutionDecision` that says:

- what must/may be stated;
- what may be inferred, with explicit allowed modality;
- what must remain unresolved;
- what declaration mode/provenance/status/relation is valid;
- forbidden upgrades for the current turn;
- one terse natural-language answer shape.

For A1, the stopping condition should be deterministic before live validation: a fixture with the A1 contract/decision must produce a prompt projection that contains a bounded inference recipe and forbids cause/actor/time/history/lead establishment; validator fixtures should show an answer using that recipe passes without weakening rejection of the original overreach.

This slice improves both cooperation and cost if it replaces some duplicate guidance rather than adding yet another large block, but the quality improvement is the primary objective.

## L. Architecture Status

**A - PR-BR remains closed.**

Repository and live-trace evidence shows poor model cooperation, conservative retry behavior, and large duplicated prompt payloads. It does not show unauthorized consequential state creation, recursive authority laundering, provenance corruption, epistemic promotion into world truth, accepted/sealed/emitted divergence, ownership contradiction, or systemic bypass of the structured authority boundary.

## Handoff Contents

Supporting artifacts:

- `artifacts/pr_bs_cooperative_realization_discovery/context_inventory.json`
- `artifacts/pr_bs_cooperative_realization_discovery/call_chain_evidence.md`
- `handoff/payload_breakdown.json`
- `handoff/REVIEW_MANIFEST.json`
- selected PR-BR closeout evidence in `artifacts/pr_br_closeout_live_revalidation/`

