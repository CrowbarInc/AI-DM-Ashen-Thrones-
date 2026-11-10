"""Player-facing removal of one established visible marking."""
import json
import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.marking_removal import recognize_removal, resolve_removal
from tests.pr_play_79df3_harness import seed_gate
from tests.test_grounded_marking_action import ACTION, NAME, WARNING, _equip, _identity, _markings, _surface
from tests.test_player_marking_observation import RESTRICTED, SECRET, _add, _remove
from tests.test_pr_play_post_npc_handoff import _env

WIPE = "I wipe the warning off my sleeve."
OBSERVE = "I examine the writing on my sleeve."
CLOTH = {
    "wipe": {"resource": "none", "surfaces": ["cloth"]},
    "rub": {"resource": "none", "surfaces": ["cloth"]},
    "clean": {"resource": "none", "surfaces": ["cloth"]},
    "wash": {"resource": "water", "surfaces": ["cloth"]},
}
PAPER = {"rub": {"resource": "none", "surfaces": ["paper"]}}


@pytest.fixture
def client(tmp_path, monkeypatch):
    _env(monkeypatch)
    from tests.helpers.storage_isolation import install

    install(tmp_path)
    seed_gate(tmp_path, monkeypatch)
    http = TestClient(__import__("game.api", fromlist=["app"]).app)
    http.__enter__()
    try:
        yield http
    finally:
        http.__exit__(None, None, None)


