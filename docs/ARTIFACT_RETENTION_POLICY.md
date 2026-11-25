# Artifact retention policy

## Temporary execution workspaces

Identify the owner, producer, and purpose when allocating a workspace. Keep generated scratch separate from retained evidence. After a successful run, publish and verify required outputs and diagnostics, then remove the disposable workspace when its consumers have finished. Keep scratch needed by an active investigation. Reuse published results instead of accumulating expanded execution copies.

## Failed executions

Keep failure evidence while it serves an active investigation. At closure, preserve significant diagnostics, required regression fixtures, and unique evidence with continuing value. Remove redundant generated workspaces after verifying that the retained evidence supports review and reproduction.

## Historical evidence and reviews

Prefer a concise final report, required regression evidence, compact machine-readable results, and verified archives where appropriate. Preserve confidentiality and appropriate access controls. Exact NTFS security descriptor restoration is optional for ordinary historical execution evidence. Honor specific security or retention requirements where they apply.

Package the smallest set that supports review. Reference authoritative retained paths and hashes for large raw trees, historical inventories, previously published evidence, large ledgers, and unchanged support material where practical. Compress machine-readable evidence when it belongs in the bundle.

## Agent responsibilities

Clean up disposable output you created once publication and validation are complete. Preserve evidence needed for review or regression reproduction. Report unusually large generated storage and avoid redundant copies. Establish ownership from creation records or equivalent positive evidence. Names, wildcards, and age alone cannot establish ownership. For pre-existing output, verify authorization, provenance, exact membership, containment, and protection and dependency exclusions. Preserve tracked files, manually authored material, active state, ambiguous content, and unsupported filesystem objects. This policy establishes manual retention practices.
