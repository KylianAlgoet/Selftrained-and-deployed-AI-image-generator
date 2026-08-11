# <span class="section-number">12</span> Failed and blocked experiments

Failures are reported here as results, with the same detail as successes. Several of them changed the
project's method more than any successful run did.

## 12.1 Blocked: three sources became unavailable mid-project

| what | how it failed | what was done |
|---|---|---|
| Digital Comic Museum | Cloudflare gating | share shifted to an already-approved source |
| Art Institute of Chicago | image CDN returned 403 | share shifted to an already-approved source |
| **SD 2.1 base** | **HTTP 401 — repository gating** | escalated to the student; two candidates used |

The base-model block is the consequential one. Two sibling repositories from the same organisation
also returned 401 while SDXL returned 200, which identified it as deliberate gating rather than an
outage.

**Nothing was substituted without approval.** The student was asked and chose to proceed with two
candidates. Three alternatives were declined and recorded, including an ungated community mirror
rejected because its fidelity to the original cannot be verified while the original is gated.

**The cost is permanent and is carried into the limitations:** the base-model decision rests on two
measured candidates rather than three, and that candidate cannot be reproduced today without
authentication.

This pattern recurred often enough to be logged as a risk in its own right — third-party hosting
becoming unavailable mid-project — and the mitigation adopted afterwards was to pin immutable commit
hashes for every model actually used, and to verify availability at the moment of use rather than
assume it.

## 12.2 The measurement that was contaminated, and the wrong explanation for it

An early aspect-ratio experiment produced a **20× timing spread for provably identical work**: one
strategy took 7.96 s where a later run of the same work took 4.10 s.

**The first hypothesis was thermal throttling. It was tested and ruled out** — a hotter, more
throttled card ran the same work *faster*. The actual cause was in-process CUDA caching-allocator
state: all four geometries had shared one process.

Re-running one configuration per fresh process cut the timing spread roughly twentyfold, and
**one-configuration-per-process became the measurement rule for the rest of the project** (§6.2).
Every VRAM and latency figure in this report depends on that correction.

This is recorded as a failure because the first set of numbers was wrong and was published to the
process log before the cause was found.

## 12.3 Defects found in the project's own tooling

Four are worth reporting, because each would have produced a plausible but false result.

**An experiment runner crashed after loading the full stack.** The combined-stack experiment's own
runner unpacked one value from a function returning two. The failed row is **preserved in the
evidence with `status: failed`** rather than deleted, and it still records that the full stack loaded
at 3 308.33 MiB before failing in preprocessing. The defect was in the experiment, not in the stack.

**Twenty-four duplicate generations were biasing a diversity indicator.** Two blocks of the final
matrix overlapped at one weight. The outputs were byte-identical, so each put a self-pair into a
diversity cell and pulled it toward zero. The plan and the diversity pass were fixed and guarded by a
test; **the matrix was not regenerated**, because its evidence is a valid superset of the fixed plan,
and both fingerprints are recorded so the difference is inspectable.

**A trigger-token design was rejected against the live tokenizer before any GPU time was spent.** The
student-approved plan's tokens split into four pieces, lost their shared prefix, or collided with
words already in the caption corpus. Measured against the actual tokenizer, not assumed.

**A reporting bug presented missing data as a passed check.** Found in the analysis code, in the
project's own favour, and corrected.

## 12.4 The reproducibility defect: training is not bit-reproducible

**Diagnosed during style learning, and it is the project's most consequential internal failure.**

The adapter is created with Gaussian initialisation drawing from the **global** torch RNG. The runner
seeds a generator for the sampled latent, the noise and the timesteps — but never the global RNG. So
every process starts from a different adapter.

It was **measured rather than inferred**. Same-step adapters from two runs differ by an L2 of about
158 against a weight norm of about 112 — a ratio of √2, the signature of two independent draws —
while training itself moves the weights by about 5.

**The impact is bounded, and the bound was checked.** Each run's gates are self-contained. The data
pipeline **is** deterministic and was verified so: a 600-step run's first 300 draws were byte-identical
to the pilot's recorded sample-order hash. Every comparison was scored on generated images from arms
differing in one recorded variable, never on weight equality.

