# PR-BT Provider Context Canonicalization Discovery

## A. Executive Finding

Successful ordinary turns still cost about 25k-28k provider input tokens because the current provider request ships a large fixed realization chassis on every turn. The dominant cost is not the player request, current scene, or world facts. In the saved PR-BS live requests, the player input is 53-129 chars, the scene is 1.6k-1.7k chars, and the compact decision-facing answer recipe is 1.7k-2.4k chars. By contrast, every turn carries:

| Component | P1 chars | P2 chars | P3 chars |
|---|---:|---:|---:|
| Provider request, serialized | 110,450 | 121,438 | 110,665 |
| Live input tokens | 25,208 | 27,795 | 25,233 |
| User payload JSON content | 91,859 | 102,010 | 92,100 |
| `instructions` | 25,788 | 26,675 | 25,856 |
| `response_policy` | 20,630 | 21,237 | 20,913 |
| `SYSTEM_PROMPT` | 12,975 | 12,975 | 12,975 |
| `turn_packet` | 10,676 | 10,640 | 10,910 |
| `narrative_plan` | 4,472 | 4,965 | 4,244 |
| `context_separation_contract` | 3,509 | 3,359 | 3,437 |

The immediate answer is: PR-BS improved first-pass cooperation by adding an operational recipe, but it did not collapse the older prompt stack. The model still receives system-level policy prose, a long instruction list, a machine-readable response policy, top-level mirrors of policy subcontracts, and a turn packet that embeds a second response-policy copy plus contract copies.

No new authority contradiction was found. This is efficiency and canonicalization work, not PR-BR reopening evidence.

## B. Current Payload Anatomy

Method: deterministic character counts using `json.dumps(..., ensure_ascii=False, default=str)` against saved PR-BS `provider_request_attempt_generation_1.json` files. Live token counts are copied from PR-BS recorded usage. No model/API calls were made.

| Major component | Source | P1 | P2 | P3 | Notes |
|---|---|---:|---:|---:|---|
| `SYSTEM_PROMPT` | `game/gm.py` | 12,975 | 12,975 | 12,975 | Fixed static GM role, rule priority, schema, visibility, Q/A, bounded improvisation. |
| `instructions` | `game/prompt_context.py` + `game/gm.py` additions | 25,788 | 26,675 | 25,856 | 107-111 prose instructions; many say “obey response_policy.X”. |
| `response_policy` | `game.prompt_context` policy projection | 20,630 | 21,237 | 20,913 | Machine-readable policy; largest children are context separation, answer completeness, interaction continuity, response delta, authenticity, tone, anti-railroading. |
| `turn_packet` | `game.turn_packet.build_turn_packet` | 10,676 | 10,640 | 10,910 | Contains `response_policy` copy around 6.0k, `contracts` around 3.7k-3.8k, debug. |
| `mechanical_resolution` | provider copy of resolution | 662 | 6,253 | 1,126 | P2 is large because social/dialogue resolution content is embedded. |
| `narrative_plan` | plan bundle prompt projection | 4,472 | 4,965 | 4,244 | Turn-specific structural guidance; duplicates some policy/mode instructions. |
| `context_separation_contract` | mirror of `response_policy.context_separation` | 3,509 | 3,359 | 3,437 | Top-level duplicate of largest response-policy child. |
| `decision_facing_answer_recipe` | PR-BS projection | 2,356 | 1,876 | 1,691 | Essential current-turn operational answer guidance. |
| `scene` | public scene projection | 1,731 | 1,630 | 1,705 | Relevant authored state; modest size. |
| `referent_tracking` | referent artifact | 1,250 | 3,005 | 1,250 | Bigger in NPC social turn. |
| `gm_resolution_decision` | compact provider projection | 1,073 | 1,184 | 1,073 | Canonical decision is runtime owner; provider projection overlaps recipe. |
| `character` + `campaign` | storage projection | 2,116 each turn | 2,116 | 2,116 | Mostly fixed/static for these probes. |
| `resolution_contract` | generation projection | 569 | 723 | 537 | Compact request contract. |
| `world` | compressed world | 349 | 349 | 349 | Not a dominant cost in these probes. |
| `session` | compressed session | 340 | 353 | 340 | Not a dominant cost in these probes. |
| `player_input` | current request | 69 | 53 | 129 | Tiny; repeated elsewhere. |

The inventory artifact `PR-BT_provider_payload_inventory.json` contains per-component rows and nested breakdowns for later before/after comparison.

## C. Context Classification

