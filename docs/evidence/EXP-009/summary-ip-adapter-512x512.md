# EXP-009 measurements - IP-Adapter (base, SD 1.5) @ 512x512

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
| ip-adapter | 512x512 | medium | 0.55 | 0 | 12 | 0 | 3.338 | 3.322 | 3.358 | 0.1113 | 3924.07 | 4582.0 | 5695.5 | 2028.51 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | medium | 0.6 | 0 | 12 | 0 | 3.514 | 3.382 | 4.12 | 0.1171 | 3924.07 | 4582.0 | 5695.5 | 2214.54 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | strong | 0.8 | 0 | 12 | 0 | 3.417 | 3.379 | 4.261 | 0.1139 | 3924.07 | 4582.0 | 5695.5 | 2203.8 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | strong | 0.85 | 0 | 12 | 0 | 3.343 | 3.327 | 3.726 | 0.1114 | 3924.07 | 4582.0 | 5695.5 | 2028.67 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | strong | 1.0 | 0 | 12 | 0 | 3.399 | 3.357 | 3.785 | 0.1133 | 3924.07 | 4582.0 | 5695.5 | 2027.77 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | weak | 0.2 | 0 | 12 | 0 | 3.391 | 3.357 | 3.473 | 0.113 | 3924.07 | 4582.0 | 5695.5 | 2378.93 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | weak | 0.25 | 0 | 12 | 0 | 3.354 | 3.328 | 3.456 | 0.1118 | 3924.07 | 4582.0 | 5695.5 | 2028.05 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | weak | 0.4 | 0 | 12 | 0 | 3.468 | 3.386 | 3.521 | 0.1156 | 3924.07 | 4582.0 | 5695.5 | 2264.34 | 21.7 | `ip-adapter@512x512@tier0` |
