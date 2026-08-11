# Document control

| | |
|---|---|
| **Report** | DeckForge AI — Self-trained and Deployed AI Image Generator for Skateboard Decals |
| **Author** | Kylian Algoet |
| **Programme** | Multimedia & Creative Technologies, Erasmushogeschool Brussel |
| **Assignment** | Final bachelor resit assignment |
| **Repository** | `github.com/KylianAlgoet/Selftrained-and-deployed-AI-image-generator` |
| **Public planning** | `github.com/users/KylianAlgoet/projects/1` |
| **Submission deadline** | 2026-08-17 06:00 Europe/Brussels |

## How to read this report

Every quantitative claim is traceable to a file in the repository, and the path is given where the
claim is made. Experiment identifiers (`EXP-###`), decision records (`DR-###`), research questions
(`RQ##`) and risks (`R##`) all resolve to real records, and a validation script asserts that they do
before this PDF is built.

Numbers appearing in more than one place — test counts, the generation total, memory figures,
checkpoint hashes — are not typed into the text. They are substituted at build time from
`report/facts.yaml`, where each is proved against the evidence file that states it, so a figure that
drifts from its evidence fails the build rather than reaching this page.

**Failed and blocked work is reported as a result, not omitted.** Sections 12 and 18 exist for that
purpose, and the conclusions in section 19 are qualified where the evidence is qualified.

**Use of AI assistance.** This project was carried out with Claude Code (Anthropic) as an
engineering and documentation assistant, disclosed rather than implied. Every research conclusion,
rubric score and production selection is the student's; no generation was ever run by an assistant;
and the assistant did not validate its own results. The full account is in section 6.4, and the
session-by-session record in `docs/ai-usage.md`.

**Reproducing this document.** `python scripts/build_report.py` renders the Markdown in
`report/sources/` through the template in `report/templates/` and prints it to PDF with headless
Chrome. The design, the alternatives considered and the stated limitations are recorded in `DR-015`.
