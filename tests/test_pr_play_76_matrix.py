"""Additional PR-PLAY-76 classification and safety cases. Take/drop remain deferred."""
import pytest

from tests.test_pr_play_76_physical import act, add, door, enable, said, stage

CASES = [
    ("I sit on the bench.", "bench", "A", "yes", "you sit on the wooden bench"),
    ("Let me sit on the bench.", "bench", "A", "yes", "you sit"),
    ("I will sit on the bench.", "bench", "A", "yes", "you sit"),
    ("I rest on the bench.", "bench", "A", "yes", "you sit"),
    ("Please have a seat on the bench.", "bench", "A", "yes", "you sit"),
    ("I stand up.", "none", "A", "yes", "already standing"),
    ("I get up.", "none", "A", "yes", "already standing"),
    ("I rise.", "none", "A", "yes", "already standing"),
    ("I open the door.", "door", "A", "yes", "you open the wooden door"),
    ("Unlatch the door.", "door", "A", "yes", "you open"),
    ("I close the door.", "door", "A", "yes", "already closed"),
    ("Shut the door.", "open", "A", "yes", "you close"),
    ("I push the crate aside.", "crate", "A", "yes", "aside"),
    ("I pull the crate back.", "crate", "A", "yes", "you pull"),
    ("Nudge the crate aside.", "crate", "A", "yes", "aside"),
    ("Slide the crate away.", "crate", "A", "yes", "aside"),
    ("I shove the crate out of the way.", "crate", "A", "yes", "aside"),
    ("I lift the cup.", "cup", "A", "yes", "raised in place"),
    ("Heave the cup.", "cup", "A", "yes", "raised"),
    ("I approach the bench.", "bench", "A", "yes", "beside"),
    ("I walk over to the bench.", "bench", "A", "yes", "beside"),
    ("I open the door.", "locked", "D", "no", "locked"),
    ("I open the door.", "blocked", "D", "no", "obstructed"),
    ("I open the door.", "unknown", "D", "no", "not established"),
    ("I open the door.", "guarded", "C", "no", "important state"),
    ("I push the pillar.", "pillar", "E", "no", "cannot be moved"),
    ("I lift the boulder.", "heavy", "B", "no", "no strength check"),
    ("I climb the milestone.", "milestone", "D", "no", "no climbing check"),
    ("I climb the practice wall.", "wall", "B", "yes", "no additional view"),
    ("I open the door.", "hard", "B", "fail", "attempt fails"),
    ("I pick up the cup.", "cup", "D", "no", "inventory"),
    ("I drop the cup.", "cup", "D", "no", "inventory"),
    ("I place the cup down.", "cup", "D", "no", "carrying is not available"),
    ("I open the hatch.", "none", "E", "no", "not established"),
    ("I push the crate.", "two", "F", "no", "which do you mean"),
    ("I sit down.", "two_seats", "F", "no", "which seat"),
    ("I sit on the throne.", "bench", "E", "no", "not established"),
    ("I sit on the bench.", "far", "E", "no", "not accessible"),
    ("I open the hidden chest.", "hidden", "E", "no", "not established"),
    ("I break the door.", "door", "C", "no", "important state"),
    ("I teleport through the wall.", "none", "E", "no", "solid barrier"),
    ("I push the crate through the wall.", "crate", "E", "no", "unchanged"),
    ("Is the door open?", "door", "A", "no", "closed"),
    ("Can I move the crate?", "crate", "A", "no", "nothing has been moved"),
    ("Can I move the pillar?", "pillar", "E", "no", "cannot be moved"),
    ("Can I unlatch the door?", "locked", "D", "no", "locked"),
    ("Am I sitting?", "none", "A", "no", "not seated"),
    ("Am I standing?", "none", "A", "no", "standing"),
    ("Is the doorway clear?", "none", "D", "no", "no doorway"),
    ("I open the notice board.", "notice", "D", "no", "not established as something you can open"),
    ("I approach the notice board.", "notice", "A", "yes", "beside"),
    ("I push the crate away from the doorway.", "blocking", "A", "yes", "aside from the doorway"),
    ("Is the doorway clear?", "blocking", "A", "no", "not clear"),
    ("Could I open the door?", "door", "A", "no", "is closed"),
    ("Is there a small loose stone I could shift aside?", "stone", "A", "yes", "has not been moved"),
    ("Is there a small loose stone door?", "stone", "D", "no", "nothing has been added"),
    ("I push the loose stone aside.", "fitting", "A", "yes", "aside from the stonework"),
    ("Where is the loose stone?", "fitting", "A", "no", "beside the stonework"),
    ("I sit on it.", "bench", "A", "yes", "you sit"),
    ("Close it.", "open", "A", "yes", "you close"),
    ("I open the door and look inside.", "door", "A", "yes", "nothing concealed"),
    ("I open the hatch and sit on the bench.", "bench", "E", "no", "not attempted"),
    ("Push it.", "crate", "A", "yes", "you push"),
    ("I step back from the bench.", "beside", "A", "yes", "step back"),
    ("I force the door.", "door", "C", "no", "important state"),
    ("I steal the cup.", "cup", "D", "no", "inventory"),
]


