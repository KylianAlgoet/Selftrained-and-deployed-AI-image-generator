import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { Texture } from 'three'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { DeckViewer } from './viewer/DeckViewer'
import { GenerateForm, type GenerateFormValues } from './generate/GenerateForm'
import { ResultPanel } from './generate/ResultPanel'
import { ProgressPanel } from './generate/ProgressPanel'
import { buildProgressView } from './generate/progressModel'
import { useGenerationProgress } from './generate/useGenerationProgress'
import { StatusMessage } from './ui/StatusMessage'
import {
  ApiError,
  absoluteUrl,
  fetchGeneratedImage,
  fetchStyles,
  generate,
  type GenerateResponse,
  type StylesResponse,
} from './api/client'
import {
  DEFAULT_TEXTURE_FIT_MODE,
  TEXTURE_FIT_LABELS,
  TEXTURE_FIT_MODES,
  composeDeckTexture,
  describeFit,
  type FitDescription,
  type TextureFitMode,
} from './deck/textureFit'
import { imageFromBlob, textureFromCanvas, textureFromUrl } from './viewer/deckTextures'
import { DECALS } from './decals'
import { emptySlot, releaseSlot, swapTexture, type TextureSlot } from './viewer/textureSwap'
import { isReviewMode } from './reviewMode'
import './App.css'

type Status =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'busy' }
  | { kind: 'error'; message: string; field?: string }

interface SubmittedSnapshot {
  styleLabel: string
  referencePresent: boolean
  seed: number | undefined
  width: number
  height: number
}

