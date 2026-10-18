# PR-DE Hash Stability

Serialization is the `build_messages` blob. S1 and C1 baseline hashes match PR-DD and PR-DC exactly:

- S1 `d8d6737d1bfa4f6d0928719c7e1d454b83ba46b1868434c5be71b13053c26e4f` — 98,773 bytes
- C1 `40e5408dc2cac4524faf2cc5a17182d92b67614e4a5d50822ed20591a8260f60` — 108,362 bytes

## S2 and S3

PR-DC recorded S2 at 98,123 bytes, hash `2c48c12d…`, and S3 at 98,061 bytes, hash `c22f940c…`. PR-DD recorded the same byte counts and different hashes `8a6e000a…` and `2e9dc6fd…`.

Reconstructing both methods in one process reproduces both recorded hashes. Byte counts match. Hashes do not.

Differing paths, five on each fixture:

| Path | Class |
|---|---|
| `session.turn_counter` | A. Fixture reconstruction |
| `mechanical_resolution.metadata.interaction_obligation.turn_index` | A. Same counter |
| `resolution_contract.contract_id` | A. Generated id |
| `gm_resolution_decision.contract_id` | A. Same id |
| `mechanical_resolution.metadata.interaction_obligation.resolution_contract_id` | A. Same id |

PR-DC does not increment `turn_counter` between turns, so the id stays `sha1("<initial counter>\|<player text>")`. PR-DD increments the counter after each prior turn, so S2's index is 3 and S3's is 4. `_contract_id` hashes that index with the player text. The ids have equal length, so the request size matches and the hash does not.

The builder stamps `pr-db` and `pr-dd` do not appear in the serialized payload. They are not the cause.

No gameplay state was edited to force the hashes to match. The PR-DE fixture-local anchors are the PR-DD reconstruction: S2 `8a6e000a…`, S3 `2e9dc6fd…`. This cycle does not claim those payloads are byte-identical to PR-DC.

## N1

PR-DD recorded 106,771 bytes and hash `f3e91cce…`. This cycle also measures 106,771 bytes. The hash is not that value.

Two builds in one process match. Builds in different processes differ by one field:

`narrative_plan.answer_exposition_plan.facts[].fact` and the same fact under `response_policy.answer_completeness`, of the form `clue_text_digest:<8 hex chars>`.

`game.noncombat_resolution._surfaced_facts` sets that digest with Python's salted `hash()`. That is measurement nondeterminism, class B. With `PYTHONHASHSEED=0`, the PR-DE baseline hash is stable at `346fa064b49623075d07d161250bf656d03c831616f3e971c5ee1b952135740a`. It is not a claim of byte-identical reproduction of the PR-DD hash.

The other fixtures matched their PR-DD hashes under that seed. No unresolved payload difference remains between the PR-DC and PR-DD reconstructions of S2 and S3.
