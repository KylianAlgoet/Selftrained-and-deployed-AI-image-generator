Generation goes **direct to {{ facts.generation_width }}×{{ facts.generation_height }}** — not
square-then-crop. **One worker is asserted in code**, because a second resident pipeline does not
fit: a concurrent request gets a clean refusal, never an out-of-memory crash.

<svg class="diagram" viewBox="0 0 1440 330" role="img" aria-label="Two processes: a React frontend calling a single-worker FastAPI service that holds one resident diffusion pipeline on the GPU">
  <defs>
    <marker id="a2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#2438d8"/>
    </marker>
  </defs>
  <g font-family="Segoe UI, sans-serif">
    <rect x="4" y="40" width="330" height="200" rx="14" fill="#f4f6f9" stroke="#d9dee6" stroke-width="2"/>
    <text x="28" y="80" font-size="24" font-weight="700" fill="#11151c">Browser</text>
    <text x="28" y="116" font-size="21" fill="#46525f">React 19 + Vite</text>
    <text x="28" y="148" font-size="21" fill="#46525f">Three.js / R3F deck</text>
    <text x="28" y="180" font-size="21" fill="#46525f">Procedural geometry,</text>
    <text x="28" y="206" font-size="21" fill="#46525f">runtime texture swap</text>

    <rect x="404" y="40" width="360" height="200" rx="14" fill="#f4f6f9" stroke="#d9dee6" stroke-width="2"/>
    <text x="428" y="80" font-size="24" font-weight="700" fill="#11151c">FastAPI service</text>
    <text x="428" y="116" font-size="21" fill="#46525f">uvicorn, <tspan font-weight="700" fill="#11151c">one worker</tspan></text>
    <text x="428" y="148" font-size="21" fill="#46525f">Busy lock &#8594; 409, never OOM</text>
    <text x="428" y="180" font-size="21" fill="#46525f">Upload validation, timeouts</text>
    <text x="428" y="206" font-size="21" fill="#46525f">SHA-256 checkpoint verify</text>

    <rect x="834" y="40" width="380" height="200" rx="14" fill="#11151c"/>
    <text x="858" y="80" font-size="24" font-weight="700" fill="#ffffff">One resident pipeline</text>
    <text x="858" y="116" font-size="21" fill="#c8d0dc">Stable Diffusion 1.5</text>
    <text x="858" y="148" font-size="21" fill="#c8d0dc">+ one per-style LoRA</text>
    <text x="858" y="180" font-size="21" fill="#c8d0dc">+ IP-Adapter (optional)</text>
    <text x="858" y="206" font-size="21" fill="#8fa0ff">{{ facts.generation_width }} &#215; {{ facts.generation_height }}, direct</text>

    <rect x="1284" y="40" width="152" height="200" rx="14" fill="#2438d8"/>
    <text x="1306" y="80" font-size="24" font-weight="700" fill="#ffffff">GPU</text>
    <text x="1306" y="116" font-size="21" fill="#ccd2fb">RTX 4060</text>
    <text x="1306" y="148" font-size="21" fill="#ccd2fb">Laptop</text>
    <text x="1306" y="186" font-size="24" font-weight="700" fill="#ffffff">8 GB</text>

    <g stroke="#2438d8" stroke-width="3" marker-end="url(#a2)">
      <line x1="338" y1="140" x2="398" y2="140"/>
      <line x1="768" y1="140" x2="828" y2="140"/>
      <line x1="1218" y1="140" x2="1278" y2="140"/>
    </g>
    <text x="342" y="126" font-size="18" fill="#7b8794">HTTP</text>

    <text x="4" y="296" font-size="22" fill="#46525f">Two processes, one machine. Single-worker is a correctness requirement enforced in code, not a deployment convenience.</text>
  </g>
</svg>

## Speaker notes

Two processes on one machine: a React frontend with the Three.js deck, and a FastAPI service that
owns the model.

The single worker is what I would point at. It is not a default I never changed — it is asserted at
startup, because a second resident pipeline does not fit in what is left. Two simultaneous
requests, and the second gets a clean refusal rather than an out-of-memory crash that takes the
first down with it. Refusing correctly is a feature here.

Generation goes straight to the deck's tall ratio rather than generating a square and cropping. I
expected that to hurt, because diffusion models are trained mostly on square images. I wrote it
down as a hypothesis, tested it, and it was refuted.
