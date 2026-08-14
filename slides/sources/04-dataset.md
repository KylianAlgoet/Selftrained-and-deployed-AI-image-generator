<div class="col-text">

- **{{ facts.dataset_total }} items**, three styles, built for this project — holdout of {{ facts.dataset_holdout }} never seen in training
- Every item is **CC0, public domain, or made for this project.** No third-party licensed work
- **Licence and source URL recorded before the item entered a split** — a gate, not an afterwards audit
- Captions are **style-only.** That was tested against verbatim descriptions, and style-only won

</div>
<div class="col-figure">
<figure>
<img src="docs/evidence/dataset-v1/contact-sheet-ukiyo-e.jpg" alt="Contact sheet of the ukiyo-e training images">
<figcaption><span class="label">Ukiyo-e split.</span> Metropolitan Museum of Art, CC0. Every item carries its licence and source URL in the manifest.
</figcaption>
</figure>
</div>

## Speaker notes

The dataset is mine, and it is where a lot of the work went. A hundred and forty-eight items:
ukiyo-e woodblock prints from the Metropolitan Museum, minimal-geometric that I generated and
curated, and retro silkscreen posters from the Library of Congress. The seven-item holdout never
entered a training run, so I had something honest to test memorisation against.

Licensing was decided before training rather than justified afterwards, and the ordering is the
point. Everything is CC-zero, public domain, or made by me, so the fair-use argument never has to
be made. A licence went into the manifest as a condition of entering a split.

The captions were an experiment, not a preference: verbatim descriptions taught the model to
reproduce the caption rather than the style.
