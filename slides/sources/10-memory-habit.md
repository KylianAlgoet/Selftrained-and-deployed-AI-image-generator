**A successful run is not a run that fitted.**

Read every memory figure **against the ceiling**, never against whether the process survived.

<p class="source">EXP-005 · the measurement-methodology correction · report §19.3</p>

## Speaker notes

Fifteen seconds on the habit that came out of that, because it is the most transferable thing I
learned.

A successful run is not a run that fitted. Those are different claims, and modern systems blur
them: the driver spills, the allocator caches, the OS swaps, and the process exits zero throughout.

So from that experiment on, every memory number is read against the eight gigabyte ceiling rather
than against whether anything crashed. That is why I can tell you the margin is two hundred
megabytes instead of telling you it works on my machine.

It also cost me one measurement error — the caching allocator holds its pool across a reset, which
contaminated an experiment until I switched to one configuration per process. Documented rather
than quietly fixed, because the wrong method produced perfectly plausible numbers.
