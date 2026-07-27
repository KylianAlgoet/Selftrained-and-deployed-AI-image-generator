"""Dataset v1 collection from the user-approved source registry (2026-07-27).

Approved sources only (DR-006 + in-chat approval with conditions A-D):
  - Library of Congress WPA posters (public domain, "no known restrictions")
  - Digital Comic Museum (conditional; Cloudflare-gated at collection time ->
    condition B fallback: its retro-comic share shifted to more LOC)
  - Met Museum Open Access API (CC0)
  - Art Institute of Chicago API (approved, but its image CDN returned HTTP 403
    for all programmatic fetches at collection time -> its ukiyo-e share shifted
    to the already-approved Met source #3; no new source was added)
  - Project-original geometric generator (ml/dataset/generate_geometric.py)

Downloads raw candidates into data/raw/<style>/ with a sidecar
data/raw/candidates.csv holding per-item provenance captured at collection
time. Validation/dedup/manifest building happens in build_dataset_v1.py.
Re-runs skip files that already exist.
"""

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
CANDIDATES_CSV = RAW / "candidates.csv"
TODAY = date.today().isoformat()
USER_AGENT = "DeckForgeAI-dataset/1.0 (bachelor research project; contact: repository owner)"
PAUSE_SECONDS = 0.25

sys.path.insert(0, str(REPO))
from ml.dataset.generate_geometric import config_note, generate_geometric  # noqa: E402


def http_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def download(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception as err:  # noqa: BLE001 - log-and-skip is intended here
        print(f"  download failed ({err}): {url}")
        return False


def clean_phrase(text: str, max_words: int = 10) -> str:
    words = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text).split()
    return " ".join(words[:max_words]).lower()


def collect_met(target: int) -> list[dict]:
    """Ukiyo-e woodblock prints, Met Open Access, isPublicDomain=true (CC0)."""
    print(f"[met] searching (target {target})")
    search = http_json(
        "https://collectionapi.metmuseum.org/public/collection/v1/search?"
        + urllib.parse.urlencode({"q": "ukiyo-e woodblock print", "hasImages": "true"})
    )
    rows: list[dict] = []
    for object_id in search.get("objectIDs", []):
        if len(rows) >= target:
            break
        time.sleep(PAUSE_SECONDS)
        try:
            obj = http_json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}")
        except Exception as err:  # noqa: BLE001
            print(f"  metadata failed for {object_id}: {err}")
            continue
        if not obj.get("isPublicDomain") or not obj.get("primaryImage"):
            continue
        blob = " ".join(str(obj.get(k, "")) for k in ("objectName", "classification", "medium")).lower()
        if "woodblock" not in blob and "print" not in blob:
            continue
        filename = f"met-{object_id}.jpg"
        if not download(obj["primaryImage"], RAW / "ukiyo-e" / filename):
            continue
        rows.append(
            {
                "filename": filename,
                "style": "ukiyo-e",
                "content_phrase": clean_phrase(obj.get("title") or "japanese woodblock print"),
                "source": obj.get("objectURL") or f"https://www.metmuseum.org/art/collection/search/{object_id}",
                "author": obj.get("artistDisplayName", ""),
                "licence": "CC0",
                "permitted_use": "unrestricted, including ML training (Met Open Access CC0)",
                "notes": "The Metropolitan Museum of Art Open Access",
            }
        )
        print(f"  [{len(rows)}/{target}] {filename}")
    return rows


def collect_aic(target: int) -> list[dict]:
    """Ukiyo-e prints, Art Institute of Chicago API, is_public_domain=true (CC0)."""
    print(f"[aic] searching (target {target})")
    search = http_json(
        "https://api.artic.edu/api/v1/artworks/search?"
        + urllib.parse.urlencode(
            {
                "q": "ukiyo-e woodblock print",
                "fields": "id,title,artist_display,image_id,is_public_domain",
                "limit": "100",
            }
        )
    )
    rows: list[dict] = []
    for art in search.get("data", []):
        if len(rows) >= target:
            break
        if not art.get("is_public_domain") or not art.get("image_id"):
            continue
        time.sleep(PAUSE_SECONDS)
        filename = f"aic-{art['id']}.jpg"
        image_url = f"https://www.artic.edu/iiif/2/{art['image_id']}/full/843,/0/default.jpg"
        if not download(image_url, RAW / "ukiyo-e" / filename):
            continue
        author = (art.get("artist_display") or "").splitlines()[0] if art.get("artist_display") else ""
        rows.append(
            {
                "filename": filename,
                "style": "ukiyo-e",
                "content_phrase": clean_phrase(art.get("title") or "japanese woodblock print"),
                "source": f"https://www.artic.edu/artworks/{art['id']}",
                "author": author,
                "licence": "CC0",
                "permitted_use": "unrestricted, including ML training (AIC public domain / CC0)",
                "notes": "Art Institute of Chicago open access",
            }
        )
        print(f"  [{len(rows)}/{target}] {filename}")
    return rows


