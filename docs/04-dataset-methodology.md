# Dataset methodology

**Created:** 2026-07-27 · **Updated:** 2026-07-30 (M3 pre-check: `retro-comic` renamed to `retro-poster`; see DR-006 correction) · Answers RQ3/RQ4/RQ11.

## Final style set (DR-006, approved by Kylian 2026-07-27; style 1 relabelled 2026-07-30)

1. **Retro silkscreen poster** (`retro-poster`) — flat silkscreen colour fields, limited palettes, Art Deco/Moderne figures, bold display typography. **Renamed from `retro-comic` on 2026-07-30**: the collected material is Library of Congress WPA / Federal Theatre Project silkscreen posters and contains no halftone, comic panels, speech balloons, or sequential art, so the original label misdescribed the data (DR-006 correction section).
2. **Minimal geometric / abstract** (`minimal-geometric`) — flat shapes, restrained palettes, negative space
3. **Ukiyo-e woodblock** (`ukiyo-e`) — Japanese woodblock prints; **replaces the Phase 0 graffiti candidate** because graffiti photography is generally artist-copyrighted while ukiyo-e has large explicit CC0/PD institutional supply (see `docs/decisions/DR-006-dataset-styles-and-sourcing.md`)

**Target size:** ≈50 items per style (40–60; ~150 total + holdout), approved 2026-07-27.

## Licensing policy

- Allowed licences: **public domain, CC0, project-original** (self-created; generator config + seed recorded). Nothing else enters the manifest.
- Primary sources: open-access museum/archive collections with item-level licence statements (retro-poster, ukiyo-e); seeded programmatic self-generation (minimal-geometric). Stock-photo "free" sites, scraping, and AI-generated seed imagery are rejected (DR-006).
- Every item's licence and permitted use is recorded **before** it may enter a training split.
- The concrete source registry (institution, URL, licence statement) requires explicit human approval before any download; borderline items are batched for review.

## Inclusion, exclusion, and privacy rules

- **Include only:** decodable PNG/JPG, short side ≥ 512 px, licence in the allowlist, provenance recorded, visually on-style.
- **Exclude:** identifiable living persons, visible brands/logos/trademarks, NSFW content, contemporary artist-attributed works, watermarked images, near-duplicates.
- **Privacy:** no personal data in filenames or metadata; historical artworks only from institutional PD collections.

## Manifest schema (`data/manifests/`)

Every item records: `id`, `filename`, `style`, `caption`, `source`, `author` (where known), `licence`, `collection_date`, `permitted_use`, `width`, `height`, `sha256`, `split` (train/val/holdout), `notes`.

## Pipeline scripts (built in M2, under `ml/dataset/`)

1. Decode validation (reject corrupt/unreadable files)
2. SHA-256 hashing + exact-duplicate detection
3. Near-duplicate detection (perceptual hash) where feasible
4. Resolution and aspect-ratio statistics + minimums
5. Normalization (resize/crop policy for training resolution)
6. Caption tooling (template + manual review)
7. Split assignment (deterministic, seed-fixed)
8. Dataset statistics report (per style: counts, dimensions, licence breakdown)
9. Contact sheets for visual inspection and jury evidence

## Storage rules

Raw dataset is **not committed** (`data/raw/` ignored). Committed: manifests, statistics, contact sheets, and a small set of licence-cleared samples in `data/samples/`. Dataset versions are tagged in manifests (`dataset_version` referenced by the experiment registry).

## Bias and ethics checks (RQ11)

Per style: document source diversity, obvious cultural or representational biases in the collected material, and any content exclusions. Findings and limitations go into the report's ethics chapter — honestly, including unresolved issues.

## Open dataset findings (recorded 2026-07-30; **evidence gathered in M4, mitigation decided in Prototype 4 / M6**)

The original heading read "to be resolved in M4", which was imprecise and is corrected here. **M4
produced the *evidence* on frame and pseudo-text transfer; the dataset *mitigation decision* (a crop
pass versus negative prompting) stays in Prototype 4 (M6), where training evidence will exist.** The
body of finding 1 always said this; the heading did not match it.

Observed while re-inspecting the `retro-poster` contact sheet during the M3 pre-check. Both are recorded as honest findings rather than silently patched, because the mitigation choice needs training evidence:

1. **Framed/matted scans.** Most `retro-poster` items are photographed or scanned with visible black frames and cream mats. A style LoRA could learn the frame as part of the style. Options for M4: a crop pass over the raw material, or accept it and rely on negative prompting — decided with evidence in Prototype 4, not assumed now.
2. **Text-dominated source material.** Display typography is a defining feature of WPA posters, and diffusion models render text poorly. Training on this style therefore risks producing garbled pseudo-lettering. This is a genuine threat to the RQ4/RQ5 style-learning results and must be reported honestly whatever the outcome.

### M4 evidence on both findings (2026-08-01, Prototype 2)

Conditioning is not training, so this bounds the concern rather than settling it — but it is the
first direct evidence, and it is not encouraging for either finding.

Condition **C6** paired **R5** (`DS-0088`, a landscape WPA poster photographed in a dark frame with
large display lettering) with prompt `P1-poster`. Kylian's failure-mode observations:

| method | level | `unwanted_frame` | `pseudo_text` | `background_transfer` |
|---|---|---|---|---|
| img2img | weak | not observed | not observed | not observed |
| img2img | medium / strong | **worse** | **worse** | **worse** |
| ip-adapter | weak | not observed | **worse** | not observed |
| ip-adapter | medium / strong | **worse** | **worse** | **worse** |

**Both frame transfer and pseudo-lettering are confirmed, for both conditioning methods, at medium
influence and above.** Only the weakest settings avoid them, and IP-Adapter already shows pseudo-text
at weak.

A correction to how these findings were framed: **R1 (`DS-0077`) is also a framed, text-dominated
poster scan**, verified by opening the image. R5 is the harder case because it adds landscape
orientation — the one orientation the deck format cannot accommodate — not because it is the only
framed or text-bearing item. The problem is therefore more widespread in `retro-poster` than the
original wording implied, which strengthens the case for a crop pass rather than weakening it.

**The mitigation decision still belongs to Prototype 4 (M6)**, where LoRA training evidence will
show whether a style LoRA actually learns the frame, and whether negative prompting suppresses it.
Evidence: `docs/evidence/EXP-011/`, `docs/evidence/prototype-2/difficult-reference-artefacts.jpg`,
`docs/evidence/EXP-015-scoring/failure-mode-probe.md`.
