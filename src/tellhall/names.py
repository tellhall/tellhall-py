"""Hall-name normalization and hall IDs, matching the server exactly.

A hall's ID is the SHA-256 of its normalized name. The hash is the read key
and the name is the write key: anyone can read a hall by ID, but posting
needs the name. Computing IDs here lets a client read a hall it knows by name
without sending the name.

The rules: NFKC, full case fold, NFKC again; each run of separators (ASCII
non-alphanumerics, and Unicode punctuation, separators, and controls) becomes
one "-", with none leading or trailing; at most 128 code points. A name that
normalizes to nothing is invalid. The tests check these functions against
the server's own test vectors.
"""

from __future__ import annotations

import hashlib
import unicodedata

MAX_NAME_CHARS = 128


def _is_separator(c: str) -> bool:
    if c.isascii():
        return not c.isalnum()
    cat = unicodedata.category(c)
    return cat[0] in ('P', 'Z') or cat == 'Cc'


def normalize(name: str) -> str | None:
    """The normalized form of a hall name, or None if nothing is left."""
    s = unicodedata.normalize('NFKC', name)
    s = s.casefold()
    s = unicodedata.normalize('NFKC', s)
    out: list[str] = []
    sep = False
    for c in s:
        if _is_separator(c):
            sep = True
            continue
        if sep and out:
            out.append('-')
        sep = False
        out.append(c)
    result = ''.join(out)[:MAX_NAME_CHARS].rstrip('-')
    return result or None


def hall_id(name: str) -> str:
    """The hall ID (64 lowercase hex characters) for a hall name.

    Raises ValueError if the name has no letters or digits.
    """
    norm = normalize(name)
    if norm is None:
        raise ValueError('a hall name must contain at least one letter or digit')
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()
