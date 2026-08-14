# Claude presentation handoff — DeckForge AI bachelor defence

**Created:** 2026-08-14 · **Milestone:** M10 (**OPEN**) · **Companion:**
[`claude-asset-manifest.md`](claude-asset-manifest.md)

**Workflow change this document exists for.** This repository remains the **content and evidence
authority**: facts, experiments, decisions, limitations, speaker notes, demo flow and jury
preparation are maintained here. The **final visual presentation is designed in a separate Claude
session**, using this package. That session should not need repository access.

Everything below is drawn from tracked evidence and was re-verified on 2026-08-14. **Nothing here is
estimated except the spoken timings, which are labelled as estimates.**

---

## 1. Project context

| | |
|---|---|
| Project | **DeckForge AI** — a skateboard-decal generator |
| Student | **Kylian Algoet** |
| Programme | Multimedia & Creative Technologies, **Erasmushogeschool Brussel** |
| Defence | **2 September 2026** |
| What it does | text prompt + optional reference image → a decal in one of three trained styles → applied to an interactive 3D skateboard deck |
| What is defended | **the research process**, not the artefact |
| Hardware | one **NVIDIA RTX 4060 Laptop GPU, 8 GB**, Windows 11 |

The assignment sets thirteen mandatory requirements. The one that shapes everything: the model must
be **self-trained and run locally**, on consumer hardware.

**The primary research question, verbatim:**

> How can a locally fine-tuned diffusion model, conditioned on both a text prompt and a reference
> image, generate skateboard-decal artwork in multiple visually distinct styles with reproducible
> quality on consumer hardware with 8 GB of VRAM?

Twelve secondary questions sit under it: **eight answered within their stated scope, four bounded,
and RQ4's image-count component explicitly inconclusive.** Do not report "ten of twelve".

---

## 2. Authoritative duration

| | |
|---|---|
| **Total slot** | **20:00, including the live demo** |
| Spoken presentation | **~14:00** |
| Live demo | **~4:00** |
| Safety buffer | **~2:00** |

The current in-repository deck estimates **14:13 narration + 4:00 demo = 18:13, buffer 1:47**.

**Every timing figure is an ESTIMATE** derived from speaker-note word counts at a deliberately slow
**130 wpm**. **No rehearsal has ever been run.** 130 wpm is a chosen pace, not a measurement of how
Kylian speaks. Do not present any of these as measured delivery times.

> **Note for whoever edits the notes next:** the repository deck currently sits at 853 s against an
> enforced ceiling of 855 s, so it has almost no headroom. If you rewrite the notes, aim for
> **~830–840 s** to leave room to work.

---

## 3. The final 15-slide structure

Structure is **approved**. Do not increase the slide count without a compelling communication
reason. The jury must be able to follow: problem → research question → constraints → research
process → dataset → model decisions → conditioning → LoRA training → failures → integrated system →
testing → reproducibility → deployment → conclusions → demo → reflection.

| # | title | job | visual |
|---:|---|---|---|
| 1 | DeckForge AI | title | typography |
| 2 | The assignment + research question | the problem, then the question | minimal |
| 3 | 8 GB changed every decision | constraint + research process | P0→P5 ladder + memory bar |
| 4 | The dataset was built, not downloaded | provenance | three-style contact strip |
| 5 | SDXL was better — and rejected | quality vs feasibility | Track B grid + big numbers |
| 6 | The free method lost | near-copy evidence | **large** reference/img2img pair |
| 7 | Training longer made it less obedient | the step-300 result | **large** 300 vs 600 pair |
| 8 | What did not work | honesty | retro-poster evidence |
| 9 | The integrated system | architecture | **new clean diagram** |
| 10 | Testing | what tests do and do not prove | typography |
| 11 | Reproducibility has two halves | the split answer | split slide, one screenshot |
| 12 | Local — deliberately | deployment decision | four-option comparison |
| 13 | Conclusion | the answer + its bounds | large typography |
| 14 | Live demo | handoff | minimal, stays on screen |
| 15 | What I would change | reflection | typography |

