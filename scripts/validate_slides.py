"""Validate the defence deck before it is built.

Read-only. Exits non-zero when a hard check fails.

The deck compresses a 91-page report onto 15 slides in a 20-minute slot, and compression
is exactly where an honest claim quietly becomes a marketable one. So this validator is
weighted differently from ``validate_report.py``: alongside the usual structural checks
it enforces a **denylist** of wordings this project has decided are wrong, and a
**requirement list** of concessions that must survive onto the slide that makes the
claim. A slide can fail here for saying too little as easily as for saying too much.

Timing is a hard check for the same reason. The first deck ran to 26 slides and roughly
26 minutes against a slot that turned out to be 20, and every structural check passed on
it, because nothing here knew what the slot was. A talk that overruns fails in front of
a jury rather than in a build log, so the budget now lives in ``deck.yaml`` and is
enforced (DR-017).

    HARD      placeholders - unknown or missing slide sources - invalid tier or
              layout - invalid EXP/DR/RQ identifiers - missing speaker notes -
              denylist hits - missing required concessions - a locked quantity
              typed as a literal instead of a fact placeholder - stale fact locks -
              estimated narration outside its band, or too little buffer

    ADVISORY  slides with an unusually long note

Usage::

    python scripts/validate_slides.py            # hard checks + advisories
    python scripts/validate_slides.py --strict   # advisories become failures too
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SLIDES_DIR = REPO_ROOT / "slides"
SOURCES_DIR = SLIDES_DIR / "sources"
DECK_FILE = SLIDES_DIR / "deck.yaml"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from report_facts import FactError, load_facts, resolve  # noqa: E402
from validate_report import FORBIDDEN as REPORT_FORBIDDEN  # noqa: E402

PLACEHOLDERS = re.compile(r"\b(TODO|TBD|FIXME|XXX|LOREM IPSUM)\b|\?\?\?", re.IGNORECASE)
EXP_ID = re.compile(r"\bEXP-(\d{3}[a-z]?(?:n\d+)?)\b")
DR_ID = re.compile(r"\bDR-(\d{3})\b")
RQ_ID = re.compile(r"\bRQ(\d{1,2})\b")
NOTES_HEADING = re.compile(r"^##\s+Speaker notes\s*$", re.MULTILINE)

# Wordings the deck must never use. The first group is inherited verbatim from the
# report so the two documents cannot disagree; the second is specific to the risks of
# a slide, where there is room for a claim but not for its qualification.
DECK_FORBIDDEN = [
    (
        r"\bone human rater\b",
        "'one human rater' is the pre-M9 wording. The corrected disclosure is: one human "
        "approver, AI-assisted visual analysis, no second independent human rater",
    ),
    (
        r"(?i)\b(deployed|hosted|running|live)\b[^.]{0,40}\b(in the cloud|on a public|publicly)\b",
        "the system is not deployed publicly; DR-014 selected local deployment",
    ),
    (
        r"(?i)\b(forbids|makes it impossible|can never be)\b[^.]{0,50}\b(host|hosted|hosting|internet|online)\b",
        "the margin bounds a second resident pipeline on the validated GPU - it does not "
        "make internet hosting impossible in every future architecture",
    ),
    (
        r"(?i)no assistant (ever )?(ran|validated|generated)",
        "an absolute the M9 gates removed; use the approved authority wording instead",
    ),
    (
        r"(?i)\bstate[- ]of[- ]the[- ]art\b|\bcutting[- ]edge\b|\bseamless\b|\brevolutionary\b|\bpowerful\b",
        "marketing register; the deck states measurements, not adjectives",
    ),
    (
        r"(?i)\bproduction[- ]ready\b|\bfully (tested|automated|reproducible)\b",
        "an unbounded completeness claim",
    ),
]

# Concessions that must appear on the slide that makes the claim. The deck is where a
# bounded finding is most likely to lose its bound, so the bound is checked positively
# rather than hoped for.
# Slide ids changed when the deck was cut from 26 to 15 for the 20-minute slot (DR-017).
# Three separate slides - retro-poster, rq4 and other-failures - merged into one `limits`
# slide, so all three of their concessions are now required on it. That is a stricter
# test than before, not a looser one: the merged slide has to carry every bound its three
# predecessors carried, and `test_every_required_check_names_a_real_slide` fails the suite
# if a future edit renames a slide out from under this list.
REQUIRED: list[tuple[str, str, str]] = [
    ("limits", r"(?i)partial", "the limits slide must carry retro-poster's PARTIAL PASS verdict"),
    ("limits", r"(?i)inconclusive", "the limits slide must say the image count is INCONCLUSIVE"),
    (
        "limits",
        r"(?i)no second independent human rater",
        "the limits slide must carry the corrected M9 evaluation disclosure",
    ),
    (
        "reproducibility",
        r"(?i)training[^.]{0,80}not\b|not[^.]{0,40}reproducible",
        "the reproducibility slide must state that training is NOT reproducible from seed",
    ),
    (
        "deployment",
        r"(?i)deliberate|chosen|not selected",
        "the deployment slide must show local deployment was chosen, not forgotten",
    ),
    (
        "base-model",
        r"(?i)better|superior|higher",
        "the base-model slide must concede SDXL scored better before saying it was rejected",
    ),
    (
        "lora",
        r"(?i)not\b[^.]{0,40}\b(best|most effective)|feasib",
        "the LoRA slide must claim feasibility, not superiority (DR-009)",
    ),
]


@dataclass
class Report:
    hard: list[str] = field(default_factory=list)
    advisory: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.hard.append(msg)

    def warn(self, msg: str) -> None:
        self.advisory.append(msg)


def load_sources() -> tuple[dict, dict[str, str]]:
    deck = yaml.safe_load(DECK_FILE.read_text(encoding="utf-8"))
    texts: dict[str, str] = {}
    for entry in deck["slides"]:
        path = SOURCES_DIR / entry["file"]
        if path.exists():
            texts[entry["file"]] = path.read_text(encoding="utf-8")
    return deck, texts


def check_structure(deck: dict, texts: dict[str, str], report: Report) -> None:
    layouts = set(deck["layouts"])
    seen_n, seen_id = set(), set()
    for entry in deck["slides"]:
        where = entry["file"]
        if entry["tier"] not in {"core", "supporting"}:
            report.fail(f"{where}: tier must be 'core' or 'supporting', got {entry['tier']!r}")
        if entry["layout"] not in layouts:
            report.fail(f"{where}: unknown layout {entry['layout']!r}")
        if entry["n"] in seen_n:
            report.fail(f"{where}: duplicate slide number {entry['n']}")
        if entry["id"] in seen_id:
            report.fail(f"{where}: duplicate slide id {entry['id']!r}")
        seen_n.add(entry["n"])
        seen_id.add(entry["id"])
        if where not in texts:
            report.fail(f"{where}: declared in deck.yaml but not authored")
        elif not NOTES_HEADING.search(texts[where]):
            report.fail(f"{where}: no '## Speaker notes' section")

    expected = list(range(1, len(deck["slides"]) + 1))
    if sorted(seen_n) != expected:
        report.fail(f"slide numbers are not 1..{len(deck['slides'])}: {sorted(seen_n)}")


def check_placeholders(texts: dict[str, str], report: Report) -> None:
    for name, text in texts.items():
        for hit in set(PLACEHOLDERS.findall(text)):
            report.fail(f"{name}: placeholder {hit!r}")


def check_identifiers(texts: dict[str, str], report: Report) -> None:
    registry = REPO_ROOT / "experiments" / "registry.csv"
    known_exp = set()
    if registry.exists():
        known_exp = set(EXP_ID.findall(registry.read_text(encoding="utf-8")))
    known_dr = {p.name[3:6] for p in (REPO_ROOT / "docs" / "decisions").glob("DR-*.md")}

    for name, text in texts.items():
        for exp in set(EXP_ID.findall(text)):
            if known_exp and exp not in known_exp:
                report.fail(f"{name}: EXP-{exp} is not in the experiment registry")
        for dr in set(DR_ID.findall(text)):
            if dr not in known_dr:
                report.fail(f"{name}: DR-{dr} has no decision record")
        for rq in set(RQ_ID.findall(text)):
            if not 1 <= int(rq) <= 12:
                report.fail(f"{name}: RQ{rq} is outside RQ1-RQ12")


# Markup that only renders correctly under one declared layout. The CSS grid for a
# two-column slide is scoped to `.slide--split`, and the figure pair to
# `.slide--two-figures`, so authoring that markup under any other layout produces a
# slide that is valid HTML, passes every budget, and silently renders wrong - the
# figure stacks under the text instead of sitting beside it.
#
# Found on the `limits` slide during the 20-minute restructuring (DR-017): it was
# authored as two columns and declared as `bullets`, and nothing caught it. A layout
# name is a promise about the markup, so it is now checked.
LAYOUT_MARKUP = [
    (re.compile(r'class="col-(?:text|figure)"'), "split", "two-column markup"),
    (re.compile(r'class="figure-pair"'), "two-figures", "a figure pair"),
]


def check_layout_markup(deck: dict, texts: dict[str, str], report: Report) -> None:
    """A slide's markup must match the layout it declares."""
    for entry in deck["slides"]:
        text = texts.get(entry["file"])
        if not text:
            continue
        for pattern, required, what in LAYOUT_MARKUP:
            if pattern.search(text) and entry["layout"] != required:
                report.fail(
                    f"{entry['file']}: uses {what} but declares layout "
                    f"{entry['layout']!r}. That markup is styled only under "
                    f"'{required}', so the slide would render wrong while passing every "
                    "other check."
                )


