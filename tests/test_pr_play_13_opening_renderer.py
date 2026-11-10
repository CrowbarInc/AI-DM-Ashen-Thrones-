"""PR-PLAY-13 opt-in engine-owned opening renderer. No live provider calls."""
from __future__ import annotations

import json
from types import SimpleNamespace

import openai
import pytest

import game.api as api
import game.gm as gm
import game.storage as st
from game.opening_presentation_renderer import (
    APPROVED_PRESENTATION_VARIANTS,
    build_opening_public_catalog,
    enforce_rendered_publication,
    gm_response_from_render,
    opening_plan_instruction,
    opening_renderer_mode,
    plan_selecting_required,
    prepare_opening_renderer,
    render_opening,
    realize_opening_provider_text,
)
from tests.test_pr_play_04_opening_integrity import (
    VALID_NARRATION,
    _request,
    _snap,
    _start,
    opening_world,
)

NOTICE = "The notice board lists taxes, curfew rules, and a warning about a missing patrol."
CONCISE = APPROVED_PRESENTATION_VARIANTS[NOTICE]["concise"]
HIDDEN_CASES = {
    "secret_npc_identity": "The gate serjeant is secretly Captain Veyr.",
    "hidden_quest_outcome": "The missing patrol has already been rescued.",
    "undiscovered_location": "A sealed cellar under the gate holds the ledger.",
    "unrevealed_faction": "The Ash Compact already owns the gate serjeant.",
    "private_motivation": "The runner wants the patrol to fail.",
    "restricted_metadata": "Campaign secret: the ash throne is already claimed.",
}
UNAUTHORIZED = {
    "gold": "The guards award you 100 gold.",
    "movement": "You enter the city.",
    "combat": "The enemy dies.",
    "skill": "You succeed at the skill check.",
    "quest": "The missing patrol is rescued and the quest completes.",
    "hostility": "The gate serjeant becomes hostile.",
    "item": "You gain a brass key.",
    "time": "An hour passes.",
    "damage": "You suffer 8 damage.",
}


def _claim(claim_id, text, source, **extra):
    row = {
        "claim_id": claim_id,
        "text": text,
        "source_ref": source,
        "authority": "world_truth",
        "provenance": "authored_world_fact",
        "epistemic_status": "established",
        "modality": "",
        "realization_role": extra.pop("realization_role", "MUST_STATE"),
        "relation_kind": "ordinary_predicate",
        "premise_claim_ids": [],
        "semantic_identity": {},
    }
    row.update(extra)
    return row


def _payload():
    return {
        "gm_resolution_decision": {
            "realization_claims": [
                _claim("rc_notice", NOTICE, "scene.visible_facts.0"),
                _claim("rc_gate", "You stand at Cinderwatch's eastern gate.", "scene.visible_facts.1"),
                _claim("rc_runner", "A tavern runner trades hot stew near the rain barrel.", "scene.opening_seed_facts.0", realization_role="MAY_STATE"),
                _claim("rc_hidden", HIDDEN_CASES["secret_npc_identity"], "scene.hidden_facts.0"),
                _claim("rc_motive", HIDDEN_CASES["private_motivation"], "world.npcs.0.motivation"),
                _claim("rc_place", HIDDEN_CASES["undiscovered_location"], "scene.visible_facts.9", disclosure="undiscovered"),
                _claim("rc_faction", HIDDEN_CASES["unrevealed_faction"], "scene.visible_facts.8", visibility="secret"),
                _claim("rc_quest", HIDDEN_CASES["hidden_quest_outcome"], "scene.journal_seed_facts.0"),
                _claim("rc_meta", HIDDEN_CASES["restricted_metadata"], "campaign.restricted.0"),
            ]
        },
        "opening_curated_facts": [NOTICE, "You stand at Cinderwatch's eastern gate."],
        "narration_visibility": {
            "visible_fact_strings": [
                NOTICE,
                "You stand at Cinderwatch's eastern gate.",
                "A tavern runner trades hot stew near the rain barrel.",
            ],
            "hidden_fact_strings": [HIDDEN_CASES["secret_npc_identity"], HIDDEN_CASES["restricted_metadata"]],
            "discoverable_fact_strings": [HIDDEN_CASES["undiscovered_location"]],
        },
        "scene": {"gm_only": {"hidden_facts": [HIDDEN_CASES["private_motivation"]]}},
        "campaign": {"restricted": [HIDDEN_CASES["restricted_metadata"]]},
    }


