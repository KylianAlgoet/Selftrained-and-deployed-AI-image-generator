# <span class="section-number">6</span> Methodology

## 6.1 The decision loop

Every significant decision in this project followed the same thirteen steps, recorded in
`CLAUDE.md` before the first line of code was written:

```
problem -> research question -> alternatives -> criteria -> experiment -> execution
-> actual results -> comparison -> justification -> implementation -> validation
-> documentation -> atomic commits
```

The rule that gives it force is negative: **do not build the complete result first and invent the
process afterwards.** Fourteen decision records exist because fourteen decisions went through this
loop; each states its context, the alternatives, the criteria, the decision, and — the part most
often missing from such records — what it does **not** claim.

## 6.2 Measurement protocol

**One configuration per fresh operating-system process.** Adopted after an early experiment produced
a 20× timing spread for provably identical work: four geometries had shared one process, and the
CUDA caching allocator's state carried across them. The obvious explanation, thermal throttling, was
tested and **ruled out** — a hotter, more throttled card ran the same work faster. Every VRAM and
latency figure in this report comes from a process that ran one configuration.

**Comparisons vary one factor against a frozen kit.** Fixed prompts, fixed reference images, fixed
seeds (42, 1337, 2026), fixed resolution and sampler settings. The prompt kit is hash-locked
(`c40749bc…`) and asserted unchanged by a test, so a comparison cannot be quietly invalidated by an
edited prompt.

**Memory is quoted against the ceiling, never against whether the run crashed.** This convention
comes directly from the SDXL result in §9.1, where thirty runs "succeeded" while allocating more than
the card holds.

**Peaks are separated by phase.** Post-load, forward/backward and optimizer-step peaks are recorded
separately rather than as one process maximum. That is what made the mechanism in §9.2 readable:
activations scale with geometry, optimizer state does not.

**Thresholds are declared before results are read.** Noise floors and tolerances live in code that
predates the runs it judges.

## 6.3 Evaluation

A nine-dimension rubric, scored 1–5, was defined **before** the first experiment: prompt adherence,
style consistency, reference influence, visual quality, decal suitability, composition, artefacts,
originality, and diversity across seeds. Scoring is the student's.

Three rules govern how scores are recorded, and each exists because the alternative would have
flattered the results:

- **A blank is never a zero, and is never back-filled.** Twenty-nine score cells in one milestone are
  recorded as *not scored* and excluded from every mean rather than imputed. Text-only generation at
  the deck format was left unscored rather than reusing a comparable value from an earlier milestone.
- **Automated indicators decide nothing.** Perceptual-hash and CLIP-similarity measures support the
  rubric and never replace it. They populate no rubric cell, select no checkpoint and set no verdict,
  and they are stored in separate files from human judgement.
- **Objective measurements and human scores are never blended.** Decision records report them in
  separate sections.

### The two-gate review protocol

Style learning used **two** human review gates rather than one, because they ask different questions:

| | Gate 1 — pilots | Gate 2 — production selection |
|---|---|---|
| question | which configuration goes forward | which checkpoint ships |
| sheets | **blinded** within style | **labelled** |
| why | the arms differed in one hidden variable each, so a label would leak the answer | the question cannot be answered without knowing which checkpoint a sheet is |
| known cost | none beyond reduced context | **labelled sheets carry an expectation effect the blinded ones did not** — stated rather than left implicit |

Both gates hash the completed score file. The Gate-1 hash was supplied **before** the blinding map
was opened, verified twice, and is asserted by a test, with the file pinned in `.gitattributes` so
line-ending normalisation cannot alter it. "No score was edited after unblinding" is therefore
checkable.

## 6.4 Use of AI assistance

Claude Code (Anthropic) was used throughout as an engineering and documentation assistant, under a
written working agreement in `docs/ai-usage.md` that predates the work. Fifteen dated session entries
record what it did, what the student decided, and where its own output was wrong. This section states
the boundary; the log holds the detail.

| category | what it covered |
|---|---|
| **Human decisions** | every decision-record conclusion · all rubric scores · the Gate-1 and Gate-2 selections · the texture-fit choice, quoted verbatim in DR-012 · the CI remedy · authorising every GPU generation |
| **AI-assisted planning** | milestone plans — **which the student's review changed**: the two-phase split of the style-learning milestone, twelve mandatory corrections to the MVP plan, and the correction that gradient accumulation is not a memory tier |
| **AI-assisted implementation** | the training and inference runners, the API, the frontend, the test suites, the dataset and evaluation tooling |
| **AI-assisted documentation** | this documentation set, written from executed results |
| **AI-assisted review and debugging** | the reproducibility diagnosis behind R14, the five defects found during testing and deployment, the continuous-integration stall trace |
| **Executed by the machine** | every GPU run. **No generation was ever run by an assistant.** All {{ facts.generations_total }} were authorised by the student |
| **Produced by tools** | VRAM figures, timings, hashes, perceptual and CLIP indicators, test counts |

Three statements are load-bearing and are made without hedging.

**The assistant did not validate its own results.** Measurements come from instrumented runs; the
judgements that turned them into decisions are the student's.

**It stopped rather than deciding when a decision was not its to make.** When the clean-clone test
failed on a value documented as frozen across an earlier milestone's evidence, it diagnosed the
cause, prepared two options, and stopped — repointing that constant would have moved a fingerprint
that milestone's records cite as unchanged.

**Its own work produced defects, and they are recorded rather than absorbed.** Four browser
assertions failed on first run and were all test defects rather than application defects; a
fixture reader written with a regex failed against real TypeScript and was replaced rather than
patched; an experiment runner defect is preserved in the evidence as a failed row (§12.3). §12
reports these alongside the project's other failures, because a defect found in the tooling is worth
the same as one found in the product.
