# Reference retrieval record

**Date:** 2026-08-11 · **Milestone:** M9.8 · **Purpose:** record which cited sources were retrieved
and read, and which could not be, so the bibliography's provenance is checkable.

The rule this milestone works to: **no source is cited that has not been retrieved and inspected**,
and a search-engine extract is never presented as though the page itself had been read.

## Retrieved and read — 18 of 20

All arXiv abstract pages, both Hugging Face model cards and the Creative Commons deed were fetched
successfully and their titles, author lists, identifiers and licence designations were read from the
retrieved page.

| ref | source | retrieved |
|---:|---|---|
| 1 | Rombach et al., latent diffusion, arXiv:2112.10752 | yes |
| 2 | Podell et al., SDXL, arXiv:2307.01952 | yes |
| 3 | Hu et al., LoRA, arXiv:2106.09685 | yes |
| 4 | Ye et al., IP-Adapter, arXiv:2308.06721 | yes |
| 5 | Ruiz et al., DreamBooth, arXiv:2208.12242 | yes |
| 6 | Gal et al., Textual Inversion, arXiv:2208.01618 | yes |
| 7 | Zhang et al., ControlNet, arXiv:2302.05543 | yes |
| 8 | Radford et al., CLIP, arXiv:2103.00020 | yes |
| 9 | Lu et al., DPM-Solver++, arXiv:2211.01095 | yes |
| 10 | Hugging Face `stable-diffusion-v1-5/stable-diffusion-v1-5` | yes — licence and intended-use statement read from the model card |
| 11 | Hugging Face `h94/IP-Adapter` | yes — licence and adapter file list read from the model card |
| 14 | Creative Commons CC0 1.0 Universal deed | yes |
| 15–20 | Diffusers, PEFT, PyTorch, FastAPI, Three.js, Playwright | identifying citations for tools whose exact versions are pinned in the repository |

## NOT retrieved — 2 of 20

Two institutional policy pages could not be fetched from this environment. Both were attempted
repeatedly, on two occasions, across multiple official paths.

| ref | source | attempts | result |
|---:|---|---|---|
| 12 | The Metropolitan Museum of Art — Open Access / Image and Data Resources | `metmuseum.org/policies/image-resources` ×2 · `metmuseum.org/hubs/open-access` ×1 · `metmuseum.org/perspectives/open-access` ×1 · `metmuseum.org/information/terms-and-conditions/open-access` ×1 | **HTTP 429 Too Many Requests**, every attempt |
| 13 | Library of Congress — Rights and Access, WPA Posters | `loc.gov/collections/works-progress-administration-posters/about-this-collection/rights-and-access/` ×2 · `loc.gov/legal/` ×1 · `loc.gov/free-to-use/wpa-posters/` ×1 · `loc.gov/collections/federal-theatre-project-1935-to-1939/about-this-collection/rights-and-access/` ×1 | **HTTP 403 Forbidden**, every attempt |

The 403 is consistent with a web application firewall rejecting the fetch agent; the 429 is a rate
limit that did not clear between attempts separated by the rest of the milestone's work.

### What was done about it

**Nothing was invented, and no search extract was promoted to a quotation.** An earlier draft of the
reference chapter paraphrased search-engine extracts of these two pages. That material has been
**removed** from the bibliography, because a snippet is not an inspected source.

The citations remain in the bibliography with their **official primary URLs**, so a reader with an
unblocked connection can verify them directly. What the report says about them is limited to the
policy names, which are not in dispute, and every statement is qualified.

### Why this does not weaken the licensing evidence

**The institutional pages were never the project's primary licensing evidence.**

That evidence is `data/manifests/dataset-v1.csv`, which records for **every one of the 148 items**
its `source` URL, `author`, `licence`, `collection_date` and `permitted_use` — captured **at the
moment the item was collected**, when those servers were reachable. The manifest is in the
repository, is hash-locked, and a test asserts it has not changed.

Per-item licence values as recorded: 55 `CC0`, 52 `project-original`, 41 `public domain`.

The bibliography entries are supporting context for a reader; the manifest is the evidence.

### The pattern this repeats

This is the **fourth** time third-party hosting has obstructed this project, and the risk register
anticipated it after the first three:

1. Digital Comic Museum — Cloudflare gating, during dataset collection (M2);
2. Art Institute of Chicago — image CDN 403, during dataset collection (M2);
3. `stabilityai/stable-diffusion-2-1-base` — HTTP 401 gating, during the base-model benchmark (M3),
   which is why that decision rests on two measured candidates rather than three;
4. **The Met and the Library of Congress — 429 and 403, while writing the bibliography (M9).**

The mitigation adopted after the first three — pin immutable revisions, record provenance at the
moment of use, treat each block as a first-class result rather than a nuisance — is exactly what
makes this fourth occurrence a documentation footnote instead of a gap in the evidence.
