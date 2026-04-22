## Runtime persistence envelope (Objective #14)

### What it is
Runtime documents (`session.json`, `combat.json`) are now persisted as a **versioned envelope** rather than a raw payload object. The envelope is the canonical on-disk shape:

- **persistence_version**: integer format version (currently `1`)
- **kind**: document kind (e.g. `session`, `combat`)
- **saved_at**: ISO timestamp for the save operation
- **payload**: the runtime payload (the same dict shape game logic operates on)
- **integrity** (optional): deterministic metadata (currently a SHA-256 hash of canonicalized `payload`)

Game code continues to *operate on the payload dict*; the envelope is unwrapped/validated by the storage layer.

### Why runtime docs differ from bootstrap JSON
Authored/bootstrap files are “content sources” and are expected to remain plain JSON:

- `campaign.json`, `world.json`, `character.json`, `data/scenes/*.json`, `conditions.json`

Runtime docs represent mutable playthrough state and must be safe to load across engine changes. The envelope provides:

- **versioning** for future migrations
- **document kind** checking to prevent cross-file mixups
- **deterministic validation** (including optional integrity checks)
- a foundation for future **transactional restore** (validate before applying)

### Backward-compatibility expectations
- **Legacy runtime payloads without an envelope** may be accepted deterministically (as “missing envelope”) and treated as **normalizable forward**.
- **Unsupported versions**, **malformed envelopes/payloads**, **wrong kinds**, or **integrity mismatches** fail safely with deterministic categories.
- Fresh-session bootstrap behavior is preserved: missing runtime docs are created from defaults, and storage returns a valid payload dict.

### Post-Objective #14 guarantees (safe to rely on)

#### What is runtime persistence vs authored/bootstrap input?
- **Runtime persistence docs (mutable playthrough state)**:
  - `data/session.json`
  - `data/combat.json`
  - `data/session_log.jsonl` (append-only log; cleared atomically when requested)
  - `data/snapshots/*.json` (save slots; a bundle of runtime state)
- **Authored/bootstrap inputs (content sources, plain JSON)**:
  - `data/campaign.json`, `data/world.json`, `data/character.json`, `data/conditions.json`
  - `data/scenes/*.json`

#### On-disk shape: runtime docs are envelopes
- `session.json` and `combat.json` are stored on disk as **versioned envelopes** with a `payload` field.
- Game logic operates on the unwrapped `payload` dict; the storage layer is responsible for wrapping/unwrapping.

#### Deterministic acceptance/rejection rules
- **Legacy missing-envelope dicts** may be accepted (when explicitly allowed) and treated as “normalizable forward”.
- **Safe failures (intentional)**: unsupported versions, malformed envelopes/payloads, wrong document kind, or integrity mismatches are rejected deterministically.
- **Load-time safe fallback**: if a runtime file is present but unsafe/malformed, storage returns deterministic defaults rather than propagating undefined state.

#### Integrity mismatch behavior
- If an envelope includes `integrity`, the stored payload hash must match; mismatches fail safely with an explicit category.

#### Atomic save paths
- Runtime saves (`session.json`, `combat.json`, `session_log.jsonl`) use atomic replace semantics (temp write + `os.replace`) so a crash/failure during save does not leave a partially written live file.

#### Restore semantics: validate-first, commit-second, all-or-nothing
- Snapshot restore validates the snapshot bundle *before* mutating any live runtime files.
- Restore is **all-or-nothing** from the caller’s perspective: mid-commit failure triggers best-effort rollback to the prior live state.

#### Restore success includes coherency enforcement
- Restore only reports success after a deterministic **structural coherency check** passes (e.g., active scene ids must exist).
- If coherency fails, restore rolls back and raises a safe failure.

#### Explicit guard against overlapping runtime persistence operations
- Overlapping runtime persistence operations within the same process are explicitly serialized/guarded to avoid mixed visible runtime state windows.