def check_forbidden(texts: dict[str, str], report: Report) -> None:
    """Denylist hits fail the deck build.

    They are advisory in the report, where a human reads 91 pages anyway. Here they are
    hard: a slide is read for seconds, so a wrong word on one has a better chance of
    passing unchallenged than a wrong paragraph in a chapter.
    """
    for pattern, why in REPORT_FORBIDDEN + DECK_FORBIDDEN:
        for name, text in texts.items():
            for match in re.finditer(pattern, text):
                line = text[: match.start()].count("\n") + 1
                report.fail(f"{name}:{line}: {why} - found {match.group(0)!r}")


def check_required(deck: dict, texts: dict[str, str], report: Report) -> None:
    by_id = {e["id"]: e["file"] for e in deck["slides"]}
    for slide_id, pattern, why in REQUIRED:
        name = by_id.get(slide_id)
        if name is None:
            report.fail(f"required check names slide id {slide_id!r}, which is not in deck.yaml")
            continue
        if name not in texts:
            continue  # not yet authored; check_structure already reported it
        if not re.search(pattern, texts[name]):
            report.fail(f"{name}: {why}")


ATTRIBUTE = re.compile(r"""[\w:.-]+=(?:"[^"]*"|'[^']*')""")


def check_literal_facts(texts: dict[str, str], report: Report) -> None:
    """A locked quantity must be a placeholder, never a typed literal.

    Two exclusions, both of which exist because a check that cries wolf gets ignored,
    and an ignored check is worse than none:

    - **HTML and SVG attribute values are stripped first.** An inline diagram places
      its labels at coordinates like ``y="148"``, and 148 is also the dataset size.
      Attributes are markup, not prose. Text *content* inside an ``<svg>`` is still
      checked, because a diagram label stating a measured value is exactly as capable
      of going stale as a sentence is.
    - **Only values of three characters or more are checked.** Two-character values
      produce real false positives - 16 matches the ``16:9`` the deck legitimately
      discusses.
    """
    try:
        facts = load_facts()
    except Exception as exc:  # noqa: BLE001
        report.fail(f"could not load fact declarations: {exc}")
        return

    for fact in facts:
        literal = str(fact.value)
        if len(literal) < 3:
            continue
        pattern = re.compile(rf"(?<![\w.]){re.escape(literal)}(?![\w.])")
        for name, text in texts.items():
            # Blank out attribute values, preserving offsets so line numbers stay true.
            prose = ATTRIBUTE.sub(lambda m: " " * len(m.group(0)), text)
            for match in pattern.finditer(prose):
                line = text[: match.start()].count("\n") + 1
                report.fail(
                    f"{name}:{line}: {literal!r} is typed as a literal. Write "
                    f"{{{{ facts.{fact.key} }}}} instead, so it cannot go stale."
                )


