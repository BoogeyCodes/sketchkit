from __future__ import annotations

import pytest

from sketchkit import HyperLogLog


def test_exact_for_tiny_cardinalities():
    hll = HyperLogLog(precision=14)
    for item in ["a", "b", "c"]:
        hll.add(item)
    # Linear counting makes small counts essentially exact.
    assert hll.count() == 3


def test_duplicates_do_not_inflate_the_count():
    hll = HyperLogLog(precision=14)
    for _ in range(10_000):
        hll.add("the-same-item")
    assert hll.count() == 1


@pytest.mark.parametrize("true_count", [100, 1_000, 10_000, 100_000])
def test_estimate_is_within_expected_error(true_count: int):
    precision = 14
    hll = HyperLogLog(precision=precision)
    for i in range(true_count):
        hll.add(f"item-{i}")

    estimate = hll.count()
    expected_error = 1.04 / (2 ** (precision / 2))
    relative_error = abs(estimate - true_count) / true_count
    # Allow a comfortable multiple of the standard error for a single run.
    assert relative_error < 4 * expected_error


def test_higher_precision_is_more_accurate_on_average():
    true_count = 50_000
    errors = {}
    for precision in (8, 14):
        hll = HyperLogLog(precision=precision)
        for i in range(true_count):
            hll.add(i)
        errors[precision] = abs(hll.count() - true_count) / true_count
    assert errors[14] < errors[8]


def test_len_matches_count():
    hll = HyperLogLog(precision=12)
    for i in range(500):
        hll.add(i)
    assert len(hll) == hll.count()


def test_hashing_is_reproducible():
    a = HyperLogLog(precision=12)
    b = HyperLogLog(precision=12)
    for i in range(1000):
        a.add(i)
        b.add(i)
    assert a.count() == b.count()


@pytest.mark.parametrize("precision", [3, 17])
def test_validates_precision(precision: int):
    with pytest.raises(ValueError):
        HyperLogLog(precision=precision)
