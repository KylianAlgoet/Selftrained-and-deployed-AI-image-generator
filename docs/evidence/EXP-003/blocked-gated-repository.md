# EXP-003 — BLOCKED: candidate B (SD 2.1 base) is gated on Hugging Face

**Date:** 2026-07-30 · **Status:** blocked, not attempted further · **Prototype:** 1 (M3) · **RQ:** RQ2

A blocked experiment is a first-class result under `.claude/rules/honesty-and-evidence.md`.
This record exists so the gap in the candidate set is visible rather than quietly absent.

## Objective

Benchmark `stabilityai/stable-diffusion-2-1-base` as candidate B (the mid-point candidate) on
Track A (512×512) and Track B (512×512 native), per the approved M3 plan.

## Hypothesis

SD 2.1 base would run comfortably at 512 px on 8 GB VRAM, slightly above SD 1.5 in memory use,
serving as a middle data point between SD 1.5 and SDXL.

## Setup

Same runner, same frozen kit (fingerprint `c40749bc100deea5cc5854e40ba34928dcf3fdda31ff3c41840dafdfba1f5228`),
same pinned-revision policy as the other candidates. Unauthenticated access, per the approved plan's
decision that the entire candidate set was ungated and no Hugging Face account would be created.

## Expected result

An immutable commit SHA resolved from the Hub, then 15 measured runs per track.

## Actual result — FAILED at revision resolution

```
huggingface_hub.errors.RepositoryNotFoundError: 401 Client Error.
Repository Not Found for url: https://huggingface.co/api/models/stabilityai/stable-diffusion-2-1-base.
If you are trying to access a private or gated repo, make sure you are authenticated
and your token has the required permissions.
Invalid username or password.
```

The process exited with code 1 before loading any weights. **No generation was attempted, so no
speed, VRAM, or quality figure exists for this candidate — those fields are "not measured", not zero.**

## Scope of the block (verified 2026-07-30, unauthenticated)

| Repository | HTTP status |
|---|---|
| `stabilityai/stable-diffusion-2-1-base` | **401** |
| `stabilityai/stable-diffusion-2-1` | **401** |
| `stabilityai/stable-diffusion-2-base` | **401** |
| `stabilityai/stable-diffusion-xl-base-1.0` | 200 (candidate C — unaffected) |
| `stable-diffusion-v1-5/stable-diffusion-v1-5` | 200 (candidate A — unaffected) |

The whole Stability AI SD 2.x family now requires authentication. SDXL, from the same organisation,
does not — so this is repository-level gating, not an outage or a network fault on this machine.

## Decision

Kylian was asked before anything was changed, because the approved plan states that a gated repo
means **stop and ask, never authenticate autonomously and never add a candidate unilaterally** —
the same rule established in M2 when Digital Comic Museum and the Art Institute of Chicago proved
inaccessible.

**Decision: proceed with two candidates (SD 1.5 and SDXL).** Issue #4 requires at least two
benchmarked models, which is satisfied. Three alternatives were presented and declined:

1. Creating a Hugging Face account and accepting the Stability licence — rejected to avoid adding an
   authentication dependency to the reproducibility story.
2. The ungated community mirror `sd2-community/stable-diffusion-2-1` (complete fp16 diffusers repo,
   15.5k downloads) — rejected because it is a third-party re-upload whose fidelity to Stability's
   weights **cannot be verified while the original is gated**, which is weaker provenance than this
   project applies to its dataset.
3. Substituting a different ungated model such as `segmind/SSD-1B` — rejected as a new candidate
   outside the approved registry.

## Lesson learned

Model availability is not a stable property and must be treated like the dataset sources were: verified
at the moment of use, with the failure recorded rather than papered over. Two of five approved dataset
sources were blocked in M2 and one of three approved base models was blocked in M3 — a recurring,
reportable pattern about depending on third-party hosting for reproducible research.

## Consequence for DR-007 and the report

The base-model decision rests on **two** measured candidates, not three. This narrows the comparison
and must be stated as a limitation, not hidden. The gating is also a genuine reproducibility caveat:
anyone re-running this benchmark today cannot obtain candidate B without authenticating.
