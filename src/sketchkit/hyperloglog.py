"""A HyperLogLog: approximate count of distinct items in tiny, fixed memory."""

from __future__ import annotations

import math

from sketchkit._hashing import base_hashes


class HyperLogLog:
    """
    Estimates how many *distinct* items a stream contained, using a few kilobytes regardless of
    the true count. The idea: hash each item and look at the run of leading zero bits; seeing a
    run of length ``r`` hints that around ``2**r`` distinct items have passed. To tame the
    variance, items are split across ``2**p`` registers by the first ``p`` bits of their hash,
    each register keeps the largest run it has seen, and the estimate is a bias-corrected
    harmonic mean across registers.

    Memory is ``2**p`` bytes; the relative error is about ``1.04 / sqrt(2**p)``.
    """

    def __init__(self, precision: int = 14) -> None:
        if not 4 <= precision <= 16:
            raise ValueError("precision must be between 4 and 16")
        self.precision = precision
        self.num_registers = 1 << precision
        self._registers = bytearray(self.num_registers)
        self._alpha = self._bias_constant(self.num_registers)

    @staticmethod
    def _bias_constant(m: int) -> float:
        if m == 16:
            return 0.673
        if m == 32:
            return 0.697
        if m == 64:
            return 0.709
        return 0.7213 / (1 + 1.079 / m)

    def add(self, item: object) -> None:
        # Use the full 64-bit hash: the top `precision` bits pick the register, and the
        # remaining `w` bits are scanned for the first 1-bit from the left.
        h1, h2 = base_hashes(item)
        value = (h2 << 32) | h1  # recombine into 64 bits
        w = 64 - self.precision
        index = value >> w
        suffix = value & ((1 << w) - 1)
        # Rank = number of leading zeros in the w-bit suffix, plus one.
        rank = (w - suffix.bit_length() + 1) if suffix else (w + 1)
        if rank > self._registers[index]:
            self._registers[index] = rank

    def count(self) -> int:
        """The estimated number of distinct items added."""
        m = self.num_registers
        raw = self._alpha * m * m / sum(2.0**-r for r in self._registers)

        if raw <= 2.5 * m:
            # Small-range correction: count empty registers and use linear counting.
            zeros = self._registers.count(0)
            if zeros != 0:
                return round(m * math.log(m / zeros))
        return round(raw)

    def __len__(self) -> int:
        return self.count()
