"""Detect the short report build described in findings.md (F1).

The report build intermittently emits a PDF ~800 KB smaller at the same page count. M11 identified
the cause: Chrome rasterises the table-of-contents dot leaders (`.toc__dots`, a 1px dotted border)
into ~1.5 M individual 1x1 pixel fills, replicated into every page's content stream. In a short
build most of those fills are absent, so the leaders do not render.

Nothing else differs - text, fonts, images and page count are identical - so this is a cosmetic
check, not a content check. Content identity is evidenced separately in findings.md.

Usage:
    python docs/evidence/M11/check_report_leaders.py [path-to-pdf]

Exit code 0 if the build looks healthy, 1 if it looks short.
"""
from __future__ import annotations

import re
import sys
import zlib
from pathlib import Path

DEFAULT_PDF = Path("deliverables/DeckForge-AI-research-report.pdf")

# Measured 2026-08-15 by this script, on a healthy build (2,773,114 B) and a short build
# (1,971,967 B). These count 1x1 fills only; the totals for fills of every size are slightly
# higher (1,502,029 and 36,199) and are quoted in findings.md.
HEALTHY_FILLS = 1_500_559
SHORT_FILLS = 34_729
# Halfway between the two observations, rounded down - a build near either figure is unambiguous.
THRESHOLD = 750_000

OBJ = re.compile(rb"\n\d+ 0 obj(.*?)endobj", re.S)
FILL = re.compile(rb"1 1 re\nf\n")


def count_leader_fills(raw: bytes) -> int:
    """Count 1x1 px filled rectangles across every decompressible content stream."""
    total = 0
    for match in OBJ.finditer(raw):
        body = match.group(1)
        if b"stream" not in body:
            continue
        data = body.split(b"stream", 1)[1].lstrip(b"\r\n").rsplit(b"endstream", 1)[0]
        try:
            stream = zlib.decompress(data)
        except zlib.error:
            continue  # image data, font programs and other non-Flate streams
        total += len(FILL.findall(stream))
    return total


def main(argv: list[str]) -> int:
    pdf = Path(argv[1]) if len(argv) > 1 else DEFAULT_PDF
    if not pdf.is_file():
        print(f"FAIL  {pdf} does not exist")
        return 1

    raw = pdf.read_bytes()
    fills = count_leader_fills(raw)
    pages = len(re.findall(rb"/Type\s*/Page[^s]", raw))

    print(f"file       : {pdf}")
    print(f"bytes      : {len(raw):,}")
    print(f"pages      : {pages}")
    print(f"1x1 fills  : {fills:,}   (healthy ~{HEALTHY_FILLS:,}, short ~{SHORT_FILLS:,})")

    if fills < THRESHOLD:
        print()
        print("FAIL  this looks like a SHORT build - the TOC dot leaders are missing.")
        print("      Rebuild with `python scripts/build_report.py --strict` and check again.")
        print("      Text, figures and page count are NOT affected - see findings.md F1.")
        return 1

    print()
    print("PASS  the TOC dot leaders are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
