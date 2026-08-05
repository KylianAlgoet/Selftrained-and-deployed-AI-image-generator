"""Build the review-only Gate-2 ZIP.

Copies the Gate-2 handover, the blank scoring form and the labelled final contact
sheets into a git-ignored ZIP. Weights, checkpoints, cached latents and
full-resolution outputs are excluded by an extension allowlist, and the result is
re-verified against the archive's own name list rather than against intent.

Run:
    .venv/Scripts/python.exe scripts/build_p4_gate2_zip.py
"""

import hashlib
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

P4 = REPO / "docs" / "evidence" / "prototype-4"
OUT = REPO / "outputs" / "m6-gate-2-review-package.zip"

DOCS = [
    P4 / "GATE-2-handover.md",
    P4 / "gate-2-scoring-form.md",
    P4 / "full-run-validation.md",
]
# Only these extensions may ever enter. `.safetensors`, `.pt`, `.ckpt` and `.png`
# are therefore excluded structurally, not by remembering to leave them out.
ALLOWED_SUFFIXES = {".md", ".jpg"}
FORBIDDEN_SUBSTRINGS = ("safetensors", "checkpoint", "BLINDING-MAP", "latent")


def main() -> int:
    sheets = sorted((P4 / "final-sheets").glob("*.jpg"))
    missing = [d for d in DOCS if not d.is_file()]
    if missing:
        for d in missing:
            print(f"MISSING {d.relative_to(REPO)}")
        return 1
    if not sheets:
        print("no final sheets found")
        return 1

    members = [(d, d.name) for d in DOCS] + [(s, f"final-sheets/{s.name}") for s in sheets]

    for src, arc in members:
        if src.suffix.lower() not in ALLOWED_SUFFIXES:
            print(f"REFUSED (suffix): {arc}")
            return 1
        if any(bad in arc for bad in FORBIDDEN_SUBSTRINGS):
            print(f"REFUSED (deny-list): {arc}")
            return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src, arc in members:
            zf.write(src, arcname=arc)

    with zipfile.ZipFile(OUT) as zf:
        names = zf.namelist()
        if zf.testzip() is not None:
            print("CORRUPT archive")
            return 1
    for name in names:
        if Path(name).suffix.lower() not in ALLOWED_SUFFIXES:
            print(f"FAIL: {name} slipped in")
            return 1
        if any(bad in name for bad in FORBIDDEN_SUBSTRINGS):
            print(f"FAIL: {name} slipped in")
            return 1

    docs = [n for n in names if "/" not in n]
    sheet_names = [n for n in names if n.startswith("final-sheets/")]
    print(f"members : {len(names)}")
    print(f"  docs  : {len(docs)} ({', '.join(sorted(docs))})")
    print(f"  sheets: {len(sheet_names)}")
    print("weights / checkpoints / latents / full-resolution PNGs: ABSENT")
    print(f"size    : {OUT.stat().st_size / 1024:.0f} KB")
    print(f"sha256  : {hashlib.sha256(OUT.read_bytes()).hexdigest()}")
    print(f"path    : {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
