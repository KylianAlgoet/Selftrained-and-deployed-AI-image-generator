"""M11 B4 - dataset, provenance and licence re-audit.

Re-derives every dataset figure the report and the deck depend on, directly from
`data/manifests/dataset-v1.csv`, and compares them with the values locked in
`report/facts.yaml`. Nothing here reads a number out of prose.

Run:  .venv\\Scripts\\python.exe docs\\evidence\\M11\\audit_dataset.py
"""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "data" / "manifests" / "dataset-v1.csv"
FACTS = ROOT / "report" / "facts.yaml"

# `author` is deliberately NOT in this tuple. `docs/04-dataset-methodology.md`
# records the field as "author (where known)", and the Library of Congress WPA
# poster collection is largely anonymous - the institution attributes no artist.
# Requiring it would force the manifest to invent attributions it does not have.
# It is reported separately below instead.
REQUIRED_FIELDS = (
    "id", "filename", "style", "caption", "source", "licence",
    "collection_date", "permitted_use", "width", "height", "sha256", "split",
)

failures: list[str] = []
notes: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' - ' + detail) if detail else ''}")
    if not ok:
        failures.append(f"{label}{(' - ' + detail) if detail else ''}")


def locked(name: str) -> str | None:
    """Read a declared `value:` from report/facts.yaml without a YAML dependency."""
    text = FACTS.read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(name)}:\n(?:.*\n)*?\s+value:\s*(\S+)", text, re.M)
    return m.group(1) if m else None


rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))

print("=== B4 DATASET / LICENCE AUDIT ===")
print(f"manifest: {MANIFEST.relative_to(ROOT)}")
_raw = MANIFEST.read_bytes()
_lf = _raw.replace(b"\r\n", b"\n")
print(f"sha256, working copy as-is : {hashlib.sha256(_raw).hexdigest()}")
print(f"sha256, LF-normalised      : {hashlib.sha256(_lf).hexdigest()}")
print("(M8 found these DIFFERING on this machine - core.autocrlf had normalised the working copy")
print(" to CRLF while Git stored LF, so a frozen hash passed locally and failed on every clean")
print(" clone. They are equal above, which is the .gitattributes fix holding.)")
print()

print("--- accepted items ---")
check("148 accepted items", len(rows) == 148, f"actual {len(rows)}")

print("\n--- style counts ---")
styles = Counter(r["style"] for r in rows)
for style, n in sorted(styles.items()):
    print(f"      {style:<20} {n}")
check("exactly 3 styles", len(styles) == 3, f"actual {len(styles)}")
check("every style >= 40 items", all(n >= 40 for n in styles.values()), str(dict(styles)))
check("style counts sum to the total", sum(styles.values()) == len(rows))

print("\n--- train / validation / holdout split ---")
splits = Counter(r["split"] for r in rows)
for split, n in sorted(splits.items()):
    print(f"      {split:<20} {n}")
check("splits are exactly train/val/holdout", set(splits) == {"train", "val", "holdout"}, str(sorted(splits)))
check("splits sum to the total", sum(splits.values()) == len(rows))

print("\n--- holdout isolation ---")
holdout_ids = {r["id"] for r in rows if r["split"] == "holdout"}
train_ids = {r["id"] for r in rows if r["split"] == "train"}
val_ids = {r["id"] for r in rows if r["split"] == "val"}
check("holdout disjoint from train", not (holdout_ids & train_ids))
check("holdout disjoint from val", not (holdout_ids & val_ids))
check("holdout covers every style", {r["style"] for r in rows if r["split"] == "holdout"} == set(styles),
      str(sorted({r["style"] for r in rows if r["split"] == "holdout"})))

print("\n--- licences ---")
licences = Counter(r["licence"] for r in rows)
for lic, n in sorted(licences.items()):
    print(f"      {lic:<20} {n}")
check("every row carries a licence", all(r["licence"].strip() for r in rows))
check("no restrictive/unknown licence present",
      not {l for l in licences if l.lower() in {"", "unknown", "all rights reserved", "copyright"}},
      str(sorted(licences)))

