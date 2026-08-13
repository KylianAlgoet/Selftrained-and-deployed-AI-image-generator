<div class="callout callout--reject">
<strong>How many images does a style need? I do not know.</strong> <span class="tag tag--inconclusive">inconclusive</span>
</div>

- Trained the same style on **12, 24 and 44 images**, everything else held fixed
- The ordering came out **non-monotonic** — more images was not reliably better
- **No minimum count was established**, and none is claimed
- Reported as inconclusive rather than rounded into a recommendation

<p class="source">EXP-024n12, EXP-024n24, EXP-024 · RQ4, image-count component · report §13</p>

## Speaker notes

A question I set out to answer and did not.

RQ4 has two halves. The caption half worked: style-only captions beat verbatim ones, and that
result is in production.

The image-count half did not. Same style on twelve, twenty-four and forty-four images, everything
else fixed. I expected a curve with a plateau I could point at. What I got was non-monotonic — the
middle condition did not sit where it should have. With one run per condition I cannot separate a
real effect from variance, and repeating them enough times did not fit in the GPU budget.

So it is inconclusive, and no minimum image count is claimed anywhere in the report.

Why this slide exists: it would have been easy to write "about forty images is enough". It is
roughly what I used, it sounds reasonable, and nobody would have checked. I just did not measure
it.
