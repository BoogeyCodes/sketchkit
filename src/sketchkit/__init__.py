"""sketchkit: small, dependency-free probabilistic data structures.

Each structure trades a little accuracy for a lot of memory:

- :class:`BloomFilter`    - approximate set membership, no false negatives.
- :class:`CountMinSketch` - approximate frequency counts for a stream.
- :class:`HyperLogLog`    - approximate count of distinct items.
"""

from sketchkit.bloom import BloomFilter
from sketchkit.countmin import CountMinSketch
from sketchkit.hyperloglog import HyperLogLog

__version__ = "0.1.0"
__all__ = ["BloomFilter", "CountMinSketch", "HyperLogLog"]
