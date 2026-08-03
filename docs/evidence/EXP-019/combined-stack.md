# EXP-019 — the mandatory R12 combined-stack smoke test

**Date:** 2026-08-04 · **Milestone:** M5 (Prototype 3) · **Risk:** R12
**Device:** NVIDIA GeForce RTX 4060 Laptop GPU, **8187.5 MiB physical**

## Why this experiment was mandatory

DR-008 and risk R12 made a combined **SD 1.5 + LoRA + IP-Adapter** smoke test at
512×1536 an acceptance item for this milestone, before any later work relies on the
stack. The reason was measured, not assumed: in EXP-013, **IP-Adapter alone at
512×1536 peaked at 7965.5 MiB of 8187.5 MiB — about 222 MiB spare** — and a LoRA had
not yet been added on top.

Order was fixed in advance: **512×512 first**, deck format only after it succeeded.
Each arm ran in its own fresh OS process.

## Frozen configuration (identical across both arms)

| element | value |
|---|---|
| base model | `stable-diffusion-v1-5/stable-diffusion-v1-5` @ `451f4fe1…` |
| LoRA checkpoint | `outputs/lora/EXP-016__smoke__512x512__…__st300__seed42__tier0/pytorch_lora_weights.safetensors` |
| LoRA sha256 | `e76f822bd3b6314ae38c025ae86b4dad352701c3c86b270d1e9d0ce33e12759b` |
| LoRA weight | 1.0 |
| IP-Adapter | `h94/IP-Adapter` @ `018e402774…`, `ip-adapter_sd15.safetensors` |
| IP-Adapter scale | **0.55** (DR-008 default) |
| reference | **R2** — `data/references/R2-DS-0048-geo-1047.png`, minimal-geometric, project-original, 512×1536 |
| reference preprocessing | long side bounded 512×1536 → 341×1024 (LANCZOS); CLIP processor resize + centre-crop 224 |
| prompt | **P2-geo** (frozen kit `c40749bc…`) |
| negative prompt | frozen kit negative prompt |
| seed | 42 |
| scheduler / steps / guidance | DPMSolverMultistepScheduler / 30 / 7.5 |
| memory tier | 0 |

**R2 is drawn from the dataset holdout split**, so the LoRA trained in EXP-016 never
saw it. A pytest enforces that the training subset and the holdout split are disjoint.

## Results

Both adapters were confirmed live *simultaneously*, read back from the UNet rather
than inferred: **128 LoRA modules** and **16 IP-Adapter attention processors**
(the expected signature — SD 1.5 has one cross-attention processor per block and
IP-Adapter replaces the cross-attention half only).

| arm | geometry | status | peak allocated | peak device used | **spare** | generate |
|---|---|---|---|---|---|---|
| EXP-019a | 512×512 | ok | 3927.11 MiB | 5697.5 MiB | 2490.0 MiB | 5.227 s |
| **EXP-019b** | **512×1536** | **ok** | **5143.73 MiB** | **7985.5 MiB** | **202.0 MiB** | 14.139 s |

Post-load allocation was **3308.33 MiB** in both arms — geometry costs nothing until
generation starts.

### The LoRA's marginal cost is ~3 MiB, and it is constant

| configuration | 512×512 allocated | 512×1536 allocated |
|---|---|---|
| IP-Adapter alone (EXP-009 / EXP-013) | 3924.07 MiB | 5140.69 MiB |
| **+ LoRA (EXP-019)** | **3927.11 MiB** | **5143.73 MiB** |
| **delta** | **+3.04 MiB** | **+3.04 MiB** |

The same +3.04 MiB appears independently in EXP-018, where loading the adapter onto a
bare SD 1.5 pipeline moved the peak from 2675.38 to 2678.42 MiB. A rank-8 attention
LoRA is 1 594 368 parameters — about 3 MiB in fp16 — so the measurement matches the
arithmetic, and it does not scale with output geometry.

## Verdict on R12

**The combined stack fits at the deck format, at tier 0, with no escalation — and it
fits by 202 MiB of 8187.5 MiB, which is 2.5 % of the device.**

**This is not comfortable headroom, and must never be described as such.** It is
*less* margin than IP-Adapter alone had in EXP-013 (222 MiB), because the LoRA
consumes 20 MiB of device-level memory on top. The run succeeded, no overflow flag
fired, and no memory tier escalated — exactly the pattern that made SDXL look viable
in EXP-004 before the figures were read against the ceiling.

Consequences to carry forward:

- **R12 is re-scoped, not closed.** The specific stack tested here fits. The risk that
  *additions* to it do not fit is unchanged and now quantified: there is 202 MiB of
  room for anything further — a second adapter, a higher LoRA rank, a larger reference
  batch, or ControlNet in Prototype 5.
- Prototype 5 must treat 512×1536 + LoRA + IP-Adapter as the **memory ceiling of the
  production path**, not as a starting point to build on.
- Geometry was never reduced to make this pass, and no tier was escalated. Had it
  failed, the failure would have been its own row followed by tiers 1–4 in separate
  runs.

## Honest note: the first EXP-019a attempt failed

The first 512×512 attempt is preserved in `combined-stack.jsonl` with
`status: failed`. It was **a defect in this experiment's own runner, not a finding
about the stack**: `preprocess_for_adapter` returns `(image, note)` and the caller
unpacked it as a single value, so the note string reached the pipeline instead of the
image. It is kept rather than deleted because deleting failed rows is how a record
stops being a record.

That row still carries one real measurement: the full stack **loaded** successfully
(128 LoRA modules + 16 IP-Adapter processors, 3308.33 MiB post-load) before failing in
image preprocessing. The fix records the preprocessing note on every row, so what was
done to the reference can no longer be reconstructed incorrectly.

## Reproduce

```
.venv/Scripts/python.exe -m ml.training.combined_stack \
    --exp-id EXP-019a --width 512 --height 512 \
    --adapter-dir outputs/lora/EXP-016__smoke__512x512__r8a8__lr0p0001__bs1x1__st300__seed42__tier0

.venv/Scripts/python.exe -m ml.training.combined_stack \
    --exp-id EXP-019b --width 512 --height 1536 \
    --adapter-dir outputs/lora/EXP-016__smoke__512x512__r8a8__lr0p0001__bs1x1__st300__seed42__tier0
```

Full-resolution outputs live in git-ignored `outputs/EXP-019/`.
