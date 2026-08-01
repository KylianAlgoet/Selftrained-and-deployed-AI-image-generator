# Prototype 2 cross-method measurements (unscored)

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
| img2img | 512x512 | medium | 0.65 | 0 | 19 | 0 | 2.28 | 2.237 | 2.827 | 0.12 | 2675.38 | 2958.0 | 4071.5 | 2712.38 | 14.37 | `img2img@512x512@tier0` |
| img2img | 512x512 | strong | 0.3 | 0 | 12 | 0 | 1.208 | 1.203 | 1.225 | 0.1343 | 2675.38 | 2958.0 | 4071.5 | 2169.64 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x512 | strong | 0.4 | 0 | 19 | 0 | 1.53 | 1.51 | 1.607 | 0.1275 | 2675.38 | 2958.0 | 4071.5 | 2512.51 | 13.51 | `img2img@512x512@tier0` |
| img2img | 512x512 | strong | 0.45 | 0 | 12 | 0 | 1.627 | 1.614 | 1.745 | 0.1251 | 2675.38 | 2958.0 | 4071.5 | 2169.59 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x512 | weak | 0.75 | 0 | 12 | 0 | 2.548 | 2.512 | 2.637 | 0.1158 | 2675.38 | 2958.0 | 4071.5 | 2169.46 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x512 | weak | 0.85 | 0 | 19 | 0 | 2.874 | 2.847 | 3.0 | 0.115 | 2675.38 | 2958.0 | 4071.5 | 2513.2 | 14.03 | `img2img@512x512@tier0` |
| img2img | 512x512 | weak | 0.9 | 0 | 12 | 0 | 3.021 | 2.99 | 3.109 | 0.1119 | 2675.38 | 2958.0 | 4071.5 | 2194.89 | 10.02 | `img2img@512x512@tier0` |
| img2img | 512x1536 | medium | 0.65 | 0 | 9 | 0 | 7.98 | 7.898 | 8.051 | 0.42 | 3892.01 | 4648.0 | 5761.5 | 2212.84 | 10.79 | `img2img@512x1536@tier0` |
| ip-adapter | 512x512 | medium | 0.55 | 0 | 19 | 0 | 3.344 | 3.283 | 3.486 | 0.1115 | 3924.07 | 4582.0 | 5695.5 | 3044.45 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | medium | 0.6 | 0 | 12 | 0 | 3.514 | 3.382 | 4.12 | 0.1171 | 3924.07 | 4582.0 | 5695.5 | 2214.54 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | none | 0.0 | 0 | 12 | 0 | 3.406 | 3.338 | 3.697 | 0.1135 | 3924.07 | 4582.0 | 5695.5 | 3067.75 | 13.42 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | strong | 0.8 | 0 | 12 | 0 | 3.417 | 3.379 | 4.261 | 0.1139 | 3924.07 | 4582.0 | 5695.5 | 2203.8 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | strong | 0.85 | 0 | 19 | 0 | 3.349 | 3.327 | 3.732 | 0.1116 | 3924.07 | 4582.0 | 5695.5 | 3045.29 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | strong | 1.0 | 0 | 12 | 0 | 3.399 | 3.357 | 3.785 | 0.1133 | 3924.07 | 4582.0 | 5695.5 | 2027.77 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | weak | 0.2 | 0 | 12 | 0 | 3.391 | 3.357 | 3.473 | 0.113 | 3924.07 | 4582.0 | 5695.5 | 2378.93 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | weak | 0.25 | 0 | 19 | 0 | 3.404 | 3.328 | 3.628 | 0.1135 | 3924.07 | 4582.0 | 5695.5 | 3038.98 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x512 | weak | 0.4 | 0 | 12 | 0 | 3.468 | 3.386 | 3.521 | 0.1156 | 3924.07 | 4582.0 | 5695.5 | 2264.34 | 21.7 | `ip-adapter@512x512@tier0` |
| ip-adapter | 512x1536 | medium | 0.55 | 0 | 9 | 0 | 12.022 | 11.95 | 12.085 | 0.4007 | 5140.69 | 6852.0 | 7965.5 | 2996.66 | 13.22 | `ip-adapter@512x1536@tier0` |
| ip-adapter-plus | 512x512 | medium | 0.55 | 0 | 12 | 0 | 3.436 | 3.402 | 3.499 | 0.1145 | 3978.87 | 4634.0 | 5747.5 | 3082.38 | 19.37 | `ip-adapter-plus@512x512@tier0` |
| text-only | 512x512 | none |  | 0 | 12 | 0 | 3.248 | 3.22 | 3.302 | 0.1083 | 2675.38 | 3246.0 | 4359.5 | 2473.41 | 10.74 | `text-only@512x512@tier0` |
| text-only | 512x1536 | none |  | 0 | 9 | 0 | 11.837 | 11.713 | 11.92 | 0.3946 | 3892.01 | 5470.0 | 6583.5 | 2762.97 | 11.1 | `text-only@512x1536@tier0` |

## Scope of this table

297 generation rows across EXP-008 to EXP-013. Measurements only: no quality
judgement, no method selection, no recommendation. Those are the reviewer's, supplied
at the human-review gate.

Phase-2 similarity indicators are deliberately **absent** from this table. They live in
`docs/evidence/EXP-014/` and were computed in a separate process after all generation
finished, so that no metric model was ever resident in a process whose VRAM and
latency figures appear above.

Physical VRAM on this GPU is 8187.5 MiB. Windows WDDM spills into host RAM
without raising a CUDA OOM, so any run exceeding it is flagged rather than caught.
