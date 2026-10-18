# 02 — Baseline and Environment

```json
{
  "revision": "d31beb7d73dd4fda0f22184a6a69b947b5f470ff",
  "python": "3.12.0 (tags/v3.12.0:0fb18b0, Oct  2 2023, 13:03:39) [MSC v.1935 64 bit (AMD64)]"
}
```



The starting tree was already substantially dirty; working_tree_before.txt records it. Cycle-relative before_sources preserves prior production changes independently of HEAD. The selected regression family was actually run before production edits: 584 pass / 25 fail. Its count matches the historical report but was independently measured. Selection: regression_selection.json.



Configured gpt-4.1-mini / returned gpt-4.1-mini-2025-04-14, verified in the final Responses interpretation journal. Local .env was loaded without being copied. Disposable campaigns and FastAPI TestClient exercised production /api/chat. Sandbox-only TestClient attempts stalled and were interrupted; verified runs used approved local socket access. One intermediate complete run hit Windows os.replace PermissionError at R4 confirm_single_candidate; later complete runs passed that identity. The failure is retained. Full repository suite was not run.
