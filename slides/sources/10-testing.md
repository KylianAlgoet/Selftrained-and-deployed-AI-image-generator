- **{{ facts.pytest_suite_total }} pytest** — {{ facts.pytest_tests }} system, the rest validating the report and this deck · **{{ facts.vitest_tests }} vitest** · **{{ facts.playwright_tests }} end-to-end**
- The **clean-clone test** is the one that counts: empty directory, install from scratch, working system
- It caught an **integrity control that had only ever passed on the machine that wrote it**
- **A green suite does not prove the generator makes good pictures.** Only the human gates did that

<p class="source">docs/evidence/M8/clean-clone/ · report §15</p>

## Speaker notes

The number is split on purpose. Four hundred and seventy-three cover the product and the research
code; the rest test the documents — that every quantitative claim in the report and on this deck
still matches its evidence file.

The one that earned its place is the clean-clone test. Clone into an empty directory, install from
scratch, reach a working system. It caught a real defect: a checkpoint integrity control that
passed every time locally, because the path it checked only existed on my machine. It had been
green for weeks while verifying nothing.

The honest limit is the last line: those tests tell you the code does what I told it to. Not one
tells you a generated deck looks good.