def collect_loc(target: int) -> list[dict]:
    """WPA posters, Library of Congress ('no known restrictions' -> public domain)."""
    print(f"[loc] searching (target {target})")
    rows: list[dict] = []
    page = 1
    while len(rows) < target and page <= 6:
        listing = http_json(
            "https://www.loc.gov/collections/works-progress-administration-posters/?"
            + urllib.parse.urlencode({"fo": "json", "c": "80", "sp": str(page)})
        )
        for item in listing.get("results", []):
            if len(rows) >= target:
                break
            image_urls = item.get("image_url") or []
            if not image_urls:
                continue
            item_id = str(item.get("id", "")).rstrip("/").rsplit("/", 1)[-1]
            if not item_id:
                continue
            time.sleep(PAUSE_SECONDS)
            filename = f"loc-{item_id}.jpg"
            # Last entry in image_url is the largest rendition LOC offers here.
            if not download(image_urls[-1], RAW / "retro-comic" / filename):
                continue
            rows.append(
                {
                    "filename": filename,
                    "style": "retro-comic",
                    "content_phrase": clean_phrase(item.get("title") or "vintage poster"),
                    "source": item.get("url") or f"https://www.loc.gov/item/{item_id}/",
                    "author": "",
                    "licence": "public domain",
                    "permitted_use": "unrestricted (US WPA poster, LOC: no known restrictions)",
                    "notes": "Library of Congress WPA posters collection",
                }
            )
            print(f"  [{len(rows)}/{target}] {filename}")
        page += 1
    return rows


def collect_geometric(target: int, seed_start: int = 1000) -> list[dict]:
    """Project-original seeded generation (licence-free by construction)."""
    print(f"[geometric] generating (target {target})")
    rows: list[dict] = []
    for seed in range(seed_start, seed_start + target):
        filename = f"geo-{seed}.png"
        config = generate_geometric(seed, RAW / "minimal-geometric" / filename)
        rows.append(
            {
                "filename": filename,
                "style": "minimal-geometric",
                "content_phrase": f"abstract composition of {config.shape_count} flat geometric shapes",
                "source": "ml/dataset/generate_geometric.py",
                "author": "DeckForge AI project (Kylian Algoet)",
                "licence": "project-original",
                "permitted_use": "unrestricted (project-original generated artwork)",
                "notes": config_note(config),
            }
        )
    print(f"  generated {len(rows)}")
    return rows


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    candidates: list[dict] = []
    # Ukiyo-e: Met (source #3) only. AIC (source #4) was approved but its image
    # CDN returned HTTP 403 for every programmatic fetch (verified with default
    # and browser user agents), so per the condition-B principle its share moved
    # to the already-approved Met source rather than adding any new source.
    # collect_aic() is retained above for transparency of the attempt.
    candidates += collect_met(target=56)
    # Retro-comic: LOC only (Digital Comic Museum was Cloudflare-gated at
    # collection time -> condition B fallback to additional LOC public-domain
    # posters; no new source added).
    candidates += collect_loc(target=54)
    candidates += collect_geometric(target=52)

    for row in candidates:
        row["collection_date"] = TODAY

    fieldnames = [
        "filename", "style", "content_phrase", "source", "author",
        "licence", "permitted_use", "collection_date", "notes",
    ]
    with open(CANDIDATES_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)
    print(f"\nwrote {len(candidates)} candidates to {CANDIDATES_CSV}")


if __name__ == "__main__":
    main()
