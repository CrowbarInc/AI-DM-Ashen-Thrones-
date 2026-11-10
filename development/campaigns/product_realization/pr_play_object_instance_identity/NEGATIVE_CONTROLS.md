# Negative Controls

Milestone: `pr_play_object_instance_identity`. Date: 2026-11-09.

52 behavioral identity cases cover stacked/zero/fractional/boolean/missing quantities, malformed host/row/selection, blank id/name, missing usable, malformed UUID/revision/version/provenance, duplicate identity on selected/other rows, forced UUID collision, cross-campaign metadata, stale row, aliasing, unknown metadata preservation, ruleset extension variants, save faults, snapshot faults, concurrent selection and no implicit read migration. No PF field interpretation. New fixture supplies the existing referenced scene so actual snapshot coherency validation runs. No frozen fixture is edited. identity_traces.json includes duplicate rejection and detached first/repeat records; JUnit records all controls.