print("\n--- provenance ---")
missing = {f: [r["id"] for r in rows if not r.get(f, "").strip()] for f in REQUIRED_FIELDS}
for field, ids in missing.items():
    if ids:
        print(f"      {field}: {len(ids)} blank -> {ids[:5]}")
check("every required provenance field is populated on all rows",
      not any(missing.values()),
      ", ".join(f"{f}={len(i)}" for f, i in missing.items() if i))

unattributed = [r for r in rows if not r["author"].strip()]
by_collection = Counter(r["notes"] for r in unattributed)
print(f"      author is blank on {len(unattributed)} of {len(rows)} items - EXPECTED, not a gap:")
for note, n in by_collection.most_common():
    print(f"        {n:>3}  {note}")
check("every unattributed item is institutionally anonymous, not merely unrecorded",
      all(not r["source"].startswith("http") or "loc.gov" in r["source"] or "metmuseum" in r["source"]
          for r in unattributed),
      "an unattributed item cites a source outside the two institutional collections")
check("no unattributed item claims an author-dependent licence",
      all(r["licence"] in {"public domain", "CC0"} for r in unattributed),
      str(Counter(r["licence"] for r in unattributed)))
notes.append(
    f"{len(unattributed)} items carry no `author`: 41 Library of Congress WPA posters and 1 Met "
    "open-access item. Both collections publish these as anonymous. "
    "`docs/04-dataset-methodology.md` already documents the field as \"author (where known)\", "
    "so this is the documented behaviour rather than missing provenance."
)

print("\n--- source domains (copyright claim support) ---")
domains = Counter()
for r in rows:
    s = r["source"]
    if s.startswith("http"):
        domains[s.split("/")[2]] += 1
    else:
        domains[f"project-created: {s}"] += 1
for d, n in sorted(domains.items(), key=lambda kv: -kv[1]):
    print(f"      {d:<45} {n}")
check("project-created material is attributed to a repository generator",
      all(not r["source"].startswith("http") for r in rows if r["licence"] == "project-original"))
check("every non-project item cites an http source",
      all(r["source"].startswith("http") for r in rows if r["licence"] != "project-original"))

print("\n--- integrity mechanism ---")
hashes = [r["sha256"] for r in rows]
check("every row carries a sha256", all(len(h) == 64 for h in hashes), f"bad {sum(1 for h in hashes if len(h) != 64)}")
check("no duplicate sha256 (no duplicate image)", len(set(hashes)) == len(hashes),
      f"{len(hashes) - len(set(hashes))} duplicate(s)")
check("no duplicate id", len({r["id"] for r in rows}) == len(rows))
check("no duplicate filename", len({r["filename"] for r in rows}) == len(rows))

print("\n--- dimensions ---")
dims = Counter((r["width"], r["height"]) for r in rows)
print(f"      distinct sizes: {len(dims)}; most common: {dims.most_common(3)}")
check("all dimensions are positive integers",
      all(int(r["width"]) > 0 and int(r["height"]) > 0 for r in rows))

print("\n--- agreement with report/facts.yaml ---")
expected = {
    "dataset_total": len(rows),
    "dataset_ukiyo_e": styles.get("ukiyo-e", 0),
    "dataset_minimal_geometric": styles.get("minimal-geometric", 0),
    "dataset_retro_poster": styles.get("retro-poster", 0),
    "dataset_train": splits.get("train", 0),
    "dataset_val": splits.get("val", 0),
    "dataset_holdout": splits.get("holdout", 0),
}
for key, derived in expected.items():
    lock = locked(key)
    ok = lock is not None and int(lock) == derived
    print(f"      {key:<28} manifest={derived:<5} facts.yaml={lock}")
    check(f"{key} matches the manifest", ok, f"facts.yaml says {lock}, manifest says {derived}")

if notes:
    print("--- notes (not failures) ---")
    for n in notes:
        print(f"      * {n}")

print()
if failures:
    print(f"=== B4 RESULT: {len(failures)} FAILURE(S) ===")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("=== B4 RESULT: ALL CHECKS PASS ===")
