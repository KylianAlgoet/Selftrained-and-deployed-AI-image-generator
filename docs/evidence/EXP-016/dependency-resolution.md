# EXP-016 — PEFT dependency resolution under stack protection

**Date:** 2026-08-04 · **Milestone:** M5 (Prototype 3) · **Step:** plan step 1
**Machine:** Windows 11 Home, Python 3.11.0 venv at repo root, RTX 4060 Laptop GPU (8 GB)

## Why this record exists

Every VRAM and latency figure in M3 (EXP-001…005) and M4 (EXP-007…014) is comparable only
because the inference stack has not moved. Installing a training package that silently
upgraded a transitive dependency would retroactively invalidate that measured history.
PEFT was therefore installed as a **gated step with its own evidence**, not as a routine
`pip install`.

## Protected baseline, recorded before any install

Read from `importlib.metadata` in the target venv on 2026-08-04:

```
torch          2.13.0+cu126
torchvision    0.28.0+cu126
diffusers      0.39.0
transformers   5.14.1
accelerate     1.14.0
safetensors    0.8.0
peft           NOT INSTALLED
pip            26.2
Pillow         11.3.0
imagehash      4.3.2
pytest         8.4.2
```

Pre-install suite state: **123 passed in 1.06s**. Working tree clean at `f1eba54`,
in sync with `origin/main`.

## Version selection (from metadata, not assumption)

`diffusers 0.39.0` declares its PEFT requirement in its own `Requires-Dist`:

```
peft>=0.17.0; extra == "training"
peft>=0.17.0; extra == "dev"
```

`diffusers/utils/constants.py:24` carries an older independent floor,
`MIN_PEFT_VERSION = "0.6.0"`, which is the *loader* minimum; the `training` extra's
`>=0.17.0` is the binding constraint for this milestone.

Available official PyPI releases (`pip index versions peft`), newest first:

```
peft (0.20.0)
Available versions: 0.20.0, 0.19.1, 0.19.0, 0.18.1, 0.18.0, 0.17.1, 0.17.0, 0.16.0, ...
```

**Selected: `peft==0.20.0`** — latest official PyPI release, satisfies `>=0.17.0`.
No nightlies, pre-releases, or VCS installs were considered.

## Resolver dry-run, executed BEFORE any write to the venv

```
.venv/Scripts/python.exe -m pip install --dry-run peft==0.20.0 --report <report>.json
```

Human-readable tail — every transitive requirement resolved to an existing install:

```
Requirement already satisfied: hf-xet<2.0.0,>=1.5.1 ... (1.5.2)
Requirement already satisfied: huggingface-hub>=0.25.0 ...
Requirement already satisfied: typing-extensions>=4.1.0 ... (4.15.0)
Requirement already satisfied: setuptools>=77.0.3 (from torch>=1.13.0->peft==0.20.0) (83.0.0)
Requirement already satisfied: sympy>=1.13.3 (from torch>=1.13.0->peft==0.20.0) (1.14.0)
Requirement already satisfied: networkx>=2.5.1 (from torch>=1.13.0->peft==0.20.0) (3.6.1)
Requirement already satisfied: regex>=2025.10.22 (from transformers->peft==0.20.0) (2026.7.19)
Requirement already satisfied: tokenizers<=0.23.0,>=0.22.0 (from transformers->peft==0.20.0) (0.22.2)
...
Would install peft-0.20.0
```

Machine-readable `--report` JSON, parsed rather than eyeballed:

```
packages pip WOULD install: 1
  peft 0.20.0
PROTECTED PACKAGES TOUCHED: NONE
```

`peft 0.20.0` runtime requirements, all already satisfied by the inference stack:

```
numpy>=1.17 · packaging>=20.0 · psutil · pyyaml · torch>=1.13.0 · transformers
tqdm · accelerate>=0.21.0 · safetensors · huggingface-hub>=0.25.0
```

Note that peft's `transformers` and `safetensors` requirements carry **no upper bound**, and
its `torch>=1.13.0` / `accelerate>=0.21.0` floors sit far below the pinned versions — which is
why the resolver had no reason to move anything.

**Decision:** the dry-run showed no protected package being upgraded, downgraded or
reinstalled, so the plan's stop-and-ask condition did **not** trigger. Install proceeded.

## Install (real output)

`--no-deps` was used even though the dry-run was already clean: with every dependency
verified present, it makes the install structurally incapable of moving the stack.

```
.venv/Scripts/python.exe -m pip install --no-deps peft==0.20.0

Collecting peft==0.20.0
  Using cached peft-0.20.0-py3-none-any.whl.metadata (14 kB)
Downloading peft-0.20.0-py3-none-any.whl (775 kB)
   ---------------------------------------- 775.8/775.8 kB 10.9 MB/s  0:00:00
Installing collected packages: peft
Successfully installed peft-0.20.0
```

## Post-install verification

```
.venv/Scripts/python.exe -m pip check
No broken requirements found.
```

Real import check (not a metadata read) in the target venv:

```
peft         0.20.0
diffusers    0.39.0
transformers 5.14.1
accelerate   1.14.0
safetensors  0.8.0
torch        2.13.0+cu126
torch.cuda   12.6
cuda avail   True
device       NVIDIA GeForce RTX 4060 Laptop GPU
diffusers USE_PEFT_BACKEND: True
```

All five protected versions are **byte-for-byte the pre-install values**. `USE_PEFT_BACKEND`
flipping to `True` is the intended and only functional change: diffusers now routes LoRA
through PEFT.

Post-install suite state: **123 passed in 1.09s** — identical count to the pre-install run,
so nothing in the existing dataset/inference/evaluation code regressed.

## Optional tools deliberately NOT installed

Checked via `importlib.util.find_spec`, not installed:

```
bitsandbytes   ABSENT (not installed; not installed automatically)
xformers       ABSENT (not installed; not installed automatically)
```

- **bitsandbytes** is tier 3 of the M5 training memory ladder. It stays optional and is never
  installed automatically on this Windows machine; it requires explicit approval from Kylian.
  No claim about 8-bit optimizer support is made anywhere until it has actually installed and
  run here.
- **xformers** is not needed: torch 2.x SDPA is the Diffusers default, consistent with
  `ml/requirements-inference.txt`.

## Result

**PASS.** PEFT 0.20.0 is installed and pinned in `ml/requirements-training.txt`; the validated
inference stack is unchanged and demonstrated so, rather than asserted.
