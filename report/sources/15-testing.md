# <span class="section-number">15</span> Testing

## 15.1 The suites

| suite | count | scope |
|---|---:|---|
| pytest (`ml` + `apps/api`) | **{{ facts.pytest_tests }}** | dataset tooling, ML inference and training tooling, API contracts, upload security |
| vitest (`apps/web`) | **{{ facts.vitest_tests }}** | API client, form validation, decal provenance, texture-fit geometry, texture swapping |
| Playwright (Chromium) [20] | **{{ facts.playwright_tests }}** | the built frontend, every `/api/**` call answered from frozen fixtures |
| eslint | — | clean |
| production build | — | succeeds |

**No Python linter is installed**, so pytest is the Python gate, and this report says so rather than
implying a linting step that does not exist.

**A clean clone runs 522 passed and 5 skipped**, re-measured in the M11 audit on 2026-08-15. The
five are pre-existing conditional skips for git-ignored assets, each declaring its reason;
522 + 5 = {{ facts.pytest_suite_total }}, matching the development machine exactly. That figure is
a whole-repository run, so it is larger than the {{ facts.pytest_tests }} system tests this chapter
is scoped to: it also contains the {{ facts.pytest_report_tests }} report-validation and
{{ facts.pytest_deck_tests }} deck-validation tests, which test the documents rather than the
application. The M8 measurement of 468 + 5 = {{ facts.pytest_tests }} was correct for its date and
is superseded here, not contradicted.

## 15.2 What the suites deliberately do not prove

<div class="callout">
<span class="callout__label">The most important sentence in this section</span>
<strong>No test in any of the three suites loads the model or runs a generation.</strong> They prove
the code, the contracts, the upload rules and the interface. <strong>A green suite is not evidence
that DeckForge AI generates anything.</strong>
</div>

Generation quality, memory, latency and adapter integrity under real serving are evidenced
separately: by the experiment registry, by the residency and neutralisation experiments, by a
validation script run against a real server process, and by the single authorised clean-clone
generation. **Neither kind of evidence is presented as the other**, and the testing strategy states
this in its own opening rather than leaving a reader to infer it.

## 15.3 How the layers were designed to catch different things

**The API layer runs with the pipeline stubbed** — no GPU, no model, no network — so it can test
every status code, the lock discipline, the adapter lifecycle across all three styles and back, and
the checkpoint integrity gate against missing, wrong-size and **same-size-wrong-content** adapters.

**The browser layer runs against the built frontend**, not a dev server, with every API call answered
from frozen JSON fixtures.

That last choice creates a risk the project took seriously: **a mocked suite can keep passing against
a shape the backend no longer produces.** So the fixtures are validated against the real Pydantic
models by a Python test. A backend field rename therefore breaks a Python test rather than leaving
the browser suite passing against a stale contract — the mock cannot rot into theatre.

**Some tests exist to stop a specific past mistake returning.** A style-label regression guard
asserts that the corrected style name cannot revert. A test asserts the training and inference memory
ladders stay distinct, so "tier 2" cannot come to mean two things. Import boundaries are **AST-parsed
rather than text-scanned**, in both directions. A guard asserts that gradient accumulation never
appears as a memory tier — the correction the student made in plan review (§21.1).

## 15.4 Tests that encode research decisions

Several tests exist because a research decision would otherwise be a comment that drifts.

- The **frozen prompt kit and smoke kit are hash-locked**, so a comparison cannot be invalidated by an
  edited prompt.
- The **human scoring artifacts are hash-locked** and pinned in `.gitattributes` against line-ending
  rewriting, which makes "no score was edited after unblinding" checkable.
- The **holdout-exclusion proof joins against the dataset** rather than against the training
  manifest's own split column, so the manifest cannot vouch for itself.
- **Unmeasured sentinels must never satisfy a gate**, and `loss_decreased` must never gate anything.
- The **weights manifest is asserted against the code** by a test, so the documented adapter paths,
  sizes and hashes cannot drift from what the service actually loads.

## 15.5 Upload security

Twenty-seven rules, each with at least one negative test: extension and MIME allowlisting, mismatch
between MIME and extension, undecodable bytes, truncated files, oversize input, **decompression
bombs**, traversal filenames, and a GIF renamed to `.png`.

**Generation identifiers resolve through a registry lookup, never a path join.** This is the
structural half of the defence: a traversal string has nothing to traverse, rather than being
sanitised and hoped about.

The security matrix also records **what is not tested**, which is the half of a security document
that usually goes missing.

## 15.6 Continuous integration

The workflow runs the Python suite, the frontend suite with linting and build, and the browser suite,
on a GPU-less runner.

**All three jobs pass** — under three qualifications that materially weaken what the green means, set
out in full in §12.6 and carried as validity threats in §18.4. They are not repeated here, because a
green badge invites over-reading and a summary of a qualification tends to lose it.

**CI depends on an external host for a tokenizer**, so a red build with no defect behind it is
possible. That is recorded rather than worked around.

## 15.7 Growth, and one restraint

The suites grew from 406 pytest and 165 vitest at the MVP's close to
{{ facts.pytest_tests }} / {{ facts.vitest_tests }} / {{ facts.playwright_tests }}.

One planned addition was **dropped after checking disproved its premise**: a skip-marker for
checkpoint tests on CI turned out to be unnecessary, because the suite already passes with the
weights removed. Two further planned tests were dropped as duplicates of existing coverage. Adding
any of them would have inflated the count while implying coverage that had not changed.

**A test count is only evidence if every test earns its place.**
