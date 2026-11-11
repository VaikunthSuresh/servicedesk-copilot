"""Sub-task 4 / Section III: Retrieval-Augmented Generation over IT SOPs and KB articles.

Pipeline (v2):
  load (PDF/DOCX/MD/TXT)
  -> section-aware chunking; every chunk is prefixed with "<document title> > <section heading>"
  -> embed (all-MiniLM-L6-v2) -> persist in ChromaDB
  -> HYBRID retrieval: dense cosine similarity + BM25 keyword score, fused with Reciprocal Rank Fusion
  -> relevance gate on the best dense score (below it: decline without calling the LLM)
  -> LLM answer grounded in the top-k chunks, with [n] citations

v1 -> v2 changes were driven by the evaluation in scripts/eval_rag.py (see the report, Section III).
"""
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from ..config import settings
from . import llm

SYSTEM_PROMPT = """You are an IT Service Desk assistant. Answer ONLY from the provided context.
- Start with the direct answer in one sentence (yes/no, the rule, the number, the team).
- For a procedure, follow with numbered steps; for a policy question, state the rule and what to do instead.
- Cite sources inline like [1], [2] matching the context numbers.
- If part of the question is answered by the context, answer that part.
- Only if the context contains nothing relevant, reply exactly: "I couldn't find this in the knowledge base."
  and recommend escalating to the right team. Never invent policies, URLs or commands."""

MIN_RELEVANCE = 0.15  # best dense cosine below this = clearly off-topic -> decline without the LLM
RRF_K = 60            # standard Reciprocal Rank Fusion constant
CANDIDATES = 12       # candidates taken from each retriever before fusion

STOPWORDS = set("""a an and are as at be but by can do does for from how i if in is it its me my no not of on or our
so that the their them then there this to was we what when where which who why will with you your""".split())


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


def chunk_document(text: str, source: str) -> list[str]:
    """Split on markdown headings, chunk each section, and prefix every chunk with
    '<doc title> > <section>' so a chunk keeps the context of where it came from
    (e.g. a 'Reporting' paragraph still says it is from the Acceptable Use policy)."""
    lines = text.splitlines()
    title = next((l.lstrip("# ").strip() for l in lines if l.startswith("# ")), Path(source).stem.replace("_", " "))
    sections, heading, buf = [], "Overview", []
    for line in lines:
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            if "\n".join(buf).strip():
                sections.append((heading, "\n".join(buf)))
            heading, buf = line.lstrip("# ").strip(), []
        else:
            buf.append(line)
    if "\n".join(buf).strip():
        sections.append((heading, "\n".join(buf)))
    out = []
    for heading, body in sections:
        for c in chunk(body):
            out.append(f"{title} > {heading}\n{c}")
    return out


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
    chunks = chunk_document(load_text(path), path.name)
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
    _index.cache_clear()
    return len(chunks)


def count() -> int:
    return _collection().count()


# ---------- hybrid retrieval ----------
def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9][a-z0-9\-\.]*[a-z0-9]|[a-z0-9]", text.lower()) if t not in STOPWORDS]


class BM25:
    """Okapi BM25 (k1=1.5, b=0.75) over the chunk texts."""

    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.toks = [tokenize(d) for d in docs]
        self.k1, self.b = k1, b
        self.avgdl = sum(map(len, self.toks)) / max(1, len(self.toks))
        df = Counter(t for doc in self.toks for t in set(doc))
        n = len(self.toks)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(doc) for doc in self.toks]

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for tf, doc in zip(self.tf, self.toks):
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(doc) / self.avgdl))
            out.append(s)
        return out


@lru_cache
def _index():
    """All chunks + embeddings in memory (a service-desk KB is small) and the BM25 index."""
    got = _collection().get(include=["documents", "metadatas", "embeddings"])
    docs, metas, embs = got["documents"], got["metadatas"], got["embeddings"]
    return docs, metas, [list(e) for e in embs], BM25(docs)


def retrieve(query: str, k: int | None = None) -> list[dict]:
    if count() == 0:
        return []
    k = k or settings.top_k
    docs, metas, embs, bm25 = _index()
    q = embed([query])[0]
    dense = [sum(a * b for a, b in zip(q, e)) for e in embs]  # cosine (vectors are normalised)
    sparse = bm25.scores(query)
    rank_d = sorted(range(len(docs)), key=lambda i: -dense[i])[:CANDIDATES]
    rank_s = [i for i in sorted(range(len(docs)), key=lambda i: -sparse[i])[:CANDIDATES] if sparse[i] > 0]
    fused = Counter()
    for r, i in enumerate(rank_d):
        fused[i] += 1 / (RRF_K + r + 1)
    for r, i in enumerate(rank_s):
        fused[i] += 1 / (RRF_K + r + 1)
    top = [i for i, _ in fused.most_common(k)]
    return [{"source": metas[i]["source"], "chunk_id": metas[i]["chunk_id"], "score": round(dense[i], 4),
             "bm25": round(sparse[i], 3), "text": docs[i]} for i in top]


# ---------- generation ----------
def build_prompt(question: str, hits: list[dict]) -> str:
    ctx = "\n\n".join(f"[{i}] (source: {h['source']})\n{h['text']}" for i, h in enumerate(hits, 1))
    return f"Context:\n{ctx}\n\nQuestion: {question}\n\nAnswer:"


def answer(question: str, k: int | None = None) -> dict:
    hits = retrieve(question, k)
    if not hits or max(h["score"] for h in hits) < MIN_RELEVANCE:
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
    grounded = not text.strip().lower().startswith("i couldn't find")
    return {"answer": text, "sources": hits if grounded else [], "model": model, "grounded": grounded}
