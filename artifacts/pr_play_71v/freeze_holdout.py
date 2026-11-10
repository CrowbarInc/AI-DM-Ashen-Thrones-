"""Write the PR-PLAY-71V developer holdout once. Does not execute it."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

ATOMIC = []
for failures in (0, 1, 2, 3):
    ATOMIC.append({
        "id": f"W0{failures + 1}",
        "group": "atomic",
        "kind": "success",
        "failures": failures,
        "expect_calls": failures + 1,
        "expect_delays": [0.01, 0.03, 0.09][:failures],
    })
ATOMIC += [
    {"id": "W05", "group": "atomic", "kind": "exhaust", "expect_calls": 4, "expect_delays": [0.01, 0.03, 0.09], "expect_winerror": 5},
    {"id": "W06", "group": "atomic", "kind": "permission", "code": 32, "expect_calls": 1},
    {"id": "W07", "group": "atomic", "kind": "permission", "code": 13, "expect_calls": 1},
    {"id": "W08", "group": "atomic", "kind": "permission", "code": None, "expect_calls": 1},
    {"id": "W09", "group": "atomic", "kind": "oserror", "expect_calls": 1, "expect_errno": 5},
    {"id": "W10", "group": "atomic", "kind": "missing_source"},
    {"id": "W11", "group": "atomic", "kind": "unavailable_destination"},
    {"id": "W12", "group": "atomic", "kind": "single_outer", "failures": 3, "expect_calls": 4, "expect_outer": 1},
    {"id": "W13", "group": "atomic", "kind": "real_windows_lock"},
    {"id": "W14", "group": "atomic", "kind": "create_missing"},
    {"id": "W15", "group": "atomic", "kind": "success", "failures": 0, "expect_calls": 1, "expect_delays": [], "content": "COMPLETE-REPLACEMENT"},
]
ROLLBACK = [
    {"id": "P01", "group": "rollback", "kind": "atomic_target", "target": "session"},
    {"id": "P02", "group": "rollback", "kind": "atomic_target", "target": "combat"},
    {"id": "P03", "group": "rollback", "kind": "atomic_target", "target": "log"},
    {"id": "P04", "group": "rollback", "kind": "world_write"},
    {"id": "P05", "group": "rollback", "kind": "identifier"},
    {"id": "P06", "group": "rollback", "kind": "opening"},
    {"id": "P07", "group": "rollback", "kind": "recover_after_world"},
    {"id": "P08", "group": "rollback", "kind": "no_sentinel"},
    {"id": "P09", "group": "rollback", "kind": "unrelated_file"},
    {"id": "P10", "group": "rollback", "kind": "normal_create"},
]
CHAT = [
    {"id": f"C0{index}", "group": "chat", "kind": kind}
    for index, kind in enumerate([
        "transient_1", "transient_3", "permanent_status", "permanent_flag",
        "permanent_log", "permanent_resolve_once", "recover_after_permanent",
        "duplicate_followup", "opposite_branch", "reload_log",
    ], start=1)
]
LIFECYCLE = [
    {"id": "L01", "group": "lifecycle", "kind": "create"},
    {"id": "L02", "group": "lifecycle", "kind": "start"},
    {"id": "L03", "group": "lifecycle", "kind": "opening_scene"},
    {"id": "L04", "group": "lifecycle", "kind": "first_discovery"},
    {"id": "L05", "group": "lifecycle", "kind": "branch", "branch": "survey"},
    {"id": "L06", "group": "lifecycle", "kind": "branch", "branch": "report"},
    {"id": "L07", "group": "lifecycle", "kind": "exclusive", "branch": "survey"},
    {"id": "L08", "group": "lifecycle", "kind": "exclusive", "branch": "report"},
    {"id": "L09", "group": "lifecycle", "kind": "resume", "branch": "survey"},
    {"id": "L10", "group": "lifecycle", "kind": "resume", "branch": "report"},
]
TRANSCRIPT = [
    {"id": f"T0{index}", "group": "transcript", "kind": kind}
    for index, kind in enumerate(["survey_text", "report_text", "restore_survey", "restore_report", "continuation_isolated"], start=1)
]
DISCLOSURE = [
    {"id": f"D0{index}", "group": "disclosure", "kind": kind}
    for index, kind in enumerate(["discovery", "consequence", "rejected_narration", "failed_persist_hidden", "reload"], start=1)
]
PROJECTION = [
    {"id": f"S0{index}", "group": "projection", "kind": kind}
    for index, kind in enumerate(["new", "start", "gameplay", "save_resume", "state"], start=1)
]
CASES = ATOMIC + ROLLBACK + CHAT + LIFECYCLE + TRANSCRIPT + DISCLOSURE + PROJECTION


def main():
    assert len(CASES) == 60, len(CASES)
    assert len({row["id"] for row in CASES}) == 60
    raw = json.dumps(CASES, indent=2).encode("utf-8")
    path = OUT / "frozen_holdout.json"
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    manifest = {
        "sha256": digest,
        "cases": 60,
        "developer_authored": True,
        "independent_external_validation": False,
        "groups": {
            "atomic": 15,
            "rollback": 10,
            "chat": 10,
            "lifecycle": 10,
            "transcript": 5,
            "disclosure": 5,
            "projection": 5,
        },
    }
    (OUT / "frozen_holdout_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(digest)


if __name__ == "__main__":
    main()
