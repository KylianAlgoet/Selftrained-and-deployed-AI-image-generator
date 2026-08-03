"""Freeze the Prototype 3 (M5) LoRA smoke-test subset and prove its provenance.

The subset is fixed BEFORE any GPU work so that no training run can quietly
reselect its own data and then be compared against a differently-configured
sibling. Dataset v1 is READ, never written.

What this script does, in order:
  1. loads `data/manifests/dataset-v1.csv` read-only;
  2. applies the deterministic selection rule frozen in `ml.training.smoke_kit`
     (no RNG) and checks the result equals the frozen ID tuple;
  3. proves NO item comes from the `val` or `holdout` split, checked against
     dataset-v1 itself rather than against the new manifest's own column;
  4. verifies every image exists on disk and its SHA-256 matches dataset-v1
     byte-for-byte;
  5. verifies every caption is the dataset-v1 caption verbatim and begins with
     the frozen style phrase (the frozen caption strategy: no trigger token);
  6. verifies palette and shape-count coverage, so a silent rebuild cannot
     degrade the subset's spread;
  7. writes `data/manifests/smoke-test-p3.csv`.

It writes exactly one file and nothing else.

Run:
    .venv/Scripts/python.exe scripts/build_smoke_test_manifest.py
"""

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.dataset.hashing import sha256_file  # noqa: E402
from ml.training.smoke_kit import (  # noqa: E402
    CAPTION_STRATEGY,
    FORBIDDEN_SPLITS,
    SMOKE_ITEM_IDS,
    SMOKE_MANIFEST_PATH,
    SMOKE_SELECTION_RULE,
    SMOKE_STYLE,
    SMOKE_STYLE_PHRASE,
    SMOKE_SUBSET_SIZE,
    kit_fingerprint,
)

DATASET_MANIFEST = REPO / "data" / "manifests" / "dataset-v1.csv"
RAW_ROOT = REPO / "data" / "raw"

FIELDS = [
    "id",
    "filename",
    "source_path",
    "style",
    "split",
    "width",
    "height",
    "sha256",
    "caption",
    "inclusion_reason",
]

NOTE_RE = re.compile(r"seed=(\d+), palette_index=(\d+), shape_count=(\d+)")


def select(rows: list[dict]) -> list[dict]:
    """The frozen deterministic rule. No RNG, no sampling."""
    pool = [r for r in rows if r["style"] == SMOKE_STYLE and r["split"] == "train"]
    pool.sort(key=lambda r: r["id"])
    return pool[:SMOKE_SUBSET_SIZE]


def main() -> int:
    rows = list(csv.DictReader(DATASET_MANIFEST.open(encoding="utf-8")))
    by_id = {r["id"]: r for r in rows}
    print(f"dataset-v1: {len(rows)} items")

    selected = select(rows)
    ids = tuple(r["id"] for r in selected)

    # 2. the rule must reproduce the frozen tuple exactly
    if ids != SMOKE_ITEM_IDS:
        print(f"FAIL: selection rule produced {ids}, frozen kit expects {SMOKE_ITEM_IDS}")
        return 1
    print(f"rule reproduces the frozen {len(ids)} ids exactly")

    out_rows = []
    palettes, shapes = set(), set()

    for row in selected:
        item_id = row["id"]
        source = by_id[item_id]

        # 3. holdout/val exclusion, proven against dataset-v1
        if source["split"] in FORBIDDEN_SPLITS:
            print(f"FAIL: {item_id} is split={source['split']!r}, which is forbidden")
            return 1
        if source["split"] != "train":
            print(f"FAIL: {item_id} is split={source['split']!r}, expected 'train'")
            return 1

        # 4. the image must exist and hash byte-for-byte to the manifest value
        path = RAW_ROOT / source["style"] / source["filename"]
        if not path.is_file():
            print(f"FAIL: {item_id} image missing on disk: {path}")
            return 1
        actual = sha256_file(path)
        if actual != source["sha256"]:
            print(f"FAIL: {item_id} sha256 mismatch\n  manifest {source['sha256']}\n  on disk  {actual}")
            return 1

        # 5. caption strategy: dataset caption verbatim, frozen style phrase
        caption = source["caption"]
        if not caption.startswith(SMOKE_STYLE_PHRASE):
            print(f"FAIL: {item_id} caption does not begin with the frozen style phrase")
            return 1

        note = NOTE_RE.search(source["notes"] or "")
        if note:
            palettes.add(int(note.group(2)))
            shapes.add(int(note.group(3)))

        out_rows.append(
            {
                "id": item_id,
                "filename": source["filename"],
                "source_path": f"data/raw/{source['style']}/{source['filename']}",
                "style": source["style"],
                "split": source["split"],
                "width": source["width"],
                "height": source["height"],
                "sha256": actual,
                "caption": caption,
                "inclusion_reason": (
                    f"{SMOKE_SELECTION_RULE}; position {len(out_rows) + 1} of {SMOKE_SUBSET_SIZE}"
                ),
            }
        )

    print(f"all {len(out_rows)} images present, hashes match dataset-v1, captions verbatim")
    print(f"no item from splits {FORBIDDEN_SPLITS}")

    # 6. coverage, so a silent rebuild cannot degrade the spread
    print(f"palette coverage: {sorted(palettes)} ({len(palettes)} distinct)")
    print(f"shape-count coverage: {sorted(shapes)} ({len(shapes)} distinct)")
    if len(palettes) < 6 or len(shapes) < 6:
        print("FAIL: subset no longer covers all 6 palettes and all 6 shape counts")
        return 1

    out_path = REPO / SMOKE_MANIFEST_PATH
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)

    print()
    print(f"caption strategy: {CAPTION_STRATEGY}")
    print(f"smoke kit fingerprint: {kit_fingerprint()}")
    print(f"wrote {SMOKE_MANIFEST_PATH} ({len(out_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
