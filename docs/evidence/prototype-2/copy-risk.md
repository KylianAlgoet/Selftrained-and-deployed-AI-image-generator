# Prototype 2 copy-risk flags

Threshold: perceptual-hash (dHash) Hamming distance **<= 6**, the
project's existing `NEAR_DUPLICATE_MAX_DISTANCE`, reused unchanged.

**What this is and is not.** dHash distance is model-free and coarse. It is a
**near-copy flag only** - not a measure of style, quality, or influence strength, and
not by itself a finding that copying occurred. A flagged output is a candidate for
human judgement under `originality` and `copy_or_overfitting_risk`. Flagged outputs are
**kept and surfaced, never deleted**: an output that reproduces its reference is a
first-class RQ11 result.

## 6 flagged output(s)

| dHash | experiment | method | condition | reference | level | value | seed | geometry | CLIP similarity |
|---|---|---|---|---|---|---|---|---|---|
| **0** | EXP-013 | img2img | C4 | R4 | medium | 0.65 | 1337 | 512x1536 | 0.891022 |
| **0** | EXP-013 | img2img | C4 | R4 | medium | 0.65 | 2026 | 512x1536 | 0.897787 |
| **1** | EXP-013 | img2img | C4 | R4 | medium | 0.65 | 42 | 512x1536 | 0.86166 |
| **3** | EXP-013 | img2img | C2 | R2 | medium | 0.65 | 42 | 512x1536 | 0.823158 |
| **5** | EXP-013 | img2img | C2 | R2 | medium | 0.65 | 1337 | 512x1536 | 0.810053 |
| **5** | EXP-013 | img2img | C2 | R2 | medium | 0.65 | 2026 | 512x1536 | 0.799198 |

## Where the flags concentrate

- geometries: 512x1536
- methods: img2img
- references: R2, R4

### Median dHash distance to the reference, img2img at the medium level

| geometry | runs | median dHash | minimum |
|---|---|---|---|
| 512x512 | 31 | 27 | 12 |
| 512x1536 | 9 | 5 | 0 |

The same method at the same level behaves very differently at the two geometries. The
mechanism is mechanical and stated as such: **img2img forces the reference into the
output resolution**, so when a reference already matches the output aspect exactly - R2
and R4 are natively 512x1536 and retain 100 % of their area at the deck format - nothing
is cropped away and denoising at `strength=0.65` starts from an essentially intact copy.
At 512x512 the same references are cropped to a third of their area first.

**This concerns the production geometry**, so it is surfaced rather than filed as an
edge case. Whether these outputs actually read as copies is a human judgement: see
`copy-risk-pairs.jpg` and score them under `originality` and `copy_or_overfitting_risk`.
No conclusion about method selection is drawn here.
