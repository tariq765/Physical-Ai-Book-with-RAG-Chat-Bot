import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

print(f"Client type: {type(client)}")
print(f"Has search: {hasattr(client, 'search')}")
print(f"Attributes: {dir(client)}")
