from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(__file__))
from game_logic import (
    init_game, get_clothes, make_pick, make_ranking, get_leaderboard, get_game_state
)
import base64
import io
from transformers import AutoProcessor, CLIPModel
import torch
import pinecone
from dotenv import load_dotenv

load_dotenv()
from viton_backend import run_viton_hd, VitonHDOptions
import shutil
from PIL import Image as PILImage
import io
from fastapi.responses import StreamingResponse
from starlette.staticfiles import StaticFiles as StarletteStaticFiles
import glob
from starlette.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set PROJECT_ROOT to the parent of ezyZip (i.e., 12_clothes_tryon)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CLOTHES_DIR = os.path.join(PROJECT_ROOT, 'clothes_tryon_dataset', 'train', 'cloth')
PEOPLE_DIR = os.path.join(PROJECT_ROOT, 'clothes_tryon_dataset', 'train', 'image')
CLOTH_MASK_DIR = os.path.join(PROJECT_ROOT, 'clothes_tryon_dataset', 'train', 'cloth-mask')
OPENPOSE_JSON_DIR = os.path.join(PROJECT_ROOT, 'clothes_tryon_dataset', 'train', 'openpose_json')
OPENPOSE_IMG_DIR = os.path.join(PROJECT_ROOT, 'clothes_tryon_dataset', 'train', 'openpose_img')
IMAGE_PARSE_DIR = os.path.join(PROJECT_ROOT, 'clothes_tryon_dataset', 'train', 'image-parse-v3')

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
        print(f"[StaticFiles] get_response called for path: {path}, scope: {scope}")
        response = await super().get_response(path, scope)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = '*'
        response.headers['Access-Control-Allow-Headers'] = '*'
        print(f"[StaticFiles] After super().get_response: path={path}, status={response.status_code}, headers={dict(response.headers)}")
        if response.status_code == 404:
            # Print directory listing for debugging
            try:
                if 'clothes' in self.directory:
                    files = os.listdir(self.directory)
                    print(f"[StaticFiles] CLOTHES_DIR contents: {files}")
                elif 'image' in self.directory:
                    files = os.listdir(self.directory)
                    print(f"[StaticFiles] PEOPLE_DIR contents: {files}")
            except Exception as e:
                print(f"[StaticFiles] Could not list directory: {e}")
        return response

app.mount("/clothes", CORSMiddlewareStaticFiles(directory=CLOTHES_DIR), name="clothes")
app.mount("/people", CORSMiddlewareStaticFiles(directory=PEOPLE_DIR), name="people")

clip_model_name = "patrickjohncyh/fashion-clip"
processor = AutoProcessor.from_pretrained(clip_model_name)
model = CLIPModel.from_pretrained(clip_model_name)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

import os
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")  
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "aped-4627-b74a")  # Default to the value in test_pinecone_connection.py

# Initialize Pinecone with improved error handling
index = None
try:
    if PINECONE_API_KEY and PINECONE_API_KEY != "YOUR_API_KEY":
        print(f"Attempting to initialize Pinecone with environment: {PINECONE_ENVIRONMENT}")
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
        
        # List available indexes
        indexes = pinecone.list_indexes()
        print(f"Available Pinecone indexes: {indexes}")
        
        if "fashion-clip-index" in indexes:
            index = pinecone.Index("fashion-clip-index")
            print(f"✅ Pinecone initialized successfully in environment '{PINECONE_ENVIRONMENT}' with index 'fashion-clip-index'.")
        else:
            print(f"❌ Index 'fashion-clip-index' NOT found in environment '{PINECONE_ENVIRONMENT}'.")
            print(f"Available indexes: {indexes}")
            print("Pinecone features will be disabled - using fallback search")
            index = None
    else:
        print("❌ PINECONE_API_KEY not found or not properly set")
        print("Pinecone features will be disabled - using fallback search")
        index = None
