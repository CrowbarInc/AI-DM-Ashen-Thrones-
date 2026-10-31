from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import subprocess
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_cs_context_efficiency"

REQUESTS = [
    {
        "id": "A_PR_CQ_harmless_NPC_preference",
        "source": "exact captured payload",
        "path": ROOT / "artifacts/pr_cq_live_finalization/evidence/T1/provider_request_generation_1.json",
        "historical_input_tokens": 30877,
        "turn_class": "harmless NPC preference",
    },
    {
        "id": "B_PR_CQ_authored_patrol_question_initial",
        "source": "exact captured payload",
        "path": ROOT / "artifacts/pr_cq_live_finalization/evidence/T2/provider_request_generation_1.json",
        "historical_input_tokens": 34561,
        "turn_class": "authored NPC fact question",
    },
    {
        "id": "B2_PR_CQ_authored_patrol_question_regeneration",
        "source": "exact captured payload, retry eliminated by PR-CR under equivalent eligible conditions",
        "path": ROOT / "artifacts/pr_cq_live_finalization/evidence/T2/provider_request_generation_2.json",
        "historical_input_tokens": 42960,
        "turn_class": "authored NPC fact question retry",
    },
    {
        "id": "C_PR_CO_notice_board_examination",
        "source": "exact captured payload",
        "path": ROOT / "artifacts/pr_co_gameplay_viability/evidence/T1/provider_request_generation_1.json",
        "historical_input_tokens": 30970,
        "turn_class": "notice-board examination",
    },
    {
        "id": "D_PR_CO_ordinary_observation",
        "source": "exact captured payload",
        "path": ROOT / "artifacts/pr_co_gameplay_viability/evidence/T2/provider_request_generation_1.json",
        "historical_input_tokens": 29914,
        "turn_class": "ordinary observation",
    },
    {
        "id": "E_PR_CO_natural_language_exploration",
        "source": "exact captured payload",
        "path": ROOT / "artifacts/pr_co_gameplay_viability/evidence/T3/provider_request_generation_1.json",
        "historical_input_tokens": 35302,
        "turn_class": "natural-language exploration",
    },
]

