# EXP-012 measurements - IP-Adapter-Plus (SD 1.5) @ 512x512

Measured values only - no quality judgement, no method selection.

Reading rules that travel with these numbers:

- `peak alloc MiB` is **per run** and is the figure used to compare influence levels.
- `peak reserved MiB` and `peak device MiB` are **process-level high-water marks**.
  Influence levels share one OS process per (method, resolution, tier), so these two
  columns must not be compared between levels. Comparison **between methods** remains
  valid, because each method runs in its own fresh process.
- img2img executes `int(steps x strength)` denoising steps, so a stronger reference is
  also faster. `s/eff step` is therefore reported alongside wall-clock seconds.
- img2img `strength` is **inverted**: a lower value means a stronger reference.

| method | resolution | level | param | tier | ok | fail | median s | min s | max s | s/eff step | peak alloc MiB | peak reserved MiB | peak device MiB | peak RSS MiB | load s | process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ip-adapter-plus | 512x512 | medium | 0.55 | 0 | 12 | 0 | 3.436 | 3.402 | 3.499 | 0.1145 | 3978.87 | 4634.0 | 5747.5 | 3082.38 | 19.37 | `ip-adapter-plus@512x512@tier0` |
