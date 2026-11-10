# Source fingerprint

Captured `2026-11-08T13:11:12.594178+00:00`, before the PR-PLAY-79D-F harness and before browser acceptance.

- HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`
- Working-tree diff SHA-256 `4ace6367c229e5be92bc4b691436e032e5ceb0d005742dd7e910a30878f08ce2`
- `application_source_frozen`: true

Relevant application hashes used by the browser host:

| Path | SHA-256 |
| --- | --- |
| `game/api.py` | `c94292c3dffc8bcd3b745907c2fb31c6f864cc83f0602e49aae646f7a9a5052d` |
| `game/bounded_improvisation.py` | `eacdd501d360022cb65bb768e3a39719f398325d8012a4d5c7f7b0283d3c2427` |
| `game/publication_contract.py` | `bbd37983dfb6220184a6fdc4568973993963fc8dacdaee7ca4be0b2b8adac5c4` |
| `game/integrated_play.py` | `bf4a7e68e8cdfd52cbf29a14495c64b80e8ae8f801610be8bfec9e12d24e8ecc` |
| `game/physical_adjudication.py` | `2ce1d80efa4bb1c0b686637fe6ce625e79f0eb8323c1bd18a0e1ac9ad5ab08ee` |
| `game/exploration.py` | `fff411f08e5767dc0f3f892e2af63cec97e6c928d7989a9feb1c0e7df9c26522` |
| `game/player_http_boundary.py` | `03208c26c8c7c3ff27fc885d1802e725611b06492ca5462f9bc8e43ce487c74c` |
| `static/app.js` | `ff2c87b0ddc653e56268cd399f858859cba89dd60010958c9db06d2215044efb` |
| `static/index.html` | `508f46b102409f1fd91a39bc750fb5f250af993fd49eed7b8e277a12a8031414` |

Server identity: Python 3.14.3, pid 23332, `127.0.0.1:8111`, model `gpt-4.1-mini`, retries disabled, limits 5 requests / 4,000 input / 1,000 output / 5,000 total. The key was present and is not recorded. The host source hashes match this fingerprint. Browser evidence and the development run both use this revision. The supplemental holdout fixture hash is `212e0e39d9a6c0bb55d4d6f03b0b7c151b3a91c390184d46bd87bcc95e3bc5fa`.
