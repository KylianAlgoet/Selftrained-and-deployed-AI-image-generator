# <span class="section-number">16</span> Deployment and reproducibility

## 16.1 The decision

Three options were compared (DR-014):

| option | verdict |
|---|---|
| **A — native local, two processes, plus backup demo assets** | **selected** |
| B — Docker Compose with GPU passthrough | **screened out, not benchmarked** |
| C — cloud GPU | rejected |

**Docker was screened out rather than measured, and the record says so.** Its GPU overhead against
the {{ facts.worst_spare_mib }} MiB margin is unmeasured, measuring it would have cost generations
the closed budget did not have, GPU passthrough was never verified on this machine, and the container
toolkit is not installed. It would also not solve the actual reproducibility problem, which is the
three unregenerable adapter files, not the Python environment.

**Cloud GPU was rejected on a research ground as much as a cost one:** different hardware would
invalidate every VRAM figure in this report.

Running it is three commands — a preflight with ten checks including the three adapter hashes, a
start script, and a stop script that stops the process **tree** rather than a recorded PID, because
`--workers 1` starts two processes (§12.5).

## 16.2 The clean-clone test

The runbook was validated by cloning the repository into a fresh directory, building the environment
from scratch, and running the system — eighteen ordered steps with real output recorded.

**It failed, and the failure was the point.** A frozen dataset hash did not match, because it had
been recorded from a CRLF working copy while Git stores LF. An integrity control had never once been
tested against a fresh checkout (§12.5).

The fix was **taken to the student rather than applied**, because repointing that constant would have
moved a fingerprint that an earlier milestone's evidence cites as unchanged. The chosen resolution
separates the M6 *identifier* from the *content check*, and a test now asserts the two stay distinct.

After the fix, the clean clone completed and produced **one authorised real generation**, which
reproduced the earlier output **byte for byte** — SHA-256 `{{ facts.output_sha256 }}`,
{{ facts.output_bytes }} bytes, three days later in a freshly built environment.

**Inference is deterministic and portable given a fixed adapter.** Training is not (§12.4). Both
statements are true and neither weakens the other.

## 16.3 The weights problem

The three production adapters are **{{ facts.adapter_bytes }} bytes each** and are **not in Git** —
model weights are never committed. They also **cannot be regenerated**, because training is not
reproducible from seed.

This makes them the project's single point of failure, and it is mitigated structurally rather than
by care:

| control | what it does |
|---|---|
| weights manifest | records exact path, byte size and SHA-256 per adapter; **asserted against the code by a test** so it cannot drift |
| `verify-weights.ps1` | restores from a **parameterised** source and verifies, failing loudly per style |
| runtime verification | the service re-verifies each adapter's SHA-256 **on every style activation**, not once at startup |

The integrity gate was proved in both directions — 3 of 3 failing before restore, 3 of 3 passing
after — and it was **never proved by damaging a real adapter**. A corrupted *copy* was used, because
the originals cannot be regenerated.

<div class="callout">
<span class="callout__label">The residual risk, stated plainly</span>
The clean-clone test restored the weights <strong>from the working repository, not from the external
backup drive</strong>, which was unavailable. The restore <em>mechanism</em> is validated; the
<strong>external backup itself is not</strong>. If the working machine and that drive are both lost,
the production selection is lost with them.
</div>

## 16.4 Demonstration readiness

A four-minute timed demo script exists, built around talking over the generation rather than padding
it, and front-loading the cold-load wait as explanation rather than silence.

The backup plan has four rungs, each executable in under thirty seconds. The load-bearing one is that
**Upload your own decal needs no GPU, no model and no server round trip**, so a dead pipeline costs
about forty seconds of a four-minute talk and the entire 3D section runs unchanged. That is also why
the feature appears at 2:30 in the main script: using it as a fallback then reads as continuity
rather than retreat.

Backup assets are **existing validated material only** — real generated decals, the interface
screenshots, the deck and clean-clone captures — assembled by a script into a git-ignored directory
with a committed manifest.

**One asset does not exist: a screen recording.** It is listed as missing rather than assumed,
because it must be a recording of a real session or it does not exist. A machine failure with no
projector is **not mitigated**; that falls to slides.

## 16.5 What "reproducible" means here, precisely

The word is used in this report in three different senses, and conflating them would overstate the
result.

| sense | status |
|---|---|
| **The environment** reproduces from a clean clone | **yes** — validated, 18 steps, real output |
| **Inference** reproduces byte-for-byte given a fixed adapter | **yes** — measured across machines and days |
| **Training** reproduces from a recorded seed | **no** — the adapters are artifacts, not recipes |

The third is a genuine limitation of this project's research output, and §18.2 carries it rather than
letting the first two stand for it.
