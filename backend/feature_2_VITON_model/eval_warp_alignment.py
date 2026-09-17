"""Does the warped garment land on the person where the garment really is?

Paired test images (each person with their own garment), so the ground truth is
the garment region of the person's parse map. Measured on the warp output
directly, because the generator can copy the garment from the input photo and
hide a bad warp in the final image.

Two deliberately broken correlation layers are scored alongside, to show how
much the measurement can tell apart.

    python feature_2_VITON_model/eval_warp_alignment.py --n 40      (from backend/)
"""

import argparse
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import DATASET_ROOT  # noqa: E402
from feature_2_VITON_model import dmvton_service as svc  # noqa: E402
import models.common.correlation as corr  # noqa: E402
import models.warp_modules.mobile_afwm as afwm  # noqa: E402

UPPER_GARMENT_LABELS = [5, 6, 7]  # upper clothes, dress, coat in the VITON-HD parse maps
SIZE = (svc.MODEL_WIDTH, svc.MODEL_HEIGHT)


def swapped_axes(tenFirst, tenSecond, intStride):
    """A plausible misreading of the kernel: x and y displacements transposed."""
    out = corr.correlation_torch(tenFirst, tenSecond, intStride)
    b, _, h, w = out.shape
    return out.view(b, 7, 7, h, w).transpose(1, 2).reshape(b, 49, h, w)


def zeroed(tenFirst, tenSecond, intStride):
    return torch.zeros_like(corr.correlation_torch(tenFirst, tenSecond, intStride))


def iou(a, b):
    return (a & b).sum() / max((a | b).sum(), 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=40)
    parser.add_argument("--split", default="test")
    args = parser.parse_args()

    root = DATASET_ROOT / args.split
    names = sorted(os.listdir(root / "image"))
    names = names[:: max(1, len(names) // args.n)][: args.n]

    pipeline = svc.TryOnService(device="cpu")._load()

    def warped_mask(person, cloth, mask):
        p = svc._to_model_tensor(person.convert("RGB").resize(SIZE, Image.BICUBIC))
        c = svc._to_model_tensor(cloth.convert("RGB").resize(SIZE, Image.BICUBIC))
        m = (svc._mask_to_tensor(mask.convert("L").resize(SIZE, Image.NEAREST)) > 0.5).float()
        with torch.no_grad():
            _, flow = pipeline.warp_model(p, c * m, phase="test")
            warped = F.grid_sample(m, flow.permute(0, 2, 3, 1), mode="bilinear",
                                   padding_mode="zeros", align_corners=True)
        return warped[0, 0].numpy() > 0.5

    variants = {"correct": corr.FunctionCorrelation, "swapped_axes": swapped_axes, "zeroed": zeroed}
    scores = {k: [] for k in variants}
    flat = []
    for name in names:
        person = Image.open(root / "image" / name)
        cloth = Image.open(root / "cloth" / name)
        mask = Image.open(root / "cloth-mask" / name)
        parse = np.asarray(Image.open(root / "image-parse-v3" / name.replace(".jpg", ".png")).resize(SIZE, Image.NEAREST))
        truth = np.isin(parse, UPPER_GARMENT_LABELS)
        flat.append(iou(np.asarray(mask.convert("L").resize(SIZE, Image.NEAREST)) > 127, truth))
        for key, fn in variants.items():
            afwm.FunctionCorrelation = fn  # looked up at call time by the warp module
            scores[key].append(iou(warped_mask(person, cloth, mask), truth))
    afwm.FunctionCorrelation = corr.FunctionCorrelation

    print(f"{len(names)} paired {args.split} images: IoU of warped garment mask vs garment region on the person")
    print(f"  {'no warp (flat product mask)':30s} {np.mean(flat):.3f}")
    for key in variants:
        print(f"  {key:30s} {np.mean(scores[key]):.3f}  (median {np.median(scores[key]):.3f})")
    for key in ("swapped_axes", "zeroed"):
        wins = sum(c > o for c, o in zip(scores["correct"], scores[key]))
        print(f"  correct beats {key} in {wins}/{len(names)} images")


if __name__ == "__main__":
    main()
