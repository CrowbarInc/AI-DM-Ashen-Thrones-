import json
from pathlib import Path

root = Path("artifacts/pr_bv_first_pass_realization_competence")
removed = json.loads((root / "P1_removed_instructions.json").read_text(encoding="utf-8"))
wanted = {14, 15, 18, 29, 30, 35, 36}
lines = []
for index in sorted(wanted):
    lines.append(f"\n===== P1 REMOVED [{index}] {removed[index]['chars']} chars =====\n")
    lines.append(removed[index]["text"])
    lines.append("\n")
removed_p2 = json.loads((root / "P2_removed_instructions.json").read_text(encoding="utf-8"))
# social structure is last-ish
for index, item in enumerate(removed_p2):
    if "SOCIAL RESPONSE" in item["text"] or "NPC response contract" in item["text"] or "ordinary" in item["text"].lower()[:80]:
        lines.append(f"\n===== P2 REMOVED [{index}] {item['chars']} chars =====\n")
        lines.append(item["text"])
        lines.append("\n")

bs = (root / "P1_system_PR-BS.txt").read_text(encoding="utf-8")
cur = (root / "P1_system_current.txt").read_text(encoding="utf-8")
# Compare before the JSON schema, which is shared.
bs_head = bs.split("Return valid JSON", 1)[0]
cur_head = cur.split("Return valid JSON", 1)[0]
bs_tail = bs.split("STRUCTURED CLAIM DECLARATION RULE", 1)[1]
cur_tail = cur.split("STRUCTURED CLAIM DECLARATION RULE", 1)[1]
lines.append("\n===== SYSTEM HEAD PR-BS =====\n")
lines.append(bs_head)
lines.append("\n===== SYSTEM HEAD CURRENT =====\n")
lines.append(cur_head)
lines.append("\n===== TAIL EQUAL =====\n")
lines.append(str(bs_tail == cur_tail))
lines.append(f"\nbs tail {len(bs_tail)} cur tail {len(cur_tail)}\n")
if bs_tail != cur_tail:
    lines.append("\n===== TAIL PR-BS =====\n")
    lines.append(bs_tail)
    lines.append("\n===== TAIL CURRENT =====\n")
    lines.append(cur_tail)
(root / "guidance_excerpts.txt").write_text("".join(lines), encoding="utf-8")
print("wrote excerpts", len("".join(lines)))
