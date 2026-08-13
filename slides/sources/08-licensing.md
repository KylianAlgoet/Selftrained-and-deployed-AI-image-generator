- Every item is **CC0, public domain, or created for this project**. There is no third-party licensed work in the training set
- **Licence and source URL recorded per item, in the manifest, before the item entered a split** — not audited afterwards
- Raw images are **git-ignored**; the manifest is committed. The evidence is the record, not the pixels
- Memorisation was **tested, not assumed** — nearest-neighbour checks against the holdout
- **What I cannot claim:** those checks bound copying, they do not prove it never happens

<p class="source">data/manifests/dataset-v1.csv · DR-006 · EXP-035 · report §10, §17</p>

## Speaker notes

Licensing was decided before training rather than justified afterwards, and the ordering is the
point.

Everything is CC0, public domain, or made by me. No third-party licensed artwork at all — so the
fair-use argument never has to be made.

Each item's licence and source URL went into the manifest as a condition of entering a split.
Provenance is a gate the data passed through, not a report I wrote at the end.

The raw images are git-ignored and the manifest is committed. The record is the evidence, not the
pixels.

On memorisation: nearest-neighbour checks against the holdout bound the risk. They do not eliminate
it, and the report says that rather than rounding up to "the model does not copy". That distinction
is what I would defend if you push.
