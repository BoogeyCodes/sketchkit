from __future__ import annotations

import pytest

from sketchkit import CountMinSketch


def test_estimate_is_never_below_the_truth():
    cms = CountMinSketch(width=500, depth=4)
    truth: dict[str, int] = {}
    # A skewed stream: some items very frequent, many rare.
    stream = [f"item-{i % 300}" for i in range(20_000)]
    for item in stream:
        cms.add(item)
        truth[item] = truth.get(item, 0) + 1

    for item, actual in truth.items():
        assert cms.estimate(item) >= actual  # one-sided error: never underestimates


def test_error_is_bounded_by_epsilon_times_total():
    epsilon, delta = 0.001, 0.01
    cms = CountMinSketch.from_error(epsilon, delta)
    truth: dict[str, int] = {}
    for i in range(50_000):
        item = f"k{i % 1000}"
        cms.add(item)
        truth[item] = truth.get(item, 0) + 1

    allowed = epsilon * cms.total
    overestimates = [cms.estimate(k) - v for k, v in truth.items()]
    # The guarantee holds with probability 1 - delta; allow a tiny slack for the rare miss.
    within = sum(1 for e in overestimates if e <= allowed)
    assert within / len(overestimates) >= 1 - 5 * delta


def test_exact_for_few_items_without_collisions():
    cms = CountMinSketch(width=5000, depth=5)
    cms.add("a", 3)
    cms.add("b", 10)
    cms.add("a")
    assert cms.estimate("a") == 4
    assert cms.estimate("b") == 10
    assert cms["b"] == 10
    assert cms.total == 14


def test_unseen_item_estimates_zero_or_small():
    cms = CountMinSketch(width=5000, depth=5)
    for i in range(100):
        cms.add(f"seen-{i}")
    assert cms.estimate("never-seen") <= 1


def test_from_error_dimensions():
    cms = CountMinSketch.from_error(epsilon=0.01, delta=0.01)
    assert cms.width >= 271  # ceil(e / 0.01)
    assert cms.depth >= 5    # ceil(ln(100))


@pytest.mark.parametrize("width,depth", [(0, 5), (5, 0)])
def test_validates_dimensions(width: int, depth: int):
    with pytest.raises(ValueError):
        CountMinSketch(width=width, depth=depth)


def test_rejects_negative_count():
    with pytest.raises(ValueError):
        CountMinSketch().add("x", -1)
