<div class="col-text">

- SDXL scored **better** than SD 1.5 on my own rubric, at its native resolution
- Rejected anyway: **10 738 MiB allocated** at 1024², on a {{ facts.device_total_mib }} MiB card
- Windows **spilled into host memory instead of failing.** All thirty runs reported success
- SD 1.5 selected — not because it wins, but because **it is the one that fits at a useful resolution**

</div>
<div class="col-figure">
<figure>
<img src="docs/evidence/prototype-1/cross-model-track-B-seed42.jpg" alt="Track B benchmark grid: SDXL outputs at its designed 1024 by 1024 resolution">
<figcaption><span class="label">Track B — 1024×1024, SDXL's designed resolution.</span> The images the 10 738 MiB measurement came from.
</figcaption>
</figure>
</div>

## Speaker notes

The decision I expected to go the other way, and the one that set the method for everything after.

I benchmarked SD 1.5 against SDXL on identical prompts and seeds. At its designed resolution —
these images — SDXL is better. My own rubric scores say so, and I left that in the report rather
than quietly dropping the comparison.

I rejected it anyway: ten point seven gigabytes allocated at one thousand and twenty-four square,
on an eight gigabyte card.

The important part is that it did not crash. Windows spills GPU memory into system RAM, so all
thirty runs completed and reported success. Judged by exit code, SDXL was fine — and I would have
built the whole project on it and found out in the last month.

That is where the habit came from that I would most want to keep. A successful run is not a run
that fitted. Those are different claims, and modern systems blur them. So every memory figure after
this one is read against the ceiling, never against whether anything crashed.