def build(setup, session, scene):
    if setup == "bench":
        add(session, ident="bench", label="wooden bench", aliases=["bench", "seat"], use="seat")
    elif setup == "door":
        add(session, ident="door", label="wooden door", aliases=["door"], **door())
    elif setup == "open":
        add(session, ident="door", label="wooden door", aliases=["door"], **door(open=True))
    elif setup == "crate":
        add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
    elif setup == "cup":
        add(session, ident="cup", label="wooden cup", aliases=["cup"], mobility="movable", weight="light", portable=True, position="on the table")
    elif setup == "locked":
        add(session, ident="door", label="wooden door", aliases=["door"], **door(locked=True))
    elif setup == "blocked":
        add(session, ident="door", label="wooden door", aliases=["door"], **door(obstructed=True))
    elif setup == "unknown":
        add(session, ident="door", label="wooden door", aliases=["door"], openable=True)
    elif setup == "guarded":
        add(session, ident="door", label="guarded door", aliases=["door"], **door(consequential=True))
    elif setup == "pillar":
        add(session, ident="pillar", label="stone pillar", aliases=["pillar"], mobility="immovable")
    elif setup == "heavy":
        add(session, ident="boulder", label="boulder", aliases=["boulder"], mobility="movable", weight="heavy")
    elif setup == "milestone":
        scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
    elif setup == "wall":
        add(session, ident="wall", label="practice wall", aliases=["wall"], skill_check={"skill_id": "climb", "dc": 1})
    elif setup == "hard":
        add(session, ident="door", label="stuck door", aliases=["door"], **door(), skill_check={"skill_id": "athletics", "dc": 30})
    elif setup == "two":
        add(session, ident="a", label="oak crate", aliases=["crate"], mobility="movable", weight="light")
        add(session, ident="b", label="pine crate", aliases=["crate"], mobility="movable", weight="light")
    elif setup == "two_seats":
        add(session, ident="a", label="oak bench", aliases=["bench"], use="seat")
        add(session, ident="b", label="pine bench", aliases=["bench"], use="seat")
    elif setup == "far":
        add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat", accessible=False)
    elif setup == "hidden":
        scene["scene"]["interactables"].append({"id": "cache", "label": "hidden chest", "hidden": True, "aliases": ["chest"],
                                                "affordances": {"note": "SENTINEL_HIDDEN"}})
    elif setup == "notice":
        scene["scene"]["interactables"].append({"id": "notice_board", "label": "Notice board", "aliases": ["notice board"]})
    elif setup == "blocking":
        add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light",
            position="blocking the doorway", obstructs="doorway")
    elif setup == "stone":
        scene["scene"]["visible_facts"] = ["A weathered stone marker stands in the yard."]
    elif setup == "fitting":
        scene["scene"]["visible_facts"] = ["A weathered stone marker stands in the yard."]
        act("Is there a small loose stone I could shift aside?", session, scene)
    elif setup == "beside":
        add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat")
        act("I approach the bench.", session, scene)
    elif setup != "none":
        raise AssertionError(setup)


@pytest.fixture
def ready(monkeypatch):
    enable(monkeypatch)
    return stage()


@pytest.mark.parametrize("text,setup,category,commit,fragment", CASES, ids=[f"M{i:02d}" for i in range(len(CASES))])
def test_matrix(ready, text, setup, category, commit, fragment):
    session, scene, _ = ready
    build(setup, session, scene)
    plan, result, _ = act(text, session, scene)
    assert plan is not None
    assert plan["category"] == category
    assert fragment in said(plan, result).casefold()
    if "SENTINEL" in text or setup == "hidden":
        assert "SENTINEL" not in said(plan, result)
    if commit == "yes":
        assert result and result["success"] is True
    elif commit == "fail":
        assert result and result["success"] is False
        assert result["skill_check"]["difficulty"] == 30
    else:
        assert result is None
