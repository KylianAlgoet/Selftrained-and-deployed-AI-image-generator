# <span class="section-number">26</span> D1–D7 traceability

The mapping below was appended to at every milestone in
`docs/learning-outcome-traceability.md` rather than assembled at the end. Nothing in it is marked
complete without a repository path behind it.

## 26.1 Learning outcomes

| ID | outcome | evidence | report |
|---|---|---|---|
| **D1** | Independent applied research | 12 research questions declared before any experiment · {{ facts.experiment_count }} registered experiments · results that refuted their own hypotheses (deck aspect ratio; thermal throttling) · one result left **inconclusive** rather than forced | §5, §12, §13 |
| **D2** | Independent professional functioning | a gated model escalated for a decision rather than authenticated around · a declared GPU cap reached exactly and respected · a new dependency admitted only after a parsed resolver report · two findings deliberately **not** fixed under a freeze, with reasons | §12.1, §7.3, §18.3 |
| **D3** | Iterative planning and methodology | planning v1 preserved verbatim + 13 change-log entries with reasons · a review gate split in two after plan review · a freeze brought forward to the day work finished | §7 |
| **D4** | Comparison of multiple solution methods | six weighted matrices · base model on **measured** data across two tracks · four conditioning arms · five fine-tuning methods weighed, one measured, **with the limit stated** · both texture-fit modes built rather than one argued for | §8, §9, §11.2, §14.4 |
| **D5** | Complex problem solving via prototypes | six prototypes, none skipped, each answering the next one's precondition · a silent host-memory spill diagnosed · unseeded initialisation identified from the √2 shape of a discrepancy · five defects only a clean clone could find · a CI stall traced rather than retried at | §11, §12 |
| **D6** | Justified research conclusions | every conclusion cites a registry row, a decision record or a commit · blanks never back-filled · **visual evaluation AI-assisted, every recorded score reviewed and approved by Kylian, who held final authority** · offline indicators populate no rubric cell · gate-1 scores hashed **before** unblinding, asserted by a test · the memory figure revised **tighter** on its own evidence | §6.3, §6.4, §13, §19 |
| **D7** | Professional documentation | this report and its reproducible build · a runbook written for someone without this machine · a weights manifest guarded by a test · the application surfaces its own limitations to the user | §16, §14.6, DR-015 |

## 26.2 Mandatory requirements

| # | requirement | evidence | status |
|---:|---|---|---|
| 1 | Custom training dataset | `data/manifests/dataset-v1.csv` — {{ facts.dataset_total }} items | **met** |
| 2 | Provenance and permitted usage documented | per-item `source`, `licence`, `permitted_use`; DR-006 | **met** |
| 3 | Multiple visual styles (≥ 3) | three trained adapters; EXP-027/028/029 | **met**, one a partial pass |
| 4 | Train or fine-tune locally | 10 training runs on the audited GPU; DR-009 | **met** |
| 5 | Text and reference-image conditioning | DR-008, IP-Adapter @ {{ facts.ip_adapter_scale_default }} | **met** |
| 6 | Generate new decal artwork | {{ facts.generations_total }} real generations | **met** |
| 7 | Map onto a 3D skateboard | Prototype 0; DR-012 | **met** |
| 8 | Reproducible deployment or demo setup | runbook + clean-clone test with real output | **met** |
| 9 | Public planning link | GitHub Project mirroring M0–M11 | **met** |
| 10 | Research documentation as PDF | this document | **met on delivery** |
| 11 | Prototype evidence | `docs/evidence/`, six prototype documents | **met** |
| 12 | Final GitHub result | the repository | **met** |
| 13 | Presentation as PDF | — | **NOT MET — a later milestone** |

**Requirement 13 is outstanding and is reported as outstanding.** The presentation belongs to the
milestone after this one. No claim of full assignment completion is made anywhere in this report
(§2.2).

## 26.3 Where each research question is answered

**Eight of the twelve are answered within their stated scope. Four are only partially or boundedly
answered: RQ1, RQ4, RQ7 and RQ11.** RQ4's image-count component remains explicitly inconclusive.

| RQ | answered in | status | verdict |
|---|---|---|---|
| RQ1 | §9.2 | **bounded** | feasibility established; **"most effective" not established** — four methods never measured |
| RQ2 | §9.1 | answered | on **two** measured candidates |
| RQ3 | §10 | answered | legally documentable dataset built |
| RQ4 | §11.4 | **bounded** | captions answered; **image count INCONCLUSIVE** |
| RQ5 | §11.4 | answered | per-style selected, multi-style viable |
| RQ6 | §11.2 | answered | IP-Adapter over img2img |
| RQ7 | §11.2, §11.4 | **bounded** | rank and learning rate not swept |
| RQ8 | §9.1 | answered | **hypothesis refuted** by its own result |
| RQ9 | §11.0 | answered | UV layout controls orientation |
| RQ10 | §6.3 | answered | with the subjectivity threat stated |
| RQ11 | §17 | **bounded** | licensing settled; **memorisation not established** |
| RQ12 | §16 | answered | validated by clean clone |

## 26.4 What this matrix deliberately does not do

It does not mark a requirement met without a path, and it does not average partial results into
whole ones. **Four research questions are marked bounded rather than answered, one component is
marked inconclusive, and one requirement is marked not met.**

A traceability matrix whose every cell is green is not evidence that a project succeeded; it is
evidence that the matrix was written to be green.