A — Essential model context: current player input, compact scene-visible facts, narration visibility, speaker selection, turn summary, compact resolution contract, Decision-Facing Answer Recipe, output schema requirements, bounded improvisation boundary, essential anti-leak/authority rules.

B — Conditionally relevant model context: NPC/social structures, dialogue social plan, active interlocutor, referent tracking, lead context, world/character/campaign, narrative plan, transition state, fallback behavior, response policy subsets such as tone or social response structure.

C — Canonical runtime / validator context: full `GMResolutionDecision`, full response policy object, turn packet, resolution metadata, temporal provenance, session state, validator-facing contracts, accepted-response metadata.

D — Debug / trace context: `turn_packet.debug`, prompt debug anchors, planner seam traces, provider mechanical-resolution debug residue, selection/debug fields in policy contracts.

E — Redundant model context: top-level `context_separation_contract` vs `response_policy.context_separation`; top-level contract mirrors vs response-policy children; `turn_packet.response_policy` vs top-level `response_policy`; `turn_packet.contracts` vs response-policy/top-level contract surfaces; instruction prose that repeats system prompt or policy-object semantics; player text repeated in `player_input`, `turn_packet.player_text`, recipe requested answer, and mechanical/turn summaries.

F — Legacy/stale context: broad static system and instruction rules that teach the model how the whole engine works rather than what it must do this turn; generic mechanics/inventory/update allowances present on non-mechanical ordinary inquiry turns.

G — Uncertain: narrative plan and referent tracking can be partly redundant, but removal risk depends on turn class. The correct next move is bounded slicing plus deterministic/later micro-live validation, not wholesale removal.

## D. Static/Growing Analysis

Fixed/static costs dominate current ordinary turns:

| Category | Representative components | Current cost |
|---|---|---:|
| Static or near-static | system prompt, much of instructions, schema prose, static rule priority, anti-railroading prose | about 38k-40k chars before policy object cost |
| Turn-specific | recipe, contract, decision projection, turn summary, player input, mechanical resolution | about 4k-11k chars depending on turn |
| Session-growing bounded | recent log, selected conversational memory, interaction continuity, lead context | currently empty in P1/P2/P3 for selected/recent; code caps recent log at 5 and selected memory at 12 |
| World-growing | world, world_state, temporal provenance, lead/world progression | tiny in these probes, but future systems can grow if serialized broadly |
| Retry-only | authoritative retry context | absent in all three PR-BS probes |

The fixed scaffold explains why P1 and P3 are almost identical size despite different player intent, and why P2 grows mainly from social/mechanical payload and referent tracking rather than conversation history.

## E. Duplication Map

| Semantic information | Canonical owner | Model-facing representations | Classification | Validator/tracing impact if removed from provider |
|---|---|---|---|---|
| Response policy | response-policy builders/runtime policy object | `response_policy`, many `instructions`, `SYSTEM_PROMPT`, `turn_packet.response_policy` | accidental duplication / projection candidate | Keep runtime object; validators unaffected if provider projection remains sufficient. |
| Context separation | `response_policy.context_separation` | response-policy child, top-level `context_separation_contract`, instructions, turn packet contracts | accidental duplication | Remove top-level mirror only after tests prove policy child is enough. |
| Anti-railroading | response policy + top-level contract | `anti_railroading_contract`, `response_policy.anti_railroading`, long instruction paragraph, system agency rule | necessary core but overrepresented | Validators unaffected; model still needs compact rule. |
| Turn packet contracts | `game.turn_packet` for gates/retries | top-level `turn_packet`, top-level policy/contracts | debug/runtime leakage plus duplication | Keep in runtime/traces; provider likely needs only tiny selected fields. |
| Decision authority | `GMResolutionDecision` | `gm_resolution_decision`, `decision_facing_answer_recipe`, realization claims, resolution contract | necessary redundancy now / projection candidate | Do not remove decision projection until recipe-only live validation exists. |
| Player request | current user text | `player_input`, recipe requested answer, turn packet player_text, turn summary/mechanical text | minor duplication | Low savings; keep exact text somewhere. |
| Conversation history | memory selector | `selected_conversational_memory`, legacy `recent_log`, policy window object | projection candidate | Keep selector/runtime evidence; provider should receive one selected history surface. |
| Debug metadata | turn packet/debug, prompt debug anchors | embedded in turn packet/policies/mechanical resolution | debug-only leakage | Keep in traces, omit from provider once denylist is tested. |

## F. System Prompt Audit

System prompt sections:

