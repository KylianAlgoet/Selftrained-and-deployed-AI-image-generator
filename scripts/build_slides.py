"""Build the DeckForge AI defence deck: Markdown -> HTML -> PDF.

DR-016 extends the report pipeline of DR-015 rather than introducing a second one, so
this module deliberately imports its stages from ``build_report`` instead of copying
them. The machine still has no document toolchain and the feature freeze still forbids
installing one, so the chain is unchanged:

    slides/sources/*.md
      -> markdown-it-py            (commonmark + table + strikethrough)
      -> Jinja2 template + print CSS
      -> deliverables/*.html       (intermediate, git-ignored, always rebuilt)
      -> headless Chrome --print-to-pdf
      -> deliverables/*.pdf

Two PDFs come out of one set of sources:

    DeckForge-AI-presentation.pdf         16:9 slides, speaker notes EXCLUDED
    DeckForge-AI-presentation-notes.pdf   A4 handout, one page per slide, notes INCLUDED

Each source file holds the slide body and, under a ``## Speaker notes`` heading, the
note for that slide. One file per slide means a note cannot drift away from the slide
it belongs to.

There is no ``slides/facts.yaml``. Quantitative values resolve from the report's
``report/facts.yaml`` through ``report_facts.resolve()``, so a number corrected in the
report is corrected on the slide by the same edit.

Usage::

    python scripts/build_slides.py              # build both HTML and both PDFs
    python scripts/build_slides.py --no-pdf     # render HTML only (no Chrome needed)
    python scripts/build_slides.py --strict     # require every declared slide to exist
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

REPO_ROOT = Path(__file__).resolve().parent.parent
SLIDES_DIR = REPO_ROOT / "slides"
SOURCES_DIR = SLIDES_DIR / "sources"
TEMPLATES_DIR = SLIDES_DIR / "templates"
DECK_FILE = SLIDES_DIR / "deck.yaml"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from build_report import (  # noqa: E402
    BuildError,
    absolutise_figures,
    check_figures,
    find_chrome,
    git_head,
    make_markdown,
    print_to_pdf,
    substitute_facts,
    validate_pdf,
)
from report_facts import FactError, resolve as resolve_facts  # noqa: E402

NOTES_HEADING = re.compile(r"^##\s+Speaker notes\s*$", re.MULTILINE)
TAG = re.compile(r"<[^>]+>")
# Excluded from the text budget, for two different reasons.
#
# Captions and evidence pointers are set deliberately small and are there to be pointed
# at, not read aloud. Counting them would penalise the honest habit of naming the
# evidence file under every figure.
#
# Inline SVG is excluded on a stronger argument: the budget is a proxy for reflow
# overflow, and SVG cannot reflow. Its labels are placed at fixed coordinates inside a
# viewBox that scales to the space available, so a diagram gets smaller rather than
# taller. Whether it is still legible is a question for the human visual gate, which is
# the only thing that can answer it anyway.
BUDGET_EXEMPT = re.compile(
    r"<figcaption\b.*?</figcaption>"
    r"|<p class=\"source\">.*?</p>"
    r"|<div class=\"source\">.*?</div>"
    r"|<svg\b.*?</svg>",
    re.DOTALL,
)


@dataclass
class SlideResult:
    n: int
    id: str
    title: str
    tier: str
    layout: str
    words: int
    seconds: int
    chars: int
    bullets: int


@dataclass
class BuildResult:
    slides_html: Path
    notes_html: Path
    slides_pdf: Path | None = None
    notes_pdf: Path | None = None
    slides_pdf_bytes: int = 0
    slides_pdf_sha256: str = ""
    page_count: int | None = None
    page_count_note: str = ""
    aspect: str = ""
    slides: list[SlideResult] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    total_seconds: int = 0
    duration_s: float = 0.0


# --------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------


def split_notes(text: str, where: str) -> tuple[str, str]:
    """Separate the visible slide body from its speaker note.

    A slide with no note is a build failure rather than a warning. A note is not
    decoration here: the deck is deliberately sparse, so a slide without one is a
    slide whose argument exists nowhere.
    """
    parts = NOTES_HEADING.split(text)
    if len(parts) == 1:
        raise BuildError(
            f"{where}: no '## Speaker notes' section. Every slide needs one - the deck "
            "carries the claim and the note carries the argument."
        )
    if len(parts) > 2:
        raise BuildError(f"{where}: more than one '## Speaker notes' heading")
    body, notes = parts[0].strip(), parts[1].strip()
    if not body:
        raise BuildError(f"{where}: the slide body is empty")
    if not notes:
        raise BuildError(f"{where}: the speaker note is empty")
    return body, notes


def visible_text(html: str) -> str:
    """The body copy a reader in the room has to read, minus the budget-exempt parts."""
    stripped = BUDGET_EXEMPT.sub("", html)
    return re.sub(r"\s+", " ", TAG.sub(" ", stripped)).strip()


def check_budget(html: str, layout: str, budgets: dict[str, Any], where: str) -> tuple[int, int]:
    """Refuse a slide that will overflow its fixed height.

    This is the deterministic half of the overflow defence. A slide is a fixed
    190.5 mm box; content that does not fit is clipped by ``overflow: hidden`` rather
    than reflowed, so an over-full slide loses text silently. Catching it on the word
    count is crude but it is checkable, repeatable and it runs on every build. The
    human visual gate is the other half and neither replaces the other.
    """
    if layout not in budgets:
        raise BuildError(f"{where}: unknown layout {layout!r}")
    budget = budgets[layout]
    text = visible_text(html)
    chars = len(text)
    bullets = len(re.findall(r"<li\b", html))

    if chars > budget["max_chars"]:
        raise BuildError(
            f"{where}: {chars} visible characters exceeds the {layout} budget of "
            f"{budget['max_chars']}. Cut the slide or move the words into the speaker "
            "note - do not raise the budget to fit the text."
        )
    if bullets > budget["max_bullets"]:
        raise BuildError(
            f"{where}: {bullets} bullets exceeds the {layout} budget of "
            f"{budget['max_bullets']}."
        )
    return chars, bullets


# --------------------------------------------------------------------------
# PDF geometry
# --------------------------------------------------------------------------

MEDIABOX = re.compile(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]")


def read_aspect(pdf_path: Path) -> str:
    """Report the page geometry, or say it could not be read.

    Same honesty rule as the report's page counter: no PDF parser is installed, so this
    is a regex over the raw bytes. It succeeded on the DR-016 probe because Chrome wrote
    no object streams for a simple deck, and it may well fail once photographs are
    embedded. An unreadable box is reported as unreadable, never assumed correct - the
    visual gate is what actually confirms the shape.
    """
    data = pdf_path.read_bytes()
    boxes = {(m.group(1).decode(), m.group(2).decode()) for m in MEDIABOX.finditer(data)}
    if not boxes:
        return "not measured - no /MediaBox readable outside object streams"
    if len(boxes) > 1:
        return f"MIXED page sizes: {sorted(boxes)} - the deck must be one size throughout"
    width, height = next(iter(boxes))
    ratio = float(width) / float(height)
    verdict = "16:9" if abs(ratio - 16 / 9) < 0.005 else f"NOT 16:9 (ratio {ratio:.4f})"
    return f"{width} x {height} pt = {verdict}"


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------


def build(strict: bool = False, make_pdf: bool = True) -> BuildResult:
    started = time.time()

    if not DECK_FILE.exists():
        raise BuildError(f"{DECK_FILE} is missing")
    deck = yaml.safe_load(DECK_FILE.read_text(encoding="utf-8"))

    try:
        facts = resolve_facts()
    except FactError as exc:
        raise BuildError(f"fact locks failed, so the deck cannot be trusted:\n{exc}") from exc

    md = make_markdown()
    budgets = deck["layouts"]
    wpm = deck["timing"]["words_per_minute"]

    def render(entry: dict[str, Any]) -> dict[str, Any] | None:
        path = SOURCES_DIR / entry["file"]
        if not path.exists():
            return None
        where = entry["file"]
        text = substitute_facts(path.read_text(encoding="utf-8"), facts, where)
        body, notes = split_notes(text, where)
        check_figures(body, where)

        body_html = md.render(body)
        notes_html = md.render(notes)
        chars, bullets = check_budget(body_html, entry["layout"], budgets, where)

        words = len(visible_text(notes_html).split())
        return {
            **entry,
            "html": body_html,
            "notes_html": notes_html,
            "words": words,
            "seconds": round(words / wpm * 60),
            "chars": chars,
            "bullets": bullets,
        }

    declared = deck["slides"]
    rendered = [(e, render(e)) for e in declared]
    slides = [r for _, r in rendered if r]
    missing = [e["file"] for e, r in rendered if r is None]

    if strict and missing:
        raise BuildError(
            f"--strict: {len(missing)} of {len(declared)} declared slides are not "
            f"authored: {missing}"
        )
    if not slides:
        raise BuildError("no slide sources exist yet")

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR), undefined=StrictUndefined, autoescape=False
    )
    css = (TEMPLATES_DIR / "slides.css").read_text(encoding="utf-8")

    # The demo slide's note is a set of directions, not a script to read aloud, and the
    # demo is timed separately at its own target. Counting it in the slide total would
    # inflate the estimate and double-count the demo.
    total_seconds = sum(s["seconds"] for s in slides if s["layout"] != "demo")
    next_titles = {
        s["n"]: (slides[i + 1]["title"] if i + 1 < len(slides) else "— end of deck —")
        for i, s in enumerate(slides)
    }

    common = {
        "document": deck["document"],
        "css": css,
        "slides": slides,
        "build_commit": git_head(),
        "built_on": time.strftime("%Y-%m-%d"),
    }

    slides_html = absolutise_figures(env.get_template("slides.html.j2").render(**common))
    notes_html = absolutise_figures(
        env.get_template("notes.html.j2").render(
            **common,
            core_count=sum(1 for s in slides if s["tier"] == "core"),
            supporting_count=sum(1 for s in slides if s["tier"] == "supporting"),
            total_minutes=round(total_seconds / 60, 1),
            wpm=wpm,
            demo_minutes=deck["timing"]["demo_target_minutes"],
            next_titles=next_titles,
        )
    )

    slides_html_path = REPO_ROOT / deck["build"]["output_html"]
    notes_html_path = REPO_ROOT / deck["build"]["notes_html"]
    slides_html_path.parent.mkdir(parents=True, exist_ok=True)
    slides_html_path.write_text(slides_html, encoding="utf-8")
    notes_html_path.write_text(notes_html, encoding="utf-8")

    result = BuildResult(
        slides_html=slides_html_path,
        notes_html=notes_html_path,
        missing=missing,
        total_seconds=total_seconds,
        slides=[
            SlideResult(
                n=s["n"], id=s["id"], title=s["title"], tier=s["tier"], layout=s["layout"],
                words=s["words"], seconds=s["seconds"], chars=s["chars"], bullets=s["bullets"],
            )
            for s in slides
        ],
    )

    if make_pdf:
        chrome = find_chrome(deck["build"]["chrome_candidates"])
        slides_pdf = REPO_ROOT / deck["build"]["output_pdf"]
        notes_pdf = REPO_ROOT / deck["build"]["notes_pdf"]

        print_to_pdf(chrome, slides_html_path, slides_pdf)
        print_to_pdf(chrome, notes_html_path, notes_pdf)

        size, digest, pages, note = validate_pdf(slides_pdf)
        validate_pdf(notes_pdf)  # structural checks only; its page count is not a claim

        result.slides_pdf = slides_pdf
        result.notes_pdf = notes_pdf
        result.slides_pdf_bytes = size
        result.slides_pdf_sha256 = digest
        result.page_count = pages
        result.page_count_note = note
        result.aspect = read_aspect(slides_pdf)

        # One page per slide is the direct overflow test, and it is only a test when
        # the page count could actually be read.
        if pages is not None and pages != len(slides):
            raise BuildError(
                f"{pages} PDF pages for {len(slides)} slides - a slide has overflowed "
                "onto a second page. Cut its content; do not accept the extra page."
            )

    result.duration_s = time.time() - started
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-pdf", action="store_true", help="render HTML only")
    parser.add_argument("--strict", action="store_true", help="require every declared slide")
    args = parser.parse_args(argv)

    try:
        result = build(strict=args.strict, make_pdf=not args.no_pdf)
    except BuildError as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"slides authored   : {len(result.slides)} of {len(result.slides) + len(result.missing)}")
    if result.missing:
        print(f"not yet authored  : {len(result.missing)} slide(s)")
    print(f"slides html       : {result.slides_html}")
    print(f"notes html        : {result.notes_html}")
    if result.slides_pdf:
        print(f"slides pdf        : {result.slides_pdf}")
        print(f"notes pdf         : {result.notes_pdf}")
        print(f"bytes             : {result.slides_pdf_bytes:,}")
        print(f"sha256            : {result.slides_pdf_sha256}")
        pages = result.page_count if result.page_count is not None else "not measured"
        print(f"pages             : {pages}  ({result.page_count_note})")
        print(f"page geometry     : {result.aspect}")

    minutes = result.total_seconds / 60
    print(f"estimated speaking: {minutes:.1f} min, slides only (ESTIMATE from note word counts)")
    print(f"commit            : {git_head()}")
    print(f"build time        : {result.duration_s:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