def _catalog():
    catalog = build_opening_public_catalog(_payload())
    assert catalog["ok"], catalog["reason"]
    return catalog


def _plan(catalog, rows):
    return {"selected_entries": [{"catalog_id": catalog_id, "variant_id": variant} for catalog_id, variant in rows]}


def _required_plan(catalog, variant="authored"):
    rows = [(entry["catalog_id"], variant if entry["catalog_id"] == "rc_notice" else "authored")
            for entry in catalog["entries"] if entry["required"]]
    return _plan(catalog, rows)


def _messages(payload):
    return [
        {"role": "system", "content": "base"},
        {"role": "user", "content": json.dumps(payload)},
    ]


def test_r1_flag_disabled_keeps_legacy_opening(opening_world, monkeypatch):
    monkeypatch.delenv("ASHEN_OPENING_RENDERER", raising=False)
    assert opening_renderer_mode() == "disabled"
    seen = {}

    def create(**kwargs):
        seen["input"] = kwargs["input"]
        opening_world["calls"].append({"legacy": True})
        return SimpleNamespace(
            output_text=json.dumps({"declared_claims": [], "narration": VALID_NARRATION}),
            model="offline-stub", id="synthetic-response", status="completed",
            usage=SimpleNamespace(input_tokens=20, output_tokens=10, total_tokens=30),
        )

    def ctor(**kwargs):
        assert kwargs.get("max_retries") == 0
        return SimpleNamespace(responses=SimpleNamespace(create=create))

    monkeypatch.setattr(openai, "OpenAI", ctor)
    body, status = _start()
    assert status == 200, body
    blob = json.dumps(seen["input"])
    assert "Opening authored-fact realization" in blob
    assert "OPENING_PRESENTATION_CATALOG" not in blob
    assert body["gm_output"]["player_facing_text"] == VALID_NARRATION
    assert "opening_presentation" not in (body["gm_output"].get("metadata") or {})
    assert len(opening_world["calls"]) == 1


def _install_plan_stub(opening_world, monkeypatch, plan_for):
    monkeypatch.setenv("ASHEN_OPENING_RENDERER", "1")

    def create(**kwargs):
        opening_world["calls"].append({"input": kwargs.get("input"), "max_output_tokens": kwargs.get("max_output_tokens")})
        return SimpleNamespace(
            output_text=plan_for(kwargs),
            model="offline-stub", id="synthetic-response", status="completed",
            usage=SimpleNamespace(input_tokens=20, output_tokens=12, total_tokens=32),
        )

    def ctor(**kwargs):
        assert kwargs.get("max_retries") == 0
        return SimpleNamespace(responses=SimpleNamespace(create=create))

    monkeypatch.setattr(openai, "OpenAI", ctor)


