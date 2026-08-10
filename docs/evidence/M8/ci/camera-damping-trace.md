# The OrbitControls damping trace behind the camera-preservation tolerances

**Date:** 2026-08-10 · **Milestone:** M8 (CI fix) · **Machine:** the validated Windows 11 /
RTX 4060 Laptop machine · **Bundle:** `npm run build` with `VITE_E2E=1`, served by `vite preview`
on port 4173, driven by Chromium under Playwright with the suite's SwiftShader launch flags.

## Why this measurement was taken

The rewritten `replacing the decal does not reset the camera` reads the camera pose out of the
scene instead of screenshotting the canvas. Its first version defined "the camera has come to
rest" as **two consecutive reads being equal to within 1e-6**, sampled every 50 ms. That rule
failed three runs out of three, reporting *"the camera never came to rest"*.

The rule was wrong, not the application. drei's `<OrbitControls>` enables damping by default
(`enableDamping = true` in `@react-three/drei/core/OrbitControls.js`), so after a drag the camera
**decays towards rest geometrically and never exactly arrives**. "Two identical reads" is a state
this scene does not reach; whether the loop exited depended on where in the decay it happened to
sample.

Rather than guess at a threshold, a temporary diagnostic spec traced the actual decay. It was
deleted after this measurement was taken; the numbers below are its real output.

## Method

Sample the camera position, quaternion and orbit target every 100 ms and record `d`, the largest
single-component change since the previous sample. Four phases: after load, after an orbit drag,
after replacing the decal, after pressing **Reset view**.

## Results

### A — at rest after load (10 samples)

Every sample identical, `d = 0.00e+0`:

```
position(1.5000, -2.1000, 2.4000) quaternion(0.3016, 0.2618, -0.0865, 0.9127) target(0, 0, 0)
```

The opening pose is exactly the configured camera position, and nothing moves before the user does.

### B — after the orbit drag (40 samples, abridged)

| sample | d | position |
|---:|---|---|
| 1 | 2.59e-1 | (-1.6157, -0.4187, 3.1039) |
| 5 | 5.56e-2 | (-2.0463, -0.1722, 2.8641) |
| 10 | 9.91e-3 | (-2.1521, -0.1072, 2.7887) |
| 15 | 1.62e-3 | (-2.1688, -0.0968, 2.7761) |
| 21 | 1.19e-4 | (-2.1713, -0.0952, 2.7742) |
| 28 | 1.02e-5 | (-2.1715, -0.0951, 2.7740) |
| 33 | 1.44e-6 | (-2.1716, -0.0950, 2.7740) |
| 39 | 1.60e-7 | (-2.1716, -0.0950, 2.7740) |

A clean geometric decay, about 5 % of the remaining delta per rendered frame. It crosses **1e-4 at
~2.1 s**, **1e-5 at ~2.9 s** and **1e-6 at ~3.4 s** — all of them well past the 2 s ceiling the
first settle rule allowed.

The drag moved the camera from `(1.5, -2.1, 2.4)` to `(-2.1716, -0.0950, 2.7740)`: **3.7 world
units of position and 0.6 of quaternion.** That is the size of the signal the test must detect.

### C — after replacing the decal (10 samples)

```
position(-2.1716, -0.0950, 2.7740) quaternion(0.0127, -0.3260, 0.0044, 0.9453) target(0, 0, 0)
```

`d` between **3.75e-9 and 4.00e-8** across all ten samples, and the pose is the one phase B ended
on, to four decimals.

**The texture swap does not move the camera.** This is the claim the test exists to defend, and it
is now measured directly rather than inferred from pixels differing.

### D — after pressing Reset view (40 samples)

```
position(1.5000, -2.1000, 2.4000) quaternion(0.3016, 0.2618, -0.0865, 0.9127) target(0, 0, 0)
```

Identical to phase A. `d` starts at **1.09e-9** and decays to **2.22e-16** — floating-point dust.
Reset restores the opening viewpoint exactly, so the test can assert that rather than only
asserting that reset changed *something*.

## What the numbers were used for

| constant | value | justification |
|---|---|---|
| `SETTLE_EPSILON` | **1e-5** | Reached ~2.9 s after a drag. Below it, the remaining distance to true rest is roughly 20x the sample delta, i.e. under 1e-3. |
| `CAMERA_EPSILON` | **1e-3** | An order of magnitude above that residual, so damping cannot fail the comparison — and ~3700x below the 3.7-unit move a real camera reset would produce. |

Two consecutive samples must fall under `SETTLE_EPSILON`, and each sample waits for a rendered
frame, because damping only advances when a frame renders: on a software rasteriser a stalled
render loop can otherwise produce two identical reads while the camera is still in flight. That
was the second failure mode, and it is why the rule is not simply "one quiet sample".

## Honest limits of this evidence

- Taken on the **development machine**, not on a GitHub runner. It establishes the *shape* of the
  decay and the size of the signal; it does not measure CI frame rates. The per-frame sampling is
  what makes the rule independent of frame rate.
- It is a trace of **one** drag. A different drag length changes the starting delta and therefore
  the settling time, not the decay rate.
- It says nothing about rendering correctness. It measures camera state only.
