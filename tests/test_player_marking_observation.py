"""Player-facing marking observation and publication consistency."""
import hashlib
import json
import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from game import api, storage
from game import object_marking as marking
from game.marking_observation import recognize_observation
from tests.pr_play_79df3_harness import seed_gate
from tests.test_grounded_marking_action import ACTION, WARNING, _equip, _markings
from tests.test_pr_play_post_npc_handoff import _env

OBSERVE = "I examine the writing on my sleeve."
SECRET = "Concealed signal for the cellar."
RESTRICTED = "Restricted route past the mill."
REMOVED = "Removed line about the ferry."


@pytest.fixture
def client(tmp_path, monkeypatch):
    _env(monkeypatch)
    from tests.helpers.storage_isolation import install

    install(tmp_path)
    seed_gate(tmp_path, monkeypatch)
    http = TestClient(api.app)
    http.__enter__()
    try:
        yield http
    finally:
        http.__exit__(None, None, None)


def _post(client, text, request_id):
    response = client.post(
        "/api/chat?ui_mode=player",
        json={"text": text, "client_request_id": request_id},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    visible = str((body.get("gm_output") or {}).get("player_facing_text") or "")
    log = storage.load_log()
    resolution = log[-1].get("resolution") if log else {}
    meta = resolution.get("metadata") if isinstance(resolution, dict) else {}
    publication = storage.load_session().get("last_publication") or {}
    return {
        "visible": visible,
        "body": body,
        "meta": meta if isinstance(meta, dict) else {},
        "success": resolution.get("success") if isinstance(resolution, dict) else None,
        "publication": publication.get("visible") if isinstance(publication, dict) else None,
        "raw": json.dumps(body),
    }


def _summary(result, key):
    return result["meta"].get(key) or {}


def _add(content, request_id, *, visibility=None, scope=None):
    character = storage.load_character()
    session = storage.load_session()
    row = next(item for item in character["inventory"] if item["id"] == "travel_coat")
    request = {
        "version": 1,
        "operation": "add_marking",
        "campaign_run_id": session["campaign_run_id"],
        "character_id": character["id"],
        "instance_id": row["instance_id"],
        "request_id": request_id,
        "expected_revision": row["revision"],
        "content": content,
        "source": {"kind": "explicit_literal", "reference": "observation-fixture"},
        "authorization": {
            "caller_id": "observation-fixture",
            "decision_id": request_id + "-decision",
            "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "preconditions": {key: "fixture:" + key for key in marking.PRECONDITIONS},
            "mechanics": "not_applicable",
        },
    }
    request["request_digest"] = marking.request_digest(request)
    added = api.add_inventory_object_marking(request)
    assert added["status"] == "applied", added
    if visibility:
        classified = {"classification": visibility}
        if scope:
            classified["scope"] = scope
        character = storage.load_character()
        row = next(item for item in character["inventory"] if item["id"] == "travel_coat")
        vis = {
            "version": 1,
            "operation": "set_marking_visibility",
            "campaign_run_id": session["campaign_run_id"],
            "character_id": character["id"],
            "instance_id": row["instance_id"],
            "modification_id": added["modification_id"],
            "expected_revision": row["revision"],
            "request_id": request_id + "-visibility",
            "visibility": classified,
            "authorization": {
                "caller_id": "observation-fixture",
                "decision_id": request_id + "-class",
                "mechanics": "not_applicable",
                "preconditions": {key: "fixture:" + key for key in marking.VISIBILITY_PRECONDITIONS},
            },
        }
        vis["request_digest"] = marking.request_digest(vis)
        result = api.set_marking_visibility(vis, authorization=marking._establish_visibility_authorization(vis))
        assert result["status"] in {"applied", "no_change"}, result
    return added


def _remove(modification_id, request_id):
    character = storage.load_character()
    session = storage.load_session()
    row = next(item for item in character["inventory"] if item["id"] == "travel_coat")
    request = {
        "version": 1,
        "operation": "remove_marking",
        "campaign_run_id": session["campaign_run_id"],
        "character_id": character["id"],
        "instance_id": row["instance_id"],
        "modification_id": modification_id,
        "expected_revision": row["revision"],
        "request_id": request_id,
        "authorization": {
            "caller_id": "observation-fixture",
            "decision_id": request_id + "-decision",
            "mechanics": "not_applicable",
            "preconditions": {key: "fixture:" + key for key in marking.REMOVAL_PRECONDITIONS},
        },
    }
    request["request_digest"] = marking.request_digest(request)
    removed = api.remove_inventory_object_marking(request)
    assert removed["status"] == "applied", removed
    return removed


def test_negative_language_is_not_marking_observation():
    for text in (
        "I remember what the warning said.",
        "I tell him about the writing.",
        "I write another warning.",
        "I erase the writing.",
        "I inspect the patrol's behavior.",
        "I examine the road.",
        "I look at the gate.",
        "I read the notice.",
    ):
        assert recognize_observation(text) is None


def test_http_observation_survives_reload_removal_and_snapshots(client, tmp_path):
    from game.provider_budget import snapshot as provider_snapshot

    _equip("pf1e")
    providers = len(provider_snapshot()["records"])
    before = storage.CHARACTER_PATH.read_bytes()
    snapshot_before = storage.create_snapshot("S0 before marking")
    marked = _post(client, ACTION, "observe-loop-mark")
    assert WARNING in marked["visible"]
    assert "The marking is on it now." in marked["visible"]
    assert _summary(marked, "marking_action").get("publication_matches_commit") is True
    assert marked["success"] is True
    assert len(_markings()[2]) == 1
    character_hash = hashlib.sha256(storage.CHARACTER_PATH.read_bytes()).hexdigest()
    observed = _post(client, OBSERVE, "observe-loop-read")
    assert observed["visible"] == f"On the sleeve, the visible writing reads: {WARNING}"
    assert observed["publication"] == observed["visible"]
    assert _summary(observed, "marking_observation").get("publication_matches_commit") is True
    assert storage.CHARACTER_PATH.read_bytes() != before
    assert hashlib.sha256(storage.CHARACTER_PATH.read_bytes()).hexdigest() == character_hash
    assert len(_markings()[2]) == 1
    snapshot_marked = storage.create_snapshot("S1 after marking")
    script = (
        "import json,os,sys\n"
        "os.environ['ASHEN_DATA_DIR']=sys.argv[1]\n"
        "os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'\n"
        "os.environ['ASHEN_DISABLE_LIVE_INTERPRETATION']='1'\n"
        "os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT']='1'\n"
        "from fastapi.testclient import TestClient\n"
        "from game.api import app\n"
        "from game.provider_budget import snapshot as provider_snapshot\n"
        "with TestClient(app) as http:\n"
        "    response=http.post('/api/chat?ui_mode=player', json={'text':sys.argv[2],'client_request_id':'reload-observe'})\n"
        "print(json.dumps({'status':response.status_code,'text':response.json()['gm_output']['player_facing_text'],'providers':len(provider_snapshot()['records'])}))\n"
    )
    reloaded = subprocess.run(
        [sys.executable, "-c", script, str(storage.DATA_DIR), OBSERVE],
        cwd=os.getcwd(), check=True, capture_output=True, text=True,
    )
    payload = json.loads(reloaded.stdout.strip().splitlines()[-1])
    assert payload["status"] == 200
    assert payload["text"] == observed["visible"]
    assert hashlib.sha256(storage.CHARACTER_PATH.read_bytes()).hexdigest() == character_hash
    modification_id = _markings()[2][0]["modification_id"]
    _remove(modification_id, "observe-loop-remove")
    removed = _post(client, OBSERVE, "observe-loop-after-removal")
    assert WARNING not in removed["visible"]
    assert removed["visible"] == "You look at the sleeve. No writing is visible there."
    assert "concealed" not in removed["visible"].casefold()
    snapshot_removed = storage.create_snapshot("S2 after removal")
    assert storage.load_snapshot(snapshot_marked["id"])
    restored = _post(client, "What does my coat say?", "observe-loop-s1")
    assert WARNING in restored["visible"]
    assert SECRET not in restored["visible"]
    assert storage.load_snapshot(snapshot_before["id"])
    empty = _post(client, OBSERVE, "observe-loop-s0")
    assert WARNING not in empty["visible"]
    assert empty["visible"] == "You look at the sleeve. No writing is visible there."
    assert storage.load_snapshot(snapshot_removed["id"])
    again = _post(client, "Is the warning still written on my sleeve?", "observe-loop-s2")
    assert WARNING not in again["visible"]
    assert again["visible"] == "You look at the sleeve. No writing is visible there."
    assert len(provider_snapshot()["records"]) == providers
    evidence = os.environ.get("ASHEN_TEST_EVIDENCE_DIR")
    if evidence:
        path = os.path.join(evidence, "controlled_http_loop.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({
                "mark": marked["visible"],
                "observe": observed["visible"],
                "reload": payload,
                "removed": removed["visible"],
                "snapshot_marked": restored["visible"],
                "snapshot_before": empty["visible"],
                "snapshot_removed": again["visible"],
                "character_hash": character_hash,
                "providers": len(provider_snapshot()["records"]),
            }, handle, indent=2)


