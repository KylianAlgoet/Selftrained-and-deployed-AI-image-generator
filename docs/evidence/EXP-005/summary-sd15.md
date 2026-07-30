# EXP-005 aspect-ratio measurements - stable-diffusion-v1-5/stable-diffusion-v1-5 (UNSCORED)

Measured values only - no quality judgement. Peak VRAM is reported three ways:
torch allocator (`allocated`/`reserved`) plus device-level usage, which
additionally includes the CUDA context the allocator cannot see.

| model | track | resolution | tier | ok | fail | median s | min s | max s | peak alloc MiB | peak reserved MiB | peak device MiB | peak RSS MiB | load s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stable-diffusion-v1-5/stable-diffusion-v1-5 | direct-1x1 | 512x512 | 0 | 6 | 0 | 4.111 | 4.068 | 4.143 | 2675.38 | 3246.0 | 4359.5 | 1846.84 | 7.23 |
| stable-diffusion-v1-5/stable-diffusion-v1-5 | direct-1x2 | 512x1024 | 0 | 6 | 0 | 8.962 | 8.909 | 8.996 | 3283.69 | 4356.0 | 5469.5 | 1880.05 | 8.85 |
| stable-diffusion-v1-5/stable-diffusion-v1-5 | direct-1x3 | 512x1536 | 0 | 6 | 0 | 15.244 | 15.139 | 15.342 | 3892.01 | 5470.0 | 6583.5 | 1709.2 | 9.81 |
| stable-diffusion-v1-5/stable-diffusion-v1-5 | square-crop | 170x512 | 0 | 6 | 0 | 4.281 | 4.177 | 4.702 | 2675.38 | 3246.0 | 4359.5 | 1893.23 | 6.14 |
