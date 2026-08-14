"""Resolve the research report's fact locks against their evidence.

Every quantitative value the report repeats is declared once in ``report/facts.yaml``
and referenced in the Markdown sources as ``{{ facts.<key> }}``. This module reads
those declarations, extracts each value from the evidence file that states it, and
fails loudly when the two disagree.

Why the extraction methods are graded rather than uniform: a bare substring search
for ``"473"`` succeeds against the M8 evidence index no matter which column it lands
in, and two of that table's three columns hold superseded counts. A fact lock that
can pass against a stale value is worse than no fact lock, because it converts an
unchecked number into one that looks checked.

    structural   parse the source as CSV or JSON and read the value out of the
                 parsed object. No pattern, so no false positive is possible.
    exact_hash   the full 64-character digest must appear literally. Never a prefix.
    prose_regex  a regex carrying both the fact's context and its value, which must
                 match EXACTLY ONCE. Zero matches or several is a failure: an
                 ambiguous anchor is a broken anchor.

Usage::

    python scripts/report_facts.py --check     # verify every fact, exit non-zero on drift
    python scripts/report_facts.py --dump      # print the resolved values
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
FACTS_FILE = REPO_ROOT / "report" / "facts.yaml"

HEX64 = re.compile(r"^[0-9a-f]{64}$")


class FactError(RuntimeError):
    """A declared fact does not match the evidence it cites."""


@dataclass(frozen=True)
class Fact:
    key: str
    value: Any
    source: str
    method: str
    description: str
    pattern: str | None = None
    extractor: str | None = None

    @property
    def source_path(self) -> Path:
        return REPO_ROOT / self.source


# --------------------------------------------------------------------------
# Structural extractors. Each parses its source and returns one value.
# Registered by name so facts.yaml stays declarative.
# --------------------------------------------------------------------------

_EXTRACTORS: dict[str, Callable[[Path], Any]] = {}


def _extractor(name: str) -> Callable[[Callable[[Path], Any]], Callable[[Path], Any]]:
    def register(fn: Callable[[Path], Any]) -> Callable[[Path], Any]:
        _EXTRACTORS[name] = fn
        return fn

    return register


def _read_dataset(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@_extractor("dataset_total")
def _dataset_total(path: Path) -> int:
    return len(_read_dataset(path))


def _count_column(path: Path, column: str, wanted: str) -> int:
    return Counter(row[column] for row in _read_dataset(path))[wanted]


@_extractor("dataset_style_ukiyo_e")
def _dataset_ukiyo_e(path: Path) -> int:
    return _count_column(path, "style", "ukiyo-e")


@_extractor("dataset_style_minimal_geometric")
def _dataset_minimal_geometric(path: Path) -> int:
    return _count_column(path, "style", "minimal-geometric")


@_extractor("dataset_style_retro_poster")
def _dataset_retro_poster(path: Path) -> int:
    return _count_column(path, "style", "retro-poster")


@_extractor("dataset_split_train")
def _dataset_train(path: Path) -> int:
    return _count_column(path, "split", "train")


@_extractor("dataset_split_val")
def _dataset_val(path: Path) -> int:
    return _count_column(path, "split", "val")


@_extractor("dataset_split_holdout")
def _dataset_holdout(path: Path) -> int:
    return _count_column(path, "split", "holdout")


def _read_registry(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@_extractor("experiment_count")
def _experiment_count(path: Path) -> int:
    return len(_read_registry(path))


def _registry_row(path: Path, exp_id: str) -> dict[str, str]:
    for row in _read_registry(path):
        if row["id"] == exp_id:
            return row
    raise FactError(f"{exp_id} is not in {path.name}")


@_extractor("exp019b_spare_mib")
def _exp019b_spare(path: Path) -> float:
    """EXP-019b's spare device memory, read out of its recorded peak_vram prose.

    The registry stores peak_vram as a sentence rather than a column per figure,
    so this anchors on the row FIRST (structural) and only then reads the number
    out of that one cell.
    """
    cell = _registry_row(path, "EXP-019b")["peak_vram"]
    match = re.search(r"([\d.]+) MiB spare", cell)
    if match is None:
        raise FactError("EXP-019b peak_vram does not state a spare figure")
    return float(match.group(1))


@_extractor("exp019b_peak_allocated_mib")
def _exp019b_peak_allocated(path: Path) -> float:
    cell = _registry_row(path, "EXP-019b")["peak_vram"]
    match = re.search(r"peak ([\d.]+) allocated", cell)
    if match is None:
        raise FactError("EXP-019b peak_vram does not state a peak allocated figure")
    return float(match.group(1))


@_extractor("exp034_worst_device_used_mib")
def _exp034_worst_device_used(path: Path) -> float:
    """EXP-034's worst DEVICE-USED figure under real serving.

    This is the number that pairs with ``worst_spare_mib``: device used + spare = device
    total (7987.5 + 200.0 = 8187.5). It exists because the deck previously subtracted
    ``peak_allocated_mib`` from ``device_total_mib`` and got 3044 MiB, which is not the
    margin - peak *allocated* counts live tensors only, while the spare figure is measured
    against total device occupancy. Two different memory concepts, and the arithmetic
    between them is meaningless. Locking the device figure makes the slide's subtraction
    checkable instead of plausible.

    The reference-conditioned run is the worst case and therefore the production ceiling;
    the prompt-only figure (7969.5) is lower and must not be quoted as the ceiling.
    """
    cell = _registry_row(path, "EXP-034")["peak_vram"]
    match = re.search(r"to ([\d.]+) \(reference\)", cell)
    if match is None:
        raise FactError("EXP-034 peak_vram does not state a reference-conditioned device figure")
    return float(match.group(1))


@_extractor("device_total_mib")
def _device_total(path: Path) -> float:
    cell = _registry_row(path, "EXP-019b")["gpu"]
    match = re.search(r"([\d.]+) MiB", cell)
    if match is None:
        raise FactError("EXP-019b gpu column does not state a device size")
    return float(match.group(1))


@_extractor("lora_rank")
def _lora_rank(path: Path) -> int:
    """The rank every training run used, asserted to be unanimous.

    Reading one row would hide a disagreement; this reads them all and fails if
    the training runs did not agree.
    """
    ranks = {
        row["rank"]
        for row in _read_registry(path)
        if row["rank"] not in {"", "n/a (inference only)"}
    }
    if len(ranks) != 1:
        raise FactError(f"training runs do not agree on rank: {sorted(ranks)}")
    return int(ranks.pop())


@_extractor("clean_clone_image_sha256")
def _clean_clone_sha(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["image_sha256"]


@_extractor("decision_record_count")
def _decision_record_count(path: Path) -> int:
    return len(sorted(path.glob("DR-*.md")))


# --------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------


def load_facts(facts_file: Path = FACTS_FILE) -> list[Fact]:
    raw = yaml.safe_load(facts_file.read_text(encoding="utf-8"))
    facts = []
    for key, body in raw.items():
        facts.append(
            Fact(
                key=key,
                value=body["value"],
                source=body["source"],
                method=body["method"],
                description=body["description"],
                pattern=body.get("pattern"),
                extractor=body.get("extractor"),
            )
        )
    return facts


def _extract_structural(fact: Fact) -> Any:
    if fact.extractor is None:
        raise FactError(f"{fact.key}: method 'structural' needs an extractor")
    if fact.extractor not in _EXTRACTORS:
        raise FactError(f"{fact.key}: unknown extractor {fact.extractor!r}")
    return _EXTRACTORS[fact.extractor](fact.source_path)


def _extract_exact_hash(fact: Fact) -> Any:
    digest = str(fact.value)
    if not HEX64.match(digest):
        raise FactError(
            f"{fact.key}: exact_hash needs a full 64-character digest, "
            f"got {len(digest)} characters - a prefix is not acceptable"
        )
    text = fact.source_path.read_text(encoding="utf-8")
    if digest not in text:
        raise FactError(f"{fact.key}: {digest} does not appear in {fact.source}")
    return fact.value


def _extract_prose_regex(fact: Fact) -> Any:
    if fact.pattern is None:
        raise FactError(f"{fact.key}: method 'prose_regex' needs a pattern")
    text = fact.source_path.read_text(encoding="utf-8")
    matches = list(re.finditer(fact.pattern, text))
    if not matches:
        raise FactError(
            f"{fact.key}: pattern matched nothing in {fact.source}. "
            "The evidence moved, or the anchor was never right."
        )
    if len(matches) > 1:
        lines = [text[: m.start()].count("\n") + 1 for m in matches]
        raise FactError(
            f"{fact.key}: pattern matched {len(matches)} times in {fact.source} "
            f"(lines {lines}). An ambiguous anchor is a broken anchor - it could "
            "confirm a stale value as easily as the current one."
        )
    groups = matches[0].groupdict()
    if "value" not in groups:
        raise FactError(f"{fact.key}: pattern must capture a group named 'value'")
    return groups["value"]


_METHODS: dict[str, Callable[[Fact], Any]] = {
    "structural": _extract_structural,
    "exact_hash": _extract_exact_hash,
    "prose_regex": _extract_prose_regex,
}


def _comparable(declared: Any, extracted: Any) -> tuple[Any, Any]:
    """Normalise for comparison without loosening it.

    Prose extraction yields strings; declarations are typed. Numbers are compared
    numerically (so 200.0 matches "200.0") and strings after stripping the digit
    grouping this project's documents use, e.g. "6 414 480".
    """
    if isinstance(declared, bool):
        return declared, extracted
    if isinstance(declared, (int, float)):
        cleaned = str(extracted).replace(" ", "").replace(" ", "").replace(",", "")
        return float(declared), float(cleaned)
    return str(declared), str(extracted)


def resolve(facts: list[Fact] | None = None) -> dict[str, Any]:
    """Return every fact's declared value, having proved it against the evidence."""
    facts = facts if facts is not None else load_facts()
    resolved: dict[str, Any] = {}
    problems: list[str] = []

    for fact in facts:
        try:
            if not fact.source_path.exists():
                raise FactError(f"{fact.key}: {fact.source} does not exist")
            if fact.method not in _METHODS:
                raise FactError(f"{fact.key}: unknown method {fact.method!r}")
            extracted = _METHODS[fact.method](fact)
            declared_c, extracted_c = _comparable(fact.value, extracted)
            if declared_c != extracted_c:
                raise FactError(
                    f"{fact.key}: declared {fact.value!r} but {fact.source} "
                    f"states {extracted!r}"
                )
            resolved[fact.key] = fact.value
        except FactError as exc:
            problems.append(str(exc))
        except Exception as exc:  # noqa: BLE001 - report, never mask
            problems.append(f"{fact.key}: {type(exc).__name__}: {exc}")

    if problems:
        raise FactError(
            f"{len(problems)} fact lock(s) failed:\n  - " + "\n  - ".join(problems)
        )
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify every fact lock")
    parser.add_argument("--dump", action="store_true", help="print resolved values")
    args = parser.parse_args(argv)

    if not (args.check or args.dump):
        args.check = True

    try:
        facts = load_facts()
        resolved = resolve(facts)
    except FactError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if args.dump:
        width = max(len(k) for k in resolved)
        for fact in facts:
            print(f"{fact.key:<{width}}  {resolved[fact.key]!r:<70}  {fact.source}")

    if args.check:
        print(f"OK: {len(resolved)} fact locks resolve against their evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
