"""Shared hashing helpers.

All structures hash with BLAKE2b from the standard library rather than Python's built-in
``hash``, which is salted per process and so would not be reproducible across runs. A single
64-bit digest is split into two 32-bit halves, and the Kirsch-Mitzenmacher technique then
derives any number of hash functions as ``h1 + i * h2``. This gives k independent-enough hashes
from one digest, instead of hashing k times.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator

_MASK32 = 0xFFFFFFFF


def to_bytes(item: object) -> bytes:
    if isinstance(item, bytes):
        return item
    if isinstance(item, str):
        return item.encode("utf-8")
    return repr(item).encode("utf-8")


def base_hashes(item: object) -> tuple[int, int]:
    """Return two 32-bit hashes derived from one 64-bit BLAKE2b digest."""
    digest = hashlib.blake2b(to_bytes(item), digest_size=8).digest()
    value = int.from_bytes(digest, "big")
    return value & _MASK32, (value >> 32) & _MASK32


def hashes(item: object, count: int, modulo: int) -> Iterator[int]:
    """Yield ``count`` hashes in ``[0, modulo)`` via the Kirsch-Mitzenmacher combination."""
    h1, h2 = base_hashes(item)
    for i in range(count):
        yield (h1 + i * h2) % modulo
