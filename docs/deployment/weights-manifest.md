# Production weights — what a clean machine needs, and how to prove it has it

**Milestone:** M8 · **Related:** DR-010 (checkpoint selection), DR-014 (deployment), R14
**Authoritative source:** `apps/api/styles.py`. The table below is checked against those constants
by `apps/api/tests/test_weights_manifest.py` on every pytest run, so this document cannot drift
from the code the way `.env.example` did.

## Read this first

**These three files cannot be regenerated.** Risk R14: LoRA initialisation drew from an unseeded
global torch RNG during M6, so re-running the training that produced them yields *different*
adapters. They are authoritative **as files, by SHA-256** — not as a recipe.

That has a direct consequence for deployment: **a clean clone can reproduce the code and the
Python environment, but it cannot reproduce the weights.** They must be restored from a backup.
This is a stated limitation of the project's reproducibility, not a gap in these instructions.

They are deliberately **not tracked in Git** (`.gitignore` excludes `*.safetensors` and
`outputs/`), which is why this manifest exists.

## Required files

Each is **6 414 480 bytes**, 256 tensors, 256 LoRA keys, zero base-model keys.

| style | run | step | path, relative to `CHECKPOINT_ROOT` |
|---|---|---:|---|
| `minimal-geometric` | EXP-027 | 300 | `outputs/lora/EXP-027__style-full__512x512__r8a8__lr0p0001__bs1x1__st600__seed42__tier0/step00300/pytorch_lora_weights.safetensors` |
| `ukiyo-e` | EXP-028 | 600 | `outputs/lora/EXP-028__style-full__512x512__r8a8__lr0p0001__bs1x1__st600__seed42__tier0/step00600/pytorch_lora_weights.safetensors` |
| `retro-poster` | EXP-029 | 300 | `outputs/lora/EXP-029__style-full__512x512__r8a8__lr0p0001__bs1x1__st600__seed42__tier0/step00300/pytorch_lora_weights.safetensors` |

### SHA-256

```
minimal-geometric  2d425838cce59adc5c12b894e29439b695b98b9e40ef5d7ae667bd5216cb96a8
ukiyo-e            52381b6052ad71f165ed23425bfc4ea1ba794a3886948a741cea9cad3d81abfd
retro-poster       70d2afbfb3c09aff6ba37e1f1cf82c02ad69b0269969ea7cdf43b0ead17ba8db
```

**Two of the three are step 300, not the 600 their runs trained to.** That is the most informative
result of M6, not a transcription error: prompt adherence fell from 4 to 3 at step 600 for
`minimal-geometric` and `retro-poster` while style consistency held at 5. Only `ukiyo-e` improved
with more training. Do not "correct" a step number here.

## Where they come from

**Not from this repository, and not from a public download.** The backup lives outside the
repository on external storage, and its location is Kylian's to supply — it is deliberately not
written into these instructions, so that no private absolute path becomes the documented mechanism.

Restore is therefore parameterised:

```powershell
# From wherever the backup lives (external drive, backup folder, ...):
.\scripts\verify-weights.ps1 -RestoreFrom "E:\DeckForge-weights-backup"

# Or leave them outside the repository and point the service at them:
$env:CHECKPOINT_ROOT = "E:\DeckForge-weights"
```

`CHECKPOINT_ROOT` defaults to the repository root, so the ordinary case — weights sitting in the
repository's git-ignored `outputs/lora/` — needs no configuration at all.

## How failure is reported

Verification happens twice, on purpose.

1. **On restore**, by `scripts/verify-weights.ps1`: presence → exact byte size → SHA-256, printing
   PASS or FAIL per style with the observed hash, and exiting non-zero on any failure.
2. **On every style activation**, by `styles.verify_checkpoint()` in the running service. Not once
   at startup: the adapters live in a git-ignored tree where a stale copy or a partial write is a
   real possibility, and serving an unverified adapter would silently break the link between what a
   user sees and what was scored at gate 2.

A failure returns **HTTP 503 `model_unavailable`** with no path, no filename and no hash in the
response body; the full mismatch goes to the server log. This is proven against a **deliberately
corrupted copy** in `docs/evidence/prototype-5/` Phase B — never against a real adapter, because
R14 means a damaged one is gone for good.

**If a hash check fails, the correct action is to restore the file again. It is never to retrain,
never to "regenerate", and never to relax the check.**

## What is NOT in this manifest

- **The SD 1.5 base model and IP-Adapter.** Both are downloaded from Hugging Face at pinned
  commit SHAs into the user-level cache (`C:\Users\<user>\.cache\huggingface`), roughly 6 GB, and
  are public and re-downloadable. They are pinned in `ml/requirements-inference.txt` and
  `ml/inference/reference_schema.py`, not here.
- **The smoke and pilot adapters** under `outputs/lora/EXP-016…EXP-026`. They are research
  artifacts, not production ones, and the service never loads them.
- **The multi-style adapter (EXP-030).** Viable but not selected at gate 2 — see DR-010. It is not
  a production file.
