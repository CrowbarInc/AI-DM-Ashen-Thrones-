# Frozen Holdout

This is a developer-authored holdout. It is not external validation.

- File: `artifacts/pr_play_77/frozen_holdout.json`
- Cases: 110
- Hash: `556191b095698ead786b1feb9860ffd86c93f957378418ad7e7d302cae3d5fad`
- Official one-pass result: 106 passed, 4 failed
- Multi-turn cases in the manifest: 70
- Save/resume cases: 20
- The manifest was not edited after the run.

Retained failures:

- H017. "Heave the cup and set the cup aside." The cup was lifted. "Set aside" is not the place pattern, so the second step was not established. The lift remained.
- H068. A guarded door was refused and the independent stand continued. The door was unchanged. The oracle expected a full stop.
- H073. "I sit on the bench and stand up." succeeded with "You sit on the wooden bench. You stand." The oracle fragment looked for the word "standing".
- H089. "I open the locked door and stand up." The door stayed locked and closed. The independent stand produced category A. The oracle expected category D.

No safety defect was identified in those four. They were not repaired against the frozen file.
