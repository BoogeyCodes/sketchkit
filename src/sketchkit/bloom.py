"""A Bloom filter: approximate set membership in a bit array."""

from __future__ import annotations

import math

from sketchkit._hashing import hashes


class BloomFilter:
    """
    A space-efficient set that answers "have I seen this?" with no false negatives and a
    tunable false-positive rate. An item is added by setting ``k`` bits; it is considered
    present if all ``k`` of its bits are set. Because bits are shared between items, a
    *present* answer can be wrong (a false positive) but an *absent* answer never is.

    Size the filter for the number of items you expect and the false-positive rate you can
    tolerate; the optimal bit-count ``m`` and hash-count ``k`` are derived for you.
    """

    def __init__(self, capacity: int, error_rate: float = 0.01) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        if not 0.0 < error_rate < 1.0:
            raise ValueError("error_rate must be between 0 and 1 (exclusive)")

        self.capacity = capacity
        self.error_rate = error_rate
        # Optimal size and hash count for the target rate (standard Bloom-filter formulas).
        self.size = max(1, math.ceil(-capacity * math.log(error_rate) / (math.log(2) ** 2)))
        self.hash_count = max(1, round((self.size / capacity) * math.log(2)))
        self._bits = bytearray((self.size + 7) // 8)
        self._count = 0

    def _positions(self, item: object) -> list[int]:
        return list(hashes(item, self.hash_count, self.size))

    def add(self, item: object) -> None:
        for pos in self._positions(item):
            self._bits[pos >> 3] |= 1 << (pos & 7)
        self._count += 1

    def __contains__(self, item: object) -> bool:
        return all(self._bits[pos >> 3] & (1 << (pos & 7)) for pos in self._positions(item))

    def update(self, items: object) -> None:
        for item in items:  # type: ignore[attr-defined]
            self.add(item)

    def __len__(self) -> int:
        """The number of times :meth:`add` was called (not the distinct count)."""
        return self._count

    @property
    def bits_set(self) -> int:
        return sum(byte.bit_count() for byte in self._bits)

    def estimated_error_rate(self) -> float:
        """Current false-positive probability given how full the filter is."""
        fraction_set = self.bits_set / self.size
        return fraction_set**self.hash_count
