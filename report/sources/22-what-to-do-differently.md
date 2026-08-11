# <span class="section-number">22</span> What should be done differently

Six changes, ordered by what each would have bought. Each names the moment it comes from, so it can
be judged against what actually happened rather than as general advice.

## 22.1 Seed every source of randomness on the first day

**Cost of not doing it:** the three production adapters cannot be regenerated. They are artifacts
identified by SHA-256, and if they are lost the production selection is lost with them. Everything
downstream — a manifest, a restore script, runtime verification on every style activation, and a
whole risk entry — exists to manage a consequence that three lines of initialisation code would have
prevented.

**Why it was missed:** determinism was assumed because a generator *was* seeded, for latents, noise
and timesteps. Nobody asked whether anything else drew from a different source. It looked correct for
four milestones because every run passed every gate.

**Differently:** treat "is this deterministic" as a test with an assertion, run at the first training
run, comparing two runs of identical configuration at the weight level. It takes one afternoon.

## 22.2 Run the clean-clone test at the first milestone

**Cost of not doing it:** five real defects sat in the repository for weeks, including an integrity
control that had never once been executed anywhere but its author's machine, and a settings file
documenting five variables nothing reads.

**Why it was missed:** the clean clone was scheduled as a deployment-validation activity, which is
where it conventionally belongs. It is actually a *correctness* activity, and it is cheap.

**Differently:** clone into an empty directory and run the suite at the end of the first milestone
that produces a suite, and repeat it at every milestone boundary. Every defect it found was
environmental, and every one was invisible locally by construction.

## 22.3 Design the image-count experiment to answer the question asked

**Cost of not doing it:** RQ4's count half is inconclusive, and it is the project's only genuinely
unresolved research question.

**Why it happened:** matching the arms on equal *compute* made three training runs affordable inside
the budget. It also meant the 12-image arm saw each image 25 times and the 44-image arm saw each 6.8
times, so set size and repetition moved together and the ordering came out non-monotonic.

The confound was **declared in code before any result existed**, which is why the result is honest
rather than misleading — but honest and uninterpretable is still uninterpretable.

**Differently:** match on epochs and accept the extra GPU time, or state at design time that the
experiment measures set size at fixed compute and is not capable of establishing a minimum count. The
second is cheaper and would have set expectations correctly from the start.

## 22.4 Measure at least one alternative fine-tuning method

**Cost of not doing it:** DR-009 can claim feasibility and not superiority, and §18.2 has to say so
in the limitations. The assignment asked for five methods compared; four were compared on criteria
and never run.

**Why it happened:** a deliberate budget decision. Measuring one method properly was judged more
valuable than measuring three badly, and on a 19-day timeline with 8 GB that was probably right.

**Differently:** run a minimal Textual Inversion arm — it is the cheapest of the four in both memory
and time — on the lead style only, with the same rubric. Even a single measured comparison would move
the claim from "feasible" to "feasible and better than one measured alternative", which is a
materially stronger research position for a small cost.

## 22.5 Write the report in parallel, as planned

**Cost of not doing it:** the report was planned to run alongside the later milestones and did not
start until they were finished, which concentrated the work at the end of the schedule.

**Why it survived:** because the process was documented as it happened. Every decision record,
experiment row and process-log entry was written at the time, so the report is a synthesis of
existing evidence rather than a reconstruction. **That is the only reason writing it at the end was
possible at all** — and it is worth noting that the practice which saved it is the one the assignment
was assessing.

**Differently:** draft each chapter at the close of the milestone that produces its evidence, while
the reasoning is still available and before the numbers need looking up.

## 22.6 Establish the deck geometry from the real target immediately

**Cost of not doing it:** the mismatch between a 1:3 generated decal and a 1:3.902 UV domain was
found in the fifth prototype, four milestones after the geometry was chosen, because the test decals
happened to be 512×2000 — close enough to hide it.

**Why it happened:** the test assets were authored before there was anything to generate, so they
were made at a convenient ratio rather than the ratio the pipeline would eventually produce.

**Differently:** make every placeholder asset match the exact dimensions the real pipeline will
produce, or make it obviously wrong. A placeholder that is nearly right is the worst of the three
options, because it postpones the discovery without preventing it.

## 22.7 What would not be changed

Three practices cost time, looked inefficient, and would be repeated without hesitation.

**Micro-gating before every long run.** No long run ever started from a guess.

**Stopping at human gates with the work finished and nothing concluded.** Twice a milestone ended
with a draft decision record containing no decision. It is the reason the conclusions in §19 are
defensible.

**Preserving failed rows, refuted hypotheses and blocked experiments in the record.** They are the
most informative part of this report, and every one of them was available to be quietly deleted.