---

## 4. Factual locks — these must survive exactly

Every value here is fact-locked in `report/facts.yaml` and validated against evidence.

### 4.1 Memory — the three figures, and the one that subtracts

**This is the most dangerous set of numbers in the deck. An earlier version got it wrong.**

| figure | what it counts | value |
|---|---|---:|
| device total | the physical card | **8187.5 MiB** |
| peak **allocated** | live tensor bytes in the PyTorch allocator | 5143.73 MiB |
| **reserved** | the allocator's cached pool | 6872.0 MiB |
| worst **device used** | context + reserved pool + display = total occupancy | **7987.5 MiB** |
| **worst spare** | what is left under real serving | **200 MiB** (**2.4 %**) |

```
8187.5 − 7987.5 = 200.0      ✅ the margin
8187.5 − 5143.73 = 3043.77   ❌ NOT the margin — never present this
```

**Only `device used` is comparable with the card's total.** If peak allocated is mentioned at all,
its semantics must be stated. The prompt-only path is lighter (7969.5 MiB used); the
**reference-conditioned figure is the worst case and is the production ceiling**.

Never call 200 MiB "comfortable headroom".

### 4.2 Base model

**SD 1.5 was selected because SDXL did not fit at a useful resolution on the validated 8 GB GPU.**

- **SDXL scored *better*** than SD 1.5 under the project's own rubric **at its designed resolution**.
- SDXL needed **10 738 MiB allocated at 1024 × 1024** on a 8187.5 MiB card.
- **It did not crash.** Windows spilled GPU memory into host RAM, so **all thirty runs completed and
  reported success**. A zero exit code did not mean it fit.
- **SD 2.1 was never measurable** — authentication-gated. The comparison rests on **two** candidates,
  not three.

**Never claim SD 1.5 is qualitatively better.** The claim is feasibility at a useful resolution.

### 4.3 Reference conditioning

**IP-Adapter selected over img2img, at scale 0.55.**

Reason: **img2img produced near-copy behaviour in the measured deck-format experiment.** Six outputs
were flagged at dHash ≤ 6; **two scored dHash 0 — perceptually identical to the reference.** All
flags were img2img; **none were IP-Adapter.**

| geometry | runs | median dHash to reference | minimum |
|---|---:|---:|---:|
| 512 × 512 | 31 | 27 | 12 |
| **512 × 1536 (production)** | 9 | **5** | **0** |

Mechanism, stated plainly: img2img forces the reference into the output resolution, so a reference
already at 512 × 1536 keeps 100 % of its area and denoising at strength 0.65 starts from an
essentially intact copy.

Note the shape of this decision: **img2img costs zero extra VRAM and was rejected anyway**, on a card
with 200 MiB spare. It lost on what it does, not what it costs.

**Never claim IP-Adapter is universally superior.** It won this comparison, at this geometry.

### 4.4 LoRA

- **Three per-style LoRA adapters**, one per style. Not one multi-style adapter.
- **Rank 8**, default application strength **0.7** (adjustable 0.4–1.0).
- **minimal-geometric ships at step 300 · retro-poster at step 300 · ukiyo-e at step 600.**
- Each adapter is **6 414 480 bytes**, 256 tensors, zero base-model keys.
- **The claim is feasibility, not superiority.** Full fine-tuning, training from scratch, DreamBooth
  and Textual Inversion were **screened on criteria and never run**.

**Never claim LoRA was proven the best fine-tuning method.** Never imply the screened alternatives
were measured.

A multi-style adapter was also trained and is **viable but not selected** — per-style adapters won on
flexibility, because each style needs a different checkpoint. Do not call it a failed experiment,
and preferably do not raise it at all on a 15-slide deck.

### 4.5 Longer training

For **minimal-geometric**, comparing step 300 with step 600 on **identical prompts and identical
seeds**:

| | step 300 | step 600 |
|---|---:|---:|
| style consistency | 5 | 5 |
| **prompt adherence** | **4** | **3** |

