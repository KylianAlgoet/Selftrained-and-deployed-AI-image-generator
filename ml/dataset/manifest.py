"""Dataset manifest schema: load and validate `data/manifests/*.csv`.

Every row documents provenance and permitted use BEFORE an item may enter a
training split (project licensing policy, DR-006).
"""

import csv
from pathlib import Path

REQUIRED_FIELDS = [
    "id",
    "filename",
    "style",
    "caption",
    "source",
    "author",
    "licence",
    "collection_date",
    "permitted_use",
    "width",
    "height",
    "sha256",
    "split",
    "notes",
]

ALLOWED_LICENCES = {"public domain", "CC0", "project-original"}
ALLOWED_STYLES = {"retro-comic", "minimal-geometric", "ukiyo-e"}
ALLOWED_SPLITS = {"train", "val", "holdout"}
# `author` and `notes` may legitimately be empty (unknown author etc.).
OPTIONAL_EMPTY_FIELDS = {"author", "notes"}


def load_manifest(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def save_manifest(rows: list[dict[str, str]], path: str | Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in REQUIRED_FIELDS})


def validate_manifest(rows: list[dict[str, str]]) -> list[str]:
    """Return a list of human-readable schema violations (empty = valid)."""
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_shas: set[str] = set()

    for index, row in enumerate(rows):
        label = row.get("id") or f"row {index + 1}"
        missing = [
            field
            for field in REQUIRED_FIELDS
            if field not in OPTIONAL_EMPTY_FIELDS and not (row.get(field) or "").strip()
        ]
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")
            continue
        if row["licence"] not in ALLOWED_LICENCES:
            errors.append(f"{label}: licence {row['licence']!r} not in allowlist")
        if row["style"] not in ALLOWED_STYLES:
            errors.append(f"{label}: style {row['style']!r} not in allowed styles")
        if row["split"] not in ALLOWED_SPLITS:
            errors.append(f"{label}: split {row['split']!r} invalid")
        if not row["width"].isdigit() or not row["height"].isdigit():
            errors.append(f"{label}: width/height must be integers")
        if row["id"] in seen_ids:
            errors.append(f"{label}: duplicate id")
        seen_ids.add(row["id"])
        if row["sha256"] in seen_shas:
            errors.append(f"{label}: duplicate sha256 (exact duplicate image)")
        seen_shas.add(row["sha256"])

    return errors
