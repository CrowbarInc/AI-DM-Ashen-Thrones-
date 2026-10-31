"""Read-only prerequisites, separate from conversation assessment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.atgb.baseline import load_baseline, provenance
from tools.atgb.isolation import assert_imported_data_dir


def _contains(actual, expected):
    # Load-time shape defaults may add dictionary keys; authored lists remain exact.
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and _contains(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(_contains(a, e) for a, e in zip(actual, expected))
    return actual == expected


def check_start(*, repo: Path, data_dir: Path, imported_data_dir: Path,
                player_campaign_dir: Path, expected_location_id: str,
                session: dict, world: dict, combat: dict, log: list) -> dict:
    from game.fresh_campaign_verify import collect_fresh_campaign_violations

    failures = []
    checks = []
    def check(name, ok):
        checks.append({"check": name, "ok": bool(ok)})
        if not ok:
            failures.append(name)
    try:
        assert_imported_data_dir(imported_data_dir, data_dir, repo=repo, player_campaign_dir=player_campaign_dir)
        check("isolated_data_dir", True)
    except RuntimeError:
        check("isolated_data_dir", False)
    source, manifest = load_baseline(repo)
    marker = json.loads((data_dir / ".atgb-isolated").read_text(encoding="utf-8"))
    check("baseline_version", marker.get("baseline") == provenance())
    check("starting_location", session.get("active_scene_id") == expected_location_id)
    check("starting_scene_present", (data_dir / "scenes" / f"{expected_location_id}.json").is_file())
    for name in sorted(manifest["files"]):
        expected = json.loads((source / name).read_text(encoding="utf-8"))
        if name == "world.json":
            actual = world
            valid = _contains(actual, expected)
            actual_npcs = {n.get("id"): n for n in world.get("npcs", []) if isinstance(n, dict)}
            for npc in expected["npcs"]:
                present = actual_npcs.get(npc["id"], {})
                check(f"npc:{npc['id']}:location", present.get("location") == npc["location"])
                for topic in npc.get("topics", []):
                    check(f"npc:{npc['id']}:topic:{topic['id']}",
                          any(_contains(t, topic) for t in present.get("topics", [])))
        else:
            path = data_dir / name
            valid = path.is_file() and path.read_bytes() == (source / name).read_bytes()
        check(f"authored_baseline:{name}", valid)
    violations = collect_fresh_campaign_violations(session, world, combat, log_entries=log)
    check("fresh_runtime_and_empty_history", not violations)
    # Compare complete loaded states across initializations, ignoring generated identities/timestamps.
    def stable(value):
        if isinstance(value, dict):
            return {k: stable(v) for k, v in value.items() if k not in {"session_id", "campaign_run_id", "last_saved_at"}}
        if isinstance(value, list):
            return [stable(v) for v in value]
        return value
    state = stable({"session": session, "world": world, "combat": combat, "log": log})
    fingerprint = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    return {"ok": not failures, "baseline": provenance(), "checks": checks,
            "critical_failures": failures, "runtime_violations": violations,
            "starting_state_sha256": fingerprint,
            "unverified_conditions": [
                "Naturalness, relevance, ambiguity resolution and IC/OOC response quality require live human review.",
                "Pending questions, addressees and learned facts must arise through each scenario's own dialogue.",
                "S09 posture cues are opening/journal seeds; delivery to the player is not verified by silent reset.",
                "Absence of authored hours, price, origins or cause is not proof that a model will preserve uncertainty."]}
