# Remaining risks

No readiness blocker remains.

Informational:

- Windows attaches `conhost.exe` as a child of the worker. Owned-process termination reaped it. A diagnostic that requires zero children will fail again for that reason.
- The controller's own scenario verdict stays `INCONCLUSIVE` when readiness stops the run before actions, and `BLOCKED` when startup really fails. `INCONCLUSIVE` here means the action loop was not entered.
- Shutdown is terminate on the owned process handle, exit code 1. That is the existing harness action.
- The occupied-port worker exits before a live image query. The launch command still names the base interpreter.
- This pass does not measure live narrative quality or multi-turn state coherence. Those belong to a separate live experiment.
