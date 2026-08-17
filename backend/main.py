"""
main.py  –  FastAPI backend for the Physical AI Book RAG Chatbot.

Endpoints:
  GET  /       → Health check
  POST /chat   → RAG-powered question answering

Stack:
  • Qdrant (local)  for vector search
  • FastEmbed       for embedding (BAAI/bge-small-en-v1.5)
  • Groq            for LLM generation (llama-3.3-70b-versatile)
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(os.path.dirname(BASE_DIR), ".env"))

# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Physical AI Book RAG API",
    description="RAG-powered chatbot for the Physical AI & Humanoid Robotics textbook.",
    version="2.0.0",
)

# Enable CORS for all origins (frontend can be on any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Groq LLM client ───────────────────────────────────────────────────────────
_groq_client = None

def get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = (os.getenv("GROQ_API_KEY") or "").strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        _groq_client = Groq(api_key=api_key)
    return _groq_client

# ── Qdrant (Cloud) ────────────────────────────────────────────────────────────
_qdrant_client = None

def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        url = (os.getenv("QDRANT_URL") or "").strip() or None
        api_key = (os.getenv("QDRANT_API_KEY") or "").strip() or None
        print(f"[INFO] Initializing QdrantClient with URL: {url}, API_KEY present: {bool(api_key)} (len: {len(api_key) if api_key else 0})")
        _qdrant_client = QdrantClient(
            url=url,
            api_key=api_key,
            check_compatibility=False,
        )
    return _qdrant_client


# ── Embeddings (FastEmbed – local, no API key needed) ──────────────────────────
EMBEDDING_CACHE_DIR = os.getenv("EMBEDDING_CACHE_DIR", "./fastembed_cache")
embedding_model = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5",
    cache_dir=EMBEDDING_CACHE_DIR,
)

def get_embedding(text: str) -> list[float]:
    """Generate a single embedding vector."""
    return list(embedding_model.embed([text]))[0].tolist()


# ── Request / Response models ─────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup_check():
    """Verify Qdrant collection is accessible on startup."""
    try:
        collection_name = (os.getenv("QDRANT_COLLECTION") or "physical_ai_book_v2").strip()
        qclient = get_qdrant_client()
        if qclient.collection_exists(collection_name):
            info = qclient.get_collection(collection_name)
            print(f"[STARTUP] Qdrant collection '{collection_name}' is {info.status} with {info.points_count} points.")
        else:
            print(f"[STARTUP][WARNING] Qdrant collection '{collection_name}' does NOT exist! "
                  "You need to re-run index_local.py to recreate it.")
    except Exception as e:
        print(f"[STARTUP][ERROR] Could not connect to Qdrant: {e}")


@app.get("/")
def read_root():
    return {"message": "Physical AI Book RAG API (Local Mode) is running [OK]"}


@app.get("/health")
def health_check():
    """Health check endpoint — also keeps Qdrant cluster alive by querying it."""
    try:
        collection_name = (os.getenv("QDRANT_COLLECTION") or "physical_ai_book_v2").strip()
        qclient = get_qdrant_client()
        exists = qclient.collection_exists(collection_name)
        if exists:
            info = qclient.get_collection(collection_name)
            return {
                "status": "healthy",
                "qdrant_collection": collection_name,
                "qdrant_status": str(info.status),
                "points_count": info.points_count,
            }
        else:
            return {"status": "degraded", "error": f"Collection '{collection_name}' not found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: QueryRequest):
    """
    RAG pipeline:
      1. Embed the user query.
      2. Search Qdrant for the top-K most relevant chunks.
      3. Build a context string and send it to Groq LLM.
      4. Return the answer along with source metadata.
    """
    try:
        # 1 ── Embed the query
        query_vector = get_embedding(request.query)

        # 2 ── Retrieve relevant chunks from Qdrant
        collection_name = (os.getenv("QDRANT_COLLECTION") or "physical_ai_book_v2").strip()
        qclient = get_qdrant_client()
        search_results = qclient.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=8,                       # retrieve top 8 chunks
        ).points

        if not search_results:
            return ChatResponse(
                answer="I couldn't find any relevant information in the textbook. "
                       "Please try rephrasing your question.",
                sources=[],
            )

        # 3 ── Build context with source attribution
        context_parts = []
        sources = []
        seen_texts = set()

        for hit in search_results:
            text = hit.payload.get("text", "")
            if text in seen_texts:
                continue                   # skip exact duplicates
            seen_texts.add(text)

            title  = hit.payload.get("title", "Unknown")
            module = hit.payload.get("module", "general")
            source = hit.payload.get("source", "")

            context_parts.append(
                f"[Source: {title} | Module: {module}]\n{text}"
            )
            sources.append({
                "title": title,
                "module": module,
                "source": source,
                "score": round(hit.score, 4) if hasattr(hit, 'score') else None,
            })

        context = "\n\n---\n\n".join(context_parts)

        # 4 ── Prompt the LLM
        system_prompt = (
            "You are an expert tutor for the Physical AI & Humanoid Robotics course. "
            "Your job is to answer student questions **based ONLY on the provided context** "
            "from the course textbook. "
            "If the answer is not in the context, say: "
            "'I don't have enough information in the textbook to answer that.' "
            "Be clear, concise, and use bullet points or numbered lists when helpful. "
            "If the context includes code examples, include them in your answer."
        )

        user_prompt = (
            f"Context from the textbook:\n\n{context}\n\n"
            f"---\n\n"
            f"Student Question: {request.query}\n\n"
            f"Answer:"
        )

        gclient = get_groq_client()
        candidate_models = [
            os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            "openai/gpt-oss-120b",
            "qwen/qwen3.6-27b",
            "openai/gpt-oss-20b",
            "groq/compound-mini",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ]
        models_to_try = list(dict.fromkeys([m.strip() for m in candidate_models if m and m.strip()]))

        completion = None
        last_err = None
        for model_name in models_to_try:
            try:
                completion = gclient.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=1024,
                )
                if completion:
                    break
            except Exception as err:
                last_err = err
                print(f"[WARN] Groq model '{model_name}' failed: {err}. Trying next fallback...")

        if completion is None:
            raise last_err or Exception("All Groq model fallbacks failed.")

        answer = completion.choices[0].message.content

        return ChatResponse(answer=answer, sources=sources)

    except Exception as e:
        print(f"[ERROR] Error in /chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Run directly ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
