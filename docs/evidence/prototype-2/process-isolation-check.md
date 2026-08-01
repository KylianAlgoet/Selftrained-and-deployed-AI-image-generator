# Prototype 2 process-isolation check

A fresh OS process is used per **method x adapter variant x output resolution x
memory tier**. Influence levels deliberately **share** a process inside one such
combination, because tensor geometry does not change across levels and reloading
SD 1.5 per level would multiply runtime for no measurement gain.

That sharing is declared rather than hidden, and it is checked rather than trusted.
This carries three obligations:

- `peak_vram_allocated_mb` is **per run** and is the level-to-level figure;
- `peak_vram_reserved_mb` and `peak_device_used_mb` are **process-level high-water
  marks** and are never compared between levels sharing a process (cross-*method*
  comparison stays valid, because each method has its own fresh process);
- the spot check below must pass before the shared-process comparison is accepted.

**Tolerance: 2%, pre-declared in
`ml/inference/reference_schema.py` before any measurement, so it cannot be tuned
to the result.**

Spot-check cell: condition C1, seed 42, 512x512,
tier 0. Each clean run had its own OS process; each shared run came from the
method's sweep process.

| method | level | value | shared-process alloc MiB | clean-process alloc MiB | delta | delta % | within tolerance |
|---|---|---|---|---|---|---|---|
| img2img | weak | 0.85 | 2675.38 | 2675.38 | +0.00 | +0.000 % | yes |
| img2img | medium | 0.65 | 2675.38 | 2675.38 | +0.00 | +0.000 % | yes |
| img2img | strong | 0.4 | 2675.38 | 2675.38 | +0.00 | +0.000 % | yes |
| ip-adapter | weak | 0.25 | 3924.07 | 3924.07 | +0.00 | +0.000 % | yes |
| ip-adapter | medium | 0.55 | 3924.07 | 3924.07 | +0.00 | +0.000 % | yes |
| ip-adapter | strong | 0.85 | 3924.07 | 3924.07 | +0.00 | +0.000 % | yes |

## Verdict

**The shared-process comparison is ACCEPTED.** All 6 spot-check pairs agree
within the pre-declared 2% tolerance, so sharing a process
across influence levels did not distort `peak_vram_allocated_mb`. No method needs
re-running one level per process.

This is a confirmation, and it is recorded as one: the check was worth running
precisely because it could have come out the other way, as EXP-005's allocator
contamination did one milestone earlier.

## Process inventory

Every `process_config_key` present in the results, with the runs it produced.

| process_config_key | runs | ok | failed | max peak alloc MiB | max peak reserved MiB (process-level) |
|---|---|---|---|---|---|
| `img2img@512x1536@tier0` | 9 | 9 | 0 | 3892.01 | 4648.00 |
| `img2img@512x512@tier0` | 117 | 117 | 0 | 2675.38 | 2958.00 |
| `ip-adapter-plus@512x512@tier0` | 12 | 12 | 0 | 3978.87 | 4634.00 |
| `ip-adapter@512x1536@tier0` | 9 | 9 | 0 | 5140.69 | 6852.00 |
| `ip-adapter@512x512@tier0` | 129 | 129 | 0 | 3924.07 | 4582.00 |
| `text-only@512x1536@tier0` | 9 | 9 | 0 | 3892.01 | 5470.00 |
| `text-only@512x512@tier0` | 12 | 12 | 0 | 2675.38 | 3246.00 |

Note that one `process_config_key` value can be produced by more than one OS process:
the spot-check runs share a key with their sweep counterparts by construction, which
is exactly what makes them comparable.
