# M7 review gate — handover to Kylian

**Date:** 2026-08-06 · **Milestone:** M7 (Prototype 5 — integrated MVP)
**Status:** built, validated, and **stopped here.**

One decision is yours, and everything else in this document is evidence for it.

---

## 1. The decision you need to make

**Which texture-fit mode becomes the production default?**

The generated decal is **1:3** (512×1536). The deck's UV domain is **1:3.902**
(`DECK_LENGTH 3.2 / DECK_WIDTH 0.82`). They do not match, and there is no option that avoids
the trade-off:

| mode | what it does | measured cost |
|---|---|---|
| **A. Full surface** | fills the whole deck | artwork stretched **1.3008×** lengthwise |
| **B. Fit without stretching** | preserves the artwork, centred | **23.12 %** of the deck length bare, **11.56 % at each end** |

Both are built. Both are in the running app behind a control labelled *review control*.
**Nothing in the code picks one, and a test asserts no default is exported.**

Screenshots, same decal (`P5__ukiyo-e__ref__seed42.png`), same camera, only the mode changed:

- `screenshots/fit-full-surface.jpg`
- `screenshots/fit-without-stretch.jpg`

A caveat that belongs to neither mode and should not decide it: the Prototype-0 UV convention
already compresses the texture horizontally toward the tapered nose and tail. That is
pre-existing geometry and applies equally to both.

**Secondary, only if you want to change it:** the bare-end colour in mode B is `#242424`,
matching the deck's grip/rim material so an uncovered end reads as bare deck.

---

## 2. Start commands

**API — one process, no reload. This is a correctness requirement, not a style preference**
(the busy lock is process-local, and a second resident pipeline does not fit in 200 MiB):

