"""Opt-in engine-owned campaign-opening narration.

The model may select catalog entries and reviewed presentation variants.
It cannot supply facts, authority, or player-facing prose. Final opening
text is assembled here from public catalog content.

Disabled unless ``ASHEN_OPENING_RENDERER`` is explicitly enabled. Ordinary
turns never consult this module.

Additional presentation variants do not require an authority-model change.
Add a reviewed row to ``APPROVED_PRESENTATION_VARIANTS``, keyed by the exact
authored sentence. The variant must keep the same referents, polarity,
modality, and attribution, and it must not add a consequential outcome.
The model may select the new variant id only after that row exists.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Mapping, Sequence

FLAG = "ASHEN_OPENING_RENDERER"
CONTRACT = "opening_presentation"
CATALOG_BEGIN = "OPENING_PRESENTATION_CATALOG\n"
CATALOG_END = "\nEND_OPENING_PRESENTATION_CATALOG"
PLAN_KEYS = frozenset({"selected_entries"})
ENTRY_KEYS = frozenset({"catalog_id", "variant_id"})
NARRATION_KEYS = frozenset({
    "narration", "player_facing_text", "text", "content", "prose", "sentence", "free_text",
})
AUTHORITY_KEYS = frozenset({
    "authority", "disclosure", "required", "visibility", "provenance", "epistemic_status",
    "modality", "realization_role", "world_updates", "scene_update", "state_mutations",
    "hidden", "secret",
})
PUBLIC_SOURCE_PREFIXES = ("scene.visible_facts.", "scene.opening_seed_facts.")
HIDDEN_SOURCE_MARKERS = (
    "hidden", "secret", "backstage", "gm_only", "undiscovered", "private",
    "motivation", "restricted", "journal_seed",
)
PUBLIC_DISCLOSURE = frozenset({"", "public", "player", "visible", "player_visible", "revealed"})
HIDDEN_DISCLOSURE = frozenset({
    "hidden", "gm_only", "backstage", "secret", "undiscovered", "private", "restricted",
})
_TRUE = frozenset({"1", "true", "yes", "on"})
_FALSE = frozenset({"", "0", "false", "no", "off"})
_MAX_SELECTIONS = 24
_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)

# Reviewed alternate wording for one authored public sentence.
# Same referents: notice board, taxes, curfew rules, missing patrol.
APPROVED_PRESENTATION_VARIANTS: dict[str, dict[str, str]] = {
    "The notice board lists taxes, curfew rules, and a warning about a missing patrol.": {
        "concise": (
            "The notice board lists taxes, curfew rules, and a warning about a patrol that has gone missing."
        ),
    },
}


def opening_renderer_mode() -> str:
    """Return ``disabled``, ``enabled``, or ``invalid``.

    Unset and the usual false spellings stay on the legacy opening path.
    Any other value fails closed and must not enable the renderer.
    """
    raw = os.environ.get(FLAG)
    if raw is None:
        return "disabled"
    value = raw.strip().lower()
    if value in _FALSE:
        return "disabled"
    if value in _TRUE:
        return "enabled"
    return "invalid"


def opening_renderer_diagnostics() -> dict[str, str]:
    mode = opening_renderer_mode()
    return {"flag": FLAG, "mode": mode, "selected": mode == "enabled"}


def _norm(text: object) -> str:
    return " ".join(str(text or "").casefold().split())


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, Mapping):
            text = str(item.get("text") or item.get("content") or "").strip()
            if text:
                out.append(text)
    return out


def _disclosure(claim: Mapping[str, Any]) -> str:
    for key in ("disclosure", "visibility", "player_disclosure"):
        value = str(claim.get(key) or "").strip().lower()
        if value:
            return value
    identity = claim.get("semantic_identity") if isinstance(claim.get("semantic_identity"), Mapping) else {}
    return str(identity.get("disclosure") or identity.get("visibility") or "").strip().lower()


def _public_claim(claim: Mapping[str, Any], *, hidden_norms: set[str], visible_norms: set[str]) -> bool:
    text = str(claim.get("text") or "").strip()
    norm = _norm(text)
    if not norm or norm in hidden_norms:
        return False
    disclosure = _disclosure(claim)
    if disclosure in HIDDEN_DISCLOSURE or disclosure not in PUBLIC_DISCLOSURE:
        return False
    source = str(claim.get("source_ref") or "")
    source_low = source.lower()
    if any(marker in source_low for marker in HIDDEN_SOURCE_MARKERS):
        return False
    public_source = source.startswith(PUBLIC_SOURCE_PREFIXES)
    if not public_source and norm not in visible_norms:
        return False
    authority = str(claim.get("authority") or "")
    provenance = str(claim.get("provenance") or "")
    if authority not in {"", "world_truth"} and provenance not in {"", "authored_world_fact"}:
        if norm not in visible_norms:
            return False
    return True


def build_opening_public_catalog(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build the public opening catalog from an existing prompt payload.

    Only this function creates entries. Hidden, discoverable-but-unpublished,
    and unrecognized disclosure states are omitted. An empty or colliding
    catalog fails closed.
    """
    if not isinstance(payload, Mapping):
        return {"ok": False, "reason": "opening_catalog_empty", "entries": [], "by_id": {}, "required_ids": []}
    decision = payload.get("gm_resolution_decision") if isinstance(payload.get("gm_resolution_decision"), Mapping) else {}
    visibility = payload.get("narration_visibility") if isinstance(payload.get("narration_visibility"), Mapping) else {}
    scene = payload.get("scene") if isinstance(payload.get("scene"), Mapping) else {}
    gm_only = scene.get("gm_only") if isinstance(scene.get("gm_only"), Mapping) else {}
    curated = _string_list(payload.get("opening_curated_facts") or payload.get("opening_selector_selected_facts"))
    visible = _string_list(visibility.get("visible_fact_strings"))
    public_scene = scene.get("public") if isinstance(scene.get("public"), Mapping) else {}
    visible.extend(_string_list(public_scene.get("visible_facts")))
    hidden = _string_list(visibility.get("hidden_fact_strings"))
    hidden.extend(_string_list(visibility.get("discoverable_fact_strings")))
    hidden.extend(_string_list(gm_only.get("hidden_facts")))
    hidden.extend(_string_list(gm_only.get("discoverable_clues_locked")))
    campaign = payload.get("campaign") if isinstance(payload.get("campaign"), Mapping) else {}
    for key in ("secret", "secrets", "restricted", "hidden_metadata"):
        hidden.extend(_string_list(campaign.get(key)))
    hidden_norms = {_norm(item) for item in hidden if _norm(item)}
    visible_norms = {_norm(item) for item in visible if _norm(item)}
    curated_norms = {_norm(item) for item in curated if _norm(item)}
    entries: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    seen_text: set[str] = set()
    claims = decision.get("realization_claims") if isinstance(decision.get("realization_claims"), list) else []
    for claim in claims:
        if not isinstance(claim, Mapping):
            continue
        if not _public_claim(claim, hidden_norms=hidden_norms, visible_norms=visible_norms):
            continue
        text = str(claim.get("text") or "").strip()
        norm = _norm(text)
        if norm in seen_text:
            continue
        catalog_id = str(claim.get("claim_id") or "").strip()
        if not catalog_id:
            basis = f"{claim.get('source_ref') or ''}|{text}"
            catalog_id = "opening_fact_" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]
        if catalog_id in by_id:
            return {"ok": False, "reason": "opening_catalog_invalid", "entries": [], "by_id": {}, "required_ids": []}
        required = norm in curated_norms if curated_norms else str(claim.get("realization_role") or "") == "MUST_STATE"
        variants = {"authored": text}
        variants.update(APPROVED_PRESENTATION_VARIANTS.get(text) or {})
        entry = {
            "catalog_id": catalog_id,
            "source_claim_ref": str(claim.get("source_ref") or ""),
            "source_claim_id": str(claim.get("claim_id") or ""),
            "text": text,
            "disclosure": "public",
            "required": required,
            "variants": variants,
            "sequence": len(entries),
            "order_constrained": required,
            "claim": {
                "provenance": str(claim.get("provenance") or "authored_world_fact"),
                "epistemic_status": str(claim.get("epistemic_status") or "established"),
                "modality": str(claim.get("modality") or ""),
                "realization_role": str(claim.get("realization_role") or "MAY_STATE"),
                "relation_kind": str(claim.get("relation_kind") or "ordinary_predicate"),
                "premise_claim_ids": [
                    str(item) for item in (claim.get("premise_claim_ids") or []) if str(item).strip()
                ],
                "semantic_identity": dict(claim.get("semantic_identity") or {})
                if isinstance(claim.get("semantic_identity"), Mapping) else {},
            },
        }
        entries.append(entry)
        by_id[catalog_id] = entry
        seen_text.add(norm)
    if not entries:
        return {"ok": False, "reason": "opening_catalog_empty", "entries": [], "by_id": {}, "required_ids": []}
    required_ids = [entry["catalog_id"] for entry in entries if entry["required"]]
    if not required_ids:
        for entry in entries:
            if entry["claim"]["realization_role"] == "MUST_STATE":
                entry["required"] = True
                entry["order_constrained"] = True
        required_ids = [entry["catalog_id"] for entry in entries if entry["required"]]
    if not required_ids:
        return {"ok": False, "reason": "opening_catalog_empty", "entries": [], "by_id": {}, "required_ids": []}
    return {"ok": True, "reason": "", "entries": entries, "by_id": by_id, "required_ids": required_ids}


