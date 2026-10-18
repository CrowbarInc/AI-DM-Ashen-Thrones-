# 22 — Source Change Inventory

```json
[
  {
    "path": "game/immutable_valid_response.py",
    "sha256": "f357772591edc56b4b702db15aa9b3ef3a0f57b89d17f146a30ba924e6f43408",
    "prior_sha256": "433cdece512931a7277c717f2c6259870052742a597088c523d4a0fe0c41c0b4",
    "matches_captured_baseline": true
  },
  {
    "path": "game/api_turn_support.py",
    "sha256": "6ebfdce5ef41972b98c371e5ef353990d75db853a6cfde745ba816f809bda6bc",
    "prior_sha256": "ad543d3e9437f42ff8fe1989cda87e340f148772be2a972f9d3b804a03d77f92",
    "matches_captured_baseline": true
  },
  {
    "path": "game/api.py",
    "sha256": "b1564dc2ffa7c8d8fab52c79e7c61cd43215bc14716d4040286dc65a2ca30ea0",
    "prior_sha256": "17c4beb59216f845ecfeae7c11501dd9290bdc3f17859fcc63acf009ebede4f6",
    "matches_captured_baseline": true
  },
  {
    "path": "game/conversational_continuity.py",
    "sha256": "a2d6c98c8603d79cdd6a1da93a9a60ddf61f550979b01681da7afe7fe2db5721",
    "prior_sha256": "6c0ab85c4b78405679157ef888d674b44974a470700d9e630422326b33a69c11",
    "matches_captured_baseline": true
  },
  {
    "path": "game/dialogue_authority.py",
    "sha256": "93e9d736c0c50cc299afbec89dd0803656f8c580a8eab8b868039823b17a385c",
    "prior_sha256": "3b2c83bdd1f3766898e1802ae73c6dcc806b95b83136514cf6cdf81be3cb64e0",
    "matches_captured_baseline": true
  },
  {
    "path": "game/expressive_dialogue.py",
    "sha256": "58059bdf23a242ba71f7be64efc9d734f33d47312d5a284933d7e07c346a8288",
    "prior_sha256": "cdbc63e1d49429c7d0f1f9b17959524674d5b5373593e14711a1c35151d57335",
    "matches_captured_baseline": true
  },
  {
    "path": "game/gm_resolution_decision.py",
    "sha256": "d35a373df829ebe09e566c8b3dc73c21fd48788ab0dc1de225bbc4470219d25a"
  },
  {
    "path": "tests/test_pr_eg_r4_r1_delivery_integrity.py",
    "sha256": "79a3af7787732c5ffd91ff5f16e5325cc56d6e36f7e7ecbb047a1d441b4a9a56"
  },
  {
    "path": "tests/test_pr_ef_r2_social_authority.py",
    "sha256": "fed0274c921baf434034cb7b46411d43b09735f985d113f8efb398935aa02ed3"
  },
  {
    "path": "tools/qualify_pr_eg_r4_r1.py",
    "sha256": "ffe25bac05fd735a48aea9f29c411763e4c247d791b6e60fee060288ec5a60f8"
  },
  {
    "path": "tools/report_pr_eg_r4_r1.py",
    "sha256": "792b38f8e17a2893548a412d7e3315ef29bc5d9a1e489558002fcfbbf5fdfb85"
  }
]
```

source_diffs/*.diff are cycle-only diffs against matching source snapshots in the archived predecessor handoff, avoiding attribution of the pre-existing dirty tree to this repair. Tools and tests added by R4-R1 are explicitly listed. Data and unrelated user edits were not reverted.
