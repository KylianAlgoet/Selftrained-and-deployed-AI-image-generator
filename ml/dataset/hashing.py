"""Content hashing and duplicate detection (exact SHA-256, perceptual dHash)."""

import hashlib
from collections import defaultdict
from pathlib import Path

import imagehash
from PIL import Image

NEAR_DUPLICATE_MAX_DISTANCE = 6


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dhash_file(path: str | Path) -> imagehash.ImageHash:
    with Image.open(path) as img:
        return imagehash.dhash(img)


def find_exact_duplicates(sha_by_id: dict[str, str]) -> list[list[str]]:
    """Group item IDs sharing an identical SHA-256. Returns only groups > 1."""
    groups: dict[str, list[str]] = defaultdict(list)
    for item_id, sha in sha_by_id.items():
        groups[sha].append(item_id)
    return [sorted(ids) for ids in groups.values() if len(ids) > 1]


def find_near_duplicates(
    dhash_by_id: dict[str, imagehash.ImageHash],
    max_distance: int = NEAR_DUPLICATE_MAX_DISTANCE,
) -> list[tuple[str, str, int]]:
    """Pairs of item IDs whose perceptual-hash distance is <= max_distance."""
    ids = sorted(dhash_by_id)
    pairs: list[tuple[str, str, int]] = []
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            distance = dhash_by_id[a] - dhash_by_id[b]
            if distance <= max_distance:
                pairs.append((a, b, distance))
    return pairs
