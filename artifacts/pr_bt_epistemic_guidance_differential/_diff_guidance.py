"""Classify instruction and system-prompt deltas between PR-BS and PR-BT P1."""
import difflib
import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent


def split_instructions(text: str):
    parts = re.split(r"\n\n===== INSTR \d+ \(\d+ chars\) =====\n\n", text)
    return [part.strip() for part in parts if part.strip()]


def first_line(text: str, n=140):
    line = text.replace("\n", " | ")
    return line[:n]


def main():
    sys_bs = (OUT / "P1_system_BS.txt").read_text(encoding="utf-8")
    sys_bt = (OUT / "P1_system_BT.txt").read_text(encoding="utf-8")
    diff = list(difflib.unified_diff(sys_bs.splitlines(), sys_bt.splitlines(), lineterm="", n=2))
    (OUT / "P1_system_unified.diff").write_text("\n".join(diff), encoding="utf-8")
    print("system diff lines", len(diff))

    instr_bs = split_instructions((OUT / "P1_instructions_BS.txt").read_text(encoding="utf-8"))
    instr_bt = split_instructions((OUT / "P1_instructions_BT.txt").read_text(encoding="utf-8"))
    print("counts", len(instr_bs), len(instr_bt))

    bt_set = set(instr_bt)
    removed = []
    kept = []
    for index, text in enumerate(instr_bs):
        if text in bt_set:
            kept.append({"index": index, "chars": len(text), "head": first_line(text)})
        else:
            removed.append({"index": index, "chars": len(text), "head": first_line(text, 220), "text": text})

    bs_set = set(instr_bs)
    added = []
    for index, text in enumerate(instr_bt):
        if text not in bs_set:
            added.append({"index": index, "chars": len(text), "head": first_line(text, 220), "text": text})

    print("kept", len(kept), "removed", len(removed), "added", len(added))
    print("removed chars", sum(item["chars"] for item in removed))
    print("added chars", sum(item["chars"] for item in added))
    print("\n--- REMOVED ---")
    for item in removed:
        print(f"[{item['index']}] {item['chars']}c :: {item['head']}")
    print("\n--- ADDED ---")
    for item in added:
        print(f"[{item['index']}] {item['chars']}c :: {item['head']}")

    (OUT / "P1_removed_instructions.json").write_text(
        json.dumps(removed, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "P1_added_instructions.json").write_text(
        json.dumps(added, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "P1_kept_instructions.json").write_text(
        json.dumps(kept, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # P2/P3 instruction identity vs P1 within each version
    for probe in ("P2", "P3"):
        bs = split_instructions((OUT / f"{probe}_instructions_BS.txt").read_text(encoding="utf-8"))
        bt = split_instructions((OUT / f"{probe}_instructions_BT.txt").read_text(encoding="utf-8"))
        only_bs = [first_line(t, 160) for t in bs if t not in set(instr_bs)]
        only_bt = [first_line(t, 160) for t in bt if t not in set(instr_bt)]
        missing_bs = [first_line(t, 160) for t in instr_bs if t not in set(bs)]
        missing_bt = [first_line(t, 160) for t in instr_bt if t not in set(bt)]
        print(f"\n{probe} vs P1 BS extra {len(only_bs)} missing {len(missing_bs)}")
        for line in only_bs:
            print("  +BS", line)
        for line in missing_bs:
            print("  -BS", line)
        print(f"{probe} vs P1 BT extra {len(only_bt)} missing {len(missing_bt)}")
        for line in only_bt:
            print("  +BT", line)
        for line in missing_bt:
            print("  -BT", line)


if __name__ == "__main__":
    main()
