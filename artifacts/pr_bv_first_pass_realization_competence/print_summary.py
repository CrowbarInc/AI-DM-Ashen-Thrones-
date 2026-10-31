import json
from pathlib import Path

data = json.loads(
    Path("artifacts/pr_bv_first_pass_realization_competence/measurements.json").read_text(encoding="utf-8")
)
cur = data["probes"]["P1"]["current"]
bs = data["probes"]["P1"]["pr_bs"]
print("=== SALIENCE P1 current system ===")
for key, value in cur["salience_system"].items():
    print(f"{key:28} {value:6}")
print("=== SALIENCE P1 BS system ===")
for key, value in bs["salience_system"].items():
    delta = value - cur["salience_system"][key]
    print(f"{key:28} {value:6}  delta {delta:+}")
print("=== SALIENCE P1 current instructions ===")
for key, value in cur["salience_instructions"].items():
    print(f"{key:28} {value:6}")
print("=== SALIENCE P1 BS instructions ===")
for key, value in bs["salience_instructions"].items():
    delta = value - cur["salience_instructions"][key]
    print(f"{key:28} {value:6}  delta {delta:+}")
print("schema", cur["schema_chars"], bs["schema_chars"])
print("decl rule", cur["declaration_rule_chars"], bs["declaration_rule_chars"])
print("instr chars", cur["instruction_chars"], bs["instruction_chars"])
print("system", cur["system_chars"], bs["system_chars"])
print("--- retry P1 ---")
print(data["probes"]["P1"].get("retry_prefix", "")[:2000])
print("--- retry P2 ---")
print(data["probes"]["P2"].get("retry_prefix", "")[:2000])
print("player inputs")
for probe in ("P1", "P2", "P3"):
    row = data["probes"][probe]["current"]
    print(probe, "player_input=", row["player_input"])
    print("   turn_raw=", row["turn_summary_raw"])
    print("   packet=", row["packet_player_text"])
    print("   mode", row["narrative_mode"], row["role_allocation"], "type", row["response_type"])
    print(
        "   q",
        row["policy_player_direct_question"],
        "ans",
        row["policy_answer_completeness_enabled"],
        "hedge",
        row["policy_fallback_hedge"],
        "unk",
        row["policy_fallback_uncertainty_active"],
        "edge",
        row["policy_require_unknown_edge"],
    )
    print("   strategy", row["recipe_strategy"])
    print("   decision epistemic", row["decision_has_epistemic_acts"], "constraints", row["decision_has_narration_constraints"])
