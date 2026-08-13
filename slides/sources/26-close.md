- **D1 / D5 / D6** — {{ facts.experiment_count }} experiments, six prototypes, conclusions bounded by what was measured
- **D3 / D2** — {{ facts.decision_record_count }} decision records, a planning log that records what changed and why, public issues and board
- **D4** — alternatives compared and rejected on criteria: base model, conditioning, fine-tuning, deployment
- **D7** — a 91-page report, this deck, and a system that states its own limitations to its user
- **What I would change:** repeat every condition before drawing a curve · seed *everything* and verify by comparing weights, not by trusting the log · get a second rater

<p class="source">github.com/KylianAlgoet/Selftrained-and-deployed-AI-image-generator · docs/learning-outcome-traceability.md</p>

## Speaker notes

Briefly against the learning outcomes, then what I would change.

The research outcomes are carried by the experiment registry, the prototype ladder, and conclusions
that stop where the evidence stops. The professional ones by the decision records and a planning
log that records what slipped and why, rather than being rewritten to match the original plan.

Two things I would change, and one is embarrassing.

Repeat every condition before drawing a curve. The image-count question is inconclusive because I
ran each condition once — a planning mistake, not a resource one.

And seed everything, then verify by comparing weights rather than trusting the log. I recorded a
seed for every run and was confident about reproducibility for weeks. It was not governing the
initialisation. I found out only because I tried to reproduce a result instead of assuming I
could — which is, in the end, what this project taught me.

Thank you. I am happy to take questions.
