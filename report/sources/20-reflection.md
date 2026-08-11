# <span class="section-number">20</span> Reflection

## 20.1 What changed from the original plan

The plan was written on day one and never rewritten; thirteen change-log entries record what
actually happened instead.

**Almost everything finished early**, and the buffer compounded rather than being spent. The viewer
and the dataset both landed on the first day, which let the benchmark start three days early, which
let conditioning start three days early, and so on to a feature freeze brought forward by six days.
Only the testing milestone overran, by about an hour, and it is the one that found five real defects.

**The under-runs were not luck, and two of them changed later estimates.** Training turned out to cost
91 seconds for 300 steps, so the long training run the schedule had budgeted for never existed. The
infrastructure built for early prototypes was reusable to a degree the estimates had not anticipated
— the MVP added no modelling of its own, which is also why its memory behaviour is directly
comparable with experiments from three milestones earlier.

**Two features were added that were not in the plan**, both scoped after using the application rather
than while designing it: real generation progress, and local decal upload. Neither was scope creep in
the harmful sense — both are logged with reasons — and the progress work produced a decision record
and found three defects no test could see.

## 20.2 What failed

**A style did not learn what it was supposed to.** `retro-poster` learned the frames and typography
of its source posters. The uncomfortable part is that this was **predicted before training** — a
border-darkness measurement flagged 35 of 36 items — and the mitigation chosen, captions rather than
cropping, was tested on a different style. It ships as a partial pass because that is what it is.

**A research question did not resolve.** The image-count arms came out non-monotonic. There was a
temptation to present the ordering as a trend; the result is recorded as inconclusive instead, and
the confound that makes it hard to interpret was declared in code before any result existed.

**The reproducibility of training was broken the whole time and nobody noticed for four milestones.**
Every run passed every gate. Losses fell. Adapters loaded and changed output. Nothing looked wrong,
because nothing was wrong except the thing nobody was checking. It was found only when two runs of
the same configuration were compared at the weight level.

**An integrity check had never actually run.** The dataset hash passed on every machine it was ever
tested on — which was one machine. A clean clone failed it immediately.

## 20.3 Decisions that saved the project time

**Procedural deck geometry** removed model sourcing, licensing and UV repair from the first
milestone.

**Micro-gating before long runs** — 1 step, then 10, then 300, each authorising the next from a
measured projection — felt slow and meant no long run ever started from a guess.

**Stopping at human gates with nothing concluded.** Twice the milestone finished its measurements and
stopped, with a draft decision record containing no decision. It is the least efficient-looking
practice in the project and it is what makes the conclusions defensible.

**Building both options instead of arguing for one.** Both texture-fit modes were implemented, each
disclosing its cost numerically, with a test asserting no default was exported so a human had to
choose.

## 20.4 Evidence that changed a decision

Four times the measurement overruled the plan:

- direct tall generation was expected to degrade and was **better** on every axis measured;
- SDXL was expected to be marginal and turned out to be **impossible** at the resolution where it
  wins;
- img2img was expected to be a reasonable low-VRAM default and turned out to **copy its input**;
- a hypothesis about thermal throttling was **tested and refuted** by a hotter card running faster.

The habit underneath all four is that each expectation was written down first, so it could be seen to
be wrong.

## 20.5 Lessons that were expensive

**Check the artefact, not the description of it.** A style was labelled `retro-comic` for days; the
material is silkscreen posters with no comic properties at all. The wrong label had already reached
the prompt kit. It was caught by opening the images. The same lesson recurred when a reference image
described as "the framed one" turned out to be one of two.

**A test that has only ever passed in one place has not passed.** This applies to the dataset hash,
to the local test sweep that passed five times and failed remotely, and — uncomfortably — to any
claim in this report that rests on a single environment.

**Instrument the measurement before trusting it.** A 20× timing spread had an obvious explanation
that was wrong, and the real cause was the measurement design.

## 20.6 On working with an AI assistant

The assistant wrote most of the code and most of the documentation. Three things made that
defensible rather than dangerous, and they are worth stating because none of them is automatic.

**The gates were real.** Every conclusion, score and production selection was the student's, and
twice the milestone stopped with the work finished and nothing decided.

**Plan review caught real errors before execution.** The claim that gradient accumulation would save
memory was wrong, and was corrected by the student before any GPU time was spent on it. A review gate
that had been promised and then bypassed in the same plan was restored. These are not cosmetic
corrections; the first would have produced a measurement of a thing that does not happen.

**The assistant's own output was wrong often enough to matter.** A runner defect, an ambiguous test
selector, a fixture reader that could not parse real code, a reporting bug that presented missing data
as a passed check. The last one is the instructive one: it failed in the project's favour, which is
the direction errors are least likely to be noticed.

**What did not work well:** the assistant is comfortable producing confident prose about work it has
just done, and that is exactly where a reader should be most careful. The counter-measure adopted —
requiring every quantitative claim in this report to resolve against an evidence file at build time —
exists because judgement alone was not a sufficient check.

## 20.7 What would be done differently

**Seed everything on day one.** The reproducibility defect cost the project the ability to regenerate
its own production artifacts, and the fix is three lines. It was not written because determinism was
assumed rather than tested.

**Run the clean-clone test at the first milestone, not the eighth.** It found five defects in an
afternoon, every one of which had existed for weeks.

**Design the image-count experiment for equal epochs, or state up front that it cannot answer the
question asked.** Matching on compute made the comparison affordable and made the result nearly
uninterpretable.

**Measure one alternative fine-tuning method properly**, even a small one. DR-009's honesty about
claiming feasibility rather than superiority is correct, and it is also a consequence of a budget
decision that could have gone differently.

**Start the report earlier.** It was planned to run in parallel from the sixth milestone and did not.
Nothing was lost because the process was documented as it happened — which is the only reason writing
it at the end was possible at all.
