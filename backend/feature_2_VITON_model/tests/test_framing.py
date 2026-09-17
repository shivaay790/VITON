"""Automatic framing must crop people who stand back, and leave catalogue photos alone.

A wrong crop is far worse than no crop: the first version of the framing took
only the largest foreground region, so a white top on a white wall left just
the jeans, and a third of catalogue photos were cropped to the hips. These
tests hold both error rates down. They need the dataset and are skipped
without it.

    python -m pytest feature_2_VITON_model/tests      (from backend/)
"""

import os
import sys

import numpy as np
import pytest
from PIL import Image

BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND)
from paths import DATASET_ROOT  # noqa: E402
from feature_2_VITON_model import dmvton_service as svc  # noqa: E402

IMAGES = DATASET_ROOT / "test" / "image"
pytestmark = pytest.mark.skipif(not IMAGES.is_dir(), reason=f"dataset not found at {IMAGES}")


def _sample(step):
    return sorted(os.listdir(IMAGES))[::step]


def _cropped(image):
    return svc._frame_person(image).size != image.size


def _standing_back(image, scale, shading, rng):
    """The same person further from the camera, on a noisy wall lit from above."""
    w, h = image.size
    arr = np.asarray(image, dtype=np.float32)
    colour = np.median(np.concatenate([arr[0], arr[:, 0], arr[:, -1]]), axis=0)
    wall = (np.tile(colour, (h, w, 1)) + np.linspace(shading, -shading, h)[:, None, None]
            + rng.normal(0, 4, (h, w, 1)))
    canvas = Image.fromarray(np.clip(wall, 0, 255).astype(np.uint8))
    small = image.resize((int(w * scale), int(h * scale)), Image.BICUBIC)
    canvas.paste(small, ((w - small.size[0]) // 2, h - small.size[1]))
    return canvas


def test_catalogue_photos_are_left_alone():
    names = _sample(10)
    cropped = [n for n in names if _cropped(Image.open(IMAGES / n).convert("RGB"))]
    # Measured on all 2032 test photos: 3 cropped, all loosely framed shots whose crop is harmless.
    assert len(cropped) <= 0.01 * len(names), cropped


@pytest.mark.parametrize("scale,shading", [(0.55, 30), (0.7, 8)])
def test_person_standing_back_is_cropped(scale, shading):
    rng = np.random.default_rng(0)
    names = _sample(40)
    hits = sum(_cropped(_standing_back(Image.open(IMAGES / n).convert("RGB"), scale, shading, rng)) for n in names)
    assert hits >= 0.95 * len(names), f"{hits}/{len(names)}"
