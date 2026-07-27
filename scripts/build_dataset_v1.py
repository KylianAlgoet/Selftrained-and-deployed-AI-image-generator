"""Build the validated dataset v1 manifest from collected candidates.

Pipeline: decode/resolution validation -> SHA-256 exact dedupe -> perceptual
near-dedupe -> ID assignment -> template captions -> deterministic splits ->
schema validation -> statistics -> contact sheets -> curation log.

Raw images stay in data/raw/ (git-ignored). Committed outputs:
data/manifests/dataset-v1.csv, docs/evidence/dataset-v1/*.
"""

import csv
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.dataset.captions import build_caption  # noqa: E402
from ml.dataset.contact_sheet import make_contact_sheet  # noqa: E402
from ml.dataset.hashing import dhash_file, find_exact_duplicates, find_near_duplicates, sha256_file  # noqa: E402
from ml.dataset.manifest import save_manifest, validate_manifest  # noqa: E402
from ml.dataset.split import assign_split  # noqa: E402
from ml.dataset.stats import compute_stats, render_stats_markdown  # noqa: E402
from ml.dataset.validate import validate_image  # noqa: E402

RAW = REPO / "data" / "raw"
CANDIDATES_CSV = RAW / "candidates.csv"
MANIFEST_CSV = REPO / "data" / "manifests" / "dataset-v1.csv"
EVIDENCE = REPO / "docs" / "evidence" / "dataset-v1"

# Manual visual-review exclusions (condition C: visual coherence). Items that
# passed automated checks but were rejected after inspecting the contact sheets.
MANUAL_EXCLUDE = {
    "met-61658.jpg": "off-style: 3D wood sculpture of a bodhisattva, not a woodblock print",
}


def main() -> None:
    with open(CANDIDATES_CSV, newline="", encoding="utf-8") as fh:
        candidates = list(csv.DictReader(fh))
    print(f"candidates: {len(candidates)}")

    curation_log: list[str] = []
    accepted: list[dict] = []

    # 1) Decode + resolution validation (+ manual visual-review exclusions)
    for row in candidates:
        if row["filename"] in MANUAL_EXCLUDE:
            curation_log.append(f"REJECT (manual review: {MANUAL_EXCLUDE[row['filename']]}): {row['filename']}")
            continue
        path = RAW / row["style"] / row["filename"]
        if not path.exists():
            curation_log.append(f"REJECT (missing file): {row['filename']}")
            continue
        result = validate_image(path)
        if not result.ok:
            curation_log.append(f"REJECT ({result.reason}): {row['filename']}")
            continue
        row["_path"] = path
        row["width"] = str(result.width)
        row["height"] = str(result.height)
        accepted.append(row)
    print(f"after validation: {len(accepted)}")

    # 2) Exact duplicates (keep first of each group)
    sha_by_name = {row["filename"]: sha256_file(row["_path"]) for row in accepted}
    drop: set[str] = set()
    for group in find_exact_duplicates(sha_by_name):
        for name in group[1:]:
            drop.add(name)
            curation_log.append(f"REJECT (exact duplicate of {group[0]}): {name}")

    # 3) Near duplicates (keep first of each pair)
    dhash_by_name = {row["filename"]: dhash_file(row["_path"]) for row in accepted if row["filename"] not in drop}
    for a, b, distance in find_near_duplicates(dhash_by_name):
        if b not in drop and a not in drop:
            drop.add(b)
            curation_log.append(f"REJECT (near duplicate of {a}, dhash distance {distance}): {b}")

    accepted = [row for row in accepted if row["filename"] not in drop]
    for row in accepted:
        row["sha256"] = sha_by_name[row["filename"]]
    print(f"after dedupe: {len(accepted)}")

    # 4) IDs, captions, splits (deterministic ordering by style then filename)
    accepted.sort(key=lambda row: (row["style"], row["filename"]))
    manifest_rows: list[dict] = []
    for index, row in enumerate(accepted, start=1):
        item_id = f"DS-{index:04d}"
        manifest_rows.append(
            {
                "id": item_id,
                "filename": row["filename"],
                "style": row["style"],
                "caption": build_caption(row["style"], row["content_phrase"]),
                "source": row["source"],
                "author": row["author"],
                "licence": row["licence"],
                "collection_date": row["collection_date"],
                "permitted_use": row["permitted_use"],
                "width": row["width"],
                "height": row["height"],
                "sha256": row["sha256"],
                "split": assign_split(item_id),
                "notes": row["notes"],
            }
        )

    # 5) Schema validation gate
    errors = validate_manifest(manifest_rows)
    if errors:
        print("MANIFEST INVALID:")
        for error in errors:
            print(" -", error)
        sys.exit(1)

    MANIFEST_CSV.parent.mkdir(parents=True, exist_ok=True)
    save_manifest(manifest_rows, MANIFEST_CSV)
    print(f"manifest written: {MANIFEST_CSV} ({len(manifest_rows)} rows)")

    # 6) Statistics + contact sheets + curation log
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stats = compute_stats(manifest_rows)
    (EVIDENCE / "statistics.md").write_text(
        render_stats_markdown(stats, title="Dataset v1 statistics"), encoding="utf-8"
    )
    for style in sorted({row["style"] for row in manifest_rows}):
        paths = [RAW / style / row["filename"] for row in manifest_rows if row["style"] == style]
        sheet = make_contact_sheet(paths, EVIDENCE / f"contact-sheet-{style}.jpg")
        print(f"contact sheet: {sheet} ({sheet.stat().st_size // 1024} KB, {len(paths)} items)")

    per_style = Counter(row["style"] for row in manifest_rows)
    log_lines = [
        "# Dataset v1 curation log",
        "",
        f"Candidates collected: {len(candidates)}",
        f"Accepted into manifest: {len(manifest_rows)} ({dict(per_style)})",
        f"Rejected: {len(curation_log)}",
        "",
        "## Rejections",
        "",
    ] + [f"- {line}" for line in curation_log]
    (EVIDENCE / "curation-log.md").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"curation log: {len(curation_log)} rejections recorded")
    print("splits:", dict(Counter(row['split'] for row in manifest_rows)))


if __name__ == "__main__":
    main()
