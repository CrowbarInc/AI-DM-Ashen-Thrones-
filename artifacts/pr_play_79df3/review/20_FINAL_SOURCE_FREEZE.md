# Final Source Freeze

HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`. Product bytes were not edited after this fingerprint. The development re-run, historical lanes, HTTP acceptance, browser acceptance, and the scored holdout all read this source.

| File | SHA-256 | Role |
| --- | --- | --- |
| `game/publication_contract.py` | `c3412b7260c278b9005402748c8a4a2c5d920bd2e6532f0917e33e172a486ab9` | Publication implementation. 17,103 bytes. |
| `game/api.py` | `27afbb213fffeb90dd50df7b83ca056c6ed3baf4cc7a40eb2508c1f83f0fd055` | Chat and action classification stamp. 372,691 bytes. |
| `game/live_chat_interpretation.py` | `ceaf8049e17d67a058e5c3424338359d201c163c9f9b5d16e0f41a19cda4b9a0` | `provider_request_sent` on the blocked outcome. 30,691 bytes. |
| `game/player_http_boundary.py` | `03208c26c8c7c3ff27fc885d1802e725611b06492ca5462f9bc8e43ce487c74c` | HTTP adapter. Unchanged. 2,710 bytes. |
| `game/player_http_projection.py` | `1f7b0f3df32a9854d91f462eafab39692f7040dcc2613ab352d0e3af3ffec348` | Unchanged. |
| `game/provider_budget.py` | `5a273cfc427ea17b814beafb051c4348a323c758e378746f933cab60b1d9a37b` | Unchanged. |
| `static/app.js` | `ff2c87b0ddc653e56268cd399f858859cba89dd60010958c9db06d2215044efb` | Unchanged by this cycle. |

Tracked worktree diff of `game/api.py` and `game/live_chat_interpretation.py`: SHA-256 `c5561447e1402950034f322cac3d5ec2b672ec0d3c1bf00f38df1f3365b376f1`, 45,736 bytes. `game/publication_contract.py` is untracked, so its fingerprint is the file hash above. The API diff includes pre-existing dirt plus this cycle’s classification edits.

Browser server identity records the same four runtime hashes and `static/app.js`. Port 8114. Provider mode simulated-admission-only.

No product file changed after this freeze, so the acceptance results belong to one fingerprint.
