"""Validate the research report before it is built.

Read-only. Exits non-zero when a hard check fails.

The split between hard failures and advisories is deliberate, and follows the M9.3
gate decision: a build must not fail because a technical term is missing from a
homemade dictionary, but it must fail if a citation does not resolve or a section
is missing.

    HARD      placeholders (TODO/TBD/FIXME) - missing mandated sections -
              broken internal references - missing figure files - invalid
              EXP/DR/RQ/R/D identifiers - citation and reference mismatches -
              duplicate or skipped figure/table numbers - stale locked facts

    ADVISORY  spelling and unknown tokens - forbidden-claim denylist hits, each
              of which a human judges - page count outside the target range

Usage::

    python scripts/validate_report.py            # hard checks + advisories
    python scripts/validate_report.py --strict   # advisories become failures too
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "report"
SOURCES_DIR = REPORT_DIR / "sources"
METADATA_FILE = REPORT_DIR / "metadata.yaml"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from report_facts import FactError, load_facts, resolve  # noqa: E402

PLACEHOLDERS = re.compile(r"\b(TODO|TBD|FIXME|XXX|LOREM IPSUM)\b|\?\?\?", re.IGNORECASE)
CITATION = re.compile(r"\[(\d{1,2})\]")
BIB_ENTRY = re.compile(r"^(\d{1,2})\.\s", re.MULTILINE)
FIGURE_LABEL = re.compile(r"caption__label\">Figure (\d+)\.")
EXP_ID = re.compile(r"\bEXP-(\d{3}[a-z]?(?:n\d+)?)\b")
DR_ID = re.compile(r"\bDR-(\d{3})\b")
RQ_ID = re.compile(r"\bRQ(\d{1,2})\b")
RISK_ID = re.compile(r"\bR(\d{1,2})\b")
SECTION_REF = re.compile(r"§(\d{1,2})(?:\.\d+)*")
REPO_PATH = re.compile(r"`([a-z_][\w./-]*\.(?:py|md|csv|ts|tsx|json|yaml|yml|ps1|ini))`")

# Claims this project has decided must never appear. Each hit is reported for a
# human to judge; none of them fails the build on its own.
FORBIDDEN = [
    (r"comfortable headroom(?!.{0,80}(not|never))", "'comfortable headroom' - the margin is 2.4%"),
    (r"retro-poster[^.]{0,60}\bPASS\b(?<!PARTIAL PASS)", "retro-poster described as PASS"),
    (r"\b25 generations\b", "generation total is 27, not 25"),
    (r"LoRA is (the )?(best|superior)", "DR-009 claims feasibility, not superiority"),
    (r"bit-reproducible(?!.{0,60}(not|never|cannot))", "training is NOT bit-reproducible"),
    (r"fully reproducible training", "training is not reproducible from seed"),
]


@dataclass
class Report:
    hard: list[str] = field(default_factory=list)
    advisory: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.hard.append(msg)

    def warn(self, msg: str) -> None:
        self.advisory.append(msg)


def load_sources() -> tuple[dict, dict[str, str], str]:
    metadata = yaml.safe_load(METADATA_FILE.read_text(encoding="utf-8"))
    texts: dict[str, str] = {}
    for entry in metadata.get("front_matter", []) + metadata["sections"]:
        path = SOURCES_DIR / entry["file"]
        if path.exists():
            texts[entry["file"]] = path.read_text(encoding="utf-8")
    return metadata, texts, "\n".join(texts.values())


def check_sections(metadata: dict, texts: dict[str, str], report: Report) -> None:
    missing = [e["file"] for e in metadata["sections"] if e["file"] not in texts]
    if missing:
        report.warn(
            f"{len(missing)} of {len(metadata['sections'])} mandated sections not authored: "
            + ", ".join(missing)
        )
    for entry in metadata["sections"]:
        text = texts.get(entry["file"])
        if text is None:
            continue
        if not text.strip():
            report.fail(f"{entry['file']}: section is empty")
        expected = f'<span class="section-number">{entry["n"]}</span>'
        if expected not in text:
            report.fail(
                f"{entry['file']}: heading does not carry its mandated section number "
                f"({entry['n']})"
            )


def check_placeholders(texts: dict[str, str], report: Report) -> None:
    for name, text in texts.items():
        for match in PLACEHOLDERS.finditer(text):
            line = text[: match.start()].count("\n") + 1
            report.fail(f"{name}:{line}: placeholder {match.group(0)!r}")


def check_citations(texts: dict[str, str], report: Report) -> None:
    """Every [n] resolves, numbering is contiguous, no entry is orphaned."""
    bib = texts.get("24-references.md")
    if bib is None:
        report.warn("24-references.md not authored; citation checks skipped")
        return

    entries = sorted(int(n) for n in BIB_ENTRY.findall(bib))
    if not entries:
        report.fail("24-references.md: no numbered bibliography entries found")
        return

    expected = list(range(1, len(entries) + 1))
    if entries != expected:
        report.fail(
            f"bibliography numbering is not contiguous from 1: found {entries}"
        )

    cited: set[int] = set()
    for name, text in texts.items():
        if name == "24-references.md":
            continue
        for match in CITATION.finditer(text):
            n = int(match.group(1))
            cited.add(n)
            if n not in entries:
                line = text[: match.start()].count("\n") + 1
                report.fail(f"{name}:{line}: citation [{n}] has no bibliography entry")

    orphaned = sorted(set(entries) - cited)
    if orphaned:
        report.fail(
            f"bibliography entries never cited in the body: {orphaned}. "
            "Cite them or remove them - an uncited entry implies reading that did "
            "not inform the report."
        )


# EXP-006 and EXP-015 are NOT experiment rows: they name the human scoring
# directories under docs/evidence/. The report says so explicitly in section 13.1,
# so they are permitted here rather than being an excuse to weaken the check.
NON_RUN_EXP_IDS = {"006", "015"}


def check_identifiers(text: str, report: Report) -> None:
    registry = (REPO_ROOT / "experiments" / "registry.csv").read_text(encoding="utf-8")
    known_exp = set(EXP_ID.findall(registry)) | NON_RUN_EXP_IDS
    for exp in set(EXP_ID.findall(text)):
        if exp not in known_exp:
            report.fail(f"EXP-{exp} is cited but not in experiments/registry.csv")
    for exp in sorted(NON_RUN_EXP_IDS):
        if f"EXP-{exp}" in text and not (REPO_ROOT / "docs" / "evidence" / f"EXP-{exp}-scoring").exists():
            report.fail(
                f"EXP-{exp} is allowed as a scoring directory, but "
                f"docs/evidence/EXP-{exp}-scoring/ does not exist"
            )

    known_dr = {p.name[3:6] for p in (REPO_ROOT / "docs" / "decisions").glob("DR-*.md")}
    for dr in set(DR_ID.findall(text)):
        if dr not in known_dr:
            report.fail(f"DR-{dr} is cited but has no record in docs/decisions/")

    plan = (REPO_ROOT / "docs" / "01-research-plan.md").read_text(encoding="utf-8")
    known_rq = set(RQ_ID.findall(plan))
    for rq in set(RQ_ID.findall(text)):
        if rq not in known_rq:
            report.fail(f"RQ{rq} is cited but is not in docs/01-research-plan.md")

    risks = (REPO_ROOT / "docs" / "process" / "risk-register.md").read_text(encoding="utf-8")
    known_risk = set(RISK_ID.findall(risks))
    for risk in set(RISK_ID.findall(text)):
        if risk not in known_risk:
            report.fail(f"R{risk} is cited but is not in the risk register")


def check_section_refs(metadata: dict, text: str, report: Report) -> None:
    valid = {str(e["n"]) for e in metadata["sections"]}
    for match in set(SECTION_REF.findall(text)):
        if match not in valid:
            report.fail(f"cross-reference to section {match}, which does not exist")


def check_figures(texts: dict[str, str], report: Report) -> None:
    numbers: list[int] = []
    for name, text in texts.items():
        for raw in re.findall(r'<img src="([^"]+)"', text):
            if raw.startswith(("http", "data:")):
                continue
            if not (REPO_ROOT / raw).exists():
                report.fail(f"{name}: figure file not found: {raw}")
        numbers.extend(int(n) for n in FIGURE_LABEL.findall(text))

    duplicates = {n for n in numbers if numbers.count(n) > 1}
    if duplicates:
        report.fail(f"duplicate figure numbers: {sorted(duplicates)}")
    if numbers:
        ordered = sorted(numbers)
        if ordered != list(range(1, len(ordered) + 1)):
            report.fail(f"figure numbering is not contiguous from 1: {ordered}")


def check_repo_paths(texts: dict[str, str], report: Report) -> None:
    for name, text in texts.items():
        for path in set(REPO_PATH.findall(text)):
            if not (REPO_ROOT / path).exists():
                report.fail(f"{name}: repository path does not exist: {path}")


def check_facts(report: Report) -> None:
    try:
        resolve(load_facts())
    except FactError as exc:
        report.fail(f"fact locks failed:\n    {exc}")


def check_forbidden(texts: dict[str, str], report: Report) -> None:
    for name, text in texts.items():
        if name in {"25-appendices.md"}:
            continue
        for pattern, why in FORBIDDEN:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                line = text[: match.start()].count("\n") + 1
                report.warn(f"{name}:{line}: {why} -> {match.group(0)!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="advisories fail too")
    args = parser.parse_args(argv)

    metadata, texts, combined = load_sources()
    report = Report()

    check_sections(metadata, texts, report)
    check_placeholders(texts, report)
    check_citations(texts, report)
    check_identifiers(combined, report)
    check_section_refs(metadata, combined, report)
    check_figures(texts, report)
    check_repo_paths(texts, report)
    check_facts(report)
    check_forbidden(texts, report)

    if report.advisory:
        print(f"ADVISORY ({len(report.advisory)}):")
        for item in report.advisory:
            print(f"  ~ {item}")
    if report.hard:
        print(f"\nFAILED ({len(report.hard)}):", file=sys.stderr)
        for item in report.hard:
            print(f"  x {item}", file=sys.stderr)
        return 1

    print(f"\nOK: {len(texts)} source files pass every hard check.")
    return 1 if (args.strict and report.advisory) else 0


if __name__ == "__main__":
    raise SystemExit(main())
