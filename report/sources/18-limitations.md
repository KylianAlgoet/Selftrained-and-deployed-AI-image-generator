# <span class="section-number">18</span> Limitations

Limitations are separated into four classes, because they have different consequences: a product
limitation affects a user, a research limitation affects what may be concluded, a deployment
limitation affects whether the system can run elsewhere, and a validity threat affects whether the
evidence means what it appears to mean.

**Eight of these were approved as limitations at a review gate**, before this report existed, so they
could not be reclassified retroactively to suit the writing.

## 18.1 Product limitations

1. **Cold model loading has no honest percentage.** The pipeline loads on first request and only
   denoising has a real denominator, so loading publishes a stage name and no number (§14.3).
2. **The time estimate is approximate and covers measured denoising only.**
3. **"Finalising" may be visible only briefly** — about a second — and is deliberately not padded.
4. **Prompt adherence can be weaker than style adherence.** A prompt for a futuristic city skyline
   with a skateboarder produced a clearly on-style, usable deck graphic **in which the skyline and
   the skateboarder were not clearly represented.** Strong style conditioning dominates detailed
   content. This is consistent with the measured drop in prompt adherence at step 600 (§11.4) and is
   **not** a frontend defect. It was preserved rather than answered by silently rewriting prompts.
5. **`retro-poster` ships as a PARTIAL PASS.** It learned the frames and display typography of the
   archive posters it was trained on — confirmed, not suspected (§10.4) — and warns on every request.
6. **One generation at a time.** One API process, one worker, one resident pipeline.
7. **No CPU fallback and no container.** Without a GPU and the three adapter files the service
   returns 503 for every style, by design.

## 18.2 Research limitations

1. **RQ4's image-count result is inconclusive.** Non-monotonic ordering, **no minimum image count
   established**, matched on **equal compute rather than equal epochs**, and measured on
   `minimal-geometric` **only**. It does not generalise to the other two styles.
2. **DR-009 selects LoRA on feasibility, not superiority.** From-scratch training, full fine-tuning,
   DreamBooth [5] and Textual Inversion [6] were **screened on criteria and never executed**. No
   claim is made that LoRA is the best of the five.
3. **The base-model decision rests on two measured candidates.** SD 2.1 was gated behind
   authentication (§12.1) and cannot be reproduced today without credentials.
4. **Rank and learning rate were set, not swept.** Rank {{ facts.lora_rank }} and 1e-4 were fixed at
   the smoke-test stage. RQ7 is answered for reference strength and adapter weight only.
5. **Training is not bit-reproducible from its recorded seed (R14).** The three production adapters
   are authoritative **as files, by SHA-256, not as a recipe**, and cannot be regenerated (§12.4).
6. **Zero near-copy flags is not proof of no memorisation.** A perceptual-hash threshold is a coarse
   indicator (§13.5).
7. **One scorer.** All rubric scores are the student's. Fixed anchors, fixed seeds and blinding at
   the first gate limit subjectivity; they do not eliminate it.
8. **The Gate-2 sheets were labelled**, and labelled sheets carry an expectation effect the blinded
   Gate-1 sheets did not. Recorded at the time rather than noticed later.
9. **The caption A/B ran on the lead style, not on the style whose captions were the problem**
   (§10.5).
10. **No long native training run at the deck format was performed.** The 512×1536 training arms are
    feasibility probes of 1 and 10 steps; they establish cost, not style quality.
11. **The similarity indicator uses the same encoder family that IP-Adapter conditions on** [8],
    making it descriptive within a method rather than neutral between methods.

## 18.3 Deployment limitations

1. **The production margin is {{ facts.worst_spare_mib }} MiB** of
   {{ facts.device_total_mib }} MiB — 2.4 % of the device. **This is not comfortable headroom.**
   Anything added to the stack has to fit inside it.
2. **Validated primarily on one GPU**, an RTX 4060 Laptop. The figures in this report are that
   machine's.
3. **Scaling is not a configuration change** (§14.2).
4. **Docker was screened out, never benchmarked.** Its GPU overhead against the margin is unmeasured
   (§16.1).
5. **The external weight backup was never exercised.** The clean clone restored from the working
   repository; the **mechanism** is validated, the **external drive is not** (§16.3).
6. **Three pre-existing high-severity npm advisories** remain, in dev tooling only, deliberately
   unfixed because the remedy moves the whole validated frontend toolchain under a freeze.
7. **Transitive Python versions are unpinned.** The misleading comment was fixed; the versions were
   not constrained, because that is a dependency move.
8. **No screen recording of the demonstration exists.** It is listed as missing rather than assumed,
   because it must be a recording of a real session or it does not exist.
9. **CI depends on an external host for a tokenizer**, so a red build with no defect behind it is
   possible.

## 18.4 Validity threats

These are the limitations that bear on whether the evidence in this report means what it appears to.

1. **A green local suite is not evidence about another environment**, and this project proved it
   twice — once with an integrity hash that had only ever passed locally, once with a full local
   sweep that passed five times and still failed remotely (§12.5, §12.6).
2. **The CI green carries three qualifications** (§12.6): a green run also occurred under the **old**
   budgets; the **per-scenario retry counts of the final green retry-enabled run are unknown, not
   zero**; and a green under two retries with a 180 s budget is **weaker evidence** than a
   first-attempt green under 60 s. Only the camera scenario's first-attempt 40.2 s remote pass, taken
   before any budget rise, stands unqualified.
3. **The raised CI budgets cost the suite a capability.** CI can no longer detect a genuine
   performance regression in that range. The budget is not described anywhere in this report as a
   fix; the stall remains real and unexplained.
4. **Byte-identical repeats are strong evidence of no state residue, not proof of none.**
5. **The residency experiment deliberately breaks the one-configuration-per-process rule**, so its
   figures are **not comparable** with the single-shot experiments — stated in its own record.
6. **The texture-fit decision rests on one reviewer, one decal, one camera**, and is scoped to the
   three production styles at the deck format rather than being a general claim about a 1.3× stretch
   (§14.4).
7. **No automated test loads the model.** A green suite is not evidence that the system generates
   anything (§15.2).
8. **The final matrix contained 24 duplicate generations** that were biasing a diversity indicator.
   Fixed in the plan and guarded by a test; the matrix was **not** regenerated, because its evidence
   is a valid superset of the fixed plan, and both fingerprints are recorded (§12.3).

## 18.5 What follows from these

None of these limitations invalidates the system or the research, and none of them is presented as
fatal. Several of them are the most useful results the project produced: the reproducibility defect
in §18.2.5 is a finding about how LoRA training pipelines silently fail to be deterministic, and the
validity threats in §18.4 are a record of a project repeatedly discovering that its own verification
was weaker than it looked.

**The honest summary is that this system works, on this hardware, within a margin of about 2.4 %, and
that two of its twelve research questions did not resolve.** §19 draws conclusions on that basis and
no wider one.
