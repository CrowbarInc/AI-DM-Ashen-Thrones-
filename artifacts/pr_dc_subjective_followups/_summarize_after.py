import json
from pathlib import Path

after = json.loads(Path("artifacts/pr_dc_subjective_followups/_after.json").read_text(encoding="utf-8"))
print("ROUTED AFTER")
for row in after["routed_controls"]:
    print(
        row["reply_plan_kind"],
        row["resolver"],
        row["social_npc_id"],
        row["allowed_speaker_ids"],
        row["entry_reason"],
        "|",
        row["text"],
    )
print("DIRECT")
for row in after["direct_positive"] + after["direct_negative"]:
    print(row["reply_plan_kind"], row["npc_speech_authority"], "|", row["text"])
