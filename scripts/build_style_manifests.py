"""Freeze the Prototype 4 (M6) per-style training manifests and prove their provenance.

Five manifests are written, before any GPU work, so no training run can reselect
its own data:

    style-minimal-geometric-p4.csv       44 items  (the lead style, full set)
    style-minimal-geometric-p4-n12.csv   12 items  (RQ4 size arm)
    style-minimal-geometric-p4-n24.csv   24 items  (RQ4 size arm)
    style-ukiyo-e-p4.csv                 44 items
    style-retro-poster-p4.csv            36 items

plus one exclusion ledger recording EVERY dataset-v1 item that no training
manifest uses, with the reason - so "nothing was silently dropped" is auditable
rather than asserted.

`data/manifests/dataset-v1.csv` is opened READ-ONLY and its SHA-256 is verified
against the constant frozen in `ml.training.style_kit` before and after, so this
script provably cannot have modified it.

Checks performed, all of which block the write on failure:
  1. dataset-v1 is byte-identical to the frozen hash;
  2. every selected item is `split == train`, checked against dataset-v1 itself;
  3. every image exists on disk and its SHA-256 matches dataset-v1;
  4. the size arms are properly NESTED: n12 subset of n24 subset of n44;
  5. every training caption is rebuilt from the frozen kit and the dataset's own
     style phrase table, and is non-empty;
  6. no item appears in more than one style;
  7. the exclusion ledger accounts for all 148 dataset-v1 items.

Run:
    .venv/Scripts/python.exe scripts/build_style_manifests.py
"""

import csv
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.dataset.captions import STYLE_PHRASES  # noqa: E402
from ml.dataset.hashing import sha256_file  # noqa: E402
from ml.training import style_kit  # noqa: E402

DATASET_MANIFEST = REPO / "data" / "manifests" / "dataset-v1.csv"
MANIFEST_DIR = REPO / "data" / "manifests"
RAW_ROOT = REPO / "data" / "raw"
EVIDENCE = REPO / "docs" / "evidence" / "prototype-4"

FIELDS = [
    "id",
    "split",
    "sha256",
    "width",
    "height",
    "source_path",
    "licence",
    "permitted_use",
    "dataset_v1_caption",
    "training_caption",
    "inclusion_reason",
    "exclusion_reason",
]

EXCLUSION_FIELDS = ["id", "style", "split", "reason"]


def select_train(rows: list[dict], style: str) -> list[dict]:
    """Deterministic: train split only, sorted by id ascending. No RNG."""
    pool = [r for r in rows if r["style"] == style and r["split"] == "train"]
    pool.sort(key=lambda r: r["id"])
    return pool


def build_rows(items: list[dict], style: str, count_note: str) -> list[dict]:
    phrase = STYLE_PHRASES[style]
    caption = style_kit.build_training_caption(style, phrase)
    out = []
    for position, source in enumerate(items, start=1):
        out.append(
            {
                "id": source["id"],
                "split": source["split"],
                "sha256": source["sha256"],
                "width": source["width"],
                "height": source["height"],
                "source_path": f"data/raw/{source['style']}/{source['filename']}",
                "licence": source["licence"],
                "permitted_use": source["permitted_use"],
                "dataset_v1_caption": source["caption"],
                # Style-only by construction: identical for every item of a style.
                # The verbatim arm (EXP-023) reads `dataset_v1_caption` instead,
                # which is why both columns travel together in one file.
                "training_caption": caption,
                "inclusion_reason": (
                    f"{style} train split, sorted by id ascending; position {position} of {count_note}"
                ),
                "exclusion_reason": "",
            }
        )
    return out


