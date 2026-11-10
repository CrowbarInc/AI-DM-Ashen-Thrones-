# Controlled HTTP Lifecycle

`test_http_lifecycle_persists_reloads_and_restores` drives `POST /api/chat` on the established coat, sleeve, and mud fixture. The mud record is given an explicit wipe method for cloth. No campaign file is edited.

Sequence:

1. Snapshot S0. No active marking.
2. "I copy the warning onto my sleeve using the available mud." The warning commits and the sentence says it is on the sleeve.
3. "I examine the writing on my sleeve." The sentence is `On the sleeve, the visible writing reads: Warning: keep to the north wall.`
4. Snapshot S1.
5. "I wipe the warning off my sleeve." The sleeve revision increases by one. The active list is empty. An add receipt and a removal receipt are both present. The ruleset extension is still `pf1e`.
6. The next examination says `You look at the sleeve. No writing is visible there.` The warning text is absent. Snapshot S2.
7. A new process loads the same data directory, examines the sleeve, and repeats the wipe request id. The examination matches. The retry does not change the revision or restore the marking. Provider records in that process: 0.
8. Restoring S1 makes the examination show the warning again. Restoring S0 shows no writing and does not reveal the later warning. Restoring S2 again shows no writing.

The published removal sentence names the sleeve and the warning, and does not contain `request_id` or `modification_id`.
