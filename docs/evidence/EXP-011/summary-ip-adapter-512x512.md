# EXP-011 measurements - IP-Adapter (base, SD 1.5) @ 512x512

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
| ip-adapter | 512x512 | medium | 0.55 | 0 | 6 | 0 | 3.444 | 3.388 | 3.486 | 0.1148 | 3924.07 | 4582.0 | 5695.5 | 3039.3 | 14.12 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | strong | 0.85 | 0 | 6 | 0 | 3.428 | 3.409 | 3.732 | 0.1143 | 3924.07 | 4582.0 | 5695.5 | 3039.73 | 14.12 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | weak | 0.25 | 0 | 6 | 0 | 3.464 | 3.428 | 3.628 | 0.1155 | 3924.07 | 4582.0 | 5695.5 | 3038.98 | 14.12 | `ip-adapter@512x512@tier0` |
