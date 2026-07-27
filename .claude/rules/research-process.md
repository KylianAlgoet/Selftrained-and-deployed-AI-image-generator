# Research process

Do not build the complete result first and invent the process afterwards. The visible, iterative process is the assessed deliverable.

## Decision loop (mandatory for every important decision)

1. Define the problem
2. Formulate a research question or hypothesis
3. Identify realistic alternatives
4. Define comparison criteria
5. Build a small experiment or prototype
6. Execute it
7. Record only actual results
8. Compare alternatives
9. Justify the decision
10. Implement the selected approach
11. Validate it
12. Update documentation
13. Create appropriate atomic commits

## Experiments

- Register every experiment in `experiments/registry.csv` with an `EXP-###` ID and all mandated fields.
- Use fixed prompts, reference images, seeds, sizes, and settings for comparisons.
- Evaluate with the 1–5 rubric defined in `docs/05-experiment-methodology.md`.
- Never start a long training run before a minimal end-to-end smoke test succeeds.

## Prototypes

Prototype 0 (3D viewer) → 1 (base-model benchmark) → 2 (text + reference conditioning) → 3 (LoRA smoke test) → 4 (style learning) → 5 (integrated MVP). Each needs: research question, scope, acceptance criteria, implementation, real tests, actual results, evidence, conclusion, impact on next iteration, and related commits. Do not skip prototypes.

## Decision records

Major choices get a record in `docs/decisions/` (`DR-###-slug.md`): context, alternatives, criteria, decision, consequences, status.
