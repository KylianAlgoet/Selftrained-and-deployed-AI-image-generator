# Dataset methodology

**Created:** 2026-07-27 · **Status:** methodology defined; collection starts in milestone M2. Answers RQ3/RQ4/RQ11.

## Style candidates (initial, ≥ 3 required)

1. **Graffiti / street art** — bold lettering, spray textures, high saturation
2. **Retro comic / punk poster** — halftone, limited palettes, grain, high contrast
3. **Minimal geometric / abstract** — flat shapes, restrained palettes, negative space

Candidates may be revised during M2 if source availability or licensing forces it (change-log entry required).

## Licensing policy

- Preferred sources: original self-created work, public domain, CC0, and clearly licensed material whose licence permits ML training use.
- **Forbidden:** blind scraping of commercial brands, named artists, or unknown-provenance sources.
- Every item's licence and permitted use is recorded **before** it may enter a training split.
- Licences requiring attribution are honoured in the report and repository.

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