**It was deliberately not fixed mid-milestone.** Seeding the initialisation would have altered every
run the first gate's arms were compared against. The fix is forward-only, and the historical evidence
stands unchanged.

**The consequence is permanent:** the three production adapters are authoritative **as files, by
SHA-256, not as a recipe**. They cannot be regenerated. If they are lost, the production selection is
lost with them (§16.3).

## 12.5 Five defects that only a clean clone could find

The testing milestone was scoped to verify and instead discovered. Every one of these was invisible
on the machine the code was written on.

1. **A frozen dataset hash that had only ever passed locally.** The recorded digest was taken from a
   CRLF working copy while Git stores LF, so **an integrity control had never once been tested against
   a fresh checkout.** The fix separated the identifier from the content check, because repointing
   the original would have moved a fingerprint that earlier evidence cites as unchanged.
2. **A settings file documenting five variables nothing reads**, two implying upload security rules
   were configurable when they are not.
3. **A stale environment audit** — Node 20.18.0 recorded, 24.18.0 actual, with no record of when it
   changed.
4. **A requirements file claiming a pin it did not make.** Four "pinned" lines were comments.
5. **`--workers 1` starts two processes**, a supervisor and a worker, so the health endpoint reports
   a process ID the launcher never recorded and a naive stop strands the worker holding the port.

The first is the most instructive finding in the project. **Nothing in the risk register anticipated
"the check itself is wrong."** A clean-clone test is now the control for that class of defect (§16.2).

## 12.6 The continuous-integration failure, and what it cost to fix

The first remote run failed one browser scenario that passed locally: a camera-preservation test
timed out after 300 000 ms on the runner.

**It took five runs.** The scenario was rewritten twice — screenshot comparison, then structural with
host-side polling, then structural, in-page and frame-counted — and **passed remotely on its first
attempt in 40.2 s**. Two defects in that work were found on the way, one of them caught by a unit
test before it reached the runner: an equality rule for a camera that damping means never comes
exactly to rest, and a drift tolerance wide enough to swallow an entire change of viewpoint.

**The application was never changed.** Both rewrites were of the *measurement*.

The remaining instability was the runner itself. Failures moved between runs — 1 failure, then 3,
then 6, and a *different* six — with a 22× swing on identical code. A trace showed a single mocked
response taking 12.78 s against a 10 s expectation, and 59.1 s of a 60 s budget consumed before the
assertion under test began. Three neighbouring scenarios with identical setup completed in 5.6, 8.0
and 9.1 s while the same code path took over two minutes in between.

**Retries alone cannot fix a stall that outlasts a retry cycle**, and the evidence shows exactly that:
one scenario failed all three attempts inside a single stall window while another's retry landed
outside it.

CI budgets were raised for the runner only, on the traced evidence rather than by taste, and local
budgets were deliberately left alone so the suite keeps its performance signal.

**How the resulting green must be read**, and this report states it rather than claiming a clean
pass:

- a green run also occurred under the **old** budgets, so the green cannot be attributed to the budget
  change;
- the **per-scenario retry counts of the final green retry-enabled run are unknown, not zero** — the
  collapsed log did not carry them;
- **a green under two retries and a 180 s budget is weaker evidence than a first-attempt green under
  60 s.**

What stands without qualification is the camera scenario's **first-attempt 40.2 s remote pass, before
any budget was raised**.

**The raised budget is not described as a fix.** The stall is real and unexplained, and a budget that
lets a slow environment finish also costs the suite its ability to detect a genuine performance
regression.

## 12.7 The lesson these share

Three of the six subsections above are defects in verification rather than in the product: a
contaminated measurement, an integrity check that had never run anywhere but its author's machine,
and a test that measured the wrong thing twice.

**A green local suite is not evidence about a different environment, and this project proved it
twice** — once when a hash passed everywhere except a fresh clone, and once when a full local sweep
of every gate passed five times over and still failed remotely.
