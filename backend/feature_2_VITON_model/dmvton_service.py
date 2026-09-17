"""Virtual try-on with DM-VTON, wrapped for the API.

DM-VTON is parser-free: it needs only a photo of the person, a garment image
and a mask of that garment. No pose estimation or human parsing is involved,
which is what makes it usable on an arbitrary uploaded photo.

Model: https://github.com/KiseKloset/DM-VTON (CC BY-NC-SA 4.0, non-commercial).
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from scipy import ndimage

DMVTON_DIR = Path(__file__).resolve().parent / "DM-VTON"
if str(DMVTON_DIR) not in sys.path:
    sys.path.insert(0, str(DMVTON_DIR))

# DM-VTON was trained on VITON at 192 x 256 and its test script feeds images at
# exactly that size, so every input is brought to it.
MODEL_WIDTH, MODEL_HEIGHT = 192, 256
CHECKPOINT_FILES = {"warp": "dmvton_pf_warp.pt", "gen": "dmvton_pf_gen.pt"}
DEFAULT_CHECKPOINT_DIR = DMVTON_DIR / "checkpoints"

# How far a pixel may sit from the background colour and still count as
# background when a garment mask has to be estimated, on a 0 to 255 scale.
BACKGROUND_TOLERANCE = 20
# Looser, for finding a person against a real wall with shading and noise.
PERSON_TOLERANCE = 40
# VITON framing: the person fills the frame from just above the head down.
HEAD_MARGIN = 0.05
# Only reframe when at least this share of the photo's height is empty above
# the person. Catalogue photos have the head near the top edge.
MIN_SPACE_ABOVE = 0.15
# Foreground regions smaller than this share of the image are specks, not the person.
MIN_REGION_SHARE = 0.002


def _to_model_tensor(image: Image.Image) -> torch.Tensor:
    """RGB image at model size to a 1x3xHxW tensor in [-1, 1]."""
    array = np.asarray(image, dtype=np.float32) / 255.0
    tensor = torch.from_numpy(array).permute(2, 0, 1)
    return (tensor * 2.0 - 1.0).unsqueeze(0)


def _mask_to_tensor(mask: Image.Image) -> torch.Tensor:
    array = np.asarray(mask, dtype=np.float32) / 255.0
    return torch.from_numpy(array)[None, None]


def _border_colour(array: np.ndarray) -> np.ndarray:
    border = np.concatenate([array[0], array[-1], array[:, 0], array[:, -1]])
    return np.median(border, axis=0)


def estimate_garment_mask(cloth: Image.Image) -> Image.Image:
    """Mask for a product photo on a plain background.

    Pixels close to the border colour and connected to the image edge are
    background, everything else is garment. Filling from the edge rather than
    thresholding keeps light prints or white panels inside the garment.
    """
    array = np.asarray(cloth.convert("RGB"), dtype=np.int16)
    distance = np.abs(array - _border_colour(array)).max(axis=2)
    near_background = distance <= BACKGROUND_TOLERANCE

    labels, _ = ndimage.label(near_background)
    edge_labels = np.unique(
        np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    )
    background = np.isin(labels, edge_labels[edge_labels > 0])
    garment = ndimage.binary_opening(~background, iterations=1)
    return Image.fromarray((garment * 255).astype(np.uint8), mode="L")


def _background_by_row(array: np.ndarray, band: int = 20, smooth: int = 101) -> np.ndarray:
    """Wall colour for each row, from the left and right edges of the photo.

    A real wall is lit unevenly, usually brighter at the top. Against one
    global background colour the bright upper wall reads as foreground.
    Taking each row's colour from its own edges, smoothed down the image so an
    arm touching the edge does not skew it, follows the gradient instead.
    """
    edges = np.concatenate([array[:, :band], array[:, -band:]], axis=1)
    rows = np.median(edges, axis=1)
    rows = ndimage.median_filter(rows, size=(min(smooth, len(rows)), 1), mode="nearest")
    return rows[:, None, :]


def _person_box(image: Image.Image) -> tuple[int, int, int, int] | None:
    """Bounding box of the person in a photo taken against a plain background.

    Takes every sizeable foreground region, not just the largest. A white top
    on a white wall is invisible to this, and with only the largest region the
    box shrank to the jeans and the photo was cropped to the hips. With all
    regions the hair and face still anchor the top of the box.

    Returns None when no clear foreground is found, for example on a busy
    background, in which case the photo is used as framed.
    """
    array = np.asarray(image, dtype=np.int16)
    foreground = np.abs(array - _background_by_row(array)).max(axis=2) > PERSON_TOLERANCE
    foreground = ndimage.binary_opening(foreground, iterations=2)
    labels, count = ndimage.label(foreground)
    if count == 0:
        return None
    sizes = ndimage.sum(foreground, labels, index=range(1, count + 1))
    keep = np.flatnonzero(sizes >= MIN_REGION_SHARE * foreground.size) + 1
    person = np.isin(labels, keep)
    share = person.mean()
    if keep.size == 0 or share < 0.03 or share > 0.9:
        return None
    rows, cols = np.where(person.any(axis=1))[0], np.where(person.any(axis=0))[0]
    return int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1


def _frame_person(image: Image.Image) -> Image.Image:
    """Crop and pad a photo to the model's 3:4 aspect and VITON-style framing.

    DM-VTON was trained on catalogue shots where the person fills the frame.
    Given a photo with a lot of wall around the person it places the garment
    where it expects a torso, which lands it over the face. So when there is
    clearly empty space above the person and they are clearly smaller than the
    frame, they are cropped to that framing first. Every doubtful case is left
    as it is: a wrong crop is far worse than no crop.
    Padding uses the photo's own border colour, never stretching, since
    stretching changes body proportions in the output.
    """
    width, height = image.size
    ratio = MODEL_WIDTH / MODEL_HEIGHT
    box = _person_box(image)

    if box is not None:
        left, top, right, bottom = box
        crop_h = (bottom - top) / (1 - HEAD_MARGIN)
        crop_h = max(crop_h, (right - left) / ratio / 0.9)
        if top > MIN_SPACE_ABOVE * height and crop_h < 0.85 * height:
            crop_w = crop_h * ratio
            centre = (left + right) / 2
            x0 = round(centre - crop_w / 2)
            y0 = round(top - HEAD_MARGIN * crop_h)
            frame = (x0, y0, x0 + round(crop_w), y0 + round(crop_h))
        else:
            box = None

    if box is None:
        if width / height > ratio:
            crop_w, crop_h = width, width / ratio
        else:
            crop_w, crop_h = height * ratio, height
        x0, y0 = round((width - crop_w) / 2), round((height - crop_h) / 2)
        frame = (x0, y0, x0 + round(crop_w), y0 + round(crop_h))

    if frame == (0, 0, width, height):
        return image
    fill = tuple(int(c) for c in _border_colour(np.asarray(image)))
    canvas = Image.new("RGB", (frame[2] - frame[0], frame[3] - frame[1]), fill)
    canvas.paste(image, (-frame[0], -frame[1]))
    return canvas


class TryOnService:
    def __init__(self, checkpoint_dir: str | os.PathLike | None = None, device: str | None = None):
        self.checkpoint_dir = Path(
            checkpoint_dir or os.environ.get("DMVTON_CHECKPOINT_DIR") or DEFAULT_CHECKPOINT_DIR
        )
        self.device = device or os.environ.get("TRYON_DEVICE") or (
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self._pipeline = None
        self._lock = threading.Lock()

    def missing_checkpoints(self) -> list[str]:
        return [
            name for name in CHECKPOINT_FILES.values() if not (self.checkpoint_dir / name).is_file()
        ]

    def status(self) -> dict:
        missing = self.missing_checkpoints()
        return {
            "model": "DM-VTON (parser-free)",
            "ready": not missing,
            "loaded": self._pipeline is not None,
            "device": self.device,
            "checkpoint_dir": str(self.checkpoint_dir),
            "missing_checkpoints": missing,
            "input_size": [MODEL_WIDTH, MODEL_HEIGHT],
        }

    def _load(self):
        if self._pipeline is not None:
            return self._pipeline
        missing = self.missing_checkpoints()
        if missing:
            raise FileNotFoundError(
                f"DM-VTON checkpoints not found in {self.checkpoint_dir}: {', '.join(missing)}"
            )
        from pipelines.dmvton_pipeline import DMVTONPipeline

        checkpoints = {
            key: str(self.checkpoint_dir / name) for key, name in CHECKPOINT_FILES.items()
        }
        # align_corners=True matches the official test script the checkpoints were evaluated with.
        pipeline = DMVTONPipeline(align_corners=True, checkpoints=checkpoints)
        self._pipeline = pipeline.to(self.device).eval()
        return self._pipeline

    def try_on(
        self,
        person: Image.Image,
        cloth: Image.Image,
        cloth_mask: Image.Image | None = None,
    ) -> Image.Image:
        """Dress `person` in `cloth`. Returns a 192 x 256 image, framed as the model saw it.

        `cloth_mask` should be supplied when a real garment mask exists, such as
        the dataset's cloth-mask images. Without one it is estimated.
        """
        person = person.convert("RGB")
        cloth = cloth.convert("RGB")
        cloth_mask = cloth_mask.convert("L") if cloth_mask is not None else estimate_garment_mask(cloth)

        framed = _frame_person(person)
        size = (MODEL_WIDTH, MODEL_HEIGHT)
        person_t = _to_model_tensor(framed.resize(size, Image.BICUBIC))
        cloth_t = _to_model_tensor(cloth.resize(size, Image.BICUBIC))
        mask_t = _mask_to_tensor(cloth_mask.resize(size, Image.NEAREST))

        with self._lock:
            pipeline = self._load()
            with torch.no_grad():
                tryon, _ = pipeline(
                    person_t.to(self.device),
                    cloth_t.to(self.device),
                    mask_t.to(self.device),
                    phase="test",
                )

        # Same mapping as torchvision.utils.save_image(normalize=True, value_range=(-1, 1)).
        output = ((tryon[0].float().cpu().clamp(-1, 1) + 1) / 2).mul(255).add(0.5).clamp(0, 255)
        return Image.fromarray(output.byte().permute(1, 2, 0).numpy(), mode="RGB")