| Section | Purpose | Size/risk |
|---|---|---|
| GM identity + rule priority | Establish role and priority order | Useful but duplicated by response-policy priority/instructions. Can compact with medium risk. |
| Always answer / no validator voice | Operational behavior | Essential, but repeated in instructions and response policy. |
| App owns mechanics/persistence | Authority boundary | Essential concept; can be shorter because recipe/decision now provides turn-local authority. |
| Player expression/action declaration | Preserve player phrasing | Useful, but conditional; not always needed in same detail. |
| Scene momentum / question resolution / NPC response | Behavioral quality rules | Useful but duplicated by response policy and instructions; social/NPC portions should be conditional. |
| Perception/intent adjudication | Specific rule for behavioral insight | Conditional; should not cost every non-perception turn. |
| Visibility layers | Anti-leak boundary | Essential, but top-level `narration_visibility` makes details projectable. |
| Resolved exploration action | Mechanics/result narration | Conditional. |
| Full JSON schema | Output contract | Essential unless provider API supports separate structured schema; still large fixed cost. |
| Bounded improvisation authority | Authority boundary | Essential but can be compacted because `declared_claims`/validators enforce semantics. |

The prompt still explains architecture (“application owns mechanics and persistence”, update objects, auto-apply) when the model may only need a shorter operational rule: narrate only within supplied decision/visibility; declare consequential claims through the schema.

## G. Response Policy Audit

The response policy contributes important validator-aligned machine-readable rules, but much of it is also restated in prose. Largest children:

| Child | P1 | P2 | P3 | Note |
|---|---:|---:|---:|---|
| `context_separation` | 3,509 | 3,359 | 3,437 | Also top-level mirror. |
| `answer_completeness` | 2,079 | 2,257 | 2,369 | Usually relevant for questions. |
| `interaction_continuity` | 1,805 | 2,157 | 1,808 | Conditional; social turns need more. |
| `response_delta` | 1,762 | 1,721 | 1,724 | Often inert unless follow-up pressure is active. |
| `narrative_authenticity` | 1,608 | 1,629 | 1,608 | Quality rule, partly static. |
| `tone_escalation` | 1,477 | 1,462 | 1,422 | Conditional outside social/high-tension turns. |
| `anti_railroading` | 1,451 | 1,451 | 1,451 | Static policy duplicated elsewhere. |
| `fallback_behavior` | 1,315 | 1,403 | 1,482 | Conditional on uncertainty/fallback. |

Policy necessary for correct behavior: answer completeness, narrative authority, visibility, anti-railroading, no validator voice, relevant social/tone/fallback constraints.

Policy likely present because the model historically reconstructed the authority system itself: large descriptive policy objects plus matching explanatory instruction paragraphs plus system prose. PR-BS recipe reduces this need for ordinary authority-safe answers.

## H. Turn Packet Audit

`game/turn_packet.py` explicitly says the turn packet is a separate compact artifact for contracts, route hints, continuity snapshots, debug metadata, gates, retries, and diagnostics, and not authoritative engine state. Current provider copies are still large:

| Turn packet child | P1 | P2 | P3 |
|---|---:|---:|---:|
| `response_policy` | 6,022 | 6,012 | 6,083 |
| `contracts` | 3,753 | 3,741 | 3,814 |
| `debug` | 287 | 287 | 348 |
| compact referent/route/player fields | <400 combined | <400 | <400 |

This is the clearest runtime/debug object leaking into the provider. The model may need selected route and contract facts, but not a second policy object, duplicate contract subtree, or debug. Validators/gates can keep the full packet outside the provider request.

## I. Conversation-History Audit

Conversation history reaches the model through `selected_conversational_memory` and legacy `recent_log`, with a `conversational_memory_window` policy object also shipped and mirrored into `response_policy`. Current behavior in `game/prompt_context.py` and `game/conversational_memory_window.py`:

- `MAX_RECENT_LOG = 5`.
- `MAX_LOG_ENTRY_SNIPPET = 200`.
- `CONVERSATIONAL_MEMORY_SOFT_LIMIT = 12`.
- `CONVERSATIONAL_MEMORY_MAX_CANDIDATES = 36`.
- selector contract uses `recent_turn_window=6`, `soft_memory_limit=12`, `stale_after_turns=18`.
- older material is relevance-selected and stale-deprioritized unless reintroduced.

Measured P1/P2/P3 have empty selected memory/recent log because each probe is isolated. Deterministic growth is therefore bounded by caps, not unbounded raw transcript serialization.

Estimated provider growth from the current code path, assuming selected recent turns have typical snippets near the 200-char GM cap plus player text and JSON overhead:

