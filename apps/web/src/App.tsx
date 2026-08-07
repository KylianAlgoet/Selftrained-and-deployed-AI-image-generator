import { useCallback, useEffect, useRef, useState } from 'react'
import type { Texture } from 'three'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import { DeckViewer } from './viewer/DeckViewer'
import { GenerateForm, type GenerateFormValues } from './generate/GenerateForm'
import { ResultPanel } from './generate/ResultPanel'
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
import './App.css'

type Status =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'busy' }
  | { kind: 'error'; message: string; field?: string }

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

  const handleSubmit = useCallback(
    async (values: GenerateFormValues) => {
      setStatus({ kind: 'loading' })
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
        await applyFit(image, fitMode)

        setStatus({ kind: 'idle' })
      } catch (error) {
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
      }
    },
    [applyFit, fitMode],
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

  return (
    <main className="app">
      <header>
        <h1>DeckForge AI</h1>
        <p>
          Describe a skateboard decal, generate it with a locally trained style, and see it on
          the deck.
        </p>
      </header>

      {stylesError && (
        <p className="banner error" role="alert">
          {stylesError}
        </p>
      )}

      <div className="layout">
        <aside className="panel">
          <GenerateForm
            styles={styles}
            busy={status.kind === 'loading'}
            disabled={Boolean(stylesError)}
            fieldError={status.kind === 'error' ? { field: status.field, message: status.message } : null}
            onSubmit={handleSubmit}
          />

          {status.kind === 'busy' && (
            <p className="banner busy" role="status">
              The GPU is finishing another decal. Try again in a moment.
            </p>
          )}
          {status.kind === 'loading' && (
            <p className="banner" role="status">
              Generating at 512×1536 — this takes around 15 seconds.
            </p>
          )}
          {status.kind === 'error' && !status.field && (
            <p className="banner error" role="alert">
              {status.message}
            </p>
          )}

          {result && (
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

        <section className="viewer-column">
          <div className="viewer-controls">
            <fieldset className="fit-modes">
              <legend>Texture fit</legend>
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
            <label className="local-decal" title="Review control: put a decal from disk on the deck">
              Load decal <span className="review-only">review control</span>
              <input
                type="file"
                accept=".png,.jpg,.jpeg,.webp"
                onChange={(event) => void handleLocalDecal(event.target.files?.[0] ?? null)}
              />
            </label>
            <button type="button" onClick={() => controlsRef.current?.reset()}>
              Reset view
            </button>
            <label className="invert-demo" title="Controlled demonstration of an inverted UV layout — not a real defect">
              <input
                type="checkbox"
                checked={invertDemo}
                onChange={(event) => setInvertDemo(event.target.checked)}
              />
              Inverted-UV demonstration
            </label>
          </div>

          {invertDemo && (
            <p className="demo-banner">
              Controlled demonstration: the decal is deliberately rendered with an inverted UV
              layout to show what an orientation defect would look like.
            </p>
          )}
          {textureError && (
            <p className="banner error" role="alert">
              {textureError}
            </p>
          )}

          <div className="viewer-wrapper">
            <DeckViewer
              texture={texture}
              invertDemo={invertDemo}
              onControlsReady={(controls) => {
                controlsRef.current = controls
              }}
            />
          </div>
        </section>
      </div>

      <footer>
        <p>
          Deck geometry is a self-created project asset. Drag to orbit, scroll to zoom. Texture fit
          defaults to full surface (DR-012), which stretches the decal 1.3008× along the deck; the
          alternative preserves the artwork and leaves the ends bare.
        </p>
      </footer>
    </main>
  )
}
