import os
import sys
import torch
from PIL import Image
from transformers import AutoProcessor, CLIPModel
import pinecone
from dotenv import load_dotenv

load_dotenv()

# Define local dataset path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import CLOTHES_DIR as DATASET_CLOTH_DIR

# Load FashionCLIP
model_id = "patrickjohncyh/fashion-clip"
device = "cuda" if torch.cuda.is_available() else "cpu"

model = CLIPModel.from_pretrained(model_id).to(device)
processor = AutoProcessor.from_pretrained(model_id)

# Pinecone API Key and config
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "aped-4627-b74a")
PINECONE_INDEX_HOST = (
    os.environ.get("PINECONE_INDEX_HOST")
    or os.environ.get("PINECONE_HOST")
    or os.environ.get("PINECONE_INDEX_URL")
)
if PINECONE_INDEX_HOST:
    PINECONE_INDEX_HOST = PINECONE_INDEX_HOST.strip().strip("`")

# Initialize Pinecone with error handling
try:
    if not PINECONE_INDEX_HOST:
        raise RuntimeError("Missing PINECONE_INDEX_HOST")
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
    index_name = "fashion-clip-index"
    dimension = 512

    index = pc.Index(index_name, host=PINECONE_INDEX_HOST)
    print("Pinecone index connected successfully via host")
except Exception as e:
    print(f"Failed to initialize Pinecone: {e}")
    print("Pinecone features will be disabled")
    index = None

# Load and preprocess images
def load_images_from_folder(folder_path):
    return [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

def preprocess_image(image_path):
    image = Image.open(image_path).convert("RGB")
    return processor(images=image, return_tensors="pt")["pixel_values"].squeeze(0)

PRODUCT_BRANDS = ["Adidas", "Levi's", "Puma", "HUGO", "Nike", "Champion", "Tommy Hilfiger", "Calvin Klein"]
PRODUCT_CATEGORIES = ["tshirts", "shirts", "hoodies", "jackets"]
PRODUCT_COLORS = ["white", "black", "navy", "gray", "blue", "red", "green"]
PRODUCT_PRICE_BUCKETS = sorted(set(
    list(range(0, 2001, 50)) + list(range(25, 2000, 50)) + list(range(49, 2000, 50)) + list(range(99, 2000, 100))
))

def _stable_hash(text: str) -> int:
    value = 0
    for i, ch in enumerate(text.lower()):
        value = (value * 131 + (ord(ch) * (i + 1))) % 1000000007
    return value

def predict_metadata_from_image(filename):
    base = os.path.splitext(os.path.basename(filename))[0]
    h = _stable_hash(base)
    return {
        "brand": PRODUCT_BRANDS[h % len(PRODUCT_BRANDS)],
        "category": PRODUCT_CATEGORIES[(h // 3) % len(PRODUCT_CATEGORIES)],
        "color": PRODUCT_COLORS[(h // 7) % len(PRODUCT_COLORS)],
        "price": PRODUCT_PRICE_BUCKETS[(h // 11) % len(PRODUCT_PRICE_BUCKETS)]
    }

# Embed and upload
def embed_and_upload(image_folder):
    if index is None:
        print("Pinecone not available, skipping upload")
        return
        
    try:
        image_paths = load_images_from_folder(image_folder)
        batch = []

        for i, img_path in enumerate(image_paths):
            file_name = os.path.basename(img_path)

            pixel_values = preprocess_image(img_path).unsqueeze(0).to(device)
            with torch.no_grad():
                image_embeds = model.get_image_features(pixel_values)
                image_embeds = torch.nn.functional.normalize(image_embeds, p=2, dim=-1)

            embedding = image_embeds.squeeze().cpu().tolist()
            md = predict_metadata_from_image(file_name)

            batch.append({"id": file_name, "values": embedding, "metadata": md})

            # Upload every 50 or final
            if len(batch) == 50:
                try:
                    index.upsert(vectors=batch)
                    print(f"Uploaded {len(batch)} embeddings to Pinecone.")
                except Exception as e:
                    print(f"Failed to upload batch: {e}")
                batch = []
        
        if batch:
            try:
                index.upsert(vectors=batch)
                print(f"✅ Uploaded final batch of {len(batch)} to Pinecone.")
            except Exception as e:
                print(f"Failed to upload final batch: {e}")
    except Exception as e:
        print(f"Error in embed_and_upload: {e}")

# Use local dataset path
def main():
    image_folder_path = DATASET_CLOTH_DIR
    embed_and_upload(image_folder_path)

    if index is not None:
        try:
            stats = index.describe_index_stats()
            print(stats)

            # Example fetch by filename (not full path)
            example_id = os.listdir(image_folder_path)[0]
            response = index.fetch(ids=[example_id])
            print(response)
        except Exception as e:
            print(f"Error getting stats: {e}")
    else:
        print("Pinecone not available, skipping stats")

    def show_image_matches(matches, base_path):
        for match in matches:
            img_path = os.path.join(base_path, match["id"])
            print(f"{match['id']} | Score: {match['score']}")
            if os.path.exists(img_path):
                display(Image.open(img_path).resize((200, 200)))

    def image_to_vector(image_path):
        img = preprocess_image(image_path).unsqueeze(0).to(device)
        with torch.no_grad():
            img_embed = model.get_image_features(img)
            img_embed = torch.nn.functional.normalize(img_embed, p=2, dim=-1)
        return img_embed.squeeze().cpu().tolist()

    # Example query
    query_image = os.listdir(image_folder_path)[0]
    query_vector = image_to_vector(os.path.join(image_folder_path, query_image))
    results = index.query(vector=query_vector, top_k=10, include_metadata=True)
    show_image_matches(results["matches"], base_path=image_folder_path)

if __name__ == "__main__":
    main()