**Longer training preserved style and cost obedience.** `retro-poster` shows the same effect.
**Ukiyo-e is the counterexample — it improved and therefore ships at step 600.**

This was only visible because each run was checkpointed at 150/300/450/600 and the checkpoints were
scored. A single global step count would have been wrong for two styles of three.

### 4.6 retro-poster

**PARTIAL PASS. Never upgrade to PASS.**

It learned the **frames, borders and display typography** of the archive posters, not only their
style — the training material is WPA silkscreen posters, and almost all of it has a frame and large
lettering as part of the composition. Outputs place subjects inside poster frames with pseudo-text
that is not quite readable.

It ships **labelled in the interface**, on every request. It was **not dropped**, and **not
re-scored until it passed**.

### 4.7 RQ4 image count

**INCONCLUSIVE.**

The same style was trained on **12, 24 and 44 images** with everything else fixed. The ordering came
out **non-monotonic**, with **one run per condition**, so a real effect cannot be separated from
variance. Repeating conditions enough times did not fit the GPU budget.

**No minimum image count was established and none is claimed.** Do not infer a threshold. Do not say
"about forty images is enough".

### 4.8 Reproducibility — two halves, do not merge them

| | |
|---|---|
| **Inference** | **Reproducible.** A clean clone in a fresh environment reproduced an earlier output **byte for byte three days later** — SHA-256 `46bbf160e427…`, 1 089 939 bytes |
| **Training** | **NOT bit-reproducible from the recorded seed.** The LoRA initialisation draws from an **unseeded global RNG**, so the recorded seed never governed it |

Consequences: the three production checkpoints are **artifacts verified by hash on every request,
not recipes**. They **cannot be regenerated**. The data pipeline *is* deterministic and was verified
separately.

The defect produced runs that looked completely valid; it is **invisible unless you compare weights**,
and was found only by attempting to reproduce a result rather than assuming it would reproduce.

### 4.9 Evaluation — the disclosure, in approved wording

- Visual evaluation was **AI-assisted**: **ChatGPT contributed visual analysis and proposed scoring**
  at the review gates.
- **Kylian reviewed and approved every recorded score** and **retained final decision authority**
  over every production selection and research conclusion.
- **One human approver. No second independent human rater. Therefore no inter-rater agreement can be
  reported.**
- **Gate 1 was blinded.** 12 blinded sheets; scores fixed and their SHA-256 supplied **before** the
  blinding map was opened; hash-locked by a test so a score cannot be altered after unblinding.
- **Gate 2 was labelled, by necessity** — it asks which checkpoint ships, which cannot be answered
  without knowing which checkpoint a sheet is. The gate record itself states that **labelled sheets
  carry an expectation effect that blinded ones do not**.

**Never say all visual scoring was blind.** Never erase the blinding that did happen either.

The rubric was **defined before the images were reviewed**, on a 1–5 scale.

### 4.10 Deployment

**Native local Windows/NVIDIA + pre-generated backup demo assets. Selected from four options
compared on nine criteria. There is no public cloud deployment, and that was deliberate.**

- Not cloud: cost over the project, a network dependency on the one day everything must work, and —
  deciding — it answers nothing. The question is what fits in 8 GB of *consumer* hardware.
- Not Docker: GPU passthrough was **never verified on this machine** and its overhead is
  **unmeasured**, which is disqualifying on this margin.
- Reproducibility is carried by the **runbook and the clean-clone proof**, not by a URL.

**Never claim internet hosting is impossible.** The measured constraint is narrower: **~200 MiB
worst spare on the validated GPU prevents a second resident pipeline there**, so multi-worker GPU
inference is unsupported **on that machine**.

### 4.11 Architecture

- **One API worker. One generation at a time.** Asserted in code at startup, not a default.
- A concurrent generation request receives a **clean 409 refusal**, never an OOM crash.
- Generation goes **directly to 512 × 1536** — not square-then-crop. The hypothesis that the tall
  ratio would degrade quality was **tested and refuted**.
- Two processes on one machine: React + Three.js browser client, FastAPI service owning the model.
- Uploads validated: allowlist, real decode, size limits, random internal filenames, no user string
  reaching a filesystem path.
