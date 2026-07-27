import pytest

from ml.dataset.split import assign_split


def test_deterministic_across_calls():
    ids = [f"DS-{i:04d}" for i in range(200)]
    first = [assign_split(item_id) for item_id in ids]
    second = [assign_split(item_id) for item_id in ids]
    assert first == second


def test_ratios_approximated_over_many_ids():
    ids = [f"DS-{i:04d}" for i in range(2000)]
    splits = [assign_split(item_id) for item_id in ids]
    train = splits.count("train") / len(splits)
    val = splits.count("val") / len(splits)
    holdout = splits.count("holdout") / len(splits)
    assert 0.75 < train < 0.85
    assert 0.07 < val < 0.13
    assert 0.07 < holdout < 0.13


def test_seed_changes_assignment_but_stays_valid():
    ids = [f"DS-{i:04d}" for i in range(300)]
    a = [assign_split(i, seed=42) for i in ids]
    b = [assign_split(i, seed=1337) for i in ids]
    assert a != b
    assert set(a) | set(b) <= {"train", "val", "holdout"}


def test_invalid_ratios_rejected():
    with pytest.raises(ValueError, match="sum to 1"):
        assign_split("DS-0001", ratios={"train": 0.5, "val": 0.2, "holdout": 0.2})