CATEGORY_ORDER = [
    "System instructions",
    "Developer instructions",
    "Authority policies",
    "Narration policies",
    "Resolver-specific instructions",
    "Mechanical resolution data",
    "World and scenario state",
    "NPC information",
    "Scene information",
    "Conversation history",
    "Validation/retry feedback",
    "Output schema and formatting instructions",
    "Other material",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def rough_tokens(text: str) -> int:
    # GPT-4.1 tokenization is not available locally in this repo. This is a conservative
    # attribution estimate; historical totals use provider-reported usage.
    return max(1, math.ceil(len(text) / 4))


def role_contents(request: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    system = ""
    user = ""
    payload: dict[str, Any] = {}
    parsed_user_index: int | None = None
    user_messages: list[str] = []
    for msg in request.get("provider_input") or []:
        if msg.get("role") == "system":
            system += str(msg.get("content") or "")
        elif msg.get("role") == "user":
            user_messages.append(str(msg.get("content") or ""))
    user = "\n".join(user_messages)
    for idx, content in enumerate(user_messages):
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            payload = parsed
            parsed_user_index = idx
            break
    if parsed_user_index is not None:
        retry_feedback = "\n".join(
            msg for idx, msg in enumerate(user_messages) if idx != parsed_user_index
        ).strip()
        if retry_feedback:
            payload["__retry_feedback__"] = retry_feedback
    return system, user, payload


def classify_top_key(key: str, value: Any, system: str = "") -> str:
    k = key.lower()
    if key == "__system__":
        if "NARRATION-ONLY RESPONSE CONTRACT" in system or "Return valid JSON only" in system:
            return "System instructions"
        return "System instructions"
    if key == "__developer__":
        return "Developer instructions"
    if k in {
        "response_policy",
        "narrative_authority",
        "narration_visibility",
        "bounded_improvisation",
        "layering_rules",
        "speaker_selection",
        "scene_state_anchor_contract",
        "context_separation_contract",
    }:
        return "Authority policies"
    if k in {
        "instructions",
        "narration_obligations",
        "player_expression_contract",
        "narrative_plan",
        "narrative_roles",
        "referent_tracking",
        "referent_clause_prompt_hints",
        "active_interlocutor",
        "dialogue_social_plan",
        "decision_facing_answer_recipe",
    }:
        if key == "instructions":
            return "Narration policies"
        return "Narration policies" if "narrative" in k or "narration" in k or "dialogue" in k else "Resolver-specific instructions"
    if k in {
        "resolution_contract",
        "gm_resolution_decision",
        "mechanical_resolution",
        "resolved_exploration_action",
        "resolved_combat_action",
        "skill_check",
        "response_type_contract",
        "turn_summary",
        "intent",
        "clues",
        "known_answer_hint",
        "passive_scene_pressure",
    }:
        return "Mechanical resolution data"
    if k in {
        "campaign",
        "world",
        "world_progression",
        "lead_context",
        "follow_up_pressure",
        "planner_head_state",
    }:
        return "World and scenario state"
    if "npc" in k or "interlocutor" in k or k in {"knowledge_scope", "social_interlocutor_profile"}:
        return "NPC information"
    if k in {
        "scene",
        "public_scene",
        "originating_scene_id",
        "scene_transition_already_occurred",
        "scene_runtime",
        "current_scene",
    } or "scene" in k:
        return "Scene information"
    if k in {"recent_log", "selected_conversational_memory", "conversational_memory_window"}:
        return "Conversation history"
    if "retry" in k or "validation" in k or "failure" in k:
        return "Validation/retry feedback"
    if k in {"schema", "format", "provider_response_contract"}:
        return "Output schema and formatting instructions"
    return "Other material"


def repeated_instruction_stats(payload: dict[str, Any], system: str) -> dict[str, Any]:
    instructions = [str(x) for x in payload.get("instructions") or [] if isinstance(x, str)]
    repeated_in_payload = [text for text, n in Counter(instructions).items() if n > 1]
    semantic = []
    for text in instructions:
        if text and text in system:
            semantic.append(text[:220])
    return {
        "instruction_count": len(instructions),
        "exact_instruction_duplicates": len(repeated_in_payload),
        "instructions_repeated_in_system": len(semantic),
        "examples_repeated_in_system": semantic[:8],
    }


def source_for_category(category: str) -> str:
    return {
        "System instructions": "game/gm.py::_SYSTEM_PROMPT_HEADER, NARRATION_ONLY_SYSTEM_PROMPT/SYSTEM_PROMPT",
        "Developer instructions": "none in captured provider_input; app packs policy into system/user messages",
        "Authority policies": "game/prompt_context.py::build_narration_context and policy builders",
        "Narration policies": "game/prompt_context.py plus game/narration_plan_bundle.py projections",
        "Resolver-specific instructions": "game/gm.py::build_messages overlays, CTIR/narration plan projections",
        "Mechanical resolution data": "game/gm_resolution_decision.py, game/resolution_contract.py, game/ctir_runtime.py projections",
        "World and scenario state": "game/prompt_context.py, game/world_progression.py, game/leads.py",
        "NPC information": "game/prompt_context.py, game/interaction_context.py, game/social.py",
        "Scene information": "game/prompt_context.py, data/scenes/*.json projections",
        "Conversation history": "game/conversational_memory_window.py, game/planner_ctir_projection.py::_compress_recent_log",
        "Validation/retry feedback": "game/gm_retry.py and retry payload overlays",
        "Output schema and formatting instructions": "game/gm.py::SYSTEM_PROMPT/NARRATION_ONLY_RESPONSE_CONTRACT",
        "Other material": "mixed payload keys",
    }.get(category, "")


def mandatory_for(category: str) -> str:
    return {
        "System instructions": "mandatory but oversized/duplicated",
        "Developer instructions": "not present",
        "Authority policies": "mandatory in compact form",
        "Narration policies": "mandatory in resolver-specific form",
        "Resolver-specific instructions": "mandatory when applicable",
        "Mechanical resolution data": "mandatory for resolved/consequential turns; over-projected for simple social",
        "World and scenario state": "conditional; current prompt sends broad slice",
        "NPC information": "conditional; active speaker required, unrelated NPCs usually not",
        "Scene information": "mandatory current scene slice; duplicate seed/visible/journal facts are reducible",
        "Conversation history": "conditional bounded window",
        "Validation/retry feedback": "only retry attempts",
        "Output schema and formatting instructions": "mandatory but can be compact",
        "Other material": "case by case",
    }[category]


def payload_evidence() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    dup_examples: dict[str, Any] = {}
    for spec in REQUESTS:
        req = read_json(spec["path"])
        system, user, payload = role_contents(req)
        cat_text: dict[str, str] = defaultdict(str)
        cat_text["System instructions"] += system
        for k, v in payload.items():
            cat_text[classify_top_key(k, v, system)] += f"\n{k}: {stable_json(v)}"
        total_est = sum(rough_tokens(text) for text in cat_text.values())
        dup = repeated_instruction_stats(payload, system)
        dup_examples[spec["id"]] = dup
        top_keys = sorted(
            [(k, rough_tokens(stable_json(v))) for k, v in payload.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:12]
        summaries.append(
            {
                **spec,
                "model": req.get("model"),
                "provider_input_messages": len(req.get("provider_input") or []),
                "system_est_tokens": rough_tokens(system),
                "user_est_tokens": rough_tokens(user),
                "attribution_est_tokens": total_est,
                "top_keys": top_keys,
                "dup": dup,
            }
        )
        for category in CATEGORY_ORDER:
            est = rough_tokens(cat_text.get(category, ""))
            pct = (est / total_est * 100) if total_est else 0.0
            rows.append(
                {
                    "request_id": spec["id"],
                    "turn_class": spec["turn_class"],
                    "source_kind": spec["source"],
                    "historical_input_tokens": spec["historical_input_tokens"],
                    "category": category,
                    "estimated_tokens": est,
                    "estimated_pct": f"{pct:.1f}",
                    "source_module": source_for_category(category),
                    "construction_function": construction_for(category),
                    "mandatory": mandatory_for(category),
                    "duplicated_elsewhere": duplicated_for(category, dup),
                    "measurement_note": "Category count is local chars/4 estimate; historical_input_tokens is exact API usage.",
                }
            )
    return rows, summaries, dup_examples


def construction_for(category: str) -> str:
    return {
        "System instructions": "build_messages chooses NARRATION_ONLY_SYSTEM_PROMPT or SYSTEM_PROMPT",
        "Developer instructions": "not emitted as separate role",
        "Authority policies": "build_narration_context",
        "Narration policies": "build_narration_context + build_messages appended instructions",
        "Resolver-specific instructions": "collect_narration_context_call_kwargs/build_narration_context/build_messages",
        "Mechanical resolution data": "CTIR/resolution contract/gm_resolution_decision prompt projection",
        "World and scenario state": "prompt_context world/lead/progression projection",
        "NPC information": "active_interlocutor/speaker_selection/social profile projections",
        "Scene information": "public_scene/narration_visibility/scene anchor projections",
        "Conversation history": "select_conversational_memory_window/_compress_recent_log",
        "Validation/retry feedback": "build_retry_prompt_for_failure when retrying",
        "Output schema and formatting instructions": "system prompt contract selection",
        "Other material": "miscellaneous payload assembly",
    }[category]


def duplicated_for(category: str, dup: dict[str, Any]) -> str:
    if category in {"System instructions", "Narration policies", "Authority policies"}:
        return f"yes; {dup['instructions_repeated_in_system']} payload instructions are also present in system prompt"
    if category in {"Scene information", "Mechanical resolution data"}:
        return "yes; same authored facts often appear in visible/opening/journal facts and decision required_content"
    if category == "Output schema and formatting instructions":
        return "partly; response contract appears in system and provider-side validation expectations"
    return "not materially observed or conditional"


def write(path: str, text: str) -> None:
    (OUT / path).write_text(text.strip() + "\n", encoding="utf-8")


def git_text(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace")
    except Exception as exc:
        return f"<unavailable: {exc}>"


def write_artifacts() -> None:
    rows, summaries, dup_examples = payload_evidence()
    with (OUT / "PR-CS_token_accounting.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    evidence_manifest = []
    for spec in REQUESTS:
        data = spec["path"].read_bytes()
        evidence_manifest.append(
            {
                "request_id": spec["id"],
                "turn_class": spec["turn_class"],
                "source_kind": spec["source"],
                "repo_relative_path": spec["path"].relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "historical_input_tokens": spec["historical_input_tokens"],
            }
        )
    (OUT / "PR-CS_payload_evidence_manifest.json").write_text(
        json.dumps(evidence_manifest, indent=2), encoding="utf-8"
    )

    top_lines = []
    for s in summaries:
        top = ", ".join(f"{k}~{v}" for k, v in s["top_keys"][:8])
        top_lines.append(
            f"| {s['id']} | {s['historical_input_tokens']} | {s['system_est_tokens']} | {s['user_est_tokens']} | {top} |"
        )

    safety = f"""# PR-CS Audit Report

## Phase 0 Worktree Safety

- git HEAD: `{git_text(['rev-parse', 'HEAD']).strip()}`
- git status: preserved dirty worktree; see `changed_files.txt` for the full pre/post relevant status.
- model configuration: `.env.example` declares `DEFAULT_MODEL_NAME=gpt-4o-mini`, `HIGH_PRECISION_MODEL_NAME=gpt-4.1-mini`, `RETRY_ESCALATION_MODEL_NAME=gpt-4.1-mini`, `ENABLE_MODEL_ROUTING=true`.
- captured provider model for audited gameplay generation: `gpt-4.1-mini`; historical completions report `gpt-4.1-mini-2025-04-14`.
- provider configuration: OpenAI Responses API via repo code; no live provider calls in PR-CS.
- tokenizer: exact GPT-4.1 tokenizer is not vendored in the repo and `tiktoken` is not declared in `requirements.txt`. Historical request totals use exact provider usage. Category attribution uses clearly labeled local `ceil(chars/4)` estimates, not invented exact tokenization.

## Phase 1 Payload Evidence

| Request | Exact API input tokens | Est. system tokens | Est. user payload tokens | Largest top-level payload keys by estimate |
|---|---:|---:|---:|---|
{chr(10).join(top_lines)}

The five required representative requests are exact captured payloads, not reconstructions. The PR-CQ retry payload is included as separate evidence because PR-CR eliminates it under equivalent eligible conditions; it is not counted as required initial prompt size.

## Core Finding

Ordinary gameplay reaches roughly 31k-35k input tokens because every generation request receives a broad all-purpose narration payload. The largest contributors are not conversation history; they are duplicated policy/instruction text, full mechanical/authority projections, repeated authored scene facts across multiple projections, and broad world/lead/NPC scaffolding that is often irrelevant to the current resolver.

## Decision

PR-CS decision: **A - CLEAR LOW-RISK OPTIMIZATION PATH**.

Substantial unnecessary context is supported by exact captured payloads. The lowest-risk first move is deduplication and resolver-specific projection, while retaining deterministic state, validators, CTIR, finalization, and persistence outside the provider prompt.
"""
    write("PR-CS_audit_report.md", safety)

    write(
        "PR-CS_context_category_breakdown.md",
        """# PR-CS Context Category Breakdown

See `PR-CS_token_accounting.csv` for per-request estimates. Across exact captured initial generation requests, the main categories are:

- System instructions: mandatory, but repeated by payload instructions; narration-only requests still carry a large universal rule hierarchy.
- Narration and authority policies: mandatory in principle, but currently sent as a broad aggregate instead of resolver-specific compact rules.
- Mechanical resolution data: mandatory for consequential/action turns, oversized for harmless subjective dialogue because full `gm_resolution_decision.realization_claims` and `decision_facing_answer_recipe.required_content` duplicate scene facts.
- Scene/world state: current scene is required, but visible/opening/journal seed facts and lead/world pressure slices repeat semantically.
- Conversation history: bounded and comparatively small in early turns; not the primary cause of 31k-35k prompts.
- Retry feedback: absent on initial requests; large only on regeneration. PR-CR removes the eligible authored retry path.
""",
    )

    graph = """# PR-CS Prompt Construction Graph

```text
HTTP turn / probe
  -> game.api turn orchestration
    -> deterministic resolver / CTIR attachment
      -> resolution_contract
      -> gm_resolution_decision
      -> response_type_contract
      -> narration_plan_bundle
    -> game.gm.collect_narration_context_call_kwargs
    -> game.gm.build_messages
      -> game.prompt_context.build_narration_context
        -> response_policy builders
        -> narration_visibility builder
        -> narrative_authority builder
        -> scene_state_anchor builder
        -> context_separation / anti_railroading / purity / authenticity contracts
        -> conversational_memory_window selector
        -> world_progression and lead projections
        -> speaker_selection / dialogue_social_plan / NPC knowledge gates
        -> public_narrative_plan_projection_for_prompt
      -> social-authority dialogue plan key pruning
      -> passive / known-answer / exploration / combat overlays
      -> provider contract selection
      -> system prompt selection
      -> provider_input = [system, user JSON payload]
    -> OpenAI Responses API call
    -> hard parse / validation / retry gate
    -> immutable valid response finalizer
```

Duplication enters through independent paths: `SYSTEM_PROMPT`/`NARRATION_ONLY_SYSTEM_PROMPT`, `payload.instructions`, `response_policy`, `narration_visibility`, `gm_resolution_decision.realization_claims`, `decision_facing_answer_recipe.required_content`, and scene seed/visible/journal fact projections.

Intentional redundancy protects authority and diegetic voice. Accidental duplication is visible where identical or near-identical scene facts and rule prose are repeated three or more times in the same user payload.
"""
    write("PR-CS_prompt_construction_graph.md", graph)

    matrix = """# PR-CS Resolver Context Matrix

| Resolver class | Minimum authoritative state | Minimum world/NPC/scene context | Unnecessary material observed in broad prompt |
|---|---|---|---|
| Harmless NPC preference | Active speaker, availability, subjective-reply permission, no durable-fact boundary | Active NPC label, visible scene anchor, current player question | Full scene fact duplication, broad leads/faction pressure, unrelated NPC existence, action/exploration rules |
| Authored NPC fact question | Active speaker, knowledge scope, authored answer/known-answer projection, refusal limits | Relevant lead/topic and NPC knowledge boundary | Full action schema, unrelated scene facts, broad policy prose repeated in system and instructions |
| Observation | Visibility contract, scene facts, discoverable hinting permission, response type | Current scene and visible entities/facts | Social-specific dialogue plan rules, unrelated NPC knowledge gates, inactive combat/action rules |
| Exploration | Resolution/action contract, scene transition flag, visible/discoverable facts, outcome authority | Current scene plus target/action slice | Unrelated NPC dialogue rules, inactive social detail, full lead registry when action-local |
| Passive waiting | Passive streak, time pressure, visible scene pressure | Current scene and pending lead pressure only if due | Full mechanical/action schemas and unrelated NPC knowledge |
| Physical world action | CTIR/resolution, skill/combat/action outcome, visible target | Action target, outcome, state mutations allowed/blocked | Subjective dialogue policy, broad social answer rules |
| Consequential social interaction | Speaker, social plan, knowledge scope, check/result if any, authority ceilings | Active NPC and relevant relationship/topic/lead | Unrelated location/NPC/world mechanics, inactive exploration schemas |
| Combat | Combat state, actors, initiative/action result, mechanical outcome | Combat participants, terrain/visible facts, result | Social/lead dialogue scaffolding, noncombat exploration prose policies |
"""
    write("PR-CS_resolver_context_matrix.md", matrix)

    sep = """# PR-CS Authority / Generation Separation

The deterministic resolver, hard validator, immutable finalizer, state persistence, and subsequent-turn continuity all require rich authority state. The provider does not require all of that state in full.

Material needed by deterministic pipeline but over-sent to provider:

- Full realization claim arrays with source refs, semantic identity, persistence, relation kind, and premise IDs for simple narration-only social turns.
- Multiple copies of authored scene facts through visible facts, opening seed facts, journal seed facts, `gm_resolution_decision.realization_claims`, and recipe `required_content`.
- Full policy object shapes when the provider only needs compact behavioral obligations for the selected response type.
- Broad lead/world pressure booleans when the turn is a local harmless exchange.

Safe separation principle: keep complete CTIR, resolver, validator, and persistence data in app memory and logs; send a compact provider-facing projection that contains only the claims, constraints, and output contract needed to realize this turn. Authority must remain app-owned.
"""
    write("PR-CS_authority_generation_separation.md", sep)

    dup_lines = ["# PR-CS Duplication Inventory", ""]
    for req_id, dup in dup_examples.items():
        dup_lines.append(f"## {req_id}")
        dup_lines.append(f"- payload instruction count: {dup['instruction_count']}")
        dup_lines.append(f"- exact duplicate instructions inside payload: {dup['exact_instruction_duplicates']}")
        dup_lines.append(f"- payload instructions also present in system prompt: {dup['instructions_repeated_in_system']}")
        for ex in dup["examples_repeated_in_system"][:4]:
            dup_lines.append(f"- repeated example: `{ex}`")
        dup_lines.append("")
    dup_lines.append("High-volume semantic duplication also appears in authored scene facts copied through scene visible facts, opening seed facts, journal seed facts, realization claims, and answer recipe required content.")
    write("PR-CS_duplication_inventory.md", "\n".join(dup_lines))

    relevance = """# PR-CS Context Relevance Audit

| Request | Required | Conditionally required | Redundant | Irrelevant or likely unnecessary | Uncertain |
|---|---|---|---|---|---|
| PR-CQ harmless NPC preference | active Guard Captain, subjective reply permission, speaker selection, no durable fact boundary, current scene anchor | one visible rain/gate fact for grounding | repeated no-validator/answer-first policy; repeated scene facts in claims and recipe | missing-patrol/notice-board/full faction pressure for a rain preference | exact minimal NPC mannerism policy size |
| PR-CQ patrol question | active Guard Captain, authored answer/knowledge boundary, missing patrol topic, speaker selection | relevant lead rows and visible notice board | repeated scene facts and policy prose | unrelated tavern runner/townhouse/ragged stranger for direct patrol question | how much lead context improves answer usefulness |
| PR-CO notice-board examination | notice board visible fact, investigation/observation contract, discoverable hinting boundary | current scene pressure and relevant lead rows | generic answer/social policy; repeated scene seed facts | subjective NPC dialogue rules and unrelated NPC knowledge | whether full world pressure helps tone |
| PR-CO ordinary observation | visible scene facts and observation response type | scene momentum/pressure if due | full realization claim detail duplicated from scene facts | social answer scaffolding, combat/action schemas | lead reminders may be useful depending player intent |
| PR-CO exploration | resolved action/transition/outcome, target scene slice | related world/lead pressure | broad policy and scene fact duplication | unrelated social preference rules, inactive NPC knowledge | exact target-specific scene projection needs test coverage |
"""
    write("PR-CS_context_relevance_audit.md", relevance)

    candidates = """# PR-CS Optimization Candidates

| Rank | Candidate | Affected modules | Current cost evidence | Estimated savings | Complexity | Authority risk | Gameplay risk | Required tests | Reversible |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | Deduplicate policy prose between system prompt and payload instructions | `game/gm.py`, `game/prompt_context.py` | 60+ payload instructions; many exact/semantic repeats of system rules | 2k-5k input tokens | low | low if canonical rule ids stay | low | prompt/guard, PR-CP, PR-CR, C18/C19 | yes |
| 2 | Collapse duplicate authored scene fact projections | `game/prompt_context.py`, decision recipe projection | facts repeated in visible/opening/journal/claims/recipe | 3k-8k | medium | medium; must preserve source refs app-side | low-medium | authored-answer preservation, immutable validation, NPC boundaries | yes |
| 3 | Resolver-specific provider projection | `game/gm.py`, `game/prompt_context.py` | harmless dialogue carries exploration/combat/world action scaffolding | 8k-18k for simple turns | medium | medium | medium | PR-CC/CE/CK/CN plus continuity | yes |
| 4 | Keep validator-only metadata out of provider prompt | CTIR/projection/finalizer modules | semantic identity, persistence, premise/source metadata not always needed for narration-only | 2k-7k | medium | medium-high | low if validator retains full state | immutable finalizer, consequential rejection | yes |
| 5 | Selective NPC/scene/lead projection | prompt_context, leads, interaction_context | unrelated NPCs and broad lead/world pressure appear in local questions | 2k-6k | medium | medium | medium | NPC knowledge boundaries, exploration authority | yes |
| 6 | Conversation history compression/versioned memory rows | conversational_memory_window | not dominant in early turns; grows later | 1k-5k later | medium | low | medium | history continuity, callback tests | yes |
| 7 | Retry feedback minimization | gm_retry | retry adds ~8.4k in PR-CQ authored patrol before PR-CR | now lower after PR-CR; still useful for other retries | low | low | low | retry recovery/failure-locality tests | yes |
| 8 | Deterministic authored-answer delivery | API/finalization | PR-CR already removes eligible authored retry; further direct delivery could remove some generation | up to whole call for narrow authored answers | high | high if overused | medium | broad authored/fallback/social tests | yes with flag |
"""
    write("PR-CS_optimization_candidates.md", candidates)

    targets = """# PR-CS Token Targets

Simple NPC dialogue target 3,000-6,000 input tokens: feasible after deduplicating policy, sending only active speaker/knowledge/scene anchor, and keeping validator-only metadata app-side.

Ordinary exploration target 5,000-10,000 input tokens: feasible for local observe/investigate/interact turns if scene projection becomes target-specific and inactive social/combat policy is omitted.

Complex consequential actions target 10,000-20,000 input tokens: feasible but not guaranteed. Combat, multi-actor social pressure, transitions, or high-risk inference may legitimately require the upper range or exceed it until projection tests mature.

Authority information that must remain: CTIR/resolution contract, response type contract, visibility/authority ceilings, active scene facts, relevant NPC knowledge boundaries, allowed state mutations, and hard validation inputs. The key optimization is not deletion from authoritative state; it is not sending every deterministic artifact verbatim to the provider.
"""
    write("PR-CS_token_targets.md", targets)

    regression = """# PR-CS Regression Strategy

Required before implementation:

- PR-CP authorized finalization
- PR-CR authored retry recovery
- PR-CI authored-answer preservation
- PR-CC social reply planning
- PR-CE subjective preference handling
- PR-CK resolver selection
- PR-CN contextual extraction
- immutable-response validation
- consequential-claim rejection
- C18/C19 authority protections
- NPC knowledge boundaries
- exploration authority
- world-state continuity
- conversation-history continuity

Existing tests largely verify behavior and validation outcomes, not provider prompt completeness. Add projection contract tests that assert each resolver class includes its minimum authority slice and excludes known irrelevant sections. Add golden prompt-shape tests with token/char budgets per resolver profile so reductions cannot silently remove required authority.
"""
    write("PR-CS_regression_strategy.md", regression)

    road = """# PR-CS Implementation Roadmap

Stage 1: Policy and instruction deduplication.
Scope: remove repeated prose from payload instructions when equivalent canonical system/policy references exist. Success: simple captured prompts drop at least 2k estimated tokens with no behavior change. Stop if any rule loses a single canonical owner.

Stage 2: Resolver-specific projection profiles.
Scope: social-preference, authored-answer, observation, exploration, passive, physical-action, consequential-social, combat prompt profiles. Success: simple NPC dialogue under 6k-10k measured input tokens in dry-run/live validation, complex actions retain all authority gates. Stop on validator or continuity regression.

Stage 3: Compact authority projections.
Scope: send minimal claim text/source ids to provider; retain full semantic identity/persistence/premise metadata for validators/finalizer outside provider prompt. Success: 3k-8k additional savings on initial turns. Stop on immutable-response or consequential-claim regression.

Stage 4: Selective scene/NPC/lead projection.
Scope: active speaker, current target/action, directly relevant lead/topic only. Success: ordinary exploration consistently 5k-10k unless complex. Stop if authored knowledge or world-state continuity weakens.

Stage 5: Optional deterministic delivery for narrow authored answers.
Scope: only after profiles are stable; use deterministic output where generation adds no value. Success: zero provider calls for narrow eligible authored responses. Stop if narrative usefulness or agency suffers.
"""
    write("PR-CS_implementation_roadmap.md", road)

    changed = git_text(["status", "--short"])
    write("changed_files.txt", changed)

    current_review = f"""# CURRENT_REVIEW

PR-CS

MODE:
PROVIDER CONTEXT EFFICIENCY AUDIT

LIVE CALLS:
0

PR-CR inherited decision:
A - EARLY AUTHORED PROJECTION VERIFIED

Historical token baseline:
PR-CO 295,037 total tokens / 12 provider requests / 54.8% retry-token overhead. PR-CQ 108,690 total tokens / 2 completed gameplay turns / 39.6% retry-token overhead.

Reconstructed token baseline:
No reconstruction was needed for the requested representatives; exact captured payloads were available. Category attribution is local chars/4 estimate because exact GPT-4.1 tokenizer is not vendored.

Largest context contributors:
Broad payload instructions, repeated authority/narration policies, full mechanical/claim projections, repeated authored scene facts, and broad world/lead/NPC context.

Confirmed duplication:
System prompt rules repeat in payload instructions; scene facts repeat through visible/opening/journal facts, realization claims, and answer recipe required_content.

Resolver-specific unnecessary context:
Simple social turns carry exploration/combat/action scaffolding and unrelated scene/world/NPC details; observation/exploration turns carry social dialogue policy that is not active.

Authority-sensitive context:
CTIR/resolution contract, visibility, narrative authority ceilings, active speaker knowledge, accepted claims, response type contract, finalizer/validator state.

Estimated safe savings:
Initial low-risk savings likely 5k-10k tokens for simple turns; staged resolver-specific projection can plausibly reach 15k-25k savings for dialogue/observation without deleting authority state.

Token target feasibility:
Simple NPC dialogue 3k-6k feasible after projection/dedup. Ordinary exploration 5k-10k feasible for local turns. Complex consequential actions 10k-20k feasible for many but not all cases.

Recommended first implementation:
Policy/instruction deduplication followed by resolver-specific prompt profiles.

PR-CS decision:
A - CLEAR LOW-RISK OPTIMIZATION PATH

Recommended next step:
Implement Stage 1 deduplication behind focused prompt-shape regression tests, then measure provider input tokens with no authority-contract relaxation.
"""
    (ROOT / "handoff" / "CURRENT_REVIEW.md").write_text(current_review, encoding="utf-8")

    manifest = {
        "review": "PR-CS",
        "mode": "PROVIDER CONTEXT EFFICIENCY AUDIT",
        "live_calls": 0,
        "artifacts": sorted(p.name for p in OUT.iterdir() if p.is_file()),
    }
    (ROOT / "handoff" / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    zip_path = ROOT / "handoff" / "CURRENT_REVIEW.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(ROOT / "handoff" / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
        zf.write(ROOT / "handoff" / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
        for p in sorted(OUT.iterdir()):
            if p.is_file() and p.name != "build_pr_cs_audit.py":
                zf.write(p, f"artifacts/pr_cs_context_efficiency/{p.name}")


if __name__ == "__main__":
    write_artifacts()
