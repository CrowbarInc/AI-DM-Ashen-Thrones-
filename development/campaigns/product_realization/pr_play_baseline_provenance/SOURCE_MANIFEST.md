# Source manifest

Milestone `pr_play_baseline_provenance`. Branch `feature/product-realization`. HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`. Capture time `2026-11-09T01:15:10.953631+00:00`. Dirty working tree preserved, not reset to HEAD.

Complete machine manifest: `artifacts/pr_play_baseline_provenance/source_manifest.json`, 1294 file hashes; aggregate sorted-path/hash identity `02fb4ccf8ae2d016aef1ba6b2d140279c04285e734cedf56764f8f3a1c8cf151`. Complete modified-tracked/untracked path status: `entry_git_status.txt`; post-cycle status in `final_git_status.txt`. Relevant untracked game/tests/config files are included in the hash map; the status file disambiguates them from tracked modifications. The existing configuration/dependency files are hashed, local installed versions recorded in `dependency_versions.json`.

| Relevant file | SHA-256 |
|---|---|
| `game/api.py` | `c74933294c97d44e840531a12b96a524d727c7c556d3a94c04b033cfada684c7` |
| `game/gm.py` | `f16073aff66ab861847f44d7573356e9244c4ec8de298dabbe70c166bf4b5f3b` |
| `game/conversational_orchestration.py` | `f991c3ac8386cd5704736245cae3e5c5745e062790b1fdeb166e932bfe28d8f5` |
| `game/conversational_continuity.py` | `b68d6aa6acea6dde06c53c15d9b09e606f6309e786cf7f0c9d48c0871d94855a` |
| `game/intent_parser.py` | `9aee3169211959a8d94bdced0ce51d17c1b50484e5a99f3f12731c8ba6f64751` |
| `game/referenced_surface.py` | `aae11daa7c13ed7a77fb79546bfed778ffcc03017e112528f64860ff4c5affc7` |
| `game/exploration.py` | `fff411f08e5767dc0f3f892e2af63cec97e6c928d7989a9feb1c0e7df9c26522` |
| `game/perception_grounding.py` | `de12afb50862029542db682f6b8cacf52064a6521c4ed665955792e6af08246a` |
| `game/immutable_valid_response.py` | `1ffd6158184c621a79c0358e7a0ac6db49fc32580fcfbbd2dad07bb2df165afe` |
| `game/player_http_projection.py` | `1f7b0f3df32a9854d91f462eafab39692f7040dcc2613ab352d0e3af3ffec348` |
| `game/narrative_planning.py` | `e8fcc1c085e6283d50a052dcfeae5b9d797201d01e719ddec5339fc6655481cb` |
| `game/state_authority.py` | `d8fea5b33f914d3a51e59598edd2143584bf9af083b32db6c42a33697d846533` |
| `tests/test_pr_play_post_npc_handoff.py` | `b86f17f469595119cc2085a908dc5d84b6d650bdd0c3a926c55281c6b3c16a98` |
| `tests/test_referenced_surface_grounding_inspection_resolution.py` | `eadc2c24f678f9ba08d2e89209e7dfebd8205f202aabb1ec6808ea471ca7cea3` |
| `tests/test_pr_br_continuation18_immutable_boundary.py` | `c4681f3bc5c8d9dcf68110a8222523c62351c647972d290e6eadbaaaf8727f86` |
| `tests/test_perception_narration_authority_audible_non_invention.py` | `f37e54f81f5450e6bc9f4624393673a04224c9aa60a1c6c02bcaf6808020d506` |
| `requirements.txt` | `7df630b523cb940fa6b71336cae45514263e5dcdd02ef351cbb35bf3da9d63ca` |
| `pytest.ini` | `5b3ea4fa4e6db7f778b7b14fa6a21c5461cf66fb95e91dfb915974afcf35a618` |

Executable source/test snapshot: `artifacts/pr_play_baseline_provenance/current_source_snapshot.zip`, 1143 members verified against the manifest, SHA-256 `77b551a3ab7b9f2e22a5e243d15e53814b51563e21f541216429cf7609be73e5`. This external evidence snapshot is intentionally not recursively nested in the standard review ZIP; selected canonical modules and complete source manifest are packaged. Retain the snapshot alongside the evidence. Runtime data is hash-only; tests seed their own synthetic states. No environment/credential files, virtualenv or Git database were copied. This is a current comparison baseline, not an authenticated historical state or full campaign backup.

Both test runs hash-check 1,292 game/test/data/static/prompt files unchanged; final seal also rechecks all 1294 manifest paths including configuration. Existing historical archives remain at entry SHA-256. Only new cycle evidence/reports and authorized handoff surfaces change.