| Turn | Current history contribution | Notes |
|---:|---:|---|
| 1 | 0 | measured probes empty |
| 10 | roughly 2k-7k chars | up to 5 recent-log rows plus up to 12 selected memory items, depending overlap |
| 25 | roughly 2k-7k chars | bounded; stale items excluded unless re-grounded |
| 50 | roughly 2k-7k chars | bounded if selector remains sole history path |
| 100 | roughly 2k-7k chars | bounded; risk shifts to world/temporal state, not raw chat |

History duplicates authoritative state when accepted narration is also preserved as scene/world/temporal facts. The selector helps, but the provider should avoid shipping both `recent_log` and `selected_conversational_memory` once non-empty.

## J. World / Temporal-State Audit

Measured world/session state is small in the PR-BS probes: `world` is 349 chars; `session` is 340-353; `world_state` is tiny/empty; temporal provenance does not appear as a large provider component here. Consequential truth the model needed was mostly in `scene`, `resolution_contract`, `gm_resolution_decision`, and the answer recipe.

Validators and runtime still need richer provenance: gm inferences, player hypotheses, accepted incidentals, rejected consequential rows, discourse focus, turn counter, accepted-response metadata. The model only needs the turn-relevant slice: current visible observations, relevant prior unresolved hypothesis/inference, involved NPC/location facts, and exact answer boundary.

Current context selection partially answers this for conversational memory, but not as a general provider-boundary rule for future world/temporal systems. The responsible layer is `prompt_context` projection: it should remain the single model-facing selection/projection boundary rather than serializing every runtime object.

## K. Debug-Metadata Audit

Provider-facing information with debug/runtime-only value:

- `turn_packet.debug` and missing-contract/source diagnostics.
- `planner_seam_trace` inside response policy.
- selection debug fields in conversational memory window.
- prompt debug anchors that are useful for audits but not generation.
- provider mechanical-resolution debug residue, especially when a turn carries large social/mechanical structures.
- repeated IDs/derivation codes where no instruction depends on the exact identifier.

This material can remain in traces/runtime objects and be excluded from provider requests. Deterministic denylist tests should prove validators still receive canonical objects.

## L. Schema Overhead

Meaningful overhead is not short field names; it is repeated full structures and repeated prose. The largest serialization overheads are:

- `turn_packet.response_policy` duplicates about 6k chars every turn.
- `turn_packet.contracts` duplicates about 3.7k-3.8k chars every turn.
- top-level contract mirrors duplicate response-policy children, with `context_separation_contract` alone about 3.4k chars.
- instruction list repeats policy semantics in 25.8k-26.7k chars.
- system prompt repeats many of the same rules in 13k chars.
- optional/inert policy fields are serialized even when not active.

Do not optimize field names. Remove or project duplicate structures first.

## M. Minimum-Sufficient-Context Design

Proposed provider request shape:

```text
compact stable GM operating rules and JSON schema
+ current player request
+ selected current-turn authoritative facts:
  scene-visible facts, involved speaker/NPC, relevant prior claim/hypothesis if any
+ compact resolution contract
+ Decision-Facing Answer Recipe
+ minimal model-facing response policy projection:
  only active answer/visibility/authority/social/tone/fallback rules for this turn
+ selected conversational memory OR recent_log, not both
+ compact output/schema contract
```

Excluded from the minimum provider context:

| Excluded/reduced | Why model does not need full copy | Canonical owner remains | Risk |
|---|---|---|---|
| full `turn_packet` | gate/retry/diagnostic object; duplicates policy/contracts | `game.turn_packet`, gm metadata/traces | low-medium; keep route fields if useful |
| full response-policy mirror in packet | already top-level | response policy runtime object | low if top-level retained |
| top-level duplicated policy contracts | response-policy child is canonical provider surface | response-policy builders | low-medium |
| debug/seam traces | diagnostics only | traces/artifacts | low |
| broad static instruction prose | repeats system/policy/recipe | prompt constants/tests | medium; micro-live needed |
| full world/campaign when irrelevant | current turn only needs selected facts | storage/runtime | medium for future complex turns |
| both `recent_log` and `selected_conversational_memory` | same conversational need | memory selector | low-medium |

## N. Conditional-Context Design

Conditional injection should be explicit by turn class:

- Combat mechanics only when combat route/resolution exists.
- Inventory/character details only for equipment, skill, health, spell, or stat interactions.
- NPC profile/social response structure only when a specific NPC is involved.
- Tone escalation only for social/conflict/hostile contexts.
- Geography/transition details only for travel or location change.
- Temporal provenance only when the turn references a prior hypothesis, inference, rejected claim, accepted incidental, or active discourse focus.
- Narrative plan facets only when their mode-specific signals are active and not already represented by answer recipe/visibility/speaker selection.

