"""Deterministic scene-opening fallback text composition (shared upstream / gate compatibility).

**Ownership:** :mod:`game.opening_deterministic_fallback` is the single shared implementation of the
deterministic opening line composer (curated facts → prose). :mod:`game.upstream_response_repairs`
builds the canonical ``upstream_prepared_opening_fallback`` payload from this function; the gate
(:mod:`game.final_emission_gate`) **selects** that payload when present and only invokes this module
locally as a compatibility path when the payload is missing or unusable—without owning alternate prose.

Extracted from ``final_emission_gate`` so upstream can import without importing the gate (cycles).
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

from game.final_emission_text import _normalize_text

OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER = "[opening_fallback_failed_closed: empty_curated_facts]"


def _opening_clean_fact_list(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            continue
        clean = item.strip()
        key = clean.lower()
        if not clean or key in seen:
            continue
        seen.add(key)
        out.append(clean)
    return out


def opening_context_from_gm_output(gm_output: Mapping[str, Any] | None) -> Dict[str, Any]:
    ctx: Dict[str, Any] = {
        "location_anchors": [],
        "visible_facts": [],
        "actionable_labels": [],
        "opening_fallback_context_source": "none",
        "opening_fallback_basis_count": 0,
        "opening_fallback_context_missing": True,
        "opening_curated_facts_source": "selector",
        "opening_selector_source_used": "none",
        "opening_selector_selected_facts": [],
        "opening_curated_facts": [],
        "opening_final_fallback_basis": [],
        "opening_final_basis_matches_selector": False,
    }
    if not isinstance(gm_output, Mapping):
        raise AssertionError("scene_opening missing curated facts")
    if "opening_curated_facts" not in gm_output:
        raise AssertionError("scene_opening missing curated facts")
    gm_curated = gm_output.get("opening_curated_facts")
    if not isinstance(gm_curated, list):
        raise AssertionError("scene_opening missing curated facts")
    curated_facts = _opening_clean_fact_list(gm_curated)
    ctx["visible_facts"].extend(curated_facts)
    ctx["opening_curated_facts"] = list(curated_facts)
    if ctx["visible_facts"]:
        ctx["opening_fallback_context_source"] = "opening_curated_facts"
        md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), Mapping) else {}
        em = md.get("emission_debug") if isinstance(md.get("emission_debug"), Mapping) else {}
        src = str(em.get("opening_curated_facts_source") or "").strip()
        selector_src = str(em.get("opening_selector_source_used") or src or "").strip()
        ctx["opening_curated_facts_source"] = src or "selector"
        ctx["opening_selector_source_used"] = selector_src or "selector"
        selector_facts = _opening_clean_fact_list(
            gm_output.get("opening_selector_selected_facts")
            if isinstance(gm_output.get("opening_selector_selected_facts"), list)
            else em.get("opening_selector_selected_facts")
        )
        ctx["opening_selector_selected_facts"] = selector_facts or list(curated_facts)
    pc = gm_output.get("prompt_context")
    if isinstance(pc, Mapping):
        plan = pc.get("narrative_plan") if isinstance(pc.get("narrative_plan"), Mapping) else {}
        scene_opening = plan.get("scene_opening") if isinstance(plan.get("scene_opening"), Mapping) else {}
        scene_anchors = plan.get("scene_anchors") if isinstance(plan.get("scene_anchors"), Mapping) else {}
        for raw in (scene_opening.get("location_anchors"), scene_anchors.get("location_anchors")):
            if isinstance(raw, (list, tuple)):
                ctx["location_anchors"].extend(str(x).strip() for x in raw if isinstance(x, str) and str(x).strip())
            elif isinstance(raw, str) and raw.strip():
                ctx["location_anchors"].append(raw.strip())

        scene_block = pc.get("scene")
        public_scene = scene_block.get("public") if isinstance(scene_block, Mapping) else None
        if isinstance(public_scene, Mapping):
            loc = public_scene.get("location") or public_scene.get("id")
            if isinstance(loc, str) and loc.strip():
                ctx["location_anchors"].append(loc.strip())
        else:
            public_scene = None
    else:
        public_scene = None

    if isinstance(public_scene, Mapping):
        for key in ("actions", "suggested_actions", "exits", "interactables", "objects"):
            rows = public_scene.get(key)
            if not isinstance(rows, list):
                continue
            for row in rows[:6]:
                if not isinstance(row, Mapping):
                    continue
                label = row.get("label") or row.get("name") or row.get("id")
                if isinstance(label, str) and label.strip():
                    ctx["actionable_labels"].append(label.strip())

    # Preserve order while removing duplicates.
    for key in ("location_anchors", "visible_facts", "actionable_labels"):
        seen: set[str] = set()
        out: list[str] = []
        for raw in ctx.get(key) or []:
            clean = str(raw or "").strip()
            low = clean.lower()
            if not clean or low in seen:
                continue
            seen.add(low)
            out.append(clean)
        ctx[key] = out
    ctx["opening_fallback_basis_count"] = len(ctx.get("visible_facts") or [])
    ctx["opening_fallback_context_missing"] = ctx["opening_fallback_basis_count"] <= 0
    ctx["opening_final_fallback_basis"] = list(ctx.get("visible_facts") or [])
    ctx["opening_final_basis_matches_selector"] = (
        list(ctx.get("opening_final_fallback_basis") or [])
        == list(ctx.get("opening_selector_selected_facts") or [])
    )
    return ctx


def _actionable_hook_from_opening_context(context: Mapping[str, Any]) -> str:
    labels = [str(x).strip() for x in (context.get("actionable_labels") or []) if str(x).strip()]
    if labels:
        head = labels[:3]
        if len(head) == 1:
            return f"You can start with {head[0]}."
        if len(head) == 2:
            return f"You can start with {head[0]} or {head[1]}."
        return f"You can start with {head[0]}, {head[1]}, or {head[2]}."
    facts = [str(x).strip() for x in (context.get("visible_facts") or []) if str(x).strip()]
    hook_targets: list[str] = []
    joined = " ".join(facts).lower()
    if "notice board" in joined or "notice" in joined:
        hook_targets.append("read the notice board")
    if "guard" in joined:
        hook_targets.append("press the guards")
    if "runner" in joined or "tavern" in joined:
        hook_targets.append("approach the tavern runner")
    if "wagon" in joined or "traffic" in joined or "crowd" in joined:
        hook_targets.append("work through the crowd")
    if hook_targets:
        head = hook_targets[:3]
        if len(head) == 1:
            return f"You can {head[0]}."
        if len(head) == 2:
            return f"You can {head[0]} or {head[1]}."
        return f"You can {head[0]}, {head[1]}, or {head[2]}."
    return ""


def _opening_fact_matches_any(fact: str, needles: tuple[str, ...]) -> bool:
    low = fact.lower()
    return any(needle in low for needle in needles)


def _pick_opening_fallback_fact(
    facts: list[str],
    *,
    used: set[str],
    needles: tuple[str, ...],
) -> str:
    for fact in facts:
        key = fact.lower()
        if key not in used and _opening_fact_matches_any(fact, needles):
            used.add(key)
            return fact
    for fact in facts:
        key = fact.lower()
        if key not in used:
            used.add(key)
            return fact
    return ""


def deterministic_opening_fallback_text_and_meta(
    gm_output: Mapping[str, Any] | None,
) -> tuple[str, Dict[str, Any]]:
    """Shared deterministic opening composer (curated facts → text + meta).

    Called from :mod:`game.upstream_response_repairs` for the prepared payload and from
    :mod:`game.final_emission_gate` only on the compatibility path when that payload is absent.
    """
    from game.final_emission_opening_fallback import build_opening_fallback_result_meta

    context = opening_context_from_gm_output(gm_output)
    facts = [str(x).strip().rstrip(".") for x in (context.get("visible_facts") or []) if str(x).strip()]
    meta = build_opening_fallback_result_meta(context=context, facts=facts)
    if not meta["opening_final_basis_matches_selector"]:
        raise AssertionError("curated opening facts diverged from selector output")
    if not facts:
        return OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER, build_opening_fallback_result_meta(
            context=context,
            facts=facts,
            opening_fallback_failed_closed=True,
            force_fail_closed_context_source=True,
        )

    used: set[str] = set()
    environment = _pick_opening_fallback_fact(
        facts,
        used=used,
        needles=("gate", "district", "market", "road", "square", "rain", "mist", "banners", "street", "yard"),
    )
    activity = _pick_opening_fallback_fact(
        facts,
        used=used,
        needles=("guard", "refugee", "wagon", "crowd", "runner", "stranger", "observer", "watch", "hawking"),
    )
    hook_fact = _pick_opening_fallback_fact(
        facts,
        used=used,
        needles=("notice", "curfew", "tax", "missing", "patrol", "offers", "signals", "speak", "coin", "risk"),
    )
    hook = _actionable_hook_from_opening_context(context)
    parts = [str(p).strip().rstrip(".") for p in (environment, activity, hook_fact, hook) if str(p).strip()]
    return _normalize_text(". ".join(parts) + "."), meta
