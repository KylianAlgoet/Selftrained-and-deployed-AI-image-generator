# <span class="section-number">17</span> Ethics, copyright, privacy and bias

## 17.1 Training data and copyright

Generative image models are contested precisely because of what they are trained on. This project
cannot resolve that debate, but it can be answerable for its own dataset, and it was designed to be
from the first day.

**Every one of the {{ facts.dataset_total }} items is public domain, CC0, or created for this
project.** No item entered a training split before its licence and source were recorded. Stock-photo
"free" tiers, scraping and AI-generated seed imagery were rejected as source categories, and the
source registry required human approval before any download.

The distinction that matters: this is a claim about **what was collected**, and it is verifiable
per item from the manifest (§10.2).

<div class="callout">
<span class="callout__label">The limitation this does not escape</span>
The <strong>base model</strong> was not trained by this project. Stable Diffusion 1.5 was trained on
a large web-scraped corpus whose licensing is the subject of active dispute and litigation. A
clean fine-tuning dataset does not make the base model's provenance clean, and no amount of care in
§10 changes that. <strong>The output of this system inherits the base model's provenance</strong>,
and any commercial deployment would have to confront it directly.
</div>

There is a second inheritance. The model card for the base weights states that the model "is intended
for research purposes only" [10]. This project is research and sits inside that intent, but the
assignment frames a commercial client, and a real deployment would need a licence position this
report is not in a position to give.

## 17.2 Reproducing the reference image

A reference-conditioning feature can become a copying machine, and in this project it demonstrably
did — the measured result is in §11.2.

The ethical reading of that result is what belongs here. Had img2img been selected for its zero
memory cost, the system would have offered users a route to reproduce any image they uploaded. That
is a problem about what a product invites people to do, and it would have existed regardless of
whether anyone noticed the perceptual-hash flags. **The method that was rejected was the cheaper
one**, and it was rejected on this behaviour rather than on quality.

Flagged outputs are surfaced rather than deleted, and the rejected method survives only as a
documented fallback with its behaviour stated.

**Memorisation of training data** was checked separately and found none — which, as §13.5 states, is
a coarse indicator rather than proof.

## 17.3 Privacy and untrusted input

**In the dataset:** no identifiable living persons, no personal data in filenames or metadata, and
historical artworks only from institutional public-domain collections.

**In the running system:** every upload is untrusted input reaching an image decoder, and is treated
as hostile. Extension and MIME allowlisting, mismatch detection, actual decode validation, size and
dimension limits, decompression-bomb rejection, random internal filenames, and traversal prevention —
twenty-seven rules, each with at least one negative test (§15.5).

The structural decision matters more than the rules: **generation identifiers resolve through a
registry lookup, never a path join.** A traversal string has nothing to traverse, rather than being
sanitised and hoped about. Errors are safe by design — no local paths, no stack traces — and metadata
never contains a filesystem path.

**Uploaded decals never leave the browser.** The `Upload your own decal` feature decodes locally,
sends nothing to the server and never touches the model, and that is proved from server-side request
counts rather than asserted (§14.5).

## 17.4 Bias

Three biases are present in this system and are named rather than managed away.

**The dataset is culturally narrow, and unevenly so.** Two of three styles are Western institutional
archive material; the third is Japanese woodblock print, collected from a Western museum's
digitisation of it. A model trained on {{ facts.dataset_ukiyo_e }} ukiyo-e prints from one
institution's holdings learns that institution's collecting history — what it acquired, from whom,
and what it chose to digitise — not the tradition itself.

**One style is synthetic.** `minimal-geometric` was generated programmatically by this project, so it
contains exactly the biases of the generator that made it: six palettes, six shape counts, and
nothing else. It is the easiest style to fit, and §13.3 notes its lowest final loss is a property of
that synthetic simplicity rather than a quality result.

**The base model's biases are inherited wholesale** and were not measured. Diffusion models trained
on web-scale data carry well-documented representational skews. This project ran no bias evaluation
of generated output, and **does not claim the system is unbiased** — it claims only that the
fine-tuning data's composition is documented and inspectable.

## 17.5 Honest representation of what the system is

Two design decisions in this project are ethical positions about not misleading a user, and both cost
something to hold.

**The progress display refuses to invent a number.** Only denoising has a real denominator, so
loading, decoding and saving publish a stage name and no percentage, and the one-second finalising
step is not padded to make the label linger (§14.3). A weighted fake percentage would have looked
better.

**A weaker style ships with its weakness visible.** `retro-poster` is a partial pass, and the
application warns on **every request** for it rather than confining the caveat to documentation
(§14.6). The same applies to the prompt-adherence limitation, which was found during a walkthrough
and preserved rather than hidden by rewriting user prompts behind their back.

## 17.6 What was not addressed

- **No content filter.** The safety checker is present but disabled, as is conventional for research
  use; a deployed system serving customers would need a moderation position this project does not
  take.
- **No provenance marking.** Generated images carry reproducibility metadata but no watermark or
  C2PA-style content credential.
- **No bias evaluation of output**, as above.
- **No consent mechanism** for uploaded reference images beyond the fact that they are processed
  locally in the browser for decals and transiently for conditioning.

Each is a real gap. They are listed here rather than in §23 because they are not features that were
postponed — they are questions a commercial deployment would have to answer before launch.
