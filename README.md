# sketchkit

[![CI](https://github.com/BoogeyCodes/sketchkit/actions/workflows/ci.yml/badge.svg)](https://github.com/BoogeyCodes/sketchkit/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)
![No dependencies](https://img.shields.io/badge/dependencies-none-success)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

Three probabilistic data structures in pure Python, with no dependencies. Each answers a question
about a stream using a fixed, tiny amount of memory, trading a little accuracy for a lot of space.

| Structure | Question it answers | Memory | Error |
| --- | --- | --- | --- |
| **Bloom filter** | "Have I seen this item?" | ~1.2 KB per 1,000 items at 1% | false positives only, never false negatives |
| **Count-Min Sketch** | "How many times has this item appeared?" | a fixed grid, independent of item count | never underestimates |
| **HyperLogLog** | "How many *distinct* items were there?" | a few KB for billions of items | ~1% relative |

```python
from sketchkit import BloomFilter, CountMinSketch, HyperLogLog

seen = BloomFilter(capacity=1_000_000, error_rate=0.01)
seen.add("alice@example.com")
"alice@example.com" in seen   # True
"bob@example.com" in seen     # almost always False

freq = CountMinSketch.from_error(epsilon=0.001, delta=0.01)
for word in stream:
    freq.add(word)
freq.estimate("the")          # approximate count, never too low

distinct = HyperLogLog(precision=14)
for visitor_id in visits:
    distinct.add(visitor_id)
distinct.count()              # distinct visitors, within ~1%, in 16 KB
```

## Why

Exact answers to "have I seen this?", "how often?" and "how many distinct?" need memory that grows
with the data — a set, a counter dict, another set. At scale that is the whole problem. These three
structures answer the same questions in **constant** memory by allowing a small, bounded error, and
they are a genuinely elegant corner of computer science. sketchkit implements them from first
principles, clearly enough to read, with tests that check the probabilistic guarantees actually hold.

Measured on real inputs (see the demo below), the defaults deliver:

```
Bloom   : 958,506 bits, 7 hashes; false positives 0.99% against a 1% target
CountMin: 'hot' key actual 142,858, estimate 142,943 (0.06% high, never low)
HLL     : 500,000 distinct counted as 495,697 using 16 KB (0.86% off)
```

## Install

```bash
pip install git+https://github.com/BoogeyCodes/sketchkit.git
```

Python 3.10+. Standard library only.

## The three structures

### Bloom filter — approximate membership

A bit array plus `k` hash functions. Adding an item sets `k` bits; the item is "present" if all `k`
are set. Because bits are shared, a *present* answer can be a false positive, but an *absent* answer
is never wrong. You give it the number of items you expect and the false-positive rate you can
tolerate, and it derives the optimal bit-count and hash-count.

```python
bf = BloomFilter(capacity=10_000, error_rate=0.01)
bf.update(known_ids)
if candidate not in bf:
    # definitely new — safe to do the expensive check
    ...
```

### Count-Min Sketch — approximate frequencies

A `depth x width` grid of counters. Each item increments one counter per row; its estimate is the
*minimum* of those counters. Collisions can only push counters up, so the estimate never
underestimates, and the minimum cancels most of the overcount. Size it directly from an error target:
`from_error(epsilon, delta)` guarantees the error is at most `epsilon x total` with probability
`1 - delta`.

```python
cms = CountMinSketch.from_error(epsilon=0.001, delta=0.01)
cms.add("GET /api/users", 1)
cms.estimate("GET /api/users")
```

### HyperLogLog — approximate distinct count

Hash each item; the length of the leading run of zero bits hints at how many distinct items have been
seen. Averaging that across `2**precision` registers (by a bias-corrected harmonic mean, with a
linear-counting correction for small counts) estimates the cardinality in a few kilobytes, whatever
the true number. Relative error is about `1.04 / sqrt(2**precision)`.

```python
hll = HyperLogLog(precision=14)   # 16 KB, ~0.8% error
for event in events:
    hll.add(event.user_id)
hll.count()
```

## A note on hashing

All three hash with BLAKE2b from the standard library, not Python's built-in `hash`, which is salted
per process and so would give different results across runs. A single 64-bit digest is split and the
Kirsch–Mitzenmacher technique derives every hash a structure needs as `h1 + i * h2`, so each item is
hashed once rather than `k` times. Results are reproducible across processes and machines — a property
the tests assert.

## Testing

```bash
pip install -e ".[dev]"
pytest
```

Thirty tests. Beyond the usual unit checks, they verify the probabilistic guarantees on real data:
the Bloom filter's observed false-positive rate stays near its target and it never gives a false
negative; the Count-Min Sketch never underestimates and its overestimate stays within the
`epsilon x total` bound; and the HyperLogLog's estimate lands within a few standard errors of the
truth, with higher precision measurably more accurate. CI runs them on Python 3.10 through 3.13.

## Project layout

```
src/sketchkit
├── _hashing.py      BLAKE2b base hashes + Kirsch-Mitzenmacher combination
├── bloom.py         BloomFilter
├── countmin.py      CountMinSketch
└── hyperloglog.py   HyperLogLog
tests/               pytest, including statistical guarantee checks
```

## Ideas for later

- Union and intersection of Bloom filters and HyperLogLogs.
- A scalable Bloom filter that grows instead of being pre-sized.
- Serialisation so a sketch can be saved and merged across machines.

## License

MIT
