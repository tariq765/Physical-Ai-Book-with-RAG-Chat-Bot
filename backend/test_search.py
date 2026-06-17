import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir="D:/fastembed_cache")

def get_embeddings(text):
    embeddings = list(embedding_model.embed([text]))
    return embeddings[0].tolist()

query = "What is ROS2?"
vector = get_embeddings(query)

try:
    print("Trying query_points...")
    res = client.query_points(
        collection_name=os.getenv("QDRANT_COLLECTION"),
        query=vector,
        limit=3
    )
    print("Query_points worked!")
    print(f"Results: {res.points}")
except Exception as e:
    print(f"An error occurred: {e}")