except Exception as e:
    print(f"❌ Failed to initialize Pinecone: {e}")
    print("Pinecone features will be disabled - using fallback search")
    index = None

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
                print(f"[clothes_list] ❌ Directory does not exist: {clothes_dir}")
                return {"clothes": [], "total": 0, "page": page, "page_size": page_size}
            
            all_files = os.listdir(clothes_dir)
            all_clothes = [f for f in all_files if f.endswith('.jpg')]
            print(f"[clothes_list] Found {len(all_clothes)} JPG files out of {len(all_files)} total files")
            
            # Filtering logic placeholder (no metadata available)
            # If you add metadata, filter here
            total = len(all_clothes)
            start = (page - 1) * page_size
            end = start + page_size
            page_clothes = all_clothes[start:end]
            print(f"[clothes_list] Returning {len(page_clothes)} items for page {page}")
            return {"clothes": page_clothes, "total": total, "page": page, "page_size": page_size}
        elif session_id == "people":
            people_dir = PEOPLE_DIR
            print(f"[clothes_list] Loading people from: {people_dir}")
            print(f"[clothes_list] Directory exists: {os.path.exists(people_dir)}")
            
            if not os.path.exists(people_dir):
                print(f"[clothes_list] ❌ Directory does not exist: {people_dir}")
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
    page_size: int = Query(25, ge=1, le=100)
):
    print(f"🔍 Search request - Query: '{query}', Page: {page}, Page Size: {page_size}")
    
    try:
        # Check if Pinecone is available
        if index is None:
            print("📝 Using fallback search (Pinecone not available)")
            return _fallback_search(query, page, page_size)
        
        # Use Pinecone for semantic search
        print("🔍 Using Pinecone semantic search")
        return _pinecone_search(query, page, page_size)
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        print("🔄 Falling back to basic search due to error")
        return _fallback_search(query, page, page_size)

def _fallback_search(query: str, page: int, page_size: int):
    """Fallback search when Pinecone is not available"""
    try:
        clothes_dir = CLOTHES_DIR
        print(f"🔍 Searching in directory: {clothes_dir}")
        print(f"🔍 Directory exists: {os.path.exists(clothes_dir)}")
        
        if not os.path.exists(clothes_dir):
            print(f"❌ Directory does not exist: {clothes_dir}")
            return {
                "clothes": [],
                "scores": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "search_type": "fallback",
                "error": "Directory not found"
            }
        
        all_files = os.listdir(clothes_dir)
        print(f"🔍 All files in directory: {len(all_files)} files")
        print(f"🔍 First 5 files: {all_files[:5]}")
        
        all_clothes = [f for f in all_files if f.endswith('.jpg')]
        print(f"🔍 JPG files found: {len(all_clothes)}")
        print(f"🔍 First 5 JPG files: {all_clothes[:5]}")
        
        # Simple text-based filtering
        if query.strip() and query.lower() != 'all':
            filtered_clothes = [f for f in all_clothes if query.lower() in f.lower()]
            print(f"🔍 After filtering for '{query}': {len(filtered_clothes)} files")
        else:
            filtered_clothes = all_clothes
            print(f"🔍 No query filter applied or query is 'all', using all {len(filtered_clothes)} files")
        
        total = len(filtered_clothes)
        start = (page - 1) * page_size
        end = start + page_size
        page_clothes = filtered_clothes[start:end]
        
        print(f"📝 Fallback search found {total} items, returning {len(page_clothes)} for page {page}")
        
        return {
            "clothes": page_clothes,
            "scores": [1.0] * len(page_clothes),  # Default scores
            "total": total,
            "page": page,
            "page_size": page_size,
            "search_type": "fallback"
        }
    except Exception as e:
        print(f"❌ Fallback search error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Fallback search error: {str(e)}")

def _pinecone_search(query: str, page: int, page_size: int):
    """Semantic search using Pinecone"""
    try:
        inputs = processor(text=[query], return_tensors="pt").to(device)
        with torch.no_grad():
            text_embed = model.get_text_features(**inputs)
            text_embed = torch.nn.functional.normalize(text_embed, p=2, dim=-1)
        vector = text_embed.squeeze().cpu().tolist()

        top_k = 100 
        results = index.query(vector=vector, top_k=top_k, include_metadata=True)
        matches = results["matches"]
        paged_matches = matches[(page-1)*page_size:page*page_size]

        print(f"🔍 Pinecone search found {len(matches)} items, returning {len(paged_matches)} for page {page}")

        return {
            "clothes": [m["id"] for m in paged_matches],
            "scores": [m["score"] for m in paged_matches],
            "total": len(matches),
            "page": page,
            "page_size": page_size,
            "search_type": "pinecone"
        }
    except Exception as e:
        print(f"❌ Pinecone search error: {e}")
        print("🔄 Falling back to basic search due to Pinecone error")
        return _fallback_search(query, page, page_size)

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

