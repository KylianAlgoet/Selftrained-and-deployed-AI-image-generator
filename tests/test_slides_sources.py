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
    check_inline_html_blocks,
    check_layout_markup,
    check_literal_facts,
    check_required,
    check_timing,
    note_seconds,
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
    softened = {by_id["limits"]: "retro-poster learned the style well.\n"}
    report = Report()
    check_required(deck, softened, report)
    assert any("PARTIAL PASS" in msg for msg in report.hard), report.hard


def test_dropping_the_inconclusive_verdict_is_caught(deck: dict) -> None:
    by_id = {e["id"]: e["file"] for e in deck["slides"]}
    softened = {by_id["limits"]: "More images gave better results.\n"}
    report = Report()
    check_required(deck, softened, report)
    assert any("INCONCLUSIVE" in msg for msg in report.hard), report.hard


def test_the_merged_limits_slide_carries_all_three_of_its_concessions(deck: dict) -> None:
    """Three slides became one; none of their bounds may be lost in the merge.

    retro-poster, rq4 and other-failures were separate slides in the 26-slide deck. If a
    future edit trims the merged slide, this is what notices that a concession went with
    the trimming rather than only the prose.
    """
    limits = [entry for entry in REQUIRED if entry[0] == "limits"]
    assert len(limits) == 3, "the limits slide must require all three merged concessions"


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
# 3. Timing - the constraint that restructured the deck (DR-017)
# --------------------------------------------------------------------------


def test_every_slide_declares_the_layout_its_markup_needs(
    deck: dict, sources: dict[str, str]
) -> None:
    report = Report()
    check_layout_markup(deck, sources, report)
    assert not report.hard, report.hard


def test_two_column_markup_under_the_wrong_layout_is_caught(deck: dict) -> None:
    """The defect this guard was written for: valid HTML, every budget passed, renders wrong."""
    bullets_slide = next(e for e in deck["slides"] if e["layout"] == "bullets")
    mismatched = {bullets_slide["file"]: '<div class="col-text">\n\n- a\n\n</div>\n'}
    report = Report()
    check_layout_markup(deck, mismatched, report)
    assert any("split" in msg for msg in report.hard), report.hard


def test_no_inline_svg_contains_a_blank_line(sources: dict[str, str]) -> None:
    report = Report()
    check_inline_html_blocks(sources, report)
    assert not report.hard, report.hard


def test_a_blank_line_inside_an_svg_is_caught() -> None:
    """The defect that shipped: CommonMark ends an HTML block at the first blank line."""
    broken = '<svg viewBox="0 0 10 10">\n  <rect x="1"/>\n\n  <text>lost</text>\n</svg>\n'
    report = Report()
    check_inline_html_blocks({"probe.md": broken}, report)
    assert any("blank line" in msg for msg in report.hard), report.hard


def test_the_authored_deck_fits_its_timing_budget(deck: dict, sources: dict[str, str]) -> None:
    """The whole talk must fit the 20-minute slot, demo included."""
    report = Report()
    check_timing(deck, sources, report)
    assert not report.hard, report.hard


def test_the_declared_budget_is_internally_consistent(deck: dict) -> None:
    """narration_max + demo + min_buffer must not exceed the slot.

    Without this, the three bounds could be set to values no deck can satisfy, and the
    failure would look like a deck problem rather than a budget problem.
    """
    t = deck["timing"]
    assert (
        t["narration_max_seconds"] + t["demo_target_seconds"] + t["min_buffer_seconds"]
        <= t["total_budget_seconds"]
    )
    assert t["narration_min_seconds"] < t["narration_max_seconds"]


def test_an_overrunning_deck_is_caught(deck: dict, sources: dict[str, str]) -> None:
    """The guard has to bite, or it is decoration.

    The first deck overran its slot by six minutes and every check passed on it. This is
    the test that would have failed then.
    """
    bloated = dict(sources)
    first = deck["slides"][0]["file"]
    bloated[first] = sources[first] + ("\n\n" + "filler " * 900)
    report = Report()
    check_timing(deck, bloated, report)
    assert any("narration" in msg for msg in report.hard), report.hard


def test_the_demo_is_never_counted_as_zero(deck: dict, sources: dict[str, str]) -> None:
    """The demo slide's note is directions, so it is excluded from the word count.

    Excluded must not mean free: the handoff and the demo itself are declared costs, and
    the combined total has to carry both.
    """
    t = deck["timing"]
    assert t["demo_target_seconds"] > 0 and t["demo_handoff_seconds"] > 0

    demo_files = [e["file"] for e in deck["slides"] if e["layout"] == "demo"]
    assert demo_files, "the deck must have a demo slide"

    seconds = note_seconds(deck, sources)
    narration = (
        sum(seconds[e["file"]] for e in deck["slides"] if e["layout"] != "demo")
        + t["demo_handoff_seconds"]
    )
    combined = narration + t["demo_target_seconds"]
    assert combined <= t["total_budget_seconds"] - t["min_buffer_seconds"]


# --------------------------------------------------------------------------
# 4. The test-count split the deck reports
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