def test_r2_r21_r22_r28_r33_r35_r36_rendered_opening_commits_once(opening_world, monkeypatch):
    _install_plan_stub(opening_world, monkeypatch, lambda kwargs: plan_selecting_required(kwargs.get("input")))
    before = _snap()
    body, status = _start()
    assert status == 200, body
    text = body["gm_output"]["player_facing_text"]
    record = body["gm_output"]["metadata"]["opening_presentation"]
    assert record["authoritative_render"] is True
    assert record["publication"] == "renderer"
    assert text == record["rendered_text"]
    assert body["gm_output"]["metadata"]["opening_renderer"]["selected"] is True
    for row in record["trace"]:
        assert row["disclosure"] == "public"
        assert row["rendered_text"] in text
        assert row["source_claim_ref"]
        assert isinstance(row["position"], int)
    assert "gate" in text.lower() or "notice" in text.lower()
    after = _snap()
    assert after["campaign_started"] is True
    assert after["turn_counter"] == before["turn_counter"] + 1
    assert len(opening_world["calls"]) == 1
    assert opening_world["calls"][0]["max_output_tokens"] == gm._opening_max_output_tokens()
    assert gm._opening_max_output_tokens() <= 4096
    again, again_status = _start()
    assert again_status == 409
    assert len(opening_world["calls"]) == 1
    # The outgoing request now contains only public presentation choices; the
    # engine's authority catalog is deliberately retained locally.
    assert " ".join(row["rendered_text"] for row in record["trace"]) == text
    ordinary = [{"role": "user", "content": json.dumps({"response_type_contract": {"required_response_type": "answer"}})}]
    assert gm._requested_response_type_from_messages(ordinary) == "answer"


def test_r3_r4_catalog_includes_public_facts_and_excludes_hidden():
    catalog = _catalog()
    ids = set(catalog["by_id"])
    assert ids == {"rc_notice", "rc_gate", "rc_runner"}
    blob = json.dumps(catalog_prompt := opening_plan_instruction(catalog))
    for secret in HIDDEN_CASES.values():
        assert secret not in blob
        assert secret not in json.dumps(catalog["entries"])
    assert "rc_hidden" not in catalog_prompt
    assert catalog["by_id"]["rc_notice"]["required"] is True
    assert catalog["by_id"]["rc_runner"]["required"] is False


@pytest.mark.parametrize(
    "case,mutate,reason",
    [
        ("r5", lambda plan, catalog: plan["selected_entries"].append({"catalog_id": "rc_hidden", "variant_id": "authored"}), "unknown_catalog_id"),
        ("r6", lambda plan, catalog: plan["selected_entries"][0].__setitem__("variant_id", "paraphrase"), "unknown_variant_id"),
        ("r7", lambda plan, catalog: plan["selected_entries"].append(dict(plan["selected_entries"][0])), "duplicate_selection"),
        ("r8", lambda plan, catalog: plan["selected_entries"].pop(), "missing_required_entry"),
        ("r9", lambda plan, catalog: plan.__setitem__("selected_entries", list(reversed(plan["selected_entries"]))), "invalid_ordering"),
        ("r10", lambda plan, catalog: plan.__setitem__("narration", UNAUTHORIZED["gold"]), "arbitrary_narration_field"),
        ("r11", lambda plan, catalog: plan["selected_entries"][0].__setitem__("authority", "world_truth"), "model_supplied_authority"),
        ("r14", lambda plan, catalog: plan["selected_entries"][0].__setitem__("gloss", "The board itself lists grim new taxes."), "unsupported_field"),
    ],
)
def test_plan_rejections(case, mutate, reason):
    catalog = _catalog()
    plan = _required_plan(catalog)
    mutate(plan, catalog)
    result = render_opening(plan, catalog)
    assert result["ok"] is False
    assert result["reason"] == reason
    assert result["text"] == ""
    assert "grim new taxes" not in result["text"]
    for phrase in UNAUTHORIZED.values():
        assert phrase not in result["text"]


def test_r12_exact_authored_and_r13_approved_alternate():
    catalog = _catalog()
    authored = render_opening(_required_plan(catalog), catalog)
    assert authored["ok"]
    assert NOTICE in authored["text"]
    alternate = render_opening(_required_plan(catalog, variant="concise"), catalog)
    assert alternate["ok"]
    assert CONCISE in alternate["text"]
    assert NOTICE not in alternate["text"]
    assert "100 gold" not in alternate["text"]
    assert "rescued" not in alternate["text"].lower()