@app.post("/viton_preview_upload")
async def viton_preview_upload(
    person_image: UploadFile = File(...),
    cloth_image: UploadFile = File(...)
):
    import tempfile
    try:
        print(f"=== VITON Upload Debug ===")
        print(f"Person image filename: {person_image.filename}")
        print(f"Cloth image filename: {cloth_image.filename}")
        print(f"Person image size: {person_image.size if hasattr(person_image, 'size') else 'Unknown'}")
        print(f"Cloth image size: {cloth_image.size if hasattr(cloth_image, 'size') else 'Unknown'}")
        
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        src_root = os.path.join(PROJECT_ROOT, 'clothes_tryon_dataset', 'train')
        dest_root = os.path.join(backend_dir, 'VITON-HD/datasets/single_test')
        
        print(f"Backend dir: {backend_dir}")
        print(f"Source root: {src_root}")
        print(f"Destination root: {dest_root}")
        
        # Get cloth filename from uploaded file
        cloth_filename = cloth_image.filename
        if not cloth_filename:
            cloth_filename = next(tempfile._get_candidate_names()) + '.jpg'
        
        print(f"Using cloth filename: {cloth_filename}")
        
        # Generate a unique person filename
        person_filename = next(tempfile._get_candidate_names()) + '.jpg'
        
        # Use the proven method from viton_test_single.py
        def prepare_single_viton_dataset(person, cloth, src_root, dest_root, person_image_path=None):
            test_dir = os.path.join(dest_root, 'test')
            os.makedirs(test_dir, exist_ok=True)
            subdirs = ['image', 'cloth', 'cloth-mask', 'openpose-json', 'openpose-img', 'image-parse']
            for sub in subdirs:
                os.makedirs(os.path.join(test_dir, sub), exist_ok=True)

            print(f"Preparing dataset with person: {person}, cloth: {cloth}")
            
            # Save uploaded person image (this will replace the dataset person image)
            person_path = os.path.join(test_dir, 'image', person)
            if person_image_path is not None:
                # Verify the source image exists and is valid
                if not os.path.exists(person_image_path):
                    raise Exception(f"Source person image not found: {person_image_path}")
                
                # Copy the image and verify it was copied successfully
                shutil.copy(person_image_path, person_path)
                if not os.path.exists(person_path):
                    raise Exception(f"Failed to copy person image to: {person_path}")
                
                # Verify the copied image is valid
                try:
                    from PIL import Image
                    with Image.open(person_path) as img:
                        img.verify()
                    print(f"Copied and verified uploaded person image to: {person_path}")
                except Exception as e:
                    print(f"Warning: Copied image verification failed: {e}")
                    # Try to re-save the image properly
                    try:
                        with Image.open(person_image_path) as img:
                            img.save(person_path, 'JPEG')
                        print(f"Re-saved person image: {person_path}")
                    except Exception as e2:
                        raise Exception(f"Failed to save valid person image: {e2}")
            else:
                # This should not happen since we always provide person_image_path
                raise Exception("person_image_path must be provided")
            
            # Copy cloth image from dataset (since we have the filename)
            cloth_src = os.path.join(src_root, 'cloth', cloth)
            cloth_dest = os.path.join(test_dir, 'cloth', cloth)
            shutil.copy(cloth_src, cloth_dest)
            print(f"Copied cloth image from {cloth_src} to {cloth_dest}")
            
            # Copy cloth mask
            cloth_mask_src = os.path.join(src_root, 'cloth-mask', cloth)
            cloth_mask_dest = os.path.join(test_dir, 'cloth-mask', cloth)
            shutil.copy(cloth_mask_src, cloth_mask_dest)
            print(f"Copied cloth mask from {cloth_mask_src} to {cloth_mask_dest}")
            
            # Copy openpose keypoints (json)
            pose_json = person.replace('.jpg', '_keypoints.json')
            pose_json_src = os.path.join(src_root, 'openpose_json', pose_json)
            pose_json_dest = os.path.join(test_dir, 'openpose-json', pose_json)
            shutil.copy(pose_json_src, pose_json_dest)
            print(f"Copied pose JSON from {pose_json_src} to {pose_json_dest}")
            
            # Copy openpose rendered image (png)
            pose_img = person.replace('.jpg', '_rendered.png')
            pose_img_src = os.path.join(src_root, 'openpose_img', pose_img)
            pose_img_dest = os.path.join(test_dir, 'openpose-img', pose_img)
            shutil.copy(pose_img_src, pose_img_dest)
            print(f"Copied pose image from {pose_img_src} to {pose_img_dest}")
            
            # Copy parsing image (png)
            parse_img = person.replace('.jpg', '.png')
            parse_img_src = os.path.join(src_root, 'image-parse-v3', parse_img)
            parse_img_dest = os.path.join(test_dir, 'image-parse', parse_img)
            shutil.copy(parse_img_src, parse_img_dest)
            print(f"Copied parse image from {parse_img_src} to {parse_img_dest}")
            
            # Write test_pairs.txt in dest_root (not in test/)
            test_pairs_path = os.path.join(dest_root, 'test_pairs.txt')
            with open(test_pairs_path, 'w') as f:
                f.write(f"{person} {cloth}\n")
            print(f"Created test pairs file: {test_pairs_path}")
            print(f"Test pair content: {person} {cloth}")
            
            # Verify all files exist
            required_files = [
                os.path.join(test_dir, 'image', person),
                os.path.join(test_dir, 'cloth', cloth),
                os.path.join(test_dir, 'cloth-mask', cloth),
                os.path.join(test_dir, 'openpose-json', pose_json),
                os.path.join(test_dir, 'openpose-img', pose_img),
                os.path.join(test_dir, 'image-parse', parse_img)
            ]
            
            print("Verifying all required files exist:")
            for file_path in required_files:
                exists = os.path.exists(file_path)
                print(f"  {file_path}: {exists}")
                if not exists:
                    raise Exception(f"Required file not found: {file_path}")
            
            print("All required files verified successfully!")

        # Check if dataset directories exist
        print(f"Checking dataset directories...")
        print(f"CLOTHES_DIR exists: {os.path.exists(CLOTHES_DIR)}")
        print(f"PEOPLE_DIR exists: {os.path.exists(PEOPLE_DIR)}")
        print(f"CLOTH_MASK_DIR exists: {os.path.exists(CLOTH_MASK_DIR)}")
        print(f"OPENPOSE_JSON_DIR exists: {os.path.exists(OPENPOSE_JSON_DIR)}")
        print(f"OPENPOSE_IMG_DIR exists: {os.path.exists(OPENPOSE_IMG_DIR)}")
        print(f"IMAGE_PARSE_DIR exists: {os.path.exists(IMAGE_PARSE_DIR)}")
        
        # Check if cloth file exists in dataset
        cloth_path_in_dataset = os.path.join(CLOTHES_DIR, cloth_filename)
        print(f"Cloth file in dataset: {cloth_path_in_dataset}")
        print(f"Cloth file exists: {os.path.exists(cloth_path_in_dataset)}")
        
        if not os.path.exists(cloth_path_in_dataset):
            available_clothes = os.listdir(CLOTHES_DIR)[:5] if os.path.exists(CLOTHES_DIR) else []
            print(f"Available clothes (first 5): {available_clothes}")
            raise HTTPException(status_code=500, detail=f"Cloth file {cloth_filename} not found in dataset")
        
        # Find a reference person from dataset for pose and parsing data
        person_files = [f for f in os.listdir(PEOPLE_DIR) if f.endswith('.jpg')]
        if not person_files:
            raise HTTPException(status_code=500, detail="No reference person found in dataset")
        
        # Use a person that has all required data (pose, parsing, etc.)
        # Let's use a person that might be more similar to the uploaded image
        # We'll try to find a person with a similar pose/body type
        reference_person = None
        for person in person_files[:20]:  # Check first 20 people
            pose_json = person.replace('.jpg', '_keypoints.json')
            pose_img = person.replace('.jpg', '_rendered.png')
            parse_img = person.replace('.jpg', '.png')
            
            pose_json_path = os.path.join(OPENPOSE_JSON_DIR, pose_json)
            pose_img_path = os.path.join(OPENPOSE_IMG_DIR, pose_img)
            parse_img_path = os.path.join(IMAGE_PARSE_DIR, parse_img)
            
            if (os.path.exists(pose_json_path) and 
                os.path.exists(pose_img_path) and 
                os.path.exists(parse_img_path)):
                reference_person = person
                break
        
        if not reference_person:
            reference_person = person_files[0]  # Fallback to first person
            print(f"Warning: Using fallback reference person: {reference_person}")
        else:
            print(f"Using reference person with complete data: {reference_person}")
        
        # Create a unique person filename for the uploaded image to avoid conflicts
        import time
        unique_person_filename = f"uploaded_{int(time.time())}.jpg"
        print(f"Using unique person filename: {unique_person_filename}")
        
        # Check if reference person files exist
        pose_json = reference_person.replace('.jpg', '_keypoints.json')
        pose_img = reference_person.replace('.jpg', '_rendered.png')
        parse_img = reference_person.replace('.jpg', '.png')
        
        print(f"Checking reference person files...")
        print(f"Pose JSON: {os.path.join(OPENPOSE_JSON_DIR, pose_json)} - Exists: {os.path.exists(os.path.join(OPENPOSE_JSON_DIR, pose_json))}")
        print(f"Pose IMG: {os.path.join(OPENPOSE_IMG_DIR, pose_img)} - Exists: {os.path.exists(os.path.join(OPENPOSE_IMG_DIR, pose_img))}")
        print(f"Parse IMG: {os.path.join(IMAGE_PARSE_DIR, parse_img)} - Exists: {os.path.exists(os.path.join(IMAGE_PARSE_DIR, parse_img))}")
        
        # Save uploaded person image temporarily
        temp_person_path = os.path.join(backend_dir, 'temp_person.jpg')
        person_image_content = await person_image.read()
        with open(temp_person_path, 'wb') as f:
            f.write(person_image_content)
        
        # Verify the saved image is valid
        try:
            from PIL import Image
            with Image.open(temp_person_path) as img:
                img.verify()
            print(f"Uploaded image verified successfully: {temp_person_path}")
        except Exception as e:
            print(f"Warning: Uploaded image verification failed: {e}")
            # Try to re-save the image properly
            try:
                with Image.open(io.BytesIO(person_image_content)) as img:
                    img.save(temp_person_path, 'JPEG')
                print(f"Re-saved uploaded image: {temp_person_path}")
            except Exception as e2:
                print(f"Failed to re-save image: {e2}")
                raise HTTPException(status_code=500, detail="Invalid uploaded image format")
        
        print(f"Saved uploaded person image to: {temp_person_path}")
        
        # Get the uploaded person image filename
        uploaded_person_filename = person_image.filename
        print(f"Uploaded person image filename: {uploaded_person_filename}")
        
        # Get list of available persons in dataset
        person_files = [f for f in os.listdir(PEOPLE_DIR) if f.endswith('.jpg')]
        
        # Check if this person exists in the dataset
        if uploaded_person_filename not in person_files:
            print(f"Warning: Uploaded person {uploaded_person_filename} not found in dataset")
            print(f"Available persons (first 10): {person_files[:10]}")
            # Try to find a similar person or use the first available one
            matching_person = person_files[0] if person_files else None
        else:
            matching_person = uploaded_person_filename
            print(f"Found exact match for uploaded person: {matching_person}")
        
        if not matching_person:
            raise HTTPException(status_code=500, detail="No matching person found in dataset")
        
        print(f"Using person: {matching_person}")
        
        # Verify that this person has all required data
        pose_json = matching_person.replace('.jpg', '_keypoints.json')
        pose_img = matching_person.replace('.jpg', '_rendered.png')
        parse_img = matching_person.replace('.jpg', '.png')
        
        pose_json_path = os.path.join(OPENPOSE_JSON_DIR, pose_json)
        pose_img_path = os.path.join(OPENPOSE_IMG_DIR, pose_img)
        parse_img_path = os.path.join(IMAGE_PARSE_DIR, parse_img)
        
        print(f"Checking required data for {matching_person}:")
        print(f"  Pose JSON: {pose_json_path} - Exists: {os.path.exists(pose_json_path)}")
        print(f"  Pose IMG: {pose_img_path} - Exists: {os.path.exists(pose_img_path)}")
        print(f"  Parse IMG: {parse_img_path} - Exists: {os.path.exists(parse_img_path)}")
        
        if not all([os.path.exists(pose_json_path), os.path.exists(pose_img_path), os.path.exists(parse_img_path)]):
            print(f"Warning: {matching_person} missing some required data, trying to find alternative...")
            # Find another person with complete data
            for person in person_files[:20]:
                pose_json = person.replace('.jpg', '_keypoints.json')
                pose_img = person.replace('.jpg', '_rendered.png')
                parse_img = person.replace('.jpg', '.png')
                
                pose_json_path = os.path.join(OPENPOSE_JSON_DIR, pose_json)
                pose_img_path = os.path.join(OPENPOSE_IMG_DIR, pose_img)
                parse_img_path = os.path.join(IMAGE_PARSE_DIR, parse_img)
                
                if all([os.path.exists(pose_json_path), os.path.exists(pose_img_path), os.path.exists(parse_img_path)]):
                    matching_person = person
                    print(f"Using alternative person with complete data: {matching_person}")
                    break
        
        # Check if cloth mask exists
        cloth_mask_path = os.path.join(CLOTH_MASK_DIR, cloth_filename)
        print(f"Cloth mask path: {cloth_mask_path}")
        print(f"Cloth mask exists: {os.path.exists(cloth_mask_path)}")
        
        if not os.path.exists(cloth_mask_path):
            raise HTTPException(status_code=500, detail=f"Cloth mask {cloth_filename} not found in dataset")
        
        # Prepare dataset using the matching person from dataset
        # Use the matching_person filename for the dataset structure, but save the uploaded image
        prepare_single_viton_dataset(matching_person, cloth_filename, src_root, dest_root, person_image_path=temp_person_path)
        
        print(f"Test pair: {matching_person} {cloth_filename}")

        # Run VITON-HD using the same method as viton_test_single.py
        print(f"Setting up VITON-HD options...")
        opt = VitonHDOptions(
            name="single_test",
            dataset_dir=dest_root + '/',
            checkpoint_dir=os.path.join(backend_dir, 'VITON-HD/checkpoints/'),
            save_dir=os.path.join(backend_dir, 'VITON-HD/results/'),
            load_height=1024,
            load_width=768,
            batch_size=1,
            workers=1
        )
        
        print(f"VITON-HD options:")
        print(f"  - Dataset dir: {opt.dataset_dir}")
        print(f"  - Checkpoint dir: {opt.checkpoint_dir}")
        print(f"  - Save dir: {opt.save_dir}")
        
        # Check if checkpoints exist
        checkpoint_files = [
            os.path.join(opt.checkpoint_dir, "seg_final.pth"),
            os.path.join(opt.checkpoint_dir, "gmm_final.pth"),
            os.path.join(opt.checkpoint_dir, "alias_final.pth")
        ]
        
        print(f"Checking checkpoint files...")
        for checkpoint in checkpoint_files:
            print(f"  - {checkpoint}: {os.path.exists(checkpoint)}")
        
        print(f"Running VITON-HD...")
        result_files = run_viton_hd(opt)
        print(f"VITON-HD completed. Result files: {result_files}")
        
        if not result_files:
            raise HTTPException(status_code=500, detail="VITON-HD did not generate any result.")
        
        # The result_files list contains paths with .jpg extension
        result_path = result_files[0]
        print(f"Expected result path: {result_path}")
        
        # Check if the file exists with .jpg extension
        if not os.path.exists(result_path):
            # Try without .jpg extension (VITON-HD sometimes saves without extension)
            result_path_no_ext = result_path.replace('.jpg', '')
            print(f"Trying without extension: {result_path_no_ext}")
            if os.path.exists(result_path_no_ext):
                result_path = result_path_no_ext
                print(f"Found result file without extension: {result_path}")
            else:
                # Check the directory for any files with similar names
                result_dir = os.path.dirname(result_path)
                base_name = os.path.splitext(os.path.basename(result_path))[0]
                print(f"Looking for files with base name: {base_name}")
                if os.path.exists(result_dir):
                    files_in_dir = os.listdir(result_dir)
                    print(f"Files in result directory: {files_in_dir}")
                    for file in files_in_dir:
                        if base_name in file:
                            print(f"Found potential result file: {file}")
                            result_path = os.path.join(result_dir, file)
                            break
                
                if not os.path.exists(result_path):
                    raise HTTPException(status_code=500, detail="Result image not found.")
        
        print(f"Final result path: {result_path}")
        print(f"Result file exists: {os.path.exists(result_path)}")
        
        print(f"VITON result generated: {result_path}")
        
        # Clean up temporary file
        if os.path.exists(temp_person_path):
            os.remove(temp_person_path)
            print(f"Cleaned up temporary file: {temp_person_path}")
        
        print(f"=== VITON Upload Debug Complete ===")
        return StreamingResponse(open(result_path, 'rb'), media_type="image/jpeg")
    except Exception as e:
        print(f"VITON preview upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create VITON preview: {str(e)}")

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
        from game_logic import get_available_clothes_for_player
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
    import os
    clothes_dir = CLOTHES_DIR
    all_clothes = [f for f in os.listdir(clothes_dir) if f.endswith('.jpg')]
    top_images = all_clothes[:top_k]
    # Return as full URLs for frontend display
    image_urls = [f"/clothes/{img}" for img in top_images]
    return {"images": image_urls}

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
    """Debug endpoint to check dataset structure"""
    try:
        print("=== DATASET DEBUG ===")
        
        # Check all dataset paths
        dataset_info = {
            "CLOTHES_DIR": {
                "path": CLOTHES_DIR,
                "exists": os.path.exists(CLOTHES_DIR),
                "file_count": len(os.listdir(CLOTHES_DIR)) if os.path.exists(CLOTHES_DIR) else 0,
                "sample_files": os.listdir(CLOTHES_DIR)[:5] if os.path.exists(CLOTHES_DIR) else []
            },
            "PEOPLE_DIR": {
                "path": PEOPLE_DIR,
                "exists": os.path.exists(PEOPLE_DIR),
                "file_count": len(os.listdir(PEOPLE_DIR)) if os.path.exists(PEOPLE_DIR) else 0,
                "sample_files": os.listdir(PEOPLE_DIR)[:5] if os.path.exists(PEOPLE_DIR) else []
            },
            "CLOTH_MASK_DIR": {
                "path": CLOTH_MASK_DIR,
                "exists": os.path.exists(CLOTH_MASK_DIR),
                "file_count": len(os.listdir(CLOTH_MASK_DIR)) if os.path.exists(CLOTH_MASK_DIR) else 0
            },
            "OPENPOSE_JSON_DIR": {
                "path": OPENPOSE_JSON_DIR,
                "exists": os.path.exists(OPENPOSE_JSON_DIR),
                "file_count": len(os.listdir(OPENPOSE_JSON_DIR)) if os.path.exists(OPENPOSE_JSON_DIR) else 0
            },
            "OPENPOSE_IMG_DIR": {
                "path": OPENPOSE_IMG_DIR,
                "exists": os.path.exists(OPENPOSE_IMG_DIR),
                "file_count": len(os.listdir(OPENPOSE_IMG_DIR)) if os.path.exists(OPENPOSE_IMG_DIR) else 0
            },
            "IMAGE_PARSE_DIR": {
                "path": IMAGE_PARSE_DIR,
                "exists": os.path.exists(IMAGE_PARSE_DIR),
                "file_count": len(os.listdir(IMAGE_PARSE_DIR)) if os.path.exists(IMAGE_PARSE_DIR) else 0
            }
        }
        
        # Check VITON setup
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        viton_dir = os.path.join(backend_dir, 'VITON-HD')
        checkpoints_dir = os.path.join(viton_dir, 'checkpoints')
        
        viton_info = {
            "viton_dir": {
                "path": viton_dir,
                "exists": os.path.exists(viton_dir)
            },
            "checkpoints": {
                "seg_final.pth": os.path.exists(os.path.join(checkpoints_dir, "seg_final.pth")),
                "gmm_final.pth": os.path.exists(os.path.join(checkpoints_dir, "gmm_final.pth")),
                "alias_final.pth": os.path.exists(os.path.join(checkpoints_dir, "alias_final.pth"))
            }
        }
        
        print("Dataset Info:", dataset_info)
        print("VITON Info:", viton_info)
        
        return {
            "status": "success",
            "dataset": dataset_info,
            "viton": viton_info
        }
    except Exception as e:
        print(f"Debug dataset error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/debug_upload")
