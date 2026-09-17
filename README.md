# VITON: Virtual Try-On Shop

A working prototype of a fashion store with AI virtual try-on. Upload a photo, or pick a sample model, choose a top from the shop, and see it on the person.

- **Virtual try-on** with [DM-VTON](https://github.com/KiseKloset/DM-VTON), a parser-free model: it needs only the photo, the garment and a garment mask. No pose estimation or human parsing, so it works on an arbitrary uploaded photo.
- **Shop** over the VITON-HD garment images, with search and filters. Semantic search through FashionCLIP and Pinecone when configured, metadata filtering when not.
- **Style game**: players pick tops for each other, see them tried on, and rank the results.

React 18 + TypeScript + Vite + Tailwind on the front, FastAPI + PyTorch on the back.

> Demonstration only. The brands, prices and colours in the shop are synthetic, derived from each filename. Both the model and the dataset are licensed for **non-commercial** use, see [Licences](#licences).

---

## Quick start (Windows)

You need Python 3.10, Node.js 18+, the dataset and the model weights.

**1. Dataset.** Download the [VITON-HD dataset](https://github.com/shadow2496/VITON-HD) and place it next to this repository, so the layout is:

```
clothes_tryon_dataset/
  train/
    image/        person photos
    cloth/        garment photos
    cloth-mask/   garment masks
VITON/            this repository
```

Only `image`, `cloth` and `cloth-mask` are used. To keep the dataset elsewhere, set `DATASET_DIR` in `backend/.env`.

**2. Model weights.** Download `dmvton_pf_warp.pt` and `dmvton_pf_gen.pt` from the [DM-VTON release folder](https://drive.google.com/drive/folders/1wfWGsR0vWC5LrA26xhj92ec_GoCKV80A) into:

```
backend/feature_2_VITON_model/DM-VTON/checkpoints/
```

**3. Backend.**

```powershell
cd backend
quick_setup.bat
```

This creates the virtual environment, installs `requirements.txt`, copies `.env.example` to `.env`, and prints the try-on model's status. It should report `'ready': True`.

**4. Frontend.**

```powershell
cd frontend
npm install
```

**5. Run.** `run_app.bat` in the repository root starts both, or separately:

```powershell
cd backend;  venv\Scripts\activate;  uvicorn main:app --reload --port 8000
cd frontend; npm run dev
```

Open http://localhost:5173. On the **Shop** tab, hover a top and click **Try On**, then pick a sample model and click **Generate**.

### Using an NVIDIA GPU

`requirements.txt` installs the CPU build of PyTorch, which is enough: a try-on takes about a second on a laptop CPU. For a GPU, install the CUDA build before the requirements:

```powershell
pip install torch==2.1.1 --index-url https://download.pytorch.org/whl/cu121
```

The model then runs on the GPU automatically (override with `TRYON_DEVICE=cpu`).

---

## Configuration

Both halves read settings from a `.env` file. These are gitignored: copy the `.env.example` in each folder and never commit a real `.env`.

| File | Variable | Purpose |
| --- | --- | --- |
| `backend/.env` | `PINECONE_API_KEY`, `PINECONE_INDEX_HOST` | Optional semantic search. Without them the shop uses metadata filtering and FashionCLIP is never downloaded |
| `backend/.env` | `DATASET_DIR`, `DATASET_SPLIT` | Dataset location, default `../../clothes_tryon_dataset` and `train` |
| `backend/.env` | `DMVTON_CHECKPOINT_DIR`, `TRYON_DEVICE` | Model weights folder, and `cpu` or `cuda` |
| `frontend/.env` | `VITE_API_URL` | Backend URL, default `http://localhost:8000` |

## Checking a setup

```
GET /tryon/status      model weights found, device, loaded or not
GET /debug/dataset     dataset folders and file counts
```

Or run a single try-on without the API:

```powershell
cd backend
python feature_2_VITON_model/tryon_cli.py --person 00000_00.jpg --cloth 00001_00.jpg --output out.png
python feature_2_VITON_model/tryon_cli.py --person me.jpg --cloth shirt.jpg --output out.png
```

Bare filenames are looked up in the dataset.

---

## How the try-on works

`backend/feature_2_VITON_model/dmvton_service.py` wraps DM-VTON for the API.

1. **Garment mask.** A shop garment uses its real mask from the dataset. An uploaded garment gets an estimated one: pixels near the background colour and connected to the image edge are background, everything else is garment, so light prints inside a garment survive.
2. **Framing.** DM-VTON was trained on catalogue photos where the person fills the frame. On a photo with a lot of wall around the person it places the garment where it expects a torso, which puts it over the face. So a person clearly smaller than the frame, on a plain background, is cropped to catalogue framing first. Photos are padded, never stretched, because stretching changes body proportions in the output.
3. **Inference** at the model's native 192 x 256, with the same preprocessing and `align_corners=True` as DM-VTON's official test script.

### Running without cupy

DM-VTON's warping module computes a correlation volume with a CUDA kernel compiled through cupy, and raises `NotImplementedError` on CPU. That is why an earlier version of this project could not run the model. `models/common/correlation.py` now includes a pure PyTorch implementation, used whenever cupy is not installed or the tensors are on CPU. The CUDA kernel is still used when cupy is available on a GPU.

### How it was checked

- **The PyTorch layer matches the kernel exactly.** `feature_2_VITON_model/tests/test_correlation.py` compares it against a line by line transcription of the CUDA kernel's index arithmetic, on odd sizes and strides 1 to 3. Maximum difference 2e-16.
- **The warp puts the garment in the right place.** `feature_2_VITON_model/eval_warp_alignment.py` warps each of 40 test garments onto the person who wears it, and measures overlap with the garment region of that person's parse map:

  | Warp | IoU with true garment region |
  | --- | --- |
  | No warp, flat product mask | 0.373 |
  | **This implementation** | **0.838** (median 0.904) |
  | Correlation with x and y swapped | 0.832 |
  | Correlation zeroed out | 0.810 |

  It is measured on the warp output rather than the final image because the generator can copy the garment from the input photo and hide a bad warp. The two broken variants are there to show how much the measurement can tell apart: this model leans only lightly on the correlation layer, so the end to end numbers support the implementation, and the exact-match test above is the decisive evidence.

### Limitations

- Output is 192 x 256. The model is small and fast by design, not high resolution.
- Best with a front-facing photo against a plain background, dressed in a top. Automatic framing and mask estimation both assume a plain background.
- Tops only. The model was trained on upper-body garments.

---

## API

| Endpoint | |
| --- | --- |
| `POST /viton_preview_upload` | `person_image` file, plus `cloth` (a shop filename) or `cloth_image` (a file). Returns a PNG |
| `GET /tryon/status` | Try-on model status |
| `GET /clothes_list` | Garments (`session_id=store`), sample people (`session_id=people`), or a game's clothes |
| `GET /search_clothes` | Search with `query`, `category`, `color`, `company`, `priceMax` |
| `GET /recommend` | Recommendation carousel |
| `POST /start_game`, `/pick`, `/rank` | Style game |
| `GET /leaderboard`, `/detailed_leaderboard`, `/received_clothes`, `/available_clothes` | Style game state |
| `GET /clothes/{file}`, `/people/{file}` | Dataset images |
| `GET /debug/dataset`, `/debug/directories`, `/debug/test_images` | Setup checks |

Game sessions live in memory, so restarting the backend clears them.

## Project structure

```
backend/
  main.py                          API
  paths.py                         dataset location, shared by every module
  feature_1_pinecone_search/       scripts that build and debug the Pinecone index
  feature_2_VITON_model/
    dmvton_service.py              try-on service
    tryon_cli.py                   one try-on from the command line
    eval_warp_alignment.py         warp accuracy measurement
    tests/                         correlation layer test
    DM-VTON/                       vendored model code
  feature_3_game/                  style game logic
frontend/
  src/components/VirtualTryOn.tsx  try-on page
  src/utils/api.ts                 API client
run_app.bat                        start backend and frontend
```

## Licences

- **DM-VTON** code and weights: [CC BY-NC-SA 4.0](https://github.com/KiseKloset/DM-VTON/blob/main/LICENSE), non-commercial. Vendored in `backend/feature_2_VITON_model/DM-VTON/` from upstream commit `5dcd04e`. Changes: `models/common/correlation.py` gained the PyTorch implementation and an optional cupy import. The `exp/` folder of training and metric experiments is not included.
- **VITON-HD dataset**: [CC BY-NC 4.0](https://github.com/shadow2496/VITON-HD), non-commercial.

Any commercial use of the try-on would need a model and data licensed for it.
