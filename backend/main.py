from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Dict, Optional
import io
import os
import sys
import traceback
sys.path.append(os.path.dirname(__file__))
from paths import CLOTHES_DIR, PEOPLE_DIR, CLOTH_MASK_DIR, DATASET_ROOT
from feature_3_game.game_logic import (
    init_game, get_clothes, make_pick, make_ranking, get_leaderboard, get_game_state,
    get_available_clothes_for_player,
)
from feature_2_VITON_model.dmvton_service import TryOnService
import torch
import pinecone
from PIL import Image as PILImage
from starlette.concurrency import run_in_threadpool
from starlette.staticfiles import StaticFiles as StarletteStaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(f"[Startup] CLOTHES_DIR: {CLOTHES_DIR}")
print(f"[Startup] PEOPLE_DIR: {PEOPLE_DIR}")
try:
    clothes_files = os.listdir(CLOTHES_DIR)
    jpg_clothes = [f for f in clothes_files if f.endswith('.jpg')]
    print(f"[Startup] CLOTHES_DIR total files: {len(clothes_files)}")
    print(f"[Startup] CLOTHES_DIR JPG files: {len(jpg_clothes)}")
    print(f"[Startup] CLOTHES_DIR sample files: {jpg_clothes[:5]}{' ...' if len(jpg_clothes) > 5 else ''}")
except Exception as e:
    print(f"[Startup] Could not list CLOTHES_DIR: {e}")
try:
    people_files = os.listdir(PEOPLE_DIR)
    jpg_people = [f for f in people_files if f.endswith('.jpg')]
    print(f"[Startup] PEOPLE_DIR total files: {len(people_files)}")
    print(f"[Startup] PEOPLE_DIR JPG files: {len(jpg_people)}")
    print(f"[Startup] PEOPLE_DIR sample files: {jpg_people[:5]}{' ...' if len(jpg_people) > 5 else ''}")
except Exception as e:
    print(f"[Startup] Could not list PEOPLE_DIR: {e}")

