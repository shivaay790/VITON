import os
import pinecone
from dotenv import load_dotenv

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

# Dummy vector with 512 dimensions (assuming CLIP model dimensionality)
dummy_vector = [0.0] * 512 

print("Querying index without filters to inspect metadata...")
response = index.query(vector=dummy_vector, top_k=5, include_metadata=True)

for match in response['matches']:
    print(f"ID: {match['id']}")
    print(f"Score: {match['score']}")
    print(f"Metadata: {match.get('metadata', {})}")
    print("-" * 40)