def test_mixed_visibility_http_discloses_only_the_visible_mark(client):
    _equip()
    visible = _add(WARNING, "visible-mark", visibility="visible")
    _add(SECRET, "concealed-mark", visibility="concealed")
    _add(RESTRICTED, "restricted-mark", visibility="restricted", scope="gm-only")
    removed = _add(REMOVED, "removed-mark", visibility="visible")
    _remove(removed["modification_id"], "remove-mixed")
    result = _post(client, OBSERVE, "mixed-observe")
    assert WARNING in result["visible"]
    for hidden in (SECRET, RESTRICTED, REMOVED, visible["modification_id"], "request_id", "gm-only"):
        assert hidden not in result["visible"]
        assert hidden not in result["raw"]
    state = client.get("/api/state?ui_mode=player")
    assert SECRET not in state.text and RESTRICTED not in state.text and REMOVED not in state.text
    assert "concealed" not in result["visible"].casefold()
    assert storage.CHARACTER_PATH.read_bytes()
    again = _post(client, "I can clearly see the hidden writing on my sleeve.", "mixed-claim")
    assert SECRET not in again["visible"] and RESTRICTED not in again["visible"]


def test_paraphrases_and_false_targets(client):
    _equip()
    _post(client, ACTION, "paraphrase-mark")
    cloth = _post(client, "I look over the markings on the cloth.", "paraphrase-cloth")
    assert WARNING in cloth["visible"]
    paper = _post(client, "I inspect the inscription on the paper.", "paraphrase-paper")
    assert paper["visible"] == "You look at the page. No writing is visible there."
    assert WARNING not in paper["visible"]
    missing = _post(client, "I examine the writing on my collar.", "paraphrase-collar")
    assert missing["visible"] == "No established object matches what you tried to examine."
    pronoun = _post(client, "Is the warning still written there?", "paraphrase-there")
    assert pronoun["visible"] == "Say which object you mean."
    assert WARNING not in pronoun["visible"]
    before = storage.CHARACTER_PATH.read_bytes()
    for text, request_id in (
        ("I remember what the warning said.", "neg-remember"),
        ("I tell him about the writing.", "neg-tell"),
        ("I erase the writing.", "neg-erase"),
        ("I inspect the patrol's behavior.", "neg-patrol"),
        ("I examine the road.", "neg-road"),
    ):
        result = _post(client, text, request_id)
        assert _summary(result, "marking_observation") == {}
        assert SECRET not in result["visible"]
    assert storage.CHARACTER_PATH.read_bytes() == before


