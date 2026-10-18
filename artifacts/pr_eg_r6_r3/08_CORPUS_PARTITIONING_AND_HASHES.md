# 08 — Corpus Partitioning and Hashes

Development 42, validation 48, holdout 42. Official freeze was written before the 396 scored calls.

- Corpus `e2ea325b34e1ad936dc847452fc3a1634ff55b6d47f09f86d59d17ee23575d30`
- Development `c7576bb67b9d506dfdd2ed372ec19ab6b2c72696138e62a32700cee216058d99`
- Validation `b2b2e60a638a49edfdacb3ea7b00da4918fd54bd8b4611b2223cc75f58626a05`
- Holdout `7abff8f39eac96f518bf647887e518f639d0a97fcca7793e317718e8182fc863`

Holdout ids were not edited after the run. A one-case smoke (`D01`) ran before the freeze to fix witness failures being counted as malformed output. That smoke is not in the 396 and was not used to change labels.
