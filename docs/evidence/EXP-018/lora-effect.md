# EXP-018 - LoRA load-and-generate effect (Phase 2, offline CPU)

CLIP encoder loaded on CPU in 0.59s. This workload ran in its own
process after all generation finished, so it enters no GPU VRAM or latency figure.

## Lower-bound diagnostic - adapter loaded at weight 0.0

**4 of 4 outputs are byte-identical to the no-adapter baseline.**

This is a DIAGNOSTIC, not a pass condition. Byte equality is the strongest
available positive result, but divergence would not have failed the milestone:
loading an inactive adapter can legitimately change the execution graph or the
numerical path even when it contributes nothing.

| case | seed | identical | mean abs diff | changed px | dHash | CLIP cos |
|---|---|---|---|---|---|---|
| V1-target-style | 42 | True | 0.0 | 0.0 | 0 | 1.0 |
| V1-target-style | 1337 | True | 0.0 | 0.0 | 0 | 1.0 |
| V2-control | 42 | True | 0.0 | 0.0 | 0 | 1.0 |
| V2-control | 1337 | True | 0.0 | 0.0 | 0 | 1.0 |

## Changed-output test - adapter loaded at weight 1.0

**4 of 4 outputs changed beyond the pre-declared noise floor.**

Thresholds declared before reading any result: mean absolute pixel difference
>= 0.5 on the 0-255 scale AND >= 1% of
subpixels differing. A differing PNG SHA alone was never treated as sufficient.

**No visual-quality claim is made here.** Whether the change is an improvement is
Prototype 4's question, judged by a human against the rubric.

| case | seed | sha differs | mean abs diff | changed px | dHash | CLIP cos | beyond noise |
|---|---|---|---|---|---|---|---|
| V1-target-style | 42 | True | 66.330776 | 0.99906 | 28 | 0.713815 | True |
| V1-target-style | 1337 | True | 51.890769 | 0.994462 | 20 | 0.724695 | True |
| V2-control | 42 | True | 57.720755 | 0.993874 | 24 | 0.646657 | True |
| V2-control | 1337 | True | 53.262669 | 0.992034 | 20 | 0.479559 | True |

## Reading the CLIP column honestly

The cosine is a descriptive indicator, not a referee. It entangles subject,
composition, colour and style, and it uses the same CLIP family the project
conditions with elsewhere. It supports the pixel and hash evidence; it does not
replace the human rubric, which Prototype 3 deliberately does not invoke.