- Deck geometry is **procedural**, so no third-party 3D model licence enters the deliverable.

### 4.12 Generation total

**27 total** — 25 inside the frozen research matrix, 1 manual human-review run in M7, 1 deployment
validation run in M8. **Do not change this from build or test activity, and do not report 25.**

### 4.13 Dataset

**148 items · three styles · built for this project.**

| style | items |
|---|---:|
| ukiyo-e (Metropolitan Museum, CC0) | 55 |
| minimal-geometric (generated and curated by Kylian) | 52 |
| retro-poster (Library of Congress, public domain) | 41 |

Split **124 train / 17 validation / 7 holdout**. The **holdout never entered a training run.**

Every item is **CC0, public domain, or made for this project** — no third-party licensed work. The
**licence and source URL were recorded before an item entered a split**, as a gate rather than an
audit afterwards. Raw images are git-ignored; the manifest is committed.

Captions are **style-only**, selected over verbatim descriptions by a blinded A/B at Gate 1.

Memorisation is **bounded, not settled**: nearest-neighbour checks against the holdout flagged
**0 of 252** in the final matrix. `dHash ≤ 6` is a coarse near-copy indicator, **not proof**.

### 4.14 Process totals

**40 registered experiments · 17 decision records · 6 prototypes (P0–P5) · 2 human approval gates.**

---

## 5. Current test counts — measured 2026-08-14

**The deck previously showed 489 as the suite total. That figure is the M9 close and is now
stale.** Measured in this environment on 2026-08-14:

| suite | count | note |
|---|---:|---|
| **pytest, total** | **527** | full repository run |
| — system (product + research) | 473 | `apps/`, `ml/` |
| — report validation | 16 | every quantitative claim vs its evidence file |
| — deck validation | 38 | the same, for the presentation |
| **vitest** | **183** | 12 files |
| **Playwright end-to-end** | **38** | 6 files |

**On the slide:** the **527 total**, plus vitest and Playwright, and the clean-clone validation.
**In the notes only:** the three-way split, and that 473 of them test the system while the rest test
the documents.

**The line that matters more than any number:** *automated tests prove behaviour, not visual
quality. Only the human gates judged whether the pictures were good.*

The clean-clone test is the one worth naming: clone into an empty directory, install from scratch,
reach a working system. **It caught an integrity control that had only ever passed on the machine
that wrote it** — it had been green for weeks while verifying nothing.

---

## 6. Current speaker notes

These are the notes as they stand in the repository. They are the **narrative to preserve**; the
next session may rewrite them for natural delivery, keeping the claims and the bounds intact.

They should sound like Kylian speaking, not like a paper being read. Short sentences. Say numbers the
way a person says them ("two hundred megabytes", not "200.0 MiB"). Keep technical terms where they
carry weight and explain them in half a sentence.

**Slide 1 — 0:15**
> Good morning. I am Kylian Algoet, and this is DeckForge AI. What I am defending is not the demo.
> It is the research: what fits in eight gigabytes, and how I established it.

**Slide 2 — 1:01**
> A skateboard manufacturer wants customers to design their own decks. Today that needs a designer
> for every order, which does not scale to one-offs.
>
> The assignment sets four things: a self-trained model, both a prompt and a reference image, an
> interactive three-D deck, and reproducibility by someone else. The hard part is that all of it
> runs on one consumer laptop GPU.
>
> Every clause of the question was chosen to be falsifiable. Distinct styles is a claim needing
> evidence, not an adjective. Reproducible quality is where my answer splits in half. And eight
> gigabytes is a number, so a configuration either fits or it does not.
>
> This is assessed on the research process. So when I show you a failure later, I am not apologising
> — I am showing you the deliverable.

