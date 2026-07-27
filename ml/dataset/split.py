"""Deterministic train/val/holdout assignment.

The split is a pure function of (seed, item id): stable across runs and
independent of processing order, so re-running the pipeline never reshuffles
existing items.
"""

import hashlib

DEFAULT_SEED = 42
DEFAULT_RATIOS = {"train": 0.8, "val": 0.1, "holdout": 0.1}


def assign_split(
    item_id: str,
    seed: int = DEFAULT_SEED,
    ratios: dict[str, float] | None = None,
) -> str:
    ratios = ratios or DEFAULT_RATIOS
    if abs(sum(ratios.values()) - 1.0) > 1e-9:
        raise ValueError("split ratios must sum to 1")
    digest = hashlib.sha256(f"{seed}:{item_id}".encode()).hexdigest()
    # 12 hex chars -> uniform float in [0, 1)
    fraction = int(digest[:12], 16) / 16**12
    cumulative = 0.0
    for name, ratio in ratios.items():
        cumulative += ratio
        if fraction < cumulative:
            return name
    return list(ratios)[-1]
