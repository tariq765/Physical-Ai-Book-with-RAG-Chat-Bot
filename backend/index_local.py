import os
import glob
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from fastembed import TextEmbedding

load_dotenv()

# Use local storage for Qdrant
client = QdrantClient(path="D:/Physical ai book/backend/local_qdrant")

embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir="D:/fastembed_cache")

def get_embeddings(text):
    embeddings = list(embedding_model.embed([text]))
    return embeddings[0].tolist()

COLLECTION_NAME = "physical_ai_book_local"

def create_collection():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print(f"Collection {COLLECTION_NAME} created.")
    else:
        print(f"Collection {COLLECTION_NAME} already exists.")

def index_docs():
    docs_path = "D:/Physical ai book/book/docs/**/*.md"
    files = glob.glob(docs_path, recursive=True)
    
    points = []
    idx = 1
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Simple chunking by paragraph
            chunks = [c.strip() for c in content.split('\n\n') if c.strip()]
            for chunk in chunks:
                vector = get_embeddings(chunk)
                points.append(PointStruct(
                    id=idx,
                    vector=vector,
                    payload={"text": chunk, "source": file_path}
                ))
                idx += 1
    
    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        print(f"Indexed {len(points)} chunks from {len(files)} files.")
    else:
        print("No documents found to index.")

if __name__ == "__main__":
    create_collection()
    index_docs()