class CORSMiddlewareStaticFiles(StarletteStaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'
        if response.status_code == 404:
            print(f"[StaticFiles] 404 for {path} in {self.directory}")
        return response

# check_dir=False so the API still starts, and reports the problem, when the dataset is missing.
app.mount("/clothes", CORSMiddlewareStaticFiles(directory=CLOTHES_DIR, check_dir=False), name="clothes")
app.mount("/people", CORSMiddlewareStaticFiles(directory=PEOPLE_DIR, check_dir=False), name="people")

PRODUCT_BRANDS = ["Adidas", "Levi's", "Puma", "HUGO", "Nike", "Champion", "Tommy Hilfiger", "Calvin Klein"]
PRODUCT_CATEGORIES = ["tshirts", "shirts", "hoodies", "jackets"]
PRODUCT_COLORS = ["white", "black", "navy", "gray", "blue", "red", "green"]
PRODUCT_PRICE_BUCKETS = sorted(set(
    list(range(0, 2001, 50)) +
    list(range(25, 2000, 50)) +
    list(range(49, 2000, 50)) +
    list(range(99, 2000, 100))
))


def _stable_hash(text: str) -> int:
    value = 0
    for i, ch in enumerate(text.lower()):
        value = (value * 131 + (ord(ch) * (i + 1))) % 1000000007
    return value


def _metadata_for_cloth(filename: str):
    base = os.path.splitext(filename)[0]
    h = _stable_hash(base)
    return {
        "brand": PRODUCT_BRANDS[h % len(PRODUCT_BRANDS)],
        "category": PRODUCT_CATEGORIES[(h // 3) % len(PRODUCT_CATEGORIES)],
        "color": PRODUCT_COLORS[(h // 7) % len(PRODUCT_COLORS)],
        "price": PRODUCT_PRICE_BUCKETS[(h // 11) % len(PRODUCT_PRICE_BUCKETS)]
    }


def _matches_filters(filename: str, query: str = "", category: str = None, color: str = None, company: str = None, price_max: int = None) -> bool:
    meta = _metadata_for_cloth(filename)
    query_text = (query or "").strip().lower()

    if category and category.strip():
        normalized_category = category.strip().lower()
        if normalized_category != "tops" and meta["category"] != normalized_category:
            return False

    if color and color.strip() and meta["color"] != color.strip().lower():
        return False

    if company and company.strip() and meta["brand"].lower() != company.strip().lower():
        return False

    if price_max is not None and meta["price"] > price_max:
        return False

    if query_text and query_text != "all":
        searchable = f"{filename.lower()} {meta['brand'].lower()} {meta['category'].lower()} {meta['color'].lower()} {meta['price']}"
        # Every word must appear somewhere, so "black hoodie" matches a black item in "hoodies".
        if not all(word in searchable for word in query_text.split()):
            return False

    return True

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")  
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "aped-4627-b74a")
PINECONE_INDEX_HOST = (
    os.environ.get("PINECONE_INDEX_HOST")
    or os.environ.get("PINECONE_HOST")
    or os.environ.get("PINECONE_INDEX_URL")
)
if PINECONE_INDEX_HOST:
    PINECONE_INDEX_HOST = PINECONE_INDEX_HOST.strip().strip("`")

# Initialize Pinecone with improved error handling
index = None
try:
    if PINECONE_API_KEY and PINECONE_API_KEY != "YOUR_API_KEY":
        if not PINECONE_INDEX_HOST:
            print("[WARN] PINECONE_INDEX_HOST is missing; set it to your index host URL")
            index = None
            raise RuntimeError("Missing PINECONE_INDEX_HOST")
        print(f"Attempting to initialize Pinecone using host: {PINECONE_INDEX_HOST}")
        # Support both old and new Pinecone SDKs.
        if hasattr(pinecone, "Pinecone"):
            pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
            index = pc.Index("fashion-clip-index", host=PINECONE_INDEX_HOST)
            print(f"[OK] Pinecone initialized with explicit host for index 'fashion-clip-index'.")
        else:
            pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
            index = pinecone.Index("fashion-clip-index", host=PINECONE_INDEX_HOST)
            print(f"[OK] Pinecone (legacy SDK) initialized with explicit host for index 'fashion-clip-index'.")
    else:
        print("[WARN] PINECONE_API_KEY not found or not properly set")
        index = None
except Exception as e:
    print(f"[WARN] Failed to initialize Pinecone: {e}")
    index = None

# FashionCLIP embeds search queries for Pinecone. It is a large download, so it
# is only loaded when semantic search is actually available.
processor = model = None
device = "cuda" if torch.cuda.is_available() else "cpu"
if index is not None:
    from transformers import AutoProcessor, CLIPModel
    clip_model_name = "patrickjohncyh/fashion-clip"
    processor = AutoProcessor.from_pretrained(clip_model_name)
    model = CLIPModel.from_pretrained(clip_model_name).to(device)
else:
    print("[INFO] Pinecone not configured: shop search uses metadata filtering instead of FashionCLIP")

tryon_service = TryOnService()
print(f"[Startup] Try-on: {tryon_service.status()}")

class StartGameRequest(BaseModel):
    num_players: int
    num_rounds: int
    timer: int
    n_clothes: Optional[int] = 10

class PickRequest(BaseModel):
    session_id: str
    round_num: int
    player: str
    picks: Dict[str, int]

class RankRequest(BaseModel):
    session_id: str
    round_num: int
    player: str
    ranking: List[int]

@app.post("/start_game")
def start_game(req: StartGameRequest):
    print("Received start_game request:", req)
    try:
        n_clothes = req.n_clothes if req.n_clothes is not None else 10
        session_id = init_game(req.num_players, req.num_rounds, req.timer, n_clothes)
        game_state = get_game_state(session_id)
        
        response = {
            "session_id": session_id, 
            "players": game_state['players'],
            "timer": game_state['timer'],
            "num_rounds": game_state['num_rounds']
        }
        
        print(f"[start_game] Returning response: {response}")
        print(f"[start_game] Number of players returned: {len(game_state['players'])}")
        
        return response
    except Exception as e:
        print("Error in /start_game:", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/design")
def design(prompt: str = Body(...)):
    # Placeholder: return a static image for now
    return {"image": "https://images.pexels.com/photos/1884581/pexels-photo-1884581.jpeg?auto=compress&cs=tinysrgb&w=500"}

@app.get("/clothes_list")
def clothes_list(
    session_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    category: str = Query(None),
    color: str = Query(None),
    company: str = Query(None),
    priceMax: int = Query(None)
):
    try:
        if session_id == "store":
            clothes_dir = CLOTHES_DIR
            print(f"[clothes_list] Loading from: {clothes_dir}")
            print(f"[clothes_list] Directory exists: {os.path.exists(clothes_dir)}")
            
            if not os.path.exists(clothes_dir):
                print(f"[clothes_list] [ERROR] Directory does not exist: {clothes_dir}")
                return {"clothes": [], "total": 0, "page": page, "page_size": page_size}
            
            all_files = os.listdir(clothes_dir)
            all_clothes = [f for f in all_files if f.endswith('.jpg')]
            print(f"[clothes_list] Found {len(all_clothes)} JPG files out of {len(all_files)} total files")
            
            filtered_clothes = [
                f for f in all_clothes
                if _matches_filters(
                    f,
                    category=category,
                    color=color,
                    company=company,
                    price_max=priceMax
                )
            ]
            total = len(filtered_clothes)
            start = (page - 1) * page_size
            end = start + page_size
            page_clothes = filtered_clothes[start:end]
            print(
                f"[clothes_list] Returning {len(page_clothes)} items for page {page} "
                f"after filters category='{category}', color='{color}', company='{company}', priceMax='{priceMax}'"
            )
            return {"clothes": page_clothes, "total": total, "page": page, "page_size": page_size}
        elif session_id == "people":
            people_dir = PEOPLE_DIR
            print(f"[clothes_list] Loading people from: {people_dir}")
            print(f"[clothes_list] Directory exists: {os.path.exists(people_dir)}")
            
            if not os.path.exists(people_dir):
                print(f"[clothes_list] [ERROR] Directory does not exist: {people_dir}")
                return {"clothes": [], "total": 0, "page": page, "page_size": page_size}
            
            all_files = os.listdir(people_dir)
            all_people = [f for f in all_files if f.endswith('.jpg')]
            print(f"[clothes_list] Found {len(all_people)} JPG files out of {len(all_files)} total files")
            
            total = len(all_people)
            start = (page - 1) * page_size
            end = start + page_size
            page_people = all_people[start:end]
            print(f"[clothes_list] Returning {len(page_people)} people for page {page}")
            return {"clothes": page_people, "total": total, "page": page, "page_size": page_size}
        else:
            clothes = get_clothes(session_id)
            total = len(clothes)
            start = (page - 1) * page_size
            end = start + page_size
            page_clothes = clothes[start:end]
            return {"clothes": page_clothes, "total": total, "page": page, "page_size": page_size}
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        print(f"[clothes_list] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error loading clothes: {str(e)}")

@app.get("/search_clothes")
def search_clothes(
    query: str = Query("", min_length=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    category: str = Query(None),
    color: str = Query(None),
    company: str = Query(None),
    priceMax: int = Query(None)
):
    semantic_parts = []
    if company and company.strip(): semantic_parts.append(company.strip())
    if color and color.strip(): semantic_parts.append(color.strip())
    if category and category.strip(): semantic_parts.append(category.strip())
    
    use_query = query.strip() if query and query.strip() != "all" else ""
    if use_query:
        semantic_parts.append(use_query)
        
    final_query_text = " ".join(semantic_parts) if semantic_parts else "all"

    print(f"[SEARCH] Final Semantic Query: '{final_query_text}', Page: {page}, Page Size: {page_size}")
    
    try:
        if index is None:
            return _fallback_search(use_query, page, page_size, category=category, color=color, company=company, price_max=priceMax)
        print("[INFO] Using Pinecone semantic search with dynamic labeling")
        return _pinecone_search(final_query_text, page, page_size, category=category, color=color, company=company, price_max=priceMax)
        
    except Exception as e:
        print(f"[ERROR] Search error: {e}")
        raise

def _fallback_search(query: str, page: int, page_size: int, category: str = None, color: str = None, company: str = None, price_max: int = None):
    """Fallback search when Pinecone is not available"""
    try:
        clothes_dir = CLOTHES_DIR
        print(f"[SEARCH] Searching in directory: {clothes_dir}")
        print(f"[SEARCH] Directory exists: {os.path.exists(clothes_dir)}")
        
        if not os.path.exists(clothes_dir):
            print(f"[ERROR] Directory does not exist: {clothes_dir}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "search_type": "fallback",
                "error": "Directory not found"
            }
        
        all_files = os.listdir(clothes_dir)
        print(f"[SEARCH] All files in directory: {len(all_files)} files")
        print(f"[SEARCH] First 5 files: {all_files[:5]}")
        
        all_clothes = [f for f in all_files if f.endswith('.jpg')]
        print(f"[SEARCH] JPG files found: {len(all_clothes)}")
        print(f"[SEARCH] First 5 JPG files: {all_clothes[:5]}")
        
        filtered_clothes = [
            f for f in all_clothes
            if _matches_filters(
                f,
                query=query,
                category=category,
                color=color,
                company=company,
                price_max=price_max
            )
        ]

        print(
            f"[SEARCH] Filtered results for query='{query}', category='{category}', color='{color}', "
            f"company='{company}', priceMax='{price_max}': {len(filtered_clothes)} files"
        )
        
        total = len(filtered_clothes)
        start = (page - 1) * page_size
        end = start + page_size
        page_clothes = filtered_clothes[start:end]
        
        print(f"[INFO] Fallback search found {total} items, returning {len(page_clothes)} for page {page}")
        
        return {
            # Same shape as the Pinecone search, which is what the shop reads.
            "items": [{"id": f, "score": None, "metadata": _metadata_for_cloth(f)} for f in page_clothes],
            "total": total,
            "page": page,
            "page_size": page_size,
            "search_type": "fallback"
        }
    except Exception as e:
        print(f"[ERROR] Fallback search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Fallback search error: {str(e)}")

def _pinecone_search(query: str, page: int, page_size: int, category: str = None, color: str = None, company: str = None, price_max: int = None):
    """Semantic search using Pinecone with optional metadata filters"""
    try:
        inputs = processor(text=[query], return_tensors="pt").to(device)
        with torch.no_grad():
            text_embed = model.get_text_features(**inputs)
            text_embed = torch.nn.functional.normalize(text_embed, p=2, dim=-1)
        vector = text_embed.squeeze().cpu().tolist()

        top_k = 200 
        
        # User requested pure visual inference: ignore fixed DB constraints and rely purely on the generated semantic vector
        results = index.query(vector=vector, top_k=top_k, include_metadata=True)
        matches = results["matches"]
        paged_matches = matches[(page-1)*page_size:page*page_size]

        print(f"[SEARCH] Pinecone semantic search found {len(matches)} items, returning {len(paged_matches)} for page {page}")

        return {
            "items": [
                {
                    "id": m["id"],
                    "score": m.get("score"),
                    "metadata": {
                        **m.get("metadata", {}),
                        **({"brand": company} if company else {}),
                        **({"company": company} if company else {}),
                        **({"category": category} if category else {}),
                        **({"color": color} if color else {})
                    }
                } for m in paged_matches
            ],
            "total": len(matches),
            "page": page,
            "page_size": page_size,
            "search_type": "pinecone"
        }
    except Exception as e:
        print(f"[ERROR] Pinecone search error: {e}")
        raise HTTPException(status_code=500, detail=f"Pinecone search error: {str(e)}")

@app.post("/pick")
def pick(req: PickRequest):
    try:
        make_pick(req.session_id, req.round_num, req.player, req.picks)
        return {"message": "Pick received"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rank")
def rank(req: RankRequest):
    try:
        make_ranking(req.session_id, req.round_num, req.player, req.ranking)
        return {"message": "Ranking received"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leaderboard")
def leaderboard(session_id: str = Query(...)):
    try:
        board = get_leaderboard(session_id)
        return {"leaderboard": board}
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") 

@app.get("/detailed_leaderboard")
def detailed_leaderboard(session_id: str = Query(...)):
    try:
        game_state = get_game_state(session_id)
        leaderboard = game_state['leaderboard']
        picks = game_state.get('picks', {})
        rankings = game_state.get('rankings', {})   	
        players = game_state['players']
        num_rounds = game_state['num_rounds']
        
        round_scores = {}
        for round_num in range(1, num_rounds + 1):
            round_scores[round_num] = {player: 0 for player in players}
            
            if round_num in rankings:
                round_rankings = rankings[round_num]
                round_picks = picks.get(round_num, {})
                
                for player, ranking in round_rankings.items():
                    n = len(ranking)
                    for rank, cloth_idx in enumerate(ranking):
                        points = n - rank

                        for other in players:
                            if other != player and other in round_picks and player in round_picks[other]:
                                if round_picks[other][player] == cloth_idx:
                                    round_scores[round_num][other] += points
        
        return {
            "leaderboard": leaderboard,
            "round_scores": round_scores,
            "players": players,
            "num_rounds": num_rounds
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

def _read_upload_image(data: bytes, label: str) -> PILImage.Image:
    try:
        image = PILImage.open(io.BytesIO(data))
        image.load()
        return image
    except Exception:
        raise HTTPException(status_code=400, detail=f"The {label} is not a readable image.")


@app.get("/tryon/status")
def tryon_status():
    return tryon_service.status()


@app.post("/viton_preview_upload")
async def viton_preview_upload(
    person_image: UploadFile = File(...),
    cloth_image: Optional[UploadFile] = File(None),
    cloth: Optional[str] = Form(None),
):
    """Dress an uploaded photo in a garment using DM-VTON. Returns a PNG.

    The garment is either `cloth`, a shop item's filename, in which case the
    dataset's real garment mask is used, or an uploaded `cloth_image`, whose
    mask is estimated. If both are sent, `cloth` wins.
    """
    missing = tryon_service.missing_checkpoints()
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Try-on model weights are missing ({', '.join(missing)}). See 'Model weights' in the README.",
        )

    person = _read_upload_image(await person_image.read(), "person photo")

    mask = None
    if cloth:
        name = os.path.basename(cloth)
        cloth_path = os.path.join(CLOTHES_DIR, name)
        if not os.path.isfile(cloth_path):
            raise HTTPException(status_code=404, detail=f"Garment {name} is not in the dataset.")
        garment = PILImage.open(cloth_path)
        mask_path = os.path.join(CLOTH_MASK_DIR, name)
        if os.path.isfile(mask_path):
            mask = PILImage.open(mask_path)
    elif cloth_image is not None:
        garment = _read_upload_image(await cloth_image.read(), "garment image")
    else:
        raise HTTPException(status_code=400, detail="Send a garment: 'cloth' for a shop item or 'cloth_image' for an upload.")

    try:
        result = await run_in_threadpool(tryon_service.try_on, person, garment, mask)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Try-on failed: {e}")

    buffer = io.BytesIO()
    result.save(buffer, format="PNG")
    return Response(content=buffer.getvalue(), media_type="image/png")

@app.get("/received_clothes")
def received_clothes(session_id: str = Query(...), round_num: int = Query(...), player: str = Query(...)):
    try:
        game_state = get_game_state(session_id)
        picks = game_state.get('picks', {}).get(round_num, {})
        players = game_state['players']
        received_clothes = []
        
        for other_player in players:
            if other_player != player and other_player in picks and player in picks[other_player]:
                cloth_idx = picks[other_player][player]
                received_clothes.append(cloth_idx)
        
        return {
            "received_clothes": received_clothes,
            "original_count": len([p for p in players if p != player]),
            "actual_count": len(received_clothes)
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/available_clothes")
def available_clothes(session_id: str = Query(...), round_num: int = Query(...), target_player: str = Query(...)):
    try:
        available_indices = get_available_clothes_for_player(session_id, round_num, target_player)
        return {
            "available_clothes": available_indices,
            "target_player": target_player,
            "round_num": round_num
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_cloth")
async def generate_cloth(request: Request):
    import random
    try:
        body = await request.json()
        prompt = body.get('prompt', '')
    except Exception:
        prompt = ''
    clothes_dir = CLOTHES_DIR
    all_clothes = [f for f in os.listdir(clothes_dir) if f.endswith('.jpg')]
    if not all_clothes:
        raise HTTPException(status_code=404, detail="No clothes found in dataset.")
    filename = random.choice(all_clothes)
    return {"filename": filename}

@app.get("/recommend")
def recommend(top_k: int = 4):
    import random
    # Enhanced dynamic recommendation - pick a style and brand theme
    themes = [
        {"q": "vintage street style", "brand": "Levi's", "cat": "tshirts"},
        {"q": "modern athletic sportswear", "brand": "Nike", "cat": "hoodies"},
        {"q": "premium executive fashion", "brand": "HUGO", "cat": "shirts"},
        {"q": "casual weekend outfit", "brand": "Champion", "cat": "jackets"},
        {"q": "minimalist summer wear", "brand": "Calvin Klein", "cat": "tshirts"},
        {"q": "classic urban style", "brand": "Adidas", "cat": "hoodies"}
    ]
    theme = random.choice(themes)
    
    try:
        if index is not None:
            # Shift semantic query slightly to avoid repetitive result sets
            results = _pinecone_search(theme['q'], page=1, page_size=top_k)
            items = []
            for m in results.get("items", []):
                # Inject labels into the recommendation stream so AI matches visuals
                meta = {
                    **m.get("metadata", {}),
                    "brand": theme['brand'],
                    "company": theme['brand'],
                    "category": theme['cat']
                }
                items.append({"id": m["id"], "metadata": meta})
            return {"images": items}
        else:
            clothes_dir = CLOTHES_DIR
            all_clothes = [f for f in os.listdir(clothes_dir) if f.endswith('.jpg')]
            random.shuffle(all_clothes)
            return {"images": [{"id": img, "metadata": {}} for img in all_clothes[:top_k]]}
    except Exception as e:
        print(f"[RECO] error: {e}")
        return {"images": []}

@app.get("/api/ping")
def ping():
    return {"message": "pong"}

@app.get("/debug/directories")
def debug_directories():
    """Debug endpoint to check directory access"""
    try:
        clothes_exists = os.path.exists(CLOTHES_DIR)
        people_exists = os.path.exists(PEOPLE_DIR)
        
        clothes_count = 0
        people_count = 0
        
        if clothes_exists:
            all_files = os.listdir(CLOTHES_DIR)
            clothes_count = len([f for f in all_files if f.endswith('.jpg')])
        
        if people_exists:
            all_files = os.listdir(PEOPLE_DIR)
            people_count = len([f for f in all_files if f.endswith('.jpg')])
        
        return {
            "clothes_dir": CLOTHES_DIR,
            "people_dir": PEOPLE_DIR,
            "clothes_exists": clothes_exists,
            "people_exists": people_exists,
            "clothes_count": clothes_count,
            "people_count": people_count,
            "sample_clothes": os.listdir(CLOTHES_DIR)[:5] if clothes_exists else [],
            "sample_people": os.listdir(PEOPLE_DIR)[:5] if people_exists else []
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/dataset")
def debug_dataset():
    """Dataset folders and try-on model status, for checking a fresh setup."""
    def describe(path):
        exists = os.path.isdir(path)
        return {"path": path, "exists": exists, "file_count": len(os.listdir(path)) if exists else 0}

    return {
        "status": "success",
        "dataset_root": str(DATASET_ROOT),
        "dataset": {
            "CLOTHES_DIR": describe(CLOTHES_DIR),
            "PEOPLE_DIR": describe(PEOPLE_DIR),
            "CLOTH_MASK_DIR": describe(CLOTH_MASK_DIR),
        },
        "tryon": tryon_service.status(),
        "pinecone": index is not None,
    }

@app.get("/debug/test_images")
def test_images():
    """Test if images can be served correctly"""
    try:
        print("=== TEST IMAGE SERVING ===")
        
        # Test person images
        person_files = [f for f in os.listdir(PEOPLE_DIR) if f.endswith('.jpg')][:3]
        cloth_files = [f for f in os.listdir(CLOTHES_DIR) if f.endswith('.jpg')][:3]
        
        person_urls = [f"/people/{f}" for f in person_files]
        cloth_urls = [f"/clothes/{f}" for f in cloth_files]
        
        return {
            "status": "success",
            "person_files": person_files,
            "cloth_files": cloth_files,
            "person_urls": person_urls,
            "cloth_urls": cloth_urls,
            "message": "Test image URLs generated - try accessing them directly"
        }
        
    except Exception as e:
        print(f"Test images error: {e}")
        return {"status": "error", "message": str(e)}