```
.venv/Scripts/python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

**Frontend:**

```
cd apps/web
npm run dev
```

**Application URL:** http://localhost:5173

---

## 3. Real `/api/health` response (Phase A, captured)

```
pid 21604 · cuda True · pipeline_loaded False (before the first generation)
single_worker_guard: enforced · device_total_mb 8187.5
```

The PID is reported so a second, accidentally launched server is visible. **Nothing inside one
process can detect another one** — multiple separately launched API processes are unsupported.

---

## 4. Test counts (real, just run)

| suite | count | result |
|---|---:|---|
| pytest (`ml` + `apps/api`) | **371** | all pass — 289 pre-existing, unchanged, + 82 new |
| vitest (`apps/web`) | **66** | all pass |
| eslint | — | clean |
| `npm run build` | — | succeeds |

**No linter is installed for Python.** pytest remains the Python validation gate.

---

## 5. EXP-034 — the residency result

Twelve requests, six cases run twice, one process. **All eight criteria declared before the run
passed.**

- Allocated after generation: **3316.64 MiB in all 13 runs.** Growth between cycles: **0.00 MiB**
  against a 64 MiB allowance. Six unload/load cycles across three adapters accumulated nothing.
- Peak allocated: **5143.73 MiB — byte-identical to M5's EXP-019b.**
- **All 6 repeated cases byte-identical** across cycles.
- **Worst spare: 200.0 MiB.** That is *tighter* than the 202.0 MiB quoted from EXP-032, and it
  is not comfortable headroom.

Full record: `docs/evidence/EXP-034/README.md`.

---

## 6. Runtime checkpoint hashes (verified on disk, 2026-08-06)

Each 6 414 480 bytes, each matching its gate-2 recorded value:

| style | run | step | sha256 |
|---|---|---:|---|
| minimal-geometric | EXP-027 | 300 | `2d425838cce59adc5c12b894e29439b695b98b9e40ef5d7ae667bd5216cb96a8` |
| ukiyo-e | EXP-028 | 600 | `52381b6052ad71f165ed23425bfc4ea1ba794a3886948a741cea9cad3d81abfd` |
| retro-poster | EXP-029 | 300 | `70d2afbfb3c09aff6ba37e1f1cf82c02ad69b0269969ea7cdf43b0ead17ba8db` |

The service re-verifies these on **every** style activation and refuses to serve on mismatch.
It never regenerates — R14 means they cannot be reproduced from their seed.

---

## 7. Generated images and metadata

Six decals from Phase A, in git-ignored `outputs/prototype-5/`:

```
P5__minimal-geometric__promptonly__seed42.png    P5__minimal-geometric__ref__seed42.png
P5__ukiyo-e__promptonly__seed42.png              P5__ukiyo-e__ref__seed42.png
P5__retro-poster__promptonly__seed42.png         P5__retro-poster__ref__seed42.png
```

Their full per-image metadata is in `api-validation.jsonl`. EXP-034's twelve are in
`outputs/EXP-034/`, EXP-035's two in `outputs/EXP-035/`.

---

## 8. Prompt-only and reference-conditioned evidence

Every style works both ways (Phase A):

| style | prompt-only | reference | spare (prompt-only / ref) |
|---|---|---|---|
| minimal-geometric | ok 12–13 s | ok 13.07 s | 218.0 / 200.0 MiB |
| ukiyo-e | ok 12.89 s | ok 12.96 s | 218.0 / 200.0 MiB |
| retro-poster | ok 13.14 s | ok 13.31 s | 218.0 / 202.0 MiB |

**`retro-poster` returned a warning on all of its requests** — its H4 limitation reaches the
user, not just the documentation.

**Prompt-only is not a trivial path.** With IP-Adapter resident, diffusers raises if no
reference is passed, so the service keeps the adapter at scale 0.0 with a constructed grey
placeholder. **EXP-035** tested the claim that rests on: the grey placeholder and real holdout
artwork produced **byte-identical** output, and the same bytes as EXP-034's prompt-only result.

---

## 9. Style-switch evidence

EXP-034 switched styles on every one of its 12 requests. Every request had **exactly one**
adapter live, matching the requested style, with **128 live UNet LoRA modules**. No previous
adapter ever remained. The API test suite additionally walks
`minimal-geometric → ukiyo-e → retro-poster → minimal-geometric` and asserts the live state
rather than trusting `load_lora_weights` to have worked.

---

## 10. Failure and recovery evidence

**Corrupted checkpoint (Phase B).** The three real adapters were **copied** to a sandbox and the
`retro-poster` copy replaced with `\x00` bytes of **exactly the same length**, so the sha256
check is what rejects it. The real files were never written to.

- corrupted adapter → **HTTP 503**, no path or filename in the response
- the busy lock was **not** left held
- `minimal-geometric` → **HTTP 200** immediately after, **with no restart**

**Deadline (Phase C).** With a 5 s deadline against ~13 s generations:

- warmed request → **504 after 6.33 s, stopped after 14 of 30 denoising steps**
- lock released afterwards

The abort lands on a **step boundary** and the VAE decode after the loop is **not
interruptible**, so a 504 means "the denoising loop was stopped", not "the GPU idled at exactly
5.000 s". A client disconnect does **not** release the lock — there is no background thread, so
no path exists where a response is sent while GPU work continues.

---

## 11. GPU budget

The plan declared a hard cap of **25 real generations** before any ran. Final count: **25 of 25.**

| purpose | count |
|---|---:|
| EXP-034 smoke | 1 |
| EXP-034 matrix | 12 |
| Phase A serving | 6 |
| Phase B recovery | 1 |
| Phase C aborts | 2 |
| EXP-035 | 2 |

The cap is reached exactly. **No further real generation may run in M7 without your decision.**
This is why the fit-mode screenshots were captured by loading an *existing* generated decal from
disk through a review control, rather than by generating a new one.

---

## 12. Manual acceptance checklist

Start both processes, open http://localhost:5173, then:

- [ ] The style list shows three styles; `retro-poster` is marked *(partial)*.
- [ ] Selecting `retro-poster` shows its limitation before you generate.
- [ ] Generate with a prompt only. It completes and appears on the deck.
- [ ] The result panel's metadata shows the adapter run, step, weight, seed and hashes.
- [ ] Generate again with the same prompt and seed — the image is identical.
- [ ] Attach a reference image and generate. "Reference influence" becomes adjustable.
- [ ] Try a `.exe` or `.gif` renamed to `.png` as a reference — it is refused with a clear message.
- [ ] Switch style and generate. The new style appears; the previous one does not linger.
- [ ] **Compare the two texture-fit modes on the same decal. Choose the production default.**
- [ ] Toggle the inverted-UV demonstration — the decal flips nose/tail, confirming orientation.
- [ ] Download the PNG and the metadata JSON.
- [ ] Orbit and zoom, then generate again: the camera does not move.

---

## 13. What I have NOT done, and will not do before you review

- **Not chosen the texture-fit mode.** No default is exported and a test enforces that.
- **Not declared M7 complete.** Planning still shows it in progress.
- **Not pushed.** `main` is ahead of `origin/main`.
- **Not touched the GitHub issue or project board** — `gh` is unavailable and those are yours.
- **Not begun M8.**
- **Not run a 26th generation.**
