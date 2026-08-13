"""The defence deck must stay inside its box, and its guards must actually bite.

Two halves, following the pattern `test_report_facts.py` established:

1. The authored deck is structurally sound and every slide fits its layout budget.
2. The machinery rejects what it claims to reject - an over-full slide, a slide with
   no speaker note, a denylisted wording, a dropped concession, a typed literal.

The second half is the one that earns its place. M8 found an integrity control that
had only ever passed on the machine that wrote it; a slide validator nobody has watched
fail is the same defect wearing a different hat.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_report import BuildError  # noqa: E402
from build_slides import (  # noqa: E402
    DECK_FILE,
    SOURCES_DIR,
    check_budget,
    split_notes,
    visible_text,
)
from report_facts import resolve  # noqa: E402
from validate_slides import (  # noqa: E402
    DECK_FORBIDDEN,
    REQUIRED,
    Report,
    check_forbidden,
    check_literal_facts,
    check_required,
)


@pytest.fixture(scope="module")
def deck() -> dict:
    return yaml.safe_load(DECK_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sources(deck: dict) -> dict[str, str]:
    return {
        entry["file"]: (SOURCES_DIR / entry["file"]).read_text(encoding="utf-8")
        for entry in deck["slides"]
        if (SOURCES_DIR / entry["file"]).exists()
    }


# --------------------------------------------------------------------------
# 1. The authored deck
# --------------------------------------------------------------------------


def test_every_declared_slide_is_authored(deck: dict, sources: dict[str, str]) -> None:
    missing = [e["file"] for e in deck["slides"] if e["file"] not in sources]
    assert not missing, f"declared in deck.yaml but not authored: {missing}"


def test_slide_numbers_are_contiguous_from_one(deck: dict) -> None:
    numbers = [e["n"] for e in deck["slides"]]
    assert numbers == list(range(1, len(numbers) + 1))


def test_slide_ids_are_unique(deck: dict) -> None:
    ids = [e["id"] for e in deck["slides"]]
    assert len(ids) == len(set(ids))


def test_every_layout_has_a_budget(deck: dict) -> None:
    for entry in deck["slides"]:
        assert entry["layout"] in deck["layouts"], entry["file"]


def test_every_tier_is_core_or_supporting(deck: dict) -> None:
    for entry in deck["slides"]:
        assert entry["tier"] in {"core", "supporting"}, entry["file"]


def test_every_slide_has_a_speaker_note(deck: dict, sources: dict[str, str]) -> None:
    """A slide with no note is a claim with no argument behind it."""
    for entry in deck["slides"]:
        body, notes = split_notes(sources[entry["file"]], entry["file"])
        assert body.strip(), entry["file"]
        assert notes.strip(), entry["file"]


def test_every_slide_fits_its_layout_budget(deck: dict, sources: dict[str, str]) -> None:
    """The deterministic half of the overflow defence.

    The slide box is a fixed 190.5 mm with `overflow: hidden`, so text that does not
    fit is clipped rather than reflowed - it disappears instead of erroring.
    """
    from build_slides import make_markdown, substitute_facts

    md = make_markdown()
    facts = resolve()
    for entry in deck["slides"]:
        text = substitute_facts(sources[entry["file"]], facts, entry["file"])
        body, _ = split_notes(text, entry["file"])
        check_budget(md.render(body), entry["layout"], deck["layouts"], entry["file"])


def test_the_deck_has_no_facts_file_of_its_own() -> None:
    """One source of truth. A second facts file is how two documents start disagreeing."""
    assert not (REPO_ROOT / "slides" / "facts.yaml").exists()


def test_the_authored_deck_passes_its_own_denylist(sources: dict[str, str]) -> None:
    report = Report()
    check_forbidden(sources, report)
    assert not report.hard, report.hard


def test_the_authored_deck_keeps_every_required_concession(
    deck: dict, sources: dict[str, str]
) -> None:
    report = Report()
    check_required(deck, sources, report)
    assert not report.hard, report.hard


def test_no_locked_quantity_is_typed_as_a_literal(sources: dict[str, str]) -> None:
    report = Report()
    check_literal_facts(sources, report)
    assert not report.hard, report.hard


# --------------------------------------------------------------------------
# 2. The guards reject what they claim to reject
# --------------------------------------------------------------------------


def test_an_over_full_slide_is_rejected(deck: dict) -> None:
    html = "<p>" + ("word " * 400) + "</p>"
    with pytest.raises(BuildError, match="exceeds the statement budget"):
        check_budget(html, "statement", deck["layouts"], "probe.md")


def test_too_many_bullets_are_rejected(deck: dict) -> None:
    html = "<ul>" + ("<li>a</li>" * 12) + "</ul>"
    with pytest.raises(BuildError, match="bullets exceeds"):
        check_budget(html, "bullets", deck["layouts"], "probe.md")


def test_a_slide_with_no_speaker_note_is_rejected() -> None:
    with pytest.raises(BuildError, match="Speaker notes"):
        split_notes("# A slide\n\nSome body copy.\n", "probe.md")


def test_a_slide_with_an_empty_speaker_note_is_rejected() -> None:
    with pytest.raises(BuildError, match="speaker note is empty"):
        split_notes("Body copy.\n\n## Speaker notes\n", "probe.md")


def test_small_print_is_excluded_from_the_budget() -> None:
    """Captions and evidence pointers are set small on purpose and must not count.

    Otherwise the honest habit - naming the evidence file under a figure - would be
    the thing that pushes a slide over its limit.
    """
    caption = "<figcaption>" + ("x" * 4000) + "</figcaption>"
    assert len(visible_text("<p>short</p>" + caption)) < 40


@pytest.mark.parametrize(
    "phrase",
    [
        "Scored by one human rater against the rubric.",
        "The system is deployed in the cloud for the jury.",
        "The 200 MiB margin forbids hosting it online.",
        "No assistant ever ran a generation.",
        "A seamless, state-of-the-art pipeline.",
        "The result is production-ready.",
    ],
)
def test_denylisted_wordings_are_caught(phrase: str) -> None:
    report = Report()
    check_forbidden({"probe.md": phrase}, report)
    assert report.hard, f"denylist missed: {phrase!r}"


def test_dropping_the_partial_pass_verdict_is_caught(deck: dict) -> None:
    """The single most important thing the deck must not quietly upgrade."""
    by_id = {e["id"]: e["file"] for e in deck["slides"]}
    softened = {by_id["retro-poster"]: "retro-poster learned the style well.\n"}
    report = Report()
    check_required(deck, softened, report)
    assert any("PARTIAL PASS" in msg for msg in report.hard), report.hard


def test_dropping_the_inconclusive_verdict_is_caught(deck: dict) -> None:
    by_id = {e["id"]: e["file"] for e in deck["slides"]}
    softened = {by_id["rq4"]: "More images gave better results.\n"}
    report = Report()
    check_required(deck, softened, report)
    assert any("INCONCLUSIVE" in msg for msg in report.hard), report.hard


def test_a_typed_literal_instead_of_a_fact_placeholder_is_caught() -> None:
    report = Report()
    check_literal_facts({"probe.md": "The dataset holds 148 items.\n"}, report)
    assert any("dataset_total" in msg for msg in report.hard), report.hard


def test_two_character_values_are_not_literal_checked() -> None:
    """`16:9` is discussed legitimately, and 16 is a locked value. No false positive."""
    report = Report()
    check_literal_facts({"probe.md": "The deck is 16:9 throughout.\n"}, report)
    assert not report.hard, report.hard


# --------------------------------------------------------------------------
# 3. The test-count split the deck reports
# --------------------------------------------------------------------------


def test_the_pytest_split_adds_up() -> None:
    """473 product/research + 16 report tests = 489. The deck must not blur the three."""
    facts = resolve()
    assert facts["pytest_tests"] + facts["pytest_report_tests"] == facts["pytest_total"]


def test_the_deck_forbidden_patterns_all_compile() -> None:
    for pattern, why in DECK_FORBIDDEN:
        re.compile(pattern)
        assert why.strip()


def test_every_required_check_names_a_real_slide(deck: dict) -> None:
    ids = {e["id"] for e in deck["slides"]}
    for slide_id, pattern, why in REQUIRED:
        assert slide_id in ids, f"REQUIRED names unknown slide id {slide_id!r}"
        re.compile(pattern)
        assert why.strip()
