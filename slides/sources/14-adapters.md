| style | experiment | ships at | verdict |
|---|---|---|---|
| `minimal-geometric` | EXP-027 | step 300 | <span class="tag tag--pass">pass</span> |
| `ukiyo-e` | EXP-028 | step 600 | <span class="tag tag--pass">pass</span> |
| `retro-poster` | EXP-029 | step 300 | <span class="tag tag--partial">partial pass</span> |

Applied at weight **{{ facts.lora_weight_default }}**. Every checkpoint is **verified by SHA-256 on
every request** — the weights cannot be rebuilt, so they are treated as artifacts, not recipes.

<p class="source">docs/deployment/weights-manifest.md · guarded by pytest so the manifest cannot drift from the code</p>

## Speaker notes

What actually ships — a table rather than a claim, so you can check it.

Three adapters, three different checkpoint steps, three separate experiments. Two are clean passes
against the rubric. One is a partial pass, and that is the next slide.

Default weight zero point seven, which is where the blind scoring landed. It stays adjustable in
the interface.

The last line matters more than it looks. Each checkpoint's hash is verified when the style is
activated, on every request — not once at startup. These weights cannot be regenerated, so the
files are the authority, and an integrity check on every request is what catches a swap or a
corruption.

Why they cannot be regenerated is the determinism slide.
