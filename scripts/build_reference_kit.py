"""Freeze the Prototype 2 reference-image kit and prove its provenance.

The kit is licence-safe by construction (plan section C.1): references come only
from dataset v1's HOLDOUT split and from the project's own seeded generator. No
new external image is introduced. Dataset v1 is READ, never written.

Using the holdout split is deliberate: those items are excluded from training by
construction, so when Prototypes 3-4 train LoRAs on the same data the Prototype 2
reference results remain uncontaminated.

What this script does, in order:
  1. loads `data/manifests/dataset-v1.csv` read-only;
  2. checks every dataset-derived reference resolves to a real manifest item in
     the holdout split, with matching SHA-256 and dimensions;
  3. regenerates R4 from seed 9001 and records its byte-exact SHA-256;
  4. copies the two project-original references into `data/references/` and
     verifies the copies are byte-identical;
  5. computes the img2img retained-area fraction at 512x512 and 512x1536;
  6. writes `docs/evidence/prototype-2/reference-kit.md` + `.csv` and a contact
     sheet of all five references.

It writes nothing outside `data/references/` and `docs/evidence/prototype-2/`.

Run:
    .venv/Scripts/python.exe scripts/build_reference_kit.py
"""

import csv
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from ml.dataset.contact_sheet import make_contact_sheet  # noqa: E402
from ml.dataset.generate_geometric import config_note, generate_geometric  # noqa: E402
from ml.dataset.hashing import sha256_file  # noqa: E402
from ml.dataset.manifest import load_manifest  # noqa: E402
from ml.inference.reference_schema import REFERENCES, ReferenceSpec, retained_area_fraction  # noqa: E402

MANIFEST = REPO / "data" / "manifests" / "dataset-v1.csv"
REFERENCE_DIR = REPO / "data" / "references"
EVIDENCE_DIR = REPO / "docs" / "evidence" / "prototype-2"

# The two output geometries M4 measures. 512x512 is comparable to every
# Prototype 1 baseline; 512x1536 is the DR-007 deck format.
TARGET_GEOMETRIES: tuple[tuple[int, int], ...] = ((512, 512), (512, 1536))

FIELDNAMES = [
    "id",
    "category",
    "origin",
    "dataset_item_id",
    "generator_seed",
    "licence",
    "permitted_use",
    "width",
    "height",
    "sha256",
    "source_path",
    "repo_path",
    "committed",
    "retained_area_512x512",
    "retained_area_512x1536",
    "manifest_check",
    "note",
]


def manifest_index() -> dict[str, dict[str, str]]:
    return {row["id"]: row for row in load_manifest(MANIFEST)}


def verify_against_manifest(spec: ReferenceSpec, index: dict[str, dict[str, str]]) -> tuple[str, str]:
    """Return (manifest_check, sha256). Discrepancies are reported, never silently
    tolerated - a reference whose provenance cannot be proven must not be used."""
    if spec.origin == "generated":
        return "n/a - generated from seed, not a manifest item", ""

    item = index.get(spec.dataset_item_id)
    if item is None:
        return f"FAIL - {spec.dataset_item_id} not present in the manifest", ""

    problems: list[str] = []
    if item["split"] != "holdout":
        problems.append(f"split is {item['split']!r}, expected 'holdout'")
    if (int(item["width"]), int(item["height"])) != (spec.width, spec.height):
        problems.append(f"manifest dimensions {item['width']}x{item['height']} != registry {spec.width}x{spec.height}")
    if item["licence"] != spec.licence:
        problems.append(f"manifest licence {item['licence']!r} != registry {spec.licence!r}")

    source = REPO / spec.source_path
    if not source.exists():
        problems.append(f"source file missing at {spec.source_path}")
        return "FAIL - " + "; ".join(problems), item["sha256"]

    actual = sha256_file(source)
    if actual != item["sha256"]:
        problems.append(f"file SHA-256 {actual[:16]}... != manifest {item['sha256'][:16]}...")

    if problems:
        return "FAIL - " + "; ".join(problems), actual
    return f"OK - {spec.dataset_item_id} holdout, SHA-256 matches manifest and file on disk", actual


