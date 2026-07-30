# EXP-004 measurements - stabilityai/stable-diffusion-xl-base-1.0

Measured values only - no quality judgement. Peak VRAM is reported three ways:
torch allocator (`allocated`/`reserved`) plus device-level usage, which
additionally includes the CUDA context the allocator cannot see.

| model | track | resolution | tier | ok | fail | median s | min s | max s | peak alloc MiB | peak reserved MiB | peak device MiB | peak RSS MiB | load s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stabilityai/stable-diffusion-xl-base-1.0 | A | 512x512 | 0 | 15 | 0 | 16.512 | 15.028 | 17.517 | 7859.26 | 9030.0 | 8187.5 | 2309.61 | 229.45 |
| stabilityai/stable-diffusion-xl-base-1.0 | B | 1024x1024 | 0 | 15 | 0 | 118.733 | 118.122 | 127.538 | 10738.08 | 14510.0 | 8187.5 | 6806.57 | 34.7 |
