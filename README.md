# VITON — AI-Assisted Virtual Try-On Platform

End-to-end prototype for an AI-assisted fashion shopping experience. The project combines a Vite + React frontend with a FastAPI backend that serves dataset assets, powers a multiplayer styling game, and runs VITON-HD for virtual garment try-on.

## Highlights
- Shop view backed by the `clothes_tryon_dataset`, with filtering hooks and cart state.
- GPU-enabled virtual try-on pipeline (VITON-HD) that composites user uploads with catalog garments.
- Styling game mode with round-based scoring, leaderboards, and real-time picks.
- Semantic or fallback search for garments (Pinecone optional).
- Chatbot and designer studio panels prepared for future AI integrations.

## 🔑 Environment & Secrets

Both halves of the app read their configuration from `.env` files, which are gitignored:

| File | Variable | Purpose |
| --- | --- | --- |
| `backend/.env` | `PINECONE_API_KEY` | Semantic garment search ([app.pinecone.io](https://app.pinecone.io)) |
| `frontend/.env` | `VITE_API_URL` | Base URL of the backend (defaults to `http://localhost:8000`) |

Copy the matching `.env.example` in each directory and fill in your own values. Never commit a real `.env`.

## Project Structure
- `frontend/` — React 18 + TypeScript app (Vite, Tailwind, lucide-react) providing the UI, tabs, and API client.
- `backend/` — FastAPI service exposing game endpoints, dataset browse/search, VITON preview generation, and static serving of garment/person imagery.
- `clothes_tryon_dataset/` — Expected sibling directory containing `train/` and `test/` splits with images, masks, OpenPose keypoints, and parses.
- `backend/VITON-HD/` — Bundled third-party implementation and checkpoints used by `viton_backend.py`.

## Prerequisites
- Python 3.10+ (GPU-enabled PyTorch recommended for VITON-HD).
- Node.js 18+ and npm.
- (Optional) Pinecone account for semantic search — supply `PINECONE_API_KEY` and `PINECONE_ENVIRONMENT`.
- Ensure the `clothes_tryon_dataset` directory sits two levels above `backend/main.py`, matching the current repo layout.

## Backend Setup
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment (required)
copy .env.example .env      # macOS/Linux: cp .env.example .env
# then edit .env and set PINECONE_API_KEY

uvicorn main:app --reload --port 8000
```

Notes:
- The service requires access to GPU-friendly PyTorch for acceptable VITON performance.
- `quick_setup.bat` contains a minimal bootstrap sequence for Windows shells.
- VITON checkpoints are expected in `backend/VITON-HD/checkpoints/` (`seg_final.pth`, `gmm_final.pth`, `alias_final.pth`).

## Frontend Setup
```powershell
cd frontend
npm install

copy .env.example .env      # macOS/Linux: cp .env.example .env
# VITE_API_URL defaults to http://localhost:8000 - change it to point at a deployed backend

npm run dev
# Vite serves on http://localhost:5173 by default
```

The backend URL lives in one place, `frontend/src/config.ts`, which reads `VITE_API_URL`.
The frontend reads backend status from `${VITE_API_URL}/api/ping` and expects garment assets at `/clothes/{filename}` and people assets at `/people/{filename}`.

## Key API Endpoints
- `POST /start_game` — initialize multiplayer styling session.
- `GET /clothes_list` — paginate garments; accepts `session_id`, paging params, and filters.
- `GET /search_clothes` — semantic or fallback filename search.
- `POST /viton_preview_upload` — upload person + cloth images; returns composited preview.
- `GET /recommend` — sample top garments for recommendation carousel.
- `GET /debug/*` — utility endpoints for verifying dataset, VITON setup, and static serving.

## Development Tips
- Keep the backend running on port 8000 before starting the frontend dev server.
- When testing virtual try-on, make sure uploaded filenames exist in the dataset (cloth masks and pose data must be present).
- The styling game stores session state in-memory; restarting the backend resets all games.
- For Pinecone search, confirm the index `fashion-clip-index` exists or the backend will fall back to filename search.

## Next Steps
- Harden authentication and persistence layers (currently none).
- Add production-ready deployment configs (Docker, CI/CD).
- Expand metadata for garments to unlock richer filtering and recommendations.

Happy experimenting!

