# AT-FG-02A-EXEC — Controlled cache cleanup

**Verdict PASS. Integrity PASS.**

Branch `feature/product-realization` at `6e59c070dcf522594c915ab39b61e198f56c3e28`.

| Metric | Result |
| --- | ---: |
| Authorized candidates | 409 |
| Successfully deleted | 409 |
| Skipped | 0 |
| Failed | 0 |
| Apparent bytes removed by ledger | 16,246,229 |
| Allocated bytes removed by ledger | 17,088,936 |
| Repository size before (apparent bytes) | 34,501,697,472 |
| Repository size after (apparent bytes) | 34,485,451,243 |
| Observed repository size decrease (apparent bytes) | 16,246,229 |
| Repository regular files before | 3,862,005 |
| Repository regular files after | 3,861,596 |
| Repository directories before and after | 312,475 → 312,475 |
| Volume free space before deletion (bytes) | 364,691,886,080 |
| Volume free space after deletion (bytes) | 364,708,646,912 |
| Observed volume free-space change (bytes) | +16,760,832 |

The repository measurements include ignored files and Git metadata and precede publication of this report. Windows allocation was measured on validated file handles. The volume delta is the net free-space change during the deletion window and can reflect unrelated activity on the same volume.

## Integrity

- Baseline capture started 2026-11-22T01:43:01.728714+00:00. Post-execution capture started 2026-11-22T01:49:06.296786+00:00.
- Git comparison matched. The baseline had 35 modified tracked paths, 51 missing tracked paths and 257 ordinary untracked status entries. The comparison covered HEAD, branch, index SHA-256, exact porcelain records and pre-existing dirty tracked file hashes.
- Compared SHA-256 for 436 pinned files across AT-OPT and current PR-PLAY evidence, active live scratch, handoff exports and the session pointer. Protected membership and hashes matched. The existing discrepancy between the November 21 session pointer and the November 18 stable review remains.
- The non-target metadata comparison matched outside Git object storage. The no-reparse walk compared directory membership and ordinary file paths, sizes, last-write times and attributes. Pinned and pre-existing dirty tracked files also had content digests. The Git metadata exception below was isolated to the baseline interval. These snapshots cannot detect changes reverted between measurements.
- Windows Restart Manager checked the 409 exact files and flagged 0 as open or unavailable. Repository-linked Cursor worker PID(s) 30772. The host check found no candidate-producing runner. Each deletion used an exclusive handle to verify the exact path, identity, allocation and SHA-256 immediately before marking the file for deletion.
- The original manifest, retained caches and directory structure were included in the integrity checks. No backups or tests were run.

## Exceptions

- The first metadata comparison flagged `.git`. Follow-up found 8,565 files under `.git/objects/` with last-write timestamps during the pre-deletion baseline interval. The latest timestamp was 2026-11-22 01:46:08 UTC. The deletion window began at 01:48:54 UTC. No Git file showed a last-write timestamp during or after that window at the follow-up check. Git metadata file count, directory count and apparent byte total matched across both snapshots. The process that refreshed the timestamps was not identified. The read-only Git integrity check `git fsck --full --no-dangling` exited successfully.

## Next action

The cache cleanup is complete. Request separate authorization before any further governance work.

## Deletion ledger

Source manifest SHA-256 `18674b12af0a7728e6178fd8a41e2490b7b32c018c29f0044f07031b89812120`.

