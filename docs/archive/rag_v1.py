"""Sub-task 4 / Section III: Retrieval-Augmented Generation over IT SOPs and KB articles.

Owner: Member 3.
Pipeline: load (PDF/DOCX/MD/TXT) -> chunk -> embed (MiniLM) -> Chroma -> retrieve top-k -> LLM with citations.
"""
from functools import lru_cache
from pathlib import Path

from ..config import settings
from . import llm

SYSTEM_PROMPT = """You are an IT Service Desk assistant. Answer ONLY from the provided context.
- Give numbered, actionable troubleshooting steps.
- Cite sources inline like [1], [2] matching the context numbers.
- If the context does not contain the answer, say "I couldn't find this in the knowledge base"
  and recommend escalating to the right team. Never invent policies, URLs or commands."""

MIN_RELEVANCE = 0.25  # cosine similarity below this = treat as "not found"


# ---------- loading & chunking ----------
def load_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    if suffix == ".docx":
        import docx
        return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk(text: str, size: int | None = None, overlap: int | None = None) -> list[str]:
    """Paragraph-aware character chunking with overlap."""
    size = size or settings.chunk_size
    overlap = overlap if overlap is not None else settings.chunk_overlap
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) + 2 <= size:
            buf = f"{buf}\n\n{p}" if buf else p
            continue
        if buf:
            chunks.append(buf)
            buf = buf[-overlap:] + "\n\n" + p if overlap else p
        else:
            buf = p
        while len(buf) > size:  # very long paragraph
            chunks.append(buf[:size])
            buf = buf[size - overlap:]
    if buf:
        chunks.append(buf)
    return chunks


# ---------- vector store ----------
@lru_cache
def _embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.embedding_model)


@lru_cache
def _collection():
    import chromadb
    client = chromadb.PersistentClient(path=settings.chroma_dir,
                                       settings=chromadb.Settings(anonymized_telemetry=False))
    return client.get_or_create_collection(settings.collection_name, metadata={"hnsw:space": "cosine"})


def embed(texts: list[str]) -> list[list[float]]:
    return _embedder().encode(texts, normalize_embeddings=True).tolist()


def ingest_file(path: Path) -> int:
    chunks = chunk(load_text(path))
    if not chunks:
        return 0
    col = _collection()
    col.delete(where={"source": path.name})  # re-ingesting a file replaces it
    col.add(
        ids=[f"{path.name}::{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embed(chunks),
        metadatas=[{"source": path.name, "chunk_id": i} for i in range(len(chunks))],
    )
    return len(chunks)


def count() -> int:
    return _collection().count()


def retrieve(query: str, k: int | None = None) -> list[dict]:
    if count() == 0:
        return []
    res = _collection().query(query_embeddings=embed([query]), n_results=k or settings.top_k)
    return [
        {"source": m["source"], "chunk_id": m["chunk_id"], "score": round(1 - d, 4), "text": doc}
        for doc, m, d in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    ]


# ---------- generation ----------
def build_prompt(question: str, hits: list[dict]) -> str:
    ctx = "\n\n".join(f"[{i}] (source: {h['source']})\n{h['text']}" for i, h in enumerate(hits, 1))
    return f"Context:\n{ctx}\n\nQuestion: {question}\n\nAnswer:"


def answer(question: str, k: int | None = None) -> dict:
    hits = [h for h in retrieve(question, k) if h["score"] >= MIN_RELEVANCE]
    if not hits:
        return {
            "answer": "I couldn't find this in the knowledge base. Please escalate to the L2 team.",
            "sources": [], "model": "none", "grounded": False,
        }
    if llm.available():
        text = llm.chat(SYSTEM_PROMPT, build_prompt(question, hits))
        model = settings.llm_model
    else:  # extractive fallback so the demo works without an API key
        text = "LLM not configured; most relevant knowledge-base excerpt:\n\n" + hits[0]["text"] + " [1]"
        model = "extractive-fallback"
    return {"answer": text, "sources": hits, "model": model, "grounded": True}