**Slide 3 — 1:14**
> The number the whole project is built around. Under real serving the device is essentially full:
> two hundred megabytes spare, two point four per cent. It fits, and not easily. I never call it
> headroom.
>
> One distinction I would defend if you push on it. Peak allocated tensors are about five gigabytes
> — that is not the margin. The rest of the device is the CUDA context, the allocator's cached pool
> and the display. Only device occupancy is comparable with the card's total.
>
> Six prototypes, each answering the question the next depends on. Building the three-D deck first
> made the deck's aspect ratio a hard input to the image problem, and caught an orientation fault
> that square test images would have hidden.
>
> Every choice ran the same loop, with the criteria fixed before the experiment. Gate one was
> blinded; gate two had to be labelled, because you cannot choose which checkpoint ships without
> knowing which one you are looking at.

**Slide 4 — 1:00**
> I assembled and curated the dataset for this project, and it is where a lot of the work went. A
> hundred and forty-eight items: ukiyo-e woodblock prints from the Metropolitan Museum,
> minimal-geometric that I generated and curated, and retro silkscreen posters from the Library of
> Congress. The seven-item holdout never entered a training run, so I had something honest to test
> memorisation against.
>
> Licensing was decided before training rather than justified afterwards, and the ordering is the
> point. Everything is CC-zero, public domain, or made by me, so the fair-use argument never has to
> be made. A licence went into the manifest as a condition of entering a split.
>
> The captions were an experiment, not a preference: verbatim descriptions taught the model to
> reproduce the caption rather than the style.

**Slide 5 — 1:04**
> The decision I expected to go the other way, and the one that set the method for everything after.
>
> I benchmarked SD 1.5 against SDXL on identical prompts and seeds. At its designed resolution —
> these images — SDXL is better. My own rubric scores say so, and I left that in the report.
>
> I rejected it anyway: ten point seven gigabytes allocated at one thousand and twenty-four square,
> on an eight gigabyte card.
>
> The important part is that it did not crash. Windows spills GPU memory into system RAM, so all
> thirty runs completed and reported success. Judged by exit code, SDXL was fine — and I would have
> built the whole project on it and found out in the last month.
>
> That is where one habit came from: a successful run is not a run that fitted.

**Slide 6 — 1:08**
> The decision where the criteria mattered most.
>
> Two realistic ways to condition on a reference. img2img starts the diffusion from the reference
> itself and costs nothing extra. IP-Adapter encodes it and injects it through cross-attention,
> which costs VRAM I did not have. On a card with two hundred megabytes spare, that should have
> ended the argument.
>
> Look at the pairs. Left is the reference the user supplied, right is what img2img returned at the
> deck format. Several are perceptually the same image. Every near-copy flag in that milestone came
> from img2img; none came from IP-Adapter.
>
> So I rejected the cheaper method on what it does, not what it costs. A system that hands back the
> customer's own upload with a filter on it is not a generator — and on a product where people
> upload artwork they care about, that is also the failure mode with legal consequences.

**Slide 7 — 1:25**
> My favourite result, and I only have it because of a process decision.
>
> Same style, same prompts, same seeds. Left is three hundred training steps, right is six hundred.
> Six hundred is more stylised — and less obedient. Prompt adherence dropped from four to three
> while style consistency held at five. The model got better at the style by getting worse at
> listening to you. On a product where the customer types what they want, that is the wrong trade.
>
> So two of three adapters ship from step three hundred, not the six hundred they trained to. I only
> saw that because I checkpointed four times along each run and had them scored blind. One global
> step count would have got two styles out of three wrong.
>
> Full fine-tuning does not fit, and training from scratch was infeasible within this project's
> compute and data budget. LoRA trains a small pair of matrices beside a frozen base model.
>
> The honest bound: I did not prove LoRA beats the alternatives. Three of them were screened on
> criteria and never run, so that question is bounded, not answered.

**Slide 8 — 1:23**
> A limitations slide that is only a formality is worse than none.
>
> One of my three styles is a partial pass. The training material is silkscreen posters, so almost
> all of it has a frame and display lettering as part of the composition, and the adapter learned
> all of that. Ask for a mountain and you get a mountain inside a poster frame. I could have dropped
> the style, or re-scored it until it passed. I shipped it labelled.
>
> Second, a question I set out to answer and did not. Same style on twelve, twenty-four and
> forty-four images, everything else fixed. I expected a plateau; what I got was non-monotonic, one
> run per condition, so I cannot separate a real effect from variance. It would have been easy to
> write that forty is enough, and nobody would have checked.
>
> Third, and I would rather raise it myself. Scoring was AI-assisted: ChatGPT proposed visual
> analysis and scores at the gates, and I reviewed and approved every recorded score. But there was
> no second independent human rater, so I cannot report inter-rater agreement.

