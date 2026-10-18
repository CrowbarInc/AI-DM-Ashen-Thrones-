# PR-DI Scoring Rubric

Scores: PASS, PARTIAL, FAIL, UNSUPPORTED, NOT OBSERVABLE.

- PASS: evidence shows the candidate handled the category correctly for this scenario.
- PARTIAL: evidence shows a useful but incomplete or misrepresented handling.
- FAIL: evidence shows the candidate missed, distorted, or counterproductively handled the category.
- UNSUPPORTED: the category is not applicable to the scenario, or the requested mechanic is outside the engine's supported operation set. Unsupported is not automatically a failure.
- NOT OBSERVABLE: the artifact does not contain enough evidence to score the category.

Categories:

1. Intent understanding: recognizes what the player is trying to do or ask, independent of whether it can be executed.
2. Entity identification: resolves or honestly leaves unresolved the relevant NPCs, objects, places, or enemies.
3. Compound-action decomposition: separates multiple player intents into ordered supported/unsupported pieces when the utterance contains more than one action.
4. Ambiguity recognition: detects referential or procedural ambiguity and asks for clarification rather than guessing.
5. Action representation: emits a shape the validator/tool interface can understand without smuggling unauthorized state changes.
6. Execution eligibility: reaches a supported resolver/tool execution when one is warranted, or stops before execution when execution would be unsafe or impossible.
7. Authority integrity: avoids creating world canon, hidden facts, direct state mutation, or validation bypass. Engine-enforced rejection is noted separately from model self-restraint.
8. Unsupported-mechanic recognition: identifies unsupported rules/mechanics without treating recognition failure as interpretation failure when the intent was clear.
9. Gameplay usefulness: produces a player-useful outcome: action execution, safe clarification, or meaningful unsupported/refusal response.
10. Failure recovery requirements: LOW means the next system step is simple; MEDIUM needs routing/schema/tool correction; HIGH needs architectural or substantial harness work.

Important scoring constraints:

- Schema validity alone is not success.
- Rejection alone is not failure.
- A safe refusal or clarification can be gameplay-useful.
- Unsupported mechanics are separated from intent recognition.
- Candidate C's permitted tool call is scored separately from whether the tool call was useful or whether it completed execution.
