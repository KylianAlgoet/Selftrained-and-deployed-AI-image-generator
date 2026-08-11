# <span class="section-number">3</span> Learning outcomes

Seven learning outcomes are assessed. They are stated here with the evidence that carries each one;
the complete mapping, including file paths and experiment identifiers, is in §26 and in
`docs/learning-outcome-traceability.md`, which was appended to at every milestone rather than
assembled at the end.

| ID | outcome | principal evidence in this report |
|---|---|---|
| **D1** | Independent applied research | §5 research questions · §13 forty registered experiments · §12 results that refuted their own hypotheses |
| **D2** | Independent professional functioning | §7 planning and gates · §12 blocked sources escalated rather than worked around · §17 licence policy enforced before collection |
| **D3** | Iterative planning and professional methodology | §7.3 thirteen planning change-log entries with reasons · §6.3 the two-gate review protocol |
| **D4** | Comparison and application of multiple solution methods | §8 weighted architecture matrices · §9 base-model and fine-tuning comparisons · §11.2 four conditioning arms |
| **D5** | Complex problem solving via prototypes and new technologies | §11 six prototypes, each answering the question the next depended on · §12 the defects found along the way |
| **D6** | Justified research conclusions | §13 conclusions tied to registry rows · §18 limitations that qualify them · §19 |
| **D7** | Professional documentation and presentation | this report · §16 the runbook and weights manifest · the evidence set under `docs/evidence/` |

## 3.1 How the evidence was produced

Two habits account for most of the evidence behind these outcomes, and both were adopted early
enough to shape the work rather than describe it.

**Thresholds were written down before results were read.** Noise floors, pass conditions and
tolerances live in code and in plans that predate the runs they judge. This is what allows §9.2 to
report a diagnostic as a diagnostic rather than promoting it to a pass after the fact, and what makes
"the adapter changed the output" a measured claim instead of an impression.

**Human judgement was separated from automated measurement, and the separation was enforced.** The
rubric scores in this report are the student's. Automated indicators — perceptual hashes, CLIP
similarity — populate no rubric cell, select no checkpoint and decide no verdict; they live in
separate files from human judgement, and §6.3 explains why that boundary was drawn where it was. At
the first review gate the completed score sheet was hashed **before** the blinding map was opened, so
"no score was edited after unblinding" is a check rather than a promise, and a test still asserts it.

## 3.2 What the outcomes are not claimed on

D4 asks for comparison of multiple solution methods. Four of the five mandated fine-tuning methods
were **screened on criteria and never executed** (§9.2). The comparison that exists is real and
documented; it is not a measured five-way benchmark, and this report does not present it as one.

D6 asks for justified conclusions. Two of the twelve research questions end **inconclusive or only
partially answered** (§5.2), and they are reported that way. A learning outcome is not better served
by a tidy answer than by an honest one.
