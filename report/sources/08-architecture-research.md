# <span class="section-number">8</span> Architecture research

Six architecture decisions were taken with weighted criteria matrices before or during construction.
Four were reasoned judgements made in the first days, when no measurements existed. Two were taken
later **with measured hardware data**, and they are the ones §9 covers in detail.

Each criterion is weighted 1–5 by importance, each alternative scored 1–5. The weighted total
justifies the reasoned decision rather than replacing it — a matrix that outputs a decision nobody
can explain is a spreadsheet, not a method.

## 8.1 Repository structure

| criterion (weight) | monorepo | multi-repo | flat folder |
|---|---:|---:|---:|
| Jury traceability: one history tells the whole story (5) | 5 | 2 | 3 |
| Tooling simplicity on one machine (4) | 4 | 2 | 5 |
| Deadline risk (4) | 5 | 2 | 4 |
| Reproducibility / clean-clone test (4) | 5 | 3 | 3 |
| Separation of concerns (3) | 4 | 5 | 1 |
| **weighted total (max 100)** | **93** | **51** | **69** |

**Monorepo** (DR-001). A single Git history is itself evidence for the assessed process: the
commit sequence, the experiments and the documentation move together and can be read as one story.

## 8.2 Backend framework

| criterion (weight) | FastAPI | Flask | Node/Express |
|---|---:|---:|---:|
| Native fit with a Python ML stack (5) | 5 | 5 | 1 |
| Built-in validation for untrusted input (5) | 5 | 2 | 3 |
| Async and long-running requests (4) | 5 | 2 | 4 |
| Auto-generated API documentation (3) | 5 | 2 | 3 |
| Testability (4) | 5 | 4 | 2 |
| Time to productivity in 19 days (4) | 4 | 4 | 3 |
| **weighted total (max 125)** | **121** | **81** | **65** |

**FastAPI with Pydantic** (DR-002). Express would have forced a second process boundary between the
API and the model for no benefit. The validation criterion is weighted at 5 because every upload is
untrusted input reaching an image decoder (§17.3).

## 8.3 Frontend and 3D stack

| criterion (weight) | React + Vite + TS + R3F | plain Three.js | SvelteKit + Threlte |
|---|---:|---:|---:|
| 3D scene and UI state integration (5) | 5 | 2 | 4 |
| Ecosystem for product viewers (4) | 5 | 4 | 2 |
| Type safety for the API contract (4) | 5 | 4 | 4 |
| Testing story (4) | 5 | 3 | 4 |
| Time to first prototype (4) | 4 | 3 | 3 |
| **weighted total (max 105)** | **101** | **66** | **72** |

**React, Vite, TypeScript and React Three Fiber** (DR-003), with plain Three.js recorded as the
revision path. Prototype 0 was scheduled immediately afterwards precisely to test this choice against
reality rather than leave it on paper (§11.0).

## 8.4 ML toolchain

| criterion (weight) | Diffusers + PEFT | kohya-ss sd-scripts | ComfyUI |
|---|---:|---:|---:|
| Scriptable reproducibility: configs, seeds, testable (5) | 5 | 4 | 2 |
| Integration into the API service (5) | 5 | 3 | 2 |
| Memory optimisation for 8 GB (4) | 4 | 5 | 3 |
| Evidence value: readable code, not a black box (4) | 5 | 3 | 2 |
| Community-validated LoRA quality (3) | 4 | 5 | 4 |
| **weighted total (max 105)** | **98** | **83** | **54** |

**Diffusers, PEFT and Accelerate** (DR-004), with kohya-ss held as a fallback if memory proved too
tight. Note that kohya scores *higher* on memory optimisation and was still not selected: the
scriptability and evidence criteria outweighed it, and the decision recorded that the fallback would
be taken if measurements demanded it.

**They did not.** Training fitted at the lowest memory tier at both geometries with no escalation
(§9.2), so the fallback was formally retired rather than left as an open option.

## 8.5 Deck geometry

The deck model could have been sourced, bought, hand-modelled or generated procedurally.
**Procedural generation was selected** (DR-005): it removes third-party model licensing entirely,
guarantees a UV layout the project controls, and made the nose-to-tail orientation question testable
rather than inherited.

This decision removed a whole work package from the first milestone and is the main reason it
finished in about four hours against a ten-hour estimate (§7.2). It also has a cost, discovered four
milestones later: the test decals bundled with the viewer were 512×2000, which **concealed the
mismatch between the generated 1:3 decal and the deck's 1:3.902 UV domain** until the MVP was built
(§11.5).

## 8.6 Service architecture

The last architecture decision was taken with measured data and is the most constrained of the six.
Its inputs are in §9.3: the production stack leaves **{{ facts.worst_spare_mib }} MiB spare** under
real serving conditions.

| option | verdict |
|---|---|
| One process, one worker, one resident pipeline | **selected** (DR-011) |
| Multiple workers | **impossible** — a second resident pipeline does not fit in {{ facts.worst_spare_mib }} MiB |
| Load per request | rejected — a cold load costs ~30 s against ~12 s resident |
| A job queue with a separate worker process | rejected — same memory arithmetic, plus a component the deadline could not absorb |

**The service runs exactly one API process with one worker, holding one pipeline resident, and
serving one generation at a time behind a process-local lock.** A startup guard rejects a worker
count above 1.

This is a consequence of a measurement, not a preference, and it is stated in the report as a
limitation rather than as a design virtue (§18.3): **scaling this system is not a configuration
change.** It would need a second GPU or a smaller resident footprint.
