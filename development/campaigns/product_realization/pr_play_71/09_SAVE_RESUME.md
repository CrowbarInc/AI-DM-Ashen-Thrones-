# SAVE RESUME

Automatic action/chat saves preserve the active runtime. Explicit Save Slots snapshots preserve campaigns across New Campaign, which intentionally replaces active runtime. The supported controls are Create Snapshot and Load; no invented Save button was added. Identity, character, current scene, discoveries/journal, flags, inventory and actions are checked via snapshots and restored state. Both snapshots remain isolated on disk in normal_data/snapshots.

Same-tab refresh was verified for both. The application tab was closed and reopened at localhost; this is a new tab/origin to the same server, not a clean browser profile/session. Save-slot selection A↔B was verified; subsequent supported actions completed. No server restart AFTER branch completion was tested. First cached frontend load restored A's state while B's transcript remained: preserved as cached_frontend_resume_mismatch.*. Reopened frontend correctly calls reloadAll and restores matching transcript.
