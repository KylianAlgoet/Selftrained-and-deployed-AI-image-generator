# <span class="section-number">5</span> Research questions

## 5.1 Primary question

> **How can a locally fine-tuned diffusion model, conditioned on both a text prompt and a reference
> image, generate skateboard-decal artwork in multiple visually distinct styles with reproducible
> quality on consumer hardware (8 GB VRAM)?**

A working hypothesis was recorded at the same time, and deliberately labelled a hypothesis rather
than a plan:

> A LoRA fine-tune of a pretrained SD 1.5-class diffusion model, trained locally per style (or as one
> multi-style LoRA), combined with an image-conditioning method (img2img, IP-Adapter, or ControlNet),
> will produce acceptable multi-style decal artwork within the hardware and time budget.

It survived, but not untouched. Three of its clauses were settled against expectation: the
multi-style option was built and rejected on evidence (§11.4), img2img was rejected as the primary
conditioning method for a reason nobody anticipated (§11.2), and "reproducible" turned out to mean
two different things for inference and for training (§18.2).

## 5.2 Subquestions and where they stand

Twelve subquestions were registered before any experiment ran, each with a hypothesis, a method and
the prototype expected to answer it.

**Eight are answered within their stated scope: RQ2, RQ3, RQ5, RQ6, RQ8, RQ9, RQ10 and RQ12. Four
are only partially or boundedly answered: RQ1, RQ4, RQ7 and RQ11.** RQ4's image-count component
remains explicitly **inconclusive**.

RQ1 is counted as bounded rather than answered for a specific reason: it asks which method is
*feasible and most effective*. Feasibility is demonstrated; **"most effective" was never established,
because four of the five candidate methods were screened and never measured** (§9.2).

| RQ | question | status | answered by |
|---|---|---|---|
| RQ1 | Which fine-tuning method is feasible and most effective on 8 GB? | **feasibility only** | §9.2 · EXP-016…019 · DR-009 |
| RQ2 | Which pretrained base model is feasible on this hardware? | **answered, two candidates** | §9.1 · EXP-002, EXP-004 · DR-007 |
| RQ3 | How can a legally usable custom dataset be created? | **answered** | §10 · DR-006 |
| RQ4 | How many images per style, and what caption standards? | **INCONCLUSIVE on count** | §11.4 · EXP-024n12/n24 |
| RQ5 | One multi-style LoRA or separate style LoRAs? | **answered** | §11.4 · EXP-030 · DR-010 |
| RQ6 | How should text and reference conditioning be combined? | **answered** | §11.2 · EXP-008…014 · DR-008 |
| RQ7 | Which generation parameters most influence quality? | **partially answered** | §11.2, §11.4 · EXP-008/009/031 |
| RQ8 | How should the deck aspect ratio be handled? | **answered, hypothesis refuted** | §9.1 · EXP-005 · DR-007 |
| RQ9 | How is the decal mapped onto a 3D deck? | **answered** | §11.0 · DR-005, DR-012 |
| RQ10 | How should decals be evaluated objectively? | **answered, with a stated threat** | §6.2 |
| RQ11 | What are the copyright, privacy, bias and ethics constraints? | **partially answered** | §17 |
| RQ12 | What deployment setup is reproducible on this hardware? | **answered** | §16 · DR-014 |

### The four that are bounded

**RQ1 is bounded to feasibility.** See above: the "most effective" half of the question is
unanswered, and DR-009 says so rather than implying a comparison that did not happen.

**RQ4's image-count half is inconclusive.** Training the lead style on 12, 24 and 44 images at equal
compute produced a **non-monotonic** ordering, and **no minimum image count was established**. Two
further limits apply and are not softened: the arms were matched on *compute*, not on epochs, so each
smaller set saw its images far more often (25.0, 12.5 and 6.8 presentations per item respectively);
and the comparison ran on `minimal-geometric` only, so it does not generalise to the other two
styles. The caption half of RQ4 *was* answered, by a blinded A/B (§11.4).

**RQ7 is partially answered.** Reference strength and conditioning scale were swept properly, and
LoRA weight was compared across a matrix. **Rank and learning rate were set, not swept** — rank 8 and
1e-4 were fixed at the smoke-test stage and never varied, so no claim is made about their optimality.

**RQ11 is partially answered.** Licensing, provenance and privacy are settled and enforced. The
memorisation question is not: 0 of 252 outputs were flagged as near-copies of training images, and a
perceptual-hash threshold is a **coarse indicator, not proof** that a model has not memorised
anything.

## 5.3 How the questions were kept honest

Two protocol rules did most of the work.

**A hypothesis that cannot be refuted was rewritten before it was tested.** One style-learning
hypothesis originally read that a trained adapter would be "at least as strong" as a baseline — a
claim equality satisfies, so no result could refute it. It was replaced with four explicit verdict
rules before Phase B ran.

**Results that refuted their own hypothesis were kept.** RQ8 predicted that direct tall generation
would degrade composition and that generate-then-crop would be more reliable. The measurements said
the opposite, and the recorded conclusion says so (§9.1). The same happened to a timing anomaly
initially blamed on thermal throttling, which was tested and ruled out (§12.2).
