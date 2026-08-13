**Yes — and the configuration that fits is now specific and measured.** SD 1.5 at
{{ facts.generation_width }}×{{ facts.generation_height }}, one per-style LoRA at
{{ facts.lora_weight_default }}, IP-Adapter at {{ facts.ip_adapter_scale_default }}, one resident pipeline.

Bounded three ways: **the margin is 2.4 %** · **reproducible describes inference, not training** ·
**"multiple distinct styles" is three, and one is partial.**

*Not concluded:* that LoRA beats the alternatives · that SD 1.5 is the best base model · that three
styles is enough · that any image count is a threshold · that a green suite means good pictures.

<p class="source">report §19 · eight RQs answered in scope, four bounded, one component inconclusive</p>

## Speaker notes

The answer is yes, and the useful part is the specificity: I can name the configuration that fits,
with the memory reading behind each element.

But the bounds matter more than the yes, so I state all three every time. The margin is two point
four per cent — it fits, not comfortably. Reproducible describes inference, not training. And
multiple distinct styles means three, one of which is partial.

The second half is what I would most like to be judged on: things I could easily have concluded and
did not, because I did not measure them. That LoRA beats the alternatives. That SD 1.5 is the best
base model. Any minimum image count. That a green test suite means good pictures.

Each of those is one easy sentence. None is supported by what I measured, so none of them is in the
report.
