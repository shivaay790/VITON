"""Run one try-on from the command line, without starting the API.

    python feature_2_VITON_model/tryon_cli.py --person me.jpg --cloth shirt.jpg --output out.png
    python feature_2_VITON_model/tryon_cli.py --person 00000_00.jpg --cloth 00001_00.jpg --output out.png

Bare filenames are looked up in the dataset (person in image/, garment in cloth/),
and a dataset garment uses its real mask from cloth-mask/.
"""

import argparse
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import CLOTHES_DIR, CLOTH_MASK_DIR, PEOPLE_DIR  # noqa: E402
from feature_2_VITON_model.dmvton_service import TryOnService  # noqa: E402


def resolve(path, dataset_dir):
    if os.path.isfile(path):
        return path
    candidate = os.path.join(dataset_dir, path)
    if os.path.isfile(candidate):
        return candidate
    sys.exit(f"Not found: {path} (also looked in {dataset_dir})")


def main():
    parser = argparse.ArgumentParser(description="DM-VTON virtual try-on for a single image pair")
    parser.add_argument("--person", required=True, help="photo path, or a dataset filename")
    parser.add_argument("--cloth", required=True, help="garment image path, or a dataset filename")
    parser.add_argument("--output", required=True, help="where to write the result (PNG)")
    parser.add_argument("--mask", help="garment mask; defaults to the dataset mask, else estimated")
    parser.add_argument("--device", help="cpu or cuda; defaults to cuda when available")
    args = parser.parse_args()

    person_path = resolve(args.person, PEOPLE_DIR)
    cloth_path = resolve(args.cloth, CLOTHES_DIR)
    mask_path = args.mask
    if mask_path is None:
        dataset_mask = os.path.join(CLOTH_MASK_DIR, os.path.basename(cloth_path))
        if os.path.dirname(os.path.abspath(cloth_path)) == os.path.abspath(CLOTHES_DIR) and os.path.isfile(dataset_mask):
            mask_path = dataset_mask

    service = TryOnService(device=args.device)
    if service.missing_checkpoints():
        sys.exit(f"Missing model weights: {service.status()}")
    result = service.try_on(
        Image.open(person_path),
        Image.open(cloth_path),
        Image.open(mask_path) if mask_path else None,
    )
    result.save(args.output)
    print(f"Saved {args.output}  (mask: {'given' if mask_path else 'estimated'}, device: {service.device})")


if __name__ == "__main__":
    main()
