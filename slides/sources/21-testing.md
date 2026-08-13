- **{{ facts.pytest_tests }}** product and research tests **+ {{ facts.pytest_report_tests }}** report-validation tests = **{{ facts.pytest_total }} pytest**
- **{{ facts.vitest_tests }}** frontend unit tests · **{{ facts.playwright_tests }}** browser end-to-end scenarios
- The **clean-clone test** is the one that counts: clone into an empty directory, install from scratch, reach a working system
- It caught an **integrity control that had only ever passed on the machine that wrote it**
- A green suite does not prove the generator makes good pictures. **Only the human gates did that**

<p class="source">docs/evidence/M8/ · docs/evidence/M8/clean-clone/ · report §15</p>

## Speaker notes

Testing, and one result that changed how I think about testing.

I keep the pytest number split on purpose. Four hundred and seventy-three tests cover the product
and the research code. Sixteen more test the report itself — that every quantitative claim still
matches the evidence file it came from. Four hundred and eighty-nine altogether, plus the frontend
and browser suites.

The one that earned its place is the clean-clone test: clone into an empty directory, install from
scratch, reach a working system, about ten minutes.

It caught a real defect. A checkpoint integrity control passed every time locally — because the
path it checked only existed on my machine. In a clean clone it failed immediately. It had been
green for weeks while verifying nothing.

The honest limit: those tests tell you the code does what I told it to. Not one of them tells you a
generated deck looks good. Only the human gates did that.