**Slide 9 — 0:48**
> Two processes on one machine: a React frontend with the Three.js deck, and a FastAPI service that
> owns the model.
>
> The single worker is what I would point at. It is asserted at startup, because a second resident
> pipeline does not fit in what is left. Two simultaneous requests, and the second gets a clean
> refusal rather than an out-of-memory crash that takes the first down with it. Refusing correctly
> is a feature here.
>
> Generation goes straight to the deck's tall ratio rather than cropping a square. I expected that
> to hurt; I wrote it down as a hypothesis, tested it, and it was refuted.

**Slide 10 — 0:52**
> The number is split on purpose. Four hundred and seventy-three cover the product and the research
> code; the rest test the documents — that every quantitative claim in the report and on this deck
> still matches its evidence file.
>
> The one that earned its place is the clean-clone test. Clone into an empty directory, install from
> scratch, reach a working system. It caught a real defect: a checkpoint integrity control that
> passed every time locally, because the path it checked only existed on my machine. It had been
> green for weeks while verifying nothing.
>
> The honest limit is the last line: those tests tell you the code does what I told it to. Not one
> tells you a generated deck looks good.

**Slide 11 — 1:06**
> The primary question asks for reproducible quality, and this is where my answer splits in half.
>
> Inference is deterministic — and not just on my machine on the same day. A clean clone in a fresh
> environment, three days later, reproduced an earlier output byte for byte. Same hash.
>
> Training is not reproducible at all from its recorded seed. Two runs with identical configuration
> and an identical seed produced different weights, because the adapter initialisation draws from an
> unseeded global generator. The seed I was diligently recording never governed the part that
> mattered.
>
> So the checkpoints are artifacts, not recipes. Their hashes are verified on every request, and the
> deployment docs say plainly that three required files cannot be regenerated.
>
> The part worth pushing on is that this defect produces runs that look completely fine. It is
> invisible unless you compare weights.

**Slide 12 — 1:03**
> Is it actually deployed is a fair question, and the answer needs no spin. There is no public URL.
> It runs locally, and that was a choice between four compared options rather than something I ran
> out of time for.
>
> Not cloud, because it adds a network dependency on the one day everything must work and — the
> deciding part — answers nothing. The question is what fits in eight gigabytes of consumer
> hardware. A rented data-centre card replaces that question rather than answering it.
>
> Not Docker, because GPU passthrough was never verified here and its overhead is unmeasured, which
> on this margin is disqualifying.
>
> What I do claim is reproducibility, and it rests on the runbook and the clean-clone test — a
> stronger claim than a URL, which only proves it runs where I put it.

**Slide 13 — 0:48**
> The answer is yes, and the useful part is the specificity: I can name the configuration that fits,
> with the memory reading behind each element.
>
> But the bounds matter more than the yes, so I state all three every time. The margin is two point
> four per cent — it fits, not comfortably. Reproducible describes inference, not training. And
> multiple distinct styles means three, one of which is partial.
>
> The second half is what I would most like to be judged on: things I could easily have concluded
> and did not, because I did not measure them. None of them is in the report.

**Slide 14 — 0:15 spoken handoff, then the demo**
> "This runs locally, on this laptop's GPU. The three styles are not prompt tricks — they are
> adapters I trained on the dataset I showed you."

*(The rest of slide 14's note is stage directions, not narration — see §7. It is excluded from the
spoken total.)*

