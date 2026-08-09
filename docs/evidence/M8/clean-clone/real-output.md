# Clean-clone real output — the one authorised generation

**Date:** 2026-08-09 · **Milestone:** M8 (phase M8.8) · **Result: PASS**
**Authorised by Kylian Algoet at the M8 human gate**, explicitly, before it ran.

## Classification — read this before citing anything below

**This is M8 deployment validation. It is NOT a research experiment.**

- It has **no `EXP-###` id** and is **not** in `experiments/registry.csv`.
- It is **not** part of EXP-034, EXP-035 or any frozen matrix.
- It compares nothing, evaluates no style, explores no prompt, and supports no
  research conclusion about model quality.

Its only job is to prove the criterion *"a clean-clone test succeeds with real output"*.

### The generation count is 27, and stays stated as 27

| purpose | count |
|---|---:|
| research matrix (M3–M7), closed at its cap | 25 |
| Kylian's manual M7 human-review run | 1 |
| **this deployment validation** | **1** |
| **total** | **27** |

Never reported as 25.

## Configuration — already validated, nothing new

`minimal-geometric` (the unambiguous PASS) · **prompt-only**, no reference — one variable, fewest
moving parts · seed **42** · defaults: LoRA weight 0.7, 30 steps, guidance 7.5, 512×1536.
Prompt: *"a mountain and a rising sun"*.

Driven **from the browser**, not with curl. A curl call would prove prompt → API → model → PNG; the
criterion is the whole chain, and only a browser run also proves PNG → frontend → 3D deck. **One
generation, the complete path.**

## Result

```
HTTP 200   generation_id MYOcI34c3yfyj2z1YtKAtA
```

| field | value |
|---|---|
| prompt built | `xgeo minimal geometric abstract style skateboard decal artwork, a mountain and a rising sun` |
| seed / steps | 42 · **30 of 30** |
| adapter | **EXP-027 step 300**, sha256 `2d425838cce59adc…` — **matches the gate-2 record** |
| live LoRA modules | 128 · active adapters `['minimal-geometric']` |
| reference | none · `ip_adapter_scale` 0.0 |
| output | 512×1536 PNG, 1 089 939 bytes |
| `generate_seconds` | **16.649** |
| browser wall clock | **63.16 s** — includes the cold model load |
| peak allocated | **5143.73 MiB** |
| peak device used | 7969.5 MiB of 8187.5 → **218.0 MiB spare** |
| warnings | none |
| `POST /api/generate` calls | **1** |
| console errors | **0** |

## The strongest result: byte-identical reproduction across environments

**The clean clone reproduced M7's Phase A output exactly.**

```
M7 Phase A (2026-08-06)  outputs/prototype-5/P5__minimal-geometric__promptonly__seed42.png
  sha256 46bbf160e4270429e6692467dc6c59577e99bf3178dedd8d38193d0335fb6d7f   1 089 939 bytes

M8 clean clone (2026-08-09)  clean-clone-generation.png
  sha256 46bbf160e4270429e6692467dc6c59577e99bf3178dedd8d38193d0335fb6d7f   1 089 939 bytes
```

Same seed, same settings, same adapter, **a freshly built environment three days later** — and a
byte-identical PNG. Verified two independent ways: `sha256sum` on both files, and the
`image_sha256` the service itself computed and recorded in the metadata.

**This does not contradict R14, and must not be quoted as if it did.** R14 says *training* is not
bit-reproducible from its recorded seed, because LoRA initialisation drew from an unseeded global
RNG. This result is about *inference*: given a **fixed adapter file**, a fixed seed and fixed
settings, generation is deterministic and portable across environments. The two statements are
about different halves of the pipeline and both remain true.

It is also independent corroboration that the restored adapter is the right file — a different
adapter could not have produced the same bytes.

## Memory: consistent with every prior measurement

`peak_allocated_mb` **5143.73** is **byte-identical** to EXP-019b (M5) and EXP-034 (M7). Three
milestones, two machines-worth of setup, one number.

`spare_device_mb` **218.0** matches EXP-034's prompt-only figure exactly. The tighter **200.0 MiB**
worst case belongs to the *reference-conditioned* path, which this run deliberately did not use —
so **218.0 does not supersede 200.0**, and the operative production ceiling is still 200.0 MiB.

## Honest progress, captured mid-flight

Screenshot `01-generating.jpg` was taken 6 s in, during the cold model load. The panel read:

```
GENERATING DECAL
Loading the local generation model…
No step percentage at this stage
Elapsed: 6 seconds
STYLE Minimal geometric · REFERENCE IMAGE No · SEED 42 · OUTPUT 512×1536 · GENERATION Local
```

**No percentage, no invented progress bar** — DR-013's rule, observed in a real cold start rather
than in a fixture.

## The chain, proven end to end

| link | evidence |
|---|---|
| prompt → API | `POST /api/generate` sent once, HTTP 200 |
| API → model | real adapter loaded, 128 live LoRA modules, 30/30 steps |
| model → PNG | 512×1536, 1 089 939 bytes, hash recorded by the service |
| PNG → frontend | result panel with duration and full metadata |
| frontend → **3D deck** | *"Applied to the deck preview"*, live WebGL context, orbit works |
| downloads | PNG and metadata JSON both saved **through the application's own buttons** |

Screenshots: `01-generating.jpg` · `02-result-and-deck.jpg` · `03-deck-orbited.jpg`.

## Artifacts

| file | tracked? | what it is |
|---|---|---|
| `real-output/clean-clone-generation-metadata.json` | yes | the sidecar, downloaded from the application |
| `real-output/generation-record.json` | yes | the full run record, including the raw API response |
| `real-output/screenshots/` | yes | three captures, ~95 KB each |
| `outputs/m8-clean-clone/clean-clone-generation.png` | **no** | the decal itself, 1 089 939 bytes |

**The PNG is deliberately not committed.** Generated images live in git-ignored `outputs/` in this
project, and a 1 MB binary would be larger than anything else tracked under `docs/evidence/`.
Nothing is lost by that: its sha256 is recorded in three independent places (this document, the
metadata sidecar, and the service's own `image_sha256`), the screenshots show the result and the
deck, and the file is **byte-identical** to the already-recorded
`outputs/prototype-5/P5__minimal-geometric__promptonly__seed42.png`.

## Afterwards

`stop-demo.ps1` stopped both processes, all three ports were released, and **no orphan uvicorn or
vite process remained**. The clean-clone directory is deleted; it is regenerable in ~10 minutes by
following `docs/deployment/runbook.md`, which is the point.
