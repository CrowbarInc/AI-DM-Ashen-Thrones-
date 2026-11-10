# Visibility Contract

Milestone: `pr_play_object_visibility_authoring`. Date: 2026-11-09.

Authoritative location is inventory row `marking_visibility={version:1,markings:{modification_id:visibility}}`, exactly the predecessor observation schema. Leaf forms are {classification:visible}, {classification:concealed}, or {classification:restricted,scope:<bounded nonblank scope>}. No observable alias or default visible migration. Legacy missing classification remains unknown/undisclosed. Malformed/unsupported metadata containers or selected leaves refuse authoring rather than overwrite opaque data. Unknown row/map fields and other entries survive.

Verified transitions: unclassified -> visible -> concealed -> visible; visible -> restricted -> visible. Ordinary authority may see visible only, explicit concealed authority may see concealed, restricted requires matching scope or trusted wildcard. All observations still need independently established observer/access/scope/current-state authority. Exact same-value replay returns original receipt. New same-value requests commit status=no_change receipt with unchanged revision and no object delta; storing this receipt makes no-change replay durable without pretending a mutation occurred.
