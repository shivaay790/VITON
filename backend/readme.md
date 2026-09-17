# Backend

```powershell
quick_setup.bat                      # once: venv, dependencies, .env
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

- `main.py`: the API.
- `paths.py`: where the dataset is. Every module reads its paths from here.
- `feature_1_pinecone_search/`: scripts that build and debug the optional Pinecone index.
- `feature_2_VITON_model/dmvton_service.py`: virtual try-on. `tryon_cli.py` runs one pair without the API.
- `feature_2_VITON_model/DM-VTON/`: vendored model code, see the root README for licence and changes.
- `feature_3_game/`: the style game.

Check a setup with `GET /debug/dataset` and `GET /tryon/status`.
