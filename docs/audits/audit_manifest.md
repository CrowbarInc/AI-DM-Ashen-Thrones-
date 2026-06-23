# Audit Manifest

This manifest indexes the organized audit documentation and records files that remain at operationally
pinned paths. Status values are `active`, `closed`, `historical`, `generated`, or `needs review`.

| Cycle or topic | File | Type | Path | Status | Notes |
|---|---|---|---|---|---|
| BW | `BW_protected_replay_trend_window_discovery.md` | discovery | `docs/audits/discovery/BW_protected_replay_trend_window_discovery.md` | closed | Trend-window design and corpus discovery |
| BW | `BW_protected_replay_trend_window_closeout.md` | closeout | `docs/audits/closeouts/BW_protected_replay_trend_window_closeout.md` | closed | Operating procedure and closeout |
| BX | `BX_speaker_identity_file_inventory.txt` | discovery evidence | `docs/audits/discovery/BX_speaker_identity_file_inventory.txt` | closed | Speaker-identity file inventory |
| BX | `BX_speaker_identity_end_to_end_parity_discovery.md` | discovery | `docs/audits/discovery/BX_speaker_identity_end_to_end_parity_discovery.md` | closed | Speaker parity discovery |
| BX | `BX_speaker_identity_end_to_end_parity_closeout.md` | closeout | `docs/audits/closeouts/BX_speaker_identity_end_to_end_parity_closeout.md` | closed | Speaker parity closeout |
| BY | `BY_first_semantic_mutation_attribution_discovery.md` | discovery | `docs/audits/discovery/BY_first_semantic_mutation_attribution_discovery.md` | closed | First-mutation attribution discovery |
| BY | `semantic_mutation_attribution_closeout.md` | generated closeout | `artifacts/by4/semantic_mutation_attribution_closeout.md` | generated | Retained at writer-owned artifact path |
| BZ | `BZ_protected_replay_trend_window_2_discovery.md` | discovery | `docs/audits/discovery/BZ_protected_replay_trend_window_2_discovery.md` | closed | Second trend-window discovery |
| BZ1 | `BZ1_protected_replay_trend_window_2_scaffold.md` | scaffold | `docs/audits/scaffolds/BZ1_protected_replay_trend_window_2_scaffold.md` | closed | Executable cycle scaffold |
| BZ2 | `BZ2_recurrence_movement_classification.md` | metric | `docs/audits/metrics/BZ2_recurrence_movement_classification.md` | closed | Recurrence movement classification |
| BZ | `BZ_protected_replay_trend_window_2_closeout.md` | closeout | `docs/audits/closeouts/BZ_protected_replay_trend_window_2_closeout.md` | closed | Second trend-window closeout |
| CA | `CA_corrective_change_locality_cohort_discovery.md` | discovery | `docs/audits/CA_corrective_change_locality_cohort_discovery.md` | needs review | Flat path retained pending generator/reference audit |
| CA | `CA_program_closeout.md` | closeout | `docs/audits/CA_program_closeout.md` | needs review | Flat path retained pending generator/reference audit |
| CA | `ca12_program_closeout_report.md` | generated report | `artifacts/ca12_program_closeout_report.md` | generated | Retained at artifact-writer path |
| CB | `CB_feature_boundary_readiness_discovery.md` | discovery | `docs/audits/CB_feature_boundary_readiness_discovery.md` | needs review | Operational references remain flat |
| CB | `CB_CLOSE_feature_boundary_readiness.md` | closeout | `docs/audits/CB_CLOSE_feature_boundary_readiness.md` | needs review | Operational references remain flat |
| CC | `CC_feature_readiness_closeout_discovery.md` | discovery | `docs/audits/discovery/CC_feature_readiness_closeout_discovery.md` | active | User-authored discovery preserved and relocated |
| BR/BS | `BR1`, `BR2`, `BRL1`, `BS2`-`BS5` documents | metrics/contracts | `docs/audits/metrics/` | historical | High-confidence metric and contract documents |
| H-BF cycles | Reconnaissance and inventory documents | discovery | `docs/audits/discovery/` | historical | Consolidated from `docs/cycles/`, root, reports, and refactor folders |
| H-BF cycles | Closure, closeout, and implementation summaries | closeout | `docs/audits/closeouts/` | historical | Consolidated from `docs/cycles/`, root, reports, and refactor folders |
| BG | `codex_bg_recon_blocks.txt` | instruction block | `docs/audits/scaffolds/codex_bg_recon_blocks.txt` | historical | Root instruction fragment relocated |
| Legacy audit tree | 61 classified files | mixed | `audits/` | needs review | Several paths are test/generator contracts |
| Flat audit tree | 257 classified files | mixed | `docs/audits/` | needs review | Generator-aware migration required |
| Generated evidence | Report and metric artifacts | evidence | `artifacts/` | generated | Retained where current writers emit them |
| Documentation governance | `documentation_governance.md` | policy | `docs/audits/documentation_governance.md` | active | Permanent ownership, location, and path-contract rules |
| Documentation governance | `documentation_governance_closeout.md` | closeout | `docs/audits/documentation_governance_closeout.md` | closed | Final 472-file ownership classification and cleanup judgment |

For the file-by-file inventory, including confidence and rationale, see
`docs/audits/documentation_inventory.csv`.