```text
path|apparent_bytes|allocated_bytes|sha256|validation|deletion|error
game/behavioral_evaluators/__pycache__/__init__.cpython-312.pyc|791|4096|98ac46723dd7cbf8b49ead523c7832d18b5d114d2b965515af735f378898d4bd|PASS|DELETED|
game/behavioral_evaluators/__pycache__/intent_fulfillment.cpython-312.pyc|17672|20480|dbaa5222cb82fddceace51061e34e3e78c8890d3a70d516645fe029a83a2ac87|PASS|DELETED|
game/behavioral_evaluators/__pycache__/player_agency.cpython-312.pyc|12364|16384|eca8b2a240fd6309103c0088e3327039f57164d30ba96d6078d94b83a3f58750|PASS|DELETED|
game/behavioral_evaluators/__pycache__/session_cohesion.cpython-312.pyc|23471|24576|7b548c5c6e0d386e24e301fbde91edb02a2be55e049056a6462a895e19646592|PASS|DELETED|
game/importers/__pycache__/pf_json_importer.cpython-312.pyc|7515|8192|eca0d7c4876fa2772ef84651f66f2befc1eb9b4d722b24bef8986bfed8ce3b88|PASS|DELETED|
tests/__pycache__/__init__.cpython-312.pyc|204|208|a52b6afaf8df42b35bf04c44cf9621414b4cb146d677b5548cb0a6cc0e851eaa|PASS|DELETED|
tests/__pycache__/conftest.cpython-312-pytest-9.0.3.pyc|6005|8192|d8e94b005c3831187f503b4931cfda43d1e488d491e41d09a4a7d21f1954e270|PASS|DELETED|
tests/__pycache__/conftest.cpython-312-pytest-9.1.1.pyc|6005|8192|215fe20f36a3a5b664a6ebeedc3e0270f019be2031c4ff143eaf90a3b3c1dbc9|PASS|DELETED|
tests/__pycache__/debug_trace_utils.cpython-312.pyc|1458|4096|53a9ee3eda3949c58a990fd42a0af467a0dd7b662f0f427ad46039573d312df2|PASS|DELETED|
tests/__pycache__/failure_classification_contract.cpython-312.pyc|12495|16384|b5359e1df0eb5205377d95e2eb5055a525c1cf7cbe8cdf526e7dccfea092e6df|PASS|DELETED|
tests/__pycache__/ownership_guard_bd_dependency_compression.cpython-312.pyc|16502|20480|112c1facac34fcaf0eaa5d6d37cdc2f2df28a01ec3eda6d58236c86b0001aa92|PASS|DELETED|
tests/__pycache__/ownership_guard_bv16c_terminal_monkeypatch.cpython-312.pyc|4897|8192|b088430b15057525ddb28aa9307f91a7326d0550e3a7ffbbb240805677d23356|PASS|DELETED|
tests/__pycache__/ownership_guard_bv_compatibility.cpython-312.pyc|39316|40960|932c3879268cb3a6980e14b1280b80d09ac672409d98138de9eee8163c21aa66|PASS|DELETED|
tests/__pycache__/pr_play_54_corpus.cpython-312.pyc|16853|20480|b09f61c479f542dbd2f1136859686e1f8bb4f0f44a3570e769b08be8271f5966|PASS|DELETED|
tests/__pycache__/pr_play_55_development.cpython-312.pyc|6071|8192|3f262719a651ef06f9c2879a9dd8ddecdddf5e42f02474cb5aee48871768ddec|PASS|DELETED|
tests/__pycache__/pr_play_55_evaluate.cpython-312.pyc|13696|16384|2f7e7bc099c3f63e6b0dd7be80fc0860876435fbc4752587dbe543d7dd942e69|PASS|DELETED|
tests/__pycache__/pr_play_58_development.cpython-312.pyc|5118|8192|ddfc97fedb18533f15ecbd3b7c0bac8d8038a35de62411a309e4b36bd971c26e|PASS|DELETED|
tests/__pycache__/pr_play_59_development.cpython-312.pyc|3331|4096|321f94ba2c5cdd333257bb9d454b6c3712bf1ab60986a7973c92985daa0692df|PASS|DELETED|
tests/__pycache__/pr_play_64_development.cpython-312.pyc|6530|8192|f4297e7c6fea01f2dcf041d39b59709f073879a2184c6a037e06362594827890|PASS|DELETED|
tests/__pycache__/test_api_narration_path_selection.cpython-312-pytest-9.1.1.pyc|123397|126976|9996e4b8c68eb654b9e47c3aeb92bced1d22a8a7571fd7068421199f67a458dc|PASS|DELETED|
tests/__pycache__/test_atgb_r1_02_revision_boundary.cpython-312-pytest-9.1.1.pyc|26943|28672|266da4dc8599b38a41430f365ea7b70f7c835835bb9630ec6c8de40a35b30ba9|PASS|DELETED|
tests/__pycache__/test_atgb_r1_04_readiness.cpython-312-pytest-9.1.1.pyc|34394|36864|4596b5b9c195f4f299677f05719b7a9ec73b7a8d2fa12a8180651bf238359a96|PASS|DELETED|
tests/__pycache__/test_atgb_r1_07_correction_contract.cpython-312-pytest-9.1.1.pyc|35892|36864|ac6bd6e9b86aae5177733bd8ff6485da13f46dbce1c0dee45dffe7ca7f672cdb|PASS|DELETED|
tests/__pycache__/test_atgb_r2_02_speech_participant_grounding.cpython-312-pytest-9.1.1.pyc|67605|69632|8dc4c2242b6f436baa9bac7e0981fb2104e42ca92b690e28bdf787b380bef2c2|PASS|DELETED|
tests/__pycache__/test_atgb_r2_04_question_evidence_contract.cpython-312-pytest-9.1.1.pyc|17424|20480|641aeddb6898e94961d21de2b87db5177aed6f9487b988bc85902a0733ab8242|PASS|DELETED|
tests/__pycache__/test_atgb_readiness.cpython-312-pytest-9.1.1.pyc|16871|20480|52dc7263ad69740b036d84fa4c01216de3a7e9daa3b0567a6d8f8d7f1746bd31|PASS|DELETED|
tests/__pycache__/test_atomic_character_save.cpython-312-pytest-9.0.3.pyc|27494|28672|2c2beb6560911a706eb9f8360efa096fe18f6403b4e54b2a0a29a4bc95ffe54d|PASS|DELETED|
tests/__pycache__/test_atomic_character_save.cpython-312-pytest-9.1.1.pyc|27494|28672|2c2beb6560911a706eb9f8360efa096fe18f6403b4e54b2a0a29a4bc95ffe54d|PASS|DELETED|
tests/__pycache__/test_authored_knowledge_realization.cpython-312-pytest-9.1.1.pyc|46451|49152|6d48b93d99bdb9eb583bb5ae12fc250e0ae67264d9995aad71f68326406438e9|PASS|DELETED|
tests/__pycache__/test_authoritative_lead_provenance_social_prose_non_ingestion.cpython-312-pytest-9.1.1.pyc|65450|65536|5575438aa725472190f71087a0a5472b63827eed279bb3cf3850439673c7e591|PASS|DELETED|
tests/__pycache__/test_automated_playtest.cpython-312-pytest-9.1.1.pyc|42880|45056|d9c3161fcb2823976165f2d1aefe9510b27fa2b1ea251d993a4a587e3616ba68|PASS|DELETED|
tests/__pycache__/test_bound_speaker_knowledge_resolution.cpython-312-pytest-9.1.1.pyc|57368|61440|cf2dd8461e61367d59756f4450bc12475f32e573247f56da063c2db0e682312b|PASS|DELETED|
tests/__pycache__/test_bounded_improvisation_authority.cpython-312-pytest-9.1.1.pyc|15817|16384|65efbeaf1feaf853c6f72988eba535b3668db291924cea185142169259c66550|PASS|DELETED|
tests/__pycache__/test_broad_address_social_bid.cpython-312-pytest-9.1.1.pyc|62511|65536|63f4d201fe5371c01795d5c3f3c9b071543ae2fa25a9c06a78e09657b77efed6|PASS|DELETED|
tests/__pycache__/test_broadcast_open_call_social.cpython-312-pytest-9.1.1.pyc|5522|8192|0472f2fc914d9a18dabcafc4d664b6bbcac2225cb95b80ef689abef227b986ba|PASS|DELETED|
tests/__pycache__/test_bv14a_social_exchange_emission_facade_delegates.cpython-312-pytest-9.1.1.pyc|9532|12288|659a908400d47bb4ef6c67a2c78415b01d96506621dae4893e5f3d056cd68a4c|PASS|DELETED|
tests/__pycache__/test_by3_strict_social_semantic_mutation.cpython-312-pytest-9.1.1.pyc|23549|24576|40abb18934ad57f8703c2f405dbeaa03f4bfaa23ebc90ee3fbdeb3cc7d1acc2d|PASS|DELETED|
tests/__pycache__/test_campaign_reset.cpython-312-pytest-9.1.1.pyc|22552|24576|6b7a853c2b938fd0fca6509f026cb934cc42ef44115a93610d9f3de6b970fbbf|PASS|DELETED|
tests/__pycache__/test_campaign_state_factory.cpython-312-pytest-9.1.1.pyc|10415|12288|bc79a702279752f81ea2a3eb6211884396ffa07caf48d8465452f7ca5f3a9ffa|PASS|DELETED|
tests/__pycache__/test_clue_discovery.cpython-312-pytest-9.1.1.pyc|14796|16384|95b5c997ee1a49260316f2920e44a1af1215ee92cf9892334616bc98f388b9b2|PASS|DELETED|
tests/__pycache__/test_clue_idempotence.cpython-312-pytest-9.1.1.pyc|12202|12288|d0a06a72c8d5b69fbf4f8ca5ad3539f9d69c69a614d6af6da64d48e6ab99609a|PASS|DELETED|
tests/__pycache__/test_clue_knowledge.cpython-312-pytest-9.1.1.pyc|34998|36864|cd5c0f2b525c62e26d58039859299501fb3ad3aa49a1d7f7522ebd9c88a18946|PASS|DELETED|
tests/__pycache__/test_combat_resolution.cpython-312-pytest-9.0.3.pyc|32597|32768|ddefcaa167b57ad09460cf87ea90ed294b5e99eab17649f68d7c8c31bab1b3c2|PASS|DELETED|
tests/__pycache__/test_combat_resolution.cpython-312-pytest-9.1.1.pyc|32597|32768|08ead83c42bd6a3e974f6bf02ab10cd3a2f5b97a9b7b01a8acf64c0ba7b41f9b|PASS|DELETED|
tests/__pycache__/test_compat_import_governance.cpython-312-pytest-9.1.1.pyc|47341|49152|ecee878eea12050ad1c02c3825c71f2a74f3dcc03b26570e0d10a642d4d3549e|PASS|DELETED|
tests/__pycache__/test_contract_registry.cpython-312-pytest-9.0.3.pyc|15218|16384|540416be1294a5dc5c12c5cc4bdd77b9f7fb229d24b08e573605667f1d7bed17|PASS|DELETED|
tests/__pycache__/test_contract_registry.cpython-312-pytest-9.1.1.pyc|15218|16384|540416be1294a5dc5c12c5cc4bdd77b9f7fb229d24b08e573605667f1d7bed17|PASS|DELETED|
tests/__pycache__/test_dialogue_interaction_establishment.cpython-312-pytest-9.1.1.pyc|20405|20480|7717e4273ccbee89174c717b5c1c18d0463090ca3f4fe256e16c28e59c32c797|PASS|DELETED|
tests/__pycache__/test_dialogue_plan_final_emission_gate.cpython-312-pytest-9.1.1.pyc|32523|32768|8ad3cd77776d2145fb528bd2edc5cbaff9c03b5e734f7d0e09f57732983d1cc1|PASS|DELETED|
tests/__pycache__/test_dialogue_routing_lock.cpython-312-pytest-9.1.1.pyc|13805|16384|aa480adf195cad194fa2b351b17381203939e6f2d9da7dee53b5743970431ec0|PASS|DELETED|
tests/__pycache__/test_dialogue_social_convergence.cpython-312-pytest-9.1.1.pyc|41754|45056|55fec83afd712a8223e766137a1fd0007cb8712cd39beda992ba9484958824cf|PASS|DELETED|
tests/__pycache__/test_dialogue_social_plan.cpython-312-pytest-9.1.1.pyc|41963|45056|2b01bddd9acdc1c1ff7ee6b11aa48d83267db374358bb251569b109226eaaae9|PASS|DELETED|
tests/__pycache__/test_dialogue_social_plan_block_x_contract_pins.cpython-312-pytest-9.1.1.pyc|6204|8192|20de00eab21002c42b2c89fa52b21bc2d9eb012af5c0af6d4a17d10c77b46bf5|PASS|DELETED|
tests/__pycache__/test_dialogue_social_plan_block_y.cpython-312-pytest-9.1.1.pyc|15455|16384|8a61150d01b72c4c9e30a5b935a1204649f8d527256a390241c3a55af37bd616|PASS|DELETED|
tests/__pycache__/test_dialogue_social_plan_block_z.cpython-312-pytest-9.1.1.pyc|8530|12288|a7eff0598ce29caf9ec7d281b1c3b7f1801d025e14c5cd594171953d58f7b039|PASS|DELETED|
tests/__pycache__/test_diegetic_fallback_narration.cpython-312-pytest-9.0.3.pyc|28194|28672|84bb0d020757aece2b695fe2917ee3020afed63c8a4942d043863c41f35228dd|PASS|DELETED|
tests/__pycache__/test_diegetic_fallback_narration.cpython-312-pytest-9.1.1.pyc|28194|28672|84bb0d020757aece2b695fe2917ee3020afed63c8a4942d043863c41f35228dd|PASS|DELETED|
tests/__pycache__/test_directed_social_routing.cpython-312-pytest-9.1.1.pyc|102912|106496|0409f05e146f9b1b2db454b1a2bd3ba080292e9aeda88d3bdad0a4470cfbf0f4|PASS|DELETED|
tests/__pycache__/test_empty_social_retry_regressions.cpython-312-pytest-9.1.1.pyc|45788|49152|a897ab68b03166435c49d2504485b0b0e3d1012b026e4969830e902e2e378111|PASS|DELETED|
tests/__pycache__/test_explicit_world_action_social_lock_override.cpython-312-pytest-9.1.1.pyc|103518|106496|5644866ca0c8f0d3ddc2102b4e0275c24d0a9573dd93ab319d94d1477a9dad72|PASS|DELETED|
tests/__pycache__/test_exploration_resolution.cpython-312-pytest-9.1.1.pyc|146756|147456|8912540fc7060873499e1540f6c7563025846d6ec8bf35cdf37941ed56433e31|PASS|DELETED|
tests/__pycache__/test_exploration_skill_checks.cpython-312-pytest-9.1.1.pyc|22940|24576|86e53354082d1db3aa0549731f14c699b56f79ab2aeae296870a5aad71b0a59c|PASS|DELETED|
tests/__pycache__/test_final_emission_visibility.cpython-312-pytest-9.1.1.pyc|97695|98304|9865d85b611383a0e2f57e53a061a8168d5bbe460975f8a36480f001eade2423|PASS|DELETED|
tests/__pycache__/test_final_emission_visibility_fallback.cpython-312-pytest-9.1.1.pyc|201977|204800|59862e6a42a682106d24fe519c5467e35e4657358357ec34c788b750096034fc|PASS|DELETED|
tests/__pycache__/test_five_turn_gameplay.cpython-312-pytest-9.1.1.pyc|67511|69632|f8f873dafe6b9b471348137b72c75eddde87f9226863415844098947c46b7c5f|PASS|DELETED|
tests/__pycache__/test_five_turn_gameplay.cpython-312.pyc|22044|24576|820c1292ce7974ae80ce3ffa8ed69d426e506cb0af1f728cf3d6891669ddc37a|PASS|DELETED|
tests/__pycache__/test_followup_topic_continuity_public_clue_paraphrase.cpython-312-pytest-9.1.1.pyc|41408|45056|050c60d763e226c0abaa840eb5110a2c846cf78f7fb9736f571f442d502046bc|PASS|DELETED|
tests/__pycache__/test_frontend_ui_mode_hardening_objective15.cpython-312-pytest-9.1.1.pyc|20170|20480|e4c6403612ec3e483564d6a2d279949969bd6520d502f8a792485c9d4c3361c0|PASS|DELETED|
tests/__pycache__/test_generalized_destination_exit_resolution.cpython-312-pytest-9.1.1.pyc|55768|57344|7bc704751f41502b150861a92b2d33518620ba3084f78670a6f1c8ba5440b825|PASS|DELETED|
tests/__pycache__/test_generalized_destination_exit_resolution.cpython-312.pyc|18757|20480|7218e3e754d44a176f35dd3cfb2dffdd994ecc9d3a7f052569fcebd7e8c09b2a|PASS|DELETED|
tests/__pycache__/test_grounded_marking_action.cpython-312-pytest-9.0.3.pyc|77396|77824|8cfd74b1281aa51da21c117ad7175a8a421656c3d3d28ff800d997cfc78fa0c3|PASS|DELETED|
tests/__pycache__/test_grounded_marking_action.cpython-312-pytest-9.1.1.pyc|77396|77824|8cfd74b1281aa51da21c117ad7175a8a421656c3d3d28ff800d997cfc78fa0c3|PASS|DELETED|
tests/__pycache__/test_grounded_marking_action.cpython-312.pyc|25189|28672|2ec4f53ad637bbc55fe5d7bdc40ab9dc04b72c1512d5db50a31c5a6fbe694e46|PASS|DELETED|
tests/__pycache__/test_grounded_marking_removal.cpython-312-pytest-9.0.3.pyc|98047|98304|f0ac05c60fc201be5f013df1a8e2a4d2799929d49f4640bb2e1013edfb4f8c0b|PASS|DELETED|
tests/__pycache__/test_grounded_marking_removal.cpython-312-pytest-9.1.1.pyc|98047|98304|19b0b62dfb5d8f13791e0c42e41f8eaed440b3602079483791a010760f829d26|PASS|DELETED|
tests/__pycache__/test_grounded_marking_removal.cpython-312.pyc|33261|36864|3e3213ad2d8dab2bfd2640655e4707bcbfb87930b65c65886e4af78b11d121ea|PASS|DELETED|
tests/__pycache__/test_grounded_social_absence_live_model_non_invention.cpython-312-pytest-9.1.1.pyc|54427|57344|eb89604aaeed28986bb6947f37a1baa4dd6ddb62c93bab0c7747190841d7ccf3|PASS|DELETED|
tests/__pycache__/test_intent_parser.cpython-312-pytest-9.1.1.pyc|140526|143360|fdab16ca7857bdec66014aec68617d48df4a355e4d01304c45869ed085eaa7b2|PASS|DELETED|
tests/__pycache__/test_investigation_result_provenance_non_invention.cpython-312-pytest-9.1.1.pyc|93967|94208|146451488444e3068d9fd655ddf21fa1254befe072fa66dfab3e914b5499eb20|PASS|DELETED|
tests/__pycache__/test_listen_question_not_social_capture.cpython-312-pytest-9.1.1.pyc|30617|32768|b7fdafa643657ca894266fd618ef655a4b03a9022c2859723d28a4a586783866|PASS|DELETED|
tests/__pycache__/test_local_observation_followup_social_recovery.cpython-312-pytest-9.1.1.pyc|21891|24576|b1eaec5a726de6721a9173716c8c17ded3eee4a86ac7f8b4c50d418d6335a90e|PASS|DELETED|
tests/__pycache__/test_manual_play_latency.cpython-312-pytest-9.0.3.pyc|51358|53248|55f6e49749f27690b90c5dfb6caeb4b498345227354769e3dd3b570d672e09ce|PASS|DELETED|
tests/__pycache__/test_manual_play_latency.cpython-312-pytest-9.1.1.pyc|51352|53248|361fb92af83a4ea72da054928573262d124de6654c56dab17d4318e1497059fd|PASS|DELETED|
tests/__pycache__/test_narration_state_consistency.cpython-312-pytest-9.0.3.pyc|32499|32768|e01724475193877666cb0d97cf20a03d7f8fed81b4f0fde0ad3f79a297019ec2|PASS|DELETED|
tests/__pycache__/test_narration_state_consistency.cpython-312-pytest-9.1.1.pyc|32499|32768|e01724475193877666cb0d97cf20a03d7f8fed81b4f0fde0ad3f79a297019ec2|PASS|DELETED|
tests/__pycache__/test_narrative_planning_transition_node.cpython-312-pytest-9.0.3.pyc|14488|16384|c728bd499b83b071904c7b145b13aef1b6885c8d33ce9c6b838b2e41a4e347af|PASS|DELETED|
tests/__pycache__/test_narrative_planning_transition_node.cpython-312-pytest-9.1.1.pyc|14500|16384|039533fa04b91cf72f3a364398bd09cd498960651c3fdd5d708874845365ae57|PASS|DELETED|
tests/__pycache__/test_nearby_place_existence_knowledge_ownership.cpython-312-pytest-9.1.1.pyc|118616|118784|55ae0af06a0c1d98224f9bd97ab4c89ef7804123e60afbdd11f7c1089849af26|PASS|DELETED|
tests/__pycache__/test_new_campaign_silent_reset_nc2.cpython-312-pytest-9.1.1.pyc|17537|20480|8d0af3392dffde029d93ae55a19f9f6dad63394f8a2d2c77663c959af843c371|PASS|DELETED|
tests/__pycache__/test_noncombat_runtime_integration.cpython-312-pytest-9.1.1.pyc|18535|20480|7b835622f945e9681cf89d8247d2d0c482449068bc07462a63ac0cd6b75123dd|PASS|DELETED|
tests/__pycache__/test_object_instances.cpython-312-pytest-9.0.3.pyc|63700|65536|98c9da5b43e5338f97f19118df34ff9a434a88a6fdfffc41ea0b903a31007fb7|PASS|DELETED|
tests/__pycache__/test_object_instances.cpython-312-pytest-9.1.1.pyc|63700|65536|98c9da5b43e5338f97f19118df34ff9a434a88a6fdfffc41ea0b903a31007fb7|PASS|DELETED|
tests/__pycache__/test_object_instances.cpython-312.pyc|21505|24576|7b70a3d73dfed2061487b7a9edbddbea177136e7c09f407605d12f11fdff0763|PASS|DELETED|
tests/__pycache__/test_object_marking.cpython-312-pytest-9.0.3.pyc|61478|65536|78f371c6fc43c7631f05d0b3fd360094a1087006080c73bdf39ec7ed6ccc5914|PASS|DELETED|
tests/__pycache__/test_object_marking.cpython-312-pytest-9.1.1.pyc|61478|65536|78f371c6fc43c7631f05d0b3fd360094a1087006080c73bdf39ec7ed6ccc5914|PASS|DELETED|
tests/__pycache__/test_object_marking.cpython-312.pyc|27942|28672|a60bd79e9094fd0c507bf0cf0672ceecbdca114c86639908685a355761f1c797|PASS|DELETED|
tests/__pycache__/test_object_marking_inspection.cpython-312-pytest-9.0.3.pyc|77211|77824|59ce9d33d9466c5b67fa2dacf03ec25199874bb741b18600106130b7c8ca32df|PASS|DELETED|
tests/__pycache__/test_object_marking_inspection.cpython-312-pytest-9.1.1.pyc|77168|77824|1408b2fbb1df8e2049074742815c59bf08bf7de1081dc4068b1981d4403e9fa3|PASS|DELETED|
tests/__pycache__/test_object_observation.cpython-312-pytest-9.0.3.pyc|85994|86016|44dc62ba5806206cd2745e71c4db8e0977665d64e95f80d57e577c808034dd96|PASS|DELETED|
tests/__pycache__/test_object_observation.cpython-312-pytest-9.1.1.pyc|85951|86016|5e28addaa6abc51b886492702df9cb857531392f5211ba57f91a06961d2e5261|PASS|DELETED|
tests/__pycache__/test_object_visibility_authoring.cpython-312-pytest-9.1.1.pyc|104516|106496|76d5e0f692b5ea6eb6eb41dc61d4a75f3132900799a5175edd1b296949a0fe77|PASS|DELETED|
tests/__pycache__/test_opening_start_seam_regressions.cpython-312-pytest-9.1.1.pyc|70868|73728|261350c1e5b572f982f482d89e04118b603c59599db29b29ed1534d8ffc488a3|PASS|DELETED|
tests/__pycache__/test_perception_narration_authority_audible_non_invention.cpython-312-pytest-9.0.3.pyc|74157|77824|58bdaa842f811f61563107d74b90c7e7aea5e582d9e8fb95b3ae35cf3918309b|PASS|DELETED|
tests/__pycache__/test_perception_narration_authority_audible_non_invention.cpython-312-pytest-9.1.1.pyc|74157|77824|58bdaa842f811f61563107d74b90c7e7aea5e582d9e8fb95b3ae35cf3918309b|PASS|DELETED|
tests/__pycache__/test_physical_action_typing_compound_perception_realization.cpython-312-pytest-9.1.1.pyc|86965|90112|3907dd656085a7e3b50d2ca76be18651dac96714650cdd25be6f776fcfdb0ff5|PASS|DELETED|
tests/__pycache__/test_player_marking_observation.cpython-312-pytest-9.0.3.pyc|71985|73728|fb4940f349cb3d6fbd763bf36daf370607f21ef6e50268ec4113f3a054261c95|PASS|DELETED|
tests/__pycache__/test_player_marking_observation.cpython-312-pytest-9.1.1.pyc|71985|73728|fb4940f349cb3d6fbd763bf36daf370607f21ef6e50268ec4113f3a054261c95|PASS|DELETED|
tests/__pycache__/test_player_marking_observation.cpython-312.pyc|27087|28672|72587c16891e8c7133ff8f08aabfae2dc599ed90e848a5a4101efcab366dc265|PASS|DELETED|
tests/__pycache__/test_playtest_startup_readiness.cpython-312-pytest-9.1.1.pyc|16076|16384|416350165f3af33dcf52c23228e19b3ca9e5963aa9c48a493061c275afd02a7a|PASS|DELETED|
tests/__pycache__/test_pr_br_continuation18_immutable_boundary.cpython-312-pytest-9.0.3.pyc|69277|69632|a79ae6fa80b279ebac6ce55c5304357a0faa551045c9644884217e3f9b087018|PASS|DELETED|
tests/__pycache__/test_pr_br_continuation18_immutable_boundary.cpython-312-pytest-9.1.1.pyc|69277|69632|a79ae6fa80b279ebac6ce55c5304357a0faa551045c9644884217e3f9b087018|PASS|DELETED|
tests/__pycache__/test_pr_br_continuation25_semantic_ownership.cpython-312-pytest-9.1.1.pyc|46066|49152|bc0a1fabe9291e40765acc8a50b94d310ad827bf3d7a06119bf001d3dad7f429|PASS|DELETED|
tests/__pycache__/test_pr_br_continuation26_semantic_closure.cpython-312-pytest-9.1.1.pyc|39379|40960|f8461a3caa29fdf1673ad8cd6148132db47dea6005dc726de7b03216069df07d|PASS|DELETED|
tests/__pycache__/test_pr_br_continuation26_semantic_closure.cpython-312.pyc|11630|12288|3ffad5903d3581e96b95839bc1e1ef35e5c228ce78b480c5fb553f9e8f2fe54c|PASS|DELETED|
tests/__pycache__/test_pr_br_qualifier_movement_mixed_intent.cpython-312-pytest-9.1.1.pyc|38824|40960|505245b4f4e80fbba5b660681d7a53a6f1d0057927d270038ec7571b80ce185d|PASS|DELETED|
tests/__pycache__/test_pr_br_structured_realization_envelope.cpython-312-pytest-9.1.1.pyc|26750|28672|e12fc50a6aed8132c53525c80ded6005163da1a0543e3da362f65b00629b4ff0|PASS|DELETED|
tests/__pycache__/test_pr_bu_lexical_scope.cpython-312-pytest-9.0.3.pyc|32836|36864|ca5156ff2bc120071aa81e134e5a37b3c2d1db0c4f8127f0adb4a1be307e6135|PASS|DELETED|
tests/__pycache__/test_pr_bu_lexical_scope.cpython-312-pytest-9.1.1.pyc|32836|36864|ca5156ff2bc120071aa81e134e5a37b3c2d1db0c4f8127f0adb4a1be307e6135|PASS|DELETED|
tests/__pycache__/test_pr_bu_narration_claim_composition.cpython-312-pytest-9.1.1.pyc|75067|77824|614281d271655ebc114a70e35cec26562785084b7329daa188c900f5d1f5a4d0|PASS|DELETED|
tests/__pycache__/test_pr_bw_narration_only_envelope.cpython-312-pytest-9.0.3.pyc|22708|24576|798d7625a6fb9a1f559570468bd26be6e957936e09071b4eb8d7342c7531a5ce|PASS|DELETED|
tests/__pycache__/test_pr_bw_narration_only_envelope.cpython-312-pytest-9.1.1.pyc|22708|24576|798d7625a6fb9a1f559570468bd26be6e957936e09071b4eb8d7342c7531a5ce|PASS|DELETED|
tests/__pycache__/test_pr_cc_social_reply_reconciliation.cpython-312-pytest-9.1.1.pyc|14991|16384|5054d7821677c416bb189690f837791ea3f7c4c06c10a611a0481e76be017b44|PASS|DELETED|
tests/__pycache__/test_pr_ck_ordinary_resolver_selection.cpython-312-pytest-9.1.1.pyc|26425|28672|d499f83a9ccb7a2ab3a1f4c6f9b86ce8a9781eba8c5ac1c29d8f5fe338227e10|PASS|DELETED|
tests/__pycache__/test_pr_cp_authorized_finalization.cpython-312-pytest-9.1.1.pyc|31887|32768|a1e09e488d7adf388e21694778db1ae70adcd6a541e31d3e99cbb736abc062de|PASS|DELETED|
tests/__pycache__/test_pr_cw_social_context_projection.cpython-312-pytest-9.0.3.pyc|35687|36864|df47ce3aebdc2e127a99cc451371d105b94c7515aca52440f00dda004f60ecbe|PASS|DELETED|
tests/__pycache__/test_pr_cw_social_context_projection.cpython-312-pytest-9.1.1.pyc|35687|36864|7ecdaf44e54a60f93b7a97a6e9a059e56e7eb372b729728f2223e3485e8cb920|PASS|DELETED|
tests/__pycache__/test_pr_cx_authority_assurance.cpython-312-pytest-9.0.3.pyc|9500|12288|8da1dd181898e55f896e3a1233781ab91cf10e87fa2a25234254675999828dae|PASS|DELETED|
tests/__pycache__/test_pr_cx_authority_assurance.cpython-312-pytest-9.1.1.pyc|9500|12288|8da1dd181898e55f896e3a1233781ab91cf10e87fa2a25234254675999828dae|PASS|DELETED|
tests/__pycache__/test_pr_db_speaker_grounding.cpython-312-pytest-9.0.3.pyc|36863|36864|94534f633984b406050076e72f5a25099afb60a7a34dff8de810f187b045b2d5|PASS|DELETED|
tests/__pycache__/test_pr_db_speaker_grounding.cpython-312-pytest-9.1.1.pyc|36872|40960|71c8cf190ed6a2248564cd75081b21d45238b163d3a12793b2f8c8249dfb8c04|PASS|DELETED|
tests/__pycache__/test_pr_de_exact_contract_deduplication.cpython-312-pytest-9.0.3.pyc|23500|24576|331d298a1d292b94a87760e34400f157044d768066d060047a3e222f8b6e51cc|PASS|DELETED|
tests/__pycache__/test_pr_de_exact_contract_deduplication.cpython-312-pytest-9.1.1.pyc|23477|24576|d3fd6812740232115569ab99692796456dd27f282c3b34508edda204169debb0|PASS|DELETED|
tests/__pycache__/test_pr_dh_live_interpretation.cpython-312-pytest-9.1.1.pyc|4638|8192|69caa05e3d0433adb04c9a395760c677dd87a65bb8c79ed7f38da59b9343f079|PASS|DELETED|
tests/__pycache__/test_pr_do_authority_separation.cpython-312-pytest-9.0.3.pyc|49638|53248|43290f4e7686ae5a007bd387d374e67d15376306f2c1c65b4b59db9b26af3f26|PASS|DELETED|
tests/__pycache__/test_pr_do_authority_separation.cpython-312-pytest-9.1.1.pyc|49638|53248|43290f4e7686ae5a007bd387d374e67d15376306f2c1c65b4b59db9b26af3f26|PASS|DELETED|
tests/__pycache__/test_pr_dr_live_vertical_slice.cpython-312-pytest-9.0.3.pyc|42493|45056|13c67925ac8e2c03528e2fea587398ff4cd053962ab977b82953883e153188b9|PASS|DELETED|
tests/__pycache__/test_pr_dr_live_vertical_slice.cpython-312-pytest-9.1.1.pyc|42493|45056|13c67925ac8e2c03528e2fea587398ff4cd053962ab977b82953883e153188b9|PASS|DELETED|
tests/__pycache__/test_pr_du_player_pipeline.cpython-312-pytest-9.0.3.pyc|40377|40960|673eb159f2951d9721234d56bd60397e45c077b4c8403c07d75a152dee6c536e|PASS|DELETED|
tests/__pycache__/test_pr_du_player_pipeline.cpython-312-pytest-9.1.1.pyc|40377|40960|673eb159f2951d9721234d56bd60397e45c077b4c8403c07d75a152dee6c536e|PASS|DELETED|
tests/__pycache__/test_pr_dy_live_gameplay.cpython-312-pytest-9.1.1.pyc|28297|28672|4e745c1533f9a8c5c371c4a742a1061a15c931736e9271841c050353195d22f9|PASS|DELETED|
tests/__pycache__/test_pr_ea_conversational_orchestration.cpython-312-pytest-9.1.1.pyc|26409|28672|10fc119f66aaa101dc240a8e9e723adfe26eaa298da0d71171a2aa914f00a28e|PASS|DELETED|
tests/__pycache__/test_pr_ec_movement_partial_intent.cpython-312-pytest-9.1.1.pyc|62430|65536|376f0f756f540e1ccd70bac10be826a23ea3aaeb7a304d20fc5acccdf7a0938a|PASS|DELETED|
tests/__pycache__/test_pr_ed_provider_efficiency.cpython-312-pytest-9.0.3.pyc|27321|28672|65a13fcd3fd3540151dac47970c576fc1a3d6359760b5d4f0a0583018f2974aa|PASS|DELETED|
tests/__pycache__/test_pr_ed_provider_efficiency.cpython-312-pytest-9.1.1.pyc|27321|28672|65a13fcd3fd3540151dac47970c576fc1a3d6359760b5d4f0a0583018f2974aa|PASS|DELETED|
tests/__pycache__/test_pr_ef_gm_authority.cpython-312-pytest-9.1.1.pyc|41747|45056|50e8f40854ae12f16363cc82cb9ccabb68e1de53d5d1d88dfdb203b005f56b24|PASS|DELETED|
tests/__pycache__/test_pr_ef_r1_semantic_handoff.cpython-312-pytest-9.1.1.pyc|38660|40960|3a4752faf697bb8b34a057885687e3e486618623a748869ec4cc735916768a27|PASS|DELETED|
tests/__pycache__/test_pr_ef_r2_social_authority.cpython-312-pytest-9.1.1.pyc|27318|28672|a08cff168f8609741ddc00bcc62a0923bd9be017b7c86654f753dfe190af7587|PASS|DELETED|
tests/__pycache__/test_pr_ef_r4_authorization.cpython-312-pytest-9.1.1.pyc|46357|49152|4c46dec106461908e78f6f834de4fa39f704dd41a88ffbcac71fee6f5aaa05f2|PASS|DELETED|
tests/__pycache__/test_pr_eg_dialogue_quality.cpython-312-pytest-9.1.1.pyc|26272|28672|8e0f5ce9eaf11a634a26f7048da390da1fba44f0b51be2ec7c6409b3876c703a|PASS|DELETED|
tests/__pycache__/test_pr_eg_r1_continuity.cpython-312-pytest-9.0.3.pyc|30765|32768|66e231bebbb629785a1219ddaeac1ed14aa0b6d852dba4477254f80da0d87334|PASS|DELETED|
tests/__pycache__/test_pr_eg_r1_continuity.cpython-312-pytest-9.1.1.pyc|30765|32768|66e231bebbb629785a1219ddaeac1ed14aa0b6d852dba4477254f80da0d87334|PASS|DELETED|
tests/__pycache__/test_pr_eg_r2c_r2_reference_eligibility.cpython-312-pytest-9.1.1.pyc|64632|65536|60dec886508f5753be495f8fe4cc298e6e026c7c3f1905a9145b8f726f4bf1e0|PASS|DELETED|
tests/__pycache__/test_pr_eg_r2c_speech_adoption.cpython-312-pytest-9.1.1.pyc|82014|86016|54d9b1ed31aca31949127fd9a11ae8cc90cfcd75e91bd25a141cb98b130aa8bc|PASS|DELETED|
tests/__pycache__/test_pr_eg_r3_expressive_dialogue.cpython-312-pytest-9.1.1.pyc|59328|61440|dbb0a364b55b87a084fa2cf871a14c853321d5277307bebcf87bbdc5dff056a4|PASS|DELETED|
tests/__pycache__/test_pr_eg_r3_r1_expression_semantics.cpython-312-pytest-9.1.1.pyc|82091|86016|a32b2037cd1e19840398a07344202bd80160aed35765768fb2d77b8722cc87b2|PASS|DELETED|
tests/__pycache__/test_pr_eg_r4_r1_delivery_integrity.cpython-312-pytest-9.1.1.pyc|39311|40960|fefb62778c32321d5b33c278537e1af7b50b3c2bb6c08ccebbee8eb80d1ebe30|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_r1_disclosure_boundary.cpython-312-pytest-9.1.1.pyc|31555|32768|bb425ebcf904ba854bbf77f076ce566fd4ef5ac74ba69ee129774888f420d30e|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_r1_r1_provenance.cpython-312-pytest-9.1.1.pyc|57854|61440|1fb37cbe1a4495cb1a815237a586991b34414ee05e1ebf4fa73feeee4e2e6803|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_r2_grounding.cpython-312-pytest-9.1.1.pyc|34226|36864|c19f639660b3c9d4d6bbf4ed22844cc41b9f56f1972329d59e5edbaa50842528|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_r2_r1_referents.cpython-312-pytest-9.1.1.pyc|62954|65536|0728ab5bc6bd2838c467bd30c5db71810c08385c559e9263c6febe4e7535436d|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_r2_r2_operations.cpython-312-pytest-9.1.1.pyc|43199|45056|e2456d38fae5371130ac7ec73cee911d431ac63e7fedf2f84eab5e79e9a48899|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_r3_harness.cpython-312-pytest-9.1.1.pyc|15730|16384|bb06cd02b50e2bc418e64868bd78518427a66aea46cf8d6718a9b555644d6d9d|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_r3_r1_candidates.cpython-312-pytest-9.1.1.pyc|126854|126976|761ee45d15eab645dcca74714a2ee0084bc5e862f1b680ed4b466edadfb081db|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_r4_correspondence.cpython-312-pytest-9.1.1.pyc|13413|16384|65c3327954778cfe7e93cda4d6dd4ee99f7b0c44d671702fd5d5cc0ff5aa3c29|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_r4_r1_alignment.cpython-312-pytest-9.1.1.pyc|21884|24576|5edd3e525628e2478ec8dc135c5e1bed7219a086178c61596ec474cf39cc8541|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_r5_diagnostic.cpython-312-pytest-9.1.1.pyc|13376|16384|8162b815be7c79e2753a4900be06fb482a0d9b058285c38b4c2a931ee31e8dda|PASS|DELETED|
tests/__pycache__/test_pr_eg_r6_unified_semantic_planning.cpython-312-pytest-9.1.1.pyc|95629|98304|61fc65e89f6bd6b3cb612923b4aafea118fcd70c81e3d74309a069b24e070af9|PASS|DELETED|
tests/__pycache__/test_pr_play_04_opening_integrity.cpython-312-pytest-9.1.1.pyc|67495|69632|fe833c439e461eee94e099075fff81a2b8218cbbec29be37eecfea0984829409|PASS|DELETED|
tests/__pycache__/test_pr_play_05_diagnostics.cpython-312-pytest-9.1.1.pyc|45817|49152|9dd724634eef34739c75b75b48ff66245604ede279b35fe828dd64d9fd917ee4|PASS|DELETED|
tests/__pycache__/test_pr_play_06_opening_budget.cpython-312-pytest-9.1.1.pyc|18806|20480|151edc0bc5d08ff2653ad28761286255dff5bdc96c2e9c618883c70328e2256f|PASS|DELETED|
tests/__pycache__/test_pr_play_10_overlays.cpython-312-pytest-9.1.1.pyc|33215|36864|248071f6ee2c09e5827477c9cd2dfebe09a09d4bcb6f34957052a40f07ce2465|PASS|DELETED|
tests/__pycache__/test_pr_play_13_opening_renderer.cpython-312-pytest-9.1.1.pyc|71423|73728|893fab44793844a825ce66d4083754926b36b1b2640711178a4b155b838f913c|PASS|DELETED|
tests/__pycache__/test_pr_play_18_contract_alignment.cpython-312-pytest-9.1.1.pyc|38468|40960|0a22c0aca1ac5285e15e30fdf1f6a8aaf53778bb753f1543958dba3f1951241b|PASS|DELETED|
tests/__pycache__/test_pr_play_20_response_confidentiality.cpython-312-pytest-9.1.1.pyc|38245|40960|04e6f97aa4c4cce268ebec899956aec3f11ff68eacd19d53129572afeb15bab0|PASS|DELETED|
tests/__pycache__/test_pr_play_21_privileged_reads.cpython-312-pytest-9.1.1.pyc|36298|36864|2fc7f8d7f69274761c37bba61c336cc1376065613ba00f7ad759e1ed01c8621e|PASS|DELETED|
tests/__pycache__/test_pr_play_23_harness.cpython-312-pytest-9.1.1.pyc|26141|28672|d848a3efafe64fc110840d8035b4173701fb9809f112d31703c0b9db16aaa367|PASS|DELETED|
tests/__pycache__/test_pr_play_23_local_interaction.cpython-312-pytest-9.1.1.pyc|32889|36864|58698ba26689d4ffed8d4d873045be30fd03f1c28c5b54398645f080143b9a19|PASS|DELETED|
tests/__pycache__/test_pr_play_25_public_fact_dialogue.cpython-312-pytest-9.1.1.pyc|36861|36864|4b3bc57bb2b24dfb7567d837cc4345303a47cd429f403c3d773829ebc8098249|PASS|DELETED|
tests/__pycache__/test_pr_play_27_expression_recovery.cpython-312-pytest-9.1.1.pyc|40974|45056|d434f4aad4f562d9824c8e0328ee74dfe9a278a3c939065e712aa97d18bd395d|PASS|DELETED|
tests/__pycache__/test_pr_play_28_baseline_reproduction.cpython-312-pytest-9.1.1.pyc|19489|20480|2452fee13e2ca3166ae9b0ba2887cc05a662d72960555d2cb80e1ac44094fc48|PASS|DELETED|
tests/__pycache__/test_pr_play_28_baseline_reproduction.cpython-312.pyc|10096|12288|3a7d6b644fb6dcfcde25506df90b9987f4df53801189e1dd5b186ae36cdbb954|PASS|DELETED|
tests/__pycache__/test_pr_play_28_topic_authority.cpython-312-pytest-9.1.1.pyc|35317|36864|a4f2653a86f05c33f7e9f4ec253f5bbc142325bc1ceecf480f1ab7e361bdb36c|PASS|DELETED|
tests/__pycache__/test_pr_play_33_process_ownership.cpython-312-pytest-9.1.1.pyc|22787|24576|762c7ffe5ea72274446b1c3647770f09059306cd339dcb634bad138754b4f565|PASS|DELETED|
tests/__pycache__/test_pr_play_34_readiness_diagnostics.cpython-312-pytest-9.1.1.pyc|19681|20480|b0e5ddfcb6020a17cd7ebb1b4f1ebb3869dfb9bf1bd79d7133449624eedf9b02|PASS|DELETED|
tests/__pycache__/test_pr_play_36_opening_rejection.cpython-312-pytest-9.1.1.pyc|34538|36864|69aff2f1265858d1a284b491284ecb20ee99ad8b39b341b2edccee58240eb2f6|PASS|DELETED|
tests/__pycache__/test_pr_play_37_opening_recovery.cpython-312-pytest-9.1.1.pyc|89774|90112|780989f6e6f85a0afff919bd037f6cd29e509c21054000abfe49cac3d7bc64fc|PASS|DELETED|
tests/__pycache__/test_pr_play_39_action_admission.cpython-312-pytest-9.0.3.pyc|67300|69632|ac81108816b75b1f7e7ba78bb702311c32957569239cb458338738ffe0500531|PASS|DELETED|
tests/__pycache__/test_pr_play_39_action_admission.cpython-312-pytest-9.1.1.pyc|67300|69632|ac81108816b75b1f7e7ba78bb702311c32957569239cb458338738ffe0500531|PASS|DELETED|
tests/__pycache__/test_pr_play_39_action_admission.cpython-312.pyc|25833|28672|95cf5a4c5aa101ab7252760b1544442729274f188248db2ce7fba5aac7a82462|PASS|DELETED|
tests/__pycache__/test_pr_play_40_scenario_generalization.cpython-312-pytest-9.1.1.pyc|50309|53248|905c2d67ee4e39343d3256f1236d2f551b27bf5925f30002fda745afa65b9fd3|PASS|DELETED|
tests/__pycache__/test_pr_play_42_evidence_boundaries.cpython-312-pytest-9.1.1.pyc|96372|98304|a3b3a5f26e16e0c9f59063c7ec2fb8c2f9203d1cd8c30cd3d63416a2437d1755|PASS|DELETED|
tests/__pycache__/test_pr_play_44_information_delivery.cpython-312-pytest-9.1.1.pyc|48306|49152|67464a7f86e36455b6f327c2f4abbc0183819fa2f6655309af70713db410b9a0|PASS|DELETED|
tests/__pycache__/test_pr_play_45_narration_authority.cpython-312-pytest-9.0.3.pyc|37271|40960|75a84201affefbc9458e55af8413adb4ce2e59ad766855a93179d10263f6b4be|PASS|DELETED|
tests/__pycache__/test_pr_play_45_narration_authority.cpython-312-pytest-9.1.1.pyc|37271|40960|75a84201affefbc9458e55af8413adb4ce2e59ad766855a93179d10263f6b4be|PASS|DELETED|
tests/__pycache__/test_pr_play_46_mechanical_boundary.cpython-312-pytest-9.0.3.pyc|28606|28672|e131e7aa62c5a407b613d66c67ac9a2543fd02b16582259cd213d884364c1981|PASS|DELETED|
tests/__pycache__/test_pr_play_46_mechanical_boundary.cpython-312-pytest-9.1.1.pyc|28606|28672|8f1f9d9a338690cef11704b15838be45735acfe4768f702b824d37bd6696124e|PASS|DELETED|
tests/__pycache__/test_pr_play_47_controlled_renderer.cpython-312-pytest-9.0.3.pyc|73682|73728|e41e19f8dd6be0c184a10d3ecbbb2a2333138221c8500de6f4e2a6b9f0947d77|PASS|DELETED|
tests/__pycache__/test_pr_play_47_controlled_renderer.cpython-312-pytest-9.1.1.pyc|73682|73728|e41e19f8dd6be0c184a10d3ecbbb2a2333138221c8500de6f4e2a6b9f0947d77|PASS|DELETED|
tests/__pycache__/test_pr_play_47_controlled_renderer.cpython-312.pyc|35933|36864|c219ec438bbe225e9cff16260fdac498624ba7b5674851a29b07f0042cdd42b9|PASS|DELETED|
tests/__pycache__/test_pr_play_49_anchored_narration.cpython-312-pytest-9.1.1.pyc|73033|73728|cf7ad704122135dff394c557f307a751f43c9ffc822532927ccf258b166f2d9e|PASS|DELETED|
tests/__pycache__/test_pr_play_51_geography_grounding.cpython-312-pytest-9.0.3.pyc|33488|36864|81eb39af24582c8f4448dd587600319200c16bdf22cdcd03ab912ca3f7e76ece|PASS|DELETED|
tests/__pycache__/test_pr_play_51_geography_grounding.cpython-312-pytest-9.1.1.pyc|33488|36864|81eb39af24582c8f4448dd587600319200c16bdf22cdcd03ab912ca3f7e76ece|PASS|DELETED|
tests/__pycache__/test_pr_play_52_quarantined_integration.cpython-312-pytest-9.0.3.pyc|83488|86016|77c98aef5d3a14b9975d0ebd0592c1137d79e366fb903cbc2a13860ee2ed1f98|PASS|DELETED|
tests/__pycache__/test_pr_play_52_quarantined_integration.cpython-312-pytest-9.1.1.pyc|83488|86016|8e03f2c7dff70177085932a989fd58d27097988682425243430df5168e9b6e76|PASS|DELETED|
tests/__pycache__/test_pr_play_52_quarantined_integration.cpython-312.pyc|39647|40960|0deed20fec9f9f076a7a10d646f411795aabee1c1a08ec71b34b9ce98dccd2d7|PASS|DELETED|
tests/__pycache__/test_pr_play_53_quarantined_live.cpython-312-pytest-9.0.3.pyc|71695|73728|b531796198ffc12a4c385d0778477a08e1667cd39dc1af80ccc3b5f29622f559|PASS|DELETED|
tests/__pycache__/test_pr_play_53_quarantined_live.cpython-312-pytest-9.1.1.pyc|71695|73728|b531796198ffc12a4c385d0778477a08e1667cd39dc1af80ccc3b5f29622f559|PASS|DELETED|
tests/__pycache__/test_pr_play_54_consequential_validation.cpython-312-pytest-9.0.3.pyc|46274|49152|04c1ef0166dbbdeb9fcfd4ce4879752ccdc2820e3c46d511884472fc6fc6d5be|PASS|DELETED|
tests/__pycache__/test_pr_play_54_consequential_validation.cpython-312-pytest-9.1.1.pyc|46274|49152|5c96f31bfa943f785b4da54ee00ac1201ede0ee166d612c32fccff1e58ae2246|PASS|DELETED|
tests/__pycache__/test_pr_play_55_discovery_claims.cpython-312-pytest-9.0.3.pyc|26218|28672|39970b9e03f70f08f6bd4cd569176988f66080513eb41ede32cc57e7cd618a71|PASS|DELETED|
tests/__pycache__/test_pr_play_55_discovery_claims.cpython-312-pytest-9.1.1.pyc|26218|28672|39970b9e03f70f08f6bd4cd569176988f66080513eb41ede32cc57e7cd618a71|PASS|DELETED|
tests/__pycache__/test_pr_play_55_holdout.cpython-312-pytest-9.0.3.pyc|4390|8192|da960c3387004dcca3f456550d08b2172ffc2947a11165df9683d964487c6e6f|PASS|DELETED|
tests/__pycache__/test_pr_play_55_holdout.cpython-312-pytest-9.1.1.pyc|4390|8192|da960c3387004dcca3f456550d08b2172ffc2947a11165df9683d964487c6e6f|PASS|DELETED|
tests/__pycache__/test_pr_play_57_integrated_narration.cpython-312-pytest-9.0.3.pyc|26472|28672|2310d090b636f5d541bcfcc0efc374e7d214bedd83927298ac2f812d1ec6ef13|PASS|DELETED|
tests/__pycache__/test_pr_play_57_integrated_narration.cpython-312-pytest-9.1.1.pyc|26472|28672|2310d090b636f5d541bcfcc0efc374e7d214bedd83927298ac2f812d1ec6ef13|PASS|DELETED|
tests/__pycache__/test_pr_play_57_integrated_narration.cpython-312.pyc|13496|16384|124036864082bf57bdcd5e72015ecbebeb31010af632745e763bbfb438e61e04|PASS|DELETED|
tests/__pycache__/test_pr_play_58_semantic_coverage.cpython-312-pytest-9.0.3.pyc|4556|8192|a8f5f854908fde7de6bf6909941b063babf558021ff0008d09f8ef69e22ce2c4|PASS|DELETED|
tests/__pycache__/test_pr_play_58_semantic_coverage.cpython-312-pytest-9.1.1.pyc|4556|8192|a8f5f854908fde7de6bf6909941b063babf558021ff0008d09f8ef69e22ce2c4|PASS|DELETED|
tests/__pycache__/test_pr_play_59_persistent_consequences.cpython-312-pytest-9.0.3.pyc|11411|12288|f8f2801a058341dca8cd027b1c23be6a4e6384f98cb4aad66457db9a582e486d|PASS|DELETED|
tests/__pycache__/test_pr_play_59_persistent_consequences.cpython-312-pytest-9.1.1.pyc|11411|12288|f8f2801a058341dca8cd027b1c23be6a4e6384f98cb4aad66457db9a582e486d|PASS|DELETED|
tests/__pycache__/test_pr_play_60_gameplay_readiness.cpython-312-pytest-9.1.1.pyc|8394|12288|57e16b7c5027150da04ecde6e80d7d5ccd663925333171fe565c12c981c25068|PASS|DELETED|
tests/__pycache__/test_pr_play_60_inventory_projection.cpython-312-pytest-9.0.3.pyc|13018|16384|602c556456ed00212b93141609b7a3840eae7f0b271ed66b55d8a9072883f8da|PASS|DELETED|
tests/__pycache__/test_pr_play_60_inventory_projection.cpython-312-pytest-9.1.1.pyc|13018|16384|602c556456ed00212b93141609b7a3840eae7f0b271ed66b55d8a9072883f8da|PASS|DELETED|
tests/__pycache__/test_pr_play_61_player_facing.cpython-312-pytest-9.0.3.pyc|38744|40960|9521cb722966ab428265c393e65c9e1c57145c10e6d386b0576466e11d1ff59c|PASS|DELETED|
tests/__pycache__/test_pr_play_61_player_facing.cpython-312-pytest-9.1.1.pyc|38744|40960|9521cb722966ab428265c393e65c9e1c57145c10e6d386b0576466e11d1ff59c|PASS|DELETED|
tests/__pycache__/test_pr_play_62_investigation_quality.cpython-312-pytest-9.0.3.pyc|20907|24576|8dd98a33c783d10e5f58f70d039e572a020b1ee913f3b85a87acb906deab88b7|PASS|DELETED|
tests/__pycache__/test_pr_play_62_investigation_quality.cpython-312-pytest-9.1.1.pyc|20907|24576|8dd98a33c783d10e5f58f70d039e572a020b1ee913f3b85a87acb906deab88b7|PASS|DELETED|
tests/__pycache__/test_pr_play_63_disclosure.cpython-312-pytest-9.0.3.pyc|18889|20480|3206a4f7fb59b7c042c5b3287c8637b872ac203e62b0b65f3a9e07e247070dc9|PASS|DELETED|
tests/__pycache__/test_pr_play_63_disclosure.cpython-312-pytest-9.1.1.pyc|18889|20480|3206a4f7fb59b7c042c5b3287c8637b872ac203e62b0b65f3a9e07e247070dc9|PASS|DELETED|
tests/__pycache__/test_pr_play_63_disclosure.cpython-312.pyc|8422|12288|d9c26d96e809e66b55c2a87eee2fa3ad85ae276c194c2b228cc6a59c463171b3|PASS|DELETED|
tests/__pycache__/test_pr_play_64_discovery_language.cpython-312-pytest-9.0.3.pyc|5398|8192|4909ded7b2becd999e90780a56e032ee7b52a57d94db630de12a7ce193ae5712|PASS|DELETED|
tests/__pycache__/test_pr_play_64_discovery_language.cpython-312-pytest-9.1.1.pyc|5398|8192|4909ded7b2becd999e90780a56e032ee7b52a57d94db630de12a7ce193ae5712|PASS|DELETED|
tests/__pycache__/test_pr_play_65_authoritative_disclosure.cpython-312-pytest-9.0.3.pyc|28918|32768|469eade19fb514ca6c01c0d4f3186c7ca8488dd8d5835bc8dcd4424f782a52d8|PASS|DELETED|
tests/__pycache__/test_pr_play_65_authoritative_disclosure.cpython-312-pytest-9.1.1.pyc|28918|32768|4f116905ca14def1dbfb4e8e8e1a331d4d871d75bfb9081c021f7b74e21e2718|PASS|DELETED|
tests/__pycache__/test_pr_play_66_publication.cpython-312-pytest-9.1.1.pyc|24999|28672|5da77d42087ddedf39cdc8ece52c47e5492cd92a9107e186a0c36cea7c8d4d50|PASS|DELETED|
tests/__pycache__/test_pr_play_66_publication.cpython-312.pyc|14864|16384|0dfc671ccb79002c1440e8e7879f559c10bb4cd39559d29bd6fe054eff1c518f|PASS|DELETED|
tests/__pycache__/test_pr_play_67_player_projection.cpython-312-pytest-9.1.1.pyc|26553|28672|37b8f9229b475e2851e974926b701de9f1a4ea7c7d849e7c2882c10d4248f4b3|PASS|DELETED|
tests/__pycache__/test_pr_play_68_structured_publication.cpython-312-pytest-9.1.1.pyc|27452|28672|b16474999527270c11bd620559a48d8069e75a80b48a09bc236aacf285d039f8|PASS|DELETED|
tests/__pycache__/test_pr_play_68_structured_publication.cpython-312.pyc|12621|16384|5dfb6920f0f118531d2f8176297e08f52800713dd5c9e80c1ca337eefe90bf28|PASS|DELETED|
tests/__pycache__/test_pr_play_69_target_references.cpython-312-pytest-9.1.1.pyc|23656|24576|a7947c8febc213ccca9697b4ec0b37eac76a1c3fe9533902c5e05a05fd3e16ab|PASS|DELETED|
tests/__pycache__/test_pr_play_70_branching.cpython-312-pytest-9.1.1.pyc|32169|32768|dd8c556f1abc60cdd663883de50423e7dbc0b34338307bd6fdb2339a5542497a|PASS|DELETED|
tests/__pycache__/test_pr_play_70_branching.cpython-312.pyc|13269|16384|91e53021fc5ea15953cafb4b529d43b852e6f47adc731b131f2c8fab5bdec962|PASS|DELETED|
tests/__pycache__/test_pr_play_71_lifecycle.cpython-312-pytest-9.0.3.pyc|30404|32768|03882b5445d1afb37dbd032ae4ccef0e228ad571f76cd15b8ce7db4c9b89f4f0|PASS|DELETED|
tests/__pycache__/test_pr_play_71_lifecycle.cpython-312-pytest-9.1.1.pyc|30404|32768|03882b5445d1afb37dbd032ae4ccef0e228ad571f76cd15b8ce7db4c9b89f4f0|PASS|DELETED|
tests/__pycache__/test_pr_play_71_lifecycle.cpython-312.pyc|13398|16384|c08333dac01e85e3b5438ed0be93ab85689d5e60151f47f3f88994ae4078226e|PASS|DELETED|
tests/__pycache__/test_pr_play_71_persistence_recovery.cpython-312-pytest-9.1.1.pyc|19219|20480|c281850c5874d2d95e99493c0d096fe8fe3e7f2ebc6ad55104a1017071161cc7|PASS|DELETED|
tests/__pycache__/test_pr_play_71v_verification.cpython-312-pytest-9.1.1.pyc|110956|114688|973b1e92919dbd59ed7b65adf401eb09282b0ec11421eec3b9dfa9a931953f88|PASS|DELETED|
tests/__pycache__/test_pr_play_71v_verification.cpython-312.pyc|35392|36864|8bf70828e7b3b47d68fe63e201cad045d12cc4a9cf31937654201e6e0411ce2c|PASS|DELETED|
tests/__pycache__/test_pr_play_72_boundary_repairs.cpython-312-pytest-9.1.1.pyc|6718|8192|655ad3e6011042f1296f7f6625c7069e79c245075c03d7e6561ba72b62fbec46|PASS|DELETED|
tests/__pycache__/test_pr_play_72_failures.cpython-312-pytest-9.1.1.pyc|16957|20480|f07ab0f6a16281cd12942ed7932fc2aab285e4c6bc1376fb0ada137fdd928ba9|PASS|DELETED|
tests/__pycache__/test_pr_play_72_initiative.cpython-312-pytest-9.1.1.pyc|28035|28672|46812aadb557654b5d2f454bba29fbb72d608c0351dc73051c4cc68f1a1bbec3|PASS|DELETED|
tests/__pycache__/test_pr_play_72_supplemental.cpython-312-pytest-9.1.1.pyc|17264|20480|9236f77a7bcc58ffb22a2ea36df6ba07710f118ccba9205b8178ac122855c4b2|PASS|DELETED|
tests/__pycache__/test_pr_play_72v_post_holdout.cpython-312-pytest-9.1.1.pyc|11000|12288|e51ca0f7807fbfa9a659efebd03115f189e8fa0999962699120a424936fa37c2|PASS|DELETED|
tests/__pycache__/test_pr_play_72v_resolution.cpython-312-pytest-9.1.1.pyc|26142|28672|d316d8e8b0c783ecfa5f20f4c857924e6f3263368cef46002454da4babab6a4b|PASS|DELETED|
tests/__pycache__/test_pr_play_73_general_purpose.cpython-312-pytest-9.1.1.pyc|55207|57344|17f3b5ea184bf5c4f09e25e2fb81e8b893da7e53774844c85162921b19b656fa|PASS|DELETED|
tests/__pycache__/test_pr_play_73_inherited_safety.cpython-312-pytest-9.1.1.pyc|31512|32768|0454abd65e932e3caa6068f23e55f74637bf2e54daf72863501da249faf64260|PASS|DELETED|
tests/__pycache__/test_pr_play_74_controlled_world.cpython-312-pytest-9.1.1.pyc|31212|32768|f4edd56deb63e090d6c8807b999a14c5ce79a414dd19276dd2430635ad7a90a1|PASS|DELETED|
tests/__pycache__/test_pr_play_75_dynamic_npcs.cpython-312-pytest-9.1.1.pyc|51798|53248|0ba00ce2c9d8e7c91a3f259417f2f4a42cd054e0615e480595cdb1c3727191be|PASS|DELETED|
tests/__pycache__/test_pr_play_75_dynamic_npcs.cpython-312.pyc|19631|20480|bfacfd47af019de7366f45d68bc939b473737bb8d6c3d23053ab591f11f3d4b7|PASS|DELETED|
tests/__pycache__/test_pr_play_75_persistence.cpython-312-pytest-9.1.1.pyc|12147|12288|5210d43d0e5adcbaaffda1cb61cce51277f35b9467ff624bf6032a11fb22a970|PASS|DELETED|
tests/__pycache__/test_pr_play_76_physical.cpython-312-pytest-9.0.3.pyc|121575|122880|755fa1acbc354c4a889e5f3af49c00a3b79a8609857c0f50dc9c4655e4945840|PASS|DELETED|
tests/__pycache__/test_pr_play_76_physical.cpython-312-pytest-9.1.1.pyc|121575|122880|755fa1acbc354c4a889e5f3af49c00a3b79a8609857c0f50dc9c4655e4945840|PASS|DELETED|
tests/__pycache__/test_pr_play_76_physical.cpython-312.pyc|39238|40960|5553c38fdc577643df22b53b82b094b24600838453f2589fc02557b9e7345179|PASS|DELETED|
tests/__pycache__/test_pr_play_78_integrated.cpython-312-pytest-9.0.3.pyc|49973|53248|5a976aa6cef16ee6f08262ea33290c0f6e6062a6385d890379ef53be9b055321|PASS|DELETED|
tests/__pycache__/test_pr_play_78_integrated.cpython-312-pytest-9.1.1.pyc|49973|53248|fcdb3fad6b7d07a8902c14aa6bc4f17ec7517fca5931dc0e39c327fa73c28e1a|PASS|DELETED|
tests/__pycache__/test_pr_play_78_integrated.cpython-312.pyc|27229|28672|936a624eb124c8798af6ebd5c82490c98b50c0d2f7bc5b83393c2489bc99ae49|PASS|DELETED|
tests/__pycache__/test_pr_play_78a_authored.cpython-312-pytest-9.0.3.pyc|52580|53248|da8af02c79a1883b85b87153a96c78643f41de163302bc68ddd45a66090d2823|PASS|DELETED|
tests/__pycache__/test_pr_play_78a_authored.cpython-312-pytest-9.1.1.pyc|52580|53248|da8af02c79a1883b85b87153a96c78643f41de163302bc68ddd45a66090d2823|PASS|DELETED|
tests/__pycache__/test_pr_play_preseal_authority.cpython-312-pytest-9.0.3.pyc|39122|40960|4fc04967b180e2101b20e366364f783e36f2cce71c1a95dd648877983354c9d5|PASS|DELETED|
tests/__pycache__/test_pr_play_preseal_authority.cpython-312-pytest-9.1.1.pyc|39122|40960|4fc04967b180e2101b20e366364f783e36f2cce71c1a95dd648877983354c9d5|PASS|DELETED|
tests/__pycache__/test_pr_play_t05_composition.cpython-312-pytest-9.0.3.pyc|21125|24576|6a3a3c4837c1d852664e52301cf42c3345593e19ad1f54365d309e5fd937be2b|PASS|DELETED|
tests/__pycache__/test_pr_play_t05_composition.cpython-312-pytest-9.1.1.pyc|21125|24576|6a3a3c4837c1d852664e52301cf42c3345593e19ad1f54365d309e5fd937be2b|PASS|DELETED|
tests/__pycache__/test_pr_play_t06_persistent_manipulation.cpython-312-pytest-9.1.1.pyc|16057|16384|0dde3643b43ff1cbe6a7745811bd96a444ecdd0ff33204f2534d95743c3b7e62|PASS|DELETED|
tests/__pycache__/test_prompt_context.cpython-312-pytest-9.0.3.pyc|368262|368640|d8f916c3e39d83fdbe8dd1aea684f0367df6338a2243a67305fe992700f0d81c|PASS|DELETED|
tests/__pycache__/test_prompt_context.cpython-312-pytest-9.1.1.pyc|368262|368640|393f593c0d59aff5cc0cc56994538452c7d136e20ee0d4863d6307ce54a1671d|PASS|DELETED|
tests/__pycache__/test_prompt_context_ctir_boundary.cpython-312-pytest-9.1.1.pyc|45885|49152|509451a0013fa1664198ea0d8d348c5cffeaa6d8a4a0d9ab8640962811b3d4b6|PASS|DELETED|
tests/__pycache__/test_prompt_context_ctir_consumption.cpython-312-pytest-9.1.1.pyc|41549|45056|f705af445f5277eaffb3b2b5e5af2e19b061048880ad3ed1b8e62bcbebaf8ae3|PASS|DELETED|
tests/__pycache__/test_prompt_context_plan_only_convergence.cpython-312-pytest-9.1.1.pyc|48454|49152|e4d869ca6d89b90d8efc546c310818249a222475ef79378b73be4181ad372f91|PASS|DELETED|
tests/__pycache__/test_prompt_context_public_prompt_boundary.cpython-312-pytest-9.1.1.pyc|11054|12288|c84371293a3448106d5540c8eb7460c75564434fad9b5d1338a8711986a15efb|PASS|DELETED|
tests/__pycache__/test_prompt_context_transition_node_consumption.cpython-312-pytest-9.0.3.pyc|28113|28672|23ec02b77017d1a210248fb38682d295e4457d7d2e16b6c372c6d8d99d1cd0fb|PASS|DELETED|
tests/__pycache__/test_prompt_context_transition_node_consumption.cpython-312-pytest-9.1.1.pyc|28113|28672|23ec02b77017d1a210248fb38682d295e4457d7d2e16b6c372c6d8d99d1cd0fb|PASS|DELETED|
tests/__pycache__/test_provider_accounting_integrity.cpython-312-pytest-9.0.3.pyc|61633|65536|a6989d96f357a993fbe77e69d3c1d8f1b25dd16dd76a988569ca7e728804fa6f|PASS|DELETED|
tests/__pycache__/test_provider_accounting_integrity.cpython-312-pytest-9.1.1.pyc|61633|65536|a6989d96f357a993fbe77e69d3c1d8f1b25dd16dd76a988569ca7e728804fa6f|PASS|DELETED|
tests/__pycache__/test_referenced_surface_grounding_inspection_resolution.cpython-312-pytest-9.0.3.pyc|78034|81920|3f7f7fd9259b91398a10273d77ae2122a06a2e5a4664aa2ad527e14263aafccc|PASS|DELETED|
tests/__pycache__/test_referenced_surface_grounding_inspection_resolution.cpython-312-pytest-9.1.1.pyc|78034|81920|3f7f7fd9259b91398a10273d77ae2122a06a2e5a4664aa2ad527e14263aafccc|PASS|DELETED|
tests/__pycache__/test_referenced_surface_grounding_inspection_resolution.cpython-312.pyc|24206|24576|3a40dc0515f519bb79683ea59d34ade187c95a648802383cba60acfd301d0cc8|PASS|DELETED|
tests/__pycache__/test_referential_clarity_strict_social_local_repair.cpython-312-pytest-9.1.1.pyc|35775|36864|ab1a3e98f3e0c3edfb15eedc72b09fafd7b2d30a1de9a7a770cc814c59cba902|PASS|DELETED|
tests/__pycache__/test_retry_social_fallback_block3_scope.cpython-312-pytest-9.1.1.pyc|21770|24576|eaf3485112ebfaa4baf52b89b19bee6e53a24860e566054d16400303862caae3|PASS|DELETED|
tests/__pycache__/test_runtime_persistence_regression_suite_obj14.cpython-312-pytest-9.1.1.pyc|60614|61440|36978c2082bf0eb3b36677c0f3061f1c77be8e98b86a4edfbf36c33e1f06a317|PASS|DELETED|
tests/__pycache__/test_save_load.cpython-312-pytest-9.0.3.pyc|18583|20480|796ecb595b2c9d842b6f062fd8349559fb323320cf7e9746e0fb1a4bc4e765c5|PASS|DELETED|
tests/__pycache__/test_save_load.cpython-312-pytest-9.1.1.pyc|18583|20480|796ecb595b2c9d842b6f062fd8349559fb323320cf7e9746e0fb1a4bc4e765c5|PASS|DELETED|
tests/__pycache__/test_scene_destination_binding.cpython-312-pytest-9.1.1.pyc|107524|110592|1b3a6aa17c685004e3cc577c6af8a7d763b8e9a7233c52e5c6ad1bf4f49736c6|PASS|DELETED|
tests/__pycache__/test_skill_checks.cpython-312-pytest-9.0.3.pyc|26754|28672|3a4ac14b75d43b1b77aa22dee480f6125080f2e6a6d3238a7d8a6963b49ddaf3|PASS|DELETED|
tests/__pycache__/test_skill_checks.cpython-312-pytest-9.1.1.pyc|26754|28672|3a4ac14b75d43b1b77aa22dee480f6125080f2e6a6d3238a7d8a6963b49ddaf3|PASS|DELETED|
tests/__pycache__/test_snapshots.cpython-312-pytest-9.0.3.pyc|14200|16384|4c18b387282aeba6aba6c57ba36dfa2880c0b264ab402ee7ad257d47514ff1b6|PASS|DELETED|
tests/__pycache__/test_snapshots.cpython-312-pytest-9.1.1.pyc|14200|16384|4c18b387282aeba6aba6c57ba36dfa2880c0b264ab402ee7ad257d47514ff1b6|PASS|DELETED|
tests/__pycache__/test_social.cpython-312-pytest-9.1.1.pyc|116403|118784|d46dcc685595a5872f15245c5bfa8ef6ca5a764c1e171da6a89b0b63143e6a16|PASS|DELETED|
tests/__pycache__/test_social_answer_candidate.cpython-312-pytest-9.1.1.pyc|21235|24576|a358ded2ade6ef1846ccb5966bfcddfb00e16af3283fd0390c866f4c8b5033ea|PASS|DELETED|
tests/__pycache__/test_social_answer_retry_prioritization.cpython-312-pytest-9.1.1.pyc|12116|12288|e90ad6a821bdc24bf9e40b9a0c5c3f4496dd1b822c3eb4f1afee1c067d37091e|PASS|DELETED|
tests/__pycache__/test_social_contract_turn_trace.cpython-312-pytest-9.1.1.pyc|13424|16384|cc7cd5b26647c2dbc4414c1a887e66993ff80cdbe34884c9ca58ac1ec6b935e7|PASS|DELETED|
tests/__pycache__/test_social_destination_redirect_leads.cpython-312-pytest-9.1.1.pyc|27152|28672|7048a874735b21b93cecc4ebc52237631554dfe2af7be0cfa0e0d941d4be458a|PASS|DELETED|
tests/__pycache__/test_social_emission_quality.cpython-312-pytest-9.1.1.pyc|88323|90112|c4c90970bfd715c3fdf23e7203bdb64595bb26b1b189b159b37eac61be5b0cf4|PASS|DELETED|
tests/__pycache__/test_social_escalation.cpython-312-pytest-9.1.1.pyc|50447|53248|97e3b4fde5f0575c248bc9885faf5c33477babf5808c67f1039b6906b233bfc7|PASS|DELETED|
tests/__pycache__/test_social_exchange_emission.cpython-312-pytest-9.1.1.pyc|253324|253952|c28917e538d09659d7c77f4e64588647869332c5028bd0907f2e4b9746b2634d|PASS|DELETED|
tests/__pycache__/test_social_fallback_leak_containment.cpython-312-pytest-9.1.1.pyc|11779|12288|79f6206c8b3b326fd00d637e750521f58571eb7fdefe68f86099bc5daa453059|PASS|DELETED|
tests/__pycache__/test_social_interaction_authority.cpython-312-pytest-9.1.1.pyc|17345|20480|1f71e14e6f71fd40f417a33dbe156992f1768cbd047a9f1da47915fcacd7cdb9|PASS|DELETED|
tests/__pycache__/test_social_lead_landing.cpython-312-pytest-9.1.1.pyc|156938|159744|e0243f4ed67ff16da31a6363c3611a0b3404464d20d35299d9facf4d820d6459|PASS|DELETED|
tests/__pycache__/test_social_lock_continuity_escape.cpython-312-pytest-9.1.1.pyc|17965|20480|8afe49e44a5fee7e1bc9fafb414d81452d98a4502e29b7e811d6fc677e6085c4|PASS|DELETED|
tests/__pycache__/test_social_probe_determinism.cpython-312-pytest-9.1.1.pyc|27182|28672|6687ffe6f9f748100d6df1b555eec64ce47b88135bdd48995d3cc88cc2a739e3|PASS|DELETED|
tests/__pycache__/test_social_question_relevance_answer_selection.cpython-312-pytest-9.1.1.pyc|100751|102400|949475f655c4004296c7936fee90e8c4fa0f549e423b3a2bbfec798afe27acc5|PASS|DELETED|
tests/__pycache__/test_social_speaker_grounding.cpython-312-pytest-9.1.1.pyc|50465|53248|2bd36cb11f281ce02a5727f9921de042d4425bebb2aa2c7efeca7e4e01c3a0fb|PASS|DELETED|
tests/__pycache__/test_social_target_authority_regressions.cpython-312-pytest-9.1.1.pyc|61238|61440|89f658f8be5cfd1724b802f33c4ac3c631c907bff6620e821ae206bd0c9af6c2|PASS|DELETED|
tests/__pycache__/test_social_topic_anchor.cpython-312-pytest-9.1.1.pyc|18387|20480|8822b76a133062246b1b06f85e2653e6900dbe7f2205ee610d33f0f3bf256c2c|PASS|DELETED|
tests/__pycache__/test_start_campaign_api.cpython-312-pytest-9.0.3.pyc|103121|106496|99dfbb86454a78b50d8ec886bccab6482aaefb407dcba8429df601cbdcf1cc41|PASS|DELETED|
tests/__pycache__/test_start_campaign_api.cpython-312-pytest-9.1.1.pyc|103121|106496|cc5bf4a8372e362098a7c76d8cfaa10a2a60c7ba669def5172505b7229591747|PASS|DELETED|
tests/__pycache__/test_start_campaign_api.cpython-312.pyc|33037|36864|c5b69e7b3cb73e8e1331efeb3a5990a3e99f73d0c5eced27ec705b72b69d6296|PASS|DELETED|
tests/__pycache__/test_state_authority.cpython-312-pytest-9.0.3.pyc|46024|49152|f851a109c3b13e954624ac69a2364c32ae9e8227b3c6c306cf3b19037416bc6f|PASS|DELETED|
tests/__pycache__/test_state_authority.cpython-312-pytest-9.1.1.pyc|46024|49152|f851a109c3b13e954624ac69a2364c32ae9e8227b3c6c306cf3b19037416bc6f|PASS|DELETED|
tests/__pycache__/test_state_channels.cpython-312-pytest-9.1.1.pyc|10290|12288|39946dc5725fecd3e4925e1834222690aa6036836f349e39403280093b0fa603|PASS|DELETED|
tests/__pycache__/test_stay_leave_social_lock_override.cpython-312-pytest-9.1.1.pyc|78384|81920|1770211d95342339a689357aef56d1c6cbbbec33ab4796eef980e4b36f0f8e7f|PASS|DELETED|
tests/__pycache__/test_stay_leave_social_lock_override.cpython-312.pyc|22809|24576|e07700eac8fddc9c5c140b98c97a5bbde4f8be738c8070bd3c41bdd2647edcad|PASS|DELETED|
tests/__pycache__/test_strict_social_answer_pressure_cashout.cpython-312-pytest-9.1.1.pyc|52975|53248|9e37d6dcb189f3fd9f39e729697d0ba84b08a08bdda8d9ad552299cc2ec4f78f|PASS|DELETED|
tests/__pycache__/test_strict_social_emergency_fallback_dialogue.cpython-312-pytest-9.1.1.pyc|29086|32768|c0d0b85a0a68992c54b0f53bef85f38a96a65c3422518a0fa8ab73a12621e075|PASS|DELETED|
tests/__pycache__/test_turn_pipeline_shared.cpython-312-pytest-9.1.1.pyc|389032|389120|b803bb3a1cf5de8543ba02a01ceb109fd9d059af1c02c195ce0a69ab0fc9d603|PASS|DELETED|
tests/__pycache__/test_ui_mode_backend_integration.cpython-312-pytest-9.1.1.pyc|35417|36864|736b07bd12e6bde8c65fab83271df4fb26d91b2379dfc090a605ec57d6a023fa|PASS|DELETED|
tests/__pycache__/test_ui_mode_backend_integration.cpython-312.pyc|10680|12288|d63b2af1fe30c90743ca6e7998273df3214dfe08453ea2ffa89bca739d9b8780|PASS|DELETED|
tests/__pycache__/test_ui_mode_policy.cpython-312-pytest-9.1.1.pyc|12002|12288|28a05558d08ecd2dbaf4889ec487a700c84eec1fa557b8c5949671ad19b5cfcf|PASS|DELETED|
tests/__pycache__/test_ui_mode_regression_matrix_objective15.cpython-312-pytest-9.1.1.pyc|23853|24576|7f69d8c0d9a4c99c7b18d3dbd13eb112129c56848f2ab323c3ece4a8e9497ef7|PASS|DELETED|
tests/__pycache__/test_unparsed_movement_state_narration_integrity.cpython-312-pytest-9.1.1.pyc|60116|61440|6ea1c2f497ed39965d4d3c011742b6ddfd81ecd4124b541b4c31a08135f60c47|PASS|DELETED|
tests/__pycache__/test_unresolved_travel_narration_authority.cpython-312-pytest-9.1.1.pyc|52085|53248|a5c288baea882a7ee06a20a0069666bc3d191bc217d42f4bc57a146b6d259099|PASS|DELETED|
tests/__pycache__/test_world_action_social_continuity_break.cpython-312-pytest-9.1.1.pyc|24179|24576|23e82a10f418a2dc09696d25a913f432a4cf3643554a1c0c1f0444d7908af973|PASS|DELETED|
tests/__pycache__/test_world_updates_and_clue_normalization.cpython-312-pytest-9.1.1.pyc|81880|81920|eb432708442c85844a0cc2eefffd5c8bf2472de9e2bba461c9adc200ff15dc69|PASS|DELETED|
tests/helpers/__pycache__/__init__.cpython-312.pyc|212|216|6aececa1c81ce23de2c649af298d4a90637b226a3a5a561d0f7d70d848a5aa60|PASS|DELETED|
tests/helpers/__pycache__/actor_consistency_smoke.cpython-312.pyc|2000|4096|cb0a2dce3f53a1dfcdabb270849dbdf9a6d1bd40764ae84c37216d9eb0a635de|PASS|DELETED|
tests/helpers/__pycache__/ctir_narration_bundle.cpython-312.pyc|1558|4096|597038ee4e3f91c3ad5adbfbc20c1eeb90886a521f112f76ebfa75e68d394238|PASS|DELETED|
tests/helpers/__pycache__/dialogue_social_plan.cpython-312.pyc|3864|4096|601a3b4b4cd5f9b8858f32db23414c5f530f5354a02bdf39cf1eee7c4834ee4e|PASS|DELETED|
tests/helpers/__pycache__/emission_smoke_assertions.cpython-312.pyc|22600|24576|c6eb84337a620307fd8898a6804f063f6a09517be0bda0c06d668e725faeea95|PASS|DELETED|
tests/helpers/__pycache__/failure_classification_alignment.cpython-312.pyc|21823|24576|f4a00a78dbc708acfc54f35acce74b9f85024c96534bd052af8d51a3257311da|PASS|DELETED|
tests/helpers/__pycache__/failure_classification_builders.cpython-312.pyc|24416|24576|0372845279fee79f19831797c09577d3d5bdcec04fdb2e1e149a2bf0e2bca5c5|PASS|DELETED|
tests/helpers/__pycache__/failure_classification_dashboard_expectations.cpython-312.pyc|47814|49152|f06f71df736f87c20ca96b84840db2b7a7d5380465dc8dc3c93efba130fc1df3|PASS|DELETED|
tests/helpers/__pycache__/failure_classification_split_owner.cpython-312.pyc|39545|40960|d59781f7e875310599af311f26cb690ad380115dc616f50ba632df7b2a9c2d50|PASS|DELETED|
tests/helpers/__pycache__/failure_classification_sync.cpython-312.pyc|1465|4096|0de16e25cda8601bef9746cdbf58b916d9352feead9987ee5cee181169014367|PASS|DELETED|
tests/helpers/__pycache__/failure_classifier.cpython-312.pyc|46807|49152|fea5a61409efe24b7fceae8e60dea6f77baca718df6a4eca482b5fac42697409|PASS|DELETED|
tests/helpers/__pycache__/failure_dashboard_drift.cpython-312.pyc|26105|28672|a334f1abb8604b0b50c1ee847a9e5b519e95a83547ec713c5da77b25ae57d1d4|PASS|DELETED|
tests/helpers/__pycache__/failure_dashboard_orchestration.cpython-312.pyc|4373|8192|a366019d4cfb1e918188810b8c8749d426f390bfea42a6f833fc31a41f6bad87|PASS|DELETED|
tests/helpers/__pycache__/failure_dashboard_paths.cpython-312.pyc|6120|8192|11228d21188873650ce77f6cd41f3e8c18d2aa20958ee063f6f7d17079f7dd18|PASS|DELETED|
tests/helpers/__pycache__/failure_dashboard_recurrence.cpython-312.pyc|104608|106496|5da9842123f4ea1732e26e91e4cd5d4f01345f6f6a6f35eac87a412101f8658e|PASS|DELETED|
tests/helpers/__pycache__/failure_dashboard_report.cpython-312.pyc|54994|57344|2093b93459023dfdf467fd6bd257e8f8d98108251aa8da391bcc058b0595d8e4|PASS|DELETED|
tests/helpers/__pycache__/failure_dashboard_session.cpython-312.pyc|5800|8192|c81ce711eaf9d8833a72d490bfb95ba36f9dad9b36afb9c271efaf264d1afd7c|PASS|DELETED|
tests/helpers/__pycache__/failure_dashboard_stability.cpython-312.pyc|13683|16384|660046a9f2de41fa83ba3dcfd823a1e43522fb13adde1fb93d41c3cd1d1082c2|PASS|DELETED|
tests/helpers/__pycache__/fallback_bridge_smoke.cpython-312.pyc|1605|4096|140c2cdf59277f28d29926bbc31c97fed117d26bb8e6a91b84371e1157e977c1|PASS|DELETED|
tests/helpers/__pycache__/gate_orchestration_smoke.cpython-312.pyc|3031|4096|f1d6ca5d3375810f0ecf91d4ca7835a478a3a2dd81c036c0e258a83209e4c3f7|PASS|DELETED|
tests/helpers/__pycache__/golden_replay.cpython-312.pyc|100293|102400|22f3eb6412b808803988e25bfe9233af2983cddb2cccd096ebf5faa1dab11bdd|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_fixtures.cpython-312.pyc|17866|20480|13730258349af5742e824e4a8490290888d5ed67b13c818ac527ff790af42f8b|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_projection.cpython-312.pyc|17635|20480|b24a531c07f1ccf6150a17a2e337663dcbd2bcc547de382bc92ad653ec686a65|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_projection_engine.cpython-312.pyc|7233|8192|db5972c18ea25a5d7b8d9b5014ea14cda1fb3b475a3e503d63037b9298ffe512|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_projection_extractors.cpython-312.pyc|12644|16384|7bb2503cd935fd0d1eeb31bdfb79e2b2c487a643a6801f570d688d6a2708bebc|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_projection_fallbacks.cpython-312.pyc|4754|8192|c8d6d4e742fddc0aee7adc5de36b1b6b15996569c5ea5aeef93441abd64df3f0|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_projection_fields.cpython-312.pyc|9794|12288|aadc2d0bc9cefc9f6d1f4b6e009ca593c03f487d6787bafbf0fec1726a1c2b7a|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_projection_manifest.cpython-312.pyc|7411|8192|48a046d27f21c286ac38e960ebc869c6753fef4270f680fb004ca2bc2783b1d4|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_projection_presence.cpython-312.pyc|10733|12288|196807c4da3e3594f55548bff9f762cb48f417399e9633e9efd4ad1f5861bccb|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_projection_registry.cpython-312.pyc|18052|20480|0c2170f4ed420c1a8a74021e47516e0b982438820bc49d16cc8642a4f65f9955|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_projection_semantic.cpython-312.pyc|1412|4096|ab1fb525eb990a29235495fb04b92a634283bd17dfce6e13e96ec65c68094733|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_projection_speaker.cpython-312.pyc|5748|8192|069f76993da7dd28671cc32107e16ce78b2486da62dea5253bed5ac3bf22eaae|PASS|DELETED|
tests/helpers/__pycache__/golden_replay_trend.cpython-312.pyc|59894|61440|c1d05d054ef4e14e2289315b87e2b18232455c6bb20cd14d7ece9891f4ac7143|PASS|DELETED|
tests/helpers/__pycache__/live_model_guard.cpython-312.pyc|4825|8192|0dbb428a6e5b9d62082aa6ea1f18a8fe815d0de9856e319de9f480bf862b3b0f|PASS|DELETED|
tests/helpers/__pycache__/objective7_referent_fixtures.cpython-312.pyc|2623|4096|6933d05f8af4577640b7a1db7ee7ab685ddf51855591a69d285d3066ca65ae44|PASS|DELETED|
tests/helpers/__pycache__/opening_fallback_evidence.cpython-312.pyc|28249|28672|dbc2c3045125f8f8ab299da89d7f4c27416cd4f3a8ab5550e73c33ffecacecef|PASS|DELETED|
tests/helpers/__pycache__/opening_fallback_gate_harness.cpython-312.pyc|3215|4096|bdf4f3fc26b4cab4eec3b921bd3f7ddf53762e10206eaa342272b976364a84f5|PASS|DELETED|
tests/helpers/__pycache__/post_speaker_finalize_probe.cpython-312.pyc|16895|20480|7bcf902509521f4a7640a375e6d76f7722b2cb34f689846a0925a140d4e2fe13|PASS|DELETED|
tests/helpers/__pycache__/protected_replay_registry.cpython-312.pyc|12274|12288|33c217f4c4955f7d738a78a8c2de82cf2af504f3625f72b378878c3258d55336|PASS|DELETED|
tests/helpers/__pycache__/protected_semantic_mutation_measurement.cpython-312.pyc|38212|40960|c882eab9cbc1800d846ff47172c94741e32acdfa43178ff2ec46eafc410faf29|PASS|DELETED|
tests/helpers/__pycache__/repairs_consumer_facade.cpython-312.pyc|2158|4096|8da26f4a7ba53bce7b6d76a51f341d52a87a0f056eeec8897f20ee9cd06dc278|PASS|DELETED|
tests/helpers/__pycache__/replay_bug_recurrence.cpython-312.pyc|18056|20480|be6e46809d37bceb3c880af2028a9cf88983cb2a034300908ba80b00615ee53e|PASS|DELETED|
tests/helpers/__pycache__/replay_bug_recurrence_events.cpython-312.pyc|52141|53248|0f9fc7a1b870e3612651ee40e55f8c240cd679e1e3c8e18ed698083a0c99ebca|PASS|DELETED|
tests/helpers/__pycache__/replay_bug_recurrence_history.cpython-312.pyc|128015|131072|f0524a1db190a306f571499ae38067abadecb4c8794d05016dbf119e924bed97|PASS|DELETED|
tests/helpers/__pycache__/replay_bug_recurrence_serialization.cpython-312.pyc|97731|98304|8289ee30edde5429d640546ffbe240c00504c1269767cd0dcf5cac983dbc176b|PASS|DELETED|
tests/helpers/__pycache__/replay_bug_recurrence_statistics.cpython-312.pyc|192609|196608|68907693a819d3a8c7a9cc5d083b1663e6ec0c691960ffb5d8e58496b15c798c|PASS|DELETED|
tests/helpers/__pycache__/replay_drift_hotspots.cpython-312.pyc|9955|12288|4a1b07be2d4214249107c6531ffaeff739425bf2993b1743b8fd145f7f3eedb6|PASS|DELETED|
tests/helpers/__pycache__/replay_drift_longitudinal.cpython-312.pyc|8198|12288|0526f9a17b69f7de9b9de1c293723091281af93e08e77999fa9859c54cbcb65b|PASS|DELETED|
tests/helpers/__pycache__/replay_drift_reports.cpython-312.pyc|2149|4096|93800729415ef062a1eef98e359ba9ba7b0366458ba20a56d8c0c4a005115ec3|PASS|DELETED|
tests/helpers/__pycache__/replay_drift_risk.cpython-312.pyc|29289|32768|95b7ced0e2dd03be0bb360d2c98f3044d2e603e4a4d782f75a9afaf54863c97e|PASS|DELETED|
tests/helpers/__pycache__/replay_drift_rows.cpython-312.pyc|3548|4096|bbf3cdb023839e260f9640e33e52d4b9ef4b7394d9793dfb98dd9aaae8ddbd1a|PASS|DELETED|
tests/helpers/__pycache__/replay_drift_taxonomy.cpython-312.pyc|49434|53248|394390823ad7c7d13dad05f8272440dacd15eaffca0bcc9d5000449daf0b6f96|PASS|DELETED|
tests/helpers/__pycache__/replay_drift_trends.cpython-312.pyc|10549|12288|ab8c3cb4eb7fef5649983e9868059ee0c665373bf17649827d86c1fe807c981b|PASS|DELETED|
tests/helpers/__pycache__/replay_fem_read_smoke.cpython-312.pyc|1909|4096|a2a0d551b9188556e0f3c3dbc718aebfccd17d6c9ad91e10446b1d42623860be|PASS|DELETED|
tests/helpers/__pycache__/replay_observed_row_fixtures.cpython-312.pyc|6362|8192|2868ebe0641960fc682b01771a5a2975cac6f1e4733d3219d207726a1f3a5811|PASS|DELETED|
tests/helpers/__pycache__/response_type_smoke.cpython-312.pyc|3228|4096|3828feaa4c394aab92d0900ba3482ee060873739f31097c3316cfd24d6d53252|PASS|DELETED|
tests/helpers/__pycache__/route_determinism_smoke.cpython-312.pyc|3514|4096|61e2477878990f6269274fbae38323f4a9462eabb0dcd664cb3eb6574e3b0142|PASS|DELETED|
tests/helpers/__pycache__/runtime_lineage_reporting.cpython-312.pyc|7715|8192|2f5353da41dad964a9edcf107ae2a07bc02fa355c86f56d9974a1c7024bf1e0f|PASS|DELETED|
tests/helpers/__pycache__/semantic_mutation_attribution.cpython-312.pyc|42041|45056|d76e32eb3b348d49a4108252da4b82f978c337d7804802c563b2baf3434a4bd3|PASS|DELETED|
tests/helpers/__pycache__/social_escalation_fixtures.cpython-312.pyc|1362|4096|f7fe0d310fd7735f1703d5035d7fc2abfb437a5dcffa1598ba11b0e7c9dd7026|PASS|DELETED|
tests/helpers/__pycache__/storage_isolation.cpython-312.pyc|5604|8192|33caa45b71b4a1e55262e9880394ead78930e0bab27e7220895148bb000104a7|PASS|DELETED|
tests/helpers/__pycache__/strict_social_harness.cpython-312.pyc|4945|8192|d7f6fd4c479a888ce522f51da0467edddf32585a6ee6af9ff0de958fe1001498|PASS|DELETED|
tests/helpers/__pycache__/transcript_runner.cpython-312.pyc|6171|8192|b7a478b6b5618f59202751913fa6964e195fc46ac2b86f0ee1ed280145c504b1|PASS|DELETED|
tests/helpers/__pycache__/transcript_snapshots.cpython-312.pyc|12396|16384|22876e0218eb5d013685888347d6687eeb83b6d108cdd7de964a526c67751e9a|PASS|DELETED|
tests/helpers/__pycache__/turn_pipeline_http_fixtures.cpython-312.pyc|7389|8192|2c2d54e356436b35904b751da668f9017df8ea286d88b038c64a9ea8098a0f68|PASS|DELETED|
tools/atgb/__pycache__/__init__.cpython-312.pyc|1081|4096|6effe92101a182203642d143e2238c429a3907fee91d8f78fe4e84551284cf9c|PASS|DELETED|
tools/atgb/__pycache__/accounting.cpython-312.pyc|13975|16384|bc2ca845c2eeaeac443303a1306552c6b8ceeabb71531e36967939f21b50a066|PASS|DELETED|
tools/atgb/__pycache__/baseline.cpython-312.pyc|3262|4096|2df505e19823ad649a7bd4bac19868b648a2ae39f0fc8a391b57e7a8ad1e06cf|PASS|DELETED|
tools/atgb/__pycache__/budget.cpython-312.pyc|6465|8192|e80707ff095120fb9234450c24bc37d087899e669ed21eda4124fe7af28f4924|PASS|DELETED|
tools/atgb/__pycache__/chat_worker.cpython-312.pyc|22366|24576|1873515646b9aa6f8fdc6c03d1a9737f6ae1512a5e090b8a02482c44cca65173|PASS|DELETED|
tools/atgb/__pycache__/driver.cpython-312.pyc|31907|32768|6c80b41abf758c3314b13ccf8eca1dbe2df5c6f19d9493674edffa20c1674092|PASS|DELETED|
tools/atgb/__pycache__/fixtures.cpython-312.pyc|14192|16384|a9c03008e90d35b018473c4b55937ec271656ffc8d9c724d71b8a00d91a9f946|PASS|DELETED|
tools/atgb/__pycache__/isolation.cpython-312.pyc|9255|12288|9ff1b3f97a06d8e82f4988b043a77a3f5dfdced4370de44b030eee9110de4112|PASS|DELETED|
tools/atgb/__pycache__/preflight.cpython-312.pyc|6564|8192|3d419578e775a8da166f850766cdeb8c0a6e1671af4f8cc70d349ac5a2547e30|PASS|DELETED|
tools/atgb/__pycache__/readiness.cpython-312.pyc|12662|16384|21a77d76b8fb97a73370f092c7b57b32aa9a19d39d8ccbd41ee125906ecc4888|PASS|DELETED|
tools/atgb/__pycache__/results.cpython-312.pyc|21396|24576|3e00705b318918f1ef2b93132f06646afbcbd7fe4632fb6192a4d825510e720d|PASS|DELETED|
tools/atgb/__pycache__/worksheet.cpython-312.pyc|9834|12288|21cfecde4f339e2d2f34c80dcc098c285609b7ed223c50e99ee98f09571d1524|PASS|DELETED|
```
