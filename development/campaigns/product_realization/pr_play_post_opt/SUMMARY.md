# PR-PLAY Post-Optimization Gameplay Evaluation

**Evaluation verdict: A/PASS.** The evaluation completed. The play session did not.

Twelve provider-free continuation turns ran on an already-started frontier-gate campaign. Live provider calls: 0. No campaign opening. No production edit. PR-PLAY-80 was not opened. HEAD `d40f1ed198236c604085f1c842ead267a8104ce2`.

The engine can complete a grounded NPC follow-up and one authored scene change. It cannot carry a natural sequence. After the Guard Captain answered the patrol question, the next inspection, reading, improvisation, and recall turns were swallowed by conversational orchestration. Two of those turns repeated the captain's previous sentence. The player never heard the notice.

## Counts

- Turns attempted: 12. All returned HTTP 200.
- Publication events labeled completed runtime responses: 11.
- Session-pointer advances: 7.
- Operational refusals: 1. That refusal added no publication event.
- Published fallback sentences: 3.
- Provider dispatches: 0. `call_gpt` was entered 4 times and returned before dispatch.
- Local processing time: 1,598.794 ms total. This is TestClient time with provider calls disabled.

## Player experience

Two turns were useful: the captain's patrol answer, and the arrival at Old Milestone. The greeting was a real NPC line and a weak answer. The retreat refusal was the correct unsupported-action result. The other turns did not give the player the information or adjudication they asked for.

## Dominant blocker

Conversational orchestration keeps the previous NPC answer in force. `repeat_delivered_statement` reused the captain's line for a notice reading and for a mud-copy improvisation. `destination_not_established` treated a walk to the visible notice board as travel. `ungrounded_provider_target` turned a recall of that notice into an address clarification.

## Recommended next action

Option A. Repair that orchestration boundary so a new notice, inspection, or recall intent is not answered with the previous NPC sentence and a visible interactable is not treated as an unestablished destination. Do not start that repair in this cycle. Do not open PR-PLAY-80. Do not launch live play from this result.

Reports in this directory. Evidence: `artifacts/pr_play_post_opt/`.
