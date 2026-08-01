# EXP-008 measurements - SD 1.5 img2img @ 512x512

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
| img2img | 512x512 | medium | 0.6 | 0 | 12 | 0 | 2.154 | 2.121 | 2.169 | 0.1197 | 2675.38 | 2958.0 | 4071.5 | 2169.54 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x512 | medium | 0.65 | 0 | 12 | 0 | 2.275 | 2.237 | 2.827 | 0.1197 | 2675.38 | 2958.0 | 4071.5 | 2169.72 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x512 | strong | 0.3 | 0 | 12 | 0 | 1.208 | 1.203 | 1.225 | 0.1343 | 2675.38 | 2958.0 | 4071.5 | 2169.64 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x512 | strong | 0.4 | 0 | 12 | 0 | 1.524 | 1.51 | 1.587 | 0.127 | 2675.38 | 2958.0 | 4071.5 | 2171.14 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x512 | strong | 0.45 | 0 | 12 | 0 | 1.627 | 1.614 | 1.745 | 0.1251 | 2675.38 | 2958.0 | 4071.5 | 2169.59 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x512 | weak | 0.75 | 0 | 12 | 0 | 2.548 | 2.512 | 2.637 | 0.1158 | 2675.38 | 2958.0 | 4071.5 | 2169.46 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x512 | weak | 0.85 | 0 | 12 | 0 | 2.862 | 2.847 | 2.883 | 0.1145 | 2675.38 | 2958.0 | 4071.5 | 2169.66 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x512 | weak | 0.9 | 0 | 12 | 0 | 3.021 | 2.99 | 3.109 | 0.1119 | 2675.38 | 2958.0 | 4071.5 | 2194.89 | 10.02 | `img2img@512x512@tier0` |
