**{{ facts.device_total_mib }} MiB.** The shipped stack peaks at **{{ facts.peak_allocated_mib }} MiB**
and leaves **{{ facts.worst_spare_mib }} MiB** spare while serving — **2.4 % of the card.**

<svg class="diagram" viewBox="0 0 1440 300" role="img" aria-label="Six prototypes in sequence, each answering the question the next one depends on">
  <defs>
    <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#7b8794"/>
    </marker>
  </defs>
  <g font-family="Segoe UI, sans-serif">
    <g>
      <rect x="4" y="60" width="216" height="150" rx="12" fill="#f4f6f9" stroke="#d9dee6" stroke-width="2"/>
      <text x="24" y="98" font-size="30" font-weight="700" fill="#2438d8">P0</text>
      <text x="24" y="132" font-size="25" font-weight="650" fill="#11151c">3D deck</text>
      <text x="24" y="168" font-size="21" fill="#46525f">Can a decal map</text>
      <text x="24" y="194" font-size="21" fill="#46525f">the right way up?</text>
    </g>
    <g>
      <rect x="248" y="60" width="216" height="150" rx="12" fill="#f4f6f9" stroke="#d9dee6" stroke-width="2"/>
      <text x="268" y="98" font-size="30" font-weight="700" fill="#2438d8">P1</text>
      <text x="268" y="132" font-size="25" font-weight="650" fill="#11151c">Base model</text>
      <text x="268" y="168" font-size="21" fill="#46525f">Which one fits</text>
      <text x="268" y="194" font-size="21" fill="#46525f">in 8 GB?</text>
    </g>
    <g>
      <rect x="492" y="60" width="216" height="150" rx="12" fill="#f4f6f9" stroke="#d9dee6" stroke-width="2"/>
      <text x="512" y="98" font-size="30" font-weight="700" fill="#2438d8">P2</text>
      <text x="512" y="132" font-size="25" font-weight="650" fill="#11151c">Conditioning</text>
      <text x="512" y="168" font-size="21" fill="#46525f">Reference image</text>
      <text x="512" y="194" font-size="21" fill="#46525f">without copying</text>
    </g>
    <g>
      <rect x="736" y="60" width="216" height="150" rx="12" fill="#f4f6f9" stroke="#d9dee6" stroke-width="2"/>
      <text x="756" y="98" font-size="30" font-weight="700" fill="#2438d8">P3</text>
      <text x="756" y="132" font-size="25" font-weight="650" fill="#11151c">LoRA smoke</text>
      <text x="756" y="168" font-size="21" fill="#46525f">Does training</text>
      <text x="756" y="194" font-size="21" fill="#46525f">fit at all?</text>
    </g>
    <g>
      <rect x="980" y="60" width="216" height="150" rx="12" fill="#f4f6f9" stroke="#d9dee6" stroke-width="2"/>
      <text x="1000" y="98" font-size="30" font-weight="700" fill="#2438d8">P4</text>
      <text x="1000" y="132" font-size="25" font-weight="650" fill="#11151c">Style learning</text>
      <text x="1000" y="168" font-size="21" fill="#46525f">Three adapters,</text>
      <text x="1000" y="194" font-size="21" fill="#46525f">human-scored</text>
    </g>
    <g>
      <rect x="1224" y="60" width="212" height="150" rx="12" fill="#11151c" stroke="#11151c" stroke-width="2"/>
      <text x="1244" y="98" font-size="30" font-weight="700" fill="#8fa0ff">P5</text>
      <text x="1244" y="132" font-size="25" font-weight="650" fill="#ffffff">Integrated MVP</text>
      <text x="1244" y="168" font-size="21" fill="#c8d0dc">Everything, in</text>
      <text x="1244" y="194" font-size="21" fill="#c8d0dc">one service</text>
    </g>
    <g stroke="#7b8794" stroke-width="2.5" marker-end="url(#ar)">
      <line x1="224" y1="135" x2="242" y2="135"/>
      <line x1="468" y1="135" x2="486" y2="135"/>
      <line x1="712" y1="135" x2="730" y2="135"/>
      <line x1="956" y1="135" x2="974" y2="135"/>
      <line x1="1200" y1="135" x2="1218" y2="135"/>
    </g>
    <text x="4" y="266" font-size="22" fill="#46525f">Each prototype answers the question the next one depends on. None was skipped.</text>
  </g>
</svg>

**{{ facts.experiment_count }} experiments · {{ facts.decision_record_count }} decision records ·
two human gates**, scored blind against a rubric written before the images existed.

## Speaker notes

The number the whole project is built around. Eight gigabytes — the figure the driver reports, not
the marketing one. The production stack peaks just over five gigabytes and leaves about two hundred
megabytes spare while actually serving. Two point four per cent. It fits, and it does not fit
easily. I never call it headroom.

Six prototypes, each answering the question the next depends on. P0 is the one worth defending.
Building the three-D deck before I had any artwork looks like the wrong order. It was not: it made
the deck's aspect ratio a hard input to the image problem, and it caught an orientation fault that
conveniently square test images would have hidden until the end.

Every choice ran the same loop — alternatives, criteria fixed before the experiment, then the
measured result. Several decision records reject the option I expected to pick, and the next two
are both like that.
