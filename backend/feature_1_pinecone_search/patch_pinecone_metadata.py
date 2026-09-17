import os
import sys
import pinecone
from dotenv import load_dotenv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "aped-4627-b74a")
PINECONE_INDEX_HOST = (
    os.environ.get("PINECONE_INDEX_HOST")
    or os.environ.get("PINECONE_HOST")
    or os.environ.get("PINECONE_INDEX_URL")
)
if PINECONE_INDEX_HOST:
    PINECONE_INDEX_HOST = PINECONE_INDEX_HOST.strip().strip("`")

print("Initializing Pinecone...")
if hasattr(pinecone, "Pinecone"):
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index("fashion-clip-index", host=PINECONE_INDEX_HOST)
else:
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    index = pinecone.Index("fashion-clip-index", host=PINECONE_INDEX_HOST)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import CLOTHES_DIR as DATASET_CLOTH_DIR

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

def generate_metadata(filename):
    base = os.path.splitext(filename)[0]
    h = _stable_hash(base)
    return {
        "brand": PRODUCT_BRANDS[h % len(PRODUCT_BRANDS)],
        "category": PRODUCT_CATEGORIES[(h // 3) % len(PRODUCT_CATEGORIES)],
        "color": PRODUCT_COLORS[(h // 7) % len(PRODUCT_COLORS)],
        "price": PRODUCT_PRICE_BUCKETS[(h // 11) % len(PRODUCT_PRICE_BUCKETS)]
    }

def update_with_retry(filename, max_retries=10, initial_backoff=0.5):
    md = generate_metadata(filename)
    retries = 0
    while retries < max_retries:
        try:
            # We first fetch the metadata to see if it's already updated.
            # This avoids unnecessary write requests which hit rate limits harder than reads.
            res = index.fetch(ids=[filename])
            vec = res.get('vectors', {}).get(filename, {})
            meta = vec.get('metadata') or {}
            if filename in res.get('vectors', {}) and 'brand' in meta:
                return True, filename, "Already updated"

            index.update(id=filename, set_metadata=md)
            return True, filename, "Updated"
        except Exception as e:
            if '429' in str(e) or 'limit' in str(e).lower():
                time.sleep(initial_backoff * (2 ** retries))
                retries += 1
            else:
                return False, filename, str(e)
    return False, filename, "Max retries exceeded"

def main():
    if not os.path.exists(DATASET_CLOTH_DIR):
        print(f"Error: Dataset not found at {DATASET_CLOTH_DIR}")
        return

    files = [f for f in os.listdir(DATASET_CLOTH_DIR) if f.endswith('.jpg')]
    total_files = len(files)
    print(f"Found {total_files} .jpg files in dataset.")
    print("Starting metadata patch with rate-limit handling...")

    start_time = time.time()
    success_count = 0
    fail_count = 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(update_with_retry, f): f for f in files}
        
        for idx, future in enumerate(as_completed(futures), 1):
            success, filename, msg = future.result()
            if success:
                success_count += 1
            else:
                fail_count += 1
                print(f"Failed to update {filename}: {msg}")
            
            if idx % 100 == 0:
                elapsed = time.time() - start_time
                print(f"Processed {idx}/{total_files} records... ({success_count} successful) in {elapsed:.1f}s")
                
    total_time = time.time() - start_time
    print(f"Finished patching {total_files} records in Pinecone.")
    print(f"Success: {success_count}, Failed: {fail_count}")
    print(f"Total time elapsed: {total_time:.2f} seconds.")

if __name__ == "__main__":
    main()
