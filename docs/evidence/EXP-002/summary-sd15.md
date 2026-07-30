# EXP-002 measurements - stable-diffusion-v1-5/stable-diffusion-v1-5

Measured values only - no quality judgement. Peak VRAM is reported three ways:
torch allocator (`allocated`/`reserved`) plus device-level usage, which
additionally includes the CUDA context the allocator cannot see.

| model | track | resolution | tier | ok | fail | median s | min s | max s | peak alloc MiB | peak reserved MiB | peak device MiB | peak RSS MiB | load s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stable-diffusion-v1-5/stable-diffusion-v1-5 | A | 512x512 | 0 | 15 | 0 | 4.069 | 4.037 | 5.169 | 2675.38 | 3246.0 | 4359.5 | 2667.06 | 7.95 |
| stable-diffusion-v1-5/stable-diffusion-v1-5 | probe | 512x768 | 0 | 15 | 0 | 6.811 | 6.557 | 7.15 | 2979.33 | 3864.0 | 4977.5 | 2644.81 | 7.72 |