export default function App() {
  const [styles, setStyles] = useState<StylesResponse | null>(null)
  const [stylesError, setStylesError] = useState<string | null>(null)
  const [status, setStatus] = useState<Status>({ kind: 'idle' })
  const [result, setResult] = useState<GenerateResponse | null>(null)
  const [texture, setTexture] = useState<Texture | null>(null)
  const [fit, setFit] = useState<FitDescription | null>(null)
  const [fitMode, setFitMode] = useState<TextureFitMode>(DEFAULT_TEXTURE_FIT_MODE)
  const [invertDemo, setInvertDemo] = useState(false)
  const [textureError, setTextureError] = useState<string | null>(null)

  // Frontend-owned parts of the waiting state. These are NOT reported by the
  // backend: by the time they are true the GPU has already finished, so calling
  // them generation progress would be a lie about where the time went.
  const [submitted, setSubmitted] = useState<SubmittedSnapshot | null>(null)
  const [imageReady, setImageReady] = useState(false)
  const [applyingTexture, setApplyingTexture] = useState(false)

  const progress = useGenerationProgress()

  // Review tools are resolved once, at mount: the production interface must not
  // depend on a URL the user could stumble into mid-session.
  const reviewMode = useMemo(() => isReviewMode(), [])

  const controlsRef = useRef<OrbitControlsImpl | null>(null)
  const slotRef = useRef<TextureSlot<Texture>>(emptySlot<Texture>())
  // The decoded image is retained so switching fit mode recomposes the SAME
  // artwork rather than regenerating - the two modes must be comparable.
  const imageRef = useRef<HTMLImageElement | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchStyles()
      .then((response) => {
        if (!cancelled) setStyles(response)
      })
      .catch(() => {
        if (!cancelled) {
          setStylesError(
            'Could not reach the generation service. Start it with: python -m uvicorn apps.api.main:app --workers 1',
          )
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Start with the Prototype-0 bundled decal so the deck is never bare, and so
  // the orientation reference stays available before anything is generated.
  useEffect(() => {
    let cancelled = false
    textureFromUrl(DECALS[0].url)
      .then((loaded) => {
        if (cancelled) {
          loaded.dispose()
          return
        }
        slotRef.current = { texture: loaded, objectUrl: null }
        setTexture(loaded)
      })
      .catch(() => {
        // A missing starter decal is cosmetic: the deck renders bare and the
        // generate flow is unaffected, so it is not surfaced as an error.
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    return () => {
      slotRef.current = releaseSlot(slotRef.current)
    }
  }, [])

  const applyFit = useCallback(async (image: HTMLImageElement, mode: TextureFitMode) => {
    const { canvas, fit: description } = composeDeckTexture(
      image as unknown as CanvasImageSource & { width: number; height: number },
      mode,
      () => document.createElement('canvas'),
    )

    const outcome = await swapTexture(
      slotRef.current,
      { source: canvas },
      { load: async (source) => textureFromCanvas(source as HTMLCanvasElement) },
    )

    slotRef.current = outcome.slot
    if (outcome.ok) {
      setTexture(outcome.slot.texture)
      setFit(description)
      setTextureError(null)
    } else {
      // The previous decal is still on the deck; say what happened rather than
      // blanking the board.
      setTextureError(
        `The decal could not be applied to the deck (${outcome.error?.message ?? 'unknown error'}). The previous decal is still shown.`,
      )
    }
  }, [])

  const generating = status.kind === 'loading'

  const handleSubmit = useCallback(
    async (values: GenerateFormValues) => {
      if (generating) return // a second submit cannot start a second generation
      const styleLabel =
        styles?.styles.find((item) => item.key === values.style)?.label ?? values.style
      setSubmitted({
        styleLabel,
        referencePresent: Boolean(values.referenceImage),
        seed: values.seed,
        width: styles?.width ?? 512,
        height: styles?.height ?? 1536,
      })
      setImageReady(false)
      setApplyingTexture(false)
      setStatus({ kind: 'loading' })
      progress.begin()

      try {
        const response = await generate({
          prompt: values.prompt,
          style: values.style,
          seed: values.seed,
          loraWeight: values.loraWeight,
          ipAdapterScale: values.ipAdapterScale,
          referenceImage: values.referenceImage,
        })
        setResult(response)

        const blob = await fetchGeneratedImage(response.image_url)
        const image = await imageFromBlob(blob)
        imageRef.current = image
        // Only now is the request genuinely complete: the response arrived AND
        // the PNG decoded in the browser. Nothing before this point may claim
        // 100 %.
        setImageReady(true)

        setApplyingTexture(true)
        await applyFit(image, fitMode)
        setApplyingTexture(false)

        setStatus({ kind: 'idle' })
      } catch (error) {
        setApplyingTexture(false)
        if (error instanceof ApiError && error.isBusy) {
          setStatus({ kind: 'busy' })
          return
        }
        setStatus({
          kind: 'error',
          message:
            error instanceof ApiError
              ? error.message
              : 'Generation failed. Check that the service is running.',
          field: error instanceof ApiError ? error.field : undefined,
        })
      } finally {
        // Polling stops on every exit - success, refusal, timeout or crash.
        // It never held anything on the server, so stopping frees nothing but
        // the browser's own timer.
        progress.end()
      }
    },
    [applyFit, fitMode, generating, progress, styles],
  )

  const handleFitMode = useCallback(
    (mode: TextureFitMode) => {
      setFitMode(mode)
      if (imageRef.current) void applyFit(imageRef.current, mode)
      else setFit(describeFit(mode, 512, 1536))
    },
    [applyFit],
  )

  /**
   * Review-only: put a decal already on disk onto the deck.
   *
   * The texture-fit comparison needs a 1:3 decal, and Prototype 0's bundled
   * decals were authored at 512x2000 - the deck's own aspect - which is
   * precisely why the mismatch never surfaced until generation started
   * producing 512x1536. Without this, comparing the two fit modes would mean
   * generating another image purely to look at it. It also lets a reviewer
   * re-examine any earlier decal without spending GPU time.
   */
  const handleLocalDecal = useCallback(
    async (file: File | null) => {
      if (!file) return
      try {
        const image = await imageFromBlob(file)
        imageRef.current = image
        await applyFit(image, fitMode)
      } catch {
        setTextureError('That file could not be read as an image.')
      }
    },
    [applyFit, fitMode],
  )

  function download(blobUrl: string, filename: string) {
    const anchor = document.createElement('a')
    anchor.href = blobUrl
    anchor.download = filename
    anchor.click()
  }

  async function handleDownloadImage() {
    if (!result) return
    const blob = await fetchGeneratedImage(result.image_url)
    const url = URL.createObjectURL(blob)
    download(url, `deckforge-${result.generation_id}.png`)
    URL.revokeObjectURL(url)
  }

  function handleDownloadMetadata() {
    if (!result) return
    const payload = JSON.stringify(
      { ...result.metadata, texture_fit: fit ?? null, warnings: result.warnings },
      null,
      2,
    )
    const url = URL.createObjectURL(new Blob([payload], { type: 'application/json' }))
    download(url, `deckforge-${result.generation_id}.json`)
    URL.revokeObjectURL(url)
  }

  const progressView = buildProgressView({
    telemetry: progress.telemetry,
    telemetryUnavailable: progress.unavailable,
    elapsedMs: progress.elapsedMs,
    etaExpired: progress.etaExpired,
    imageReady,
    applyingTexture,
  })

  const showProgress = generating && submitted !== null

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <h1>DeckForge AI</h1>
            <p className="brand-tagline">
              Design a decal. Generate it locally. Preview it on the deck.
            </p>
          </div>
        </div>
        <p className="build-tag">
          <span className="tag">Local generation</span>
          <span className="tag">Research prototype</span>
          {reviewMode && <span className="tag tag-review">Review mode</span>}
        </p>
      </header>

      {stylesError && (
        <div className="app-alert">
          <StatusMessage tone="error">{stylesError}</StatusMessage>
        </div>
      )}

      <main className="workspace">
        <aside className="control-column" aria-label="Create a decal">
          <GenerateForm
            styles={styles}
            busy={generating}
            disabled={Boolean(stylesError)}
            fieldError={
              status.kind === 'error' ? { field: status.field, message: status.message } : null
            }
            onSubmit={handleSubmit}
          />

          {status.kind === 'busy' && (
            <StatusMessage tone="busy">
              The GPU is finishing another decal. Try again in a moment.
            </StatusMessage>
          )}
          {status.kind === 'error' && !status.field && (
            <StatusMessage tone="error">{status.message}</StatusMessage>
          )}

          {showProgress && <ProgressPanel view={progressView} submitted={submitted} />}

          {result && !showProgress && (
            <ResultPanel
              metadata={result.metadata}
              warnings={result.warnings}
              imageUrl={absoluteUrl(result.image_url)}
              fit={fit}
              onDownloadImage={handleDownloadImage}
              onDownloadMetadata={handleDownloadMetadata}
            />
          )}
        </aside>

        <section className="viewer-column" aria-label="Deck preview">
          <div className="viewer-bar">
            <h2 className="viewer-title">Deck preview</h2>
            <div className="viewer-actions">
              {reviewMode && (
                <>
                  <fieldset className="fit-modes">
                    <legend>
                      Texture fit <span className="review-only">review</span>
                    </legend>
                    {TEXTURE_FIT_MODES.map((mode) => (
                      <label key={mode}>
                        <input
                          type="radio"
                          name="fit-mode"
                          value={mode}
                          checked={fitMode === mode}
                          onChange={() => handleFitMode(mode)}
                        />
                        {TEXTURE_FIT_LABELS[mode]}
                      </label>
                    ))}
                  </fieldset>
                  <label
                    className="local-decal"
                    title="Review control: put a decal from disk on the deck"
                  >
                    Load decal <span className="review-only">review</span>
                    <input
                      type="file"
                      accept=".png,.jpg,.jpeg,.webp"
                      onChange={(event) =>
                        void handleLocalDecal(event.target.files?.[0] ?? null)
                      }
                    />
                  </label>
                  <label
                    className="invert-demo"
                    title="Controlled demonstration of an inverted UV layout — not a real defect"
                  >
                    <input
                      type="checkbox"
                      checked={invertDemo}
                      onChange={(event) => setInvertDemo(event.target.checked)}
                    />
                    Inverted-UV demonstration <span className="review-only">review</span>
                  </label>
                </>
              )}
              <button type="button" onClick={() => controlsRef.current?.reset()}>
                Reset view
              </button>
            </div>
          </div>

          {invertDemo && (
            <StatusMessage tone="warning">
              Controlled demonstration: the decal is deliberately rendered with an inverted UV
              layout to show what an orientation defect would look like.
            </StatusMessage>
          )}
          {textureError && <StatusMessage tone="error">{textureError}</StatusMessage>}

          <div className="viewer-wrapper">
            <DeckViewer
              texture={texture}
              invertDemo={invertDemo}
              onControlsReady={(controls) => {
                controlsRef.current = controls
              }}
            />
          </div>

          <p className="viewer-note">
            Drag to orbit, scroll to zoom. The deck geometry is a self-created project asset.
            The decal fills the whole surface (DR-012), which stretches it 1.3008× along the
            board.
          </p>
        </section>
      </main>
    </div>
  )
}
