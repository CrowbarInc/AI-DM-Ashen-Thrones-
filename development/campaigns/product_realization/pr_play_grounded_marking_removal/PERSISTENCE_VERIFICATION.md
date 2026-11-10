# Persistence Verification

The lifecycle test saves through the normal character writer. A second process reads that directory and sees the same empty active list and the same revision. The object instance id does not change.

Snapshots:

| Snapshot | Active warning | Examination |
|---|---|---|
| S0 before the copy | absent | no writing is visible |
| S1 after the copy | present | the warning is read back |
| S2 after the wipe | absent | no writing is visible |

Restoring an earlier snapshot does not keep the later sentence. The removal receipt exists in S2 and is not present in S0. The add receipt remains in the timeline that contains the marking. The removal service does not delete that add receipt when it appends the removal receipt.

A retry after a later, different marking has raised the revision does not apply the original removal a second time and does not remove the new marking.
