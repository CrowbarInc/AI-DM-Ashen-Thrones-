from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import game.api as api_mod
import game.storage as st
from game.api import app


ROOT = Path(__file__).resolve().parents[1]
SCENES_DIR = ROOT / "data" / "scenes"
VISIBLE_FACT_LIMIT = 12
RUNTIME_RESULT_RE = re.compile(
    r"\b("
    r"upon closer inspection|examining|reveals?|suggests?|indicat(?:e|es|ing)|"
    r"appears? to have|has recently|have recently|after you|as you|"
    r"dead drop|footprints?|disturbed crates?|Galinor|Lord Aldric|Lirael"
    r")\b",
    re.IGNORECASE,
)


def _norm_fact(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def _scene_files_digest(scene_dir: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(scene_dir.glob("*.json"))
    }


def _runtime_tmp_dir() -> Path:
    path = ROOT / "artifacts" / "scene_canon_hygiene_runtime" / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path


def _patch_data_dir_from_repo(base: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data_dir = base / "data"
    scenes_dir = data_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    for src in SCENES_DIR.glob("*.json"):
        shutil.copy2(src, scenes_dir / src.name)
    monkeypatch.setattr(st, "BASE_DIR", base)
    monkeypatch.setattr(st, "DATA_DIR", data_dir)
    monkeypatch.setattr(st, "SCENES_DIR", scenes_dir)
    monkeypatch.setattr(st, "CHARACTER_PATH", data_dir / "character.json")
    monkeypatch.setattr(st, "CAMPAIGN_PATH", data_dir / "campaign.json")
    monkeypatch.setattr(st, "SESSION_PATH", data_dir / "session.json")
    monkeypatch.setattr(st, "WORLD_PATH", data_dir / "world.json")
    monkeypatch.setattr(st, "COMBAT_PATH", data_dir / "combat.json")
    monkeypatch.setattr(st, "CONDITIONS_PATH", data_dir / "conditions.json")
    monkeypatch.setattr(st, "SESSION_LOG_PATH", data_dir / "session_log.jsonl")


def test_scene_visible_facts_are_canon_hygienic() -> None:
    failures: list[str] = []
    for path in sorted(SCENES_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        scene = payload.get("scene") if isinstance(payload.get("scene"), dict) else {}
        facts = scene.get("visible_facts") if isinstance(scene.get("visible_facts"), list) else []
        if len(facts) > VISIBLE_FACT_LIMIT:
            failures.append(f"{path.name}: {len(facts)} visible_facts exceeds {VISIBLE_FACT_LIMIT}")
        seen: set[str] = set()
        for fact in facts:
            if not isinstance(fact, str):
                failures.append(f"{path.name}: non-string visible_fact {fact!r}")
                continue
            norm = _norm_fact(fact)
            if norm in seen:
                failures.append(f"{path.name}: duplicate visible_fact {fact!r}")
            seen.add(norm)
            if RUNTIME_RESULT_RE.search(fact):
                failures.append(f"{path.name}: runtime/result phrasing in visible_fact {fact!r}")
    assert not failures, "\n".join(failures)


def test_scene_opening_selector_fails_closed_without_seed_or_spine_facts() -> None:
    from game.opening_visible_fact_selection import select_opening_narration_visible_facts

    assert (
        select_opening_narration_visible_facts(
            {
                "id": "polluted",
                "visible_facts": [
                    "Upon closer inspection, faint footprints lead away from a dead drop.",
                    "Rain beads on the gate stones.",
                ],
            }
        )
        == []
    )


def test_runtime_scene_update_path_refuses_canonical_scene_visible_fact_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = _runtime_tmp_dir()
    _patch_data_dir_from_repo(base, monkeypatch)
    session = st.load_session()
    world = st.load_world()
    combat = st.load_combat()
    canon = st.load_scene("frontier_gate")

    with pytest.raises(RuntimeError, match="Canonical scene mutation attempted"):
        api_mod._apply_post_gm_updates(
            {"scene_update": {"visible_facts_add": ["Runtime clue belongs in an overlay."]}},
            canon,
            session,
            world,
            combat,
            {"kind": "observe"},
        )


def test_campaign_start_and_playthrough_do_not_modify_scene_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = _runtime_tmp_dir()
    _patch_data_dir_from_repo(base, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)

    def fake_gpt(*_args, **_kwargs):
        return {
            "player_facing_text": "Rain needles the gate as guards hold the line.",
            "scene_update": {
                "visible_facts_add": [
                    "Runtime-only observation from this playthrough belongs in the overlay."
                ]
            },
            "tags": [],
        }

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    before = _scene_files_digest(st.SCENES_DIR)

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        assert client.post("/api/start_campaign").status_code == 200
        assert client.post("/api/chat", json={"text": "I scan the notice board."}).status_code == 200

    assert _scene_files_digest(st.SCENES_DIR) == before
    canon = st.load_scene("frontier_gate")
    assert "Runtime-only observation from this playthrough belongs in the overlay." not in canon["scene"]["visible_facts"]
    session = st.load_session()
    effective = st.get_effective_scene(session, "frontier_gate")
    assert "Runtime-only observation from this playthrough belongs in the overlay." in effective["scene"]["visible_facts"]
