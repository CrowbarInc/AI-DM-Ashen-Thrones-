"""Print the fields needed to classify the PR-PLAY-41 clarifications. No provider calls."""
from __future__ import annotations

import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[2] / "artifacts" / "atgb" / "pr_play_41" / "live" / "20261102T110016Z-47c71d381798"


def rows(label):
    path = RUN / label / "persistent" / "session_log.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    for label in ("opening", "turns/T1/after", "turns/T2/after", "turns/T3/after", "turns/T4/after"):
        last = rows(label)[-1]
        print("=" * 20, label, "keys", sorted(last))
        resolution = last.get("resolution") if isinstance(last.get("resolution"), dict) else {}
        meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
        decision = meta.get("conversational_decision") if isinstance(meta.get("conversational_decision"), dict) else {}
        auth = decision.get("authorization") if isinstance(decision.get("authorization"), dict) else {}
        print("player_input", last.get("player_input"))
        print("primary", decision.get("primary_intention"))
        print("reason", decision.get("reason"))
        print("proposed", decision.get("proposed_operation"), decision.get("proposed_target"))
        print("auth_text", auth.get("player_text"))
        print("auth_prov", auth.get("authority_provenance"), auth.get("target_resolution"), auth.get("target_provenance"), auth.get("direct_address"))
        print("choices", auth.get("choices"))
        print("conflict", auth.get("conflict_details"))
        live = meta.get("live_chat_interpretation") if isinstance(meta.get("live_chat_interpretation"), dict) else {}
        record = live.get("record") if isinstance(live.get("record"), dict) else {}
        components = record.get("action_components")
        print("live_status", live.get("status"), live.get("reason"), live.get("interpretation_status"))
        print("components", components)
        bridge = meta.get("stored_interpretation_bridge")
        print("bridge", bridge)


if __name__ == "__main__":
    main()
