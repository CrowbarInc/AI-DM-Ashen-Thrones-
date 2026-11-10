from pathlib import Path
text = Path("artifacts/pr_play_79c/browser_data/session.json").read_text(encoding="utf-8")
for needle in ("last_publication", "last_background_expression", "last_narration"):
    start = 0
    n = 0
    while True:
        i = text.find(needle, start)
        if i < 0:
            break
        n += 1
        print("\n==", needle, n, "==")
        print(text[max(0, i-80):i+220].replace("\n", " "))
        start = i + len(needle)
    print("count", needle, n)