def materialise(spec: ReferenceSpec) -> tuple[str, str]:
    """Ensure the file the runner reads exists. Returns (sha256, provenance_note)."""
    destination = REPO / spec.repo_path

    if spec.origin == "generated":
        destination.parent.mkdir(parents=True, exist_ok=True)
        config = generate_geometric(spec.generator_seed, destination)
        return sha256_file(destination), config_note(config)

    source = REPO / spec.source_path
    if destination != source:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        if sha256_file(destination) != sha256_file(source):
            raise RuntimeError(f"{spec.id}: committed copy is not byte-identical to its source")
    return sha256_file(destination), f"copied verbatim from {spec.source_path}"


def build_rows() -> list[dict]:
    index = manifest_index()
    rows: list[dict] = []
    for spec in REFERENCES.values():
        check, manifest_sha = verify_against_manifest(spec, index)
        actual_sha, provenance = materialise(spec)
        if manifest_sha and manifest_sha != actual_sha:
            check += " | WARNING: materialised file hash differs from manifest hash"
        rows.append(
            {
                "id": spec.id,
                "category": spec.category,
                "origin": spec.origin,
                "dataset_item_id": spec.dataset_item_id or "n/a",
                "generator_seed": "n/a" if spec.generator_seed is None else spec.generator_seed,
                "licence": spec.licence,
                "permitted_use": spec.permitted_use,
                "width": spec.width,
                "height": spec.height,
                "sha256": actual_sha,
                "source_path": spec.source_path or "n/a - generated",
                "repo_path": spec.repo_path,
                "committed": "yes" if spec.committed else "no",
                "retained_area_512x512": round(
                    retained_area_fraction(spec.width, spec.height, 512, 512), 4
                ),
                "retained_area_512x1536": round(
                    retained_area_fraction(spec.width, spec.height, 512, 1536), 4
                ),
                "manifest_check": check,
                "note": f"{spec.note} ({provenance})",
            }
        )
    return rows


