# Prototype 2 monotonicity check

**Question.** Does the median `overall_reference_similarity` increase as the shared
influence level rises? This is controllability condition 3 of four, and the plan
sets the bar at **at least 3 of the 4 style-matched conditions**.

**What this number is.** Cosine similarity of CLIP ViT-H image embeddings between an
output and its reference. It entangles subject, composition, semantics, colour and
style, so it is an **overall reference-image similarity indicator, never a style
score.** Style transfer is judged by the human `style_consistency` dimension.

**Stated limitation.** The CLIP tower used here is the same family IP-Adapter
conditions on, so this indicator is descriptive **within** a method and is not a
neutral referee **between** methods. It orders the levels; the rubric decides.

Levels are ordered by ascending reference influence: none < weak < medium < strong.
For img2img that is the **opposite** of ascending `strength`, which is inverted.

| method | condition | monotone? | median similarity by level |
|---|---|---|---|
| img2img | C1 | yes | weak 0.1252, medium 0.2119, strong 0.4052 |
| img2img | C2 | yes | weak 0.5335, medium 0.7013, strong 0.7472 |
| img2img | C3 | yes | weak 0.3570, medium 0.5776, strong 0.7746 |
| img2img | C4 | yes | weak 0.6246, medium 0.8885, strong 0.9062 |
| img2img | C5 | yes | weak 0.2092, medium 0.3406, strong 0.4662 |
| img2img | C6 | yes | weak 0.1718, medium 0.2665, strong 0.7529 |
| ip-adapter | C1 | yes | none 0.1013, weak 0.2239, medium 0.4017, strong 0.5142 |
| ip-adapter | C2 | yes | none 0.3940, weak 0.5874, medium 0.6682, strong 0.7129 |
| ip-adapter | C3 | yes | none 0.2777, weak 0.5258, medium 0.7532, strong 0.8403 |
| ip-adapter | C4 | yes | none 0.2668, weak 0.5103, medium 0.7424, strong 0.7426 |
| ip-adapter | C5 | yes | weak 0.2737, medium 0.7406, strong 0.8297 |
| ip-adapter | C6 | yes | weak 0.1774, medium 0.3858, strong 0.4845 |
| ip-adapter-plus | C1 | unanswerable | medium 0.3387 |
| ip-adapter-plus | C2 | unanswerable | medium 0.6674 |
| ip-adapter-plus | C3 | unanswerable | medium 0.8298 |
| ip-adapter-plus | C4 | unanswerable | medium 0.6524 |

## Counts

| method | conditions monotone | conditions answerable | bar (>= 3 of 4 style-matched) |
|---|---|---|---|
| img2img | 6 | 6 | met |
| ip-adapter | 6 | 6 | met |
| ip-adapter-plus | 0 | 0 | not applicable - single level measured, so monotonicity is untestable |

`unanswerable` means that condition had fewer than two ordered levels with usable
values. It is reported as an absent answer rather than filled in.

This check orders levels by an automatic indicator only. Whether the ordering is
**visible and useful to a human** is controllability condition 4, and it is settled
by the rubric at the review gate, not here.
