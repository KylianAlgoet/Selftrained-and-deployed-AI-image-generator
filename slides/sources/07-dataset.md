<div class="col-text">

- **{{ facts.dataset_total }} items**, three styles, built for this project
- Ukiyo-e **{{ facts.dataset_ukiyo_e }}** · minimal-geometric **{{ facts.dataset_minimal_geometric }}** · retro-poster **{{ facts.dataset_retro_poster }}**
- Split **{{ facts.dataset_train }} / {{ facts.dataset_val }} / {{ facts.dataset_holdout }}** — the holdout was never seen in training
- Captions are **style-only**, not verbatim descriptions. That comparison was run, and style-only won

</div>
<div class="col-figure">
<figure>
<img src="docs/evidence/dataset-v1/contact-sheet-ukiyo-e.jpg" alt="Contact sheet of the ukiyo-e training images">
<figcaption><span class="label">Ukiyo-e split.</span> Metropolitan Museum of Art, CC0. Every item carries its licence and source URL in the manifest.
</figcaption>
</figure>
</div>

## Speaker notes

The dataset is mine, and it is where a lot of the work went.

A hundred and forty-eight items across three styles: ukiyo-e woodblock prints from the Metropolitan
Museum, CC0; minimal-geometric, which I generated and curated; and retro silkscreen posters from
the Library of Congress, public domain.

The seven-item holdout never entered a training run, so I had something honest to test memorisation
against.

The captions were a real experiment, not a preference. Style-only against verbatim descriptions, on
the same images and seeds. Style-only gave better prompt adherence; verbatim captions taught the
model to reproduce the caption rather than the style.

If you ask about dataset size, my answer is honest and not flattering. That is slide sixteen.
