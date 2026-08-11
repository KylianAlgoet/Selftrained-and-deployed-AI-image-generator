# <span class="section-number">21</span> Lessons learned

Each lesson below is tied to the moment that produced it. They are ordered by how much they changed
the project's behaviour afterwards.

## 21.1 Technical

**Read memory against the ceiling, not against the exit code.** A model reported thirty successful
runs while allocating 31 % more memory than the card physically holds. No exception was raised and no
escalation triggered, because the operating system spilled into host memory. Every memory figure in
this report is quoted against {{ facts.device_total_mib }} MiB as a direct result (§9.1).

**Separate memory peaks by phase.** Recording post-load, forward/backward and optimizer-step peaks
separately, rather than one process maximum, is what revealed that activations scale with geometry
while optimizer state does not — and therefore that gradient checkpointing was the correct first
escalation and a lower-memory optimizer would have been the wrong move (§9.2).

**One configuration per process.** A shared process gave a 20× timing spread for identical work
through allocator state, and the first explanation offered — thermal throttling — was wrong (§12.2).

**A hoped-for result is a diagnostic, not a pass condition.** An adapter at weight 0.0 producing
byte-identical output is welcome evidence and must not be allowed to fail the experiment, because
loading an inactive adapter can legitimately change the execution graph. Declaring it a diagnostic
before the run is what kept it honest (§9.2).

**A differing hash is not evidence of a meaningful change.** The weight-1.0 arm required a noise
floor declared before any result was read, not merely a different image.

**Verify against the live object, not the call that returned.** Adapter attachment is confirmed by
reading 128 LoRA modules and 16 attention processors back off the UNet, because a call that does not
raise is not evidence that anything attached.

**Gradient accumulation is not a memory tier.** At micro-batch 1 it changes effective batch size, not
peak memory. Caught in plan review before any GPU time was spent, and now enforced by a guard.

## 21.2 Methodological

**Write the threshold down before reading the result.** Noise floors, tolerances and pass conditions
all predate the runs they judge. This is the single practice that most distinguishes the experiments
in this report from a set of demonstrations.

**A hypothesis that equality satisfies cannot be refuted.** One style-learning hypothesis read "at
least as strong as" and was rewritten into four explicit verdict rules before it could be tested.

**Blind first, label second, and hash the scores before unblinding.** The first review gate's score
file was hashed before the blinding map was opened, so "no score was edited afterwards" is checkable.
The second gate had to be labelled — the question required it — and the expectation effect that
introduces is recorded rather than left implicit (§6.3).

**A blank is not a zero.** Twenty-nine unscored cells were excluded from every mean rather than
imputed, and one comparison was left unscored rather than reusing a plausible number from an earlier
milestone.

**Let automated indicators inform and never decide.** They populate no rubric cell and select no
checkpoint, and they live in separate files from human judgement.

**Build both options and decide nothing.** Used at three gates. The version of this that works has a
test asserting no default was exported, so the choice cannot be made by omission.

## 21.3 Reproducibility

**Determinism is not inherited; it is per-source-of-randomness.** Seeding a generator for latents,
noise and timesteps produced a fully deterministic data pipeline and a completely non-reproducible
adapter, because one initialisation drew from the global generator. Everything looked fine for four
milestones (§12.4).

**Pin immutable revisions, and verify availability at the moment of use.** Four separate third-party
sources became unavailable during this project, one of them while the bibliography was being written
(§24.4).

**Some artifacts must be preserved rather than regenerated**, and a system that depends on them needs
a manifest, a restore path and runtime verification — not a note in a README (§16.3).

**Line endings can break an integrity check.** A hash-locked evidence file needed an explicit
attribute to survive checkout on a machine configured differently from its author's.

## 21.4 Testing and CI

**A green local suite is not evidence about a different environment**, and this project proved it
twice in one milestone (§12.5, §12.6).

**Retries cannot help a stall that outlasts a retry cycle.** Three attempts inside one stall window
all failed while another test's retry, landing outside it, passed. Raising the retry count would have
been the obvious wrong move.

**Wait in frames, not milliseconds, when the thing you are waiting for advances per rendered frame.**
A camera test that polled on wall-clock time was making a bet on the frame rate, and lost it on a
GPU-less runner.

**A mocked suite must be pinned to the real contract.** Frozen fixtures are validated against the
real API models by a separate test, so a field rename breaks a test rather than leaving the browser
suite passing against a shape that no longer exists.

**A test count is only evidence if every test earns its place.** Three planned tests were dropped
after checking disproved their premise (§15.7).

## 21.5 Working with AI assistance

**Gates are the mechanism, not good intentions.** The boundary held because milestones stopped with
work finished and nothing concluded, not because anyone remembered to be careful.

**Review the plan, not just the output.** The most valuable corrections in this project were made
before execution: a memory claim that was false, a review gate that had been promised and bypassed in
the same document, and an experiment design that would have answered a different question than the
one asked.

**Errors in your favour are the dangerous ones.** A reporting bug that presented missing data as a
passed check is harder to notice than one that breaks a build.

**Make the claims checkable rather than trusting the prose.** Every quantitative value in this report
is resolved against its evidence file at build time, and a value that has drifted fails the build.
That mechanism exists because careful writing was not a sufficient control.