def check_facts(report: Report) -> None:
    try:
        resolve()
    except FactError as exc:
        report.fail(f"fact locks failed:\n{exc}")


def note_seconds(deck: dict, texts: dict[str, str]) -> dict[str, float]:
    """Estimated spoken seconds per slide file, from its speaker note's word count."""
    wpm = deck["timing"]["words_per_minute"]
    out: dict[str, float] = {}
    for entry in deck["slides"]:
        text = texts.get(entry["file"])
        if not text:
            continue
        parts = NOTES_HEADING.split(text)
        if len(parts) != 2:
            continue
        out[entry["file"]] = len(parts[1].split()) / wpm * 60
    return out


def check_notes_length(deck: dict, texts: dict[str, str], report: Report) -> None:
    """Advisory per-slide ceiling. The total below is what actually binds.

    The layout budgets stop a slide overflowing in space; this stops one slide
    overflowing in time. The demo slide is exempt - its note is a set of directions
    rather than a script, and the demo is timed separately.
    """
    ceiling = deck["timing"]["note_ceiling_seconds"]
    seconds = note_seconds(deck, texts)
    for entry in deck["slides"]:
        if entry["layout"] == "demo" or entry["file"] not in seconds:
            continue
        value = seconds[entry["file"]]
        if value > ceiling:
            report.warn(
                f"{entry['file']}: note is ~{value:.0f}s spoken, over the {ceiling}s "
                "ceiling. Trim it, or move the background into "
                "docs/presentation/jury-questions.md where it is available if asked."
            )


