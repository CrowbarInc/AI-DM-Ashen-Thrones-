# State and quarantine

New coverage code accepts text and an existing detached request and has no campaign persistence/provider import. Input-deepcopy tests verify no hook mutation. Existing integrated HTTP tests compare accepted/rejected candidate paths with deterministic baseline player text and full state snapshots and guard storage writers. They cover fallback and no publication even for an accepted candidate. Exceptions and malformed provider responses retain deterministic completed action behavior.

No candidate authorizes discoveries, inventory, conditions, NPC state, quests or mechanics. No default gate/mode/prompt/provider-budget change. Protected data/static/experiments and existing game files are hashed against entry; only the two intentional existing validation files may change. integrity.json contains actual path-level results. These checks do not prove complete semantic safety; H41 remains quarantined because the API never promotes integrated prose.
