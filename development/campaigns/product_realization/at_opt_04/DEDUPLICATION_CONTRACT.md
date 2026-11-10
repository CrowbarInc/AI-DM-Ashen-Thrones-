# Deduplication Contract

Owner: `omit_duplicate_turn_packet_policy` in `game/gm.py`. One implementation. Called only from `build_messages`, after exact contract mirroring and before `project_narration_payload`.

The root `response_policy` is not modified. Gate and retry packets are not passed through this function.

## Equality

A nested key is a duplicate only when `_json_value_equal` is true: `json.dumps(..., ensure_ascii=False, sort_keys=True)` matches for the complete value. A `TypeError` or `ValueError` means not equal, so the key stays.

That comparison does not use Python's `==`. `True` and `1` are not duplicates. `False` and `0` are not duplicates. `None` equals `None` and is a duplicate when both sides have the key. A nested `None` whose key is absent from the root stays.

Lists and dicts are compared as whole values. Key order inside a dict does not matter because the dump sorts keys. One different child keeps the entire nested value. Children of an unequal object are not removed.

No other normalization was added.

## Cases

| Case | Result |
| --- | --- |
| Every nested key duplicates the root | Nested `response_policy` is omitted. Other packet fields stay. |
| Every nested key differs | Nested policy stays, and the original payload object is returned. |
| Mixed keys | Only the duplicate keys are removed. Remaining keys keep their order and values. |
| Key absent from the root | Kept. |
| Root policy is `{}` | Nested keys are absent from the root, so they stay. |
| Nested policy is `{}` | Left in place. An empty mapping is not treated as a full duplicate. |
| Root or packet is missing or not a dict | Payload returned unchanged. |
| Nested policy is not a dict | Left in place. |
| Non-JSON value | Left in place, because equality cannot be established. |

`turn_packet.contracts` still drops a contract key only when that whole value JSON-equals the root policy. That path was not given a second implementation.

## Immutability and idempotence

The input dict, the nested policy dict, and nested values are not mutated. A change copies the payload and the packet. Kept values are the original objects, not rewritten children.

If nothing is removed, the same payload object is returned. Applying the helper to its own output does not remove more keys. A second serialized dump matches the first.