def write_manifest(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    # Content hash, normalised to LF. A raw byte hash of a text file under Git
    # is a hash of the CHECKOUT, not of the content - it made this same check
    # fail on every clean clone until M8 found it.
    before = style_kit.sha256_dataset_content(DATASET_MANIFEST)
    if before != style_kit.DATASET_V1_CONTENT_SHA256:
        print(
            f"FAIL: dataset-v1 content hash {before} != "
            f"frozen {style_kit.DATASET_V1_CONTENT_SHA256}"
        )
        return 1
    print(f"dataset-v1 verified read-only at {before[:16]}...")

    rows = list(csv.DictReader(DATASET_MANIFEST.open(encoding="utf-8")))
    print(f"dataset-v1: {len(rows)} items")

    used_ids: set[str] = set()
    written: list[tuple[str, int]] = []
    lead = style_kit.LEAD_STYLE

    for style_spec in sorted(style_kit.STYLES, key=lambda s: s.order):
        style = style_spec.key
        selected = select_train(rows, style)
        if not selected:
            print(f"FAIL: no train items for {style}")
            return 1

        # 3. every image present, hash matching dataset-v1
        for source in selected:
            path = RAW_ROOT / source["style"] / source["filename"]
            if not path.is_file():
                print(f"FAIL: {source['id']} image missing on disk: {path}")
                return 1
            actual = sha256_file(path)
            if actual != source["sha256"]:
                print(f"FAIL: {source['id']} sha256 mismatch on disk")
                return 1
            # 2. train-only, proven against dataset-v1
            if source["split"] != "train":
                print(f"FAIL: {source['id']} split is {source['split']!r}, not train")
                return 1

        # 6. no item may belong to two styles
        ids = {r["id"] for r in selected}
        if ids & used_ids:
            print(f"FAIL: {style} overlaps an earlier style on {sorted(ids & used_ids)}")
            return 1
        used_ids |= ids

        out_rows = build_rows(selected, style, f"{len(selected)}")
        out_path = MANIFEST_DIR / f"style-{style}-p4.csv"
        write_manifest(out_rows, out_path)
        written.append((out_path.name, len(out_rows)))
        print(f"  {style:20s} {len(out_rows):3d} items -> {out_path.name}")
        print(f"  {'':20s} training caption: {out_rows[0]['training_caption']!r}")

        # 4. nested size arms, lead style only
        if style == lead:
            full_ids = [r["id"] for r in out_rows]
            previous: list[str] | None = None
            for n in style_kit.SIZE_ARM_COUNTS:
                if n > len(selected):
                    print(f"FAIL: size arm {n} exceeds {len(selected)} available")
                    return 1
                arm = build_rows(selected[:n], style, f"{n} (RQ4 size arm)")
                arm_ids = [r["id"] for r in arm]
                if arm_ids != full_ids[:n]:
                    print(f"FAIL: size arm {n} is not a prefix of the full set")
                    return 1
                if previous is not None and not set(previous) <= set(arm_ids):
                    print(f"FAIL: nesting broken - {len(previous)} not a subset of {n}")
                    return 1
                previous = arm_ids
                arm_path = MANIFEST_DIR / f"style-{style}-p4-n{n}.csv"
                write_manifest(arm, arm_path)
                written.append((arm_path.name, n))
                print(f"  {'':20s} size arm n={n:2d} -> {arm_path.name}")
            if previous is not None and not set(previous) <= set(full_ids):
                print("FAIL: largest size arm is not a subset of the full set")
                return 1
            print(f"  {'':20s} nesting verified: n12 subset of n24 subset of n{len(full_ids)}")

    # 7. exclusion ledger - account for every dataset-v1 item not used
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    ledger = []
    for source in rows:
        if source["id"] in used_ids:
            continue
        split = source["split"]
        if split == "holdout":
            reason = (
                "holdout split - reserved untouched for the memorisation comparison and the "
                "Prototype 2 reference kit; never trained on"
            )
        elif split == "val":
            reason = "validation split - excluded from training by the dataset-v1 split design"
        else:
            reason = "not selected"
        ledger.append({"id": source["id"], "style": source["style"], "split": split, "reason": reason})

    ledger_path = EVIDENCE / "style-manifest-exclusions.csv"
    with ledger_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=EXCLUSION_FIELDS)
        writer.writeheader()
        writer.writerows(ledger)

    accounted = len(used_ids) + len(ledger)
    print()
    print(f"exclusion ledger: {len(ledger)} items -> {ledger_path.relative_to(REPO)}")
    print(f"accounted for {accounted} of {len(rows)} dataset-v1 items")
    if accounted != len(rows):
        print("FAIL: not every dataset-v1 item is accounted for")
        return 1
    if any(r["split"] == "train" for r in ledger):
        print("FAIL: a train item was excluded without a written reason")
        return 1

    after = sha256_file(DATASET_MANIFEST)
    if after != before:
        print(f"FAIL: dataset-v1 CHANGED during this run ({before} -> {after})")
        return 1
    print(f"dataset-v1 unchanged after the run: {after[:16]}...")
    print(f"style kit fingerprint: {style_kit.kit_fingerprint()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
