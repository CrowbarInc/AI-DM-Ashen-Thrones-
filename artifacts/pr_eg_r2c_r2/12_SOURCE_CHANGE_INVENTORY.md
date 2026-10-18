# 12 — Source Change Inventory

```json
{
  "game/live_chat_interpretation.py": {
    "before_sha256": "5bd80b61f634f304d543740b103c18ac25cb8d6132357cd5fe91714a6e26556a",
    "after_sha256": "e1bb64a32566c02d9ff537cc67e8a7929e247270fcff04fabe8af03b8b8af126"
  },
  "game/player_interpretation_bridge.py": {
    "before_sha256": "cb13724480ed13edb1d796f096caf75656e468e314480b460f6f0ef6dd8a2d70",
    "after_sha256": "aff6e94afaeebc236fdd65508314735c96cfc9dce9051fb210f13cfce0d00cf0"
  },
  "game/conversational_continuity.py": {
    "before_sha256": "3f5041949f82164d0b687c7452b804a5de4c579c6070307585f394e5651c5aec",
    "after_sha256": "19638f542a5a3e57d7d0dda16308951a301c3d06339d81fe0ea51dc26f7dbac1"
  },
  "tests/test_pr_ef_r2_social_authority.py": {
    "before_sha256": "f0e39b20a5d154a5ab2746d9a236be6a723ccab2b60067394f96dbcec11a5110",
    "after_sha256": "da99709656896fedf3a1816838a22f5acff9f2fa90df21cd565fb97c7c55904c"
  }
}
```



Production changes: bridge reconcile_reference_annotations/normalized entry; live normalize_social_scope/interpret_production_turn; continuity_directive. Existing matching, addressee resolution, ownership correction and topic selector are reused. Social resolver, dialogue authority, immutable adoption, storage and API implementations were not edited.



New focused tests plus one old normalization assertion changed: provider subject alone no longer clears distant kingdom. Old assertion is preserved under before_sources/tests. This contract correction is explicit, not a hidden inherited failure resolution. All historical R1/R2C/R4 frozen fixtures remain unchanged. Tooling supplies HTTP qualification, provenance/state/cost audits, exact failure comparison and packaging. Unified cycle-relative diffs and source snapshots separate this work from the initially dirty tree.
