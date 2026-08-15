"""M11 B7 - PDF audit of every deliverable intended for submission.

Validates the three tracked PDFs without adding a dependency: the PDF structure is
parsed directly, and page text is extracted from the uncompressed content streams.

Checks per file: opens and parses; page count; page geometry; per-page text volume
(a blank or near-blank page is a defect); raw-markup leakage; image XObject presence;
and font embedding.

Run:  .venv\\Scripts\\python.exe docs\\evidence\\M11\\audit_pdfs.py
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_text import page_texts  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
DELIVERABLES = ROOT / "deliverables"

TARGETS = [
    ("research report", "DeckForge-AI-research-report.pdf", True),
    ("presentation", "DeckForge-AI-presentation.pdf", True),
    # The notes handout is deliberately text-only: it is the narration, not slides.
    ("speaker notes", "DeckForge-AI-presentation-notes.pdf", False),
]

# Markup that must never reach a rendered page. Matched against the whitespace-
# stripped text: the PDFs position every glyph individually, so the extracted
# string has spaces between letters and a literal "{{facts.x}}" would never match
# with its spaces intact.
RAW_MARKUP = [
    (r"\{\{", "unresolved {{fact}} placeholder"),
    (r"<figure|</figure|<div|</div|<span|<img|<table>", "raw HTML tag"),
    (r"&amp;|&lt;|&gt;|&nbsp;|&quot;", "unescaped HTML entity"),
]

# DELIBERATELY NOT CHECKED on the squeezed text, and the reason is worth keeping:
# every one of these produced only false positives on this corpus, because
# removing the spaces creates the pattern out of ordinary prose.
#
#   `](`   -> the RENDERED citation "[18] (DR-002)" squeezes to "[18](DR-002)"
#   `**`   -> "/api/**", a real glob in the Playwright section
#   todo   -> "confined *to do*cumentation", "people *to do*"
#   nan    -> "artwork *on an* interactive deck"
#
# A check that cannot separate its target from ordinary text is not a weak check,
# it is a misleading one. TODO/TBD/FIXME are already HARD failures in
# scripts/validate_report.py, where they are matched against the source with its
# whitespace intact - which is the level that can actually see them.

failures: list[str] = []
results: dict[str, dict] = {}


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"    [{'PASS' if ok else 'FAIL'}] {label}{(' - ' + detail) if detail else ''}")
    if not ok:
        failures.append(f"{label}{(' - ' + detail) if detail else ''}")
    return ok


def squeeze(text: str) -> str:
    """Drop every space: the generators kern glyph by glyph, so extracted words
    arrive as 'D e c k F o r g e'. Markup is detected on the squeezed form."""
    return re.sub(r"\s+", "", text)


print("=== B7 PDF AUDIT ===\n")

for label, name, expects_images in TARGETS:
    path = DELIVERABLES / name
    print(f"--- {label}: {name} ---")
    if not path.exists():
        check(f"{label} exists", False, f"{path} not found")
        continue

    raw = path.read_bytes()
    size = len(raw)
    sha = hashlib.sha256(raw).hexdigest()
    print(f"    bytes  : {size:,}")
    print(f"    sha256 : {sha}")

    check("starts with a PDF header", raw[:5] == b"%PDF-", raw[:8].decode("latin-1", "replace"))
    check("ends with EOF marker", b"%%EOF" in raw[-1024:])

    # Page count from the page-tree /Count, cross-checked against /Type /Page objects.
    counts = [int(c) for c in re.findall(rb"/Type\s*/Pages[^>]*?/Count\s+(\d+)", raw, re.S)]
    page_objs = len(re.findall(rb"/Type\s*/Page[^s]", raw))
    pages = max(counts) if counts else page_objs
    print(f"    pages  : {pages}  (/Type /Page objects: {page_objs})")
    check("page tree and page objects agree", pages == page_objs, f"{pages} vs {page_objs}")

    # Geometry
    boxes = {tuple(round(float(v), 1) for v in m)
             for m in re.findall(rb"/MediaBox\s*\[\s*([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)\s*\]", raw)}
    print(f"    media boxes: {sorted(boxes)}")
    check("one uniform page geometry", len(boxes) == 1, f"{len(boxes)} distinct MediaBox values")

    # Fonts and images
    fonts = set(re.findall(rb"/BaseFont\s*/([A-Za-z0-9+#-]+)", raw))
    embedded = len(re.findall(rb"/FontFile[23]?\b", raw))
    images = len(re.findall(rb"/Subtype\s*/Image", raw))
    print(f"    fonts  : {len(fonts)} face(s), {embedded} embedded font programme(s)")
    print(f"    images : {images} image XObject(s)")
    check("at least one font is embedded", embedded > 0, "no /FontFile - text may not render portably")
    if expects_images:
        check("document contains images", images > 0, "no image XObjects found")
    else:
        print("    [note] text-only by design - the notes handout carries no figures")

    # Text per page, decoded through each font's ToUnicode CMap.
    texts = page_texts(raw)
    squeezed = [squeeze(t) for t in texts]
    lengths = [len(s) for s in squeezed]
    print(f"    pages with recovered text: {len(texts)}")

    if not texts or not any(lengths):
        check("text decoded from the content streams", False,
              "no text decoded - EVERY text check below would pass vacuously")
        results[label] = {"name": name, "bytes": size, "sha256": sha, "pages": pages, "text": ""}
        print()
        continue

    print(f"    glyphs per page: min={min(lengths)} median={sorted(lengths)[len(lengths)//2]} max={max(lengths)}")
    check("text decoded from every page", len(texts) == pages, f"{len(texts)} of {pages}")

    near_blank = [i + 1 for i, n in enumerate(lengths) if n < 50]
    check("no blank or near-blank page", not near_blank,
          f"{len(near_blank)} page(s) under 50 glyphs: {near_blank[:8]}")

    joined = "\n".join(squeezed)
    for pattern, why in RAW_MARKUP:
        hits = re.findall(pattern, joined, re.I)
        check(f"no {why}", not hits, f"{len(hits)} hit(s), e.g. {hits[:3]}")

    results[label] = {
        "name": name, "bytes": size, "sha256": sha, "pages": pages,
        "boxes": sorted(boxes), "images": images, "text": joined,
        "pretty": "\n".join(texts),
    }
    print()

# Cross-file checks
print("--- cross-file ---")
if "presentation" in results and "speaker notes" in results:
    d, n = results["presentation"]["pages"], results["speaker notes"]["pages"]
    check("notes cover the deck (one page per slide, plus a cover)", n in (d, d + 1),
          f"deck {d} pages vs notes {n} pages")

# ---------------------------------------------------------------------------
# The hard factual locks, checked against what the PDFs actually SAY.
# Each entry: (must-appear regex, must-NOT-appear regex or None, description)
# Matched on the squeezed text, so patterns carry no spaces.
# ---------------------------------------------------------------------------
LOCKS = [
    (r"8187\.?5", None, "device total 8187.5 MiB is stated"),
    # Rendered as "200.0" in the report and "200" on the slide - both are the
    # same fact-locked value, so the check accepts either form.
    (r"200(\.0)?MiB", None, "worst spare 200 MiB is stated"),
    (None, r"3043\.?77", "the false 8187.5-5143.73 margin does NOT appear"),
    (r"(?i)partialpass", None, "retro-poster's PARTIAL PASS is stated"),
    (r"(?i)inconclusive", None, "the inconclusive RQ4 image-count result is stated"),
    (None, r"(?i)bothgates(were)?scoredblind|bothgatesblind",
     "the withdrawn 'both gates blind' claim does NOT appear"),
    # The phrase is permitted ONLY when a negation governs it. M9 and M10 both
    # required exactly this wording, so the check is that every occurrence is
    # negated - not that the words never appear.
    (None, r"(?i)(?<!not)(?<!never)(?<!isnot)(?<!nevercalled)comfortableheadroom",
     "'comfortable headroom' appears only under a negation"),
    # DR-009 selects LoRA on measured FEASIBILITY and explicitly does not claim
    # superiority over the methods that were screened but never run. The phrase is
    # therefore allowed only where a negation governs it, which is how both of the
    # report's occurrences read ("No claim is made that...", "It does not conclude
    # that..."). The lookbehind spans the negating clause.
    (None, r"(?i)(?<!noclaimismadethat)(?<!doesnotconcludethat)LoRAisthebest",
     "'LoRA is the best' appears only under a negation"),
    (None, r"(?i)SD1\.?5(is|was)better(quality|thanSDXL)",
     "SD 1.5 is never claimed to be better in quality"),
]

STALE_STATUS = [
    (r"(?i)inprogress\b", "'in progress' status language"),
    (r"(?i)notstarted\b", "'not started' status language"),
    (r"(?i)tobewritten|comingsoon|sectionpending", "unfinished-content language"),
    # `placeholder` is NOT listed: the report legitimately discusses placeholder
    # ASSETS as a lessons-learned finding and as EXP-035's subject.
]

for label in ("research report", "presentation"):
    if label not in results:
        continue
    text = results[label]["text"]
    print(f"\n--- {label}: factual locks and status language ---")
    for must, must_not, desc in LOCKS:
        if must is not None:
            check(desc, bool(re.search(must, text)), "expected string not found in the rendered text")
        else:
            hits = re.findall(must_not, text)
            check(desc, not hits, f"{len(hits)} occurrence(s): {hits[:3]}")
    for pattern, desc in STALE_STATUS:
        hits = re.findall(pattern, text)
        check(f"no {desc}", not hits, f"{len(hits)} occurrence(s)")

# The deck carries `worst_device_used_mib` because M10's correction required the
# margin's arithmetic to be checkable on the slide. The report does not state it,
# and does not need to: its memory table gives `peak allocated`, `peak device` and
# `spare` as three separate columns across eight rows, and on every row where the
# device peak is known, spare = 8187.5 - peak device exactly. The relationship the
# deck got wrong is what the report's own table demonstrates.
print("\n--- the memory relationship, per document ---")
if "presentation" in results:
    check("the deck states worst device used (7987.5)",
          bool(re.search(r"7987\.?5", results["presentation"]["text"])),
          "the deck's margin arithmetic is not checkable without it")
if "research report" in results:
    t = results["research report"]["text"]
    check("the report states the one-shot device peak (7985.5)", bool(re.search(r"7985\.?5", t)))
    check("the report states peak allocated (5143.73)", bool(re.search(r"5143\.?73", t)))
    print("    [note] the report does not print 7987.5; its serving row shows '-' for peak device.")
    print("           Not a false claim - an omission where a fact-locked measurement now exists.")

print()
print("=== recorded state (measured now, not carried forward) ===")
for label, r in results.items():
    print(f"  {label:<16} {r['pages']:>3} pages · {r['bytes']:>9,} B · {r['sha256'][:16]}…")

print()
if failures:
    print(f"=== B7 RESULT: {len(failures)} FAILURE(S) ===")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("=== B7 RESULT: ALL CHECKS PASS ===")