**Slide 15 — 0:46**
> Three things I would change.
>
> Repeat every condition before drawing a curve. The image-count question is inconclusive because I
> ran each condition once — a planning mistake, not a resource one.
>
> Seed everything, then verify by comparing weights rather than trusting the log. I was confident
> about reproducibility for weeks, and only found out because I tried to reproduce a result instead
> of assuming I could.
>
> And get a second rater.
>
> That last line is what I would like to be judged on: conclusions that stop where the evidence
> stops. Thank you — I am happy to take questions.

---

## 7. Demo flow and fallback

**Target 4:00 live.** Full script: `docs/presentation/demo-script.md`. Backup:
`docs/presentation/demo-backup-plan.md`.

### The mechanic that makes it work

**Press Generate early and keep talking.** A warm generation is **~13 s**, a cold one **~30 s**.
Both are dead air if you stop, and both are enough time to explain the progress panel if you do not.

### Flow

| time | what |
|---|---|
| 0:00–0:30 | what it is and why — local GPU, three trained styles |
| 0:30–0:45 | the controls: prompt, style, optional reference image |
| **0:45** | **press Generate** |
| 0:45–1:30 | talk over the generation — the progress panel reports **real diffusion steps** |
| 1:30–1:50 | the result, and its metadata: seed, pinned model revision, adapter hash, measured VRAM |
| 1:50–2:30 | the 3D deck, including the stretch disclosure |
| 2:30–2:50 | `Upload your own decal` — **also the fallback, so the room has seen it work** |
| 2:50–3:30 | what the research actually found |
| 3:30–4:00 | reproducibility, and close |

**Suggested prompt:** *a mountain and a rising sun*, style **Ukiyo-e** — the unambiguous pass, and it
reads well at a distance.

**Do not generate with `retro-poster`.** It is the partial pass; demonstrate it in words and generate
with a full pass.

### Fallback — approved wording

> **"If live generation fails, I switch to a validated recorded run and state that explicitly."**

Then go to `Upload your own decal` with a pre-generated PNG **and name which recorded run it is**.

**Do not** reload, retry, open a terminal, or run a second generation. **Do not editorialise about
whose fault the failure is** — the older wording *"that is a live-demo problem, not a project
problem"* is defensive and has been removed everywhere.

The failure ladder has four rungs, each executable in under 30 seconds: keep talking → upload a
pre-generated PNG → pre-captured screenshots → slides carrying the same screenshots.

**If the output ignores half the prompt, that is not a failure — it is the prompt-adherence
limitation demonstrating itself.** Say so and use it.

---

## 8. Jury Q&A — summary

**A detailed document already exists: `docs/presentation/jury-questions.md`.** It holds full answers
with evidence paths, written for 30–60 seconds each.

**Slides do not need to pre-answer every question.** Do not overload a slide to defend an edge case
— that is what the Q&A document and the speaker notes are for.

One-line positions on the likely questions:

| question | position |
|---|---|
| What exactly did you train? | Three LoRA adapters, rank 8, on my own 148-item dataset. The base model is pretrained SD 1.5 |
| Why call it self-trained? | The styles are trained by me; the base model is not, and the report says so |
| Why LoRA? | It fits in 8 GB and trains in minutes. **Feasibility, not superiority** |
| Why not from scratch? | Infeasible within this project's compute and data budget |
| Why SD 1.5 / why not SDXL? | SDXL scored better and needed 10 738 MiB at 1024². It spilled to host RAM instead of failing |
| Why IP-Adapter? | img2img returned near-copies at the deck format — two at dHash 0 |
| Dataset licensing? | CC0, public domain, or made for the project. Licence recorded **before** the split |
| How do you know the styles were learned? | Human-scored rubric at two gates, plus base-model controls |
| Why is retro-poster partial? | It learned poster frames and lettering, not only style. Shipped labelled |
| Why is RQ4 inconclusive? | 12/24/44 non-monotonic, one run per condition |
| How reproducible? | Inference byte-for-byte on a clean clone. **Training not, from seed** |
| Why is training not reproducible? | Adapter init draws from an unseeded global RNG |
| Why local? / Is it deployed? | Four options compared; local selected. No public URL, deliberately |
| Why one worker? | ~200 MiB spare — a second resident pipeline does not fit. Concurrency gets a 409 |
| What would you change? | Repeat conditions; seed and verify weights; get a second rater |
| How was Claude Code used? | Documented per session in `docs/ai-usage.md`, including what it got wrong |
| Which decisions were Kylian's? | All gate decisions, production selections and research conclusions |
| Biggest limitation? | Evaluation: one approver, AI-assisted analysis, no inter-rater agreement |

