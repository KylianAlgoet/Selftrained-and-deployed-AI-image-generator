# DR-006: Dataset style set and sourcing strategy

**Date:** 2026-07-27 · **Status:** accepted (style set and target size approved by Kylian in-session)

## Context
M2 must produce a custom training dataset (≥3 visually distinct styles) with documented provenance and permitted usage (RQ3), sized realistically for LoRA training and the deadline (RQ4), under strict licensing rules (risk R3).

## Decision 1 — Style set
The Phase 0 candidate **graffiti/street art is replaced by ukiyo-e woodblock**. Photographs of real graffiti are typically copyrighted by their artists, capping safely usable supply; ukiyo-e has a large, explicitly CC0/PD institutional supply, is visually iconic on skateboard decks, and stays clearly distinct from the other styles. Approved set:

1. **Retro comic / punk poster** (`retro-comic`) — halftone, limited palettes, bold ink
2. **Minimal geometric / abstract** (`minimal-geometric`) — flat shapes, restrained palettes
3. **Ukiyo-e woodblock** (`ukiyo-e`) — Japanese prints

## Decision 2 — Sourcing strategies (compared)

| Strategy | Verdict | Reason |
|---|---|---|
| Open-access museum/archive collections (item-level CC0/PD) | **Primary** for retro-comic and ukiyo-e | Explicit licences, institutional provenance, stable URLs |
| Programmatic self-generation (seeded scripts) | **Primary** for minimal-geometric | Total licence control, deterministic, reproducible from config+seed |
| "Free" stock sites (Unsplash/Pexels) | Rejected | Licences restrict redistribution/dataset compilation |
| Scraping art/social platforms | Rejected | Forbidden by project rules; unverifiable rights |
| AI-generated seed imagery | Rejected | Provenance ambiguity; undermines the self-trained-model narrative |

## Decision 3 — Target size
≈50 items per style (40–60; ~150 total plus holdout), approved by Kylian; enough for the multi-style vs. per-style LoRA comparison (RQ5) within the M2 window.

## Consequences
- `docs/04-dataset-methodology.md` updated (style swap, counts, rules).
- Concrete source registry (institution, URL, licence statement) still requires **explicit approval before any download** (separate gate, Prompt 3 pause rule).
- Risk R3 mitigation strengthened: every source is institutionally licensed or project-original.
