"""M11 B8 - link and path audit across every Git-tracked markdown source.

Internal links and referenced paths are resolved against the working tree and are
definitive. External URLs are classified rather than judged: this project has hit
403/429 from institutional hosts four times (M2 Digital Comic Museum and the Art
Institute of Chicago, M9's two unretrievable references), so an HTTP failure here
is evidence about the host, not proof that the citation is wrong.

Failure classes:
    BROKEN-INTERNAL   a repository path that does not exist
    STALE-PATH        an internal path that exists only under a different name
    EXTERNAL-FAIL     a URL that did not return a success status
    EXTERNAL-BLOCKED  403/429 - reachable but refusing an automated client

Run:  .venv\\Scripts\\python.exe docs\\evidence\\M11\\audit_links.py [--check-external]
"""

from __future__ import annotations

import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# Bare URLs matter here: the mandatory public planning link (project brief
# requirement 9) is written as a bold bare URL in README.md, not as a markdown
# link, so a link-only sweep would never check the one URL the assignment requires.
BARE_URL = re.compile(r"(?<![(\[])\bhttps?://[A-Za-z0-9._~:/?#@!$&*+,;=%-]+")
LOCAL_HOSTS = ("localhost", "127.0.0.1")
BACKTICK_PATH = re.compile(r"`([A-Za-z0-9_./\\-]+\.(?:md|py|ts|tsx|csv|yaml|yml|json|ps1|jsonl|pdf|txt|cfg|ini))`")


def tracked_markdown() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True)
    return [ROOT / line for line in out.stdout.splitlines() if line]


files = tracked_markdown()

# Every tracked file's basename, so a bare filename named in prose can be told
# apart from a path that is actually wrong.
all_tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
basenames = {Path(p).name for p in all_tracked.stdout.splitlines() if p}

link_ok = 0
link_bad: list[tuple[str, str]] = []
path_ok = 0
path_bad: list[tuple[str, str]] = []
expected: list[tuple[str, str]] = []
prose_names = 0
anchors_skipped = 0
external: dict[str, list[str]] = defaultdict(list)


# Bases a written path may be relative to. `apps/web` and `docs/evidence` are
# conventions this project already uses: a frontend section writes
# `src/viewer/DeckViewer.tsx`, an evidence index writes `EXP-031/final-matrix.jsonl`.
BASES = ["", "apps/web", "docs", "docs/evidence", "ml", "apps"]

# Written paths that correctly do NOT resolve in this repository, each with the
# reason. These are not stale - resolving them would mean the documentation was
# wrong, not right.
EXPECTED_UNRESOLVED = {
    "slides/facts.yaml":
        "DELIBERATELY ABSENT - the deck holds no facts of its own; DR-016 and the "
        "handoff both instruct that this file must never be created",
    "loaders/ip_adapter.py":
        "LIBRARY-INTERNAL - a path inside diffusers, cited to show where "
        "CLIPVisionModelWithProjection is loaded, not a file in this repository",
    "slides/sources/13-step-300.md":
        "HISTORICAL - a slide of the 26-slide deck, removed by DR-017's "
        "restructuring; the build record and process log describe what was there",
    "docs/evidence/EXP-0xx/training-runs.jsonl":
        "TEMPLATE - 'EXP-0xx' is a pattern, not an identifier",
    "error-context.md":
        "TOOL ARTEFACT - a file Playwright writes into its own trace output",
    ".run/demo.json":
        "RUNTIME ARTEFACT - written by start-demo.ps1 and deleted by stop-demo.ps1, "
        "inside the git-ignored .run/ directory. The M12 record cites its timestamp as "
        "evidence of when the demo was alive; the file itself is not expected to survive",
    "apps/web/src/viewer/ViewerControls.tsx":
        "HISTORICAL - a Prototype 0 component, superseded by the M7 interface "
        "redesign; prototype-0.md records what Prototype 0 built and is not rewritten",
    "ViewerControls.tsx": "HISTORICAL - see apps/web/src/viewer/ViewerControls.tsx",
}


def resolve(path: Path, target: str) -> bool:
    clean = target.split("#")[0].split("?")[0].replace("\\", "/")
    if not clean:
        return True
    if (path.parent / clean).exists():
        return True
    return any((ROOT / base / clean.lstrip("/")).exists() for base in BASES)