@pytest.mark.parametrize("ruleset", ["pf1e", "rules_light", "science_fiction"])
def test_observation_ignores_ruleset_extension(client, ruleset):
    _equip(ruleset)
    _post(client, ACTION, "ruleset-mark-" + ruleset)
    visible = _post(client, OBSERVE, "ruleset-read-" + ruleset)["visible"].casefold()
    assert WARNING.casefold() in visible
    for term in ("perception", "difficulty class", "spell", "linguistics"):
        assert term not in visible
    assert storage.load_character()["ruleset_extension"]["id"] == ruleset


def test_authority_boundaries_do_not_disclose(client):
    _equip()
    _add(SECRET, "boundary-secret", visibility="concealed")
    legacy = storage.load_character()
    row = legacy["inventory"][0]
    row["markings"] = [{
        "version": 1, "type": "add_marking", "modification_id": row["markings"][0]["modification_id"],
        "applied_revision": row["markings"][0]["applied_revision"], "content": SECRET,
        "source": row["markings"][0]["source"], "authorization": row["markings"][0]["authorization"],
        "request_id": row["markings"][0]["request_id"], "request_digest": row["markings"][0]["request_digest"],
    }]
    row.pop("marking_visibility", None)
    storage.save_character(legacy)
    legacy_read = _post(client, OBSERVE, "legacy-read")
    assert SECRET not in legacy_read["visible"]
    assert legacy_read["visible"] == "You look at the sleeve. No writing is visible there."
    character = storage.load_character()
    character["inventory"][0]["usable"] = False
    storage.save_character(character)
    blocked = _post(client, OBSERVE, "blocked-read")
    assert blocked["visible"] == "You cannot see that surface from here."
    assert SECRET not in blocked["visible"]
    character = storage.load_character()
    character["inventory"][0]["usable"] = True
    twin = json.loads(json.dumps(character["inventory"][0]))
    twin["id"] = "second_coat"
    twin["instance_id"] = "11111111-1111-4111-8111-111111111111"
    twin["provenance"] = dict(twin["provenance"], source={"host": "character.inventory", "legacy_id": "second_coat"})
    character["inventory"].insert(0, twin)
    storage.save_character(character)
    ambiguous = _post(client, OBSERVE, "ambiguous-read")
    assert ambiguous["visible"] == "More than one established object matches. Name the one you mean."
    assert SECRET not in ambiguous["visible"]


