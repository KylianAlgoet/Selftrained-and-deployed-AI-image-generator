# DR-006: Dataset style set and sourcing strategy

**Date:** 2026-07-27 · **Status:** accepted; **amended 2026-07-30** — style 1 relabelled `retro-comic` → `retro-poster` (see "Correction 2026-07-30" at the end; the original decision text below is preserved unchanged)

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

---

## Correction 2026-07-30 — style 1 relabelled `retro-comic` → `retro-poster`

**Type:** terminology and schema correction. **Found by:** Kylian, during the M3 (Prototype 1) pre-check. **Original decision text above is preserved as written; this section records the correction.**

### Problem

Style 1 was named `retro-comic` ("Retro comic / punk poster", described as "halftone, limited palettes, bold ink"). Re-inspection of `docs/evidence/dataset-v1/contact-sheet-retro-poster.jpg` and all 41 manifest rows shows the accepted material is **Library of Congress WPA / Federal Theatre Project silkscreen theatre posters** — "Carmen", "Alien Corn", "The Chocolate Soldier", "Counsellor at Law", "The Amazing Dr. Clitterhouse", "Dracula", "Day Is Darkness". Every row carries `notes = "Library of Congress WPA posters collection"`.

Actual visual signature: **flat silkscreen colour fields, limited palettes, Art Deco/Moderne figures, dominant display typography**. The material contains **no halftone dots, no comic panels, no speech balloons, no ink-outlined comic figures, and no sequential art**. The label described a style the dataset does not contain.

### Why it mattered beyond naming

The inaccurate label had already propagated into the draft M3 benchmark prompt kit, which asked for *"halftone shading and bold ink outlines"* — i.e. the frozen evaluation kit would have prompted for a style absent from the training data, invalidating every later LoRA comparison that uses that kit as its pre-training baseline. This is why the correction was made a hard gate before any M3 experiment.

### Decision

- Identifier: **`retro-poster`** — chosen over `wpa-poster` because it stays style-descriptive and UI-safe; precise provenance belongs in the manifest, methodology, and this record, not in a future UI dropdown value.
- Caption style phrase: `"retro comic poster style"` → **`"retro silkscreen poster style"`** (silkscreen is factually how WPA posters were produced and is the dominant visual signature).
- **No image was altered, re-collected, or removed to fit either name.** Pixels, SHA-256 values, and item IDs are untouched.

### Verification (real output, 2026-07-30)

Regenerated the manifest and diffed it against the committed version:

```
rows before/after: 148 148
columns that changed: {'style': 41, 'caption': 41}
UNEXPECTED column changes: {}
id mismatches: 0
sha256 identical: True
split identical: True
filename identical: True
splits after: {'train': 124, 'val': 17, 'holdout': 7}
styles after: {'minimal-geometric': 52, 'retro-poster': 41, 'ukiyo-e': 55}
validate_manifest errors: 0
VERDICT: PASS - only style+caption changed
```

`split.py` keys on item ID rather than style, and `retro-poster` occupies the same alphabetical position as `retro-comic`, so IDs and splits were expected to be stable — this was **verified rather than assumed**. `pytest`: 36 passed (34 previous + 2 new regression guards asserting `retro-comic` is absent from `ALLOWED_STYLES` and `STYLE_PHRASES`).

### Consequences

- M2's acceptance criteria are **not** invalidated — three styles remain defined, licence-verified, deduplicated, and split; only the label was imprecise. Issue #3 receives a traceability comment and **stays closed**; M2 was not reopened.
- Two related dataset findings were recorded at the same time for resolution in M4 (framed/matted scans; text-dominated source material) — see `docs/04-dataset-methodology.md`.
