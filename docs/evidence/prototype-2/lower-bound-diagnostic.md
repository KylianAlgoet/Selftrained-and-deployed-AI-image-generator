# EXP-010 lower-bound equivalence diagnostic

**This is a diagnostic, and it is worded as one.** Controllability condition 1 says
that at minimum influence the output should be equivalent to the text-only baseline.
Equivalence is established in this order: exact `output_sha256` match, and if the
hashes differ, documented pixel and perceptual similarity plus visual inspection.

**Differing PNG hashes alone do not fail this condition.** Loading IP-Adapter replaces
attention processors and may alter the execution graph even at scale 0.0. Exact
equality is a strong positive result, never a promise.

## Comparison A - IP-Adapter at scale 0.0 vs the text-only baseline

| condition | seed | baseline sha256 | scale-0.0 sha256 | identical |
|---|---|---|---|---|
| C1 | 42 | `cee27050f45b5ab6...` | `cee27050f45b5ab6...` | **yes** |
| C1 | 1337 | `3700558a0617e3ae...` | `3700558a0617e3ae...` | **yes** |
| C1 | 2026 | `bdd8c131c8b17a9d...` | `bdd8c131c8b17a9d...` | **yes** |
| C2 | 42 | `f003da95ec7cb646...` | `f003da95ec7cb646...` | **yes** |
| C2 | 1337 | `1ff00b4e4febfc9b...` | `1ff00b4e4febfc9b...` | **yes** |
| C2 | 2026 | `fe73e9ca27613198...` | `fe73e9ca27613198...` | **yes** |
| C3 | 42 | `7f65ab15a171c3cc...` | `7f65ab15a171c3cc...` | **yes** |
| C3 | 1337 | `e3a150b2f5ad2b98...` | `e3a150b2f5ad2b98...` | **yes** |
| C3 | 2026 | `b9f0ce46bea516e1...` | `b9f0ce46bea516e1...` | **yes** |
| C4 | 42 | `508187805990d2be...` | `508187805990d2be...` | **yes** |
| C4 | 1337 | `8c12c88af5d948a0...` | `8c12c88af5d948a0...` | **yes** |
| C4 | 2026 | `f9a56e953419233e...` | `f9a56e953419233e...` | **yes** |

**12 of 12 pairs are byte-identical.**

Every pair matched exactly. That is a strong positive result: at scale 0.0 the
IP-Adapter cross-attention path contributes nothing, and the method's lower bound
is the text-only baseline exactly rather than approximately.

## Comparison B - this milestone's text-only baseline vs Prototype 1 EXP-002

The frozen kit means Prototype 1's EXP-002 rows at 512x512, seeds 42/1337/2026,
prompts P1-P4 *should* reproduce as this milestone's baseline. Tested, not promised.

| prompt | seed | EXP-002 sha256 | EXP-010 sha256 | identical |
|---|---|---|---|---|
| P1-poster | 42 | `cee27050f45b5ab6...` | `cee27050f45b5ab6...` | **yes** |
| P1-poster | 1337 | `3700558a0617e3ae...` | `3700558a0617e3ae...` | **yes** |
| P1-poster | 2026 | `bdd8c131c8b17a9d...` | `bdd8c131c8b17a9d...` | **yes** |
| P2-geo | 42 | `f003da95ec7cb646...` | `f003da95ec7cb646...` | **yes** |
| P2-geo | 1337 | `1ff00b4e4febfc9b...` | `1ff00b4e4febfc9b...` | **yes** |
| P2-geo | 2026 | `fe73e9ca27613198...` | `fe73e9ca27613198...` | **yes** |
| P3-ukiyo | 42 | `7f65ab15a171c3cc...` | `7f65ab15a171c3cc...` | **yes** |
| P3-ukiyo | 1337 | `e3a150b2f5ad2b98...` | `e3a150b2f5ad2b98...` | **yes** |
| P3-ukiyo | 2026 | `b9f0ce46bea516e1...` | `b9f0ce46bea516e1...` | **yes** |
| P4-deck | 42 | `508187805990d2be...` | `508187805990d2be...` | **yes** |
| P4-deck | 1337 | `8c12c88af5d948a0...` | `8c12c88af5d948a0...` | **yes** |
| P4-deck | 2026 | `f9a56e953419233e...` | `f9a56e953419233e...` | **yes** |

**12 of 12 pairs are byte-identical across milestones.**

This is a cross-milestone repeatability result: the same pinned model, frozen
prompt kit, scheduler, seed and geometry reproduce the same bytes days apart on
the same machine. It also confirms the M4 baseline is the M3 baseline, so the
two milestones' figures are directly comparable.
