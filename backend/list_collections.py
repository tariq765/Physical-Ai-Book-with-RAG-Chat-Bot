import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

try:
    collections = client.get_collections()
    print(f"Collections: {collections}")
except Exception as e:
    print(f"Error: {e}")
