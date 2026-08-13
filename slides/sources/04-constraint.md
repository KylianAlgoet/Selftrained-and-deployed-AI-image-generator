**{{ facts.device_total_mib }} MiB of VRAM.** One RTX 4060 Laptop GPU.

The shipped stack peaks at **{{ facts.peak_allocated_mib }} MiB** and leaves
**{{ facts.worst_spare_mib }} MiB spare** under real serving — **2.4 % of the card.**

<p class="source">EXP-019b, EXP-032, EXP-034 · experiments/registry.csv · risk R12</p>

## Speaker notes

The number the whole project is built around.

Eight gigabytes — the measured figure the driver reports, not the marketing one. The production
stack, with the base model, one adapter and the reference encoder all resident, peaks just over
five gigabytes and leaves about two hundred megabytes spare while actually serving.

Two point four per cent. It fits, and it does not fit easily. I never call it headroom, because it
is not.

Two consequences, both deliberate. The service runs exactly one worker — a second pipeline does not
fit, so a concurrent request gets a clean refusal instead of a crash. And anything added later has
two hundred megabytes to fit into.

Hold on to this number. It is behind the next three decisions.