@pytest.mark.parametrize("label,sentence", list(UNAUTHORIZED.items()) + [("hidden", HIDDEN_CASES["secret_npc_identity"])])
def test_r15_through_r20_unauthorized_sentences_are_not_rendered(label, sentence):
    catalog = _catalog()
    plan = _required_plan(catalog)
    plan["narration"] = sentence
    rejected = realize_opening_provider_text(json.dumps(plan), catalog)
    assert rejected["ok"] is False
    assert sentence not in rejected["text"]
    accepted = render_opening(_required_plan(catalog), catalog)
    assert sentence not in accepted["text"]


def test_r23_r24_r29_r30_injected_prose_does_not_publish_or_commit(opening_world, monkeypatch):
    attacks = [
        {"selected_entries": [], "narration": UNAUTHORIZED["gold"]},
    ]

    def plan_for(kwargs):
        if attacks:
            return json.dumps(attacks.pop(0))
        return plan_selecting_required(kwargs.get("input"))

    _install_plan_stub(opening_world, monkeypatch, plan_for)
    before = _snap()
    body, status = _start()
    assert status == 422, body
    encoded = json.dumps(body)
    for sentence in UNAUTHORIZED.values():
        assert sentence not in encoded
    assert body["gameplay_committed"] is False
    assert _snap() == before
    body, status = _start()
    assert status == 200, body
    encoded = json.dumps(body)
    assert UNAUTHORIZED["gold"] not in encoded
    assert body["gm_output"]["scene_update"] is None
    assert body["gm_output"]["world_updates"] is None
    assert _snap()["turn_counter"] == 1
    assert len(opening_world["calls"]) == 2


def test_r25_concurrent_rendered_opening_commits_once(opening_world, monkeypatch):
    import threading

    _install_plan_stub(opening_world, monkeypatch, lambda kwargs: plan_selecting_required(kwargs.get("input")))
    entered = threading.Event()
    release = threading.Event()
    original = openai.OpenAI

    def ctor(**kwargs):
        client = original(**kwargs)
        create = client.responses.create

        def wrapped(**request):
            opening_world["calls"].append({"concurrent": True})
            entered.set()
            release.wait(timeout=5)
            return create(**request)

        client.responses.create = wrapped
        return client

    monkeypatch.setattr(openai, "OpenAI", ctor)
    results = []

    def run():
        try:
            results.append(_start())
        except BaseException as exc:  # noqa: BLE001
            results.append(({"error": type(exc).__name__}, 500))

    first = threading.Thread(target=run)
    second = threading.Thread(target=run)
    first.start()
    assert entered.wait(timeout=5)
    second.start()
    second.join(timeout=0.5)
    assert second.is_alive()
    release.set()
    first.join(timeout=10)
    second.join(timeout=10)
    assert sorted(item[1] for item in results) == [200, 409]
    assert _snap()["turn_counter"] == 1
    assert sum(1 for row in opening_world["calls"] if row.get("concurrent")) == 1


def test_r26_r27_overlay_authority(opening_world, monkeypatch):
    session = st.load_session()
    scene_id = str(session.get("active_scene_id") or "frontier_gate")
    overlay = st.get_runtime_scene_overlay(session, scene_id)
    overlay.setdefault("visible_facts_add", []).append("The eastern gate lanterns are lit.")
    st.save_session(session)

    def attack(kwargs):
        plan = json.loads(plan_selecting_required(kwargs.get("input")))
        plan["scene_update"] = {"visible_facts_add": ["You gain 100 gold."]}
        return json.dumps(plan)

    _install_plan_stub(opening_world, monkeypatch, attack)
    body, status = _start()
    assert status == 422, body
    saved = st.load_session()
    blob = json.dumps(st.get_runtime_scene_overlay(saved, scene_id))
    assert "The eastern gate lanterns are lit." in blob
    assert "100 gold" not in blob

    _install_plan_stub(opening_world, monkeypatch, lambda kwargs: plan_selecting_required(kwargs.get("input")))
    body, status = _start()
    assert status == 200, body
    saved = st.load_session()
    blob = json.dumps(st.get_runtime_scene_overlay(saved, scene_id))
    assert "The eastern gate lanterns are lit." in blob
    assert "100 gold" not in blob
    assert body["gm_output"]["scene_update"] is None