def write_csv(rows: list[dict]) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / "reference-kit.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_markdown(rows: list[dict], sheet: Path | None) -> Path:
    lines = [
        "# Prototype 2 reference-image kit (frozen)",
        "",
        "Five references, frozen for every M4 experiment. Sourcing rule (plan section C.1):",
        "references come **only** from dataset v1's holdout split and from the project's own",
        "seeded generator. No new external image was introduced, and dataset v1 was read,",
        "never written.",
        "",
        "The holdout split is used deliberately: those items are excluded from training by",
        "construction, so when Prototypes 3-4 train LoRAs on the same data these reference",
        "results remain uncontaminated.",
        "",
        "## Provenance and licence",
        "",
        "| id | category | origin | item | licence | dimensions | SHA-256 | committed |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        item = row["dataset_item_id"] if row["origin"] != "generated" else f"seed {row['generator_seed']}"
        lines.append(
            f"| {row['id']} | {row['category']} | {row['origin']} | {item} | {row['licence']} | "
            f"{row['width']}x{row['height']} | `{row['sha256'][:16]}...` | {row['committed']} |"
        )

    lines += [
        "",
        "Full SHA-256 values are in [`reference-kit.csv`](reference-kit.csv).",
        "",
        "**Commit policy.** The two project-original references (R2, R4) are committed under",
        "`data/references/`: they are tiny, licence-clean, and byte-reproducible from a seed.",
        "The three externally sourced references (R1, R3, R5) are **not** committed, consistent",
        "with the existing \"raw images stay out of Git\" policy; their manifest ID plus SHA-256",
        "makes them re-derivable from `data/manifests/dataset-v1.csv`.",
        "",
        "## Integrity verification",
        "",
        "Each dataset-derived reference was checked against the manifest for split membership,",
        "dimensions, licence, and SHA-256 of the actual file on disk.",
        "",
        "| id | check |",
        "|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['id']} | {row['manifest_check']} |")

    lines += [
        "",
        "## img2img retained area after centre-crop",
        "",
        "img2img forces the reference into the output resolution, so part of every reference",
        "that does not already match the target aspect is discarded. This quantifies that cost",
        "instead of describing it. **IP-Adapter does not crop to the output geometry** - it",
        "passes the reference through a 224 px CLIP crop regardless of output size - so these",
        "fractions apply to the img2img arm only.",
        "",
        "| id | native | retained at 512x512 | retained at 512x1536 |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {row['width']}x{row['height']} | "
            f"{row['retained_area_512x512'] * 100:.0f} % | {row['retained_area_512x1536'] * 100:.0f} % |"
        )

    lines += [
        "",
        "## Correction made after inspecting the images",
        "",
        "All five references were opened and viewed before the condition table was written, rather",
        "than described from the plan text. One label did not survive that check:",
        "",
        "- The approved M4 plan describes condition **C5** as \"reference says cresting wave, prompt",
        "  says minimal geometric\". *Cresting wave* is the wording of prompt **P3-ukiyo**, not the",
        "  content of **R3**. R3 (`DS-0103`, `met-37129.jpg`) is a landscape ukiyo-e print of a seated",
        "  figure at a low desk in an interior. The conflict C5 tests is real and unchanged - a",
        "  figurative ukiyo-e scene against a minimal-geometric prompt - but it is now described",
        "  accurately, and C3 is labelled *style-matched on style, subject-mismatched* rather than",
        "  simply \"style-matched\".",
        "",
        "A second observation, recorded so it is not mistaken for a property only R5 has: **R1 is also",
        "a framed, text-dominated poster scan.** R5 remains the harder case because it adds landscape",
        "orientation, which the deck format cannot accommodate - but frame and typography transfer can",
        "and should be looked for in C1 as well as C6.",
        "",
        "## Roles",
        "",
    ]
    for row in rows:
        lines.append(f"- **{row['id']}** ({row['category']}): {row['note']}")

    lines += [
        "",
        "## Conditions built from this kit",
        "",
        "| condition | reference | prompt | purpose |",
        "|---|---|---|---|",
    ]
    from ml.inference.reference_schema import CONDITIONS

    for condition in CONDITIONS.values():
        lines.append(
            f"| {condition.id} | {condition.reference_id} | {condition.prompt_id} | {condition.purpose} |"
        )

    if sheet is not None:
        lines += [
            "",
            "## Contact sheet",
            "",
            f"![reference kit]({sheet.name})",
            "",
            "All five references at thumbnail size, so the kit is visible without the raw data.",
            "",
        ]

    path = EVIDENCE_DIR / "reference-kit.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def build_sheet(rows: list[dict]) -> Path | None:
    paths = [REPO / row["repo_path"] for row in rows]
    missing = [p for p in paths if not p.exists()]
    if missing:
        print(f"  cannot build contact sheet, missing: {[str(p) for p in missing]}")
        return None
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out = EVIDENCE_DIR / "reference-kit-sheet.jpg"
    make_contact_sheet(paths, out, thumb_size=256, columns=len(paths))
    return out


def main() -> int:
    if not MANIFEST.exists():
        print(f"manifest not found at {MANIFEST}", file=sys.stderr)
        return 1

    rows = build_rows()
    failures = [row for row in rows if row["manifest_check"].startswith("FAIL")]

    sheet = build_sheet(rows)
    csv_path = write_csv(rows)
    md_path = write_markdown(rows, sheet)

    for row in rows:
        print(f"  {row['id']}: {row['manifest_check']}")
    print(f"\nregistry csv .. {csv_path}")
    print(f"registry md ... {md_path}")
    if sheet is not None:
        print(f"contact sheet . {sheet} ({sheet.stat().st_size // 1024} KB)")

    if failures:
        print(f"\n{len(failures)} reference(s) FAILED provenance verification", file=sys.stderr)
        return 1
    print(f"\n{len(rows)} references verified against the manifest and materialised.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
