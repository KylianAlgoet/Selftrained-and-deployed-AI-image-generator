# Dataset methodology

**Created:** 2026-07-27 · **Updated:** 2026-07-27 (M2: final style set per DR-006) · Answers RQ3/RQ4/RQ11.

## Final style set (DR-006, approved by Kylian 2026-07-27)

1. **Retro comic / punk poster** (`retro-comic`) — halftone, limited palettes, grain, high contrast, bold ink
2. **Minimal geometric / abstract** (`minimal-geometric`) — flat shapes, restrained palettes, negative space
3. **Ukiyo-e woodblock** (`ukiyo-e`) — Japanese woodblock prints; **replaces the Phase 0 graffiti candidate** because graffiti photography is generally artist-copyrighted while ukiyo-e has large explicit CC0/PD institutional supply (see `docs/decisions/DR-006-dataset-styles-and-sourcing.md`)

**Target size:** ≈50 items per style (40–60; ~150 total + holdout), approved 2026-07-27.

## Licensing policy

- Allowed licences: **public domain, CC0, project-original** (self-created; generator config + seed recorded). Nothing else enters the manifest.
- Primary sources: open-access museum/archive collections with item-level licence statements (retro-comic, ukiyo-e); seeded programmatic self-generation (minimal-geometric). Stock-photo "free" sites, scraping, and AI-generated seed imagery are rejected (DR-006).
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
