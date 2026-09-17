import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "_vendor"))
import pinecone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ.get("PINECONE_API_KEY", "YOUR_API_KEY")
ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT", "aped-4627-b74a")
INDEX_HOST = (
    os.environ.get("PINECONE_INDEX_HOST")
    or os.environ.get("PINECONE_HOST")
    or os.environ.get("PINECONE_INDEX_URL")
)
INDEX_NAME = "fashion-clip-index"

print(f"Testing Pinecone connection...")
print(f"API Key: {'set' if API_KEY and API_KEY != 'YOUR_API_KEY' else 'NOT SET!'}")
print(f"Environment: {ENVIRONMENT}")
print(f"Host: {'set' if INDEX_HOST else 'NOT SET!'}")

try:
    pc = pinecone.Pinecone(api_key=API_KEY)
    print("Pinecone client initialized successfully.")
    if not INDEX_HOST:
        raise RuntimeError("PINECONE_INDEX_HOST is required")
    index = pc.Index(INDEX_NAME, host=INDEX_HOST.strip().strip("`"))
    stats = index.describe_index_stats()
    print(f"✅ Connected to '{INDEX_NAME}'")
    print(f"✅ Index stats: {stats}")
except Exception as e:
    print(f"❌ Pinecone connection failed: {e}")
