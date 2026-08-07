# M7 interface screenshots — mocked telemetry, not GPU measurements

**Captured:** 2026-08-07 · Chrome, Vite dev server, real `uvicorn --workers 1` process.

## Read this before quoting any number in these images

**These are interface verification, not measurements.** Every progress value visible in
`02`–`04` was injected by a browser-side mock, not produced by a generation:

- **No image was generated.** The M7 GPU budget was exhausted at 25 of 25 before this pass, and
  no 26th generation was run. `POST /api/generate` was intercepted in the browser and never
  reached the server — the interceptor counted its calls, and the API's own
  `/api/generation-progress` still reported **`pipeline_loaded: false`** afterwards, which is the
  independent check that the model was never loaded.
- **The decal on the deck in `05`–`06` is a real earlier output** —
  `outputs/prototype-5/P5__ukiyo-e__ref__seed42.png` from Phase A — served to the dev server from
  a temporary file that was deleted after capture. It is not tracked and was not re-generated.
- **The step counts, elapsed times and estimates are fabricated inputs**, chosen to exercise each
  state. `13.07s`, `5143.73 MiB` and `200.0 MiB` in the metadata panel are real EXP-034 / Phase-A
  figures used as realistic fixture values; they are **not** measurements of anything shown here.
- The elapsed counters read 80–112 seconds because a state was held open while it was
  photographed. A real generation is 12–13 s resident.

The real measurements live in `docs/evidence/EXP-034/`, `docs/evidence/prototype-5/README.md` and
`api-validation.jsonl`. Nothing in this folder may be cited as a performance result.

## What each file shows

| file | state | what it verifies |
|---|---|---|
| `01-idle-production.jpg` | production idle, ~1920 px | the studio layout; **no review-only control is present** |
| `02-loading-model.jpg` | cold model load | a stage sentence and **no percentage**; the previous decal is still on the deck; Generate disabled and still readable |
| `03-denoising.jpg` | denoising, step 18/30 | ink filled to the real fraction; `Screen-print pass 18 / 30` **and** `Diffusion step 18 of 30 — 60%`; `About 6 seconds remaining` |
| `04-finalising-eta-expired.jpg` | after the last step | percentage withdrawn, `Finishing the artwork…` — the estimate had expired and was **retracted rather than counted past zero** |
| `05-success-result.jpg` | result | the decal on the deck at `full-surface` with its 1.3008× stretch disclosed; PNG and metadata downloads; Generate re-enabled |
| `06-error-timeout.jpg` | 504 | the existing error text, unchanged; **previous decal preserved**; retry available |
| `07-responsive-1024-768.jpg` | 1024 px and 768 px | single-column stack, no horizontal scroll, viewer still 360 px |
| `08-responsive-1440-390.jpg` | 1440 px and 390 px | two-column desktop, and a usable narrow layout |
| `09-review-mode.jpg` | `?review=1` | the review tools return, `full-surface` still selected |
| `10-upload-own-decal.jpg` | user's own artwork on the deck | `Upload your own decal` in the production UI, the `User-uploaded artwork` provenance strip with the filename, Replace/Remove — and **no AI metadata or downloads**, because none exists for it |
| `11-upload-failure-preserves-decal.jpg` | undecodable upload | the actionable error **and the previously uploaded decal still on the board** |

### 10 and 11 are real, not mocked

Unlike `02`–`06`, these two involve no mock at all. The artwork was drawn in the browser to a
canvas, exported as a genuine PNG and fed through the real `#decal-upload` control; the failure
case is a file declaring `image/png` whose bytes are not an image, so the **decode** is what
rejects it.

**The upload path made zero API requests**, which is checked from the server rather than asserted:
across both uploads the access log's `POST /api/generate` count stayed at **1** (Kylian's own
generation), the progress-poll count stayed at **48**, and `/api/health` still reported
`allocated_mb: 3316.64` — unchanged, so no GPU work happened.

## How the narrow viewports were captured

`resize_window` had no effect: the browser window was maximised on a 1536 px screen and the page
was at 80 % zoom, so the CSS viewport stayed at 1920 px whatever was requested. The 1024, 768,
1440 and 390 px layouts were therefore rendered in **iframes of those exact widths**. An iframe
is a real viewport — media queries evaluate against its own width — so the stacking shown is the
genuine responsive behaviour and not a scaled screenshot. Each was also probed
programmatically for grid columns, viewer height and horizontal overflow; those readings are in
the process log.

## Two defects these captures found

Both were fixed before the screenshots above were taken, and neither was visible in tests:

1. **The desktop shell overflowed the viewport** by 70 px (`min-height: 100vh` let the flex column
   grow), putting the deck partly below the fold and giving the whole page a scrollbar.
2. **A horizontal scrollbar** on every page, traced to `.generate-form input[type='file'] { width:
   100% }` beating `.visually-hidden` on specificity and stretching the hidden file input to
   1992 px.
