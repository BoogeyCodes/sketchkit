"""A Count-Min Sketch: approximate frequency counts for a stream."""

from __future__ import annotations

import math

from sketchkit._hashing import base_hashes


class CountMinSketch:
    """
    Estimates how many times each item has been seen, using a fixed amount of memory no matter
    how many distinct items there are. It keeps a ``depth`` x ``width`` grid of counters; each
    item increments one counter per row, and its estimate is the *minimum* of those counters.

    Collisions can only ever push a counter up, so the estimate is never an underestimate; the
    minimum across rows cancels most of the overcount. With ``width = ceil(e/epsilon)`` and
    ``depth = ceil(ln(1/delta))`` the error is at most ``epsilon * total`` with probability
    ``1 - delta``.
    """

    def __init__(self, width: int = 2000, depth: int = 5) -> None:
        if width < 1 or depth < 1:
            raise ValueError("width and depth must be at least 1")
        self.width = width
        self.depth = depth
        self._rows = [[0] * width for _ in range(depth)]
        self._total = 0

    @classmethod
    def from_error(cls, epsilon: float, delta: float) -> CountMinSketch:
        """Build a sketch whose error is at most ``epsilon`` * total with probability 1 - ``delta``."""
        if not 0.0 < epsilon < 1.0 or not 0.0 < delta < 1.0:
            raise ValueError("epsilon and delta must be between 0 and 1 (exclusive)")
        width = math.ceil(math.e / epsilon)
        depth = math.ceil(math.log(1 / delta))
        return cls(width=width, depth=max(1, depth))

    def _columns(self, item: object) -> list[int]:
        # Derive one column per row from two base hashes (Kirsch-Mitzenmacher).
        h1, h2 = base_hashes(item)
        return [(h1 + row * h2) % self.width for row in range(self.depth)]

    def add(self, item: object, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be non-negative")
        for row, col in enumerate(self._columns(item)):
            self._rows[row][col] += count
        self._total += count

    def estimate(self, item: object) -> int:
        """The estimated number of times ``item`` was added. Never an underestimate."""
        return min(self._rows[row][col] for row, col in enumerate(self._columns(item)))

    def __getitem__(self, item: object) -> int:
        return self.estimate(item)

    @property
    def total(self) -> int:
        return self._total