async def debug_upload(
    person_image: UploadFile = File(...),
    cloth_image: UploadFile = File(...)
):
    """Debug endpoint to check if files are being uploaded correctly"""
    try:
        print(f"=== DEBUG UPLOAD ===")
        print(f"Person image: {person_image.filename}, size: {person_image.size if hasattr(person_image, 'size') else 'Unknown'}")
        print(f"Cloth image: {cloth_image.filename}, size: {cloth_image.size if hasattr(cloth_image, 'size') else 'Unknown'}")
        
        # Check if cloth file exists in dataset
        cloth_filename = cloth_image.filename
        cloth_path_in_dataset = os.path.join(CLOTHES_DIR, cloth_filename)
        
        return {
            "status": "success",
            "person_image": {
                "filename": person_image.filename,
                "size": person_image.size if hasattr(person_image, 'size') else 'Unknown'
            },
            "cloth_image": {
                "filename": cloth_image.filename,
                "size": cloth_image.size if hasattr(cloth_image, 'size') else 'Unknown'
            },
            "cloth_in_dataset": {
                "path": cloth_path_in_dataset,
                "exists": os.path.exists(cloth_path_in_dataset)
            },
            "dataset_info": {
                "clothes_dir": CLOTHES_DIR,
                "clothes_dir_exists": os.path.exists(CLOTHES_DIR),
                "available_clothes": len(os.listdir(CLOTHES_DIR)) if os.path.exists(CLOTHES_DIR) else 0
            }
        }
    except Exception as e:
        print(f"Debug upload error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/debug/test_viton")
