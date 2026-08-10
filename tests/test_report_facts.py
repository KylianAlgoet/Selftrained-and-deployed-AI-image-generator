"""The research report's numbers must equal the evidence's numbers.

These tests are the reason a stale figure in the report fails the build rather
than reaching the jury. They cover two things:

1. Every declared fact resolves against the evidence file it cites.
2. The extraction machinery actually rejects what it claims to reject.

The second half matters as much as the first. M8 found an integrity control that
had only ever passed on the machine that wrote it, and a fact lock nobody has
watched fail is the same class of defect: it looks like verification and is not.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from report_facts import (  # noqa: E402
    FACTS_FILE,
    Fact,
    FactError,
    load_facts,
    resolve,
)


@pytest.fixture(scope="module")
def facts() -> list[Fact]:
    return load_facts()


# --------------------------------------------------------------------------
# 1. The declared facts match their evidence
# --------------------------------------------------------------------------


def test_every_declared_fact_matches_its_evidence(facts: list[Fact]) -> None:
    """The whole point. If this fails, a number in the report has drifted."""
    resolved = resolve(facts)
    assert len(resolved) == len(facts)


def test_every_fact_source_exists(facts: list[Fact]) -> None:
    missing = [f"{f.key} -> {f.source}" for f in facts if not f.source_path.exists()]
    assert not missing, f"fact sources that do not exist: {missing}"


def test_every_fact_has_a_description(facts: list[Fact]) -> None:
    """A fact whose meaning is not written down cannot be reviewed."""
    undescribed = [f.key for f in facts if not f.description.strip()]
    assert not undescribed


def test_prose_regex_facts_capture_a_value_group(facts: list[Fact]) -> None:
    bad = [
        f.key
        for f in facts
        if f.method == "prose_regex" and "(?P<value>" not in (f.pattern or "")
    ]
    assert not bad, f"prose_regex facts without a 'value' capture group: {bad}"


def test_prose_regex_patterns_are_unambiguous(facts: list[Fact]) -> None:
    """Each prose anchor must match exactly once in its source.

    A pattern matching twice could confirm a superseded value as readily as the
    current one - which is precisely how a substring anchor like "473" would
    behave against the M8 evidence table, whose other columns hold 406 and 473.
    """
    ambiguous = {}
    for fact in facts:
        if fact.method != "prose_regex":
            continue
        text = fact.source_path.read_text(encoding="utf-8")
        count = len(re.findall(fact.pattern or "", text))
        if count != 1:
            ambiguous[fact.key] = count
    assert not ambiguous, f"anchors matching != 1 time: {ambiguous}"


def test_hash_facts_are_full_length(facts: list[Fact]) -> None:
    """A truncated digest is not an integrity check."""
    short = [
        f.key
        for f in facts
        if f.method == "exact_hash" and not re.fullmatch(r"[0-9a-f]{64}", str(f.value))
    ]
    assert not short, f"exact_hash facts that are not 64 hex characters: {short}"


# --------------------------------------------------------------------------
# 2. The machinery rejects what it claims to reject
# --------------------------------------------------------------------------


def test_a_wrong_declared_value_fails(facts: list[Fact]) -> None:
    """Change the number, keep the evidence: the lock must notice."""
    target = next(f for f in facts if f.key == "pytest_tests")
    tampered = Fact(
        key=target.key,
        value=474,  # one more than the evidence states
        source=target.source,
        method=target.method,
        description=target.description,
        pattern=target.pattern,
    )
    with pytest.raises(FactError, match="pytest_tests"):
        resolve([tampered])


def test_a_stale_value_from_the_wrong_column_fails(facts: list[Fact]) -> None:
    """The specific failure this design exists to prevent.

    406 is a real pytest count - it is the M7 column of the same table. A weak
    anchor would confirm it. The context-anchored pattern must not.
    """
    target = next(f for f in facts if f.key == "pytest_tests")
    stale = Fact(
        key=target.key,
        value=406,
        source=target.source,
        method=target.method,
        description=target.description,
        pattern=target.pattern,
    )
    with pytest.raises(FactError):
        resolve([stale])


def test_an_ambiguous_pattern_fails(facts: list[Fact]) -> None:
    """A bare number matches many places; that must be an error, not a pass."""
    ambiguous = Fact(
        key="ambiguous_probe",
        value=473,
        source="docs/evidence/M8/README.md",
        method="prose_regex",
        description="deliberately weak anchor, used to prove the guard works",
        pattern=r"(?P<value>473)",
    )
    with pytest.raises(FactError, match="matched"):
        resolve([ambiguous])


def test_a_truncated_hash_is_rejected() -> None:
    """`46bbf160e427...` appears all over the docs. A prefix must not satisfy a lock."""
    truncated = Fact(
        key="truncated_probe",
        value="46bbf160e427",
        source="docs/evidence/M8/README.md",
        method="exact_hash",
        description="deliberately truncated digest, used to prove the guard works",
    )
    with pytest.raises(FactError, match="64-character"):
        resolve([truncated])


def test_a_missing_source_fails() -> None:
    missing = Fact(
        key="missing_probe",
        value=1,
        source="docs/evidence/M8/this-file-does-not-exist.md",
        method="prose_regex",
        description="deliberately missing source, used to prove the guard works",
        pattern=r"(?P<value>1)",
    )
    with pytest.raises(FactError, match="does not exist"):
        resolve([missing])


def test_an_unmatched_pattern_fails() -> None:
    """If the evidence is rewritten and the anchor stops matching, fail loudly."""
    unmatched = Fact(
        key="unmatched_probe",
        value=1,
        source="docs/evidence/M8/README.md",
        method="prose_regex",
        description="deliberately unmatchable anchor, used to prove the guard works",
        pattern=r"\*\*Zorknangle count:\s*(?P<value>\d+)\*\*",
    )
    with pytest.raises(FactError, match="matched nothing"):
        resolve([unmatched])


# --------------------------------------------------------------------------
# 3. The declarations themselves stay honest
# --------------------------------------------------------------------------


def test_facts_file_is_valid_yaml_with_required_keys() -> None:
    raw = yaml.safe_load(FACTS_FILE.read_text(encoding="utf-8"))
    assert isinstance(raw, dict) and raw
    for key, body in raw.items():
        for required in ("value", "source", "method", "description"):
            assert required in body, f"{key} is missing '{required}'"
        assert body["method"] in {"structural", "exact_hash", "prose_regex"}


def test_the_generation_total_is_twenty_seven(facts: list[Fact]) -> None:
    """Guarded explicitly because reporting 25 has been a live risk all project.

    25 is the research cap; 27 is the truth (25 research + 1 M7 human review
    + 1 M8 deployment validation).
    """
    resolved = resolve(facts)
    assert resolved["generations_total"] == 27
    assert resolved["generations_research"] == 25


def test_the_production_margin_is_the_serving_figure(facts: list[Fact]) -> None:
    """200.0 (EXP-034, real serving) governs, not 202.0 and not the 218.0 prompt-only run."""
    resolved = resolve(facts)
    assert resolved["worst_spare_mib"] == 200.0
    assert resolved["oneshot_spare_mib"] == 202.0
    assert resolved["worst_spare_mib"] < resolved["oneshot_spare_mib"]


def test_dataset_counts_are_internally_consistent(facts: list[Fact]) -> None:
    resolved = resolve(facts)
    by_style = (
        resolved["dataset_ukiyo_e"]
        + resolved["dataset_minimal_geometric"]
        + resolved["dataset_retro_poster"]
    )
    by_split = (
        resolved["dataset_train"] + resolved["dataset_val"] + resolved["dataset_holdout"]
    )
    assert by_style == resolved["dataset_total"]
    assert by_split == resolved["dataset_total"]
