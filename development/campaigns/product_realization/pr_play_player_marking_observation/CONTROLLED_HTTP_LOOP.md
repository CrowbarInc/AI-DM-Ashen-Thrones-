# Controlled HTTP Loop

Command: `tests/test_player_marking_observation.py::test_http_observation_survives_reload_removal_and_snapshots` through `POST /api/chat?ui_mode=player`.

Fixture: the predecessor coat with an accessible sleeve, carried mud, and the disclosed warning. Ruleset extension `pf1e` is stored and unused.

Sequence and published text:

1. `I copy the warning onto my sleeve using the available mud.` commits one visible marking. The sentence contains `The marking is on it now.` and the warning. `publication_matches_commit` is true.
2. `I examine the writing on my sleeve.` publishes `On the sleeve, the visible writing reads: Warning: keep to the north wall.` Character bytes are unchanged.
3. A new process, with `ASHEN_DATA_DIR` pointed at the saved files, posts the same examination. It returns the same sentence. Provider records in that process: 0. Character hash is unchanged.
4. Trusted `remove_inventory_object_marking` removes that modification id. There is no natural-language removal in this cycle.
5. The same examination publishes `You look at the sleeve. No writing is visible there.` The warning is absent.

Snapshots restored in the same test:

- S1 after marking: `What does my coat say?` includes the warning.
- S0 before marking: the sleeve shows no visible writing.
- S2 after removal: `Is the warning still written on my sleeve?` shows no visible writing.

No request id, receipt, or concealed string is in those player sentences. The parent process provider record count is unchanged.
