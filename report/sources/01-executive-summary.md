# <span class="section-number">1</span> Executive summary

DeckForge AI is a working system that lets a customer of a skateboard manufacturer describe a deck
graphic in words, optionally upload a reference image, choose one of three visual styles, and see the
generated artwork on an interactive 3D skateboard deck before downloading it. The image model is
fine-tuned locally, on a single consumer laptop GPU, from a dataset built for this project.

The engineering result is that it works. The research result is more specific, and more useful: it is
a measured account of what fits in **8 GB of video memory**, what does not, and how the difference was
established rather than assumed.

## What was built

A local diffusion pipeline — Stable Diffusion 1.5, three per-style LoRA adapters trained for this
project, and IP-Adapter for reference-image conditioning — served by a FastAPI process behind a React
and Three.js frontend. Generation is direct to the deck format,
{{ facts.generation_width }}×{{ facts.generation_height }} pixels, and the result is mapped onto a
procedurally generated 3D deck with correct nose-to-tail orientation.

The dataset holds **{{ facts.dataset_total }} items** across three styles, every one of them public
domain, CC0 or created for this project, with its licence and source URL recorded per item before it
was allowed into a training split.

## What the research established

Six prototypes were built in sequence, each answering a question the next one depended on. Forty
experiments are registered with their configuration, measured hardware readings and conclusions.

The central constraint governed every decision. SDXL produces better artwork than SD 1.5 at its
native resolution — the student's own rubric scores say so — and it was **rejected anyway**, because
at 1024×1024 it allocated 10 738 MiB on a card with {{ facts.device_total_mib }} MiB. Windows spilled
silently into host memory rather than raising an out-of-memory error, so all thirty runs "succeeded".
That experiment set the method for everything after it: **read every memory figure against the
ceiling, never against whether the run crashed.**

The production stack fits that ceiling with **{{ facts.worst_spare_mib }} MiB to spare** under real
serving conditions — 2.4 % of the device. This is not comfortable headroom, and the report does not
describe it as such. It is why the service runs exactly one worker with one resident pipeline.

Reference conditioning went to IP-Adapter at scale {{ facts.ip_adapter_scale_default }} rather than
img2img, on evidence that was sharper than expected: every near-copy flag in that milestone came from
img2img at the deck format, some of them perceptually indistinguishable from the reference image. A
method that reproduces its input is not a generator.

Style learning produced three adapters at a default weight of {{ facts.lora_weight_default }}. Two of
the three ship at **training step 300, not the 600 they were trained to** — prompt adherence fell
while style consistency held, so training longer made the model more stylish and less obedient. That
finding exists only because checkpoints were saved at four points and a human compared them.

## What did not work, and is reported as such

- **One style ships as a partial pass.** `retro-poster` learned the frames and display typography of
  the archive posters it was trained on. It is shipped with the limitation stated and a warning on
  every request, rather than dropped or quietly upgraded.
- **The image-count question is inconclusive.** Training on 12, 24 and 44 images produced a
  non-monotonic ordering, and no minimum count was established. It is reported as inconclusive.
- **Training is not bit-reproducible from its recorded seed.** The adapters must be preserved as
  artifacts, verified by SHA-256, because they cannot be regenerated. Inference, separately, *is*
  deterministic: a clean clone reproduced an earlier output byte for byte, three days later, in a
  freshly built environment.
- **One base-model candidate could never be measured.** SD 2.1 was gated behind authentication, so
  the model decision rests on two candidates rather than three.

## What it means

The system meets every mandatory requirement of the assignment, and the report states plainly where
its evidence stops. The strongest claim it makes is not that the pipeline works, but that the reasons
for each choice are measured, recorded, and in several cases the opposite of what was expected at the
start.
