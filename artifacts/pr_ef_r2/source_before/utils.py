import math
import re
import secrets
from datetime import datetime, timezone


def utc_iso_now() -> str:
    """Return timezone-aware UTC timestamp in ISO format ending with Z.
    Preserves compatibility with existing persisted timestamp format.
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def roll_die(sides: int) -> int:
    return secrets.randbelow(sides) + 1


def int_mod(score: int) -> int:
    return math.floor((score - 10) / 2)


def slugify(text: str) -> str:
    t = text.strip().lower().replace("'", '')
    t = re.sub(r'[^a-z0-9]+', '_', t)
    return t.strip('_')