def check_timing(deck: dict, texts: dict[str, str], report: Report) -> None:
    """The whole talk must fit the slot. HARD, in both directions.

    This check exists because the first deck did not fit and nothing said so. It was
    built to 26 slides and ~26 minutes of narration while no authoritative duration was
    recorded anywhere in the repository, and every structural check passed on it. A deck
    that overruns its slot is as broken as one whose text is clipped - it just fails in
    front of a jury instead of in a build log.

    Over the maximum is an overrun. UNDER the minimum fails too: it means the estimate
    has drifted far enough from the design that the buffer is no longer the one that was
    reasoned about, and in practice it means a note was gutted rather than deliberately
    cut. Both directions are a signal to re-derive the budget, not to nudge a bound.

    The demo is never counted as zero. Its note is directions, so the demo slide is
    excluded from the word-count total and its two real costs - the spoken handoff and
    the demo itself - are declared in deck.yaml instead.
    """
    timing = deck["timing"]
    seconds = note_seconds(deck, texts)
    if len(seconds) != len(deck["slides"]):
        return  # slides missing; check_structure has already reported it

    spoken = sum(
        seconds[entry["file"]] for entry in deck["slides"] if entry["layout"] != "demo"
    )
    narration = spoken + timing["demo_handoff_seconds"]
    combined = narration + timing["demo_target_seconds"]
    buffer = timing["total_budget_seconds"] - combined

    lo, hi = timing["narration_min_seconds"], timing["narration_max_seconds"]
    if not lo <= narration <= hi:
        report.fail(
            f"narration is ~{narration:.0f}s ({narration / 60:.1f} min), outside the "
            f"{lo}-{hi}s target. Restructure the deck - do not plan to speak faster, "
            "and do not widen the band to fit the notes."
        )
    if buffer < timing["min_buffer_seconds"]:
        report.fail(
            f"buffer is ~{buffer:.0f}s against a {timing['min_buffer_seconds']}s minimum. "
            f"narration {narration:.0f}s + demo {timing['demo_target_seconds']}s exceeds "
            f"the {timing['total_budget_seconds']}s slot."
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="advisories fail too")
    args = parser.parse_args(argv)

    if not DECK_FILE.exists():
        print(f"FAIL: {DECK_FILE} is missing", file=sys.stderr)
        return 1

    deck, texts = load_sources()
    report = Report()

    check_structure(deck, texts, report)
    check_layout_markup(deck, texts, report)
    check_placeholders(texts, report)
    check_identifiers(texts, report)
    check_forbidden(texts, report)
    check_required(deck, texts, report)
    check_literal_facts(texts, report)
    check_facts(report)
    check_notes_length(deck, texts, report)
    check_timing(deck, texts, report)

    for msg in report.hard:
        print(f"HARD     {msg}")
    for msg in report.advisory:
        print(f"ADVISORY {msg}")

    print()
    print(f"slides authored : {len(texts)} of {len(deck['slides'])}")
    print(f"hard failures   : {len(report.hard)}")
    print(f"advisories      : {len(report.advisory)}")

    if report.hard:
        return 1
    if args.strict and report.advisory:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
