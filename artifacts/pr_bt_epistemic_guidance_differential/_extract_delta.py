"""Extract PR-BS vs PR-BT provider-facing guidance for differential discovery."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

PAIRS = [
    (
        "P1",
        ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/provider_request_attempt_generation_1.json",
        ROOT / "artifacts/pr_bt_provider_deduplication_micro_live/evidence/P1/provider_request_attempt_generation_1.json",
    ),
    (
        "P2",
        ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/provider_request_attempt_generation_1.json",
        ROOT / "artifacts/pr_bt_provider_deduplication_micro_live/evidence/P2/provider_request_attempt_generation_1.json",
    ),
    (
        "P3",
        ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/provider_request_attempt_generation_1.json",
        ROOT / "artifacts/pr_bt_provider_deduplication_micro_live/evidence/P3/provider_request_attempt_generation_1.json",
    ),
]


def load(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    provider = data["provider_input"]
    system = provider[0]["content"]
    user = json.loads(provider[1]["content"])
    return data, system, user


def summarize_value(value, depth=0):
    if isinstance(value, str):
        return f"str:{len(value)}"
    if isinstance(value, list):
        return f"list:{len(value)}"
    if isinstance(value, dict):
        return {k: summarize_value(v, depth + 1) for k, v in value.items()}
    if value is None:
        return None
    return type(value).__name__


def main():
    summary = {}
    for name, path_bs, path_bt in PAIRS:
        data_bs, sys_bs, user_bs = load(path_bs)
        data_bt, sys_bt, user_bt = load(path_bt)
        instr_bs = user_bs.get("instructions") or []
        instr_bt = user_bt.get("instructions") or []
        (OUT / f"{name}_system_BS.txt").write_text(sys_bs, encoding="utf-8")
        (OUT / f"{name}_system_BT.txt").write_text(sys_bt, encoding="utf-8")
        (OUT / f"{name}_instructions_BS.txt").write_text(
            "".join(f"\n\n===== INSTR {i} ({len(text)} chars) =====\n\n{text}" for i, text in enumerate(instr_bs)),
            encoding="utf-8",
        )
        (OUT / f"{name}_instructions_BT.txt").write_text(
            "".join(f"\n\n===== INSTR {i} ({len(text)} chars) =====\n\n{text}" for i, text in enumerate(instr_bt)),
            encoding="utf-8",
        )
        keys = sorted(set(user_bs) | set(user_bt))
        key_report = []
        for key in keys:
            left = user_bs.get(key, "<MISSING>")
            right = user_bt.get(key, "<MISSING>")
            same = left == right
            key_report.append(
                {
                    "key": key,
                    "same": same,
                    "bs": summarize_value(left) if left != "<MISSING>" else "<MISSING>",
                    "bt": summarize_value(right) if right != "<MISSING>" else "<MISSING>",
                    "bs_chars": len(json.dumps(left, ensure_ascii=False)) if left != "<MISSING>" else 0,
                    "bt_chars": len(json.dumps(right, ensure_ascii=False)) if right != "<MISSING>" else 0,
                }
            )
        summary[name] = {
            "system_bs_chars": len(sys_bs),
            "system_bt_chars": len(sys_bt),
            "system_same": sys_bs == sys_bt,
            "user_raw_bs": len(data_bs["provider_input"][1]["content"]),
            "user_raw_bt": len(data_bt["provider_input"][1]["content"]),
            "instr_count_bs": len(instr_bs),
            "instr_count_bt": len(instr_bt),
            "instr_chars_bs": sum(len(x) for x in instr_bs),
            "instr_chars_bt": sum(len(x) for x in instr_bt),
            "keys": key_report,
        }
        print(name, "system same", sys_bs == sys_bt, len(sys_bs), len(sys_bt))
        print("  instr", len(instr_bs), sum(len(x) for x in instr_bs), "->", len(instr_bt), sum(len(x) for x in instr_bt))
        for row in key_report:
            if not row["same"]:
                print(
                    f"  DIFF {row['key']}: bs {row['bs_chars']} bt {row['bt_chars']} "
                    f"delta {row['bs_chars'] - row['bt_chars']}"
                )
    (OUT / "key_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