---

## 9. Design direction

Design a **real bachelor-defence deck**, not a report exported to slides.

**Aesthetic:** modern, premium, minimal, technical, editorial. Skateboard / creative-tech identity.
Dark and light used intentionally as a system, not decoratively. Bold typography. Large evidence
images. Strong visual hierarchy.

**Avoid:** generic corporate PowerPoint, AI-gradient clichés, icon soup, decorative graphics that
carry no information, and walls of text.

**Every important element must be readable from the back of a classroom.**

**One central message per slide.** Prefer **image + statement**, **comparison + conclusion**,
**diagram + takeaway** over bullet lists.

### Permitted

Rearranging text · shortening visible copy · moving detail into speaker notes · cropping evidence
images · combining evidence images · creating diagrams from the verified facts above · using
typography to make quantitative comparisons land · changing backgrounds and layout · adding labels,
arrows and callouts · making quantitative relationships graphical.

### Forbidden

Fake screenshots · fake generated outputs · invented experiment results · altering evidence imagery
misleadingly · fabricated metrics · **upgrading any bounded finding** · implying an experiment was
performed when it was only screened.

---

## 10. Claims Claude must never make

1. SD 1.5 is better than SDXL. *(It is not — it fits.)*
2. IP-Adapter is universally better than img2img.
3. LoRA is the best fine-tuning method, or the alternatives were measured.
4. retro-poster passed.
5. Any minimum image count, or that ~40 images is enough.
6. The system is reproducible, without splitting inference from training.
7. Training can be repeated from its recorded seed.
8. All visual scoring was blind.
9. Scoring was entirely the student's, with no AI assistance.
10. The system is deployed publicly, or hosted online.
11. Internet hosting is impossible.
12. `8187.5 − 5143.73` is the memory margin.
13. 200 MiB is comfortable headroom.
14. Multiple users can generate concurrently.
15. The test suite proves the generated images are good.
16. Any timing figure is a measured rehearsal.
17. A generation total other than 27.
18. "Production-ready", "state-of-the-art", "seamless", "fully tested/automated".

---

## 11. Known issues with the current PDF

The current `deliverables/DeckForge-AI-presentation.pdf` is a **content reference, not a visual
target**.

1. **Slide 9's architecture diagram rendered as literal source code** in an earlier PDF — 16
   `<text>`, 3 `<rect>` and 3 `<line>` elements printed as escaped markup. **Root cause:** CommonMark
   ends an HTML block at the first blank line, and the inline SVG contained 5 blank lines, so
   everything after the first was escaped. Fixed in-repo and now guarded by a test — **but the
   diagram should be redrawn, not extracted.**
2. **Slide 6's comparison is too small to read at presentation distance.** See the asset manifest for
   the exact crop.
3. **Slide 8 is visually dense.** Keep every limitation; simplify the presentation.
4. **Slide 10 previously showed 489** as the suite total. Corrected to **527**.
5. **Slide 14's fallback wording** was defensive. Corrected.

---

## 12. Current M10 state

**M10 is OPEN. It is not complete and must not be recorded as complete.**

| item | state |
|---|---|
| deck content and structure | drafted, restructured, **content-reviewed and corrected** |
| 15-slide structure | **approved** |
| non-GPU validation | **passing** |
| **visual human gate** | **OPEN** |
| **timed rehearsal / criterion C** | **OPEN — never run** |
| backup demo rehearsal | **OPEN** |
| final PDF export | pending the visual redesign |
| push / issue closure | **NOT DONE** |

Still required before M10 can close: human visual approval · a real timed rehearsal · a backup demo
rehearsal · criterion C · final PDF export · push and closure.
