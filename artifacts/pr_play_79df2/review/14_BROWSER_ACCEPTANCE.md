# Browser acceptance

Host: `http://127.0.0.1:8112/`, player mode, typed chat only. Suggested actions were not used. No new campaign opening.

Final source fingerprint: `game/publication_contract.py` `36f8416c168ea456412fd4e2fec8aefc1898f552a223e16f338fb31774ed54ba`, server pid 33276.

Confirmed existing state: Cinderwatch Gate District, scene `frontier_gate`, Gate Guard present, 2 clues.

Final-source turn:

- Input `Hello, Gate Guard.`
- One expression, accepted.
- Visible sentence matches the publication event and the session pointer.
- Snapshot `2026-11-08T16-20-50_7bf157dc`.
- Reload: 23 log entries, 2 clues, the accepted sentence still present.

Superseded fingerprint `37b24c8ce4568d62e36dfdb4528dfffad9938cd7efec03408bdb4332a35e3c98` also showed a live rejected question and a live accepted greeting, with the pointer matching each delivered sentence. That revision failed historical regression (17 new identities) because it stored `campaign_id`. It is not combined into this pass.

Screenshots:

- `screenshots/79df2_final_hello_visible.png` — accepted sentence on the final source.
- `screenshots/79df2_final_accepted.png` — the log position before scrolling to that sentence; it shows the two admission refusals above it.
- `screenshots/79df2_accepted_dialogue.png` and `79df2_snapshot_restored.png` — superseded revision.
