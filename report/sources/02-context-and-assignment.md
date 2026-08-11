# <span class="section-number">2</span> Context and assignment

## 2.1 The brief

The client is a skateboard manufacturer. The system must let a customer enter a text prompt, upload a
reference image, select a visual style, generate new decal artwork with a **self-trained (locally
fine-tuned) model**, view the result on an interactive 3D skateboard deck, and download the artwork.

This is a final bachelor resit assignment for Multimedia & Creative Technologies at
Erasmushogeschool Brussel. The working title of the system is **DeckForge AI**.

The assignment is unusual in one respect that shaped everything: **the assessed deliverable is the
research process, not only the artefact.** A working generator built without a visible, iterative,
evidence-based process would not satisfy it. That is why this report spends as much space on
measurements that changed decisions, and on approaches that did not work, as on the system that
resulted.

## 2.2 Mandatory requirements

Thirteen requirements are stated in the assignment. Section 26 traces each to its evidence; this
table states them, and where in this report each is addressed.

| # | requirement | addressed in |
|---:|---|---|
| 1 | Collect and create a custom training dataset | §10 |
| 2 | Document dataset provenance and permitted usage | §10, §17 |
| 3 | Support multiple visual styles (≥ 3 visually distinct) | §11.4, §13 |
| 4 | Train or fine-tune the model locally | §9.2, §11.3, §11.4 |
| 5 | Combine text prompting and a reference image | §9.3, §11.2 |
| 6 | Generate new decal artwork | §14 |
| 7 | Map it onto a 3D skateboard | §11.0, §14 |
| 8 | Provide a reproducible deployment or demonstration setup | §16 |
| 9 | Maintain a public planning link | §7 |
| 10 | Provide research documentation as PDF | this document |
| 11 | Provide prototype evidence | §11, §13 |
| 12 | Provide the final GitHub result | §16 |
| 13 | Provide a presentation as PDF | **not addressed by this report** — a later milestone |

Requirement 13 is deliberately marked outstanding. It belongs to the presentation milestone, which
had not run when this report was written, and claiming it complete would be exactly the kind of
unevidenced statement the rest of this document avoids.

## 2.3 Scope, and what was deliberately excluded

The MVP covers: prompt and optional negative prompt, an optional PNG/JPG/WEBP reference image, style
selection, reference strength, seed, generation, an interactive 3D deck preview with correct
nose-to-tail orientation, and download.

**Explicit non-goals**, fixed at the start of the project and never revisited: user accounts,
payments, social features, a webshop, native applications, and production-scale infrastructure. Any
addition to scope required an entry in the planning change log, which is how the two features that
*were* added late — real generation progress and local decal upload — are traceable rather than
silently absorbed (§7.3).

## 2.4 The constraint that shaped the project

The system had to be built and trained on the machine available, audited before any decision was
taken:

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4060 Laptop, **{{ facts.device_total_mib }} MiB VRAM** |
| System memory | 16 GB |
| OS / shell | Windows 11 Home, PowerShell 5.1 |
| Python | 3.11 (3.14 is the system default; 3.11 was used for all PyTorch [17] work) |
| Node | 24.18.0 |
| Not available | FFmpeg, nvcc, conda |

Full audit: `docs/technical/environment-audit.md`.

**Eight gigabytes of video memory is the single fact that explains most of this report.** It ruled
out the model that produced the best artwork (§9.1), forced the service to run exactly one worker
(§14), set the ceiling that every later addition had to fit inside (§9.3), and turned "does it fit"
into a question that had to be measured before each step rather than assumed after it.

The environment audit itself was later found to contain an error — the recorded Node version had
gone stale — and that is reported in §12 rather than quietly corrected, because a project whose
audit drifts is a project whose claims drift.

## 2.5 Deadlines

| event | date |
|---|---|
| Feature freeze | 2026-08-15, brought forward to 2026-08-09 |
| Final content | 2026-08-16 18:00 |
| **Submission** | **2026-08-17 06:00 Europe/Brussels** |
| Presentation | 2026-09-02 |

The freeze was brought forward six days because the implementation milestones finished early. The
reasoning, and what the freeze does and does not permit, is in §7.4.
