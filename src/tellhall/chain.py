"""The post hash chain.

Each published post's hash covers the previous post's hash (the hall ID for
the first post), the hall ID, its sequence number, the author's ring ID, its
publication time, and its public body. Variable-length fields are
length-prefixed, so no two different posts share an encoding. A client that
checks the chain knows the server has not edited, dropped, or reordered posts
since it last read them.
"""

from __future__ import annotations

import hashlib
import hmac
import struct
from typing import Any, Mapping


class ChainError(Exception):
    """A hall's posts do not form a valid hash chain."""


def post_hash(
    prev_hash: bytes,
    hall_id: str,
    seq: int,
    ring_id: str,
    published_at: str,
    body: str,
) -> str:
    """The hex hash of one post.

    `published_at` must be exactly as the server sends it, for example
    "2026-09-24T17:20:31.000000Z".
    """
    h = hashlib.sha256()
    h.update(prev_hash)
    h.update(bytes.fromhex(hall_id))
    h.update(struct.pack('>Q', seq))
    for field in (ring_id, published_at, body):
        b = field.encode('utf-8')
        h.update(struct.pack('>I', len(b)))
        h.update(b)
    return h.hexdigest()


def verify_chain(hall: Mapping[str, Any]) -> None:
    """Checks a hall as returned by `Client.read_hall`.

    Posts must run from sequence 1 without gaps, and each post's hash must
    match its contents and its predecessor. Raises ChainError otherwise.
    """
    hid = hall['id']
    prev = bytes.fromhex(hid)
    for expected_seq, p in enumerate(hall['posts'], start=1):
        if p['seq'] != expected_seq:
            raise ChainError(f'expected post {expected_seq}, found post {p["seq"]}')
        digest = post_hash(
            prev, hid, p['seq'], p['ring_id'], p['published_at'], p['body']
        )
        if not hmac.compare_digest(digest, p['hash']):
            raise ChainError(f'post {p["seq"]} does not match its hash')
        prev = bytes.fromhex(digest)
