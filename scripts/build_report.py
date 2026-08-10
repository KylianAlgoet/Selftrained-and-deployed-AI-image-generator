"""Build the DeckForge AI research report: Markdown -> HTML -> PDF.

The pipeline and the reasons for it are recorded in DR-015. In short: this machine
has no document toolchain (pandoc, LaTeX, wkhtmltopdf, WeasyPrint and LibreOffice
are all absent) and a feature freeze forbids installing one, so the report is built
from packages already in the venv plus headless Chrome.

    report/sources/*.md
      -> markdown-it-py            (commonmark + table + strikethrough)
      -> Jinja2 template + print CSS
      -> deliverables/*.html       (intermediate, git-ignored, always rebuilt)
      -> headless Chrome --print-to-pdf
      -> deliverables/*.pdf        (tracked; the submitted deliverable)

Quantitative values are never typed into a chapter. They are written as
``{{ facts.key }}`` and substituted from report/facts.yaml, each one proved against
the evidence file that states it (see scripts/report_facts.py).

Usage::

    python scripts/build_report.py              # build HTML and PDF
    python scripts/build_report.py --no-pdf     # render HTML only (no Chrome needed)
    python scripts/build_report.py --strict     # require all 26 mandated sections
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markdown_it import MarkdownIt

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "report"
SOURCES_DIR = REPORT_DIR / "sources"
TEMPLATES_DIR = REPORT_DIR / "templates"
METADATA_FILE = REPORT_DIR / "metadata.yaml"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from report_facts import FactError, resolve as resolve_facts  # noqa: E402

FACT_PLACEHOLDER = re.compile(r"\{\{\s*facts\.([a-z0-9_]+)\s*\}\}")
FIGURE_REF = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


class BuildError(RuntimeError):
    """The build cannot honestly continue."""


@dataclass
class BuildResult:
    html_path: Path
    pdf_path: Path | None = None
    pdf_bytes: int = 0
    pdf_sha256: str = ""
    page_count: int | None = None
    page_count_note: str = ""
    sections_authored: int = 0
    sections_total: int = 0
    missing_sections: list[str] = field(default_factory=list)
    duration_s: float = 0.0


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------


def make_markdown() -> MarkdownIt:
    """CommonMark plus tables and strikethrough.

    Both are core markdown-it-py rules, so no plugin is needed - which matters,
    because mdit-py-plugins is not installed and the freeze forbids adding it.
    Autolinking stays off for the same reason: linkify-it-py is absent.
    """
    md = MarkdownIt("commonmark")
    md.enable(["table", "strikethrough"])
    md.options["html"] = True  # inline SVG figures and <div class="..."> wrappers
    return md


def substitute_facts(text: str, facts: dict[str, Any], where: str) -> str:
    """Replace {{ facts.key }} with proved values, refusing unknown keys."""
    unknown: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in facts:
            unknown.add(key)
            return match.group(0)
        value = facts[key]
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    result = FACT_PLACEHOLDER.sub(replace, text)
    if unknown:
        raise BuildError(
            f"{where}: unknown fact placeholder(s) {sorted(unknown)}. "
            "Add them to report/facts.yaml with their evidence, or fix the typo - "
            "do not type the number into the chapter."
        )
    return result


def check_figures(text: str, where: str) -> list[Path]:
    """Every referenced figure must exist on disk before the build proceeds."""
    found, missing = [], []
    for raw in FIGURE_REF.findall(text):
        if raw.startswith(("http://", "https://", "data:")):
            continue
        path = (REPO_ROOT / raw).resolve()
        (found if path.exists() else missing).append(path)
    if missing:
        raise BuildError(
            f"{where}: figure(s) referenced but not on disk: "
            + ", ".join(str(p.relative_to(REPO_ROOT)) for p in missing)
        )
    return found


def absolutise_figures(html: str) -> str:
    """Rewrite repo-relative image sources to file:// URLs Chrome can load.

    Figures are referenced in place under docs/evidence/, never copied, so a figure
    cannot drift from the evidence it documents.
    """

    def replace(match: re.Match[str]) -> str:
        src = match.group(1)
        if src.startswith(("http://", "https://", "data:", "file://")):
            return match.group(0)
        return f'src="{(REPO_ROOT / src).resolve().as_uri()}"'

    return re.sub(r'src="([^"]+)"', replace, html)


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------

HEADING = re.compile(r"^(#{1,3})\s+(.*)$", re.MULTILINE)


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_]+", "-", slug)


def build_toc(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A table of contents from the authored headings.

    No page numbers: Chrome's --print-to-pdf gives no reliable way to learn where a
    heading landed without a second pass, and an invented page number would be worse
    than none. Section numbers carry the navigation instead.
    """
    entries = []
    for section in sections:
        entries.append(
            {
                "level": 1,
                "number": section["n"],
                "title": section["title"],
                "anchor": section["id"],
            }
        )
        for hashes, title in HEADING.findall(section["markdown"]):
            if len(hashes) == 2:  # h2 within a section
                entries.append(
                    {
                        "level": 2,
                        "number": None,
                        "title": title.strip(),
                        "anchor": f"{section['id']}-{slugify(title)}",
                    }
                )
    return entries