def catalog_prompt_index(catalog: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "entries": [
            {
                "catalog_id": entry["catalog_id"],
                "required": bool(entry["required"]),
                "variant_ids": sorted(entry["variants"]),
                "sequence": int(entry["sequence"]),
            }
            for entry in catalog.get("entries") or []
        ]
    }


def opening_plan_instruction(catalog: Mapping[str, Any]) -> str:
    index = json.dumps(catalog_prompt_index(catalog), separators=(",", ":"), sort_keys=True)
    return (
        "OPENING PRESENTATION PLAN: Return one JSON object and no other text. "
        "The only allowed key is selected_entries. Each entry may contain only "
        "catalog_id and variant_id. Select every required entry in increasing sequence. "
        "Optional entries may be included. Do not write narration, facts, outcomes, or state changes.\n"
        f"{CATALOG_BEGIN}{index}{CATALOG_END}"
    )


def prompt_payload_from_messages(messages: Sequence[Mapping[str, Any]] | None) -> dict[str, Any] | None:
    for message in reversed(list(messages or [])):
        if message.get("role") != "user":
            continue
        try:
            payload = json.loads(str(message.get("content") or ""))
        except (ValueError, TypeError):
            continue
        if isinstance(payload, dict):
            return payload
    return None


def prepare_opening_renderer(messages: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    catalog = build_opening_public_catalog(prompt_payload_from_messages(messages))
    if not catalog["ok"]:
        return {"ok": False, "reason": catalog["reason"], "catalog": catalog, "messages": list(messages)}
    prepared = [dict(message) for message in messages]
    instruction = {"role": "system", "content": opening_plan_instruction(catalog)}
    if prepared:
        prepared = [prepared[0], instruction, *prepared[1:]]
    else:
        prepared = [instruction]
    return {"ok": True, "reason": "", "catalog": catalog, "messages": prepared}


def _load_plan(raw: str) -> tuple[dict[str, Any] | None, str]:
    text = str(raw or "").strip()
    fence = _FENCE.fullmatch(text)
    if fence:
        text = fence.group(1).strip()
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        return None, "opening_presentation_malformed"
    if not isinstance(value, dict):
        return None, "plan_schema"
    return value, ""


def _rejected_key(keys: set[str]) -> str:
    if keys & NARRATION_KEYS:
        return "arbitrary_narration_field"
    if keys & AUTHORITY_KEYS:
        return "model_supplied_authority"
    return "unsupported_field"


def validate_presentation_plan(plan: Mapping[str, Any], catalog: Mapping[str, Any]) -> dict[str, Any]:
    if set(plan) != PLAN_KEYS:
        extra = set(plan) - PLAN_KEYS
        if extra & NARRATION_KEYS:
            return {"ok": False, "reason": "arbitrary_narration_field"}
        if extra & AUTHORITY_KEYS:
            return {"ok": False, "reason": "model_supplied_authority"}
        return {"ok": False, "reason": "unsupported_field" if extra else "plan_schema"}
    selected = plan.get("selected_entries")
    if not isinstance(selected, list) or len(selected) > _MAX_SELECTIONS:
        return {"ok": False, "reason": "plan_schema" if not isinstance(selected, list) else "plan_bound"}
    by_id = catalog.get("by_id") if isinstance(catalog.get("by_id"), Mapping) else {}
    chosen: list[dict[str, Any]] = []
    seen: set[str] = set()
    last_sequence = -1
    for item in selected:
        if not isinstance(item, Mapping) or set(item) != ENTRY_KEYS:
            extra = set(item) - ENTRY_KEYS if isinstance(item, Mapping) else set()
            return {"ok": False, "reason": _rejected_key(extra) if extra else "plan_schema"}
        catalog_id = item.get("catalog_id")
        variant_id = item.get("variant_id")
        if not isinstance(catalog_id, str) or not isinstance(variant_id, str):
            return {"ok": False, "reason": "plan_schema"}
        entry = by_id.get(catalog_id)
        if not isinstance(entry, Mapping):
            return {"ok": False, "reason": "unknown_catalog_id"}
        if entry.get("disclosure") != "public":
            return {"ok": False, "reason": "hidden_catalog_entry"}
        variants = entry.get("variants") if isinstance(entry.get("variants"), Mapping) else {}
        if variant_id not in variants:
            return {"ok": False, "reason": "unknown_variant_id"}
        if catalog_id in seen:
            return {"ok": False, "reason": "duplicate_selection"}
        seen.add(catalog_id)
        if entry.get("order_constrained"):
            sequence = int(entry.get("sequence") or 0)
            if sequence <= last_sequence:
                return {"ok": False, "reason": "invalid_ordering"}
            last_sequence = sequence
        chosen.append({"entry": entry, "variant_id": variant_id})
    missing = [catalog_id for catalog_id in catalog.get("required_ids") or [] if catalog_id not in seen]
    if missing:
        return {"ok": False, "reason": "missing_required_entry"}
    if not chosen:
        return {"ok": False, "reason": "empty_opening_render"}
    return {"ok": True, "reason": "", "chosen": chosen}


def render_opening(plan: Mapping[str, Any], catalog: Mapping[str, Any]) -> dict[str, Any]:
    checked = validate_presentation_plan(plan, catalog)
    if not checked["ok"]:
        return {"ok": False, "reason": checked["reason"], "text": "", "trace": [], "declarations": []}
    parts: list[str] = []
    trace: list[dict[str, Any]] = []
    declarations: list[dict[str, Any]] = []
    cursor = 0
    for index, choice in enumerate(checked["chosen"]):
        entry = choice["entry"]
        variant_id = choice["variant_id"]
        rendered = str(entry["variants"][variant_id]).strip()
        if not rendered:
            return {"ok": False, "reason": "empty_opening_render", "text": "", "trace": [], "declarations": []}
        parts.append(rendered)
        trace.append({
            "catalog_id": entry["catalog_id"],
            "variant_id": variant_id,
            "source_claim_ref": entry["source_claim_ref"],
            "rendered_text": rendered,
            "disclosure": "public",
            "position": cursor,
        })
        cursor += len(rendered) + (1 if index + 1 < len(checked["chosen"]) else 0)
        claim = entry["claim"]
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", rendered) if part.strip()] or [rendered]
        for offset, sentence in enumerate(sentences):
            declarations.append({
                "declaration_id": f"rendered_{entry['catalog_id']}_{offset}",
                "declaration_mode": "realize",
                "source_claim_id": entry["source_claim_id"] or None,
                "premise_claim_ids": list(claim["premise_claim_ids"]),
                "semantic_identity": dict(claim["semantic_identity"]),
                "provenance_requested": claim["provenance"],
                "epistemic_status": claim["epistemic_status"],
                "modality": claim["modality"],
                "realization_role": claim["realization_role"],
                "relation_kind": claim["relation_kind"],
                "text": sentence,
            })
    text = " ".join(parts)
    return {"ok": True, "reason": "", "text": text, "trace": trace, "declarations": declarations}


def realize_opening_provider_text(raw: str, catalog: Mapping[str, Any]) -> dict[str, Any]:
    plan, reason = _load_plan(raw)
    if plan is None:
        return {"ok": False, "reason": reason, "text": "", "trace": [], "declarations": []}
    return render_opening(plan, catalog)


def gm_response_from_render(result: Mapping[str, Any]) -> dict[str, Any]:
    text = str(result.get("text") or "")
    trace = list(result.get("trace") or [])
    return {
        "player_facing_text": text,
        "tags": ["opening_presentation_rendered"],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "Engine-owned opening presentation.",
        "metadata": {
            "output_form": "structured",
            "provider_response_contract": CONTRACT,
            "opening_renderer": {"mode": "enabled", "selected": True, "flag": FLAG},
            "opening_presentation": {
                "authoritative_render": True,
                "rendered_text": text,
                "trace": trace,
                "catalog_ids": [row["catalog_id"] for row in trace],
                "publication": "renderer",
            },
            "realization_envelope": {
                "schema_version": 1,
                "provider_response_contract": CONTRACT,
                "declared_claims": list(result.get("declarations") or []),
                "narration": text,
                "structured_contract_present": True,
                "legacy_fallback": False,
                "declaration_authorship": "engine_opening_catalog",
            },
        },
    }


def enforce_rendered_publication(gm: dict[str, Any] | None) -> dict[str, Any] | None:
    """Keep an accepted rendered opening equal to the catalog trace.

    Rejected openings are left for the existing failure response. Model update
    fields cannot remain on an accepted rendered opening.
    """
    if not isinstance(gm, dict):
        return gm
    metadata = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    record = metadata.get("opening_presentation") if isinstance(metadata.get("opening_presentation"), dict) else {}
    if not record.get("authoritative_render"):
        return gm
    if metadata.get("structured_contract_failure") or metadata.get("structured_output_rejected"):
        return gm
    accepted = metadata.get("accepted_response") if isinstance(metadata.get("accepted_response"), dict) else {}
    if accepted.get("provenance") == "safe_nonresolution" or accepted.get("authorization_source") == "safe_nonresolution":
        return gm
    text = str(record.get("rendered_text") or "")
    gm["player_facing_text"] = text
    gm["scene_update"] = None
    gm["world_updates"] = None
    gm["activate_scene_id"] = None
    gm["new_scene_draft"] = None
    gm["suggested_action"] = None
    gm.pop("improvisation_proposals", None)
    gm["debug_notes"] = "Engine-owned opening presentation."
    envelope = metadata.get("realization_envelope") if isinstance(metadata.get("realization_envelope"), dict) else None
    if isinstance(envelope, dict):
        envelope["narration"] = text
    record["publication"] = "renderer"
    return gm


def embedded_catalog_index(messages: Sequence[Mapping[str, Any]] | None) -> dict[str, Any] | None:
    for message in messages or []:
        content = str(message.get("content") or "")
        start = content.find(CATALOG_BEGIN)
        if start < 0:
            continue
        rest = content[start + len(CATALOG_BEGIN):]
        end = rest.find(CATALOG_END)
        if end < 0:
            return None
        try:
            value = json.loads(rest[:end])
        except (ValueError, TypeError):
            return None
        return value if isinstance(value, dict) else None
    return None


def plan_selecting_required(messages: Sequence[Mapping[str, Any]] | None) -> str | None:
    """Deterministic plan used by the synthetic harness. It selects no prose."""
    index = embedded_catalog_index(messages)
    if not index:
        return None
    rows = [row for row in index.get("entries") or [] if isinstance(row, Mapping) and row.get("required")]
    rows.sort(key=lambda row: int(row.get("sequence") or 0))
    if not rows:
        return None
    plan = {
        "selected_entries": [
            {"catalog_id": row["catalog_id"], "variant_id": "authored"}
            for row in rows
            if isinstance(row.get("catalog_id"), str)
        ]
    }
    return json.dumps(plan, separators=(",", ":"), sort_keys=True)
