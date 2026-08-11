# <span class="section-number">4</span> Problem statement

## 4.1 The practical problem

A skateboard manufacturer wants customers to design their own deck graphics. The obstacle is not
demand but production: commissioning artwork per customer does not scale, stock template libraries
produce decks that look like everyone else's, and a generic image generator produces images that are
not decal artwork — wrong proportions, wrong composition, and no way to see the result on a board
before ordering.

Three properties are therefore required together, and it is the combination that is hard:

1. **The output must be a decal**, not a picture of one. A skateboard deck is roughly 1:3.6; almost
   every diffusion model is trained on square or near-square images and drifts toward photographic
   product mockups when asked for a deck (§9.1, Figure 1).
2. **The style must be the manufacturer's**, consistently, across arbitrary prompts. A pretrained
   model has no notion of any particular house style, so a style has to be taught.
3. **The customer must be able to steer it**, both with words and with an image they already have,
   without the result becoming a copy of that image (§11.2).

## 4.2 The research problem

The assignment adds a constraint that turns an engineering task into a research one: the model must
be **trained or fine-tuned locally**, and the only machine available has
**{{ facts.device_total_mib }} MiB of video memory**.

That constraint is not a detail of implementation. It determines which base model can be used, which
fine-tuning method is even possible, whether reference conditioning and a trained adapter can be
resident at the same time, whether the deck's tall geometry can be generated directly or must be
reconstructed from something squarer, and how many processes the finished service may run.

None of those questions has a reliable answer in advance for a specific 8 GB card, because the
figures that circulate for these models are typically quoted for larger GPUs or with optimisations
whose costs are not stated. They had to be measured on this machine.

**The problem this project addresses is therefore:**

> How can a locally fine-tuned diffusion model, conditioned on both a text prompt and a reference
> image, generate skateboard-decal artwork in multiple visually distinct styles with reproducible
> quality on consumer hardware with 8 GB of VRAM?

## 4.3 Why the constraint is interesting rather than merely inconvenient

An 8 GB budget makes the trade-offs visible that a larger card would hide. Three of this project's
more useful findings exist only because the ceiling was close enough to hit:

- A model can report thirty successful runs while allocating more memory than the card physically
  holds, because Windows spills into host memory instead of failing (§9.1). On a 24 GB card that
  experiment returns "fine" and teaches nothing.
- The marginal cost of a trained adapter (+3.04 MiB) and of reference conditioning (~1 249 MiB) are
  worth measuring separately only when the sum is close to the limit — and it is their sum, not
  either one, that sets the production ceiling (§9.3).
- A service that holds one pipeline resident and refuses a second worker is an architectural
  consequence of a memory measurement, not a preference (§14.2).

## 4.4 What success requires

The system is successful if a customer can go from a sentence to a decal on a rotating 3D deck, in
one of at least three recognisably different styles, on this hardware, reproducibly — and if the
reasons for each design decision are traceable to evidence rather than to taste.

The second half of that sentence is the part the assignment assesses, and it is why the twelve
research questions in §5 exist.