def anchor_headings(html: str, section_id: str) -> str:
    """Give every h2 a stable id so the table of contents can link to it."""

    def replace(match: re.Match[str]) -> str:
        inner = match.group(1)
        text = re.sub(r"<[^>]+>", "", inner)
        return f'<h2 id="{section_id}-{slugify(text)}">{inner}</h2>'

    return re.sub(r"<h2>(.*?)</h2>", replace, html, flags=re.DOTALL)


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------


def find_chrome(candidates: list[str]) -> Path:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        found = shutil.which(name)
        if found:
            return Path(found)
    raise BuildError(
        "No Chrome or Edge binary found. Chrome is a build prerequisite (DR-015). "
        "Render the HTML with --no-pdf, or add a path to metadata.yaml."
    )


def print_to_pdf(chrome: Path, html_path: Path, pdf_path: Path, timeout: int = 180) -> None:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()

    command = [
        str(chrome),
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--virtual-time-budget=20000",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired as exc:
        raise BuildError(f"Chrome did not finish within {timeout}s") from exc

    if not pdf_path.exists():
        raise BuildError(
            "Chrome exited without writing a PDF.\n"
            f"  exit code: {completed.returncode}\n"
            f"  stderr: {completed.stderr.strip()[:500]}"
        )


def validate_pdf(pdf_path: Path) -> tuple[int, str, int | None, str]:
    """Structural validation, plus a page count only when it can be trusted.

    Structural checks are non-negotiable and always run. The page count is optional
    build metadata: no reliable PDF reader is installed (pypdf, PyPDF2, PyMuPDF,
    pdfminer, pikepdf and pdfinfo are all absent), and a regex over /Type /Page is
    not a general PDF parser - object streams and compression defeat it. So a count
    is reported only when two independent readings agree AND the file contains no
    object streams; otherwise it is reported as not measured and a human reads it
    off the PDF at the visual gate.
    """
    data = pdf_path.read_bytes()
    if not data:
        raise BuildError(f"{pdf_path} is empty")
    if not data.startswith(b"%PDF-"):
        raise BuildError(f"{pdf_path} does not start with %PDF-")
    if not data.rstrip().endswith(b"%%EOF"):
        raise BuildError(f"{pdf_path} does not end with %%EOF")

    digest = hashlib.sha256(data).hexdigest()

    page_count: int | None = None
    note = ""
    if b"/ObjStm" in data:
        note = "not measured - the PDF uses object streams, which a regex cannot parse"
    else:
        by_type = len(re.findall(rb"/Type\s*/Page[^s]", data))
        counts = [int(m) for m in re.findall(rb"/Count\s+(\d+)", data)]
        by_tree = max(counts) if counts else None
        if by_tree is not None and by_type and by_tree == by_type:
            page_count = by_tree
            note = "heuristic: page-tree /Count agrees with the /Type /Page object count"
        else:
            note = (
                f"not measured - readings disagree (/Count={by_tree}, "
                f"/Type /Page={by_type or 0})"
            )

    return len(data), digest, page_count, note


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------


def build(strict: bool = False, make_pdf: bool = True) -> BuildResult:
    started = time.time()

    if not METADATA_FILE.exists():
        raise BuildError(f"{METADATA_FILE} is missing")
    metadata = yaml.safe_load(METADATA_FILE.read_text(encoding="utf-8"))

    try:
        facts = resolve_facts()
    except FactError as exc:
        raise BuildError(f"fact locks failed, so the report cannot be trusted:\n{exc}") from exc

    md = make_markdown()

    def render(entry: dict[str, Any]) -> dict[str, Any] | None:
        path = SOURCES_DIR / entry["file"]
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        text = substitute_facts(text, facts, entry["file"])
        check_figures(text, entry["file"])
        html = md.render(text)
        html = anchor_headings(html, entry["id"])
        return {**entry, "markdown": text, "html": html}

    front = [r for r in (render(e) for e in metadata.get("front_matter", [])) if r]

    declared = metadata["sections"]
    rendered = [(e, render(e)) for e in declared]
    sections = [r for _, r in rendered if r]
    missing = [e["file"] for e, r in rendered if r is None]

    if strict and missing:
        raise BuildError(
            f"--strict: {len(missing)} of {len(declared)} mandated sections are not "
            f"authored: {missing}"
        )

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        undefined=StrictUndefined,
        autoescape=False,
    )
    css = (TEMPLATES_DIR / "report.css").read_text(encoding="utf-8")

    html = env.get_template("report.html.j2").render(
        document=metadata["document"],
        css=css,
        front_matter=front,
        sections=sections,
        toc=build_toc(sections),
        facts=facts,
        build_commit=git_head(),
        built_on=time.strftime("%Y-%m-%d"),
        authored=len(sections),
        total=len(declared),
    )
    html = absolutise_figures(html)

    html_path = REPO_ROOT / metadata["build"]["output_html"]
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")

    result = BuildResult(
        html_path=html_path,
        sections_authored=len(sections),
        sections_total=len(declared),
        missing_sections=missing,
    )

    if make_pdf:
        chrome = find_chrome(metadata["build"]["chrome_candidates"])
        pdf_path = REPO_ROOT / metadata["build"]["output_pdf"]
        print_to_pdf(chrome, html_path, pdf_path)
        size, digest, pages, note = validate_pdf(pdf_path)
        result.pdf_path = pdf_path
        result.pdf_bytes = size
        result.pdf_sha256 = digest
        result.page_count = pages
        result.page_count_note = note

    result.duration_s = time.time() - started
    return result


def git_head() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:  # noqa: BLE001 - a missing git is not a build failure
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-pdf", action="store_true", help="render HTML only")
    parser.add_argument(
        "--strict", action="store_true", help="require all mandated sections"
    )
    args = parser.parse_args(argv)

    try:
        result = build(strict=args.strict, make_pdf=not args.no_pdf)
    except BuildError as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"sections authored : {result.sections_authored} of {result.sections_total}")
    if result.missing_sections:
        print(f"not yet authored  : {len(result.missing_sections)} section(s)")
    print(f"html              : {result.html_path}")
    if result.pdf_path:
        print(f"pdf               : {result.pdf_path}")
        print(f"bytes             : {result.pdf_bytes:,}")
        print(f"sha256            : {result.pdf_sha256}")
        pages = result.page_count if result.page_count is not None else "not measured"
        print(f"pages             : {pages}  ({result.page_count_note})")
    print(f"commit            : {git_head()}")
    print(f"build time        : {result.duration_s:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
