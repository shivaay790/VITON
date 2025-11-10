import pinecone
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Always set the Pinecone environment from your index URL, not your physical location
API_KEY = os.environ.get("PINECONE_API_KEY", "YOUR_API_KEY")
ENVIRONMENT = "aped-4627-b74a"  # Hardcoded from your Pinecone index URL

print(f"Testing Pinecone connection...")
print(f"API Key: {'set' if API_KEY and API_KEY != 'YOUR_API_KEY' else 'NOT SET!'}")
print(f"Environment: {ENVIRONMENT}")

try:
    pinecone.init(api_key=API_KEY, environment=ENVIRONMENT)
    print("Pinecone initialized successfully.")
    indexes = pinecone.list_indexes()
    print(f"Available indexes: {indexes}")
    if "fashion-clip-index" in indexes:
        print("✅ Index 'fashion-clip-index' found!")
    else:
        print("❌ Index 'fashion-clip-index' NOT found!")
except Exception as e:
    print(f"❌ Pinecone connection failed: {e}")