# Environment measured inside the clean clone

**Date:** 2026-08-09 · **Directory:** `C:\Expert Lab\DeckForge-M8-clean-clone` · **Commit:** `824838f`

Every value below was read from a command run **inside the clone**, not copied from the working
repository.

## Toolchain

| component | version |
|---|---|
| OS | Windows 11 Home 10.0.26200 |
| Shell | Windows PowerShell 5.1 |
| Python (clone `.venv`) | 3.11.0 |
| pip **as shipped by venv** | **22.3** — cannot resolve torch (M3 finding, reproduced) |
| pip after upgrade | 26.2.1 |
| Node.js | v24.18.0 |
| npm | 11.16.0 |
| Git | 2.42.0.windows.2 |
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU |
| Driver | 610.88 |
| VRAM | 8188 MiB |

## Python packages installed in the clone

### Protected pins — all exact

```
torch              2.13.0+cu126
torchvision        0.28.0+cu126
diffusers          0.39.0
transformers       5.14.1
accelerate         1.14.0
safetensors        0.8.0
peft               0.20.0
pillow             11.3.0
```

`torch.cuda.is_available()` → **True**, device `NVIDIA GeForce RTX 4060 Laptop GPU`.
`pip check` → **No broken requirements found.**

### API stack

```
fastapi            0.141.1
uvicorn            0.52.1
pydantic           2.13.4
pydantic_core      2.46.4
httpx              0.28.1
huggingface_hub    1.25.1
starlette          1.6.0   <- differs from the dev machine's 1.4.1
numpy              2.4.4   <- differs from the dev machine's 2.4.6
```

**Both differences are transitive dependencies that are not actually pinned.**
`apps/api/requirements.txt` lists `starlette==1.4.1` in a **comment block** headed *"pinned here so
the set is reproducible"* — the lines are commented out, so nothing pins them. See
`log.md` for the full note; everything passed on the newer versions.

## Frontend

`npm ci` installed **306 packages** from `package-lock.json` in 15.7 s, audited 307, and reported
the same **3 high-severity advisories** (`brace-expansion`, `js-yaml`, `nanoid`) present on the dev
machine — pre-existing, dev-tooling only, not in the shipped bundle.

Node's `engines` are not constrained by `package.json`; the **>= 20.19** requirement is documented
in the runbook and enforced by `preflight.ps1`.

## What was NOT downloaded

- **No model weights.** The three LoRA adapters were restored from a backup, not fetched.
- **No Hugging Face model download occurred**, because no generation ran. The base model and
  IP-Adapter (~6 GB) would be fetched into the user-level cache on the first generation; that cache
  already exists on this machine from earlier milestones and is **shared**, not re-downloaded per
  clone. A genuinely cold machine would pay that download once — stated because this clean clone
  did **not** demonstrate it.
- The CLIP tokenizer used by `test_style_kit.py` resolved from the existing user-level cache. On a
  machine without it, that test needs network access to Hugging Face.
