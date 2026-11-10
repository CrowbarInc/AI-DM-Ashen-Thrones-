# FROZEN HOLDOUT

50/50 cases pass; zero failures. Distribution: 15 hidden-field, 10 nested-object, five each discovery/error/frontend/isolation/preservation. Frozen before implementation in frozen_holdout.json with SHA-256 9ceb0d66ba08287ea9339e0e65ce3f97f74d06e1be24ee9d8e4ec95e66d00e4d. Implementation freeze was recorded before the single holdout execution; source/frozen development-test hashes remain unchanged. Regression-test migrations occurred later without changing frozen production code.

Every case uses actual TCP /api responses and inspects complete serialized output; preservation cases compare authoritative state independently. Nested cases place an innocuously keyed object under the named field to challenge scalar/object confusion. Results are developer-authored evaluation, not independent external or blind validation. No tuning against holdout failures occurred; none failed. Raw result records remain unchanged.