def _post(client, text, request_id):
    response = client.post(
        "/api/chat?ui_mode=player",
        json={"text": text, "client_request_id": "rm-" + request_id},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    visible = str((body.get("gm_output") or {}).get("player_facing_text") or "")
    log = storage.load_log()
    resolution = log[-1].get("resolution") if log else {}
    meta = resolution.get("metadata") if isinstance(resolution, dict) else {}
    return {
        "visible": visible,
        "body": body,
        "meta": meta if isinstance(meta, dict) else {},
        "success": resolution.get("success") if isinstance(resolution, dict) else None,
        "raw": json.dumps(body),
    }


def _summary(result):
    return result["meta"].get("marking_removal") or {}


def _arm(item_id, methods):
    character = storage.load_character()
    row = next(item for item in character["inventory"] if item["id"] == item_id)
    row["marking_medium"]["removal"] = {"methods": methods}
    storage.save_character(character)


def _active(item_id="travel_coat"):
    _character, row, marks = _markings(item_id)
    return row, [mark["content"] for mark in marks]


def _ready(ruleset="rules_light"):
    _equip(ruleset)
    _arm("carried_mud", CLOTH)
    _arm("charcoal_stub", PAPER)


def test_recognition_rejects_other_actions():
    rejected = (
        "I erase the memory from my mind.",
        "I remove the coat.",
        "I clean my sword.",
        "I wipe my hands.",
        "I tell him to erase the writing.",
        "I examine whether the writing was removed.",
        "I inspect the erased writing.",
        "I copy the warning onto my sleeve using the mud.",
        "I examine the writing on my sleeve.",
        "I wipe the dust off my sleeve.",
    )
    for text in rejected:
        assert recognize_removal(text) is None, text
    notes = recognize_removal("I remove the warning from my notes.")
    assert notes["operation"] == "remove_marking"
    assert notes["target_phrase"] == "my notes"
    sleeve = recognize_removal("I rub away the charcoal writing.")
    assert sleeve["method"] == "rub" and sleeve["target_phrase"] == ""
    board = recognize_removal("I erase the message on the board.")
    assert board["marking_phrase"] == "message" and board["target_phrase"] == "the board"


def test_http_lifecycle_persists_reloads_and_restores(client):
    from game.provider_budget import snapshot as provider_snapshot

    _ready("pf1e")
    providers = len(provider_snapshot()["records"])
    before_id = _active()[0]["instance_id"]
    snapshot_before = storage.create_snapshot("S0 before marking")
    marked = _post(client, ACTION, "removal-loop-mark")
    assert WARNING in marked["visible"]
    assert _summary(marked) == {}
    observed = _post(client, OBSERVE, "removal-loop-read")
    assert observed["visible"] == f"On the sleeve, the visible writing reads: {WARNING}"
    snapshot_marked = storage.create_snapshot("S1 after marking")
    revision = _active()[0]["revision"]
    removed = _post(client, WIPE, "removal-loop-wipe")
    assert removed["success"] is True
    assert "no longer" in removed["visible"].casefold()
    assert WARNING in removed["visible"]
    assert "request_id" not in removed["visible"] and "modification_id" not in removed["visible"]
    assert _summary(removed)["outcome"] == "committed"
    assert _summary(removed)["publication_matches_commit"] is True
    row, contents = _active()
    assert contents == []
    assert row["instance_id"] == before_id
    assert row["revision"] == revision + 1
    assert storage.load_character()["ruleset_extension"]["id"] == "pf1e"
    receipts = storage.load_character()["object_marking_receipts"]["entries"]
    assert any(item.get("operation") == "remove_marking" for item in receipts.values())
    assert any(item.get("operation") != "remove_marking" and "resulting_revision" in item for item in receipts.values())
    quiet = _post(client, OBSERVE, "removal-loop-after")
    assert WARNING not in quiet["visible"]
    assert quiet["visible"] == "You look at the sleeve. No writing is visible there."
    snapshot_removed = storage.create_snapshot("S2 after removal")
    script = (
        "import json,os,sys\n"
        "os.environ['ASHEN_DATA_DIR']=sys.argv[1]\n"
        "os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'\n"
        "os.environ['ASHEN_DISABLE_LIVE_INTERPRETATION']='1'\n"
        "os.environ['ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT']='1'\n"
        "from fastapi.testclient import TestClient\n"
        "from game.api import app\n"
        "from game import storage\n"
        "from game.provider_budget import snapshot as provider_snapshot\n"
        "with TestClient(app) as http:\n"
        "    seen=http.post('/api/chat?ui_mode=player', json={'text':sys.argv[2],'client_request_id':'reload-observe'})\n"
        "    again=http.post('/api/chat?ui_mode=player', json={'text':sys.argv[3],'client_request_id':sys.argv[4]})\n"
        "    row=next(item for item in storage.load_character()['inventory'] if item['id']=='travel_coat')\n"
        "print(json.dumps({'seen':seen.json()['gm_output']['player_facing_text'],'again':again.json()['gm_output']['player_facing_text'],'revision':row['revision'],'marks':[mark['content'] for mark in row.get('markings') or []],'providers':len(provider_snapshot()['records'])}))\n"
    )
    reloaded = subprocess.run(
        [sys.executable, "-c", script, str(storage.DATA_DIR), OBSERVE, WIPE, "rm-removal-loop-wipe"],
        cwd=os.getcwd(), check=True, capture_output=True, text=True,
    )
    payload = json.loads(reloaded.stdout.strip().splitlines()[-1])
    assert payload["seen"] == quiet["visible"]
    assert "no longer" in payload["again"].casefold()
    assert payload["marks"] == []
    assert payload["revision"] == row["revision"]
    assert payload["providers"] == 0
    from game.integrated_play import _LANES

    _LANES.clear()
    replay = _post(client, WIPE, "removal-loop-wipe")
    assert _active()[0]["revision"] == row["revision"]
    assert _summary(replay)["outcome"] == "replay"
    assert storage.load_snapshot(snapshot_marked["id"])
    restored = _post(client, OBSERVE, "removal-loop-s1")
    assert restored["visible"] == observed["visible"]
    assert storage.load_snapshot(snapshot_before["id"])
    empty = _post(client, OBSERVE, "removal-loop-s0")
    assert WARNING not in empty["visible"]
    assert empty["visible"] == "You look at the sleeve. No writing is visible there."
    assert storage.load_snapshot(snapshot_removed["id"])
    final = _post(client, "Is the warning still written on my sleeve?", "removal-loop-s2")
    assert WARNING not in final["visible"]
    assert len(provider_snapshot()["records"]) == providers


def test_mixed_and_ambiguous_markings_remove_only_the_selected_one(client):
    _ready()
    _post(client, ACTION, "mixed-mark")
    _add(SECRET, "mixed-secret", visibility="concealed")
    _add(RESTRICTED, "mixed-restricted", visibility="restricted", scope="gm-only")
    removed = _add("Removed line about the ferry.", "mixed-old", visibility="visible")
    _remove(removed["modification_id"], "mixed-old-remove")
    _post(client, "I copy the name onto my sleeve using the available mud.", "mixed-name")
    ambiguous = _post(client, "I erase the writing off my sleeve.", "mixed-ambiguous")
    assert "more than one marking" in ambiguous["visible"].casefold()
    assert SECRET not in ambiguous["visible"] and RESTRICTED not in ambiguous["visible"]
    assert set(_active()[1]) == {WARNING, NAME, SECRET, RESTRICTED}
    wiped = _post(client, WIPE, "mixed-wipe")
    assert _summary(wiped)["outcome"] == "committed"
    assert SECRET not in wiped["visible"] and RESTRICTED not in wiped["visible"]
    assert "concealed" not in wiped["visible"].casefold()
    assert set(_active()[1]) == {SECRET, RESTRICTED, NAME}
    seen = _post(client, OBSERVE, "mixed-read")
    assert NAME in seen["visible"] and WARNING not in seen["visible"]
    assert SECRET not in seen["visible"] and RESTRICTED not in seen["visible"]
    assert "concealed" not in seen["visible"].casefold()


def test_identical_request_does_not_pick_one_of_two_copies(client):
    _ready()
    _post(client, ACTION, "copy-a")
    _post(client, ACTION, "copy-b")
    result = _post(client, WIPE, "copy-ambiguous")
    assert "more than one marking" in result["visible"].casefold()
    assert _active()[1] == [WARNING, WARNING]
    assert _summary(result)["outcome"] != "committed"


def test_paraphrases_depend_on_established_facts(client):
    _ready()
    _post(client, ACTION, "phrase-mark")
    wiped = _post(client, "I try to wipe the warning off the coat sleeve.", "phrase-wipe")
    assert WARNING in wiped["visible"] and "no longer" in wiped["visible"].casefold()
    _post(client, "Use the charcoal to write the name on the paper.", "phrase-paper")
    rubbed = _post(client, "I rub the name off the paper.", "phrase-rub")
    assert NAME in rubbed["visible"] and "no longer" in rubbed["visible"].casefold()
    assert _active("loose_paper")[1] == []
    before = storage.CHARACTER_PATH.read_bytes()
    board = _post(client, "I erase the message on the board.", "phrase-board")
    ink = _post(client, "I clean the ink from the cloth.", "phrase-ink")
    paper = _post(client, "I remove the writing from the paper.", "phrase-remove-paper")
    notes = _post(client, "I remove the warning from my notes.", "phrase-notes")
    for result in (board, ink, paper, notes):
        assert "nothing was removed" in result["visible"].casefold()
        assert result["success"] is not True
    assert storage.CHARACTER_PATH.read_bytes() == before
    for text, request_id in (
        ("I remove my coat.", "phrase-coat"),
        ("I wipe my hands.", "phrase-hands"),
        ("I erase the memory from my mind.", "phrase-memory"),
        ("I tell him to clean the board.", "phrase-tell"),
        ("I inspect the erased writing.", "phrase-inspect"),
    ):
        result = _post(client, text, request_id)
        assert _summary(result) == {}
    assert storage.CHARACTER_PATH.read_bytes() == before


def test_missing_method_resource_and_mechanics_do_not_invent(client):
    _ready()
    _post(client, ACTION, "feasibility-mark")
    _arm("carried_mud", {"rub": {"resource": "none", "surfaces": ["cloth"]}})
    denied = _post(client, WIPE, "feasibility-wipe")
    assert "not established as removable" in denied["visible"].casefold()
    assert _active()[1] == [WARNING]
    _arm("carried_mud", {"wash": {"resource": "water", "surfaces": ["cloth"]}})
    washed = _post(client, "I wash the warning off my sleeve.", "feasibility-wash")
    assert "cleaning material" in washed["visible"].casefold()
    assert _active()[1] == [WARNING]
    assert all(item["id"] != "water" for item in storage.load_character()["inventory"])
    character = storage.load_character()
    campaign_id = storage.load_session()["campaign_run_id"]
    character["inventory"].append(_identity(campaign_id, "waterskin", "Water", quantity=1, usable=True))
    storage.save_character(character)
    cleaned = _post(client, "I wash the warning off my sleeve with the water.", "feasibility-water")
    assert "no longer" in cleaned["visible"].casefold()
    assert next(item["quantity"] for item in storage.load_character()["inventory"] if item["id"] == "waterskin") == 1
    _post(client, ACTION, "feasibility-second")
    _arm("carried_mud", {"wash": {"resource": "water", "surfaces": ["cloth"], "consumption": "required"}})
    blocked = _post(client, "I wash the warning off my sleeve.", "feasibility-consume")
    assert "cannot be recorded safely" in blocked["visible"].casefold()
    assert WARNING in _active()[1]
    assert next(item["quantity"] for item in storage.load_character()["inventory"] if item["id"] == "waterskin") == 1
    character = storage.load_character()
    character["inventory"][1]["marking_medium"]["removal"]["methods"]["wipe"] = {
        "resource": "none", "surfaces": ["cloth"], "mechanics": "required",
    }
    storage.save_character(character)
    mechanics = _post(client, WIPE, "feasibility-mechanics")
    assert "rules decision" in mechanics["visible"].casefold()
    assert "difficulty class" not in mechanics["visible"].casefold()
    character = storage.load_character()
    character["inventory"][1]["marking_medium"]["removal"]["methods"]["wipe"] = {
        "resource": "none", "surfaces": ["cloth"],
    }
    character["inventory"][0]["marking_surfaces"][0]["removal_environment"] = "blocked"
    storage.save_character(character)
    environment = _post(client, WIPE, "feasibility-environment")
    assert "conditions" in environment["visible"].casefold()
    character = storage.load_character()
    character["inventory"][0]["marking_surfaces"][0].pop("removal_environment")
    character["physical_status"] = {"ordinary_removal": "unable"}
    storage.save_character(character)
    unable = _post(client, WIPE, "feasibility-unable")
    assert "not established as able" in unable["visible"].casefold()
    assert WARNING in _active()[1]


def test_concealed_marking_is_not_a_removal_target(client):
    _ready()
    hidden = _post(client, "I secretly copy the warning onto my sleeve using the available mud.", "hidden-mark")
    assert "concealed" in hidden["visible"].casefold()
    result = _post(client, "I wipe the hidden warning off my sleeve.", "hidden-wipe")
    assert "nothing was removed" in result["visible"].casefold()
    assert "keep to the north wall" not in result["visible"].casefold()
    assert "concealed" not in result["visible"].casefold()
    assert _active()[1] == [WARNING]
    other = _post(client, "I wipe the warning off the paper.", "hidden-paper")
    assert "nothing was removed" in other["visible"].casefold()
    assert _active()[1] == [WARNING]


def test_retries_conflict_and_later_revision(client):
    from game.integrated_play import _LANES

    _ready()
    _post(client, ACTION, "retry-mark")
    _post(client, "I copy the name onto my sleeve using the available mud.", "retry-name")
    _post(client, WIPE, "retry-wipe")
    assert set(_active()[1]) == {NAME}
    revision = _active()[0]["revision"]
    _LANES.clear()
    conflict = _post(client, "I wipe the name off my sleeve.", "retry-wipe")
    assert "nothing further was removed" in conflict["visible"].casefold()
    assert set(_active()[1]) == {NAME}
    assert _active()[0]["revision"] == revision
    second = _post(client, "I wipe the name off my sleeve.", "retry-name-wipe")
    assert second["success"] is True
    assert _active()[1] == []
    named_revision = _active()[0]["revision"]
    later = _post(client, ACTION, "retry-later")
    assert WARNING in _active()[1]
    later_revision = _active()[0]["revision"]
    assert later_revision > named_revision
    _LANES.clear()
    replay = _post(client, WIPE, "retry-wipe")
    assert "nothing further was removed" in replay["visible"].casefold()
    assert WARNING in _active()[1]
    assert _active()[0]["revision"] == later_revision
    gone = _post(client, "I wipe the name off my sleeve.", "retry-name-again")
    assert "nothing was removed" in gone["visible"].casefold()
    assert later["success"] is True


def test_publication_faults_do_not_restore_or_repeat_removal(client, monkeypatch):
    import game.immutable_valid_response as immutable

    _ready()
    _post(client, ACTION, "seal-mark")

    def install(sealer):
        monkeypatch.setattr(immutable, "seal_host_speech", sealer)

    def unchanged(gm, *, text, **_kwargs):
        gm["player_facing_text"] = text
        return gm

    def paraphrase(gm, *, text, **_kwargs):
        gm["player_facing_text"] = text.replace("You wipe", "You clear").replace("off the", "from the")
        return gm

    def contradictory(gm, **_kwargs):
        gm["player_facing_text"] = "The warning is still written on the sleeve. Nothing was removed."
        return gm

    def empty(gm, **_kwargs):
        gm["player_facing_text"] = " "
        return gm

    def explode(*_args, **_kwargs):
        raise RuntimeError("seal failed")

    install(unchanged)
    same = _post(client, WIPE, "seal-same")
    assert same["visible"].startswith("You wipe")
    assert _summary(same)["publication_disposition"] == "unchanged"
    assert _active()[1] == []
    _post(client, ACTION, "seal-mark-2")
    install(paraphrase)
    paraphrased = _post(client, WIPE, "seal-paraphrase")
    assert paraphrased["visible"].startswith("You clear")
    assert WARNING in paraphrased["visible"]
    assert _summary(paraphrased)["publication_disposition"] == "paraphrase"
    _post(client, ACTION, "seal-mark-3")
    install(contradictory)
    denied = _post(client, WIPE, "seal-contradict")
    assert "still written" not in denied["visible"].casefold()
    assert "no longer" in denied["visible"].casefold()
    assert denied["success"] is True
    assert _summary(denied)["publication_disposition"] == "rejected_fallback"
    assert _active()[1] == []
    _post(client, ACTION, "seal-mark-4")
    install(empty)
    blank = _post(client, WIPE, "seal-empty")
    assert WARNING in blank["visible"]
    assert _summary(blank)["publication_disposition"] == "empty"
    _post(client, ACTION, "seal-mark-5")
    install(explode)
    failed = _post(client, WIPE, "seal-raise")
    assert failed["success"] is True
    assert WARNING in failed["visible"]
    assert _summary(failed)["publication_disposition"] == "sealer_exception"
    from game.integrated_play import _LANES

    _LANES.clear()
    retry = _post(client, WIPE, "seal-raise")
    assert _summary(retry)["outcome"] == "replay"
    assert _active()[1].count(WARNING) == 0
    install(unchanged)
    _post(client, "I copy the name onto my sleeve using the available mud.", "seal-name")

    def persist_fails(*_args, **_kwargs):
        raise RuntimeError("session save failed")

    monkeypatch.setattr("game.api.save_session", persist_fails)
    persisted = client.post(
        "/api/chat?ui_mode=player",
        json={"text": "I wipe the name off my sleeve.", "client_request_id": "rm-seal-persist"},
    )
    assert persisted.status_code == 200
    assert NAME in persisted.json()["gm_output"]["player_facing_text"]
    assert _active()[1] == []
    _LANES.clear()
    monkeypatch.setattr("game.api.save_session", storage.save_session)
    replay = _post(client, "I wipe the name off my sleeve.", "seal-persist")
    assert _summary(replay)["outcome"] == "replay"
    assert _active()[1] == []


def test_save_failure_does_not_announce_removal(client, monkeypatch):
    _ready()
    _post(client, ACTION, "save-fail-mark")
    before = storage.CHARACTER_PATH.read_bytes()

    def boom(*_args, **_kwargs):
        raise RuntimeError("removal save interrupted")

    monkeypatch.setattr("game.api.save_character", boom)
    interrupted = client.post(
        "/api/chat?ui_mode=player",
        json={"text": WIPE, "client_request_id": "rm-save-fail"},
    )
    assert interrupted.status_code == 500
    body = interrupted.json()
    visible = str((body.get("gm_output") or {}).get("player_facing_text") or "")
    assert "no longer" not in visible.casefold()
    assert storage.CHARACTER_PATH.read_bytes() == before


@pytest.mark.parametrize("ruleset", ["pf1e", "rules_light", "science_fiction"])
def test_ruleset_fields_do_not_affect_removal(client, ruleset):
    _ready(ruleset)
    _post(client, ACTION, "ruleset-mark-" + ruleset)
    visible = _post(client, WIPE, "ruleset-wipe-" + ruleset)["visible"].casefold()
    assert "no longer" in visible and WARNING.casefold() in visible
    for term in ("perception", "difficulty class", "spell", "linguistics", "rarity"):
        assert term not in visible
    character = storage.load_character()
    assert character["ruleset_extension"] == {"id": ruleset, "preserved": True, "skill_name": "not-used"}
    assert _active()[1] == []


def test_stale_revision_and_unrelated_object_do_not_guess(client):
    from game.marking_removal import stage_grounded_removal

    _ready()
    _post(client, ACTION, "stale-mark")
    character = storage.load_character()
    session = storage.load_session()
    proposal = recognize_removal(WIPE)
    ready = resolve_removal(proposal, character, session)
    assert ready["outcome"] == "ready"
    ready["expected_revision"] = 99
    staged = stage_grounded_removal(character, ready, "stale-removal")
    assert staged["error"] == "stale_revision"
    assert _active()[1] == [WARNING]
    paper = _post(client, "I wipe the warning off the paper.", "stale-paper")
    assert "nothing was removed" in paper["visible"].casefold()
    assert _active()[1] == [WARNING]
    character = storage.load_character()
    campaign_id = session["campaign_run_id"]
    metal = _identity(
        campaign_id, "metal_plate", "Metal plate",
        marking_surfaces=[_surface("face", "face", "metal", ["metal", "plate"])],
    )
    character["inventory"].append(metal)
    storage.save_character(character)
    engraved = _post(client, "I wipe the writing off the metal.", "stale-metal")
    assert "nothing was removed" in engraved["visible"].casefold()
    assert storage.load_character()["inventory"][-1].get("markings") in (None, [])


def test_direct_resolution_does_not_treat_words_as_proof():
    proposal = recognize_removal("I erase the hidden warning off my sleeve.")
    resolution = resolve_removal(
        proposal,
        {"id": "actor", "inventory": [], "physical_status": {}},
        {"campaign_run_id": "campaign-1", "clue_knowledge": {}},
    )
    assert resolution["outcome"] == "unresolved"
    assert "target" in resolution["missing"]
    assert "keep to the north wall" not in resolution["player_text"]