def test_publication_faults_keep_one_committed_mark(client, monkeypatch):
    import game.immutable_valid_response as immutable

    _equip()

    def install(sealer):
        monkeypatch.setattr(immutable, "seal_host_speech", sealer)

    def unchanged(gm, *, text, **_kwargs):
        gm["player_facing_text"] = text
        return gm

    def paraphrase(gm, *, text, **_kwargs):
        gm["player_facing_text"] = text.replace("You copy", "You write")
        return gm

    def contradictory(gm, **_kwargs):
        gm["player_facing_text"] = "Nothing was written. The sleeve is blank."
        return gm

    def empty(gm, **_kwargs):
        gm["player_facing_text"] = " "
        return gm

    def explode(*_args, **_kwargs):
        raise RuntimeError("seal failed")

    install(unchanged)
    same = _post(client, ACTION, "seal-same")
    assert same["visible"].startswith("You copy")
    assert WARNING in same["visible"]
    assert _summary(same, "marking_action")["publication_disposition"] == "unchanged"
    assert len(_markings()[2]) == 1
    install(paraphrase)
    paraphrased = _post(client, "I copy the name onto the paper using the charcoal.", "seal-paraphrase")
    assert paraphrased["visible"].startswith("You write")
    assert "The name is Mara Voss." in paraphrased["visible"]
    assert _summary(paraphrased, "marking_action")["publication_disposition"] == "paraphrase"
    install(contradictory)
    denied = _post(client, "I jot the name onto the page with the charcoal.", "seal-contradict")
    assert "Nothing was written" not in denied["visible"]
    assert "The name is Mara Voss." in denied["visible"]
    assert denied["success"] is True
    assert _summary(denied, "marking_action")["publication_disposition"] == "rejected_fallback"
    assert _summary(denied, "marking_action")["publication_matches_commit"] is True
    install(empty)
    blank = _post(client, "I write the name onto the paper with the charcoal.", "seal-empty")
    assert "The name is Mara Voss." in blank["visible"]
    assert _summary(blank, "marking_action")["publication_disposition"] == "empty"
    install(explode)
    failed = _post(client, "I scribble the warning onto the page using the mud.", "seal-raise")
    assert failed["success"] is True
    assert WARNING in failed["visible"]
    assert _summary(failed, "marking_action")["publication_disposition"] == "sealer_exception"
    from game.integrated_play import _LANES

    _LANES.clear()
    retry = _post(client, "I scribble the warning onto the page using the mud.", "seal-raise")
    assert WARNING in retry["visible"]
    paper = next(item for item in storage.load_character()["inventory"] if item["id"] == "loose_paper")
    assert [mark["content"] for mark in paper.get("markings") or []].count(WARNING) == 1
    install(unchanged)

    def persist_fails(*_args, **_kwargs):
        raise RuntimeError("session save failed")

    monkeypatch.setattr(api, "save_session", persist_fails)
    persisted = client.post(
        "/api/chat?ui_mode=player",
        json={"text": "I copy the name onto my sleeve using the available mud.", "client_request_id": "seal-persist"},
    )
    assert persisted.status_code == 200
    assert "The name is Mara Voss." in persisted.json()["gm_output"]["player_facing_text"]
    coat = next(item for item in storage.load_character()["inventory"] if item["id"] == "travel_coat")
    assert [mark["content"] for mark in coat.get("markings") or []].count("The name is Mara Voss.") == 1
    _LANES.clear()
    monkeypatch.setattr(api, "save_session", storage.save_session)
    replay = _post(client, "I copy the name onto my sleeve using the available mud.", "seal-persist")
    assert "The name is Mara Voss." in replay["visible"]
    coat = next(item for item in storage.load_character()["inventory"] if item["id"] == "travel_coat")
    assert [mark["content"] for mark in coat.get("markings") or []].count("The name is Mara Voss.") == 1


def test_real_sealer_cannot_publish_a_denial_of_a_committed_mark(client):
    _equip()
    session = storage.load_session()
    session["clue_knowledge"]["password_clue"] = {
        "state": "discovered", "text": "The password is cedar.", "aliases": ["password"],
        "presentation": "explicit",
    }
    storage.save_session(session)
    result = _post(client, "I copy the password onto my sleeve using the available mud.", "password-copy")
    assert "The password is cedar." in result["visible"]
    assert "cannot share" not in result["visible"].casefold()
    assert result["success"] is True
    assert _summary(result, "marking_action")["publication_matches_commit"] is True
    assert _markings()[2][-1]["content"] == "The password is cedar."
    observed = _post(client, OBSERVE, "password-read")
    assert observed["visible"] == "On the sleeve, the visible writing reads: The password is cedar."
    assert "cannot share" not in observed["visible"].casefold()