def test_viton():
    """Test VITON processing with sample files"""
    try:
        print("=== TEST VITON PROCESSING ===")
        
        # Check if we have sample files
        if not os.path.exists(CLOTHES_DIR) or not os.path.exists(PEOPLE_DIR):
            return {"status": "error", "message": "Dataset directories not found"}
        
        # Get sample files
        cloth_files = [f for f in os.listdir(CLOTHES_DIR) if f.endswith('.jpg')]
        person_files = [f for f in os.listdir(PEOPLE_DIR) if f.endswith('.jpg')]
        
        if not cloth_files or not person_files:
            return {"status": "error", "message": "No sample files found in dataset"}
        
        sample_cloth = cloth_files[0]
        sample_person = person_files[0]
        
        print(f"Sample cloth: {sample_cloth}")
        print(f"Sample person: {sample_person}")
        
        # Check if corresponding files exist
        pose_json = sample_person.replace('.jpg', '_keypoints.json')
        pose_img = sample_person.replace('.jpg', '_rendered.png')
        parse_img = sample_person.replace('.jpg', '.png')
        
        files_exist = {
            "cloth": os.path.exists(os.path.join(CLOTHES_DIR, sample_cloth)),
            "cloth_mask": os.path.exists(os.path.join(CLOTH_MASK_DIR, sample_cloth)),
            "person": os.path.exists(os.path.join(PEOPLE_DIR, sample_person)),
            "pose_json": os.path.exists(os.path.join(OPENPOSE_JSON_DIR, pose_json)),
            "pose_img": os.path.exists(os.path.join(OPENPOSE_IMG_DIR, pose_img)),
            "parse_img": os.path.exists(os.path.join(IMAGE_PARSE_DIR, parse_img))
        }
        
        print("Files exist:", files_exist)
        
        return {
            "status": "success",
            "sample_files": {
                "cloth": sample_cloth,
                "person": sample_person
            },
            "files_exist": files_exist,
            "message": "VITON test completed - check console for details"
        }
        
    except Exception as e:
        print(f"Test VITON error: {e}")
        return {"status": "error", "message": str(e)}

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


@app.get("/people/{filename}")
async def get_person_image(filename: str):
    """Serve person images from the dataset"""
    person_path = os.path.join(PEOPLE_DIR, filename)
    print(f"Requesting person image: {filename}")
    print(f"Full path: {person_path}")
    print(f"File exists: {os.path.exists(person_path)}")
    
    if not os.path.exists(person_path):
        # List available files for debugging
        try:
            available_files = os.listdir(PEOPLE_DIR)[:10]
            print(f"Available files in PEOPLE_DIR: {available_files}")
        except Exception as e:
            print(f"Could not list PEOPLE_DIR: {e}")
        raise HTTPException(status_code=404, detail=f"Person image not found: {filename}")
    
    return FileResponse(person_path, media_type="image/jpeg")

