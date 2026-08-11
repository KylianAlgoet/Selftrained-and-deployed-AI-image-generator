# <span class="section-number">24</span> References

## 24.1 What is cited, and what is not

This project's quantitative claims are supported by **repository evidence**, not by literature. Every
memory figure, timing, hash, count and rubric score in this report cites a file in the repository,
because that is stronger evidence for a measurement taken on this machine than any external source
could be.

External references are therefore used for one purpose only: to identify the models, methods,
libraries and licence regimes the project **used**, so a reader can find the primary description of
each. No external source is cited as evidence for a measurement reported here.

**Nothing below was cited without being retrieved and read**, with two exceptions that are stated
explicitly in §24.4 rather than concealed.

## 24.2 Models and methods

<div class="references">

1. R. Rombach, A. Blattmann, D. Lorenz, P. Esser and B. Ommer, "High-Resolution Image Synthesis with
   Latent Diffusion Models", arXiv:2112.10752, 2021; CVPR 2022.
   `https://arxiv.org/abs/2112.10752` (accessed 2026-08-11).

2. D. Podell, Z. English, K. Lacey, A. Blattmann, T. Dockhorn, J. Müller, J. Penna and R. Rombach,
   "SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis", arXiv:2307.01952,
   2023. `https://arxiv.org/abs/2307.01952` (accessed 2026-08-11).

3. E. J. Hu, Y. Shen, P. Wallis, Z. Allen-Zhu, Y. Li, S. Wang, L. Wang and W. Chen, "LoRA: Low-Rank
   Adaptation of Large Language Models", arXiv:2106.09685, 2021.
   `https://arxiv.org/abs/2106.09685` (accessed 2026-08-11).

4. H. Ye, J. Zhang, S. Liu, X. Han and W. Yang, "IP-Adapter: Text Compatible Image Prompt Adapter for
   Text-to-Image Diffusion Models", arXiv:2308.06721, 2023.
   `https://arxiv.org/abs/2308.06721` (accessed 2026-08-11).

5. N. Ruiz, Y. Li, V. Jampani, Y. Pritch, M. Rubinstein and K. Aberman, "DreamBooth: Fine Tuning
   Text-to-Image Diffusion Models for Subject-Driven Generation", arXiv:2208.12242, 2022; CVPR 2023.
   `https://arxiv.org/abs/2208.12242` (accessed 2026-08-11).
   **Screened, never run** — see §9.2.

6. R. Gal, Y. Alaluf, Y. Atzmon, O. Patashnik, A. H. Bermano, G. Chechik and D. Cohen-Or, "An Image
   is Worth One Word: Personalizing Text-to-Image Generation using Textual Inversion",
   arXiv:2208.01618, 2022. `https://arxiv.org/abs/2208.01618` (accessed 2026-08-11).
   **Screened, never run** — see §9.2.

7. L. Zhang, A. Rao and M. Agrawala, "Adding Conditional Control to Text-to-Image Diffusion Models",
   arXiv:2302.05543, 2023. `https://arxiv.org/abs/2302.05543` (accessed 2026-08-11).
   **Compared on criteria, never implemented** — see §11.2.

8. A. Radford, J. W. Kim, C. Hallacy, A. Ramesh, G. Goh, S. Agarwal et al., "Learning Transferable
   Visual Models From Natural Language Supervision", arXiv:2103.00020, 2021.
   `https://arxiv.org/abs/2103.00020` (accessed 2026-08-11).
   The encoder family used both by IP-Adapter conditioning and by this project's similarity
   indicator — which is why §13.5 states that indicator is descriptive *within* a method rather than
   neutral *between* methods.

9. C. Lu, Y. Zhou, F. Bao, J. Chen, C. Li and J. Zhu, "DPM-Solver++: Fast Solver for Guided Sampling
   of Diffusion Probabilistic Models", arXiv:2211.01095, 2022.
   `https://arxiv.org/abs/2211.01095` (accessed 2026-08-11).
   The sampler used for every generation in this project.

</div>

## 24.3 Model weights actually used

<div class="references">

10. Stable Diffusion v1-5, repository `stable-diffusion-v1-5/stable-diffusion-v1-5`, licence
    CreativeML OpenRAIL-M. `https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5`
    (accessed 2026-08-11). **Pinned in this project at revision `451f4fe1…`.** The model card states
    the model "is intended for research purposes only"; §17 addresses this against the project's
    commercial framing.

