"""
index_local.py  –  Index all book content into a local Qdrant vector database.

Sources indexed:
  1. All Markdown files under  book/docs/**/*.md   (Docusaurus textbook chapters)
  2. The standalone  mark_down  file at the project root (course overview & hardware guide)

Chunking strategy:
  • Split on double-newlines (semantic paragraphs).
  • If a paragraph exceeds MAX_CHUNK_SIZE, split it further on single newlines.
  • If a line still exceeds MAX_CHUNK_SIZE, split it on sentence boundaries.
  • Apply OVERLAP characters of overlap between consecutive chunks for continuity.
  • Store rich metadata (title, module, source path) with every chunk.
"""

import os
import re
import glob
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from fastembed import TextEmbedding

load_dotenv()

BASE_DIR         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QDRANT_URL        = os.getenv("QDRANT_URL")
QDRANT_API_KEY    = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME   = os.getenv("QDRANT_COLLECTION", "physical_ai_book_local")
EMBEDDING_MODEL   = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM     = 384
CACHE_DIR         = os.getenv("EMBEDDING_CACHE_DIR", os.path.join(BASE_DIR, "backend", "fastembed_cache"))

MAX_CHUNK_SIZE    = 500     # characters per chunk (target)
OVERLAP           = 50      # characters of overlap between consecutive chunks
MIN_CHUNK_SIZE    = 30      # skip chunks shorter than this

# ── Clients ────────────────────────────────────────────────────────────────────
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)
embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL, cache_dir=CACHE_DIR)


def get_embedding(text: str) -> list[float]:
    """Generate a single embedding vector for the given text."""
    return list(embedding_model.embed([text]))[0].tolist()


# ── Chunking helpers ───────────────────────────────────────────────────────────

def _split_on_sentences(text: str, max_size: int) -> list[str]:
    """Split a long string on sentence boundaries (. ! ?)."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 > max_size and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current} {sentence}" if current else sentence
    if current.strip():
        chunks.append(current.strip())
    return chunks


def smart_chunk(content: str, max_size: int = MAX_CHUNK_SIZE,
                overlap: int = OVERLAP) -> list[str]:
    """
    Split content into overlapping chunks, respecting paragraph and sentence
    boundaries as much as possible.
    """
    # Stage 1: Split on paragraphs (double newline)
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

    # Stage 2: Break oversized paragraphs on single newlines, then sentences
    pieces: list[str] = []
    for para in paragraphs:
        if len(para) <= max_size:
            pieces.append(para)
        else:
            # Try splitting on single newlines first
            lines = [ln.strip() for ln in para.split('\n') if ln.strip()]
            for line in lines:
                if len(line) <= max_size:
                    pieces.append(line)
                else:
                    pieces.extend(_split_on_sentences(line, max_size))

    # Stage 3: Merge tiny consecutive pieces and apply overlap
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if len(current) + len(piece) + 1 <= max_size:
            current = f"{current}\n{piece}" if current else piece
        else:
            if current:
                chunks.append(current.strip())
                # Overlap: carry last `overlap` chars into the next chunk
                tail = current[-overlap:] if len(current) > overlap else current
                current = f"{tail}\n{piece}"
            else:
                current = piece
    if current.strip():
        chunks.append(current.strip())

    # Filter out trivially small chunks
    return [c for c in chunks if len(c) >= MIN_CHUNK_SIZE]


def extract_title(content: str) -> str:
    """Extract the first Markdown heading as a document title."""
    match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"


def extract_module(file_path: str) -> str:
    """Infer module name from file path (e.g., module-1-ros2)."""
    parts = file_path.replace("\\", "/").split("/")
    for part in parts:
        if part.startswith("module-"):
            return part
    return "general"


# ── Collection management ─────────────────────────────────────────────────────

def recreate_collection():
    """Delete existing collection (if any) and create a fresh one."""
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        print(f"[DELETED] Deleted old collection '{COLLECTION_NAME}'.")

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )
    print(f"[OK] Created fresh collection '{COLLECTION_NAME}'.")


# ── Indexing ───────────────────────────────────────────────────────────────────

def collect_documents() -> list[dict]:
    """
    Gather all documents to index.
    Returns a list of dicts: {content, source, title, module}
    """
    documents = []

    # ── 1. Docusaurus book chapters ────────────────────────────────────────
    docs_pattern = os.path.join(BASE_DIR, "book", "docs", "**", "*.md")
    for file_path in glob.glob(docs_pattern, recursive=True):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        documents.append({
            "content": content,
            "source": file_path.replace("\\", "/"),
            "title": extract_title(content),
            "module": extract_module(file_path),
        })

    # ── 2. Standalone mark_down file (course overview + hardware) ──────────
    mark_down_path = os.path.join(BASE_DIR, "mark_down")
    if os.path.isfile(mark_down_path):
        with open(mark_down_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        documents.append({
            "content": content,
            "source": mark_down_path.replace("\\", "/"),
            "title": "Physical AI & Humanoid Robotics – Course Overview",
            "module": "overview",
        })

    return documents


def index_all():
    """Chunk every document, embed it, and upsert into Qdrant."""
    documents = collect_documents()
    if not documents:
        print("[ERROR] No documents found to index.")
        return

    print(f"[INFO] Found {len(documents)} source documents.")

    points: list[PointStruct] = []
    idx = 1

    for doc in documents:
        chunks = smart_chunk(doc["content"])
        print(f"   - {doc['title'][:60]:60s}  ->  {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            vector = get_embedding(chunk)
            points.append(PointStruct(
                id=idx,
                vector=vector,
                payload={
                    "text": chunk,
                    "source": doc["source"],
                    "title": doc["title"],
                    "module": doc["module"],
                    "chunk_index": i,
                },
            ))
            idx += 1

    # Batch upsert (Qdrant handles large batches internally)
    BATCH_SIZE = 100
    for start in range(0, len(points), BATCH_SIZE):
        batch = points[start : start + BATCH_SIZE]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        print(f"   [UPSERT] Batch {start // BATCH_SIZE + 1} "
              f"({len(batch)} points)")

    print(f"\n[DONE] Successfully indexed {len(points)} chunks "
          f"from {len(documents)} documents into '{COLLECTION_NAME}'.")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    recreate_collection()
    index_all()
