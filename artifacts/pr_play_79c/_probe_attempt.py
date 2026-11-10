import json
from pathlib import Path

def walk(node, hits):
    if isinstance(node, dict):
        if "last_background_expression" in node:
            hits.append(node["last_background_expression"])
        for value in node.values():
            walk(value, hits)
    elif isinstance(node, list):
        for value in node:
            walk(value, hits)

data = json.loads(Path("artifacts/pr_play_79c/browser_data/session.json").read_text(encoding="utf-8"))
hits = []
walk(data, hits)
print("hits", len(hits))
print(json.dumps(hits[0], indent=2)[:4000])