11. h94/IP-Adapter, licence Apache-2.0, providing `ip-adapter_sd15` and `ip-adapter-plus_sd15` among
    others. `https://huggingface.co/h94/IP-Adapter` (accessed 2026-08-11).
    **Pinned in this project at revision `018e4027…`**; the base variant was selected and the Plus
    variant measured and not selected (§11.2).

</div>

**Both are pinned to immutable commit hashes.** That practice was adopted after three separate
third-party sources became unavailable mid-project (§12.1), and it is the reason the models this
report describes can still be identified exactly.

## 24.4 Dataset sources and licence regimes

<div class="references">

12. The Metropolitan Museum of Art, *Image and Data Resources* / Open Access policy.
    `https://www.metmuseum.org/policies/image-resources`
    Under this policy The Met makes images of artworks **it believes to be in the public domain**
    available under a Creative Commons Zero designation. Source of the
    {{ facts.dataset_ukiyo_e }} ukiyo-e items. **Retrieval blocked — see the note below.**

13. Library of Congress, *Rights and Access*, Posters: WPA Posters digital collection.
    `https://www.loc.gov/collections/works-progress-administration-posters/about-this-collection/rights-and-access/`
    Related, for Federal Theatre Project material:
    `https://www.loc.gov/collections/federal-theatre-project-1935-to-1939/about-this-collection/rights-and-access/`
    The Library does not own rights to material in its collections and does not grant or deny
    permission to publish; **assessing rights and any necessary third-party permissions remains the
    user's responsibility**, and this project treats it that way. Source of the
    {{ facts.dataset_retro_poster }} retro-poster items. **Retrieval blocked — see the note below.**

14. Creative Commons, "CC0 1.0 Universal" public-domain dedication.
    `https://creativecommons.org/publicdomain/zero/1.0/` (accessed 2026-08-11).

</div>

<div class="callout">
<span class="callout__label">Retrieval limitation on references 12 and 13</span>
Both pages were attempted repeatedly from the authoring environment across five official paths and
could not be fetched: the museum returned <strong>HTTP 429</strong> and the library
<strong>HTTP 403</strong> every time. <strong>Neither page is quoted here</strong>, and no
search-engine extract has been presented as though the page itself had been read. The official URLs
are given so a reader with an unblocked connection can verify them directly. The full attempt record
is in <code>docs/evidence/M9/reference-retrieval.md</code>.
<br><br>
<strong>These pages were never this project's primary licensing evidence.</strong> That evidence is
<code>data/manifests/dataset-v1.csv</code>, which records the source URL, author, licence, collection
date and permitted use for <strong>every one of the {{ facts.dataset_total }} items</strong>,
captured at the moment each was collected — when those servers were reachable. The manifest is
hash-locked and a test asserts it has not changed.
<br><br>
This is the <strong>fourth</strong> time third-party hosting has obstructed this project, after two
dataset sources and one base-model repository (§12.1). The mitigation adopted after those three —
record provenance at the moment of use — is why this one is a footnote rather than a gap.
</div>

## 24.5 Libraries and tools

Cited because the report makes behavioural claims about them — for example that the image-to-image
pipeline runs `int(steps × strength)` denoising steps (§13.4), and that a prompt-only request raises
while an image adapter is resident (§14). Both were established by reading the library source, not by
inference.

<div class="references">

15. Hugging Face Diffusers. `https://github.com/huggingface/diffusers` — version 0.39.0 pinned in
    this project.

16. Hugging Face PEFT. `https://github.com/huggingface/peft` — version 0.20.0, pinned and installed
    only after a parsed resolver report proved it moved none of the protected packages (§12).

17. PyTorch. `https://pytorch.org` — 2.13.0+cu126.

18. FastAPI. `https://fastapi.tiangolo.com` — the API framework selected in §8.2.

19. Three.js and React Three Fiber. `https://threejs.org` — the 3D stack selected in §8.3.

20. Playwright. `https://playwright.dev` — the browser test runner used for the
    {{ facts.playwright_tests }} end-to-end scenarios (§15).

</div>

**References 15–20 are identifying citations for tools whose exact versions are recorded in the
repository's own requirements and lock files**, which are the authoritative record of what this
project ran. Where a claim about a library's behaviour appears in this report, the evidence is the
experiment that established it, cited in place.
