"""Two normal TCP campaigns. Creation uses the public campaign APIs."""
import os
os.environ["PR74_STORAGE"] = "http_data"
os.environ["PR74_NETWORK"] = "http_network.jsonl"
import json
import statistics
from runtime import OUT, snapshot, storage
from artifacts.pr_play_67.http_harness import server
from tests.test_pr_play_71_lifecycle import byid


def main():
    rows = []
    summaries = []
    with server() as request:
        def call(path, payload=None):
            before = snapshot()
            row = request(path, payload)
            row.update(authority_before=before, authority_after=snapshot())
            rows.append(row)
            (OUT / "http_traces.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
            assert row["status"] == 200 and not row["hidden_exposures"], row
            return row["body"]

        def chat(text):
            return call("/api/chat", {"text": text})

        def act(aid):
            action = byid(aid)
            return call("/api/action", {"action_type": "exploration", "intent": action["label"], "exploration_action": {"id": aid, "type": "custom", "label": action["label"]}})

        def unchanged(before, after):
            return before["world"]["world_state"]["flags"] == after["world"]["world_state"]["flags"] and before["session"].get("discovered_clues") == after["session"].get("discovered_clues") and before["session"]["active_scene_id"] == after["session"]["active_scene_id"]

        for branch in ("survey", "report"):
            identity = call("/api/new_campaign", {})["campaign_run_id"]
            call("/api/start_campaign", {})
            chat("I examine the notice board.")
            chat("I follow the missing patrol rumor.")
            chat("I examine the weathered milestone.")
            act("patrol_" + branch)
            if branch == "report":
                chat("I return to Cinderwatch Gate.")
            follow = "Please record my survey." if branch == "survey" else "Please give the watch my patrol report."
            chat(follow)
            flag = "patrol_survey_recorded" if branch == "survey" else "patrol_guards_warned"
            assert storage.load_world()["world_state"]["flags"][flag]
            record = {}
            if branch == 'report':
                npc = chat('Is anyone sitting alone nearby?')
                record['npc_attempt'] = npc['gm_output']['player_facing_text']
                chat('I follow the missing patrol rumor.')
            for text in ['Describe the stone surface.', 'Is there anything nearby I could sit on?', 'I examine the stone seat.']:
                before = snapshot()
                body = chat(text)
                record[text] = body['gm_output']['player_facing_text']
            from game.bounded_improvisation import controlled_facts
            entries = controlled_facts(storage.load_session())
            assert len(entries) == 2
            obj = next(e for e in entries if e['family'] == 'object')
            assert len(obj['interactions']) == 1
            saved = call('/api/snapshots', {'label': branch})['snapshot']['id']
            transcript = call('/api/log')
            call('/api/new_campaign', {})
            assert controlled_facts(storage.load_session()) == []
            call('/api/snapshots/load', {'snapshot_id': saved})
            assert call('/api/log') == transcript
            assert controlled_facts(storage.load_session()) == entries
            body = chat('I examine it again.')
            assert 'ordinary' in body['gm_output']['player_facing_text'].lower()
            after = controlled_facts(storage.load_session())
            assert [e['id'] for e in after] == [e['id'] for e in entries]
            assert len(next(e for e in after if e['id'] == obj['id'])['interactions']) == 2
            before = snapshot()
            chat('Is it magical?')
            assert snapshot() == before
            summaries.append({'branch': branch, 'identity': identity, 'snapshot_id': saved,
                              'entity_id': obj['id'], 'resumed': True, 'texts': record,
                              'npc_creation': 'deferred' if branch == 'report' else 'not requested'})
    durations = [row["http_ms"] for row in rows]
    summary = {
        "campaigns": summaries,
        "requests": len(rows),
        "mean_http_ms": statistics.mean(durations),
        "median_http_ms": statistics.median(durations),
        "max_http_ms": max(durations),
        "provider_requests": 0,
        "provider_tokens": 0,
        "hidden_exposures": sum(bool(row["hidden_exposures"]) for row in rows),
    }
    (OUT / "http_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
