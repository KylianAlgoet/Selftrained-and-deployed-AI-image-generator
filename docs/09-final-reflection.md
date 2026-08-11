# Final reflection

**Status:** completed 2026-08-11 (M9). The skeleton created 2026-07-27 said content would be written
only at project end from real evidence, and that is what happened — nothing here was filled in
speculatively.

**The full reflection is chapters 19–23 of the research report** (`report/sources/`, built to
`deliverables/DeckForge-AI-research-report.pdf`). This document records the same reflection in the
project's own documentation set, and points at where each part is argued in full.

## 1. What was achieved

Twelve of thirteen mandatory requirements are met. **Requirement 13, the presentation PDF, belongs to
M10 and is outstanding** — no claim of full assignment completion is made anywhere.

The system generates skateboard-decal artwork from a text prompt and an optional reference image, in
three locally trained styles, at 512×1536, and shows it on an interactive 3D deck. It runs on one
RTX 4060 Laptop GPU with **200.0 MiB spare** under real serving.

Report §2.2, §14, §26.2.

## 2. Research conclusions

**Eight of twelve research questions are answered within their stated scope. Four are bounded:
RQ1, RQ4, RQ7, RQ11.** RQ4's image-count component is explicitly **inconclusive**.

The primary question is answered affirmatively, bounded three ways: a 2.4 % memory margin,
"reproducible" holding for inference but not training, and three styles of which one is a partial
pass.

Report §5.2, §19, §26.3.

## 3. What failed and what it taught

A style learned its source material's frames and typography and ships as a partial pass. A research
question came out non-monotonic and was recorded as inconclusive rather than presented as a trend.
Training was never reproducible from seed and nobody noticed for four milestones, because every run
passed every gate. An integrity check had only ever passed on the machine that wrote it. A test
measured the wrong thing twice on a remote runner while the application was never at fault.

Report §12, §20.2.

## 4. Planning reflection

Every milestone but one finished early and the buffer compounded; the one that overran found five
real defects. The original plan was never rewritten — thirteen change-log entries record what
actually happened, which is what makes the planning evidence rather than hindsight.

Report §7, §20.1.

## 5. Professional functioning and AI-assisted work

**Visual evaluation was AI-assisted**: ChatGPT contributed visual analysis and proposed scoring at
the review gates, while Kylian Algoet reviewed and approved the recorded scores and retained final
authority over every production selection and research conclusion. Claude Code was the engineering
and documentation assistant throughout. **Every GPU generation was explicitly authorised by Kylian
Algoet; no AI assistant had authority to initiate GPU inference without that approval.** The total
is 27.
The offline indicators populated no rubric cell and selected no checkpoint, weight, style or verdict.

The assistant's own work produced defects — a runner defect, a fixture reader that could not parse
real code, and a reporting bug that presented missing data as a passed check, which failed in the
project's favour. All are recorded.

Report §6.4, §20.6, §21.5; `docs/ai-usage.md`.

## 6. What I would do differently

Seed every source of randomness on day one. Run the clean-clone test at the first milestone rather
than the eighth. Design the image-count experiment for equal epochs, or state up front that it cannot
answer the question asked. Measure at least one alternative fine-tuning method. Write the report in
parallel as planned. Make every placeholder asset match the real pipeline's exact dimensions.

Report §22.

## 7. Future work

Close the reproducibility defect; **exercise the external backup, which is the one item that is a
race against a disk failure**; measure a second fine-tuning method; answer the image-count question
properly; test the mitigation that was never tested; and, with more VRAM, reopen SDXL and the
multi-style adapter.

Report §23.
