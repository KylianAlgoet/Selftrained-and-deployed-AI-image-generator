# EXP-013 measurements - SD 1.5 img2img @ 512x1536

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
| img2img | 512x1536 | medium | 0.65 | 0 | 9 | 0 | 7.98 | 7.898 | 8.051 | 0.42 | 3892.01 | 4648.0 | 5761.5 | 2212.84 | 10.79 | `img2img@512x1536@tier0` |
