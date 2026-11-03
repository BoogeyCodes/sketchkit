from __future__ import annotations

import pytest

from sketchkit import BloomFilter


def test_added_items_are_always_found():
    bf = BloomFilter(capacity=1000, error_rate=0.01)
    items = [f"item-{i}" for i in range(1000)]
    for item in items:
        bf.add(item)
    # No false negatives, ever.
    assert all(item in bf for item in items)
    assert len(bf) == 1000


def test_absent_items_are_usually_absent():
    bf = BloomFilter(capacity=1000, error_rate=0.01)
    for i in range(1000):
        bf.add(f"present-{i}")

    absent = [f"absent-{i}" for i in range(5000)]
    false_positives = sum(item in bf for item in absent)
    rate = false_positives / len(absent)
    # Observed rate should be in the neighbourhood of the configured 1%.
    assert rate < 0.03


def test_sizing_follows_the_formulas():
    bf = BloomFilter(capacity=10_000, error_rate=0.01)
    # ~9.6 bits per item and ~7 hashes is the known optimum for 1%.
    assert 9 * 10_000 <= bf.size <= 10 * 10_000
    assert bf.hash_count == 7


def test_lower_error_rate_costs_more_bits():
    loose = BloomFilter(capacity=1000, error_rate=0.1)
    tight = BloomFilter(capacity=1000, error_rate=0.001)
    assert tight.size > loose.size


def test_bits_set_and_estimated_rate_grow_with_load():
    bf = BloomFilter(capacity=500, error_rate=0.01)
    assert bf.bits_set == 0
    assert bf.estimated_error_rate() == 0.0
    for i in range(500):
        bf.add(i)
    assert bf.bits_set > 0
    assert 0.0 < bf.estimated_error_rate() < 0.05


def test_update_adds_many():
    bf = BloomFilter(capacity=100)
    bf.update(range(50))
    assert all(i in bf for i in range(50))


def test_hashing_is_reproducible_across_instances():
    a = BloomFilter(capacity=100, error_rate=0.01)
    b = BloomFilter(capacity=100, error_rate=0.01)
    assert a._positions("same-key") == b._positions("same-key")


@pytest.mark.parametrize("capacity,error", [(0, 0.01), (100, 0.0), (100, 1.0), (100, -0.1)])
def test_validates_arguments(capacity: int, error: float):
    with pytest.raises(ValueError):
        BloomFilter(capacity=capacity, error_rate=error)
