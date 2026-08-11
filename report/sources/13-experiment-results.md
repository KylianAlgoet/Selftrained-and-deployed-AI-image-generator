# <span class="section-number">13</span> Experiment results

## 13.1 The registry

**{{ facts.experiment_count }} experiments** are registered in `experiments/registry.csv`, each with
its research question, hypothesis, dataset version, model and pinned revision, full configuration,
hardware readings, duration, output paths, evaluation, conclusion, next action and commit.

Three rules governed the registry, and they are why it can be cited rather than merely referenced:

- **A row is created when the experiment runs**, never retroactively.
- **Memory and duration are measured, never estimated.** Unmeasured means the row says
  *not measured*.
- **Failed experiments get rows too.**

| prototype | experiments | principal questions |
|---|---|---|
| 1 | EXP-001…005 | environment gate, base model, deck aspect ratio |
| 2 | EXP-007…014 | conditioning method, controllability, near-copy risk |
| 3 | EXP-016…019 | LoRA feasibility, deck-format training, combined stack |
| 4 | EXP-020…033 | style learning, captions, image count, memorisation |
| 5 | EXP-034…035 | service residency, reference neutralisation |

Two identifiers are absent by design: EXP-006 and EXP-015 name the human scoring directories rather
than runs.

## 13.2 Memory, measured across five milestones

This is the project's spine, and its internal consistency is the strongest evidence that the
measurement protocol worked.

| configuration | geometry | peak allocated | peak device | spare |
|---|---|---:|---:|---:|
| SD 1.5 text-only | 512×512 | 2 675.38 | 4 359.5 | 3 828.0 |
| SD 1.5 text-only | 512×1536 | 3 892.01 | — | — |
| SDXL | 512×512 | 7 859.26 | 8 187.5 | ~0 |
| **SDXL** | **1024×1024** | **10 738.08** | **8 187.5** | **overflowed** |
| + IP-Adapter | 512×512 | 3 924.07 | 5 695.5 | 2 492.0 |
| + IP-Adapter | 512×1536 | 5 140.69 | 7 965.5 | 222.0 |
| LoRA training | 512×512 | 3 133.40 | 4 285.5 | 3 902.0 |
| LoRA training | 512×1536 | 5 182.58 | 6 449.5 | 1 738.0 |
| **+ LoRA + IP-Adapter** | **512×1536** | **{{ facts.peak_allocated_mib }}** | **7 985.5** | **{{ facts.oneshot_spare_mib }}** |
| **the same, serving** | **512×1536** | **{{ facts.peak_allocated_mib }}** | — | **{{ facts.worst_spare_mib }}** |

MiB, against {{ facts.device_total_mib }} MiB physical.

Three consistency results fell out of this table without being sought:

- **The text-only baseline is byte-identical across three milestones** — 2 675.38 MiB in Prototype 1,
  again in Prototype 2, and again as the reference point in Prototype 3.
- **Peak allocated for the production stack is byte-identical across three measurements** taken days
  apart, in different milestones, including one inside a freshly built clean clone.
- **A trained adapter costs +3.04 MiB regardless of output geometry**, measured independently three
  times.

A measurement protocol that reproduces to the byte across milestones is one whose comparisons can be
trusted. That is the argument for one-configuration-per-process, stated as a result rather than as a
principle.

## 13.3 Training results

Ten runs, all at the lowest memory tier, none escalated.

| run | style | steps | s/step | wall | first → last loss |
|---|---|---:|---:|---:|---|
| EXP-020 | minimal-geometric | 600 | 0.284 | — | 0.0780 → 0.0044 |
| EXP-021 | ukiyo-e | 600 | **0.408** | — | 0.6583 → 0.0302 |
| EXP-022 | retro-poster | 600 | 0.294 | — | 0.4973 → 0.0351 |
| EXP-027 | minimal-geometric | 600 | 0.283 | 175.9 s | 0.0780 → 0.0025 |
| EXP-028 | ukiyo-e | 600 | 0.398 | 244.1 s | 0.6583 → 0.2297 |
| EXP-029 | retro-poster | 600 | 0.308 | 189.5 s | 0.4973 → 0.1425 |
| EXP-030 | **multi-style** | 1800 | 0.350 | 633.8 s | 0.6290 → 0.1960 |

**Peak allocated was 3 133.4 MiB in all ten runs.** Geometry sets training memory; style, image count
and step count do not. `ukiyo-e` is slowest per step because its source images reach 4 000 pixels —
a data-loading cost, not a model cost, and identified as such rather than left as an anomaly.

**Loss is reported and not interpreted as quality.** The lowest final loss belongs to
`minimal-geometric`, whose sources are synthetic and therefore easiest to fit. It is not the best
style.

## 13.4 Conditioning results

Both methods gave **monotone, human-visible control in 6 of 6 conditions**, clearing the pre-declared
bar. The differences that decided the selection were elsewhere.

| | img2img | standard IP-Adapter |
|---|---|---|
| extra VRAM | **0** | +1 248.69 MiB |
| latency behaviour | falls with strength | flat across scale |
| usable mid-range | 0.60–0.65 | 0.40–0.60 |
| near-copy flags | **6 of 6 in the milestone** | **0** |
| originality score at the deck format | **1** | 4 |

**The latency advantage is an artefact and is reported as one.** Diffusers runs `int(steps ×
strength)` steps, so a stronger reference is also a shorter run; cost per *effective* step is flat at
0.11–0.13 s for both. Reading the wall-clock figure alone would have credited img2img with a speed-up
it does not have.

## 13.5 Evaluation and memorisation

**0 of 252** final-matrix outputs were flagged as near-copies of training images, with a holdout
control at a comparable distance — which is the point of the control.

<div class="callout">
<span class="callout__label">What this does not prove</span>
A perceptual-hash threshold is a <strong>coarse near-copy indicator, not proof of no memorisation</strong>.
It detects near-duplicates, not learned reproduction of style-level structure. The CLIP similarity
measure has a second limitation: it uses the same model family that IP-Adapter conditions on, making
it descriptive <em>within</em> a method rather than a neutral referee <em>between</em> methods.
</div>

## 13.6 Service results

The production stack was run as a long-lived service — twelve requests, six cases twice, swapping
between all three adapters.

- **Allocated memory after generation: 3 316.64 MiB in all 13 runs**, growth 0.00 MiB against a
  64 MiB allowance. Residency itself costs nothing.
- **Worst spare: {{ facts.worst_spare_mib }} MiB**, tighter than the one-shot figure, and the
  operative production ceiling.
- **Byte-identical repeats** across cycles — strong evidence of no state residue, and explicitly not
  proof of none.
- A corrupted adapter copy produced a 503 and clean recovery with no restart; a deadline exceeded
  produced a 504 after 14 of 30 steps with the lock released.

This experiment **deliberately breaks the project's own one-configuration-per-process rule**, because
serving is the thing being measured. Its record says so, and states that its figures are therefore
**not comparable** with the single-shot experiments.

## 13.7 The result that closes the loop

A clean clone, in a freshly built environment three days later, reproduced an earlier output
**byte for byte**: SHA-256 `{{ facts.output_sha256 }}`, {{ facts.output_bytes }} bytes.

**Inference is deterministic and portable given a fixed adapter.** This does **not** contradict the
finding that training is not reproducible from seed (§12.4) — those are different halves of the
pipeline, and both statements are true.