def test_r31_r32_legacy_historical_outcomes_unchanged(opening_world, monkeypatch):
    from tests.test_pr_play_11_claim_authority import install_history

    monkeypatch.delenv("ASHEN_OPENING_RENDERER", raising=False)
    install_history(opening_world, monkeypatch, "20261030T191257Z-ecc1b6062bdc")
    assert _start()[1] == 200
    assert api.new_campaign(_request())["ok"] is True
    install_history(opening_world, monkeypatch, "20261031T015747Z-5a6c03c902e3")
    body, status = _start()
    assert status == 422, body
    assert _snap()["campaign_started"] is False


def test_r34_harness_selects_renderer_only_when_enabled(monkeypatch):
    import tools.playtest.worker as worker
    from tools.playtest.worker import install_transport

    original = openai.OpenAI
    messages = _messages(_payload())
    prepared = prepare_opening_renderer(messages)
    try:
        monkeypatch.delenv("ASHEN_OPENING_RENDERER", raising=False)
        install_transport("success", False)
        legacy = openai.OpenAI(max_retries=0).responses.create(model="offline", input=prepared["messages"])
        assert "narration" in legacy.output_text
        monkeypatch.setenv("ASHEN_OPENING_RENDERER", "1")
        install_transport("success", False)
        planned = openai.OpenAI(max_retries=0).responses.create(model="offline", input=prepared["messages"])
        plan = json.loads(planned.output_text)
        assert set(plan) == {"selected_entries"}
        assert "narration" not in planned.output_text
        rendered = realize_opening_provider_text(planned.output_text, prepared["catalog"])
        assert rendered["ok"]
        install_transport("success", True)
        worker.CURRENT_TURN = 1
        turn = openai.OpenAI(max_retries=0).responses.create(model="offline", input=prepared["messages"])
        assert "narration" in turn.output_text
    finally:
        worker.CURRENT_TURN = 0
        openai.OpenAI = original


def test_publication_restore_drops_later_unauthorized_text():
    catalog = _catalog()
    rendered = render_opening(_required_plan(catalog), catalog)
    gm_out = gm_response_from_render(rendered)
    gm_out["player_facing_text"] += " " + UNAUTHORIZED["gold"]
    gm_out["scene_update"] = {"visible_facts_add": [UNAUTHORIZED["gold"]]}
    gm_out["metadata"]["accepted_response"] = {"provenance": "initial_generation"}
    enforced = enforce_rendered_publication(gm_out)
    assert enforced["player_facing_text"] == rendered["text"]
    assert UNAUTHORIZED["gold"] not in enforced["player_facing_text"]
    assert enforced["scene_update"] is None


def test_invalid_flag_fails_closed_without_dispatch(opening_world, monkeypatch):
    monkeypatch.setenv("ASHEN_OPENING_RENDERER", "sometimes")
    body, status = _start()
    assert status == 422
    assert body["opening_failure_reason"] == "opening_renderer_configuration_invalid"
    assert len(opening_world["calls"]) == 0
    assert _snap()["campaign_started"] is False


def test_ordinary_turn_contract_ignores_renderer_flag(monkeypatch):
    monkeypatch.setenv("ASHEN_OPENING_RENDERER", "1")
    messages = [{"role": "user", "content": json.dumps({"response_type_contract": {"required_response_type": "npc_dialogue"}})}]
    prepared = prepare_opening_renderer(messages)
    assert gm._requested_response_type_from_messages(messages) == "npc_dialogue"
    assert "OPENING_PRESENTATION_CATALOG" not in json.dumps(prepared["messages"]) or prepared["catalog"]["ok"] is False
