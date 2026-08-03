# Prototype 3 - LoRA training measurements

Physical VRAM: **8187.5 MiB**. Every peak below is stated against it.

| exp | phase | geometry | tier | status | gates | peak alloc MiB | peak device MiB | spare MiB | s/step | wall s |
|---|---|---|---|---|---|---|---|---|---|---|
| EXP-016a | probe-1step | 512x512 | 0 | ok | PASS | 3114.09 | 4267.50 | 3920.0 | 1.93 | 8.58 |
| EXP-016b | probe-10step | 512x512 | 0 | ok | PASS | 3133.40 | 4285.50 | 3902.0 | 0.43 | 8.66 |
| EXP-016 | smoke | 512x512 | 0 | ok | PASS | 3133.40 | 4285.50 | 3902.0 | 0.29 | 91.22 |
| EXP-017a | probe-1step | 512x1536 | 0 | ok | PASS | 5160.96 | 6429.50 | 1758.0 | 2.55 | 8.44 |
| EXP-017b | probe-10step | 512x1536 | 0 | ok | PASS | 5182.58 | 6449.50 | 1738.0 | 1.12 | 16.30 |


## Phase-separated peaks

| exp | geometry | post-load alloc | fwd+bwd peak | optimizer peak | RSS |
|---|---|---|---|---|---|
| EXP-016a | 512x512 | 2066.56 | 3114.09 | 2108.93 | 5329.75 |
| EXP-016b | 512x512 | 2066.56 | 3133.4 | 2115.01 | 5443.76 |
| EXP-016 | 512x512 | 2066.56 | 3133.4 | 2115.01 | 5543.96 |
| EXP-017a | 512x1536 | 2066.56 | 5160.96 | 2112.68 | 5080.38 |
| EXP-017b | 512x1536 | 2066.56 | 5182.58 | 2118.76 | 5027.64 |

## Technical gates

| exp | trainable tensors | parameters | base frozen | grads finite/non-zero | L2 delta | first loss | last loss |
|---|---|---|---|---|---|---|---|
| EXP-016a | 256 | 1594368 | True | True/True | 0.08769079 | 0.064612 | 0.064612 |
| EXP-016b | 256 | 1594368 | True | True/True | 0.41571364 | 0.064612 | 0.012000 |
| EXP-016 | 256 | 1594368 | True | True/True | 3.85734509 | 0.064612 | 0.004257 |
| EXP-017a | 256 | 1594368 | True | True/True | 0.08664978 | 0.050128 | 0.050128 |
| EXP-017b | 256 | 1594368 | True | True/True | 0.48575947 | 0.050128 | 0.016373 |

`loss_decreased` is recorded per run but is deliberately NOT a pass condition: a run
this short on 12 images is far too noisy for the trend to carry weight.

## Saved adapters (outside git)

| exp | bytes | tensors | LoRA keys | unexpected base-model keys | sha256 |
|---|---|---|---|---|---|
| EXP-016a | 6414480 | 256 | 256 | none | `bde521a283230d8e...` |
| EXP-016b | 6414480 | 256 | 256 | none | `8faa9eeeafaa373b...` |
| EXP-016 | 6414480 | 256 | 256 | none | `e76f822bd3b6314a...` |
| EXP-017a | 6414480 | 256 | 256 | none | `9053d846c4d131d2...` |
| EXP-017b | 6414480 | 256 | 256 | none | `e86d9c980026e2be...` |

## Reset boundaries

- **EXP-016a**: reset before component load; reset before step 0 forward/backward; reset before step 0 optimizer step
- **EXP-016b**: reset before component load; reset before step 0 forward/backward; reset before step 0 optimizer step
- **EXP-016**: reset before component load; reset before step 0 forward/backward; reset before step 0 optimizer step
- **EXP-017a**: reset before component load; reset before step 0 forward/backward; reset before step 0 optimizer step
- **EXP-017b**: reset before component load; reset before step 0 forward/backward; reset before step 0 optimizer step