for path in files:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8-sig")
    rel = path.relative_to(ROOT).as_posix()

    # 1. Real markdown links. These are navigation: a broken one is a defect.
    for m in MD_LINK.finditer(text):
        target = m.group(1)
        if target.startswith(("http://", "https://")):
            external[target].append(rel)
        elif target.startswith(("#", "mailto:")):
            anchors_skipped += 1
        elif resolve(path, target):
            link_ok += 1
        else:
            link_bad.append((rel, target))

    # 1b. Bare URLs. Local development URLs are not external resources.
    for m in BARE_URL.finditer(text):
        url = m.group(0).rstrip(".,;:)*_")   # trailing markdown emphasis is not part of the URL
        if any(h in url for h in LOCAL_HOSTS):
            continue
        if rel not in external[url]:
            external[url].append(rel)

    # 2. Backticked tokens. A token containing "/" is being presented AS a path,
    #    so it must resolve. A bare filename is prose naming a file - `pytest.ini`,
    #    `validate_slides.py` - and requiring it to resolve from the citing file's
    #    directory would flag correct writing as an error.
    for m in BACKTICK_PATH.finditer(text):
        target = m.group(1)
        if "/" in target or "\\" in target:
            if resolve(path, target):
                path_ok += 1
            elif target in EXPECTED_UNRESOLVED:
                expected.append((rel, target))
            else:
                path_bad.append((rel, target))
        elif target in basenames:
            prose_names += 1
        elif target in EXPECTED_UNRESOLVED:
            expected.append((rel, target))
        else:
            path_bad.append((rel, f"{target}  (bare filename, no such tracked file)"))

print("=== B8 LINK AND PATH AUDIT ===")
print(f"tracked markdown files scanned  : {len(files)}")
print(f"markdown links resolved         : {link_ok}")
print(f"backticked paths resolved       : {path_ok}")
print(f"bare filenames named in prose   : {prose_names}  (each matches a tracked file)")
print(f"in-page anchors skipped         : {anchors_skipped}")
print(f"distinct external URLs          : {len(external)}")
print()

print("--- broken markdown links ---")
if link_bad:
    for rel, target in link_bad:
        print(f"  BROKEN-INTERNAL  {rel}  ->  {target}")
else:
    print("  none - every markdown link resolves")
print()

print("--- written paths that intentionally do not resolve ---")
if expected:
    seen: set[str] = set()
    for rel, target in expected:
        if target not in seen:
            seen.add(target)
            print(f"  {target}")
            print(f"      {EXPECTED_UNRESOLVED[target]}")
        print(f"      cited in {rel}")
else:
    print("  none")
print()

print("--- stale paths (unexplained) ---")
if path_bad:
    for rel, target in path_bad:
        print(f"  STALE-PATH  {rel}  ->  {target}")
else:
    print("  none")
print()

print("--- external URLs by host ---")
hosts = Counter(u.split("/")[2] for u in external)
for host, n in hosts.most_common():
    print(f"  {host:<45} {n}")
print()

if "--check-external" in sys.argv:
    print("--- external reachability (one request per URL, 15 s timeout) ---")
    print("    Dataset provenance URLs are sampled, not swept: 96 of them point at two")
    print("    institutional hosts that have rate-limited this project before, and")
    print("    hammering them would produce 429s that say nothing about the citations.")
    checked: dict[str, str] = {}
    per_host: Counter = Counter()
    for url in sorted(external):
        host = url.split("/")[2]
        is_dataset = host in {"www.metmuseum.org", "www.loc.gov"}
        if is_dataset and per_host[host] >= 3:
            continue
        if url.endswith(".git"):        # a clone URL, not a page
            url = url[:-4]
        per_host[host] += 1
        req = urllib.request.Request(url, method="HEAD", headers={
            "User-Agent": "Mozilla/5.0 (compatible; DeckForge-M11-link-audit/1.0)"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                status = f"{r.status} OK"
        except urllib.error.HTTPError as e:
            status = f"{e.code} " + ("EXTERNAL-BLOCKED" if e.code in (401, 403, 429) else "EXTERNAL-FAIL")
        except Exception as e:  # noqa: BLE001 - network conditions are the finding
            status = f"EXTERNAL-FAIL {type(e).__name__}"
        checked[url] = status
        print(f"  {status:<28} {url}")
        for src in external[url][:2]:
            print(f"      cited in {src}")
    print()
    bad = {u: s for u, s in checked.items() if "OK" not in s}
    print(f"  checked {len(checked)} URL(s); {len(bad)} did not return success")
else:
    print("(external reachability not checked - pass --check-external)")

print()
if link_bad or path_bad:
    print(f"=== B8 RESULT: {len(link_bad)} broken link(s), {len(path_bad)} stale path(s) ===")
    sys.exit(1)
print("=== B8 RESULT: every markdown link and every written path resolves ===")