This keeps future Chapter II systems from becoming default prompt ballast.

## O. Long-Session Projection

Measured/deterministic/extrapolated split:

| Turn | Current design estimate | Basis | Proposed minimum estimate |
|---:|---:|---|---:|
| 1 | 110k-121k chars | measured P1/P2/P3 | about 45k-65k chars before live validation |
| 10 | 112k-128k chars | measured fixed stack + bounded history estimate | about 48k-72k |
| 25 | 112k-128k chars plus accumulated world/temporal if serialized | history bounded; world risk extrapolated | about 48k-75k with relevance selection |
| 50 | 112k-135k+ | fixed stack + future world/temporal growth | about 50k-80k if state remains selected |
| 100 | 112k-150k+ | unsustainable if future systems serialize broadly | about 50k-90k with strict conditional injection |

If nothing changes after PR-BS, long play becomes unsustainable from fixed per-turn overhead plus additive future systems. Raw conversation history is not currently the dominant threat because it is capped. The threat is a provider boundary pattern that turns each new runtime system into always-on model context.

## P. Candidate Implementation Slices

Ranked candidates:

| Rank | Slice | Savings | Fixed/growing | Complexity | AI risk | Arch risk | Testability | Micro-live need |
|---:|---|---:|---|---|---|---|---|---|
| 1 | Policy/instruction deduplication | 12k-25k chars | fixed | medium | low-medium | low | high snapshot tests | yes |
| 2 | Turn-packet provider projection | 8k-10k chars | fixed per turn | low-medium | low-medium | low | high denylist/snapshot tests | maybe/yes |
| 3 | Response-policy compact projection | 6k-12k chars | fixed/turn-specific | medium | medium | medium | medium-high | yes |
| 4 | History surface canonicalization | 1k-7k chars once history exists | bounded growing | low-medium | low | low | high | maybe |
| 5 | Debug-metadata scrub | 0.5k-2k chars now, more later | fixed/conditional | low | low | low | high | maybe not |

## Q. Recommended PR-BT Implementation Slice

Decision: implement policy/instruction deduplication first, scoped to provider-facing prose that already points at shipped machine-readable policy objects.

Exact scope:

- Keep `decision_facing_answer_recipe`, compact `resolution_contract`, compact `gm_resolution_decision`, visibility, speaker selection, and schema intact.
- Replace repeated “POLICY: obey response_policy.X” paragraphs in `instructions` with a compact policy index and only the active turn deltas.
- Remove or shorten instruction prose where the exact policy object remains in `response_policy` and validators use runtime state.
- Do not alter validators, authority ownership, retry, accepted-response boundary, or C18.

Expected savings: initial deterministic target 12k-18k chars per ordinary turn, with a stretch target near 25k if system/instruction overlap is also compacted safely. This is about 11%-22% of current PR-BS provider chars before tackling `turn_packet`.

Quality risk: low-medium. The model may still need some natural-language framing around compact policy objects. Preserve the highest-risk operational rules in compact prose.

Architectural risk: low. Canonical runtime owners do not change.

Deterministic validation:

- Snapshot P1/P2/P3 provider payload sizes.
- Assert essential keys still present: recipe, resolution contract, decision projection, visibility, output schema, player input.
- Assert removed instruction classes are still represented by retained policy objects.
- Assert validators still receive canonical runtime objects.
- Assert no retry/C18/accepted-response code path changes.

Eventual micro-live validation: rerun the three PR-BS probes plus one social follow-up and one bounded inference/hypothesis probe. Stop if first-pass acceptance falls below PR-BS baseline or authority/C18 integrity fails.

Stopping condition: one bounded reduction with measured savings and no deterministic contract regression; do not keep shaving prose in the same PR.

## R. Architecture Status

A — PR-BR REMAINS CLOSED.

I found inefficient and duplicated provider context, not evidence of authority/provenance/state-integrity contradiction. PR-BR authority boundaries remain valid: authoritative state ownership, `GMResolutionDecision`, `RealizationClaim` authority, provenance, epistemic ceilings, bounded incidental improvisation, structured declaration validation, immutable accepted response, and C18 exactness are preserved.

Decision taxonomy: A — CANONICALIZATION SLICE READY.

Evidence identifies one bounded high-value context reduction that can be implemented safely: provider-facing policy/instruction deduplication, with deterministic payload snapshots and later micro-live validation.
