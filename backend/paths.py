"""Where the dataset lives.

Every module reads its paths from here. They used to be relative to each
file's own location, so moving game_logic.py into feature_3_game/ silently
pointed it at a folder that does not exist.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
# Loaded here rather than in main.py so DATASET_DIR applies to every module,
# whichever one happens to be imported first.
load_dotenv(BACKEND_DIR / ".env")

# Default layout: <project>/clothes_tryon_dataset next to <project>/ezyZip.
# Set DATASET_DIR to use a dataset stored anywhere else.
DATASET_ROOT = Path(os.environ.get("DATASET_DIR") or BACKEND_DIR.parent.parent / "clothes_tryon_dataset")
DATASET_SPLIT = os.environ.get("DATASET_SPLIT", "train")

CLOTHES_DIR = str(DATASET_ROOT / DATASET_SPLIT / "cloth")
PEOPLE_DIR = str(DATASET_ROOT / DATASET_SPLIT / "image")
CLOTH_MASK_DIR = str(DATASET_ROOT / DATASET_SPLIT / "cloth-mask")
