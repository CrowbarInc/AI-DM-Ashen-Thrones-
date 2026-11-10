"""Read-only post-opening grounding audit for PR-PLAY-43.

Loads a copied scene snapshot and calls production grounding functions.
Does not submit a turn, call a resolver, or call the provider.
The parent process sets ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT and
points ASHEN_DATA_DIR at an empty scratch directory before this process starts.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RUMOR = "Have you heard any interesting rumors lately?"
NOTICE = "I examine the notice board."
PATROL = "I want to follow the trail connected to the missing patrol."


def unwrap(document):
    if isinstance(document, dict) and isinstance(document.get("payload"), dict):
        return document["payload"]
    return document if isinstance(document, dict) else {}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ids_of(rows):
    return [str(row.get("id") or "") for row in rows if isinstance(row, dict)]


def grounding_view(grounding):
    if not isinstance(grounding, dict):
        return {"available": False}
    return {
        "target_resolution": grounding.get("target_resolution"),
        "target_id": grounding.get("target_id"),
        "candidate_target_ids": grounding.get("candidate_target_ids"),
        "operation_eligibility": grounding.get("operation_eligibility"),
        "direct_address": grounding.get("direct_address"),
        "clarification": grounding.get("clarification"),
        "choices": [
            {"entity_id": choice.get("entity_id"), "label": choice.get("label")}
            for choice in (grounding.get("choices") or [])
            if isinstance(choice, dict)
        ],
        "allowed_operation": grounding.get("allowed_operation"),
        "communication_ownership": grounding.get("communication_ownership"),
    }


def would_clarify(authority, grounding):
    return bool(
        authority
        and isinstance(grounding, dict)
        and grounding.get("direct_address")
        and grounding.get("operation_eligibility") == "requires_clarification"
    )


def main():
    snapshot = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    report = {
        "observational": True,
        "provider_invoked_by_probe": False,
        "resolver_invoked": False,
        "turn_submitted": False,
        "skip_preflight": os.environ.get("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"),
        "data_dir": os.environ.get("ASHEN_DATA_DIR"),
    }
    try:
        if os.environ.get("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT") != "1":
            raise RuntimeError("preflight skip was not set before application import")
        from game.conversational_orchestration import (
            _analyze_clause,
            _catalog,
            _exit_rows,
            _step_from_clause,
            authored_travel_admission,
        )
        from game.incidental_entity import _clean, public_evidence_units
        from game.ordinary_semantic_ownership import (
            _npc_public_blob,
            _public_npc_candidates,
            _visible_npcs,
            addressee_authority_applies,
            assess_addressee_grounding,
        )
        from game.route_authority import route_status
        from game.storage import build_effective_scene

        report["game_api_imported"] = "game.api" in sys.modules
        if report["game_api_imported"]:
            from game.api_upstream_preflight import get_latest_upstream_api_preflight

            report["preflight_cache"] = get_latest_upstream_api_preflight()
            report["provider_invoked_by_probe"] = bool(report["preflight_cache"])

        session_doc = load_json(snapshot / "session.json")
        world = unwrap(load_json(snapshot / "world.json"))
        session = unwrap(session_doc)
        scene_id = str(session.get("active_scene_id") or "")
        scene_path = snapshot / "scenes" / f"{scene_id}.json"
        if not scene_id or not scene_path.is_file():
            report["decision"] = "INCONCLUSIVE"
            report["reasons"] = ["active_scene_file_unavailable"]
            report["active_scene_id"] = scene_id
            destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            return 3
        canon = load_json(scene_path)
        overlay = (session.get("runtime_scene_overlays") or {}).get(scene_id) or {}
        if not isinstance(overlay, dict):
            overlay = {}
        scene = build_effective_scene(canon, overlay)
        body = scene.get("scene") if isinstance(scene.get("scene"), dict) else scene
        canon_body = canon.get("scene") if isinstance(canon.get("scene"), dict) else canon

        def cleaned_list(values):
            if not isinstance(values, list):
                return []
            return [_clean(item, limit=400) for item in values if _clean(item, limit=400)]

        authored_facts = cleaned_list(canon_body.get("visible_facts"))
        added_facts = cleaned_list(overlay.get("visible_facts_add"))
        opening_seeds = cleaned_list(body.get("opening_seed_facts"))
        journal_seeds = cleaned_list(body.get("journal_seed_facts"))
        units = public_evidence_units(scene)
        structured = [
            ("authored_visible_fact", fact) for fact in authored_facts
        ] + [
            ("ai_added_visible_fact", fact) for fact in added_facts
        ] + [
            ("opening_seed_fact", fact) for fact in opening_seeds
        ] + [
            ("journal_seed_fact", fact) for fact in journal_seeds
        ]
        missing_units = [
            {"provenance": source, "fact": fact}
            for source, fact in structured
            if fact not in units
        ]
        collapsed_pairs = []
        ordered = [fact for _source, fact in structured]
        for left, right in zip(ordered, ordered[1:]):
            joined = f"{left} {right}"
            if joined in units:
                collapsed_pairs.append(joined)
        npcs = _visible_npcs(scene, world)
        associations = []
        leakage = []
        for npc in npcs:
            name = str(npc.get("name") or "").strip().lower()
            blob = _npc_public_blob(npc, scene)
            owned = [fact for _source, fact in structured if name and name in fact.lower()]
            leaked = [
                {"provenance": source, "fact": fact}
                for source, fact in structured
                if fact.lower() in blob and not (name and name in fact.lower())
            ]
            if leaked:
                leakage.append({"npc_id": npc.get("id"), "facts": leaked})
            associations.append({
                "npc_id": npc.get("id"),
                "name": npc.get("name"),
                "units_naming_npc": [unit for unit in units if name and name in unit.lower()],
                "structured_facts_naming_npc": owned,
            })
        exits = _exit_rows(scene)
        interactables = [
            {"id": row.get("id"), "label": row.get("label")}
            for row in (body.get("interactables") or [])
            if isinstance(row, dict)
        ]
        catalog = _catalog(scene, world)

        def candidates(text):
            kind, chosen = _public_npc_candidates(text, npcs, scene)
            grounding = assess_addressee_grounding(
                text, scene=scene, world=world, session=session,
            )
            return {
                "player_text": text,
                "public_candidate_kind": kind,
                "public_candidate_ids": ids_of(chosen),
                "grounding": grounding_view(grounding),
                "_grounding": grounding,
            }

        rumor = candidates(RUMOR)
        notice_public = candidates(NOTICE)
        patrol_public = candidates(PATROL)
        notice_authority = addressee_authority_applies(operation="INSPECT", player_text=NOTICE)
        patrol_authority = addressee_authority_applies(operation="MOVE", player_text=PATROL)
        clause = _analyze_clause(NOTICE, exits)
        step = _step_from_clause(
            clause, exits=exits, catalog=catalog, scene=scene, session=session,
        )
        travel = authored_travel_admission(PATROL, scene=scene, world=world, session=session)
        travel_view = None if travel is None else travel.to_public_dict()
        selected = None
        availability = None
        if travel is not None:
            selected = next(
                (row for row in exits if str(row.get("id") or "") == str(travel.proposed_target or "")),
                None,
            )
            if selected is not None:
                availability = route_status(selected, scene_id, dict(session), dict(world))
        summary = ""
        if isinstance(travel_view, dict):
            summary = str(travel_view.get("primary_intention") or "")
            proposed = travel_view.get("proposed_record") if isinstance(travel_view.get("proposed_record"), dict) else {}
            summary = str(proposed.get("summary") or travel_view.get("player_facing_text") or summary)
        if selected is not None:
            label = str(selected.get("label") or selected.get("id") or "")
            summary = f"Go to {label}."
        summary_grounding = (
            assess_addressee_grounding(summary, scene=scene, world=world, session=session)
            if summary else None
        )
        summary_authority_on_original = addressee_authority_applies(
            operation="MOVE", player_text=PATROL,
        )

        rumor_ground = rumor.pop("_grounding")
        notice_ground = notice_public.pop("_grounding")
        patrol_ground = patrol_public.pop("_grounding")
        rumor_ok = (
            rumor["public_candidate_kind"] == "unique"
            and rumor["public_candidate_ids"] == ["tavern_runner"]
            and rumor_ground.get("target_id") == "tavern_runner"
            and rumor_ground.get("operation_eligibility") == "executable"
            and "which person" not in str(rumor_ground.get("clarification") or "").lower()
        )
        notice_clarifies = would_clarify(notice_authority, notice_ground)
        notice_ok = (
            step.get("operation") == "INSPECT"
            and step.get("supported") is True
            and step.get("target_id") == "notice_board"
            and notice_authority is False
            and not notice_clarifies
        )
        patrol_clarifies = would_clarify(patrol_authority, patrol_ground)
        patrol_ok = (
            travel is not None
            and travel.category.value == "EXECUTE"
            and travel.proposed_operation == "MOVE"
            and selected is not None
            and str(selected.get("target_scene_id") or "") == "old_milestone"
            and "patrol" in str(selected.get("label") or "").lower()
            and patrol_authority is False
            and not patrol_clarifies
            and availability in {"available", "blocked"}
        )
        reasons = []
        if missing_units:
            reasons.append("structured_fact_missing_from_evidence_units")
        if collapsed_pairs:
            reasons.append("adjacent_structured_facts_collapsed")
        if leakage:
            reasons.append("structured_fact_attached_to_unnamed_npc")
        if not rumor_ok:
            reasons.append("rumor_probe_missed_unique_tavern_runner")
        if not notice_ok:
            reasons.append("inspection_probe_missed_notice_board_or_clarified_a_person")
        if not patrol_ok:
            reasons.append("movement_probe_missed_authored_patrol_exit_or_clarified_a_person")
        known_defect = bool(missing_units or collapsed_pairs or leakage or notice_clarifies or patrol_clarifies)
        if (
            rumor["public_candidate_kind"] == "ambiguous"
            and set(rumor["public_candidate_ids"]) >= {"tavern_runner"}
            and len(rumor["public_candidate_ids"]) > 1
        ):
            known_defect = True
            reasons.append("rumor_probe_reproduced_multi_npc_ambiguity")
        report.update({
            "decision": "FAIL" if reasons else "PASS",
            "reasons": reasons,
            "known_pr_play_41_defect_reproduced": known_defect,
            "active_scene_id": scene_id,
            "authored_public_facts": authored_facts,
            "ai_added_public_facts": added_facts,
            "opening_seed_facts": opening_seeds,
            "journal_seed_facts": journal_seeds,
            "evidence_units": [
                {
                    "text": unit,
                    "sources": [
                        source for source, fact in structured if fact == unit
                    ] or ["prose_summary_location_or_mode"],
                }
                for unit in units
            ],
            "npc_associations": associations,
            "fact_leakage": leakage,
            "interactables": interactables,
            "exits": [
                {
                    "id": row.get("id"),
                    "label": row.get("label"),
                    "target_scene_id": row.get("target_scene_id"),
                }
                for row in exits
            ],
            "rumor_probe": {key: value for key, value in rumor.items()},
            "inspection_probe": {
                **notice_public,
                "catalog_operation": step.get("operation"),
                "catalog_supported": step.get("supported"),
                "catalog_target_id": step.get("target_id"),
                "addressee_authority_applies": notice_authority,
                "clarification_would_fire": notice_clarifies,
            },
            "movement_probe": {
                **patrol_public,
                "travel": {
                    "category": None if travel is None else travel.category.value,
                    "proposed_operation": None if travel is None else travel.proposed_operation,
                    "proposed_target": None if travel is None else travel.proposed_target,
                    "reason": None if travel is None else travel.reason,
                    "player_facing_text": None if travel is None else travel.player_facing_text,
                },
                "selected_exit": None if selected is None else {
                    "id": selected.get("id"),
                    "label": selected.get("label"),
                    "target_scene_id": selected.get("target_scene_id"),
                },
                "route_status": availability,
                "addressee_authority_applies": patrol_authority,
                "clarification_would_fire": patrol_clarifies,
                "processing_summary": summary,
                "summary_grounding": grounding_view(summary_grounding),
                "summary_does_not_replace_original_authority": summary_authority_on_original is False,
            },
        })
    except Exception as exc:
        report["decision"] = "INCONCLUSIVE"
        report["reasons"] = ["probe_could_not_observe_production_grounding"]
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)[:800]
        report["traceback"] = traceback.format_exc()[-2000:]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
        return 2
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return 0 if report["decision"] != "INCONCLUSIVE" else 3


if __name__ == "__main__":
    sys.exit(main())
