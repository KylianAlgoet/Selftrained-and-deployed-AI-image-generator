"""The three production styles, and the checkpoints the service is allowed to serve.

Nothing here is a new decision. The styles, their triggers and the prompt form come
from the frozen M6 style kit; the checkpoints, the step counts, the PASS/PARTIAL
PASS outcomes and the default adapter weight come from Kylian's gate-2 approval and
DR-010. This module's own job is to make those choices *checkable at runtime*.

THE CHECKPOINTS ARE AUTHORITATIVE AS FILES, BY SHA-256 - NOT AS A RECIPE.
Risk R14: LoRA initialisation drew from an unseeded global RNG during M6, so these
adapters cannot be regenerated from their recorded seed. The R14 fix is
forward-only and deliberately did not touch them. If a file fails its hash check
the correct behaviour is to refuse to serve, never to retrain or "regenerate".
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ml.dataset.captions import STYLE_PHRASES
from ml.training.style_kit import style_by_key

# DR-010, confirmed by Kylian at gate 2. The user may adjust within the range; the
# default is what the human review actually scored.
DEFAULT_LORA_WEIGHT = 0.7
LORA_WEIGHT_MIN = 0.4
LORA_WEIGHT_MAX = 1.0

# DR-008. Above 0.60 prompt authority falls and pseudo-text / source-like
# composition increase, so the range is capped rather than open.
DEFAULT_IP_ADAPTER_SCALE = 0.55
IP_ADAPTER_SCALE_MIN = 0.40
IP_ADAPTER_SCALE_MAX = 0.60

OUTCOME_PASS = "PASS"
OUTCOME_PARTIAL_PASS = "PARTIAL PASS"

ADAPTER_FILENAME = "pytorch_lora_weights.safetensors"


class CheckpointUnavailable(RuntimeError):
    """A production adapter is missing, unreadable, or fails its recorded hash."""


@dataclass(frozen=True)
class ProductionStyle:
    key: str
    label: str
    run_id: str
    checkpoint_step: int
    run_dir: str
    sha256: str
    size_bytes: int
    outcome: str
    limitation: str

    @property
    def trigger(self) -> str:
        return style_by_key(self.key).trigger

    @property
    def phrase(self) -> str:
        return STYLE_PHRASES[self.key]

    @property
    def is_partial_pass(self) -> bool:
        return self.outcome == OUTCOME_PARTIAL_PASS

    def adapter_dir(self, repo_root: Path) -> Path:
        return repo_root / "outputs" / "lora" / self.run_dir / f"step{self.checkpoint_step:05d}"

    def adapter_path(self, repo_root: Path) -> Path:
        return self.adapter_dir(repo_root) / ADAPTER_FILENAME


# Recorded in docs/evidence/prototype-4/GATE-2-approval.md and DR-010, and
# re-verified against the files on disk on 2026-08-06 (all three matched, each
# 6 414 480 bytes, 256 tensors, 256 LoRA keys, zero base-model keys).
#
# Two of the three are step 300, not the 600 their runs trained to. That is the
# milestone's most informative result, not a typo: prompt adherence fell from 4 to
# 3 at step 600 for minimal-geometric and retro-poster while style consistency held
# at 5. Only ukiyo-e improved with more training.
PRODUCTION_STYLES: tuple[ProductionStyle, ...] = (
    ProductionStyle(
        key="minimal-geometric",
        label="Minimal geometric",
        run_id="EXP-027",
        checkpoint_step=300,
        run_dir="EXP-027__style-full__512x512__r8a8__lr0p0001__bs1x1__st600__seed42__tier0",
        sha256="2d425838cce59adc5c12b894e29439b695b98b9e40ef5d7ae667bd5216cb96a8",
        size_bytes=6414480,
        outcome=OUTCOME_PASS,
        limitation="",
    ),
    ProductionStyle(
        key="ukiyo-e",
        label="Ukiyo-e woodblock",
        run_id="EXP-028",
        checkpoint_step=600,
        run_dir="EXP-028__style-full__512x512__r8a8__lr0p0001__bs1x1__st600__seed42__tier0",
        sha256="52381b6052ad71f165ed23425bfc4ea1ba794a3886948a741cea9cad3d81abfd",
        size_bytes=6414480,
        outcome=OUTCOME_PASS,
        limitation="",
    ),
    ProductionStyle(
        key="retro-poster",
        label="Retro silkscreen poster",
        run_id="EXP-029",
        checkpoint_step=300,
        run_dir="EXP-029__style-full__512x512__r8a8__lr0p0001__bs1x1__st600__seed42__tier0",
        sha256="70d2afbfb3c09aff6ba37e1f1cf82c02ad69b0269969ea7cdf43b0ead17ba8db",
        size_bytes=6414480,
        outcome=OUTCOME_PARTIAL_PASS,
        # H4 was confirmed at gate 2. This ships stated, not hidden, and the style
        # was explicitly NOT dropped and NOT upgraded to a full pass.
        limitation=(
            "Partial pass: this style also learned poster conventions from its sources - "
            "pseudo-text, borders and framed composition can appear in results."
        ),
    ),
)

STYLE_KEYS: tuple[str, ...] = tuple(s.key for s in PRODUCTION_STYLES)


def production_style(key: str) -> ProductionStyle:
    for style in PRODUCTION_STYLES:
        if style.key == key:
            return style
    raise KeyError(f"unknown style {key!r}; expected one of {list(STYLE_KEYS)}")


def build_prompt(style_key: str, subject: str) -> str:
    """`<trigger> <style phrase> skateboard decal artwork, <subject>`.

    This is the EXACT form the scored M6 matrix generated with
    (`ml/training/final_matrix.py`, `build_prompt`), reproduced here rather than
    reinvented, so what a user gets is the thing the human review actually judged.
    """
    style = production_style(style_key)
    cleaned = " ".join(subject.split()).strip().rstrip(".")
    if not cleaned:
        raise ValueError("subject must not be empty")
    return f"{style.trigger} {style.phrase} skateboard decal artwork, {cleaned}"


def verify_checkpoint(style: ProductionStyle, repo_root: Path) -> Path:
    """Return the adapter path only if it is present and matches its recorded hash.

    Runs on every style activation, not once at startup: the adapters live in the
    git-ignored `outputs/` tree, where a stale copy or a partial write is a real
    possibility, and serving an unverified adapter would silently invalidate the
    link between what a user sees and what was scored.
    """
    path = style.adapter_path(repo_root)
    if not path.is_file():
        raise CheckpointUnavailable(
            f"{style.key}: adapter file missing for {style.run_id} step {style.checkpoint_step}"
        )

    data = path.read_bytes()
    if len(data) != style.size_bytes:
        raise CheckpointUnavailable(
            f"{style.key}: adapter is {len(data)} bytes, expected {style.size_bytes}"
        )

    digest = hashlib.sha256(data).hexdigest()
    if digest != style.sha256:
        raise CheckpointUnavailable(
            f"{style.key}: adapter sha256 {digest} does not match the recorded "
            f"{style.sha256} from the gate-2 approval"
        )
    return path
