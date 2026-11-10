# Frozen holdout

Developer-authored. Not external validation.

- Manifest: `artifacts/pr_play_78a/holdout_manifest.json`
- Hash: `4b34ccc581addaa2c6e05c4bb400d2b922b5b89f5ffeaf83cab0ea14aeb85007`
- Run once after the hash was written. The manifest was not edited afterward.
- Result: 120/120
- Lanes: {'paraphrase': 25, 'unavailable': 15, 'speech': 16, 'progress': 12, 'ambiguity': 1, 'movement': 4, 'scene': 6, 'mixed': 6, 'multi': 11, 'ordering': 3, 'save': 18, 'isolation': 3}
- Nontrivial paraphrase cases: 25
- Save/resume cases: 18
- Failed cases: none

Section 21 asked for at least 30 nontrivial paraphrases, 20 multi-turn cases, 15 mixed-action cases, and 10 scene cases. This frozen set has 25 nontrivial paraphrases, 11 cases tagged multi inside one longer HTTP campaign, 6 mixed cases, and 6 scene cases. Save/resume cases are 18. The shortfall is in how the holdout was composed. It is not a recorded product failure, and the manifest was not rewritten to chase a pass.
