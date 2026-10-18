# 25 — Source and Evidence Inventory

```json
{
  "game/live_chat_interpretation.py": "e1bb64a32566c02d9ff537cc67e8a7929e247270fcff04fabe8af03b8b8af126",
  "game/player_interpretation_bridge.py": "aff6e94afaeebc236fdd65508314735c96cfc9dce9051fb210f13cfce0d00cf0",
  "game/conversational_continuity.py": "19638f542a5a3e57d7d0dda16308951a301c3d06339d81fe0ea51dc26f7dbac1",
  "game/dialogue_authority.py": "7c6b34f212911a6d38a793298bb7bfa4ef42454924a688640b70b5e8e33f3387",
  "game/social.py": "15c8478b663c650d34a56a20f2b08a3d83d43389997a127c1552e29c3eed0173",
  "game/immutable_valid_response.py": "e6a51d6a472fc5f017d4b5f8ddb2f347cdae8c3660222c7f3fc8ce2232a8a555",
  "game/api.py": "4afdd813639b2d9d23a2f7fd8dd39f7de8e2f3533c9841af006923fe9ec45189",
  "game/storage.py": "58f0687b44caa9902a2c3f746a079dccfd00f8f80c69ac82a256d0da5d0a3716",
  "tests/test_pr_eg_r2c_r2_reference_eligibility.py": "18898390b543f2c759e6d942ccfbde0a5945cbf842a92e8652eff0b86d915a8b",
  "tests/test_pr_ef_r2_social_authority.py": "da99709656896fedf3a1816838a22f5acff9f2fa90df21cd565fb97c7c55904c",
  "tools/validate_pr_eg_r2c_r2.py": "103173568236ad596bc79c6604e9997c84db861020612c656f2dfccbd71613da"
}
```

Reproduction commands; fresh-provider commands consume configured usage, and local HTTP tests require socket access:

```powershell
.venv\Scripts\python.exe artifacts/pr_eg_r2c_r2/reproduce.py --baseline

.venv\Scripts\python.exe artifacts/pr_eg_r2c_r2/reproduce.py --after

.venv\Scripts\python.exe -m pytest tests/test_pr_eg_r2c_r2_reference_eligibility.py --tb=short

.venv\Scripts\python.exe artifacts/pr_eg_r2c_r2/run_final.py

.venv\Scripts\python.exe artifacts/pr_eg_r2c_r2/evaluate_predecessor_holdouts.py

.venv\Scripts\python.exe artifacts/pr_eg_r2c_r2/adversarial.py

.venv\Scripts\python.exe tools/validate_pr_eg_r2c_r2.py freeze

.venv\Scripts\python.exe tools/validate_pr_eg_r2c_r2.py

.venv\Scripts\python.exe artifacts/pr_eg_r2c_r2/audit_evidence.py

.venv\Scripts\python.exe artifacts/pr_eg_r2c_r2/build_review.py
```

Evidence classes are separated: static source/diffs; deterministic unit/owner tests; controlled interpretation-wire injection; recorded-provider reproduction; unchanged frozen expectation replay; actual fresh production /api/chat; persisted state inspection; derived audit/inference. No controlled/replayed result is live evidence. Source snapshots are review conveniences, not a complete executable repository export. artifact_inventory.json hashes evidence and REVIEW_MANIFEST.json maps portable entries to canonical paths. Credentials, caches, unrelated artifacts and active campaign saves are excluded.
