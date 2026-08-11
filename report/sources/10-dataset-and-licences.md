# <span class="section-number">10</span> Dataset methodology and licences

## 10.1 What was built

**{{ facts.dataset_total }} items across three styles**, every one public domain, CC0 or created for
this project, with its licence and source recorded per item before it was permitted into a training
split.

| style | items | licence | source |
|---|---:|---|---|
| ukiyo-e woodblock | {{ facts.dataset_ukiyo_e }} | CC0 [14] | Metropolitan Museum of Art, open access [12] |
| minimal geometric | {{ facts.dataset_minimal_geometric }} | project-original | seeded programmatic generation |
| retro silkscreen poster | {{ facts.dataset_retro_poster }} | public domain | Library of Congress — WPA / Federal Theatre Project [13] |
| **total** | **{{ facts.dataset_total }}** | | |

Splits: **{{ facts.dataset_train }} train**, **{{ facts.dataset_val }} validation**,
**{{ facts.dataset_holdout }} holdout**. The holdout items were never seen by any training run and
are the reference images used to test conditioning (§11.2), which is what makes "the adapter has not
simply memorised its inputs" a testable statement rather than an assumption.

<figure>
<img src="docs/evidence/dataset-v1/contact-sheet-ukiyo-e.jpg" alt="Contact sheet of the ukiyo-e portion of the dataset">
<figcaption><span class="caption__label">Figure 2.</span> The ukiyo-e portion of dataset-v1, CC0
from the Metropolitan Museum of Art. Contact sheets were generated per style for visual inspection
and are part of the evidence set rather than illustration.
<span class="caption__source">docs/evidence/dataset-v1/contact-sheet-ukiyo-e.jpg</span>
</figcaption>
</figure>

## 10.2 Licensing policy

The policy was written before any file was downloaded, and it is restrictive on purpose:

- **Permitted licences: public domain, CC0, project-original.** Nothing else enters the manifest.
- **Rejected outright:** stock-photo "free" sites, scraping, and AI-generated seed imagery.
- **Every item's licence and permitted use is recorded before it may enter a training split**, in a
  manifest carrying `source`, `author`, `licence`, `collection_date`, `permitted_use`, dimensions,
  SHA-256 and split.
- **The concrete source registry required explicit human approval before any download.** No source
  was added to it by an assistant.

Exclusions are equally explicit: identifiable living persons, visible brands, logos or trademarks,
NSFW content, contemporary artist-attributed works, watermarked images, and near-duplicates.

**One style choice was made for licensing reasons and it is worth stating plainly.** The original
plan called for graffiti and street art. Graffiti photography is generally artist-copyrighted, and
building a training set from it would have been either a licensing violation or an exercise in
optimistic labelling. It was replaced with ukiyo-e woodblock prints, which have large, explicit,
institutionally documented public-domain supply. The visual intent — bold, graphic, high-contrast
source material — survived the substitution.

## 10.3 The pipeline

Nine stages, each scripted and tested: decode validation, SHA-256 hashing with exact-duplicate
detection, perceptual near-duplicate detection, resolution and aspect statistics, a normalisation
policy, caption tooling, deterministic seed-fixed split assignment, per-style statistics, and contact
sheets for visual inspection.

Raw imagery is **not committed**. Manifests, statistics and contact sheets are. Model weights never
are (§16.3).

The manifest is hash-locked and a test asserts it has not changed. During the style-learning
milestone it was opened **read-only throughout**, so the claim that the dataset did not move during
training is checkable rather than asserted.

## 10.4 Two findings that were recorded before they were convenient

Both were noticed while re-inspecting the poster contact sheet during a pre-check, **before any
training run**, and both were recorded as open risks to the results rather than quietly fixed.

**Framed and matted scans.** Most `retro-poster` items are photographed or scanned with visible dark
frames and cream mats. A style adapter could learn the frame as part of the style. A border-darkness
measurement taken before training flagged **35 of 36** training items, with a median border delta of
**−73.5**, against **+29.7** and 2 of 44 for ukiyo-e.

**Text-dominated source material.** Display typography is a defining feature of WPA posters, and
diffusion models render text poorly. Only **14 of 36** poster captions describe anything visible; 20
of 41 are play-title attributions.

**Both were confirmed to transfer.** The style-learning gate marked unwanted framing and pseudo-text
worse than baseline on **every** trained poster sheet, and that is why `retro-poster` ships as a
partial pass rather than as an equal (§11.4, §18.1).

## 10.5 The mitigation that was chosen, and the one that was not

Two mitigations were available: crop the source material, or change the captions.

**Captions were chosen.** A style-only caption strategy was tested as a **blinded A/B changing
exactly one variable** and selected by the student at the first review gate. The dataset was
**never modified** — it remains byte-identical to its recorded hash and was opened read-only for the
whole milestone.

The reasoning is recorded: a crop pass would have altered the dataset for one style only, breaking
comparability with every earlier result, while the caption route was testable without touching a
single source file.

**What this does not establish**, stated in the methodology rather than left implicit: the caption
A/B ran on `minimal-geometric`, not on `retro-poster`. Style-only captions are therefore selected on
evidence from the lead style plus the pre-training audit — **not** on a measured poster comparison.
Removing frames at the pixel level was never tested and remains open (§23).

## 10.6 A correction to how these findings were first described

The initial write-up framed one reference image as the difficult case because it was framed and
text-heavy. Opening the actual image showed that a second reference was **also** a framed,
text-dominated poster scan; the first was harder only because it added landscape orientation, the one
orientation a deck cannot accommodate.

The correction is recorded in the dataset methodology, and it made the problem **more** widespread
than the original wording implied rather than less. It is included here because it is a small example
of the rule the whole project runs on: check the artefact, not the description of it (§21).
