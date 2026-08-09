import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Use Local Qdrant for stability in this session
QDRANT_PATH = os.getenv("QDRANT_PATH", "./local_qdrant")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "physical_ai_book_local")

_client_q = None

def get_qdrant_client():
    global _client_q
    if _client_q is None:
        _client_q = QdrantClient(path=QDRANT_PATH)
    return _client_q

# Initialize Local Embeddings
EMBEDDING_CACHE_DIR = os.getenv("EMBEDDING_CACHE_DIR", "./fastembed_cache")
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=EMBEDDING_CACHE_DIR)

def get_embeddings(text):
    embeddings = list(embedding_model.embed([text]))
    return embeddings[0].tolist()

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"message": "Physical AI Book RAG API (Local Mode) is running"}

@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        # 1. Get query embedding
        query_vector = get_embeddings(request.query)
        
        # 2. Search Qdrant using query_points (Modern API)
        client_q = get_qdrant_client()
        search_result = client_q.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vector,
            limit=6
        ).points
        
        context = "\n".join([r.payload.get("text", "") for r in search_result])
        
        # 3. Prompt Groq with supported model
        prompt = f"""You are an expert tutor for the Physical AI & Humanoid Robotics course. 
        Answer the student's question based ONLY on the provided context. 
        If the answer is not in the context, say you don't know based on the textbook.
        
        Context:
        {context}
        
        Question: {request.query}
        
        Answer:"""
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        
        return {"answer": completion.choices[0].message.content}
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
